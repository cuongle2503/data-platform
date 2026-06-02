"""Gemini client for RAG answer generation."""

import logging
import os
from typing import Any, Iterator

import google.generativeai as genai
from google.api_core.exceptions import InternalServerError, ResourceExhausted
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Strict system prompt for RAG
SYSTEM_PROMPT = """You are an expert economic data analyst for the World Bank.
You are helping a user with questions about global economic indicators.

INSTRUCTIONS:
1. Answer the user's question using ONLY the provided Context Data.
2. If the answer cannot be found in the Context Data, say "I don't have enough data to answer that question." Do not make up facts.
3. When you use data from an indicator, you MUST cite it using the format [IND:INDICATOR_CODE] where INDICATOR_CODE is the exact code provided in the context.
4. Format your answer using Markdown for readability (tables, bullet points, etc.).
5. Be concise but thorough. Focus on the data.
"""


class RAGClient:
    """Client for generating answers using Gemini."""

    def __init__(self, model_name: str = "gemini-2.5-pro"):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=self.api_key, transport="rest")
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
        )

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((ResourceExhausted, InternalServerError)),
    )
    def generate_answer(self, query: str, context: str) -> str:
        """Generate a complete answer based on query and context."""
        prompt = f"""
Context Data:
{context}

User Question: {query}
"""
        logger.info("Sending query to Gemini")
        response: Any = self.model.generate_content(prompt)
        return str(response.text)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((ResourceExhausted, InternalServerError)),
    )
    def generate_answer_stream(self, query: str, context: str) -> Iterator[str]:
        """Generate a streaming answer based on query and context."""
        prompt = f"""
Context Data:
{context}

User Question: {query}
"""
        logger.info("Sending streaming query to Gemini")
        response = self.model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
