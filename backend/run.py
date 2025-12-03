"""
Script simple para iniciar el servidor backend de CATIE PARES
"""
import subprocess
import sys

if __name__ == "__main__":
    print("=" * 60)
    print("🌿 CATIE PARES - Servidor Backend")
    print("=" * 60)
    print()
    
    # Ejecutar el servidor con uvicorn
    subprocess.run(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"])
