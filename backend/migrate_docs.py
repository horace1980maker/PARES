"""
Script para migrar archivos de documentos/ a documents/
y limpiar la estructura antigua
"""
import os
import shutil

def migrate_documents():
    """Migra archivos de documentos/ a documents/"""
    
    old_dir = "documentos"
    new_dir = "documents"
    
    if not os.path.exists(old_dir):
        print(f"✅ No hay carpeta '{old_dir}' para migrar")
        return
    
    print(f"🔄 Migrando archivos de '{old_dir}/' a '{new_dir}/'...")
    
    # Crear directorio nuevo si no existe
    os.makedirs(new_dir, exist_ok=True)
    
    # Copiar todos los archivos
    migrated = 0
    for root, dirs, files in os.walk(old_dir):
        for file in files:
            if file == "metadata.json":
                continue  # Skip metadata, se recreará
            
            old_path = os.path.join(root, file)
            
            # Calcular ruta relativa y crear en nuevo directorio
            rel_path = os.path.relpath(old_path, old_dir)
            new_path = os.path.join(new_dir, rel_path)
            
            # Crear subdirectorios si es necesario
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # Copiar archivo
            shutil.copy2(old_path, new_path)
            print(f"  ✓ {old_path} → {new_path}")
            migrated += 1
    
    print(f"\n✅ Migrados {migrated} archivos")
    
    # Preguntar si eliminar carpeta antigua
    print(f"\n⚠️  La carpeta '{old_dir}/' ya no se usa.")
    print(f"   Puedes eliminarla manualmente si lo deseas.")
    print(f"   Comando: Remove-Item -Recurse -Force {old_dir}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Migración de Documentos")
    print("=" * 60)
    print()
    migrate_documents()
