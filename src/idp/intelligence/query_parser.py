"""Query parsing and entity extraction for RAG."""

import re


def normalize_query(query: str) -> str:
    """Normalize query by stripping and lowering."""
    return query.strip().lower()


def extract_entities(query: str) -> dict[str, list]:
    """
    Extract relevant entities (country codes, years) from a query.
    Simple regex-based extraction for now.
    """
    # Look for 3 uppercase letters that might be ISO country codes
    country_codes = list(set(re.findall(r"\b[A-Z]{3}\b", query)))

    # Look for 4-digit years between 1900 and 2100
    years_str = set(re.findall(r"\b(19[0-9]{2}|20[0-9]{2})\b", query))
    years = sorted([int(y) for y in years_str])

    return {
        "country_codes": country_codes,
        "years": years,
    }
