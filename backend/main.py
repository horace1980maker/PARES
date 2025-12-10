from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import csv
import glob
from dotenv import load_dotenv
from document_manager import DocumentManager
from rag_processor import RAGProcessor

# Map organization names to folder names
ORG_NAME_TO_FOLDER = {
    # Colombia
    "Corporación Biocomercio": "Corporación Biocomercio",
    # Ecuador
    "Tierra Viva": "TIERRA VIVA",
    "Corporación Toisán": "Corporación Toisán",
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

def load_organization_csvs(org_folder: str) -> str:
    """
    Load all CSV files from an organization's CVS folder.
    Returns formatted text for RAG context.
    """
    # Path to organization's CVS folder
    cvs_path = os.path.join(os.path.dirname(__file__), 'documents', 'orgs', org_folder, 'CVS')
    
    if not os.path.exists(cvs_path):
        print(f"CVS folder not found: {cvs_path}")
        return ""
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(cvs_path, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in: {cvs_path}")
        return ""
    
    print(f"Found {len(csv_files)} CSV files in {cvs_path}")
    
    formatted_parts = []
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        
        # Skip the variables/dictionary file
        if 'variables' in filename.lower():
            continue
        
        # Determine the type from filename
        file_type = "DATOS"
        if 'amenaza' in filename.lower():
            file_type = "AMENAZAS"
        elif 'ecosistema' in filename.lower():
            file_type = "ECOSISTEMAS"
        elif 'priorizacion' in filename.lower():
            file_type = "PRIORIZACIÓN DE MEDIOS DE VIDA"
        elif 'medios_vida' in filename.lower() or 'medio_de_vida' in filename.lower():
            file_type = "MEDIOS DE VIDA"
        elif 'servicios_ecosistemicos' in filename.lower():
            file_type = "SERVICIOS ECOSISTÉMICOS"
        elif 'caracterizacion' in filename.lower():
            file_type = "CARACTERIZACIÓN DE MEDIOS DE VIDA"
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                continue
            
            # Get column names for context
            columns = list(rows[0].keys()) if rows else []
            
            formatted_parts.append(f"\n\n=== {file_type} (Fuente: {filename}) ===")
            
            # Format based on file type
            if 'amenaza' in filename.lower():
                formatted_parts.append(format_amenazas(rows))
            elif 'ecosistema' in filename.lower():
                formatted_parts.append(format_ecosistemas(rows))
            elif 'priorizacion' in filename.lower():
                formatted_parts.append(format_priorizacion(rows))
            elif 'medios_vida' in filename.lower() and 'servicios' in filename.lower():
                formatted_parts.append(format_medios_vida_ses(rows))
            elif 'servicios_ecosistemicos' in filename.lower():
                formatted_parts.append(format_servicios_ecosistemicos(rows))
            elif 'caracterizacion' in filename.lower():
                formatted_parts.append(format_caracterizacion(rows))
            else:
                # Generic formatting
                formatted_parts.append(format_generic(rows, columns))
        
        except Exception as e:
            print(f"Error loading CSV {filename}: {e}")
            continue
    
    return "\n".join(formatted_parts)


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
    """Format ecosystems data"""
    parts = []
    for row in rows:
        if not row.get('ecosistema'):
            continue
        eco = row.get('ecosistema', '')
        zona = row.get('grupo', '')
        salud = row.get('escala_salud', row.get('es_salud', ''))
        degradacion = row.get('causas_degradacion', row.get('causas_deg', ''))
        medios = row.get('medio_de_vida_relacionado', '')
        parts.append(f"  • {eco} ({zona}): Salud={salud}, Medios relacionados: {medios}")
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
        parts.append(f"  • {mdv} ({zona}): Total={i_total}, Seg.Alim={i_seg}, Ambiente={i_amb}, Inclusión={i_incl}")
    
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
        
        if 'ecosistema' in elemento.lower():
            by_zone[zona]['ecosistema'].append(nombre)
        else:
            by_zone[zona]['medio de vida'].append(f"{nombre} ({uso})")
    
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
        
        parts.append(f"  • [{zona}] {mdv} - {elemento}: Acceso={acceso}")
        if barreras and barreras != 'N/A':
            parts.append(f"    Barreras: {barreras}")
        if inclusion:
            parts.append(f"    Beneficiarios: {inclusion}")
    
    return "\n".join(parts)


def format_caracterizacion(rows: list) -> str:
    """Format livelihood characterization"""
    parts = []
    seen = set()
    for row in rows:
        mdv = row.get('medio_de_vida', '')
        if not mdv or mdv in seen:
            continue
        seen.add(mdv)
        
        zona = row.get('grupo', '')
        sistema = row.get('sistema', '')
        producto = row.get('cv_producto', '')
        mercado = row.get('cv_mercado', '')
        importancia = row.get('cv_importancia', '')
        
        parts.append(f"  • {mdv} ({zona}): Sistema={sistema}, Producto={producto}, Mercado={mercado}, Importancia={importancia}")
    
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

# API Endpoints
@app.get("/")
def raiz():
    return {
        "mensaje": "API CATIE PARES",
        "version": "1.0.0",
        "documentacion": "/docs"
    }

@app.get("/paises")
def obtener_paises():
    """Obtiene la lista de países disponibles"""
    return list(ORGANIZACIONES.keys())

@app.get("/organizaciones/{nombre_pais}")
def obtener_organizaciones(nombre_pais: str):
    """Obtiene las organizaciones de un país específico"""
    if nombre_pais not in ORGANIZACIONES:
        return []
    return ORGANIZACIONES[nombre_pais]

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Endpoint de chat RAG Híbrido - combina PDFs + CSVs de organización"""
    try:
        # Inicializar procesador RAG
        rag = RAGProcessor()
        
        # Obtener org_folder a partir del nombre (usar mapping global)
        org_folder = ORG_NAME_TO_FOLDER.get(request.organizacion)
        print(f"DEBUG: Request Org='{request.organizacion}' -> Folder/ID='{org_folder}'")
        
        # === HYBRID RAG: Load CSV data for organization ===
        csv_context = ""
        if org_folder:
            csv_context = load_organization_csvs(org_folder)
            if csv_context:
                print(f"DEBUG: Loaded CSV data for {org_folder} ({len(csv_context)} chars)")
            else:
                print(f"DEBUG: No CSV data found for {org_folder}")
        
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
            fuentes_unicas["org_csv_data"] = f"* 📊 Datos estructurados de {request.organizacion} (CSV)"
        
        for doc in docs:
            name = os.path.basename(doc.metadata.get('source', 'unknown'))
            tier = doc.metadata.get('retrieval_tier', 'Unknown')
            icon = "🏢" if "Tier 1" in tier else "🌍"
            page = doc.metadata.get('page', '?')
            fuentes_unicas[name] = f"* {icon} {name} (Pág. {page})"
            
        markdown_sources = "\n".join(fuentes_unicas.values())

        # Intentar usar LLM (OpenAI)
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            api_key = os.getenv("OPENAI_API_KEY")
            
            if api_key:
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

RESPONSE:"""

                messages = [HumanMessage(content=prompt)]
                response = llm.invoke(messages)
                full_response = response.content
                
                # Post-processing: Strip <thinking> block for the user
                import re
                clean_response = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL).strip()
                
                # Append Real Sources (Markdown)
                respuesta_final = f"{clean_response}\n\n**Fuentes Consultadas:**\n{markdown_sources}"
                
                return {"respuesta": respuesta_final}
            
        except Exception as llm_error:
            print(f"Error usando LLM: {llm_error}")
            import traceback
            traceback.print_exc()
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
            f"📄 **Información de {request.organizacion}**\n",
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
        
        respuesta_parts.append(f"\n---\n*Fuentes: {', '.join(fuentes)}*")
        respuesta_parts.append(f"\n\n⚠️ *Nota: Configure OPENAI_API_KEY para obtener respuestas sintetizadas por IA*")
        
        respuesta_sintetizada = "\n".join(respuesta_parts)
        
        return {"respuesta": respuesta_sintetizada}

    except Exception as e:
        print(f"Error en chat: {e}")
        return {
            "respuesta": "Lo siento, hubo un error procesando tu consulta."
        }



@app.post("/insight-territorial")
def obtener_insight_territorial_organizacion(request: ChatRequest):
    """Genera un análisis territorial basado en los documentos de una organización específica"""
    try:
        # Inicializar procesador RAG
        rag = RAGProcessor()
        
        # Obtener org_id (folder name) a partir del nombre (usando mapeo global)
        org_folder = ORG_NAME_TO_FOLDER.get(request.organizacion)
        
        if not rag.db:
            return {
                "respuesta": "El sistema de conocimiento aún no está inicializado. Por favor ingesta documentos primero."
            }
        
        if not org_folder:
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
            docs = rag.db.similarity_search(
                query_territorial,
                k=8,  # Obtener más documentos para mejor contexto
                filter={"org_id": org_folder}
            )
            
            if not docs:
                return {
                    "respuesta": f"**Análisis Territorial - {request.organizacion}**\n\n"
                                f"No se encontró información suficiente en los documentos de esta organización para generar un análisis territorial.\n\n"
                                f"Por favor, asegúrese de que existan documentos cargados para {request.organizacion}."
                }
            
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
            
            if api_key:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import HumanMessage
                
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
                
                messages = [HumanMessage(content=prompt)]
                response = llm.invoke(messages)
                
                return {"respuesta": response.content}
            
            else:
                # Fallback sin LLM - crear resumen estructurado
                fuentes = list(set([os.path.basename(doc.metadata.get('source', 'unknown')) for doc in docs]))
                
                respuesta = f"**Análisis Territorial - {request.organizacion}**\n\n"
                respuesta += f"**Información encontrada en documentos:**\n\n"
                
                # Mostrar extractos relevantes
                for i, doc in enumerate(docs[:4], 1):  # Limitar a 4 extractos
                    contenido = doc.page_content.strip()[:300]  # Primeros 300 caracteres
                    respuesta += f"{i}. {contenido}...\n\n"
                
                respuesta += f"\n**Fuentes:** {', '.join(fuentes)}\n\n"
                respuesta += "⚠️ *Configure OPENAI_API_KEY para obtener un análisis territorial estructurado y sintetizado.*"
                
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
        print(f"Error generando análisis territorial: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "respuesta": f"**Análisis Territorial**\n\n"
                        f"Error generando el análisis: {str(e)}\n\n"
                        f"Posible causa: Dependencias faltantes (langchain-openai) o problemas de configuración."
        }

