"""
Procesador RAG Híbrido por Niveles (Tiered Hybrid RAG)
Implementa búsqueda vectorial (Chroma) + palabras clave (BM25)
y estrategia de recuperación por niveles (Org > Global).
"""
import os
import time
import logging
from typing import List, Optional, Dict, Any
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Configuración de DB_DIR
DB_DIR = os.getenv("CHROMA_DB_DIR")
if not DB_DIR:
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

class RAGProcessor:
    def __init__(self, db_dir: str = DB_DIR):
        self.db_dir = db_dir
        # Use HuggingFaceEmbeddings with explicit settings to avoid meta tensor error
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embedding_function = HuggingFaceEmbeddings(
                model_name="paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("[INFO] RAG: Using HuggingFaceEmbeddings")
        except ImportError:
            from langchain_community.embeddings import SentenceTransformerEmbeddings
            self.embedding_function = SentenceTransformerEmbeddings(
                model_name="paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'}
            )
            print("[WARN] RAG: Using Fallback SentenceTransformerEmbeddings")
        
        # Inicializar ChromaDB (Vector Store)
        if os.path.exists(db_dir):
            self.db = Chroma(
                persist_directory=db_dir,
                embedding_function=self.embedding_function
            )
            print("[OK] ChromaDB cargado correctamente.")
            self._init_bm25()
        else:
            self.db = None
            self.bm25 = None
            print("[WARN] Base de datos no encontrada. Ejecute ingest.py primero.")

    def _init_bm25(self):
        """Inicializa BM25 cargando documentos de Chroma (en memoria)"""
        try:
            print("[INFO] Inicializando indice BM25 (esto puede tardar unos segundos)...")
            # Recuperar TODOS los documentos para crear índice invertido
            # NOTA: En producción con millones de docs esto no escala.
            # Para esete proyecto (<10k chunks) es aceptable.
            all_docs = self.db.get()['documents']
            all_metadatas = self.db.get()['metadatas']
            
            docs_objects = []
            for text, meta in zip(all_docs, all_metadatas):
                docs_objects.append(Document(page_content=text, metadata=meta))
                
            if docs_objects:
                self.bm25 = BM25Retriever.from_documents(docs_objects)
                self.bm25.k = 10  # Base retrieval count
                print(f"[OK] BM25 inicializado con {len(docs_objects)} fragmentos.")
            else:
                self.bm25 = None
                print("[WARN] No hay documentos para BM25.")
        except Exception as e:
            print(f"[ERROR] Error inicializando BM25: {e}")
            self.bm25 = None

    def search_tiered(self, query: str, org_id: str) -> List[Document]:
        """
        Ejecuta la estrategia 'Tiered Hybrid Retrieval':
        1. Tier 1: Documentos de la organización (Alta prioridad)
        2. Tier 2: Documentos globales (Soporte)
        """
        if not self.db:
            return []

        results = []
        
        # --- TIER 1: Organización (Priority) ---
        logger.info(f"RAG: Searching Tier 1 (Org: {org_id})...")
        tier1_docs = self._hybrid_search(
            query, 
            k=10, 
            filter_dict={"org_id": org_id}
        )
        for d in tier1_docs:
            d.metadata['retrieval_tier'] = 'Tier 1 (Org)'
        results.extend(tier1_docs)

        # --- TIER 2: Global (Support) ---
        logger.info(f"RAG: Searching Tier 2 (Global)...")
        tier2_docs = self._hybrid_search(
            query, 
            k=3, 
            filter_dict={"scope": "global"}
        )
        for d in tier2_docs:
            d.metadata['retrieval_tier'] = 'Tier 2 (Global)'
        results.extend(tier2_docs)
        
        return results

    def _hybrid_search(self, query: str, k: int, filter_dict: Dict[str, Any]) -> List[Document]:
        """
        Realiza búsqueda híbrida (Vector + BM25) y filtra resultados.
        Como BM25Retriever de LangChain no soporta filtros nativos eficientes pre-query,
        hacemos:
        1. Vector Search con filtro (Chroma)
        2. BM25 Search global -> Filtrar en Python
        3. Combinar (Dedup)
        """
        # 1. Vector Search (Semantic) - Force Diversity with MMR
        vector_docs = self.db.max_marginal_relevance_search(
            query,
            k=k,
            fetch_k=k*4,
            filter=filter_dict,
            lambda_mult=0.6 # 0.6 = balanceado tirando a semántico
        )
        
        # 2. Keyword Search (BM25)
        bm25_docs = []
        if self.bm25:
            # Recuperamos más candidatos para tener margen tras filtrar
            raw_bm25 = self.bm25.invoke(query)
            
            # Filtrado manual de BM25
            for doc in raw_bm25:
                match = True
                for key, val in filter_dict.items():
                    if doc.metadata.get(key) != val:
                        match = False
                        break
                if match:
                    bm25_docs.append(doc)
            
            # Cortar a k
            bm25_docs = bm25_docs[:k]

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score(d) = 1 / (rank + k_const) + 1 / (rank + k_const)
        rrf_k = 60 # Constante estándar para RRF
        doc_scores = {}
        doc_map = {} # uid -> Document object

        # Procesar rankings Vectoriales
        for rank, doc in enumerate(vector_docs):
            uid = f"{doc.metadata.get('source')}_{hash(doc.page_content)}"
            doc_map[uid] = doc
            if uid not in doc_scores:
                doc_scores[uid] = 0.0
            doc_scores[uid] += 1.0 / (rank + rrf_k)

        # Procesar rankings BM25
        for rank, doc in enumerate(bm25_docs):
            uid = f"{doc.metadata.get('source')}_{hash(doc.page_content)}"
            # Si el documento no estaba en vector search, añadirlo
            if uid not in doc_map:
                doc_map[uid] = doc
                doc_scores[uid] = 0.0
            doc_scores[uid] += 1.0 / (rank + rrf_k)

        # Ordenar por puntaje RRF descendente
        sorted_uids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
        
        # Construir resultado final
        final_results = []
        for uid in sorted_uids:
            final_results.append(doc_map[uid])

        return final_results[:k] # Retornar top k combinados
