import os
import json
import time
from datetime import datetime
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from tqdm import tqdm

# Configuration
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "documents"))
DB_DIR = os.getenv("CHROMA_DB_DIR")
if not DB_DIR:
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
METADATA_FILE = os.path.join(DOCS_DIR, "metadata.json")

def get_file_size_mb(file_path):
    """Retorna el tamaño del archivo en MB"""
    return os.path.getsize(file_path) / (1024 * 1024)

def update_metadata_json(documents_found):
    """
    Actualiza el archivo metadata.json con los documentos encontrados en el disco.
    Mantiene la metadata existente si es posible, o crea nueva.
    """
    existing_docs = []
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing_docs = data.get("documentos", [])
        except Exception as e:
            print(f"⚠️ Error leyendo metadata existente: {e}")

    # Crear mapa de documentos existentes por path para búsqueda rápida
    existing_map = {doc["path"]: doc for doc in existing_docs}
    
    new_docs_list = []
    
    for doc_info in documents_found:
        path = doc_info["path"]
        if path in existing_map:
            # Mantener metadata existente (preservar ID y fecha si ya existen)
            new_docs_list.append(existing_map[path])
        else:
            # Crear nueva entrada
            file_stats = os.stat(path)
            creation_time = datetime.fromtimestamp(file_stats.st_ctime).isoformat()
            
            # Determinar ID y nombre de org
            org_id = doc_info['org_id']
            org_nombre = org_id if org_id != "global" else "Conocimiento Global (NbS)"
            
            new_entry = {
                "id": f"{org_id}_{int(file_stats.st_ctime)}",
                "filename": os.path.basename(path),
                "original_filename": os.path.basename(path),
                "path": path,
                "pais": "global" if org_id == "global" else "desconocido",
                "org_id": org_id,
                "org_nombre": org_nombre,
                "fecha_subida": creation_time,
                "procesado_rag": False # Se marcará True tras ingesta exitosa
            }
            new_docs_list.append(new_entry)
            
    # Guardar actualizado
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"documentos": new_docs_list}, f, ensure_ascii=False, indent=2)
    
    return new_docs_list

def ingest_documents():
    """
    1. Escanea documents/orgs/{org_id}/*.pdf y documents/global/*.pdf
    2. Actualiza metadata.json
    3. Procesa documentos para RAG con barra de progreso
    """
    start_time = time.time()
    
    # Ensure directories exist
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        
    orgs_dir = os.path.join(DOCS_DIR, "orgs")
    global_dir = os.path.join(DOCS_DIR, "global")
    
    for d in [orgs_dir, global_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    print(f"🔍 Escaneando directorios de documentos...")
    
    found_documents = []
    pdf_files_to_process = []
    
    # 1. Escanear Organizaciones
    if os.path.exists(orgs_dir):
        for org_id in os.listdir(orgs_dir):
            org_path = os.path.join(orgs_dir, org_id)
            if os.path.isdir(org_path):
                for file in os.listdir(org_path):
                    if file.lower().endswith(".pdf"):
                        file_path = os.path.join(org_path, file)
                        found_documents.append({
                            "path": file_path,
                            "org_id": org_id
                        })
                        pdf_files_to_process.append(file_path)

    # 2. Escanear Global
    if os.path.exists(global_dir):
        for file in os.listdir(global_dir):
            if file.lower().endswith(".pdf"):
                file_path = os.path.join(global_dir, file)
                found_documents.append({
                    "path": file_path,
                    "org_id": "global"
                })
                pdf_files_to_process.append(file_path)

    if not found_documents:
        print("⚠️ No se encontraron documentos PDF en documents/orgs/ ni documents/global/.")
        return

    # Actualizar metadata.json
    current_metadata = update_metadata_json(found_documents)
    
    # Filtrar archivos ya procesados
    processed_paths = {doc["path"] for doc in current_metadata if doc.get("procesado_rag", False)}
    files_to_ingest = [f for f in pdf_files_to_process if f not in processed_paths]
    
    total_new_docs = len(files_to_ingest)
    
    if total_new_docs == 0:
        print(f"✅ Todos los documentos ({len(pdf_files_to_process)}) ya están actualizados.")
        return

    # Calcular tamaño total
    total_size_mb = sum(get_file_size_mb(f) for f in files_to_ingest)
    
    print(f"\n🚀 Iniciando ingesta de {total_new_docs} nuevos documentos ({total_size_mb:.2f} MB)")
    print("=" * 60)

    all_chunks = []
    processed_count = 0
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, 
        chunk_overlap=300
    )

    # Barra de progreso para procesamiento de archivos
    with tqdm(total=total_new_docs, desc="📄 Procesando PDFs", unit="doc") as pbar:
        for file_path in files_to_ingest:
            file_name = os.path.basename(file_path)
            file_size = get_file_size_mb(file_path)
            
            # Actualizar descripción de barra
            pbar.set_postfix_str(f"{file_name[:20]}... ({file_size:.1f}MB)")
            
            try:
                loader = PyMuPDFLoader(file_path)
                docs = loader.load()
                
                # Determinar org_id
                if "global" in os.path.normpath(file_path).split(os.sep):
                    org_id = "global"
                else:
                    # path es .../orgs/org_id/file.pdf
                    path_parts = os.path.normpath(file_path).split(os.sep)
                    # Buscar 'orgs' y tomar el siguiente
                    try:
                        idx = path_parts.index("orgs")
                        org_id = path_parts[idx + 1]
                    except ValueError:
                        org_id = "unknown"

                # Buscar ID del documento en metadata
                doc_entry = next((d for d in current_metadata if d["path"] == file_path), None)
                doc_id = doc_entry["id"] if doc_entry else "unknown"

                for doc in docs:
                    # Inyectar nombre del archivo en el contenido para mejorar recuperación
                    doc.page_content = f"Documento: {file_name}\n\n{doc.page_content}"
                    
                    doc.metadata.update({
                        "org_id": org_id,
                        "source": file_path,
                        "documento_id": doc_id,
                        "filename": file_name
                    })
                
                file_chunks = text_splitter.split_documents(docs)
                if file_chunks:
                    all_chunks.extend(file_chunks)
                    processed_count += 1
                
            except Exception as e:
                print(f"\n❌ Error en {file_name}: {e}")
            
            pbar.update(1)

    if not all_chunks:
        print("\n⚠️ No se generaron fragmentos para almacenar.")
        return

    print(f"\n🧠 Generando embeddings para {len(all_chunks)} fragmentos...")
    
    # Inicializar modelo de embeddings
    embedding_function = SentenceTransformerEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    
    # Guardar en ChromaDB con barra de progreso (simulada por lotes si es posible, o general)
    # Chroma no tiene barra de progreso nativa en add_documents, así que lo haremos por lotes
    batch_size = 100
    total_chunks = len(all_chunks)
    
    # Inicializar DB
    db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_function)
    
    with tqdm(total=total_chunks, desc="💾 Guardando en DB", unit="chunk") as pbar:
        for i in range(0, total_chunks, batch_size):
            batch = all_chunks[i:i + batch_size]
            db.add_documents(batch)
            pbar.update(len(batch))
    
    # Actualizar metadata como procesado
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for doc in data["documentos"]:
        if doc["path"] in files_to_ingest:
            doc["procesado_rag"] = True
            
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    elapsed_time = time.time() - start_time
    print(f"\n✅ ¡Ingesta completada en {elapsed_time:.2f} segundos!")
    print(f"   - Archivos procesados: {processed_count}")
    print(f"   - Fragmentos almacenados: {total_chunks}")
    print(f"   - Base de datos: {DB_DIR}")

if __name__ == "__main__":
    print("=" * 60)
    print("🌿 CATIE PARES - Sistema de Ingesta de Documentos")
    print("=" * 60)
    ingest_documents()
