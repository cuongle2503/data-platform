# API Specification

## Base URL & Envelope

- **Base**: `http://<server>:8000`
- **Prefix**: `/api/v1`
- **Docs**: `/docs` (OpenAPI)

### Common Response Envelope

```json
{
  "data": {},
  "meta": {
    "total": 320,
    "page": 1,
    "page_size": 50
  },
  "error": null
}
```

### Error Response

```json
{
  "data": null,
  "meta": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Country code 'XYZ' not found"
  }
}
```

---

## Countries API

### GET `/countries`
Retrieve a list of countries.

**Response**
```json
{
  "data": [
    {
      "country_code": "VNM",
      "country_name": "Vietnam",
      "region": "East Asia & Pacific",
      "income_group": "Lower-middle",
      "is_asean": true,
      "is_primary": true
    }
  ],
  "meta": { "total": 10, "page": 1, "page_size": 10 },
  "error": null
}
```

### GET `/countries/{country_code}`
Retrieve details for a specific country by ISO3 code. Returns 404 if not found.

---

## Indicator Catalog & Metadata

### GET `/indicators/catalog`
**Query Params (optional)**: `category`, `source_system`, `frequency`, `q` (free-text search)

**Response**
```json
{
  "data": [
    {
      "indicator_code": "NY.GDP.MKTP.CD",
      "indicator_name": "GDP (current US$)",
      "category": "gdp",
      "unit": "USD",
      "frequency": "annual",
      "description": "Gross Domestic Product at current US dollars",
      "source_system": "world_bank"
    }
  ],
  "meta": { "total": 32, "page": 1, "page_size": 32 },
  "error": null
}
```

### GET `/indicators/{indicator_code}/metadata`
Retrieve metadata for a specific indicator. 

**Query Params**: `source_system` (default `world_bank`)

---

## Time Series & Analytics

### GET `/timeseries`
Return time-series rows for 1+ indicators × 1+ countries.

**Query Params**: 
- `country_code`: string or `all` (required)
- `indicator_codes`: comma-separated string (required)
- `source_system`, `start_year`, `end_year`, `page`, `page_size`

**Response**
```json
{
  "data": [
    {
      "country_code": "VNM",
      "country_name": "Vietnam",
      "indicator_code": "NY.GDP.MKTP.CD",
      "indicator_name": "GDP (current US$)",
      "source_system": "world_bank",
      "year": 2020,
      "value": 340000000000.0,
      "loaded_at": "2026-05-18T06:00:00Z"
    }
  ],
  "meta": { "total": 25, "page": 1, "page_size": 50 },
  "error": null
}
```

### GET `/timeseries/matrix`
Return a year × country matrix for a single indicator.

**Query Params**: `indicator_code` (required), `country_codes`, `start_year`, `end_year`

### GET `/snapshot/economy`
Summary of key indicators for a given country/year.

**Query Params**: `country_code` (required), `year` (required)

### GET `/compare/countries`
Compare an indicator across multiple countries in a single year.

**Query Params**: `indicator_code` (required), `year` (required), `country_codes` (optional)

---

## Search & Embeddings APIs

### GET `/search`
Unified search over indicators and documents.

**Query Params**: `q` (required), `limit` (default 10), `type` (`indicators`, `documents`, `all`)

**Response**
```json
{
  "data": [
    {
      "type": "indicator",
      "id": "NY.GDP.MKTP.CD",
      "title": "GDP (current US$)",
      "score": 0.92,
      "source": "World Bank"
    },
    {
      "type": "document",
      "id": "doc_12345",
      "title": "Vietnam Economic Outlook 2024",
      "score": 0.87,
      "pdf_url": "https://..."
    }
  ],
  "meta": { "total": 2, "page": 1, "page_size": 10 },
  "error": null
}
```

### GET `/search/indicators`
Indicator-only search (wraps `dim_indicators` + embeddings).

### GET `/search/documents`
Document-only search.

### GET `/embeddings/similar/indicators`
**Query Params**: `indicator_code` (required), `k` (default 10)

Returns semantically similar indicators.

### GET `/embeddings/similar/documents`
Analogous to indicators, keyed by `doc_id`.

---

## Chatbot APIs

### WebSocket — `WS /chat`

**Client → Server**
```json
{
  "type": "query",
  "session_id": "uuid-optional",
  "query": "GDP của Việt Nam năm 2023?",
  "model": "gemini-2.0-flash"
}
```

**Server → Client (streaming)**
```json
{"type": "token", "data": "GDP"}
{"type": "token", "data": " của"}
{"type": "citation", "refs": ["IND:NY.GDP.MKTP.CD:VNM:2023", "DOC:doc_12345"]}
{"type": "done", "tokens_used": 512, "session_id": "uuid"}
```

### REST fallback — `POST /chat`

**Request**
```json
{
  "query": "GDP của Việt Nam năm 2023?",
  "session_id": "uuid-optional",
  "model": "gemini-2.0-flash",
  "stream": false
}
```

**Response**
```json
{
  "data": {
    "session_id": "uuid",
    "response": "GDP của Việt Nam năm 2023 đạt 433.7 tỷ USD...",
    "citations": [
      {
        "ref": "IND:NY.GDP.MKTP.CD:VNM:2023",
        "type": "indicator"
      }
    ],
    "tokens_used": 512,
    "follow_up_questions": [
      "Lạm phát của Việt Nam năm 2023 là bao nhiêu?"
    ]
  },
  "meta": null,
  "error": null
}
```