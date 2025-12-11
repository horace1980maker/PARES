"""
Script para iniciar el servidor backend de CATIE PARES
Con configuracion de encoding para Windows
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    # FIX: Set UTF-8 encoding and unbuffered output for Windows
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    print("=" * 60)
    print("CATIE PARES - Servidor Backend")
    print("=" * 60)
    print()
    
    # Run uvicorn using the same Python interpreter (preserves venv)
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
        env={
            **os.environ, 
            "PYTHONIOENCODING": "utf-8", 
            "PYTHONUTF8": "1",
            "PYTHONUNBUFFERED": "1"
        }
    )
