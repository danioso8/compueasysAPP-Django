"""
Script para descargar TODAS las imágenes desde Render
Descarga imágenes de productos, galerías y variantes desde Render
"""
import os
import sys
from pathlib import Path
import django
import requests
from datetime import datetime

# Configurar Django
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import ProductStore, Galeria, ProductVariant
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent
RENDER_BASE_URL = "https://compueasys.onrender.com"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')

def create_download_directories():
    """Crear directorios para descargar imágenes directamente en media_files"""
    
    directories = {
        'products': os.path.join(MEDIA_ROOT, 'images'),
        'gallery': os.path.join(MEDIA_ROOT, 'galeria'),
        'variants': os.path.join(MEDIA_ROOT, 'variant_images'),
        'upload': os.path.join(MEDIA_ROOT, 'upload'),
    }
    
    for dir_path in directories.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return directories

def download_image(image_path, destination_path):
    """Descargar una imagen desde Render"""
    
    try:
        # Construir URL completa
        if image_path.startswith('http'):
            url = image_path
        else:
            # Asegurar que la ruta comienza con /media/
            if not image_path.startswith('/media/'):
                image_path = '/media/' + image_path
            url = RENDER_BASE_URL + image_path
        
        # Crear directorio destino si no existe
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Descargar imagen
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Guardar imagen
        with open(destination_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, os.path.getsize(destination_path)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, "404 Not Found"
        return False, f"HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)[:30]}"
    except Exception as e:
        return False, str(e)[:30]

def download_product_images(directories):
    """Descargar imágenes de productos desde Render"""
    
    print("=" * 80)
    print("📦 DESCARGANDO IMÁGENES DE PRODUCTOS DESDE RENDER")
    print("=" * 80)
    print()
    
    products = ProductStore.objects.all()
    total = products.count()
    downloaded = 0
    failed = 0
    skipped = 0
    
    print(f"Total de productos: {total}")
    print()
    
    for i, product in enumerate(products, 1):
        if product.imagen:
            # Ruta de la imagen en Render
            image_path = str(product.imagen)
            
            # Nombre del archivo
            image_name = os.path.basename(image_path)
            destination = os.path.join(directories['products'], image_name)
            
            print(f"[{i}/{total}] {product.name[:40]:<40} ", end='')
            
            # Verificar si ya existe
            if os.path.exists(destination):
                print(f"⏭️  Ya existe")
                skipped += 1
                continue
            
            success, result = download_image(image_path, destination)
            
            if success:
                size_kb = result / 1024
                print(f"✅ ({size_kb:.1f} KB)")
                downloaded += 1
            else:
                print(f"❌ {result}")
                failed += 1
        else:
            print(f"[{i}/{total}] {product.name[:40]:<40} ⚠️  Sin imagen")
    
    print()
    print(f"✅ Descargadas: {downloaded}")
    print(f"⏭️  Ya existían: {skipped}")
    print(f"❌ Fallidas: {failed}")
    print(f"⚠️  Sin imagen: {total - downloaded - failed - skipped}")
    print()
    
    return downloaded, failed

def download_gallery_images(directories):
    """Descargar imágenes de galerías desde Render"""
    
    print("=" * 80)
    print("🖼️  DESCARGANDO IMÁGENES DE GALERÍAS DESDE RENDER")
    print("=" * 80)
    print()
    
    galleries = Galeria.objects.all()
    total = galleries.count()
    downloaded = 0
    failed = 0
    skipped = 0
    
    print(f"Total de imágenes de galería: {total}")
    print()
    
    for i, gallery in enumerate(galleries, 1):
        if gallery.galeria:
            # Ruta de la imagen en Render
            image_path = str(gallery.galeria)
            image_name = os.path.basename(image_path)
            destination = os.path.join(directories['gallery'], image_name)
            
            product_name = gallery.product.name if gallery.product else "Sin producto"
            print(f"[{i}/{total}] {product_name[:40]:<40} ", end='')
            
            # Verificar si ya existe
            if os.path.exists(destination):
                print(f"⏭️  Ya existe")
                skipped += 1
                continue
            
            success, result = download_image(image_path, destination)
            
            if success:
                size_kb = result / 1024
                print(f"✅ ({size_kb:.1f} KB)")
                downloaded += 1
            else:
                print(f"❌ {result}")
                failed += 1
        else:
            print(f"[{i}/{total}] Galería #{gallery.id:<38} ⚠️  Sin imagen")
    
    print()
    print(f"✅ Descargadas: {downloaded}")
    print(f"⏭️  Ya existían: {skipped}")
    print(f"❌ Fallidas: {failed}")
    print()
    
    return downloaded, failed

def download_variant_images(directories):
    """Descargar imágenes de variantes desde Render"""
    
    print("=" * 80)
    print("🎨 DESCARGANDO IMÁGENES DE VARIANTES DESDE RENDER")
    print("=" * 80)
    print()
    
    variants = ProductVariant.objects.all()
    total = variants.count()
    downloaded = 0
    failed = 0
    skipped = 0
    
    print(f"Total de variantes: {total}")
    print()
    
    for i, variant in enumerate(variants, 1):
        if variant.imagen:
            # Ruta de la imagen en Render
            image_path = str(variant.imagen)
            image_name = os.path.basename(image_path)
            destination = os.path.join(directories['variants'], image_name)
            
            variant_name = f"{variant.product.name} - {variant.color or variant.talla or 'Variante'}"
            print(f"[{i}/{total}] {variant_name[:40]:<40} ", end='')
            
            # Verificar si ya existe
            if os.path.exists(destination):
                print(f"⏭️  Ya existe")
                skipped += 1
                continue
            
            success, result = download_image(image_path, destination)
            
            if success:
                size_kb = result / 1024
                print(f"✅ ({size_kb:.1f} KB)")
                downloaded += 1
            else:
                print(f"❌ {result}")
                failed += 1
        else:
            print(f"[{i}/{total}] Variante #{variant.id:<36} ⚠️  Sin imagen")
    
    print()
    print(f"✅ Descargadas: {downloaded}")
    print(f"⏭️  Ya existían: {skipped}")
    print(f"❌ Fallidas: {failed}")
    print()
    
    return downloaded, failed

def create_migration_report(stats, directories):
    """Crear reporte de descarga"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(BASE_DIR, f'download_report_{timestamp}.txt')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE DESCARGA DE IMÁGENES - COMPUEASYS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Origen: {RENDER_BASE_URL}/media/\n\n")
        
        f.write("RESUMEN DE DESCARGA:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Productos descargados: {stats['products_downloaded']}\n")
        f.write(f"Productos fallidos: {stats['products_failed']}\n")
        f.write(f"Galerías descargadas: {stats['gallery_downloaded']}\n")
        f.write(f"Galerías fallidas: {stats['gallery_failed']}\n")
        f.write(f"Variantes descargadas: {stats['variants_downloaded']}\n")
        f.write(f"Variantes fallidas: {stats['variants_failed']}\n")
        f.write(f"\nTotal exitoso: {stats['total_downloaded']}\n")
        f.write(f"Total fallido: {stats['total_failed']}\n\n")
        
        f.write("UBICACIONES DE DESCARGA:\n")
        f.write("-" * 80 + "\n")
        for name, path in directories.items():
            # Contar archivos en cada directorio
            if os.path.exists(path):
                file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                f.write(f"{name}: {path} ({file_count} archivos)\n")
        f.write("\n")
        
        # Calcular tamaño total
        total_size = 0
        file_count = 0
        for dir_path in directories.values():
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            total_size += os.path.getsize(file_path)
                            file_count += 1
        
        total_size_mb = total_size / (1024 * 1024)
        f.write(f"Total de archivos descargados: {file_count}\n")
        f.write(f"Tamaño total: {total_size_mb:.2f} MB\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("SIGUIENTE PASO: Subir a Contabo\n")
        f.write("Comando: upload_to_contabo.bat\n")
        f.write("=" * 80 + "\n")
    
    return report_file

def main():
    print()
    print("=" * 80)
    print("📥 DESCARGA DE IMÁGENES DESDE RENDER")
    print("=" * 80)
    print()
    print(f"🌐 Servidor: {RENDER_BASE_URL}")
    print()
    
    # Crear directorios
    print("📁 Creando estructura de directorios...")
    directories = create_download_directories()
    print("   ✅ Directorios creados en media_files/")
    print()
    
    # Estadísticas
    stats = {
        'products_downloaded': 0,
        'products_failed': 0,
        'gallery_downloaded': 0,
        'gallery_failed': 0,
        'variants_downloaded': 0,
        'variants_failed': 0,
    }
    
    # Descargar imágenes de productos
    p_down, p_fail = download_product_images(directories)
    stats['products_downloaded'] = p_down
    stats['products_failed'] = p_fail
    
    # Descargar imágenes de galerías
    g_down, g_fail = download_gallery_images(directories)
    stats['gallery_downloaded'] = g_down
    stats['gallery_failed'] = g_fail
    
    # Descargar imágenes de variantes
    v_down, v_fail = download_variant_images(directories)
    stats['variants_downloaded'] = v_down
    stats['variants_failed'] = v_fail
    
    # Calcular totales
    stats['total_downloaded'] = p_down + g_down + v_down
    stats['total_failed'] = p_fail + g_fail + v_fail
    
    # Crear reporte
    print("=" * 80)
    print("📄 CREANDO REPORTE")
    print("=" * 80)
    print()
    
    report_file = create_migration_report(stats, directories)
    print(f"✅ Reporte guardado en: {report_file}")
    print()
    
    # Resumen final
    print("=" * 80)
    print("✅ DESCARGA COMPLETADA")
    print("=" * 80)
    print()
    print("📊 Resumen:")
    print(f"   • Imágenes descargadas: {stats['total_downloaded']}")
    print(f"   • Imágenes fallidas: {stats['total_failed']}")
    print(f"   • Ubicación: {os.path.join(BASE_DIR, 'media_files')}")
    print()
    print("🚀 Siguiente paso:")
    print("   Ejecuta: upload_to_contabo.bat")
    print()
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error crítico: {str(e)}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir...")
