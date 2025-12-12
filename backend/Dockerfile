FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema esenciales y para compilación
# build-essential: gcc/g++ para compilar extensiones
# curl: útil para debugging
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Actualizar pip y wheel para asegurar instalación binaria (wheels) y evitar compilación innecesaria
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear directorio para la DB si no existe (el volumen se montará aquí)
RUN mkdir -p /app/chroma_db

# Exponer el puerto
EXPOSE 8000

# Comando para arrancar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
