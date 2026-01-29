from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import csv
import glob
from dotenv import load_dotenv
import logging

# Defensive Imports to prevent crash on startup
IMPORT_ERRORS = []

try:
    from document_manager import DocumentManager
except ImportError as e:
    IMPORT_ERRORS.append(str(e))
    DocumentManager = None

try:
    from rag_processor import RAGProcessor
except ImportError as e:
    IMPORT_ERRORS.append(str(e))
    RAGProcessor = None

try:
    from docx_utils import create_docx_from_markdown
except ImportError as e:
    IMPORT_ERRORS.append(str(e))
    create_docx_from_markdown = None

# Configure logging - force output immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True  # Override any existing config
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Keyword detection for filtering CSV data based on question
TOPIC_KEYWORDS = {
    "ecosistemas": ["ecosistema", "ecosistemas", "ecosystem", "bosque", "bosques", "manglar", "humedal", "páramo"],
    "amenazas": ["amenaza", "amenazas", "threat", "riesgo", "peligro", "cambio climático", "deforestación", "sequía", "inundación"],
    "servicios": ["servicio ecosistémico", "servicios ecosistémicos", "SE", "provisión", "regulación", "cultural"],
    "medios_vida": ["medio de vida", "medios de vida", "livelihood", "agricultura", "ganadería", "turismo", "artesanía", "pesca"],
    "conflictos": ["conflicto", "conflictos", "conflict", "tensión", "disputa"]
}


def detect_question_topics(question: str) -> list:
    """Detect which topics the question is about based on keywords"""
    question_lower = question.lower()
    detected = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in question_lower:
                detected.append(topic)
                break
    return detected if detected else ["all"]  # Default to all if no specific topic

# Map organization names to folder names
ORG_NAME_TO_FOLDER = {
    # Colombia
    "Corporación Biocomercio": "Corporación Biocomercio",
    # Ecuador
    "Tierra Viva": "TIERRA VIVA",
    "Corporación Toisán": "TOISAN",
    # Mexico
    "CECROPIA": "CECROPIA",
    "FONCET": "FONCET",
    # Honduras
    "Fundación PUCA": "Fundación PUCA",
    "CODDEFFAGOLF": "CODDEFFAGOLF",
    "FENAPROCACAHO": "FENAPROCACAHO",
    # El Salvador
    "Asociación ADEL LA Unión": "Asociación ADEL LA Unión",
    # Guatemala
    "Defensores de la Naturaleza": "Defensores de la Naturaleza",
    "ASOVERDE": "ASOVERDE",
    "ECO": "ECO"
}

def load_organization_csvs(org_folder: str, topic_filter: list = None) -> str:
    """
    Load CSV files from an organization's CVS folder.
    Optionally filter by topic to only include relevant data for map markers.
    
    Args:
        org_folder: Name of the organization folder
        topic_filter: List of topics to include ("ecosistemas", "amenazas", "servicios", "medios_vida", "conflictos")
                     If None or ["all"], includes all data
    """
    # Path to organization's CVS folder
    cvs_path = os.path.join(os.path.dirname(__file__), 'documents', 'orgs', org_folder, 'CVS')
    
    if not os.path.exists(cvs_path):
        logger.warning(f"CVS folder not found: {cvs_path}")
        return ""
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(cvs_path, '*.csv'))
    
    if not csv_files:
        logger.warning(f"No CSV files found in: {cvs_path}")
        return ""
    
    logger.info(f"Found {len(csv_files)} CSV files in {cvs_path}")
    if topic_filter and "all" not in topic_filter:
        logger.info(f"Filtering for topics: {topic_filter}")
    
    formatted_parts = []
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        
        # Skip the variables/dictionary file
        if 'variables' in filename.lower():
            continue
            
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                continue
            
            # Get column names for context
            columns = list(rows[0].keys()) if rows else []
            keys = set(columns)
            
            # Determine type and formatter based on columns
            file_type = "DATOS"
            formatter = None
            file_topic = None  # Track which topic this file belongs to
            
            if 'tipo_amenaza' in keys:
                file_type = "AMENAZAS"
                formatter = format_amenazas
                file_topic = "amenazas"
            elif 'xcoord' in keys or 'ycoord' in keys or ('x' in keys and 'y' in keys):
                # SE file with coordinates - check filename for topic
                file_type = "SERVICIOS ECOSISTEMICOS CON UBICACION"
                formatter = format_se_con_coords
                fname_lower = filename.lower()
                if 'ecosistema' in fname_lower:
                    file_topic = "ecosistemas"
                elif 'amenaza' in fname_lower:
                    file_topic = "amenazas"
                elif 'conflicto' in fname_lower:
                    file_topic = "conflictos"
                elif 'medio' in fname_lower or 'vida' in fname_lower:
                    file_topic = "medios_vida"
                else:
                    file_topic = "servicios"
            elif 'ecosistema' in keys:
                file_type = "ECOSISTEMAS"
                formatter = format_ecosistemas
                file_topic = "ecosistemas"
            elif 'indice_total' in keys or 'producto_principal' in keys:
                file_type = "PRIORIZACION DE MEDIOS DE VIDA"
                formatter = format_priorizacion
                file_topic = "medios_vida"
            elif 'elemento_SES' in keys:
                file_type = "MEDIOS DE VIDA Y SERVICIOS"
                formatter = format_medios_vida_ses
                file_topic = "servicios"
            elif 'elemento_se' in keys:
                file_type = "SERVICIOS ECOSISTEMICOS DETALLADOS"
                formatter = format_servicios_ecosistemicos
                file_topic = "servicios"
            elif 'cv_producto' in keys or 'codigo_mdv' in keys:
                 file_type = "CARACTERIZACION DE MEDIOS DE VIDA"
                 formatter = format_caracterizacion
                 file_topic = "medios_vida"
            else:
                 # Fallback to filename if columns are ambiguous
                 if 'amenaza' in filename.lower(): 
                     file_type = "AMENAZAS"
                     formatter = format_amenazas
                     file_topic = "amenazas"
                 elif 'conflicto' in filename.lower():
                     file_type = "CONFLICTOS"
                     formatter = lambda r: format_generic(r, columns)
                     file_topic = "conflictos"
                 else:
                     file_type = "OTROS DATOS"
                     formatter = lambda r: format_generic(r, columns)
            
            # Filter by topic if specified
            if topic_filter and "all" not in topic_filter:
                if file_topic and file_topic not in topic_filter:
                    continue  # Skip files that don't match the filter
            
            formatted_parts.append(f"\n\n=== {file_type} (Fuente: {filename}) ===")
            
            if formatter:
                formatted_parts.append(formatter(rows))
            else:
                formatted_parts.append(format_generic(rows, columns))
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return "\n".join(formatted_parts)


def format_se_con_coords(rows: list) -> str:
    """Format ecosystem services with coordinates (xcoord, ycoord)"""
    parts = []
    for row in rows:
        se = row.get('SE', row.get('código SE', ''))
        mdv = row.get('MdV', '')
        provision = row.get('provisión', row.get('provision', ''))
        flujo = row.get('flujo', '')
        usuarios = row.get('usuarios', '')
        mapa = row.get('mapa', '')
        
        # Get coordinates - prioritize x/y (WGS84) over xcoord/ycoord (projected UTM)
        lat = row.get('y') or row.get('lat') or row.get('latitud')  # y is latitude in WGS84
        lon = row.get('x') or row.get('lon') or row.get('longitud') or row.get('lng')  # x is longitude
        
        coord_str = f" (COORD: {lat}, {lon})" if lat and lon else ""
        
        if se or mdv:
            parts.append(f"  * {se} - MdV: {mdv}, Provision: {provision}, Flujo: {flujo}, Usuarios: {usuarios}, Mapa: {mapa}{coord_str}")
    
    return "\n".join(parts)


def format_amenazas(rows: list) -> str:
    """Format threats/amenazas data"""
    parts = []
    # Group by zone
    by_zone = {}
    for row in rows:
        if not row.get('amenaza'):  # Skip empty rows
            continue
        zona = row.get('grupo', 'General')
        if zona not in by_zone:
            by_zone[zona] = []
        by_zone[zona].append(row)
    
    for zona, items in by_zone.items():
        parts.append(f"\n[{zona}]")
        for item in items:
            tipo = item.get('tipo_amenaza', '')
            amenaza = item.get('amenaza', '')
            magnitud = item.get('magnitud', '')
            sitios = item.get('sitios_afectados', '')
            parts.append(f"  • {amenaza} ({tipo}): Magnitud {magnitud}, Sitios: {sitios}")
    
    return "\n".join(parts)


def format_ecosistemas(rows: list) -> str:
    """Format ecosystem data"""
    parts = []
    for row in rows:
        eco = row.get('ecosistema', '')
        if not eco:
            continue
        zona = row.get('grupo', '')
        salud = row.get('escala_salud', '')
        degradacion = row.get('causas_degradacion', row.get('causas_deg', ''))
        medios = row.get('medio_de_vida_relacionado', '')
        
        # Check for coordinates
        lat = row.get('latitud') or row.get('lat')
        lon = row.get('longitud') or row.get('long') or row.get('lon') or row.get('lng')
        coord_str = f" (COORD: {lat}, {lon})" if lat and lon else ""
        
        parts.append(f"  • {eco} ({zona}): Salud={salud}, Medios relacionados: {medios}{coord_str}")
        if degradacion:
            parts.append(f"    Causas de degradación: {degradacion}")
    
    return "\n".join(parts)


def format_priorizacion(rows: list) -> str:
    """Format livelihood prioritization with scores"""
    parts = []
    for row in rows:
        if not row.get('medio_de_vida'):
            continue
        mdv = row.get('medio_de_vida', '')
        zona = row.get('grupo', '')
        i_total = row.get('indice_total', row.get('i_total', ''))
        i_seg = row.get('indice_seguridad_alimentaria', row.get('i_seg_alim', ''))
        i_amb = row.get('indice_ambiente', row.get('i_ambiente', ''))
        i_incl = row.get('indice_inlcusion', row.get('i_inclusion', ''))
        
        # Check for coordinates
        lat = row.get('latitud') or row.get('lat')
        lon = row.get('longitud') or row.get('long') or row.get('lon') or row.get('lng')
        coord_str = f" (COORD: {lat}, {lon})" if lat and lon else ""
        
        parts.append(f"  • {mdv} ({zona}): Total={i_total}, Seg.Alim={i_seg}, Ambiente={i_amb}, Inclusión={i_incl}{coord_str}")
    
    return "\n".join(parts)


def format_medios_vida_ses(rows: list) -> str:
    """Format livelihoods and ecosystem services list"""
    parts = []
    by_zone = {}
    for row in rows:
        if not row.get('nombre'):
            continue
        zona = row.get('grupo', 'General')
        if zona not in by_zone:
            by_zone[zona] = {'medio de vida': [], 'ecosistema': []}
        
        elemento = row.get('elemento_SES', '')
        nombre = row.get('nombre', '')
        uso = row.get('uso_final_medio_de_vida', '')
        
        # Check for coordinates
        lat = row.get('latitud') or row.get('lat')
        lon = row.get('longitud') or row.get('long') or row.get('lon') or row.get('lng')
        coord_str = f" (COORD: {lat}, {lon})" if lat and lon else ""
        
        entry = f"{nombre} ({uso}){coord_str}"
        
        if 'ecosistema' in elemento.lower():
            by_zone[zona]['ecosistema'].append(entry)
        else:
            by_zone[zona]['medio de vida'].append(entry)
    
    for zona, data in by_zone.items():
        parts.append(f"\n[{zona}]")
        if data['medio de vida']:
            parts.append(f"  Medios de vida: {', '.join(set(data['medio de vida']))}")
        if data['ecosistema']:
            parts.append(f"  Ecosistemas: {', '.join(set(data['ecosistema']))}")
    
    return "\n".join(parts)


def format_servicios_ecosistemicos(rows: list) -> str:
    """Format detailed ecosystem services"""
    parts = []
    for row in rows:
        if not row.get('medio_de_vida_relacionado'):
            continue
        zona = row.get('grupo', '')
        elemento = row.get('elemento_se', '')
        mdv = row.get('medio_de_vida_relacionado', '')
        acceso = row.get('accesso', '')
        barreras = row.get('barreras', '')
        inclusion = row.get('inclusion', '')
        
        # Check for coordinates
        lat = row.get('latitud') or row.get('lat')
        lon = row.get('longitud') or row.get('long') or row.get('lon') or row.get('lng')
        coord_str = f" (COORD: {lat}, {lon})" if lat and lon else ""
        
        parts.append(f"  • [{zona}] {mdv} - {elemento}: Acceso={acceso}{coord_str}")
        if barreras and barreras != 'N/A':
            parts.append(f"    Barreras: {barreras}")
        if inclusion:
            parts.append(f"    Beneficiarios: {inclusion}")
    
    return "\n".join(parts)


def format_caracterizacion(rows: list) -> str:
    """Format livelihood characterization"""
    parts = []
    # Avoid dupes
    seen = set()
    for row in rows:
        mdv = row.get('medio_de_vida', '')
        lat = row.get('latitud') or row.get('lat')
        lon = row.get('longitud') or row.get('long') or row.get('lon') or row.get('lng')
        
        # Use simple key for dupes, but if coords exist, maybe don't dedup aggressively?
        # Let's include coords in key if present
        key = f"{mdv}_{lat}_{lon}"
        if not mdv or key in seen:
            continue
        seen.add(key)
        
        zona = row.get('grupo', '')
        sistema = row.get('sistema', '')
        producto = row.get('cv_producto', '')
        mercado = row.get('cv_mercado', '')
        importancia = row.get('cv_importancia', '')
        
        coord_str = f" (COORD: {lat}, {lon})" if lat and lon else ""
        
        parts.append(f"  • {mdv} ({zona}): Sistema={sistema}, Producto={producto}, Mercado={mercado}, Importancia={importancia}{coord_str}")
    
    return "\n".join(parts)


def format_generic(rows: list, columns: list) -> str:
    """Generic formatting for unknown CSV types"""
    parts = []
    # Show first 10 rows max
    for row in rows[:10]:
        # Get non-empty values
        values = [f"{k}={v}" for k, v in row.items() if v and v.strip()]
        if values:
            parts.append(f"  • {'; '.join(values[:5])}")
    
    if len(rows) > 10:
        parts.append(f"  ... y {len(rows) - 10} registros más")
    
    return "\n".join(parts)

# Cargar variables de entorno desde .env
load_dotenv()

app = FastAPI(title="CATIE PARES API", version="1.0.0")

@app.get("/ping-debug")
def ping_debug():
    """Endpoint para verificar que esta es la versión con logs [INSIGHT]"""
    return {
        "status": "ok",
        "version": "1.0.5-insight-logs",
        "db_path": os.getenv("CHROMA_DB_DIR", "default"),
        "orgs_mapped": list(ORG_NAME_TO_FOLDER.keys())
    }


# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://localhost:5174", 
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177"
]

# Add production origins from env
if os.getenv("CORS_ORIGINS"):
    origins.extend(os.getenv("CORS_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Auto-ingestion on startup
import threading
try:
    from ingest import ingest_documents, DB_DIR as RAG_DB_DIR
except ImportError as e:
    logger.error(f"STARTUP ERROR: Could not import ingest module: {e}")
    ingest_documents = None
    RAG_DB_DIR = None

@app.on_event("startup")
def startup_event():
    """Run ingestion in background if DB is empty"""
    if not ingest_documents or not RAG_DB_DIR:
        logger.warning("STARTUP: Skipping auto-ingestion due to import error.")
        return

    logger.info(f"STARTUP: Checking RAG DB at {RAG_DB_DIR}")
    
    # Check if DB seems empty (no sqlite file)
    db_file = os.path.join(RAG_DB_DIR, "chroma.sqlite3")
    if not os.path.exists(db_file):
        logger.info("STARTUP: DB not found. Starting background ingestion...")
        threading.Thread(target=ingest_documents, daemon=True).start()
    else:
        logger.info("STARTUP: DB found. Skipping auto-ingestion.")
        # Diagnostic: List Orgs in DB
        try:
            rag = RAGProcessor()
            if rag.db:
                all_data = rag.db.get()
                if all_data['metadatas']:
                    orgs_in_db = set(m.get('org_id') for m in all_data['metadatas'] if m.get('org_id'))
                    logger.info(f"STARTUP: Database contains data for organizations: {orgs_in_db}")
                else:
                    logger.warning("STARTUP: Database exists but appears to be EMPTY.")
        except Exception as e:
            logger.error(f"STARTUP: Error during DB diagnostic: {e}")

# Mock Data - Organizaciones por país
# Datos Reales - Organizaciones por país
ORGANIZACIONES = {
    'Mexico': [
        {
            'id': 'mx1',
            'nombre': 'CECROPIA',
            'descripcion': 'Soluciones locales a retos globales de desarrollo sostenible.',
            'descripcion_en': 'Local solutions to global sustainable development challenges.',
            'area': 'Desarrollo Sostenible',
            'contacto': 'info@cecropia.org'
        },
        {
            'id': 'mx2',
            'nombre': 'FONCET',
            'descripcion': 'Fondo de Conservación El Triunfo.',
            'descripcion_en': 'El Triunfo Conservation Fund.',
            'area': 'Financiamiento',
            'contacto': 'info@foncet.org'
        }
    ],
    'Ecuador': [
        {
            'id': 'ec1',
            'nombre': 'Tierra Viva',
            'descripcion': 'Aprendiendo a través de la experimentación.',
            'descripcion_en': 'Learning through experimenting.',
            'area': 'Desarrollo Rural y Agroecología',
            'contacto': 'info@tierraviva.org'
        },
        {
            'id': 'ec2',
            'nombre': 'Corporación Toisán',
            'descripcion': 'Organización comunitaria enfocada en desarrollo sostenible en el Valle de Intag.',
            'descripcion_en': 'Community-based organization focused on sustainable development in the Intag Valley.',
            'area': 'Desarrollo Comunitario',
            'contacto': 'info@toisan.org'
        }
    ],
    'Colombia': [
        {
            'id': 'co1',
            'nombre': 'Corporación Biocomercio',
            'descripcion': 'Promoción del uso sostenible de la biodiversidad.',
            'descripcion_en': 'Promotion of sustainable use of biodiversity.',
            'area': 'Biocomercio',
            'contacto': 'info@biocomercio.org.co'
        }
    ],
    'Honduras': [
        {
            'id': 'hn1',
            'nombre': 'Fundación PUCA',
            'descripcion': 'Fundación para la Protección del Parque Nacional Montaña de Celaque.',
            'descripcion_en': 'Foundation for the Protection of Celaque Mountain National Park.',
            'area': 'Áreas Protegidas',
            'contacto': 'info@puca.org'
        },
        {
            'id': 'hn2',
            'nombre': 'CODDEFFAGOLF',
            'descripcion': 'Comité para la Defensa y Desarrollo de la Flora y Fauna del Golfo de Fonseca.',
            'descripcion_en': 'Committee for the Defense and Development of Flora and Fauna of the Gulf of Fonseca.',
            'area': 'Conservación',
            'contacto': 'info@coddeffagolf.org'
        },
        {
            'id': 'hn3',
            'nombre': 'FENAPROCACAHO',
            'descripcion': 'Federación Nacional de Productores de Cacao de Honduras.',
            'descripcion_en': 'National Federation of Cocoa Producers of Honduras.',
            'area': 'Agricultura Sostenible',
            'contacto': 'info@fenaprocacaho.org'
        }
    ],
    'El Salvador': [
        {
            'id': 'sv1',
            'nombre': 'Asociación ADEL LA Unión',
            'descripcion': 'Agencia de Desarrollo Económico Local de La Unión.',
            'descripcion_en': 'Local Economic Development Agency of La Unión.',
            'area': 'Desarrollo Local',
            'contacto': 'info@adel.org.sv'
        }
    ],
    'Guatemala': [
        {
            'id': 'gt1',
            'nombre': 'Defensores de la Naturaleza',
            'descripcion': 'Protección del patrimonio natural y cultural.',
            'descripcion_en': 'Protection of natural and cultural heritage.',
            'area': 'Conservación',
            'contacto': 'info@defensores.org.gt'
        },
        {
            'id': 'gt2',
            'nombre': 'ASOVERDE',
            'descripcion': 'Asociación para el Desarrollo Sostenible y Conservación.',
            'descripcion_en': 'Association for Sustainable Development and Conservation.',
            'area': 'Desarrollo Sostenible',
            'contacto': 'info@asoverde.org'
        },
        {
            'id': 'gt3',
            'nombre': 'ECO',
            'descripcion': 'Ecosistemas y Conservación.',
            'descripcion_en': 'Ecosystems and Conservation.',
            'area': 'Conservación',
            'contacto': 'info@eco.org.gt'
        }
    ]
}

# Pydantic Models
class ChatRequest(BaseModel):
    organizacion: str
    mensaje: str
    pais: Optional[str] = None  # Country for Hybrid RAG

class ChatResponse(BaseModel):
    respuesta: str

class TerritorialInsightRequest(BaseModel):
    lat: float
    lng: float
    nombre_ubicacion: Optional[str] = None

class ExportRequest(BaseModel):
    content: str
    filename: str = "document.docx"

# API Endpoints
@app.get("/")
def raiz():
    return {
        "mensaje": "API CATIE PARES",
        "version": "1.0.0",
        "documentacion": "/docs",
        "status": "healthy" if not IMPORT_ERRORS else "degraded",
        "errors": IMPORT_ERRORS
    }

@app.get("/paises")
def obtener_paises():
    """Obtiene la lista de países disponibles"""
    return list(ORGANIZACIONES.keys())

@app.get("/organizaciones/{nombre_pais}")
def obtener_organizaciones(nombre_pais: str):
    """Obtiene las organizaciones de un país específico (Case Insensitive)"""
    logger.info(f"DEBUG: Request orgs for '{nombre_pais}'. Available keys: {list(ORGANIZACIONES.keys())}")
    
    # Create a mapping of lowercase key -> original key
    country_map = {k.lower(): k for k in ORGANIZACIONES.keys()}
    
    # Lookup using lowercase
    target_key = country_map.get(nombre_pais.lower())
    
    if target_key:
        return ORGANIZACIONES[target_key]
    
    logger.warning(f"DEBUG: '{nombre_pais}' not found in ORGANIZACIONES (Normalized)")
    return []



# Debug Endpoints
@app.get("/admin/debug-ingest")
def debug_ingest():
    """Check ingestion status and errors"""
    db_path = os.path.join(str(RAG_DB_DIR), "chroma.sqlite3") if RAG_DB_DIR else "N/A"
    return {
        "ingest_module_loaded": ingest_documents is not None,
        "import_errors": IMPORT_ERRORS,
        "db_dir": RAG_DB_DIR,
        "db_file_path": db_path,
        "db_exists": os.path.exists(db_path) if RAG_DB_DIR else False
    }

@app.post("/admin/force-ingest")
def force_ingest():
    """Manually trigger ingestion"""
    if not ingest_documents:
        raise HTTPException(500, detail=f"Ingest module missing. Errors: {IMPORT_ERRORS}")
    
    logger.info("MANUAL: Triggering ingestion via endpoint")
    threading.Thread(target=ingest_documents, daemon=True).start()
    return {"status": "Ingestion triggered manually. Check logs for progress."}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Endpoint de chat RAG Híbrido - combina PDFs + CSVs de organización"""
    try:
        # Inicializar procesador RAG
        rag = RAGProcessor()
        
        # Obtener org_folder a partir del nombre (usar mapping global)
        org_folder = ORG_NAME_TO_FOLDER.get(request.organizacion)
        logger.info(f"CHAT: Request Org='{request.organizacion}' -> Folder/ID='{org_folder}'")
        
        # Detect topics from the question for filtering map data
        detected_topics = detect_question_topics(request.mensaje)
        logger.info(f"CHAT: Detected topics: {detected_topics}")
        
        # === HYBRID RAG: Load CSV data for organization ===
        csv_context = ""
        if org_folder:
            # Pass detected topics to filter relevant CSV data
            csv_context = load_organization_csvs(org_folder, topic_filter=detected_topics)
            if csv_context:
                logger.info(f"CHAT: Loaded filtered CSV data for {org_folder} ({len(csv_context)} chars)")
            else:
                logger.info(f"CHAT: No CSV data found for {org_folder}")
        
        if not rag.db:
             return {
                "respuesta": "El sistema de conocimiento aún no está inicializado. Por favor ingesta documentos primero."
            }

        # Usar búsqueda híbrida por niveles para PDFs
        if org_folder:
            docs = rag.search_tiered(request.mensaje, org_id=org_folder)
        else:
            docs = rag.search_tiered(request.mensaje, org_id="GLOBAL_ONLY")
        
        # Construir contexto ESTRUCTURADO con etiquetas
        contexto_parts = []
        
        # === ADD CSV CONTEXT FIRST (Organization survey data) ===
        if csv_context:
            contexto_parts.append(
                f"--- DATOS ESTRUCTURADOS: {request.organizacion} [SURVEY_DATA] ---\n"
                f"Datos de encuestas y caracterización del territorio incluyendo Medios de Vida, "
                f"Amenazas, Ecosistemas, Servicios Ecosistémicos, y Priorización:\n{csv_context}\n"
            )
        
        # === ADD PDF DOCUMENTS ===
        for doc in docs:
            source = os.path.basename(doc.metadata.get('source', 'unknown'))
            tier = doc.metadata.get('retrieval_tier', 'Support')
            tag = "ORGANIZATION_DOC (PRIORITY)" if "Tier 1" in tier else "GLOBAL_DOC (SUPPORT)"
            
            contexto_parts.append(
                f"--- SOURCE: {source} [{tag}] ---\n{doc.page_content}\n"
            )
        
        if not contexto_parts:
            return {
                "respuesta": f"No encontré información específica sobre '{request.mensaje}' en los documentos ni datos del país."
            }
        
        contexto = "\n".join(contexto_parts)
        
        # Lista de fuentes para el frontend (Markdown)
        fuentes_unicas = {}
        
        # Add CSV as source if used
        if csv_context:
            fuentes_unicas["org_csv_data"] = f"* [CSV] Datos estructurados de {request.organizacion}"
        
        for doc in docs:
            name = os.path.basename(doc.metadata.get('source', 'unknown'))
            tier = doc.metadata.get('retrieval_tier', 'Unknown')
            icon = "[ORG]" if "Tier 1" in tier else "[REF]"
            page = doc.metadata.get('page', '?')
            fuentes_unicas[name] = f"* {icon} {name} (Pag. {page})"
            
        markdown_sources = "\n".join(fuentes_unicas.values())

        # Intentar usar LLM (OpenAI)
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            api_key = os.getenv("OPENAI_API_KEY")
            
            if api_key:
                logger.info(f"CHAT: API Key detected, initializing LLM...")
                logger.info(f"CHAT: Context size: {len(contexto)} chars, Sources: {len(fuentes_unicas)}")
                
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.0,
                    openai_api_key=api_key
                )
                
                # Updated prompt for Hybrid RAG with Organization CSVs
                prompt = f"""You are an Expert Consultant for the PARES Project (Conservation & Sustainable Development).

ROLE & METHODOLOGY:
1. **Understand**: Analyze the User's question and ALL available context.
2. **Check Evidence Sources**: You have access to THREE types of data:
   - [SURVEY_DATA]: Structured data from participatory surveys about the organization's territory:
     * Medios de Vida (livelihoods): crops, livestock, tourism, products, markets
     * Amenazas (threats): climate and non-climate threats, magnitude, affected sites
     * Ecosistemas (ecosystems): health status, degradation causes
     * Servicios Ecosistémicos: provisions, flows, barriers, beneficiaries
     * Priorización: livelihood priority scores (food security, environment, inclusion)
   - [ORGANIZATION_DOC]: PDF documents from the organization (HIGHEST PRIORITY for org-specific questions)
   - [GLOBAL_DOC]: General reference documents (use for context/definitions)
3. **Synthesize**: Combine insights from ALL relevant sources.

PRIORITY RULES:
- For QUANTITATIVE questions (what threats, what livelihoods, what ecosystems, scores): Prefer [SURVEY_DATA]
- For QUALITATIVE questions (what does org do, methodologies, approaches): Prefer [ORGANIZATION_DOC]
- For DEFINITIONS or GENERAL CONTEXT: Use [GLOBAL_DOC]
- ALWAYS cite specific data points from survey data when available

CONTEXT:
{contexto}

USER QUESTION: {request.mensaje}
TARGET ORGANIZATION: {request.organizacion}

INSTRUCTIONS:
- You MUST write a <thinking> block first. Inside, explain which sources are most relevant.
- Then, write your final response in Spanish (Professional tone).
- When citing [SURVEY_DATA], be specific: mention zone names, threat names, livelihood names, scores.
- Do NOT write a "Sources" list. I will append it manually.

MAP VISUALIZATION:
- If the [SURVEY_DATA] contains coordinates marked as (COORD: lat, lon) that are RELEVANT to the question (e.g. locations of services, threats, or ecosystems), you MUST output a JSON block at the very end of your response.
- Use this EXACT format:
```map_data
[
  {{"lat": 12.345, "lng": -84.567, "label": "Brief Name", "description": "Short details"}}
]
```
- Do not invent coordinates. Only use those found in the text context.

RESPONSE:"""

                logger.info(f"CHAT: Sending prompt to LLM ({len(prompt)} chars)...")
                messages = [HumanMessage(content=prompt)]
                response = llm.invoke(messages)
                full_response = response.content
                logger.info(f"CHAT: LLM Response received ({len(full_response)} chars)")
                
                # Post-processing: Strip <thinking> block for the user
                import re
                clean_response = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL).strip()
                
                # Append Real Sources (Markdown)
                respuesta_final = f"{clean_response}\n\n**Fuentes Consultadas:**\n{markdown_sources}"
                
                logger.info(f"CHAT: Response ready, returning to user")
                return {"respuesta": respuesta_final}
            
        except Exception as llm_error:
            import traceback
            error_msg = f"LLM Error: {llm_error}\n{traceback.format_exc()}"
            with open("chat_llm_error.log", "w", encoding="utf-8") as f:
                f.write(error_msg)
            print(f"[CHAT] LLM ERROR: {llm_error}", flush=True)
            # Continuar con fallback
        
        # FALLBACK: Si no hay LLM disponible, crear un resumen mejorado
        # Eliminar duplicados y crear un resumen más inteligente
        unique_contents = []
        seen = set()
        
        for doc in docs:
            content = doc.page_content.strip()
            # Usar primeras 100 chars como identificador para detectar duplicados
            content_hash = content[:100]
            if content_hash not in seen:
                seen.add(content_hash)
                unique_contents.append(content)
        
        # Limitar a los 3 extractos más relevantes y únicos
        unique_contents = unique_contents[:3]
        
        respuesta_parts = [
            f"**Información de {request.organizacion}**\n",
            f"*Pregunta: {request.mensaje}*\n",
            "---\n"
        ]
        
        for i, contenido in enumerate(unique_contents, 1):
            # Limpiar y formatear
            contenido_limpio = contenido.replace('\n', ' ').replace('  ', ' ').strip()
            # Limitar longitud de cada extracto
            if len(contenido_limpio) > 400:
                contenido_limpio = contenido_limpio[:400] + "..."
            respuesta_parts.append(f"**{i}.** {contenido_limpio}\n")
        
        # Collect sources for fallback
        fuentes = sorted(list(set(os.path.basename(doc.metadata.get('source', 'unknown')) for doc in docs)))
        if csv_context:
            fuentes.insert(0, f"Datos de {request.organizacion} (CSV)")

        respuesta_parts.append(f"\n---\n*Fuentes: {', '.join(fuentes)}*")
        respuesta_parts.append(f"\n\n*Nota: Configure OPENAI_API_KEY para obtener respuestas sintetizadas por IA*")
        
        respuesta_sintetizada = "\n".join(respuesta_parts)
        
        return {"respuesta": respuesta_sintetizada}

    except Exception as e:
        print(f"Error en chat: {e}")
        import traceback
        traceback.print_exc()
        return {
            "respuesta": f"Lo siento, hubo un error técnico procesando tu consulta: {str(e)}"
        }



@app.post("/insight-territorial")
def obtener_insight_territorial_organizacion(request: ChatRequest):
    """Genera un análisis territorial basado en los documentos de una organización específica"""
    try:
        print(f"\n[INSIGHT] === Starting Territorial Analysis ===", flush=True)
        print(f"[INSIGHT] Organization: {request.organizacion}", flush=True)
        
        # Inicializar procesador RAG
        rag = RAGProcessor()
        
        # Obtener org_id (folder name) a partir del nombre (usando mapeo global)
        org_folder = ORG_NAME_TO_FOLDER.get(request.organizacion)
        print(f"[INSIGHT] Org folder mapping: {org_folder}", flush=True)
        
        if not rag.db:
            print(f"[INSIGHT] ERROR: RAG DB not initialized")
            return {
                "respuesta": "El sistema de conocimiento aún no está inicializado. Por favor ingesta documentos primero."
            }
        
        if not org_folder:
            print(f"[INSIGHT] ERROR: No folder found for org")
            return {
                "respuesta": f"No se encontró información para la organización '{request.organizacion}'."
            }
        
        # Consulta específica para análisis territorial
        query_territorial = f"""Análisis territorial de {request.organizacion}:
        - ¿Cuál es el área geográfica de trabajo?
        - ¿Qué amenazas ambientales enfrentan?
        - ¿Qué servicios ecosistémicos protegen o restauran?
        - ¿Qué medios de vida apoyan?
        - ¿Qué conflictos socioambientales abordan?
        - ¿Qué soluciones basadas en naturaleza implementan?
        - ¿Por qué es importante su zona de trabajo?"""
        
        # Buscar SOLO en documentos de la organización (Tier 1)
        # Usar el retriever directamente con filtro de metadata
        try:
            # Buscar solo documentos de esta organización
            # Strip org_folder just in case of whitespace
            search_filter = {"org_id": org_folder.strip()}
            print(f"[INSIGHT] Searching with filter: {search_filter}", flush=True)
            
            docs = rag.db.similarity_search(
                query_territorial,
                k=15,  # Increased k for better coverage
                filter=search_filter
            )
            
            if not docs:
                print(f"[INSIGHT] WARNING: No documents matched search for {request.organizacion} (folder: {org_folder})", flush=True)
                # Debug: check if ANY docs exist for this org
                try:
                    all_org_docs = rag.db.get(where={"org_id": org_folder.strip()}, limit=1)
                    if not all_org_docs['ids']:
                        print(f"[INSIGHT] DB ERROR: No documents found at all for org_id='{org_folder}' in ChromaDB", flush=True)
                    else:
                        print(f"[INSIGHT] DB OK: Documents exist for {org_folder}, but search query didn't match any.", flush=True)
                except Exception as e:
                    print(f"[INSIGHT] DB QUERY ERROR: {e}", flush=True)
                    
                return {
                    "respuesta": f"**Análisis Territorial - {request.organizacion}**\n\n"
                                f"No se encontró información suficiente en los documentos de esta organización para generar un análisis territorial.\n\n"
                                f"Por favor, asegúrese de que existan documentos cargados para {request.organizacion}."
                }
            
            print(f"[INSIGHT] Found {len(docs)} documents for analysis.")
            
            # Construir contexto a partir de los documentos
            contexto_parts = []
            for doc in docs:
                source = os.path.basename(doc.metadata.get('source', 'unknown'))
                contexto_parts.append(
                    f"--- DOCUMENTO: {source} ---\n{doc.page_content}\n"
                )
            
            contexto = "\n".join(contexto_parts)
            
            # Usar OpenAI si está disponible
            api_key = os.getenv("OPENAI_API_KEY")
            
            print(f"[INSIGHT] API Key present: {bool(api_key)}")
            print(f"[INSIGHT] Documents found: {len(docs)}")
            
            if api_key:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import HumanMessage
                
                print(f"[INSIGHT] Initializing LLM (gpt-4o-mini)...")
                
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.0,  # Máxima precisión
                    openai_api_key=api_key
                )
                
                prompt = f"""Eres un analista experto en conservación y desarrollo sostenible para el Proyecto PARES.

Tu tarea es generar un ANÁLISIS TERRITORIAL basado EXCLUSIVAMENTE en los documentos proporcionados de la organización {request.organizacion}.

REGLAS ESTRICTAS:
1. USA SOLO la información de los documentos proporcionados
2. Si no hay información sobre algún aspecto, indica "No especificado en los documentos"
3. NO uses conocimiento general o externo
4. Sé específico y cita detalles de los documentos
5. Responde en ESPAÑOL

DOCUMENTOS DE {request.organizacion}:
{contexto}

FORMATO REQUERIDO (usa exactamente estos encabezados con **):

**Análisis Territorial - {request.organizacion}**

**Área geográfica de trabajo:** [Describe la zona geográfica basándote en los documentos]

**Amenazas principales:** [Lista las amenazas ambientales mencionadas en los documentos]

**Servicios ecosistémicos clave:** [Lista los servicios ecosistémicos mencionados]

**Medios de vida apoyados:** [Describe los medios de vida que la organización apoya según los documentos]

**Conflictos socioambientales:** [Describe los conflictos mencionados en los documentos]

**Soluciones Basadas en Naturaleza implementadas:** [Lista las soluciones NbS que implementa la organización]

**Importancia de la zona:** [Explica por qué es importante esta zona según los documentos]

IMPORTANTE: Si alguna sección no tiene información en los documentos, escribe "No especificado en los documentos disponibles."
"""
                
                print(f"[INSIGHT] Sending prompt to LLM ({len(prompt)} chars)...")
                messages = [HumanMessage(content=prompt)]
                response = llm.invoke(messages)
                print(f"[INSIGHT] LLM Response received ({len(response.content)} chars)")
                print(f"[INSIGHT] === Analysis Complete ===\n")
                
                return {"respuesta": response.content}
            
            else:
                print(f"[INSIGHT] No API Key, using fallback mode")
                # Fallback sin LLM - crear resumen estructurado
                fuentes = list(set([os.path.basename(doc.metadata.get('source', 'unknown')) for doc in docs]))
                
                respuesta = f"**Análisis Territorial - {request.organizacion}**\n\n"
                respuesta += f"**Información encontrada en documentos:**\n\n"
                
                # Mostrar extractos relevantes
                for i, doc in enumerate(docs[:4], 1):  # Limitar a 4 extractos
                    contenido = doc.page_content.strip()[:300]  # Primeros 300 caracteres
                    respuesta += f"{i}. {contenido}...\n\n"
                
                respuesta += f"\n**Fuentes:** {', '.join(fuentes)}\n\n"
                respuesta += "*Configure OPENAI_API_KEY para obtener un análisis territorial estructurado y sintetizado.*"
                
                return {"respuesta": respuesta}
        
        except Exception as search_error:
            print(f"Error en búsqueda de documentos: {search_error}")
            import traceback
            traceback.print_exc()
            
            return {
                "respuesta": f"**Análisis Territorial - {request.organizacion}**\n\n"
                            f"Error al buscar información en los documentos: {str(search_error)}"
            }
    
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open("insight_error.log", "w", encoding="utf-8") as f:
            f.write(error_msg)
        
        return {
            "respuesta": f"**Análisis Territorial**\n\n"
                        f"Error generando el análisis: {str(e)}\n\n"
                        f"Posible causa: Dependencias faltantes (langchain-openai) o problemas de configuración."
        }


@app.post("/export-docx")
def export_docx(request: ExportRequest):
    """Generates a DOCX file from markdown content"""
    try:
        buffer = create_docx_from_markdown(request.content)
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={request.filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating DOCX: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")


@app.get("/get-report/{org_folder}")
def get_report(org_folder: str):
    """Serve organization HTML report file"""
    try:
        # Build path to report file
        report_path = os.path.join(
            os.path.dirname(__file__),
            'documents',
            'orgs',
            org_folder,
            'REPORTE',
            f'{org_folder.lower().replace(" ", "_")}_report.HTML'
        )
        
        # Check if file exists
        if not os.path.exists(report_path):
            # Try alternative naming convention
            alt_report_path = os.path.join(
                os.path.dirname(__file__),
                'documents',
                'orgs',
                org_folder,
                'REPORTE',
                'tierra_viva_report.HTML'  # Fallback for known file
            )
            if os.path.exists(alt_report_path):
                report_path = alt_report_path
            else:
                raise HTTPException(status_code=404, detail=f"Report not found for {org_folder}")
        
        return FileResponse(report_path, media_type="text/html")
        
    except Exception as e:
        logger.error(f"Error serving report: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading report: {str(e)}")

