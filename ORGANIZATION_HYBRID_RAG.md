# Organization-Specific Hybrid RAG Implementation

## Overview

This implementation adds **Hybrid RAG** capabilities to the chat system, allowing it to query both:
1. **PDF Documents** (organization-specific, via existing RAG)
2. **CSV Data** (organization-specific survey/characterization data)

## Data Location

All CSV files are stored in each organization's folder:

```
backend/
└── documents/
    └── orgs/
        └── TIERRA VIVA/
            └── CVS/
                ├── tierra_viva_Amenazas.csv
                ├── tierra_viva_Ecosistemas.csv
                ├── tierra_viva_priorizacion.csv
                ├── tierra_viva_medios_vida_y_servicios_ecosistemicos.csv
                ├── tierra_viva_servicios_ecosistemicos_y_medios_de_vida.csv
                ├── tierra_viva_Caracterizacion_A.csv
                ├── tierra_viva_Caracterizacion_B.csv
                ├── tierra_viva_Caracterizacion_C.csv
                ├── tierra_viva_Caracterizacion_D.csv
                └── database_general_TIERRAVIVA - variables.csv (skipped - dictionary)
```

## How It Works

### User Flow

```
1. User selects a country (e.g., Ecuador)
   ↓
2. Sidebar shows organizations (e.g., Tierra Viva)
   ↓
3. User clicks on organization
   ↓
4. Chat opens with Hybrid RAG enabled
   ↓
5. User asks a question
   ↓
6. System automatically:
   a) Loads ALL CSV files from organization's CVS folder
   b) Formats data by type (Amenazas, Ecosistemas, Medios de Vida, etc.)
   c) Queries PDF documents for the organization
   d) Combines both sources in the AI prompt
   e) Returns comprehensive answer citing both sources
```

## CSV Types Supported

| File Pattern | Data Type | Content |
|-------------|-----------|---------|
| `*amenaza*.csv` | AMENAZAS | Climate and non-climate threats by zone |
| `*ecosistema*.csv` | ECOSISTEMAS | Ecosystems, health status, degradation causes |
| `*priorizacion*.csv` | PRIORIZACIÓN | Livelihood priority scores |
| `*medios_vida*.csv` | MEDIOS DE VIDA | Livelihoods by zone and use type |
| `*servicios_ecosistemicos*.csv` | SERVICIOS ECOSISTÉMICOS | Ecosystem services, access, barriers |
| `*caracterizacion*.csv` | CARACTERIZACIÓN | Livelihood characterization details |

## Formatted Output Examples

### Amenazas (Threats)
```
=== AMENAZAS (Fuente: tierra_viva_Amenazas.csv) ===

[Zona Alta]
  • Sequía (climática): Magnitud 5, Sitios: Peñaherrera; Rumipamba
  • Lluvias intensas (climática): Magnitud 5, Sitios: Todas las comunidades zona alta
  • Quemas (no-climática): Magnitud 5, Sitios: Rumipamba; Chaupi Gurangui

[Zona Media]
  • Sequía (climática): Magnitud 5, Sitios: Lavandero; San Clemente
  • Deforestación (no-climática): Magnitud 3, Sitios: Lavandero; San Clemente
```

### Ecosistemas
```
=== ECOSISTEMAS (Fuente: tierra_viva_Ecosistemas.csv) ===

  • Bosque montano (Zona Alta): Salud=2
    Causas de degradación: Tala; aumento frontera agrícola
  • Páramo (Zona Alta): Salud=2
    Causas de degradación: Quemas; aumento frontera agrícola
```

### Priorización
```
=== PRIORIZACIÓN DE MEDIOS DE VIDA ===

  • Maiz (Zona Alta): Total=13, Seg.Alim=3, Ambiente=2, Inclusión=3
  • Gallinas (Zona Alta): Total=12, Seg.Alim=3, Ambiente=2, Inclusión=3
  • Turismo comunitario (Zona Media): Total=10, Seg.Alim=1, Ambiente=3, Inclusión=3
```

## Example Queries

### Survey Data (CSV-based)
```
User: "¿Cuáles son las principales amenazas en la zona alta?"
→ System uses CSV [SURVEY_DATA]
→ Returns: Sequía (magnitud 5), Lluvias intensas (magnitud 5), Quemas (magnitud 5)
```

### PDF-based
```
User: "¿Cuál es la misión de Tierra Viva?"
→ System uses PDF documents [ORGANIZATION_DOC]
→ Returns: Mission statement from PDF documents
```

### Hybrid (Both)
```
User: "¿Qué ecosistemas hay y cuál es su estado de conservación?"
→ System uses CSV for ecosystem list and health scores
→ System uses PDFs for conservation details
→ Returns: Combined response with both sources cited
```

## Source Attribution

Responses include source attribution:
```markdown
**Fuentes Consultadas:**
* 📊 Datos estructurados de Tierra Viva (CSV)
* 🏢 documento_org.pdf (Pág. 5)
* 🌍 referencia_global.pdf (Pág. 12)
```

## Adding Data for Other Organizations

To enable Hybrid RAG for another organization:

1. **Create the CVS folder:**
   ```
   backend/documents/orgs/{ORG_FOLDER}/CVS/
   ```

2. **Add CSV files** with any of these patterns in the filename:
   - `amenaza` - for threats
   - `ecosistema` - for ecosystems
   - `priorizacion` - for livelihood prioritization
   - `medios_vida` - for livelihoods
   - `servicios_ecosistemicos` - for ecosystem services
   - `caracterizacion` - for characterization

3. **CSV format requirements:**
   - UTF-8 encoding
   - First row must be headers
   - Key columns depend on type (grupo, amenaza, ecosistema, medio_de_vida, etc.)

## Technical Details

### Key Functions

- `load_organization_csvs(org_folder)` - Loads all CSVs from organization's CVS folder
- `format_amenazas(rows)` - Formats threats data grouped by zone
- `format_ecosistemas(rows)` - Formats ecosystem data
- `format_priorizacion(rows)` - Formats prioritization scores
- `format_medios_vida_ses(rows)` - Formats livelihoods list
- `format_servicios_ecosistemicos(rows)` - Formats ecosystem services
- `format_caracterizacion(rows)` - Formats characterization details
- `format_generic(rows, columns)` - Fallback for unknown CSV types

### Folder Name Mapping

```python
ORG_NAME_TO_FOLDER = {
    "Tierra Viva": "TIERRA VIVA",
    "Corporación Toisán": "Corporación Toisán",
    "CECROPIA": "CECROPIA",
    "FONCET": "FONCET",
    "Fundación PUCA": "Fundación PUCA",
    "CODDEFFAGOLF": "CODDEFFAGOLF",
    "FENAPROCACAHO": "FENAPROCACAHO",
    "Asociación ADEL LA Unión": "Asociación ADEL LA Unión",
    "Defensores de la Naturaleza": "Defensores de la Naturaleza",
    "ASOVERDE": "ASOVERDE",
    "ECO": "ECO",
    "Corporación Biocomercio": "Corporación Biocomercio"
}
```

## Error Handling

- **CVS folder not found**: Chat continues with PDF-only mode
- **No CSV files found**: Chat continues with PDF-only mode
- **CSV parsing error**: Skips problematic file, loads others
- **Variables/dictionary files**: Automatically skipped (filename contains "variables")

## Testing

### Verification Steps

1. **Backend logs should show:**
   ```
   Found 9 CSV files in .../documents/orgs/TIERRA VIVA/CVS
   DEBUG: Loaded CSV data for TIERRA VIVA (X chars)
   ```

2. **Response should include:**
   - `📊 Datos estructurados de Tierra Viva (CSV)` in sources
   - Specific data points (zone names, threat names, scores)

### Test Queries

1. "¿Cuáles son las amenazas climáticas?"
2. "¿Qué medios de vida hay en la zona baja?"
3. "¿Cuál es el estado de los ecosistemas?"
4. "¿Qué servicios ecosistémicos provee el bosque montano?"
5. "¿Cuáles medios de vida tienen mayor puntaje de seguridad alimentaria?"

## Files Modified

### Backend
- `backend/main.py` - Added organization CSV loading functions and updated chat endpoint

### Data Structure Required
```
backend/documents/orgs/{org}/CVS/*.csv
```

## Status

✅ **Complete and Ready for Testing**

---

**Implementation Date**: 2025-12-09
**Data Source**: Organization CSVs from participatory surveys
**Supported Organizations**: Any with CVS folder
