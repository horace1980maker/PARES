import os
import argparse
import json
import time
import hashlib
from datetime import datetime
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from tqdm import tqdm

# Supported file extensions
SUPPORTED_EXTENSIONS = (".pdf", ".docx")

def get_loader(file_path: str):
    """Returns the appropriate document loader based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return PyMuPDFLoader(file_path)
    elif ext == ".docx":
        return Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

# Configuration
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "documents"))
DB_DIR = os.getenv("CHROMA_DB_DIR")
if not DB_DIR:
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

# Save manifest in the DB directory so it persists with the vector store
MANIFEST_FILE = os.path.join(DB_DIR, "manifest.json")
METADATA_FILE = os.path.join(DOCS_DIR, "metadata.json")

# Constants
# Revertimos a un modelo más ligero para evitar "Killed" (OOM) en el servidor
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 1800
CHUNK_OVERLAP = 300

def calculate_file_hash(file_path):
    """Calculates MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_manifest(manifest):
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

def determine_scope_and_org(file_path):
    """
    Determines scope ('org' or 'global') and org_id based on file path.
    Assumes structure: 
    .../documents/orgs/{ORG_ID}/file.pdf -> scope=org, org_id={ORG_ID}
    .../documents/global/file.pdf -> scope=global, org_id=GLOBAL
    """
    path_parts = os.path.normpath(file_path).split(os.sep)
    
    if "global" in path_parts:
        return "global", "GLOBAL"
    
    try:
        # Find 'orgs' and take the next folder as org_id
        if "orgs" in path_parts:
            idx = path_parts.index("orgs")
            org_id = path_parts[idx + 1]
            return "org", org_id
    except IndexError:
        pass
        
    return "global", "UNKNOWN" # Fallback

def ingest_documents(clear_manifest=False):
    print(f"[START] Starting Ingestion Pipeline")
    if clear_manifest:
        print(f"   - [RESET] Clearing existing manifest and DATABASE as requested")
        if os.path.exists(MANIFEST_FILE):
            os.remove(MANIFEST_FILE)
        if os.path.exists(DB_DIR):
            import shutil
            print(f"   - [INFO] Emptying database directory: {DB_DIR}")
            for filename in os.listdir(DB_DIR):
                file_path = os.path.join(DB_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"   - [WARN] Failed to delete {file_path}. Reason: {e}")
            print(f"   - [INFO] Database directory emptied.")
            
    # Try to use HuggingFaceEmbeddings
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        embedding_function = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print(f"   - [INFO] Using HuggingFaceEmbeddings (Normalized: True)", flush=True)
    except ImportError:
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        embedding_function = SentenceTransformerEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        print(f"   - [WARN] Using Fallback SentenceTransformerEmbeddings", flush=True)
    
    print(f"   - Chunk Size: {CHUNK_SIZE} / Overlap: {CHUNK_OVERLAP}", flush=True)
    print(f"   - DB Path: {DB_DIR}", flush=True)
    print("=" * 60, flush=True)

    # 1. Setup Directories
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        
    orgs_dir = os.path.join(DOCS_DIR, "orgs")
    global_dir = os.path.join(DOCS_DIR, "global")
    
    # 2. Scan Files
    found_files = []
    
    # Scan Orgs - recursively search all subdirectories
    if os.path.exists(orgs_dir):
        for org_id in os.listdir(orgs_dir):
            org_path = os.path.join(orgs_dir, org_id)
            if os.path.isdir(org_path):
                # Use os.walk to recursively find all supported documents
                for root, dirs, files in os.walk(org_path):
                    for file in files:
                        if file.lower().endswith(SUPPORTED_EXTENSIONS):
                            found_files.append(os.path.join(root, file))


    # Scan Global
    if os.path.exists(global_dir):
        for file in os.listdir(global_dir):
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                found_files.append(os.path.join(global_dir, file))

    if not found_files:
        print("[WARN] No supported documents found (PDF, DOCX).")
        return

    # 3. Incremental Logic
    manifest = load_manifest()
    files_to_process = []
    
    print(f"[SCAN] Scanning {len(found_files)} files for changes...")
    
    for file_path in found_files:
        current_hash = calculate_file_hash(file_path)
        stored_hash = manifest.get(file_path)
        
        if current_hash != stored_hash:
            files_to_process.append(file_path)
            # manifest[file_path] = current_hash # MOVED: Only update on success

    if not files_to_process:
        print("[OK] All files are up to date. No new ingestion needed.")
        return

    print(f"[PROCESS] Processing {len(files_to_process)} new/modified files...")

    # 4. Initialize Components
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        embedding_function = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    except ImportError:
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        embedding_function = SentenceTransformerEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    # Connect to DB
    db = Chroma(
        persist_directory=DB_DIR, 
        embedding_function=embedding_function
    )

    # 5. Process Files
    for file_path in tqdm(files_to_process, desc="Ingesting"):
        try:
            filename = os.path.basename(file_path)
            
            # Setup Metadata
            scope, org_id = determine_scope_and_org(file_path)
            
            # Cleanup existing chunks for this file (to avoid duplicates on re-ingest)
            # Note: Chroma delete by where metadata is efficient
            try:
                # Método compatible con LangChain/Chroma moderno
                existing_docs = db.get(where={"source": filename})
                if existing_docs and existing_docs['ids']:
                     db.delete(existing_docs['ids'])
                # UPDATE: Let's assume standard behavior: if we re-add, we might duplicate.
                # Correct way in langchain:
                # ids_to_del = db.get(where={"source": filename})['ids']
                # if ids_to_del: db.delete(ids_to_del)
                
                existing = db.get(where={"source": filename})
                if existing and existing['ids']:
                     db.delete(existing['ids'])
                     
            except Exception as e:
                print(f"   [WARN] Warning cleaning up old chunks for {filename}: {e}")

            # Load & Split - use appropriate loader based on file type
            loader = get_loader(file_path)
            docs = loader.load()
            
            chunks = text_splitter.split_documents(docs)
            
            if not chunks:
                print(f"   [WARN] Skipped {filename} (empty)")
                continue

            # Enrich Metadata
            for chunk in chunks:
                chunk.metadata.update({
                    "source": filename, # Simple filename for easy filtering
                    "full_path": file_path,
                    "scope": scope,
                    "org_id": org_id,
                    "page": chunk.metadata.get("page", 0) + 1 # 1-based page
                })

            # Add to DB
            if chunks:
                print(f"   [INFO] Adding {len(chunks)} chunks for {filename} (Org: {org_id})")
                db.add_documents(chunks)
                print(f"   [OK] {filename} stored successfully")
            else:
                print(f"   [WARN] No chunks generated for {filename}")
            
            # 6. Mark as processed on success
            manifest[file_path] = calculate_file_hash(file_path)
            save_manifest(manifest) # Save incrementally for safety
            
        except Exception as e:
            print(f"[ERROR] Error processing {file_path}: {e}")
            # Revert manifest change for this file so we try again next time?
            # For simplicity, we won't resort complex revert logic here 
            # but in production we should.
            
    # 7. Final Manifest Save
    save_manifest(manifest)
    print(f"\n[OK] Ingestion Complete. Manifest updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB")
    parser.add_argument("--clear", "--reset", action="store_true", help="Clear manifest and re-ingest all files")
    args = parser.parse_args()
    
    ingest_documents(clear_manifest=args.clear)
