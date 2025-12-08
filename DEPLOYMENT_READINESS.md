# Evaluación de Preparación para Despliegue (Deployment Readiness)

## Estado Actual
El sistema **NO** está listo para despliegue inmediato en Hetzner/Coolify. Se han identificado los siguientes bloqueos:

### 1. URLs Hardcodeadas (Frontend)
El frontend tiene la URL del backend (`http://localhost:8001`) escrita directamente en el código en múltiples archivos:
- `src/App.jsx`
- `src/components/MapComponent.jsx`
- `src/components/ChatInterface.jsx`

Esto hará que el frontend falle en producción al intentar conectar con `localhost` del usuario visitante.

### 2. Configuración de CORS (Backend)
El backend (`main.py`) tiene una lista explícita de orígenes permitidos que solo incluye `localhost`. Debe configurarse para aceptar el dominio de producción.

### 3. Ausencia de Dockerización
No existen archivos `Dockerfile` ni `docker-compose.yml`. Coolify funciona mejor con una especificación clara de contenedor.
- **Backend**: Necesita un Dockerfile que instale dependencias y ejecute `uvicorn`.
- **Frontend**: Necesita un Dockerfile que construya la aplicación (build) y sirva los estáticos (ej. con Nginx).
- **Procesos**: El script `ingest.py` y `run.py` son manuales. Se recomienda que la ingesta sea un comando disparable o un job separado.

### 4. Persistencia de Datos (ChromaDB)
La base de datos vectorial se guarda localmente en `../chroma_db`. En un entorno Docker, esto debe ser un **volumen persistente** para no perder los embeddings al reiniciar el contenedor.

## Plan de Acción Recomendado (Siguientes Pasos)

Voy a proceder a realizar las siguientes correcciones para dejar el proyecto listo para despliegue:

1.  **Dockerizar el Backend**: Crear `backend/Dockerfile`.
2.  **Dockerizar el Frontend**: Crear `frontend/Dockerfile` (Multi-stage build con Nginx).
3.  **Orquestación**: Crear `docker-compose.yml` compatible con Coolify.
4.  **Refactorizar Frontend**: Extraer la URL de la API a una variable de entorno `VITE_API_URL`.
5.  **Ajustar CORS**: Permitir configuración de orígenes vía variable de entorno.

## Archivos a Crear/Modificar
- `docker-compose.yml` (Nuevo)
- `backend/Dockerfile` (Nuevo)
- `frontend/Dockerfile` (Nuevo)
- `frontend/src/config.js` (Nuevo para centralizar configuración)
- `frontend/src/App.jsx` (Modificar)
- `frontend/src/components/MapComponent.jsx` (Modificar)
- `frontend/src/components/ChatInterface.jsx` (Modificar)
- `backend/main.py` (Modificar)

Summary of Changes Evaluated & Implemented
I've created a detailed report in 
DEPLOYMENT_READINESS.md
, but here is the summary of the critical fixes I applied:

hardcoded URLs in Frontend: The frontend was trying to connect to http://localhost:8001. I refactored 
App.jsx
, 
MapComponent.jsx
, and 
ChatInterface.jsx
 to use a central configuration (
src/config.js
) that reads from VITE_API_URL.
Docker Configuration: I created the missing Docker files required for Coolify:
backend/Dockerfile
: Sets up Python, installs requirements, and runs Uvicorn.
frontend/Dockerfile
: Multi-stage build (Node build -> Nginx serve) with SPA support.
docker-compose.yml
: Orchestrates both services and handles persistence.
Database Persistence: I modified 
ingest.py
 and 
rag_processor.py
 to respect the CHROMA_DB_DIR environment variable, ensuring your vector database persists correctly in a Docker volume (mapped to /app/chroma_db).
CORS Configuration: Updated 
main.py
 to accept a CORS_ORIGINS environment variable, so you can whitelist your production domain.
How to Deploy on Coolify
Push your code to your git repository.
In Coolify:
Create a new resource from Git Repository.
Select Docker Compose as the build pack.
Coolify should detect the 
docker-compose.yml
 file.
Environment Variables: You MUST set these variables in the Coolify project settings:
OPENAI_API_KEY: Your OpenAI key.
VITE_API_URL: The public URL of your backend (e.g., https://api.your-domain.com or the internal Coolify URL if using internal networking, though client-side React needs the public URL).
You are now ready to deploy! 🚀