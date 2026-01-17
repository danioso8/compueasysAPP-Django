"""
Servicio de manejo de archivos
"""
import os
import hashlib
from pathlib import Path
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings


class FileService:
    """Servicio para manejo de archivos y almacenamiento"""
    
    @staticmethod
    def save_file(file, path, organization_id=None):
        """
        Guarda un archivo en el storage
        
        Args:
            file: Archivo (UploadedFile)
            path: Ruta donde guardar
            organization_id: ID de organización (para multi-tenancy)
        
        Returns:
            str: Ruta del archivo guardado
        """
        # Construir ruta con organización si se especifica
        if organization_id:
            path = f"organizations/{organization_id}/{path}"
        
        # Guardar archivo
        file_path = default_storage.save(path, ContentFile(file.read()))
        return file_path
    
    @staticmethod
    def delete_file(path):
        """
        Elimina un archivo del storage
        
        Args:
            path: Ruta del archivo
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            if default_storage.exists(path):
                default_storage.delete(path)
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_file_url(path):
        """
        Obtiene la URL pública de un archivo
        
        Args:
            path: Ruta del archivo
        
        Returns:
            str: URL del archivo
        """
        if not path:
            return None
        
        return default_storage.url(path)
    
    @staticmethod
    def calculate_file_hash(file):
        """
        Calcula el hash MD5 de un archivo
        
        Args:
            file: Archivo a procesar
        
        Returns:
            str: Hash MD5
        """
        md5 = hashlib.md5()
        
        # Resetear puntero del archivo
        file.seek(0)
        
        # Leer en chunks para archivos grandes
        for chunk in file.chunks():
            md5.update(chunk)
        
        # Resetear puntero
        file.seek(0)
        
        return md5.hexdigest()
    
    @staticmethod
    def get_file_size(file):
        """
        Obtiene el tamaño de un archivo en bytes
        
        Args:
            file: Archivo
        
        Returns:
            int: Tamaño en bytes
        """
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        return size
    
    @staticmethod
    def validate_file_extension(filename, allowed_extensions):
        """
        Valida que la extensión del archivo esté permitida
        
        Args:
            filename: Nombre del archivo
            allowed_extensions: Lista de extensiones permitidas (ej: ['.pdf', '.jpg'])
        
        Returns:
            bool: True si la extensión es válida
        """
        ext = Path(filename).suffix.lower()
        return ext in [e.lower() for e in allowed_extensions]
    
    @staticmethod
    def validate_file_size(file, max_size_mb=10):
        """
        Valida que el tamaño del archivo no exceda el límite
        
        Args:
            file: Archivo
            max_size_mb: Tamaño máximo en MB
        
        Returns:
            bool: True si el tamaño es válido
        """
        size_bytes = FileService.get_file_size(file)
        max_size_bytes = max_size_mb * 1024 * 1024
        return size_bytes <= max_size_bytes
    
    @staticmethod
    def get_upload_path(instance, filename, subfolder=''):
        """
        Genera una ruta de upload organizada por fecha y organización
        
        Args:
            instance: Instancia del modelo
            filename: Nombre del archivo
            subfolder: Subcarpeta adicional
        
        Returns:
            str: Ruta generada
        """
        from datetime import datetime
        from ..utils.formatters import slugify_filename
        
        # Slugificar nombre del archivo
        safe_filename = slugify_filename(filename)
        
        # Construir ruta
        date_path = datetime.now().strftime('%Y/%m/%d')
        org_id = getattr(instance, 'organization_id', 'default')
        
        parts = ['uploads', str(org_id)]
        
        if subfolder:
            parts.append(subfolder)
        
        parts.extend([date_path, safe_filename])
        
        return '/'.join(parts)
    
    @staticmethod
    def create_directory(path):
        """
        Crea un directorio si no existe
        
        Args:
            path: Ruta del directorio
        
        Returns:
            bool: True si se creó o ya existía
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def list_files(directory, organization_id=None):
        """
        Lista archivos en un directorio
        
        Args:
            directory: Directorio a listar
            organization_id: Filtrar por organización
        
        Returns:
            list: Lista de rutas de archivos
        """
        if organization_id:
            directory = f"organizations/{organization_id}/{directory}"
        
        try:
            directories, files = default_storage.listdir(directory)
            return files
        except Exception:
            return []
