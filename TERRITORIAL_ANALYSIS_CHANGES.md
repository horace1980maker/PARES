# Territorial Analysis Implementation - Option 3

## Overview
Implemented organization-based territorial analysis using RAG (Retrieval-Augmented Generation) that queries **only** the organization's documents to generate contextual insights.

## Behavior Flow

1. **User selects a country** → Map highlights the country
2. **Panel shows organizations** for that country in the sidebar
3. **User selects an organization** → Two things happen simultaneously:
   - **Territorial Analysis Card** appears over the map with analysis based on organization's documents
   - **Chat Interface** opens for further interaction
4. **System generates analysis** using ONLY documents from the organization's folder
5. **If no information exists** → System explicitly states "No information found in documents"

## Files Changed

### Backend Changes

#### 1. `backend/main.py`
- **Modified endpoint**: `/insight-territorial` (POST)
- **Changed from**: Map coordinate-based analysis with AI general knowledge
- **Changed to**: Organization-based analysis using RAG with document filtering
- **Key features**:
  - Uses `ChatRequest` model (organizacion + mensaje)
  - Filters documents by `org_id` metadata
  - Queries ChromaDB with `filter={"org_id": org_folder}`
  - Returns structured analysis in same format
  - Uses OpenAI to synthesize findings from documents
  - Explicitly states when information is not available

#### 2. `backend/requirements.txt`
- Added `requests` library (for future geocoding if needed)

### Frontend Changes

#### 1. `frontend/src/App.jsx`
- **Added state management**:
  - `territorialInsight` - stores the analysis data
  - `isInsightLoading` - loading state for analysis
- **Added useEffect**: Automatically fetches territorial analysis when `selectedOrg` changes
- **Added component**: `TerritorialInsightCard` positioned over the map
- **Integrated flow**: Organization selection triggers both territorial analysis and chat

#### 2. `frontend/src/components/MapComponent.jsx`
- **Removed**: Map click event handler (`MapEvents`)
- **Removed**: Territorial insight state and fetching logic
- **Removed**: `TerritorialInsightCard` from this component
- **Simplified**: Now only handles country selection via map clicks

#### 3. `frontend/src/components/TerritorialInsightCard.jsx`
- **No changes needed** - Component already supports the required format

## Technical Details

### RAG Query Strategy

```python
# Query specifically for territorial analysis aspects
query_territorial = f"""Análisis territorial de {organizacion}:
- ¿Cuál es el área geográfica de trabajo?
- ¿Qué amenazas ambientales enfrentan?
- ¿Qué servicios ecosistémicos protegen o restauran?
- ¿Qué medios de vida apoyan?
- ¿Qué conflictos socioambientales abordan?
- ¿Qué soluciones basadas en naturaleza implementan?
- ¿Por qué es importante su zona de trabajo?"""

# Search ONLY in organization documents
docs = rag.db.similarity_search(
    query_territorial,
    k=8,
    filter={"org_id": org_folder}  # Critical: filters to org only
)
```

### AI Prompt Strategy

The OpenAI prompt enforces strict rules:
1. **USE ONLY** information from provided documents
2. If no information exists, state "No especificado en los documentos"
3. **NO general knowledge** or external information
4. Be specific and cite document details
5. Respond in Spanish

### Output Format

```markdown
**Análisis Territorial - [Organization Name]**

**Área geográfica de trabajo:** [From documents or "No especificado"]

**Amenazas principales:** [From documents or "No especificado"]

**Servicios ecosistémicos clave:** [From documents or "No especificado"]

**Medios de vida apoyados:** [From documents or "No especificado"]

**Conflictos socioambientales:** [From documents or "No especificado"]

**Soluciones Basadas en Naturaleza implementadas:** [From documents or "No especificado"]

**Importancia de la zona:** [From documents or "No especificado"]
```

## Organization Folder Mapping

The system maps organization names to document folders:

```python
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
```

## Error Handling

### No Documents Found
```
**Análisis Territorial - [Organization]**

No se encontró información suficiente en los documentos de esta 
organización para generar un análisis territorial.

Por favor, asegúrese de que existan documentos cargados para [Organization].
```

### Search Error
```
**Análisis Territorial - [Organization]**

Error al buscar información en los documentos. Por favor intente nuevamente.
```

### General Error
```
**Análisis Territorial**

Error generando el análisis. Por favor intente nuevamente.
```

## Fallback Behavior

If `OPENAI_API_KEY` is not configured:
- Shows raw document excerpts (first 300 characters of top 4 documents)
- Lists source documents
- Displays warning message to configure API key

## Testing Checklist

- [x] Backend endpoint accepts `ChatRequest` with organization name
- [x] RAG filters documents by `org_id` metadata
- [x] Frontend triggers analysis on organization selection
- [x] Territorial card appears over map
- [x] Chat interface opens simultaneously
- [x] Closing territorial card also deselects organization
- [x] Map click no longer triggers territorial analysis
- [x] Analysis uses ONLY organization documents
- [x] System states when no information is available
- [x] Format matches existing `TerritorialInsightCard` expectations

## Dependencies

### Backend
- `langchain-openai` - For GPT-4o-mini synthesis
- `chromadb` - Vector database with metadata filtering
- Existing RAG infrastructure

### Frontend
- React hooks (useState, useEffect)
- Existing `TerritorialInsightCard` component
- `config.API_URL` for backend communication

## Environment Variables Required

```bash
OPENAI_API_KEY=sk-...  # Required for AI synthesis
```

Without this key, the system will still work but show raw document excerpts instead of synthesized analysis.

## Future Enhancements

1. **Cache territorial analyses** - Store generated analyses to avoid re-querying
2. **Multi-language support** - Generate analysis in user's selected language
3. **Document highlighting** - Show which documents contributed to each section
4. **Confidence scores** - Indicate how much information was available for each section
5. **Export functionality** - Allow users to download territorial analysis as PDF
