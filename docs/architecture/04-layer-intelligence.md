# Layer 4 — Intelligence (RAG & Chatbot)

## Objectives & Components

The Intelligence layer enables natural-language interaction with the platform:

- Parse user queries
- Retrieve relevant indicators and docs via lexical + semantic search
- Call Gemini to produce grounded answers with citations

Core components:

- **FastAPI** (REST + WebSocket backend)
- **PostgreSQL + pgvector** (embeddings & search)
- **Gemini** (`text-embedding-004`, 2.0 Flash, 2.5 Pro)
- **Optional Neo4j** for data lineage graphs

## Lean RAG Pipeline

A lean RAG pipeline can be:

1. **Normalize the query** (lowercase, strip, map obvious indicator/country names)
2. **Lexical search** in PostgreSQL over `dim_indicators`, `dim_countries`, and doc metadata
3. **Semantic search** in `embeddings.economic_embeddings` with pgvector
4. **Assemble context** from `gold.fact_economic_indicators` and `raw_world_bank_docs_chunks`
5. **Call Gemini** with a strict system prompt to enforce use of provided context only
6. **Stream the answer** and citations back to the client via WebSocket

Neo4j can be added later to provide multi-hop lineage traversal for complex queries.

## Query Normalization

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class NormalizedQuery:
    original: str
    normalized: str
    country_codes: list[str]
    indicator_codes: list[str]
    year_range: tuple[int, int] | None

def normalize_query(query: str) -> NormalizedQuery:
    """
    Extract structured entities from natural language query.
    
    Examples:
    - "GDP của Việt Nam năm 2023" → country_codes=["VNM"], year_range=(2023, 2023)
    - "So sánh lạm phát Việt Nam và Thái Lan" → country_codes=["VNM", "THA"]
    """
    # Implementation: regex + keyword mapping + NER
    ...
```

## Lexical Search

```python
def lexical_search_indicators(query: str, limit: int = 10) -> list[dict]:
    """
    Full-text search over dim_indicators using PostgreSQL tsvector.
    """
    sql = """
    SELECT 
        indicator_code,
        indicator_name,
        category,
        unit,
        description,
        ts_rank(search_vector, plainto_tsquery('english', %s)) AS rank
    FROM gold.dim_indicators
    WHERE search_vector @@ plainto_tsquery('english', %s)
    ORDER BY rank DESC
    LIMIT %s
    """
    # Execute and return results
    ...
```

## Semantic Search

```python
def semantic_search_indicators(
    query_embedding: list[float], 
    k: int = 10
) -> list[dict]:
    """
    Vector similarity search using pgvector.
    """
    sql = """
    SELECT 
        ref_id,
        ref_type,
        metadata,
        1 - (embedding <=> %s::vector) AS similarity
    FROM embeddings.economic_embeddings
    WHERE ref_type = 'economic_indicator'
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """
    # Execute with query_embedding
    ...
```

## Context Assembly

```python
def assemble_context(
    normalized_query: NormalizedQuery,
    lexical_results: list[dict],
    semantic_results: list[dict]
) -> str:
    """
    Fetch actual data from fact table and format for LLM.
    """
    # Merge and deduplicate indicator_codes from both searches
    indicator_codes = set(...)
    
    # Query fact table
    sql = """
    SELECT 
        c.country_name,
        i.indicator_name,
        d.year,
        f.value,
        i.unit
    FROM gold.fact_economic_indicators f
    JOIN gold.dim_countries c ON f.country_key = c.country_key
    JOIN gold.dim_indicators i ON f.indicator_key = i.indicator_key
    JOIN gold.dim_dates d ON f.date_key = d.date_key
    WHERE i.indicator_code = ANY(%s)
      AND c.country_code = ANY(%s)
      AND d.year BETWEEN %s AND %s
    ORDER BY d.year DESC
    """
    
    # Format as markdown table or structured text
    context = format_as_markdown(results)
    return context
```

## Gemini Integration

```python
import google.generativeai as genai

def generate_answer(
    query: str,
    context: str,
    model: str = "gemini-2.0-flash"
) -> str:
    """
    Call Gemini with grounded context.
    """
    system_prompt = """
    You are an economic data assistant. Answer questions using ONLY the provided context.
    If the context doesn't contain the answer, say "I don't have that information."
    Always cite your sources using the format [IND:indicator_code:country_code:year].
    """
    
    prompt = f"""
    Context:
    {context}
    
    Question: {query}
    
    Answer:
    """
    
    model = genai.GenerativeModel(model, system_instruction=system_prompt)
    response = model.generate_content(prompt)
    return response.text
```

## Streaming Response

```python
from fastapi import WebSocket

async def stream_answer(
    websocket: WebSocket,
    query: str,
    session_id: str
):
    """
    Stream Gemini response token-by-token via WebSocket.
    """
    # 1. Normalize query
    normalized = normalize_query(query)
    
    # 2. Search
    query_embedding = await get_embedding(query)
    lexical = lexical_search_indicators(query)
    semantic = semantic_search_indicators(query_embedding)
    
    # 3. Assemble context
    context = assemble_context(normalized, lexical, semantic)
    
    # 4. Stream from Gemini
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(
        f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:",
        stream=True
    )
    
    for chunk in response:
        await websocket.send_json({
            "type": "token",
            "data": chunk.text
        })
    
    # 5. Send citations
    citations = extract_citations(context)
    await websocket.send_json({
        "type": "citation",
        "refs": citations
    })
    
    await websocket.send_json({
        "type": "done",
        "session_id": session_id
    })
```

## Citation Format

Citations follow a structured format:

- **Indicator**: `IND:indicator_code:country_code:year`
  - Example: `IND:NY.GDP.MKTP.CD:VNM:2023`
- **Document**: `DOC:doc_id`
  - Example: `DOC:doc_12345`

## Future Enhancements (Deferred)

- **Neo4j**: Multi-hop lineage queries ("What indicators depend on GDP?")
- **LangGraph**: Complex multi-step reasoning workflows
- **LlamaIndex**: Advanced RAG orchestration
- **Redis caching**: Cache frequent queries and embeddings
- **Query rewriting**: Use LLM to expand/clarify ambiguous queries
