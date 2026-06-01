"""Search schemas."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request parameters."""

    q: str = Field(..., min_length=1, max_length=500, description="Search query string")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")


class SemanticSearchRequest(BaseModel):
    """Semantic search request parameters."""

    q: str = Field(
        ..., min_length=1, max_length=500, description="Natural language query for semantic search"
    )
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")


class SearchResultItem(BaseModel):
    """A single search result."""

    indicator_code: str
    indicator_name: str
    category: str | None = None
    description: str | None = None
    similarity: float | None = None
    source: str = Field(..., description="Search source: 'lexical', 'semantic', or 'combined'")
