#!/bin/bash
echo "=== Starting PARES Backend ==="

echo "=== Running document ingestion check ==="
if [ "$REINGEST_ALL" = "true" ]; then
    echo "=== [RE-INGESTION FORCED] ==="
    python ingest.py --reset
else
    python ingest.py
fi
echo "=== Ingestion check complete ==="

echo "=== Starting Uvicorn server ==="
exec uvicorn main:app --host 0.0.0.0 --port 8000
