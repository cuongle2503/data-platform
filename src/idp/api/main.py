"""FastAPI application main entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from idp.api.routers import chat, countries, indicators, search, timeseries
from idp.api.schemas.common import ErrorDetail, ResponseEnvelope
from idp.intelligence.gemini_client import RAGClient
from idp.storage.embeddings_client import GeminiEmbeddingsClient
from idp.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting FastAPI application")
    yield
    logger.info("Shutting down FastAPI application")


app = FastAPI(
    title="Intelligent Data Platform API",
    description="REST API for economic data access and RAG-powered chatbot",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning("Validation error: %s", exc.errors())
    error = ErrorDetail(code="VALIDATION_ERROR", message=str(exc.errors()))
    envelope: ResponseEnvelope[object] = ResponseEnvelope(data=None, meta=None, error=error)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=envelope.model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions."""
    logger.exception("Unhandled exception: %s", exc)
    error = ErrorDetail(code="INTERNAL_ERROR", message="An internal error occurred")
    envelope: ResponseEnvelope[object] = ResponseEnvelope(data=None, meta=None, error=error)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=envelope.model_dump(),
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


from idp.common.config import get_settings

def create_app(
    repo: StorageRepository,
    embeddings_client: GeminiEmbeddingsClient | None = None,
    rag_client: RAGClient | None = None,
) -> FastAPI:
    """Factory: wire routers to the existing app."""
    # Register routers using dependency injection
    app.include_router(countries.create_router(repo), prefix="/api/v1", tags=["countries"])
    app.include_router(indicators.create_router(repo), prefix="/api/v1", tags=["indicators"])
    app.include_router(timeseries.create_router(repo), prefix="/api/v1", tags=["timeseries"])
    if embeddings_client:
        app.include_router(
            search.create_router(repo, embeddings_client),
            prefix="/api/v1",
            tags=["search"],
        )
    if rag_client:
        app.include_router(
            chat.create_router(repo, rag_client),
            prefix="/api/v1",
            tags=["chat"],
        )
    return app

# Auto-initialize routers for uvicorn
import psycopg

try:
    settings = get_settings()
    pg_conn = psycopg.connect(settings.postgres.database_url)
    repo = StorageRepository(pg_conn)

    embeddings_client = None
    rag_client = None

    if settings.gemini.api_key:
        embeddings_client = GeminiEmbeddingsClient(
            api_key=settings.gemini.api_key,
            model_name=settings.gemini.embedding_model,
        )
        rag_client = RAGClient(
            api_key=settings.gemini.api_key,
            model_name=settings.gemini.chat_model,
        )

    create_app(repo, embeddings_client, rag_client)
except Exception as e:
    logger.error(f"Failed to auto-initialize API routers: {e}")
