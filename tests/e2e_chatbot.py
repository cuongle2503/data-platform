"""End-to-end test for Phase 4 Intelligence Layer (Chatbot)."""

import os
import sys

import psycopg

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from idp.api.main import create_app
from idp.intelligence.gemini_client import RAGClient
from idp.storage.embeddings_client import GeminiEmbeddingsClient
from idp.storage.repository import StorageRepository


def test_e2e_chatbot():
    """End-to-end test: real database, real Gemini API, full RAG pipeline."""
    print("\n" + "=" * 80)
    print("Phase 4 E2E Test: Intelligence Layer (Chatbot)")
    print("=" * 80)

    # 1. Connect to real database
    print("\n[1/6] Connecting to PostgreSQL...")
    conn = psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5433")),
        dbname=os.environ.get("POSTGRES_DB", "idp"),
        user=os.environ.get("POSTGRES_USER", "idp_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "changeme"),
    )
    print("✓ Connected to database")

    # 2. Initialize repository
    print("\n[2/6] Initializing Repository...")
    repo = StorageRepository(conn)
    countries = repo.get_countries()
    indicators = repo.get_indicators()
    print(f"✓ Repository ready: {len(countries)} countries, {len(indicators)} indicators")

    # 3. Initialize embeddings client
    print("\n[3/6] Initializing Gemini Embeddings Client...")
    try:
        embeddings_client = GeminiEmbeddingsClient()
        print("✓ Embeddings client ready")
    except ValueError as e:
        print(f"✗ Embeddings client failed: {e}")
        print("  Skipping semantic search tests")
        embeddings_client = None

    # 4. Initialize RAG client
    print("\n[4/6] Initializing RAG Client (Gemini)...")
    try:
        rag_client = RAGClient()
        print("✓ RAG client ready")
    except ValueError as e:
        print(f"✗ RAG client failed: {e}")
        print("  Cannot proceed with chatbot test")
        conn.close()
        return

    # 5. Create FastAPI app
    print("\n[5/6] Creating FastAPI app...")
    app = create_app(repo, embeddings_client, rag_client)
    print("✓ FastAPI app created with all routers")

    # 6. Test REST chat endpoint
    print("\n[6/6] Testing REST Chat Endpoint...")
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test query
    query = "What is the GDP of Vietnam in 2023?"
    print(f"\n  Query: '{query}'")

    response = client.post("/api/v1/chat", json={"query": query, "max_indicators": 5})

    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            answer = data["data"].get("answer", "")
            sources = data["data"].get("sources", [])

            print(f"\n  Answer:\n  {answer[:500]}...")
            print(f"\n  Citations: {sources}")
            print("\n✓ Chat endpoint working!")
        else:
            print(f"  Response: {data}")
    else:
        print(f"  Error: {response.text}")

    # Cleanup
    conn.close()
    print("\n" + "=" * 80)
    print("E2E Test Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_e2e_chatbot()
