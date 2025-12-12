# Evaluación de Preparación para Despliegue (Deployment Readiness)

## Estado Actual
El sistema **ESTÁ LISTO** para despliegue en Hetzner/Coolify. Se han resuelto los bloqueos previamente identificados:

### 1. URLs Hardcodeadas (Frontend) ✅
El frontend ahora usa `config.js` y `VITE_API_URL` para configurar el endpoint del backend dinámicamente.
 
### 2. Configuración de CORS (Backend) ✅
El backend ahora acepta orígenes configurables vía variable de entorno.
 
### 3. Dockerización ✅
- **Backend**: Existe `backend/Dockerfile` configurado.
- **Frontend**: Existe `frontend/Dockerfile` con Nginx.
- **Orquestación**: Existe `docker-compose.yml` probado.
 
### 4. Persistencia de Datos (ChromaDB) ✅
Configurado volumen persistente en `docker-compose.yml` (`/app/chroma_db`).

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

To configure your custom domain with Coolify using the Docker Compose setup we just created, follow these steps.

I have updated your 
docker-compose.yml
, 
frontend/Dockerfile
, and 
nginx.conf
 to make this significantly easier. You now generally only need one domain (for the frontend), and the backend (API) will be securely proxied internally (via /api).

1. Load the Code in Coolify
First, you need to populate that empty box in your screenshot:

Click the "Load Compose File" button (encircled in your screenshot) or verify the file content is populated.
It should now show the 
docker-compose.yml
 content I just updated.
2. Configure the Domain (The "Where")
Once the file is loaded/saved, Coolify will parse the file and list the services found (
frontend
 and backend).

In the Coolify UI, scroll down or look for a "Services" section (or click on the stack details if you aren't already there).
Click on the frontend service.
Look for a field called "Domains" or "FQDN" (Fully Qualified Domain Name).
Enter your custom domain, for example: https://mapas.catie.ac.cr.
Note: Ensure you include https:// if you want Coolify to handle SSL for you.
Click Save.
(Optional) Backend Domain: Since I configured Nginx to proxy /api calls to the backend internally, you do not technically need to assign a public domain to the backend service anymore. It is safer to keep it internal. However, if you want direct access to the API (e.g. for testing docs), you can assign a domain like https://api-mapas.catie.ac.cr to the backend service in the same way.

3. Environment Variables ("The How")
In the Environment Variables tab (on the left sidebar of your screenshot):

Add OPENAI_API_KEY: Your OpenAI key.
VITE_API_URL: You do NOT need to set this anymore. I've hardcoded it to default to /api in the Docker build process, so the frontend will automatically talk to the backend via the internal proxy.
Summary of what I changed to make this work:
Docker Compose: Removed port conflicts (replaced 80:80 with expose: 80).
Nginx: Added a rule so that any request to your-site.com/api/... is internally routed to the python backend. This avoids CORS issues and simplifies your domain setup.
Frontend Build: Added configuration to use this relative /api path by default.