"""Additional schemas for API types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


def new_uuid() -> str:
    return uuid4().hex[:16]


@dataclass(frozen=True)
class TimeseriesRequest:
    """Timeseries query parameters."""

    country_code: str
    indicator_codes: list[str]
    years: list[int] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimeseriesRequest":
        return cls(
            country_code=data.get("country_code", ""),
            indicator_codes=data.get("indicator_codes", []),
            years=data.get("years"),
        )
