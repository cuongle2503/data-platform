"""Chat API router — REST fallback and WebSocket streaming for RAG chatbot."""

import logging
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from idp.api.schemas.chat import ChatRequest, ChatResponse
from idp.api.schemas.common import ErrorDetail, ResponseEnvelope
from idp.intelligence.context_builder import build_context
from idp.intelligence.gemini_client import RAGClient
from idp.intelligence.query_parser import extract_entities, normalize_query
from idp.storage.repository import StorageRepository

logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(r"\[IND:([^\]]+)\]")


def extract_citations(text: str) -> list[str]:
    """Extract citation codes from [IND:CODE] format in text."""
    return list(set(CITATION_PATTERN.findall(text)))


def create_router(repo: StorageRepository, rag_client: RAGClient) -> APIRouter:
    """Create the chat router with dependency injection."""
    router = APIRouter()

    @router.post("/chat", name="chat_rest")
    async def chat_rest(request: ChatRequest) -> JSONResponse:
        """REST fallback for RAG pipeline: returns full answer with citations."""
        try:
            # 1. Normalize query
            normalized = normalize_query(request.query)

            # 2. Extract entities (optional)
            entities = extract_entities(request.query)

            # 3. Search for relevant indicators
            indicators = repo.search_indicators_lexical(normalized)

            # Fall back to indicator code search if entities found
            if entities.get("country_codes") and not indicators:
                for cc in entities["country_codes"][:3]:
                    raw = repo.get_indicator(cc)
                    if raw:
                        indicators.append(raw)

            # 4. Get timeseries data if we have entities
            timeseries_data: list[dict] = []
            if entities["country_codes"] and indicators:
                for cc in entities["country_codes"][:5]:
                    codes = [ind["indicator_code"] for ind in indicators[:5]]
                    try:
                        ts = repo.get_timeseries(
                            country=cc,
                            indicators=codes,
                            years=entities.get("years"),
                        )
                        timeseries_data.extend(ts)
                    except Exception as exc:
                        logger.warning("Timeseries fetch failed: %s", exc)

            # 5. Build context
            context = build_context(indicators[: request.max_indicators], timeseries_data)

            # 6. Generate answer via Gemini
            answer = rag_client.generate_answer(request.query, context)

            # 7. Extract citations
            sources = extract_citations(answer)

            response = ChatResponse(answer=answer, sources=sources)
            envelope = ResponseEnvelope(data=response.model_dump(), meta=None, error=None)
            return JSONResponse(content=envelope.model_dump())

        except Exception as exc:
            logger.exception("Chat error: %s", exc)
            envelope = ResponseEnvelope(
                data=None,
                meta=None,
                error=ErrorDetail(code="CHAT_ERROR", message=str(exc)),
            )
            return JSONResponse(content=envelope.model_dump(), status_code=500)

    @router.websocket("/chat/ws", name="chat_websocket")
    async def chat_websocket(websocket: WebSocket) -> None:
        """WebSocket endpoint for streaming RAG chatbot."""
        await websocket.accept()

        try:
            # Receive query
            data = await websocket.receive_json()
            query = data.get("query", "")

            if not query:
                await websocket.send_json({"error": "Query is required"})
                await websocket.close()
                return

            # 1. Normalize query
            normalized = normalize_query(query)

            # 2. Search for relevant indicators
            indicators = repo.search_indicators_lexical(normalized)

            # 3. Get timeseries data
            entities = extract_entities(query)
            timeseries_data: list[dict] = []
            if entities["country_codes"] and indicators:
                for cc in entities["country_codes"][:3]:
                    codes = [ind["indicator_code"] for ind in indicators[:3]]
                    try:
                        ts = repo.get_timeseries(
                            country=cc, indicators=codes, years=entities.get("years")
                        )
                        timeseries_data.extend(ts)
                    except Exception:
                        pass

            # 4. Build context
            context = build_context(indicators[:5], timeseries_data)

            # 5. Stream answer via Gemini
            collected_text = ""
            for token in rag_client.generate_answer_stream(query, context):
                collected_text += token
                await websocket.send_json({"token": token})

            # 6. Extract and send citations
            citations = extract_citations(collected_text)
            for code in citations:
                # Get indicator name for the citation
                ind = repo.get_indicator(code)
                name = ind["indicator_name"] if ind else code
                await websocket.send_json({"indicator_code": code, "indicator_name": name})

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as exc:
            logger.exception("WebSocket error: %s", exc)
            import contextlib

            with contextlib.suppress(Exception):
                # Client may have already disconnected
                await websocket.send_json({"error": str(exc)})

    return router
