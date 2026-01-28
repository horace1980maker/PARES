#!/bin/bash
echo "=== Starting PARES Backend ==="

echo "=== Running document ingestion check ==="
python ingest.py
echo "=== Ingestion check complete ==="

echo "=== Starting Uvicorn server ==="
exec uvicorn main:app --host 0.0.0.0 --port 8000
