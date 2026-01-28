FROM python:3.11

WORKDIR /app

# Asegurar que logs de python se vean en consola docker
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema mínimas (python:3.11 ya trae muchas)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 1. Actualizar pip
# 2. Instalar antemano PyTorch CPU (mucho más ligero y estable para build)
# 3. Instalar resto de requerimientos
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear directorio para la DB si no existe (el volumen se montará aquí)
RUN mkdir -p /app/chroma_db

# Copiar y dar permisos al script de inicio
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Exponer el puerto
EXPOSE 8000

# Comando para arrancar la aplicación (usa script que hace ingest primero)
CMD ["/app/start.sh"]
