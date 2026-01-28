#!/bin/bash
echo "=== Starting PARES Backend ==="

# Run ingestion if chroma_db is empty or doesn't have the sqlite file
if [ ! -f "/app/chroma_db/chroma.sqlite3" ]; then
    echo "=== Running initial document ingestion ==="
    python ingest.py
    echo "=== Ingestion complete ==="
fi

echo "=== Starting Uvicorn server ==="
exec uvicorn main:app --host 0.0.0.0 --port 8000
