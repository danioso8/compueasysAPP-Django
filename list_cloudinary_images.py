"""
Script para listar todas las imágenes en Cloudinary
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

import cloudinary
import cloudinary.api
from django.conf import settings

def list_cloudinary_resources():
    """Lista todos los recursos en Cloudinary"""
    
    print("\n" + "="*60)
    print("LISTADO DE IMÁGENES EN CLOUDINARY")
    print("="*60)
    
    print(f"\n☁️  Cloud Name: {settings.CLOUDINARY_STORAGE['CLOUD_NAME'] if hasattr(settings, 'CLOUDINARY_STORAGE') else 'N/A'}")
    
    try:
        # Listar todos los recursos
        result = cloudinary.api.resources(
            type="upload",
            max_results=500,
            resource_type="image"
        )
        
        resources = result.get('resources', [])
        total = len(resources)
        
        print(f"\n📊 Total de imágenes encontradas: {total}\n")
        
        if total == 0:
            print("⚠️  No se encontraron imágenes en Cloudinary")
            return
        
        # Organizar por carpeta
        folders = {}
        for resource in resources:
            public_id = resource['public_id']
            folder = public_id.split('/')[0] if '/' in public_id else 'root'
            
            if folder not in folders:
                folders[folder] = []
            
            folders[folder].append({
                'public_id': public_id,
                'url': resource['secure_url'],
                'format': resource['format'],
                'size_kb': round(resource['bytes'] / 1024, 2),
                'width': resource.get('width', 0),
                'height': resource.get('height', 0),
                'created_at': resource['created_at']
            })
        
        # Mostrar por carpetas
        for folder, images in sorted(folders.items()):
            print(f"\n📁 {folder.upper()}/ ({len(images)} imágenes)")
            print("-" * 60)
            
            for idx, img in enumerate(images, 1):
                print(f"\n  [{idx}] {img['public_id']}")
                print(f"      URL: {img['url']}")
                print(f"      Formato: {img['format']} | Tamaño: {img['size_kb']} KB")
                print(f"      Dimensiones: {img['width']}x{img['height']} px")
                print(f"      Creado: {img['created_at']}")
        
        # Resumen de tamaño
        total_size_kb = sum(img['size_kb'] for images in folders.values() for img in images)
        total_size_mb = round(total_size_kb / 1024, 2)
        
        print("\n" + "="*60)
        print(f"💾 TAMAÑO TOTAL: {total_size_mb} MB ({total_size_kb} KB)")
        print("="*60)
        
        # Listar también por carpetas específicas si existen
        print("\n\n🔍 Buscando en carpetas específicas...")
        for folder_name in ['images', 'galeria', 'variant_images', 'videos', 'upload']:
            try:
                folder_result = cloudinary.api.resources(
                    type="upload",
                    prefix=f"{folder_name}/",
                    max_results=100
                )
                count = len(folder_result.get('resources', []))
                if count > 0:
                    print(f"  ✓ {folder_name}/: {count} archivos")
            except Exception as e:
                print(f"  - {folder_name}/: No encontrada o vacía")
        
    except cloudinary.api.Error as e:
        print(f"\n❌ Error de Cloudinary API: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    list_cloudinary_resources()
