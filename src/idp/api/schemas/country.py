"""Country schemas."""

from pydantic import BaseModel, Field


class CountryResponse(BaseModel):
    """Country response model."""

    country_code: str = Field(..., description="3-letter ISO country code")
    country_name: str = Field(..., description="Full country name")
    region: str | None = Field(None, description="World Bank region")
    income_group: str | None = Field(None, description="World Bank income group")
    is_asean: bool = Field(..., description="Whether country is an ASEAN member")
    is_primary: bool = Field(..., description="Whether country is a primary focus area")
