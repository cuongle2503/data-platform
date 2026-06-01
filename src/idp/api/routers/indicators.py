"""Indicators REST router."""

import logging
from typing import Any

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from idp.api.schemas.common import ErrorDetail, PaginationMeta, ResponseEnvelope
from idp.api.schemas.indicator import IndicatorResponse
from idp.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


def create_router(repo: StorageRepository) -> APIRouter:
    """Create the indicators router. Accepts a repository for DI/testability."""
    router = APIRouter()

    @router.get("/indicators/catalog", name="list_indicators")
    async def list_indicators(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        category: str | None = Query(None, description="Filter by category"),
    ) -> JSONResponse:
        """Get paginated list of indicators."""
        all_indicators = repo.get_indicators()

        results = all_indicators
        if category:
            results = [i for i in results if i.get("category") == category]

        total = len(results)
        start = (page - 1) * page_size
        paged = results[start : start + page_size]

        indicators = [IndicatorResponse(**i) for i in paged]
        envelope = ResponseEnvelope(
            data=[ind.model_dump() for ind in indicators],
            meta=PaginationMeta(page=page, page_size=page_size, total=total),
            error=None,
        )
        return JSONResponse(content=envelope.model_dump())

    @router.get("/indicators/{code}/metadata", name="get_indicator_metadata")
    async def get_indicator_metadata(code: str) -> JSONResponse:
        """Get indicator metadata by code."""
        raw = repo.get_indicator(code)
        if raw is None:
            envelope = ResponseEnvelope(
                data=None,
                meta=None,
                error=ErrorDetail(code="NOT_FOUND", message=f"Indicator '{code}' not found"),
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=envelope.model_dump(),
            )

        indicator = IndicatorResponse(**raw)
        envelope = ResponseEnvelope(data=indicator.model_dump(), meta=None, error=None)
        return JSONResponse(content=envelope.model_dump())

    return router
