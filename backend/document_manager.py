"""
Sistema de gestión de documentos para CATIE PARES
Organiza documentos por organización y país
"""
import os
import json
from datetime import datetime
from typing import Optional

class DocumentManager:
    """Gestiona la organización y metadata de documentos subidos"""
    
    def __init__(self, base_dir: str = "documents"):
        self.base_dir = base_dir
        self.metadata_file = os.path.join(base_dir, "metadata.json")
        self._ensure_structure()
    
    def _ensure_structure(self):
        """Crea la estructura de directorios si no existe"""
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Crear metadata.json si no existe
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump({"documentos": []}, f, ensure_ascii=False, indent=2)
    
    def get_org_folder(self, pais: str, org_id: str) -> str:
        """
        Obtiene la ruta de la carpeta para una organización específica
        Estructura: documentos/{pais}/{org_id}/
        """
        folder = os.path.join(self.base_dir, pais, org_id)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    def save_document(self, 
                     file_path: str, 
                     filename: str,
                     pais: str, 
                     org_id: str,
                     org_nombre: str) -> dict:
        """
        Guarda un documento y registra su metadata
        
        Args:
            file_path: Ruta temporal del archivo subido
            filename: Nombre original del archivo
            pais: País de la organización
            org_id: ID de la organización
            org_nombre: Nombre de la organización
            
        Returns:
            dict con información del documento guardado
        """
        # Obtener carpeta de destino
        org_folder = self.get_org_folder(pais, org_id)
        
        # Generar nombre único para evitar conflictos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        
        # Ruta final del documento
        final_path = os.path.join(org_folder, unique_filename)
        
        # Copiar archivo (en producción, mover desde temp)
        import shutil
        shutil.copy2(file_path, final_path)
        
        # Crear metadata del documento
        doc_metadata = {
            "id": f"{org_id}_{timestamp}",
            "filename": unique_filename,
            "original_filename": filename,
            "path": final_path,
            "pais": pais,
            "org_id": org_id,
            "org_nombre": org_nombre,
            "fecha_subida": datetime.now().isoformat(),
            "procesado_rag": False
        }
        
        # Guardar metadata
        self._add_metadata(doc_metadata)
        
        return doc_metadata
    
    def _add_metadata(self, doc_metadata: dict):
        """Agrega metadata de un documento al registro"""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data["documentos"].append(doc_metadata)
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_org_documents(self, org_id: str) -> list:
        """Obtiene todos los documentos de una organización"""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [doc for doc in data["documentos"] if doc["org_id"] == org_id]
    
    def mark_as_processed(self, doc_id: str):
        """Marca un documento como procesado por el sistema RAG"""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for doc in data["documentos"]:
            if doc["id"] == doc_id:
                doc["procesado_rag"] = True
                break
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
