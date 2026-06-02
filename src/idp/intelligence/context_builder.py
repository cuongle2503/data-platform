"""Context builder for RAG system."""


def build_context(indicators: list[dict], timeseries_data: list[dict]) -> str:
    """
    Build markdown context from indicators and timeseries data.
    Formats data into tables for the LLM to read easily.
    """
    if not indicators and not timeseries_data:
        return "No data available."

    context_parts = []

    if indicators:
        context_parts.append("### Available Indicators")
        for ind in indicators:
            code = ind.get("indicator_code", "")
            name = ind.get("indicator_name", "")
            desc = ind.get("description", "") or "No description"
            context_parts.append(f"- **{code}** ({name}): {desc}")

    if timeseries_data:
        context_parts.append("\n### Economic Data")

        # Format as markdown table manually
        if timeseries_data:
            # Determine columns from first row
            first_row = timeseries_data[0]
            cols = ["country_code", "indicator_code", "year", "value"]
            available_cols = [c for c in cols if c in first_row]

            # Add any extra columns
            for c in first_row:
                if c not in available_cols:
                    available_cols.append(c)

            # Build table header
            header = "| " + " | ".join(available_cols) + " |"
            separator = "| " + " | ".join(["---"] * len(available_cols)) + " |"
            context_parts.append(header)
            context_parts.append(separator)

            # Build table rows
            for row in timeseries_data:
                values = [str(row.get(col, "")) for col in available_cols]
                row_str = "| " + " | ".join(values) + " |"
                context_parts.append(row_str)

    return "\n".join(context_parts)
