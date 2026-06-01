"""Chat schemas for RAG chatbot endpoints."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """REST chat request."""

    query: str = Field(..., description="User's natural language question")
    max_indicators: int = Field(5, ge=1, le=20, description="Max indicators to include in context")


class ChatResponse(BaseModel):
    """REST chat response."""

    answer: str = Field(..., description="Generated answer from LLM")
    sources: list[str] = Field(default_factory=list, description="Citation source indicator codes")


class WebSocketMessage(BaseModel):
    """WebSocket message from client."""

    query: str = Field(..., description="User's natural language question")


class WebSocketToken(BaseModel):
    """WebSocket token-by-token stream event."""

    token: str = Field(..., description="A single token from the LLM streaming response")


class WebSocketCitation(BaseModel):
    """WebSocket citation event."""

    indicator_code: str = Field(..., description="Cited indicator code")
    indicator_name: str = Field(..., description="Cited indicator name")


class WebSocketError(BaseModel):
    """WebSocket error event."""

    message: str = Field(..., description="Error description")
