# Testing Guide - Territorial Analysis

## Quick Test Steps

### 1. Verify Backend is Running
```bash
# Should be running on http://localhost:8000
# Check: http://localhost:8000/docs
```

### 2. Verify Frontend is Running
```bash
# Should be running on http://localhost:5173
```

### 3. Test the Flow

#### Step 1: Select a Country
- Click on any country on the map (e.g., Honduras, Mexico, Ecuador)
- **Expected**: Right sidebar shows organizations for that country

#### Step 2: Select an Organization
- Click on any organization card in the sidebar
- **Expected**: 
  - Territorial Analysis Card appears over the map (top-right)
  - Chat Interface opens (bottom-right)
  - Both show loading states initially

#### Step 3: Review Territorial Analysis
- **Expected format**:
  ```
  **Análisis Territorial - [Organization Name]**
  
  **Área geográfica de trabajo:** [Info from docs or "No especificado"]
  
  **Amenazas principales:** [Info from docs or "No especificado"]
  
  **Servicios ecosistémicos clave:** [Info from docs or "No especificado"]
  
  **Medios de vida apoyados:** [Info from docs or "No especificado"]
  
  **Conflictos socioambientales:** [Info from docs or "No especificado"]
  
  **Soluciones Basadas en Naturaleza implementadas:** [Info from docs or "No especificado"]
  
  **Importancia de la zona:** [Info from docs or "No especificado"]
  ```

#### Step 4: Test Chat
- Type a question in the chat interface
- **Expected**: Response based on organization's documents

#### Step 5: Close and Reselect
- Close the Territorial Analysis Card
- **Expected**: Both card and chat close, organization is deselected
- Select another organization
- **Expected**: New territorial analysis for the new organization

## Organizations to Test

### Ecuador
- **Tierra Viva** - Should have documents in `TIERRA VIVA` folder
- **Corporación Toisán** - Check if documents exist

### Honduras
- **Fundación PUCA**
- **CODDEFFAGOLF**
- **FENAPROCACAHO**

### Mexico
- **CECROPIA**
- **FONCET**

### Guatemala
- **Defensores de la Naturaleza**
- **ASOVERDE**
- **ECO**

### Colombia
- **Corporación Biocomercio**

### El Salvador
- **Asociación ADEL LA Unión**

## Expected Behaviors

### ✅ Success Cases

1. **Organization with documents**:
   - Analysis shows specific information from documents
   - Each section has relevant content
   - Sources are cited

2. **Organization with limited documents**:
   - Some sections show "No especificado en los documentos disponibles"
   - Available information is displayed
   - System is honest about gaps

3. **Organization with no documents**:
   - Message: "No se encontró información suficiente en los documentos..."
   - Prompts to ensure documents are loaded

### ❌ Error Cases to Check

1. **Network error**:
   - Shows error message
   - Doesn't crash the app

2. **Backend not running**:
   - Frontend shows error
   - User can retry

3. **Invalid organization name**:
   - Backend returns appropriate error
   - Frontend handles gracefully

## Debugging Tips

### Check Backend Logs
Look for these messages:
```
🔍 Buscando Tier 1 (Org: [org_name])...
DEBUG: Request Org='[org_name]' -> Folder/ID='[folder_name]'
```

### Check Frontend Console
Look for:
```
Obteniendo análisis territorial para: [org_name]
Análisis territorial obtenido: { respuesta: "..." }
```

### Check ChromaDB
Verify documents are ingested:
```bash
cd backend
python
>>> from rag_processor import RAGProcessor
>>> rag = RAGProcessor()
>>> docs = rag.db.similarity_search("test", k=5, filter={"org_id": "TIERRA VIVA"})
>>> print(len(docs))  # Should show number of documents
```

## Common Issues

### Issue 1: "No se encontró información suficiente"
**Cause**: No documents for that organization
**Solution**: 
1. Check if folder exists in `backend/documents/orgs/[org_name]`
2. Run ingestion: `python ingest.py`
3. Verify documents were processed

### Issue 2: Analysis shows general knowledge instead of document info
**Cause**: Filter not working or wrong org_id mapping
**Solution**: 
1. Check `ORG_NAME_TO_FOLDER` mapping in `main.py`
2. Verify metadata in ChromaDB has correct `org_id`
3. Check backend logs for filter being applied

### Issue 3: Territorial card doesn't appear
**Cause**: Frontend state issue or API error
**Solution**:
1. Check browser console for errors
2. Verify API endpoint is responding
3. Check network tab for 200 response

### Issue 4: Analysis is in English instead of Spanish
**Cause**: OpenAI prompt not being followed
**Solution**:
1. Check if `OPENAI_API_KEY` is set
2. Verify prompt includes "Responde en ESPAÑOL"
3. May need to adjust temperature or model

## Performance Notes

- **First load**: May take 2-3 seconds (RAG initialization)
- **Subsequent queries**: Should be faster (< 1 second)
- **Large documents**: May take longer to process

## Success Criteria

✅ All organizations show territorial analysis
✅ Analysis is based ONLY on organization documents
✅ System clearly states when information is missing
✅ Format is consistent and readable
✅ Chat and territorial analysis work together
✅ No crashes or unhandled errors
✅ User can switch between organizations smoothly
