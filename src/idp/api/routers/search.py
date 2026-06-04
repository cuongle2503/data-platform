"""Search API router — lexical + semantic combined search."""

import logging
from typing import cast

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from idp.api.schemas.common import ErrorDetail, ResponseEnvelope
from idp.api.schemas.search import SearchResultItem
from idp.storage.embeddings_client import GeminiEmbeddingsClient
from idp.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


def merge_results(
    lexical: list[dict[str, object]],
    semantic: list[dict[str, object]],
    limit: int,
) -> list[SearchResultItem]:
    """
    Merge and rank search results.

    Strategy:
    - Semantic results come first (by similarity).
    - Lexical results added after, deduplicating by indicator_code.
    """
    seen: set[str] = set()
    merged: list[SearchResultItem] = []

    for item in semantic:
        code = str(item["indicator_code"])
        if code in seen:
            continue
        seen.add(code)
        merged.append(
            SearchResultItem(
                indicator_code=code,
                indicator_name=str(item["indicator_name"]),
                category=cast(str | None, item.get("category")),
                similarity=cast(float | None, item.get("similarity")),
                source="semantic",
            )
        )

    for item in lexical:
        code = str(item["indicator_code"])
        if code in seen:
            continue
        seen.add(code)
        merged.append(
            SearchResultItem(
                indicator_code=code,
                indicator_name=str(item["indicator_name"]),
                category=cast(str | None, item.get("category")),
                description=cast(str | None, item.get("description")),
                source="lexical",
            )
        )

    return merged[:limit]


def create_router(repo: StorageRepository, embeddings_client: GeminiEmbeddingsClient) -> APIRouter:
    """Create the search router with dependency injection."""
    router = APIRouter()

    @router.get("/search/indicators", name="search_indicators")
    async def search_indicators(
        q: str = Query(..., min_length=1, max_length=500, description="Search query"),
        limit: int = Query(10, ge=1, le=50, description="Max results"),
    ) -> JSONResponse:
        """Search indicators by combining lexical and semantic search."""
        try:
            # Run lexical search
            lexical_results = repo.search_indicators_lexical(q)

            # Generate embedding and run semantic search
            query_embedding = embeddings_client.generate_embedding(q, task_type="retrieval_query")
            semantic_limit = min(limit, 10)
            semantic_results = repo.search_indicators_semantic(
                query_embedding, limit=semantic_limit
            )

            # Merge and rank results
            results = merge_results(lexical_results, semantic_results, limit)

            ok_envelope: ResponseEnvelope[list[dict[str, object]]] = ResponseEnvelope(
                data=[r.model_dump() for r in results],
                meta=None,
                error=None,
            )
            return JSONResponse(content=ok_envelope.model_dump())

        except Exception as exc:
            logger.exception("Search error: %s", exc)
            error_envelope: ResponseEnvelope[object] = ResponseEnvelope(
                data=None,
                meta=None,
                error=ErrorDetail(code="SEARCH_ERROR", message=str(exc)),
            )
            return JSONResponse(content=error_envelope.model_dump(), status_code=500)

    return router
