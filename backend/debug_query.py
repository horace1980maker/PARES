
import os
import sys

# Mock Env
os.environ["CHROMA_DB_DIR"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

# Import RAG
try:
    from rag_processor import RAGProcessor
except ImportError:
    # Add current dir to path
    sys.path.append(os.path.dirname(__file__))
    from rag_processor import RAGProcessor

def test_query():
    print("Initializing RAG Processor...")
    rag = RAGProcessor()
    
    query = "mision"
    org_id = "TIERRA VIVA"
    
    print(f"\n--- Testing Query: '{query}' for Org: '{org_id}' ---")
    results = rag.search_tiered(query, org_id)
    
    print(f"\nFound {len(results)} results.")
    for i, doc in enumerate(results):
        print(f"[{i+1}] {doc.metadata.get('source')} (Tier: {doc.metadata.get('retrieval_tier')})")
        print(f"    Preview: {doc.page_content[:100]}...")

if __name__ == "__main__":
    test_query()
