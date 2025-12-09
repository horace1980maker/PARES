import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
print(f"Checking DB at: {DB_DIR}")

embedding_function = SentenceTransformerEmbeddings(
     model_name="paraphrase-multilingual-MiniLM-L12-v2",
     model_kwargs={'device': 'cpu'}
)

if os.path.exists(DB_DIR):
    db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_function)
    print(f"Total documents: {db._collection.count()}")
    
    # Peek at one doc
    res = db.get(limit=1)
    if res['metadatas']:
        print("Sample Metadata:", res['metadatas'][0])
        print("Org ID:", res['metadatas'][0].get("org_id"))
        print("Scope:", res['metadatas'][0].get("scope"))
else:
    print("DB directory does not exist.")
