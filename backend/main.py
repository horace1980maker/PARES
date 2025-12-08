from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from document_manager import DocumentManager
from rag_processor import RAGProcessor

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
    """Endpoint de chat RAG"""
    try:
        # Inicializar procesador RAG
        rag = RAGProcessor()
        
        # Mapeo de nombres de organizaciones a IDs de carpetas
        # El frontend envía nombres como "Corporación Biocomercio", "Tierra Viva", etc.
        # Las carpetas en backend/documents/orgs/ tienen nombres exactos
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
        
        # Obtener org_id (folder name) a partir del nombre
        org_folder = ORG_NAME_TO_FOLDER.get(request.organizacion)
        
        if not rag.db:
             return {
                "respuesta": "El sistema de conocimiento aún no está inicializado. Por favor ingesta documentos primero."
            }

        # Usar búsqueda híbrida por niveles
        if org_folder:
            docs = rag.search_tiered(request.mensaje, org_id=org_folder)
        else:
            # Fallback a búsqueda general (Tier 2 only effectively)
            # Podríamos implementar un 'search_global' en rag_processor, 
            # pero por ahora usaremos search_tiered con un ID dummy o lógica custom.
            # Simplemente buscaremos en Tier 2.
            docs = rag.search_tiered(request.mensaje, org_id="GLOBAL_ONLY") # Esto retornará solo Tier 2 si Tier 1 falla o es vacío
        
        if not docs:
            return {
                "respuesta": f"No encontré información específica sobre '{request.mensaje}' en los documentos."
            }
        
        # Construir contexto ESTRUCTURADO con etiquetas
        contexto_parts = []
        for doc in docs:
            source = os.path.basename(doc.metadata.get('source', 'unknown'))
            tier = doc.metadata.get('retrieval_tier', 'Support')
            # Etiquetado claro para el LLM
            tag = "ORGANIZATION_DOC (PRIORITY)" if "Tier 1" in tier else "GLOBAL_DOC (SUPPORT)"
            
            contexto_parts.append(
                f"--- SOURCE: {source} [{tag}] ---\n{doc.page_content}\n"
            )
        
        contexto = "\n".join(contexto_parts)
        
        # Lista de fuentes para el frontend (HTML)
        fuentes_unicas = {}
        for doc in docs:
            name = os.path.basename(doc.metadata.get('source', 'unknown'))
            tier = doc.metadata.get('retrieval_tier', 'Unknown')
            icon = "🏢" if "Tier 1" in tier else "🌍"
            page = doc.metadata.get('page', '?')
            fuentes_unicas[name] = f"<li>{icon} {name} (Pág. {page})</li>"
            
        html_sources = "<ul>" + "".join(fuentes_unicas.values()) + "</ul>"

        # Intentar usar LLM (OpenAI)
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            api_key = os.getenv("OPENAI_API_KEY")
            
            if api_key:
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.0, # Rigor máximo
                    openai_api_key=api_key
                )
                
                # Prompt con "Methodological Backbone" y Thinking Block
                prompt = f"""You are an Expert Consultant for the PARES Project (Conservation & Sustainable Development).

ROLE & METHODOLOGY:
1. **Understand**: Analyze the User's question and the context.
2. **Define**: Identify key concepts (e.g., specific Org goals vs. global NbS definitions).
3. **Check Evidence**: Compare [ORGANIZATION_DOC] vs [GLOBAL_DOC]. 
   - RULE: [ORGANIZATION_DOC] is the TRUTH for this specific organization.
   - RULE: Use [GLOBAL_DOC] only to fill gaps or explain technical concepts.
4. **Synthesize**: Answer the user.

CONTEXT:
{contexto}

USER QUESTION: {request.mensaje}
TARGET ORGANIZATION: {request.organizacion}

INSTRUCTIONS:
- You MUST write a <thinking> block first. Inside, explain your Phase analysis and evidence check.
- Then, write your final response in Spanish (Professional tone).
- Do NOT write a "Sources" list. I will append it manually.

RESPONSE:"""

                messages = [HumanMessage(content=prompt)]
                response = llm.invoke(messages)
                full_response = response.content
                
                # Post-processing: Strip <thinking> block for the user
                import re
                clean_response = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL).strip()
                
                # Append Real Sources
                respuesta_final = f"{clean_response}\n\n<div class='sources-section'><strong>Fuentes Consultadas:</strong>{html_sources}</div>"
                
                return {"respuesta": respuesta_final}
                
                # Agregar fuentes
                respuesta_final = f"{respuesta_sintetizada}\n\n---\n*Información basada en: {', '.join(fuentes)}*"
                
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
def obtener_insight_territorial(request: TerritorialInsightRequest):
    """Genera un insight territorial para coordenadas específicas"""
    contexto_ubicacion = f"Coordenadas: {request.lat}, {request.lng}"
    if request.nombre_ubicacion:
        contexto_ubicacion += f", Ubicación: {request.nombre_ubicacion}"
    return {
        "respuesta": (
            f"**Análisis Territorial** - {contexto_ubicacion}\n\n"
            "**Amenazas principales:** Deforestación, expansión agrícola no sostenible, cambio climático.\n\n"
            "**Servicios ecosistémicos clave:** Regulación hídrica, captura de carbono, conservación de biodiversidad.\n\n"
            "**Medios de vida más afectados:** Agricultura familiar, turismo comunitario, pesca artesanal.\n\n"
            "**Conflictos presentes:** Uso de suelo, acceso al agua, tenencia de tierra.\n\n"
            "**Soluciones Basadas en Naturaleza sugeridas:** Agroforestería, restauración de riberas, corredores biológicos.\n\n"
            "**Por qué importa esta zona:** Corredor biológico crítico para la conectividad de ecosistemas en la región."
        )
    }
