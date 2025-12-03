# Estructura de Documentos - CATIE PARES

## Organización de Archivos

Los documentos se organizan manualmente en la siguiente estructura:

```
backend/documents/
├── metadata.json                    # Registro central de todos los documentos
└── orgs/
    ├── CECROPIA/                   # Mexico
    ├── FONCET/                     # Mexico
    ├── Tierra Viva/                # Ecuador
    ├── Corporación Toisán/         # Ecuador
    ├── Corporación Biocomercio/    # Colombia
    ├── Fundación PUCA/             # Honduras
    ├── CODDEFFAGOLF/               # Honduras
    ├── FENAPROCACAHO/              # Honduras
    ├── Asociación ADEL LA Unión/   # El Salvador
    ├── Defensores de la Naturaleza/ # Guatemala
    ├── ASOVERDE/                   # Guatemala
    └── ECO/                        # Guatemala
```

## Organizaciones por País

### Mexico
- **CECROPIA** - Soluciones locales a retos globales de desarrollo sostenible
- **FONCET** - Fondo de Conservación El Triunfo

### Ecuador
- **Tierra Viva** - Desarrollo Rural y Agroecología
- **Corporación Toisán** - Desarrollo sostenible en el Valle de Intag

### Colombia
- **Corporación Biocomercio** - Uso sostenible de la biodiversidad

### Honduras
- **Fundación PUCA** - Protección del Parque Nacional Montaña de Celaque
- **CODDEFFAGOLF** - Defensa y Desarrollo de Flora y Fauna del Golfo de Fonseca
- **FENAPROCACAHO** - Federación Nacional de Productores de Cacao

### El Salvador
- **Asociación ADEL LA Unión** - Agencia de Desarrollo Económico Local

### Guatemala
- **Defensores de la Naturaleza** - Protección del patrimonio natural y cultural
- **ASOVERDE** - Desarrollo Sostenible y Conservación
- **ECO** - Ecosistemas y Conservación

## Metadata de Documentos

El archivo `metadata.json` contiene información detallada de cada documento:

```json
{
  "documentos": [
    {
      "id": "TIERRA VIVA_1732752000",
      "filename": "FINAL-EC-TIERRA-VIVA-Anexo A.pdf",
      "original_filename": "FINAL-EC-TIERRA-VIVA-Anexo A.pdf",
      "path": "C:\\Users\\narva\\projects\\CATIE\\PARES\\backend\\documents\\orgs\\TIERRA VIVA\\FINAL-EC-TIERRA-VIVA-Anexo A.pdf",
      "pais": "desconocido",
      "org_id": "TIERRA VIVA",
      "org_nombre": "TIERRA VIVA",
      "fecha_subida": "2024-11-27T19:46:40.517024",
      "procesado_rag": true
    }
  ]
}
```

## Cómo el RAG Identifica Documentos

### 1. **Metadata en ChromaDB**

Cuando un documento se procesa con `ingest.py`, se almacena con metadata que incluye:

```python
{
    "org_id": "TIERRA VIVA",
    "org_nombre": "TIERRA VIVA",
    "source": "C:\\...\\documents\\orgs\\TIERRA VIVA\\documento.pdf",
    "documento_id": "TIERRA VIVA_1732752000"
}
```

### 2. **Configuración RAG Actual**

- **Chunk Size**: 1200 caracteres
- **Chunk Overlap**: 300 caracteres
- **Documentos Recuperados (k)**: 6
- **Embedding Model**: all-MiniLM-L6-v2

### 3. **Proceso de Ingesta Manual**

```bash
# 1. Colocar PDFs en la carpeta de la organización
backend/documents/orgs/Tierra Viva/documento.pdf

# 2. Ejecutar script de ingesta
cd backend
python ingest.py

# 3. El script:
#    - Escanea documents/orgs/
#    - Actualiza metadata.json
#    - Procesa documentos nuevos
#    - Genera embeddings
#    - Almacena en ChromaDB
```

### 4. **Proceso Completo de Consulta**

```
Usuario selecciona organización "Tierra Viva"
    ↓
Hace pregunta en chat: "¿Qué proyectos tienen?"
    ↓
Backend recibe: {organizacion: "Tierra Viva", mensaje: "¿Qué proyectos tienen?"}
    ↓
RAG busca en ChromaDB (recupera 6 documentos más relevantes)
    ↓
Formatea respuesta con extractos numerados
    ↓
Usuario recibe respuesta con información completa
```

## Base de Datos Vectorial

### ChromaDB
- **Ubicación**: `backend/chroma_db/` (también existe `chroma_db/` en raíz)
- **Persistencia**: Automática
- **Embeddings**: SentenceTransformer (all-MiniLM-L6-v2)

## Ventajas de esta Estructura

✅ **Organización Clara**: Una carpeta por organización  
✅ **Escalabilidad**: Agregar nuevas organizaciones es simple (crear carpeta)  
✅ **Trazabilidad**: Metadata completa de cada documento  
✅ **Gestión Manual**: Control total sobre documentos  
✅ **RAG Mejorado**: 6 documentos recuperados con chunks más grandes  
✅ **Respuestas Completas**: Extractos completos sin cortes  

## Comandos Útiles

### Ingerir Documentos
```bash
cd backend
python ingest.py
```

### Iniciar Backend
```bash
cd backend
python run.py
```

### Verificar Base de Datos
```bash
# Ver metadata.json
cat backend/documents/metadata.json

# Listar organizaciones con documentos
ls backend/documents/orgs/
```

## Ejemplo de Respuesta RAG

```
Basado en los documentos de Tierra Viva, encontré la siguiente información relevante:

**Extracto 1:**
"con la paz, el clima y la seguridad. Además, se fortalecerán las capacidades del 
equipo de la FUNDACIÓN TIERRA VIVA para implementar y escalar intervenciones 
sostenibles, fomentando sinergias transregionales..."

**Extracto 2:**
"El proyecto busca restaurar 150 hectáreas de bosque nativo en la cuenca del 
río Intag, beneficiando a 300 familias de la región..."

...hasta 6 extractos...

(Información extraída de: FINAL-EC-TIERRA-VIVA-Anexo A.pdf)
```

---

**Última actualización**: 2025-11-30  
**Sistema**: Gestión manual de documentos con ingesta automatizada
