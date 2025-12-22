"""
Script para subir imágenes locales al servidor de Render
Ejecutar con: python upload_images_to_render.py
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import ProductStore
from django.core.files import File
from pathlib import Path

def upload_local_images():
    """Sube las imágenes del directorio local media_files/images/ a los productos"""
    
    local_images_path = Path(__file__).parent / 'media_files' / 'images'
    
    if not local_images_path.exists():
        print("❌ No existe el directorio media_files/images/")
        return
    
    # Obtener todas las imágenes locales
    images = list(local_images_path.glob('*.jpg')) + list(local_images_path.glob('*.png')) + list(local_images_path.glob('*.webp'))
    
    print(f"\n📁 Encontradas {len(images)} imágenes locales")
    print("="*60)
    
    # Obtener productos sin imagen
    products_without_image = ProductStore.objects.filter(imagen__isnull=True) | ProductStore.objects.filter(imagen='')
    products_with_broken_image = []
    
    # Verificar productos con imagen rota
    for product in ProductStore.objects.exclude(imagen__isnull=True).exclude(imagen=''):
        if product.imagen:
            full_path = Path(product.imagen.path) if hasattr(product.imagen, 'path') else None
            if not full_path or not full_path.exists():
                products_with_broken_image.append(product)
    
    print(f"\n📊 Resumen:")
    print(f"   - Productos sin imagen: {products_without_image.count()}")
    print(f"   - Productos con imagen rota: {len(products_with_broken_image)}")
    print(f"   - Imágenes disponibles localmente: {len(images)}")
    
    print(f"\n📋 Imágenes locales disponibles:")
    for img in images:
        size_kb = img.stat().st_size / 1024
        print(f"   - {img.name} ({size_kb:.1f} KB)")
    
    print("\n" + "="*60)
    print("⚠️  NOTA: Este script solo muestra el estado actual.")
    print("   Para re-asignar imágenes, debes subirlas desde el Dashboard:")
    print("   https://compueasys.onrender.com/dashboard/")
    print("="*60)

if __name__ == '__main__':
    upload_local_images()
