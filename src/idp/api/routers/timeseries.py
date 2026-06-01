"""Timeseries REST router."""

import logging
from typing import Any

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from idp.api.schemas.common import ErrorDetail, ResponseEnvelope
from idp.api.schemas.indicator import TimeseriesData
from idp.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


def create_router(repo: StorageRepository) -> APIRouter:
    """Create the timeseries router. Accepts a repository for DI/testability."""
    router = APIRouter()

    @router.get("/timeseries", name="get_timeseries")
    async def get_timeseries(
        country_code: str = Query(
            ..., min_length=3, max_length=3, description="3-letter country code"
        ),
        indicator_codes: list[str] = Query(..., min_items=1, description="List of indicator codes"),
        years: list[int] | None = Query(None, description="Filter by years"),
    ) -> JSONResponse:
        """Get timeseries data for a country and set of indicators."""
        try:
            raw_data = repo.get_timeseries(
                country=country_code,
                indicators=indicator_codes,
                years=years,
            )
        except Exception as exc:
            logger.exception("Error fetching timeseries: %s", exc)
            envelope = ResponseEnvelope(
                data=None,
                meta=None,
                error=ErrorDetail(code="QUERY_ERROR", message=str(exc)),
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=envelope.model_dump(),
            )

        timeseries = [TimeseriesData(**r) for r in raw_data]
        envelope = ResponseEnvelope(
            data=[ts.model_dump() for ts in timeseries],
            meta=None,
            error=None,
        )
        return JSONResponse(content=envelope.model_dump())

    return router
