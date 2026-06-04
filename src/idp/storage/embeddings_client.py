"""Gemini embeddings client for generating text embeddings."""

import logging
from typing import cast

import google.generativeai as genai
from google.api_core.exceptions import InternalServerError, ResourceExhausted
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from idp.common.config import get_settings

logger = logging.getLogger(__name__)


class GeminiEmbeddingsClient:
    """Client for generating text embeddings using Google's Gemini API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "models/text-embedding-004",
    ):
        self.api_key = api_key or get_settings().gemini.api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required (pass it or set it in .env)")

        genai.configure(api_key=self.api_key, transport="rest")
        self.model_name = model_name

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((ResourceExhausted, InternalServerError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying embedding generation due to API error. Attempt {retry_state.attempt_number}"
        ),
    )
    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        """
        Generate embedding for a single string.

        Args:
            text: Text to embed
            task_type: Type of task for the embedding model

        Returns:
            List of floats representing the embedding vector
        """
        result = genai.embed_content(model=self.model_name, content=text, task_type=task_type)
        return result["embedding"]

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((ResourceExhausted, InternalServerError)),
    )
    def generate_embeddings_batch(
        self, texts: list[str], task_type: str = "retrieval_document"
    ) -> list[list[float]]:
        """
        Generate embeddings for a batch of strings.

        Args:
            texts: List of strings to embed
            task_type: Type of task for the embedding model

        Returns:
            List of embedding vectors (lists of floats)
        """
        if not texts:
            return []

        result = genai.embed_content(model=self.model_name, content=texts, task_type=task_type)
        embeddings = result["embedding"]
        # API returns list[list[float]] for batch, list[float] for single
        if texts and isinstance(embeddings[0], (int, float)):
            return [embeddings]
        return cast(list[list[float]], embeddings)
