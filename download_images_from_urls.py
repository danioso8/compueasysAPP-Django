"""
Script para descargar imágenes desde URLs de Cloudinary y actualizar referencias en la base de datos
"""
import os
import sys
import django
import requests
from pathlib import Path
from urllib.parse import urlparse
from django.core.files import File
from django.core.files.base import ContentFile

# Configurar Django
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import ProductStore, Galeria, ProductVariant

def download_image_from_url(url, save_path):
    """Descarga una imagen desde una URL y retorna el contenido"""
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Guardar en archivo
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # También retornar el contenido para Django
        response = requests.get(url, timeout=30)
        return response.content
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None

def ensure_dir(directory):
    """Asegura que un directorio existe"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_all_images():
    """Descarga todas las imágenes desde las URLs en la base de datos"""
    
    base_dir = Path(__file__).resolve().parent
    media_root = base_dir / 'media_files'
    
    print("\n" + "="*60)
    print("DESCARGANDO IMÁGENES DESDE URLs DE LA BASE DE DATOS")
    print("="*60)
    
    stats = {
        'productos': {'total': 0, 'descargados': 0},
        'galeria': {'total': 0, 'descargados': 0},
        'variantes': {'total': 0, 'descargados': 0}
    }
    
    # Productos
    print("\n📦 PRODUCTOS:")
    productos = ProductStore.objects.filter(imagen__isnull=False)
    stats['productos']['total'] = productos.count()
    
    for idx, producto in enumerate(productos, 1):
        if producto.imagen:
            url = producto.imagen.url
            print(f"\n[{idx}/{stats['productos']['total']}] {producto.name}")
            print(f"  URL: {url}")
             or '?' in filename:
                filename = f"producto_{producto.id}.jpg"
            
            # Limpiar nombre de archivo
            filename = filename.split('?')[0]
            
            # Crear directorio
            save_dir = media_root / 'images'
            ensure_dir(save_dir)
            
            # Ruta completa
            save_path = save_dir / filename
            
            print(f"  Guardando en: {save_path}")
            print(f"  Relación: Producto ID {producto.id}")
            
            content = download_image_from_url(url, save_path)
            if content:
                # Actualizar referencia en la base de datos
                producto.imagen.save(filename, ContentFile(content), save=True)
                stats['productos']['descargados'] += 1
                print(f"  ✓ Descargado y actualizado en DB
            if download_image_from_url(url, save_path):
                stats['productos']['descargados'] += 1.select_related('product')
    stats['galeria']['total'] = galerias.count()
    
    for idx, galeria in enumerate(galerias, 1):
        if galeria.galeria:
            url = galeria.galeria.url
            producto_name = galeria.product.name if galeria.product else "Sin producto"
            producto_id = galeria.product.id if galeria.product else "N/A"
            
            print(f"\n[{idx}/{stats['galeria']['total']}] Galería {galeria.id}")
            print(f"  Producto: {producto_name} (ID: {producto_id})")
            print(f"  URL: {url}")
            
            # Obtener nombre del archivo
            filename = os.path.basename(urlparse(url).path)
            if not filename or '?' in filename:
                filename = f"galeria_{galeria.id}.jpg"
            
            # Limpiar nombre de archivo
            filename = filename.split('?')[0]
            
            # Crear directorio
            save_dir = media_root / 'galeria'
            ensure_dir(save_dir)
            
            # Ruta completa
            save_path = save_dir / filename
            
            print(f"  Guardando en: {save_path}")
            print(f"  Relación: Producto ID {producto_id} → Galería ID {galeria.id}")
            
            content = download_image_from_url(url, save_path)
            if content:.select_related('product')
    stats['variantes']['total'] = variantes.count()
    
    for idx, variante in enumerate(variantes, 1):
        if variante.imagen:
            url = variante.imagen.url
            producto_name = variante.product.name if variante.product else "Sin producto"
            producto_id = variante.product.id if variante.product else "N/A"
            
            print(f"\n[{idx}/{stats['variantes']['total']}] {variante.nombre}")
            print(f"  Producto: {producto_name} (ID: {producto_id})")
            print(f"  URL: {url}")
            
            # Obtener nombre del archivo
            filename = os.path.basename(urlparse(url).path)
            if not filename or '?' in filename:
                filename = f"variante_{variante.id}.jpg"
            
            # Limpiar nombre de archivo
            filename = filename.split('?')[0]
            
            # Crear directorio
            save_dir = media_root / 'variant_images'
            ensure_dir(save_dir)
            
            # Ruta completa
            save_path = save_dir / filename
            
            print(f"  Guardando en: {save_path}")
            print(f"  Relación: Producto ID {producto_id} → Variante '{variante.nombre}'")
            
            content = download_image_from_url(url, save_path)
            if content:
                # Actualizar referencia en la base de datos manteniendo la relación con el producto
                variante.imagen.save(filename, ContentFile(content), save=True)
                stats['variantes']['descargados'] += 1
                print(f"  ✓ Descargado y actualizado en DB (mantiene relación con producto)
            # Obtener nombre del archivo
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = f"variante_{variante.id}.jpg"
            
            # Crear directorio
            save_dir = media_root / 'variant_images'
            ensure_dir(save_dir)
            
            # Ruta completa
            save_path = save_dir / filename
            
            print(f"  Guardando en: {save_path}")
            
            if download_image_from_url(url, save_path):
                stats['variantes']['descargados'] += 1
                print(f"  ✓ Descargado")
            else:
                print(f"  ✗ Falló")
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE DESCARGAS")
    print("="*60)
    
    print(f"\n📦 PRODUCTOS:")
    print(f"   Total: {stats['productos']['total']}")
    print(f"   Descargados: {stats['productos']['descargados']}")
    
    print(f"\n🖼️  GALERÍA:")
    print(f"   Total: {stats['galeria']['total']}")
    print(f"   Descargados: {stats['galeria']['descargados']}")
    
    print(f"\n🎨 VARIANTES:")
    print(f"   Total: {stats['variantes']['total']}")
    print(f"   Descargados: {stats['variantes']['descargados']}")
    
    total = sum(s['total'] for s in stats.values())
    descargados = sum(s['descargados'] for s in stats.values())
    
    print(f"\n✅ TOTAL: {descargados}/{total} imágenes descargadas")
    print("="*60)

if __name__ == '__main__':
    download_all_images()
