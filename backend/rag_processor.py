"""
Procesador RAG para documentos PDF
Procesa PDFs de forma incremental y los almacena en ChromaDB
"""
import os
import json
from typing import List, Optional
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

# Configuración de DB_DIR con soporte para variable de entorno (Docker)
DB_DIR = os.getenv("CHROMA_DB_DIR")
if not DB_DIR:
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

class RAGProcessor:
    """Procesa documentos PDF y los almacena en ChromaDB de forma incremental"""
    
    def __init__(self, db_dir: str = DB_DIR):
        self.db_dir = db_dir
        self.embedding_function = SentenceTransformerEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=400
        )
        
        # Cargar o crear base de datos
        if os.path.exists(db_dir):
            self.db = Chroma(
                persist_directory=db_dir,
                embedding_function=self.embedding_function
            )
        else:
            self.db = None
    
    def process_document(self, doc_info: dict) -> dict:
        """
        Procesa un documento PDF y lo agrega a ChromaDB
        
        Args:
            doc_info: Diccionario con información del documento
                     (debe incluir: path, org_id, org_nombre, pais, id)
        
        Returns:
            dict con resultado del procesamiento
        """
        try:
            file_path = doc_info['path']
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            print(f"📄 Procesando {file_path}...")
            
            # Cargar PDF
            loader = PyMuPDFLoader(file_path)
            pages = loader.load()
            
            # Dividir en chunks
            chunks = self.text_splitter.split_documents(pages)
            print(f"✂️  Creados {len(chunks)} fragmentos")
            
            # Agregar metadata a cada chunk
            for chunk in chunks:
                chunk.metadata.update({
                    "org_id": doc_info['org_id'],
                    "org_nombre": doc_info['org_nombre'],
                    "pais": doc_info['pais'],
                    "documento_id": doc_info['id'],
                    "source": file_path
                })
            # Guardar en ChromaDB
            if not chunks:
                print("⚠️ No se generaron fragmentos de texto (PDF vacío o ilegible)")
                return {
                    "success": True,
                    "chunks_created": 0,
                    "pages_processed": len(pages),
                    "warning": "No text content found"
                }
            
            print(f"🧠 Creando embeddings y almacenando...")
            if self.db is None:
                # Primera vez, crear DB
                self.db = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embedding_function,
                    persist_directory=self.db_dir
                )
            else:
                # Agregar a DB existente
                self.db.add_documents(chunks)
            
            print(f"✅ Documento procesado exitosamente")
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "pages_processed": len(pages)
            }
            
        except Exception as e:
            print(f"❌ Error procesando documento: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_retriever(self, org_id: Optional[str] = None):
        """
        Obtiene un retriever para consultas RAG
        
        Args:
            org_id: Si se especifica, filtra solo documentos de esa organización
        
        Returns:
            Retriever configurado
        """
        if self.db is None:
            return None
        
        if org_id:
            # Filtrar por la organización específica O por documentos globales
            search_kwargs["filter"] = {
                "$or": [
                    {"org_id": org_id},
                    {"org_id": "global"}
                ]
            }
        
        return self.db.as_retriever(search_kwargs=search_kwargs)

    def search_hybrid(self, query: str, org_id: str, k_org: int = 15, k_global: int = 5):
        """
        Realiza una búsqueda híbrida asegurando documentos de la organización y globales.
        
        Args:
            query: Pregunta del usuario
            org_id: ID de la organización
            k_org: Número de documentos de la organización a recuperar (Aumentado para mejor contexto)
            k_global: Número de documentos globales a recuperar
            
        Returns:
            Lista combinada de documentos
        """
        if self.db is None:
            return []
            
        # 1. Búsqueda específica de la organización (usando MMR para diversidad/precisión)
        docs_org = self.db.max_marginal_relevance_search(
            query, 
            k=k_org,
            fetch_k=k_org * 4, # Analizar más candidatos
            filter={"org_id": org_id},
            lambda_mult=0.7 # Balancear relevancia vs diversidad (0.7 favorece relevancia)
        )
        
        # 2. Búsqueda global
        docs_global = self.db.similarity_search(
            query, 
            k=k_global,
            filter={"org_id": "global"}
        )
        
        # Combinar resultados
        return docs_org + docs_global
# Reload trigger
