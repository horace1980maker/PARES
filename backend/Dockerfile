FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema para PyMuPDF y otros
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements desde la raíz (el contexto de build debe ser la raíz o backend necesita su propio req)
# Asumiremos que el contexto de build será la carpeta backend o la raíz
# Si es la raíz, la ruta es ./requirements.txt. Si es backend, es ./requirements.txt
# Vamos a asumir que el archivo requirements.txt está en la carpeta backend para el build context de backend
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear directorio para la DB si no existe (el volumen se montará aquí)
RUN mkdir -p /app/chroma_db

# Exponer el puerto
EXPOSE 8000

# Comando para arrancar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
