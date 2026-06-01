"""Indicator schemas."""

from pydantic import BaseModel, Field


class IndicatorResponse(BaseModel):
    """Indicator response model."""

    indicator_code: str = Field(..., description="World Bank indicator code")
    indicator_name: str = Field(..., description="Full indicator name")
    category: str | None = Field(None, description="Indicator category")
    unit: str | None = Field(None, description="Unit of measurement")
    description: str | None = Field(None, description="Detailed description")


class TimeseriesData(BaseModel):
    """Time series data point."""

    country_code: str = Field(..., description="3-letter ISO country code")
    indicator_code: str = Field(..., description="World Bank indicator code")
    year: int = Field(..., ge=1900, le=2100, description="Observation year")
    value: float | None = Field(..., description="Observation value")
    source: str | None = Field(None, description="Data source")
