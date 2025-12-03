# Guía de Configuración - CATIE PARES

## Requisitos Previos

- Python 3.8 o superior
- Node.js 16 o superior
- npm o yarn

## Instalación

### 1. Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
```

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
```

## Ejecución

### Iniciar el Backend

```bash
cd backend
python run.py
```

El servidor estará disponible en: `http://localhost:8001`
Documentación API: `http://localhost:8001/docs`

### Iniciar el Frontend

En otra terminal:

```bash
cd frontend
npm run dev
```

El frontend estará disponible en: `http://localhost:5173` (o el siguiente puerto disponible)

## Verificación

1. Abrir el navegador en la URL del frontend
2. La aplicación debe cargar en español por defecto
3. El toggle de idioma (EN/ES) debe estar visible en la esquina superior derecha
4. El mapa debe mostrar América Latina

## Características

✅ **Mapa Interactivo**: Haz clic en un país para ver sus organizaciones  
✅ **Organizaciones**: Información detallada de organizaciones por país  
✅ **Chat RAG**: Interfaz de chat para consultar sobre organizaciones  
✅ **Insights Territoriales**: Haz clic en cualquier punto del mapa para análisis territorial  
✅ **Bilingüe**: Cambia entre Español e Inglés con un clic  
✅ **Carga de PDFs**: Sube documentos de organizaciones para el sistema RAG  

## Datos Incluidos

La aplicación incluye datos mock para 6 países:
- Mexico (CECROPIA, FONCET)
- Ecuador (Tierra Viva, Corporación Toisán)
- Colombia (Corporación Biocomercio)
- Honduras (Fundación PUCA, CODDEFFAGOLF, FENAPROCACAHO)
- El Salvador (Asociación ADEL LA Unión)
- Guatemala (Defensores de la Naturaleza, ASOVERDE, ECO)

## Solución de Problemas

### El backend no inicia
- Verificar que el puerto 8001 esté disponible
- Verificar que todas las dependencias estén instaladas

### El frontend no carga
- Verificar que el backend esté corriendo
- Revisar la consola del navegador para errores de CORS
- Verificar que el puerto del frontend esté accesible

### Las organizaciones no cargan
- Verificar que el backend esté corriendo en el puerto 8001
- Revisar la consola del navegador para errores de red
- Asegurarse de hacer clic directamente sobre un país en el mapa

## Próximos Pasos

1. **Integrar Sistema RAG Real**: Actualmente las respuestas del chat son simuladas
2. **Procesar PDFs Subidos**: Implementar procesamiento automático de documentos
3. **Agregar Más Países**: Expandir la base de datos de organizaciones
4. **Mejorar Insights Territoriales**: Conectar con datos geoespaciales reales

## Soporte

Para preguntas o problemas, contactar al equipo de desarrollo de CATIE.
