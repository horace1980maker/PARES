from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
import os

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

embedding_function = SentenceTransformerEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': 'cpu'}
)

db = Chroma(
    persist_directory=DB_DIR, 
    embedding_function=embedding_function
)

org_id = "CECROPIA"
data = db.get(where={"org_id": org_id})

print(f"CECROPIA chunks: {len(data['ids'])}")
if len(data['ids']) > 0:
    sources = set(m.get('source') for m in data['metadatas'])
    print(f"Sources: {sources}")
else:
    # Check what orgs ARE there
    all_data = db.get()
    orgs = set(m.get('org_id') for m in all_data['metadatas'])
    print(f"Available Orgs in DB: {orgs}")
