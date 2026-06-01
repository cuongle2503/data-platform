"""Countries REST router."""

import logging
from typing import Any

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from idp.api.schemas.common import ErrorDetail, PaginationMeta, ResponseEnvelope
from idp.api.schemas.country import CountryResponse
from idp.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


def create_router(repo: StorageRepository) -> APIRouter:
    """Create the countries router. Accepts a repository for DI/testability."""
    router = APIRouter()

    @router.get("/countries", name="list_countries")
    async def list_countries(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        region: str | None = Query(None, description="Filter by region"),
        income_group: str | None = Query(None, description="Filter by income group"),
    ) -> JSONResponse:
        """Get paginated list of countries."""
        all_countries = repo.get_countries()

        # Apply filters
        results = all_countries
        if region:
            results = [c for c in results if c.get("region") == region]
        if income_group:
            results = [c for c in results if c.get("income_group") == income_group]

        total = len(results)
        start = (page - 1) * page_size
        paged = results[start : start + page_size]

        countries = [CountryResponse(**c) for c in paged]
        envelope = ResponseEnvelope(
            data=[c.model_dump() for c in countries],
            meta=PaginationMeta(page=page, page_size=page_size, total=total),
            error=None,
        )
        return JSONResponse(content=envelope.model_dump())

    @router.get("/countries/{code}", name="get_country")
    async def get_country(code: str) -> JSONResponse:
        """Get country details by ISO code."""
        raw = repo.get_country(code)
        if raw is None:
            envelope = ResponseEnvelope(
                data=None,
                meta=None,
                error=ErrorDetail(code="NOT_FOUND", message=f"Country '{code}' not found"),
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=envelope.model_dump(),
            )

        country = CountryResponse(**raw)
        envelope = ResponseEnvelope(data=country.model_dump(), meta=None, error=None)
        return JSONResponse(content=envelope.model_dump())

    return router
