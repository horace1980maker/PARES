# Resumen: Sistema de Documentos - CATIE PARES

## ¿Dónde se almacenan los documentos?

Los documentos se organizan manualmente en una estructura simple:

```
backend/documents/orgs/
├── {Nombre_Organización}/
│   └── {archivos}.pdf
```

**Ejemplo real:**
```
backend/documents/orgs/
├── Tierra Viva/
│   ├── FINAL-EC-TIERRA-VIVA-Anexo A.pdf
│   ├── plan_trabajo_2024.pdf
│   └── informe_anual.pdf
├── CECROPIA/
│   └── proyecto_conservacion.pdf
├── Corporación Toisán/
│   └── diagnostico_intag.pdf
```

## ¿Cada organización tiene su propia carpeta?

**Sí**, cada organización tiene una carpeta con su nombre exacto:

### Mexico
- `CECROPIA/`
- `FONCET/`

### Ecuador
- `Tierra Viva/`
- `Corporación Toisán/`

### Colombia
- `Corporación Biocomercio/`

### Honduras
- `Fundación PUCA/`
- `CODDEFFAGOLF/`
- `FENAPROCACAHO/`

### El Salvador
- `Asociación ADEL LA Unión/`

### Guatemala
- `Defensores de la Naturaleza/`
- `ASOVERDE/`
- `ECO/`

## ¿Cómo identifica el RAG los documentos de cada organización?

### 1. **Metadata automática durante ingesta**

Cuando ejecutas `python ingest.py`, el script:

```python
# Escanea la estructura de carpetas
for org_folder in os.listdir("documents/orgs/"):
    for pdf_file in os.listdir(f"documents/orgs/{org_folder}"):
        # Extrae org_id del nombre de la carpeta
        org_id = org_folder  # Ej: "TIERRA VIVA"
        
        # Crea metadata
        metadata = {
            "org_id": org_id,
            "org_nombre": org_id,
            "source": f"documents/orgs/{org_id}/{pdf_file}",
            "documento_id": f"{org_id}_{timestamp}"
        }
```

### 2. **Almacenamiento en ChromaDB**

Cada fragmento del documento se guarda con su metadata:

```python
chunk.metadata = {
    "org_id": "TIERRA VIVA",
    "org_nombre": "TIERRA VIVA",
    "source": ".../documents/orgs/TIERRA VIVA/documento.pdf",
    "documento_id": "TIERRA VIVA_1732752000"
}
```

### 3. **Recuperación de documentos relevantes**

Cuando el usuario hace una pregunta:

```python
# El RAG recupera los 6 documentos más relevantes
retriever = rag.get_retriever()
docs = retriever.invoke("¿Qué proyectos tienen?")  # Recupera 6 chunks

# Cada chunk incluye:
# - Contenido del texto (1200 caracteres aprox)
# - Metadata (org_id, fuente, etc.)
```

## Configuración RAG Actual

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **Chunk Size** | 1200 | Caracteres por fragmento |
| **Chunk Overlap** | 300 | Solapamiento entre fragmentos |
| **k (documentos)** | 6 | Fragmentos recuperados por consulta |
| **Embedding Model** | all-MiniLM-L6-v2 | Modelo de embeddings |

## Flujo Completo

```
1. PREPARACIÓN
   └─ Crear carpeta: backend/documents/orgs/Tierra Viva/
   └─ Copiar PDFs en la carpeta

2. INGESTA
   └─ Ejecutar: python ingest.py
   └─ Script escanea carpetas
   └─ Procesa PDFs nuevos
   └─ Divide en chunks (1200 chars, overlap 300)
   └─ Genera embeddings
   └─ Almacena en ChromaDB con metadata
   └─ Actualiza metadata.json

3. CONSULTA
   └─ Usuario selecciona "Tierra Viva"
   └─ Pregunta: "¿Cuáles son los objetivos del proyecto?"
   └─ RAG busca en ChromaDB
   └─ Recupera 6 fragmentos más relevantes (por similitud semántica)
   └─ Formatea respuesta

4. RESPUESTA
   └─ Muestra extractos numerados completos
   └─ Incluye fuentes (nombres de archivos)
   └─ SIN cortes de texto
```

## Mejoras Recientes

### ✅ Gestión Manual de Documentos
- Ya no hay upload desde el frontend
- Administrador coloca PDFs directamente en carpetas
- Mayor control y seguridad

### ✅ Formato de Respuesta Mejorado
**Antes:**
```
"Basado en los documentos de Tierra Viva, encontré...: 
con la paz, el clima y la seguridad. Además, se fortalecerán las cap...
(Información extraída de: documento.pdf)"
```

**Ahora:**
```
Basado en los documentos de Tierra Viva, encontré la siguiente información relevante:

**Extracto 1:**
"con la paz, el clima y la seguridad. Además, se fortalecerán las capacidades 
del equipo de la FUNDACIÓN TIERRA VIVA para implementar y escalar intervenciones 
sostenibles, fomentando sinergias transregionales y garantizando la replicabilidad 
de las experiencias exitosas."

**Extracto 2:**
"El proyecto tiene como objetivo restaurar 150 hectáreas de bosque nativo en 
la cuenca del río Intag, implementando sistemas agroforestales que beneficien 
a 300 familias de comunidades locales."

...hasta 6 extractos...

(Información extraída de: FINAL-EC-TIERRA-VIVA-Anexo A.pdf)
```

### ✅ Más Contexto (k=6 en vez de k=3)
- Respuestas más completas
- Menos probabilidad de perder información relevante

## Comandos Principales

```bash
# Ingerir nuevos documentos
cd backend
python ingest.py

# Iniciar servidor backend
python run.py

# Iniciar frontend
cd ../frontend
npm run dev
```

## Archivos del Sistema

```
backend/
├── documents/
│   ├── orgs/              # ← Colocar PDFs aquí
│   │   ├── Tierra Viva/
│   │   ├── CECROPIA/
│   │   └── ...
│   └── metadata.json      # Registro automático
├── chroma_db/             # Base de datos vectorial
├── ingest.py              # Script de ingesta
├── rag_processor.py       # Lógica RAG
└── main.py                # API endpoints
```

## Ventajas del Sistema

✅ **Simple** - Una carpeta por organización  
✅ **Escalable** - Solo crear carpeta para nueva org  
✅ **Automático** - `ingest.py` detecta y procesa nuevos PDFs  
✅ **Trazable** - `metadata.json` registra todo  
✅ **Preciso** - Metadata asegura respuestas correctas  
✅ **Completo** - 6 extractos sin cortes de texto  

## Organizaciones Actuales (Total: 13)

| País | Organizaciones |
|------|----------------|
| Mexico | CECROPIA, FONCET |
| Ecuador | Tierra Viva, Corporación Toisán |
| Colombia | Corporación Biocomercio |
| Honduras | Fundación PUCA, CODDEFFAGOLF, FENAPROCACAHO |
| El Salvador | Asociación ADEL LA Unión |
| Guatemala | Defensores de la Naturaleza, ASOVERDE, ECO |

---

**Última actualización**: 2025-11-30  
**Sistema**: Gestión manual + Ingesta automatizada + RAG mejorado
