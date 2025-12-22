"""
Script para migrar imágenes de Cloudinary al disco persistente de Render
Autor: CompuEasys
Fecha: Diciembre 2025

Este script:
1. Descarga todas las imágenes de Cloudinary
2. Las guarda en el disco local/persistente
3. Actualiza las referencias en la base de datos
4. Muestra progreso y estadísticas

Uso:
    python migrate_cloudinary_to_render.py
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


class CloudinaryMigrator:
    """Migrador de imágenes de Cloudinary a disco persistente"""
    
    def __init__(self):
        self.stats = {
            'productos_procesados': 0,
            'productos_migrados': 0,
            'galerias_procesadas': 0,
            'galerias_migradas': 0,
            'variantes_procesadas': 0,
            'variantes_migradas': 0,
            'errores': []
        }
    
    def is_cloudinary_url(self, url):
        """Verifica si una URL es de Cloudinary"""
        if not url:
            return False
        return 'cloudinary' in url.lower() or 'res.cloudinary.com' in url.lower()
    
    def download_image(self, url, timeout=30):
        """Descarga una imagen desde una URL"""
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Error descargando imagen: {e}")
    
    def get_filename_from_url(self, url):
        """Extrae el nombre del archivo de una URL"""
        parsed = urlparse(url)
        # Obtener el último segmento del path
        path_parts = parsed.path.split('/')
        filename = path_parts[-1]
        
        # Si no tiene extensión, intentar obtenerla de la URL
        if '.' not in filename:
            # Buscar extensión común en la URL
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                if ext in url.lower():
                    filename += ext
                    break
            else:
                filename += '.jpg'  # Default
        
        return filename
    
    def migrate_product_images(self):
        """Migra imágenes principales de productos"""
        print("\n" + "="*60)
        print("MIGRANDO IMÁGENES PRINCIPALES DE PRODUCTOS")
        print("="*60)
        
        productos = ProductStore.objects.all()
        total = productos.count()
        
        for idx, producto in enumerate(productos, 1):
            self.stats['productos_procesados'] += 1
            
            if not producto.imagen:
                print(f"[{idx}/{total}] ⊘ {producto.name}: Sin imagen")
                continue
            
            if not self.is_cloudinary_url(producto.imagen.url):
                print(f"[{idx}/{total}] ⊘ {producto.name}: No es de Cloudinary")
                continue
            
            try:
                print(f"[{idx}/{total}] ⬇ {producto.name}: Descargando...")
                
                # Descargar imagen
                image_content = self.download_image(producto.imagen.url)
                
                # Obtener nombre del archivo
                filename = self.get_filename_from_url(producto.imagen.url)
                
                # Guardar en el modelo (Django se encarga de la ruta)
                producto.imagen.save(
                    filename,
                    ContentFile(image_content),
                    save=True
                )
                
                self.stats['productos_migrados'] += 1
                print(f"[{idx}/{total}] ✓ {producto.name}: Migrado exitosamente")
                
            except Exception as e:
                error_msg = f"Producto {producto.name} (ID: {producto.id}): {str(e)}"
                self.stats['errores'].append(error_msg)
                print(f"[{idx}/{total}] ✗ {producto.name}: ERROR - {e}")
    
    def migrate_gallery_images(self):
        """Migra imágenes de galería"""
        print("\n" + "="*60)
        print("MIGRANDO IMÁGENES DE GALERÍA")
        print("="*60)
        
        galerias = Galeria.objects.all()
        total = galerias.count()
        
        for idx, galeria in enumerate(galerias, 1):
            self.stats['galerias_procesadas'] += 1
            
            if not galeria.galeria:
                print(f"[{idx}/{total}] ⊘ Galería {galeria.id}: Sin imagen")
                continue
            
            if not self.is_cloudinary_url(galeria.galeria.url):
                print(f"[{idx}/{total}] ⊘ Galería {galeria.id}: No es de Cloudinary")
                continue
            
            try:
                producto_name = galeria.product.name if galeria.product else "Sin producto"
                print(f"[{idx}/{total}] ⬇ Galería {galeria.id} ({producto_name}): Descargando...")
                
                # Descargar imagen
                image_content = self.download_image(galeria.galeria.url)
                
                # Obtener nombre del archivo
                filename = self.get_filename_from_url(galeria.galeria.url)
                
                # Guardar en el modelo
                galeria.galeria.save(
                    filename,
                    ContentFile(image_content),
                    save=True
                )
                
                self.stats['galerias_migradas'] += 1
                print(f"[{idx}/{total}] ✓ Galería {galeria.id}: Migrado exitosamente")
                
            except Exception as e:
                error_msg = f"Galería {galeria.id}: {str(e)}"
                self.stats['errores'].append(error_msg)
                print(f"[{idx}/{total}] ✗ Galería {galeria.id}: ERROR - {e}")
    
    def migrate_variant_images(self):
        """Migra imágenes de variantes de productos"""
        print("\n" + "="*60)
        print("MIGRANDO IMÁGENES DE VARIANTES")
        print("="*60)
        
        variantes = ProductVariant.objects.all()
        total = variantes.count()
        
        for idx, variante in enumerate(variantes, 1):
            self.stats['variantes_procesadas'] += 1
            
            if not variante.imagen:
                print(f"[{idx}/{total}] ⊘ {variante.nombre}: Sin imagen")
                continue
            
            if not self.is_cloudinary_url(variante.imagen.url):
                print(f"[{idx}/{total}] ⊘ {variante.nombre}: No es de Cloudinary")
                continue
            
            try:
                print(f"[{idx}/{total}] ⬇ {variante.nombre}: Descargando...")
                
                # Descargar imagen
                image_content = self.download_image(variante.imagen.url)
                
                # Obtener nombre del archivo
                filename = self.get_filename_from_url(variante.imagen.url)
                
                # Guardar en el modelo
                variante.imagen.save(
                    filename,
                    ContentFile(image_content),
                    save=True
                )
                
                self.stats['variantes_migradas'] += 1
                print(f"[{idx}/{total}] ✓ {variante.nombre}: Migrado exitosamente")
                
            except Exception as e:
                error_msg = f"Variante {variante.nombre} (ID: {variante.id}): {str(e)}"
                self.stats['errores'].append(error_msg)
                print(f"[{idx}/{total}] ✗ {variante.nombre}: ERROR - {e}")
    
    def print_summary(self):
        """Imprime resumen de la migración"""
        print("\n" + "="*60)
        print("RESUMEN DE MIGRACIÓN")
        print("="*60)
        
        print(f"\n📦 PRODUCTOS:")
        print(f"   Procesados: {self.stats['productos_procesados']}")
        print(f"   Migrados:   {self.stats['productos_migrados']}")
        
        print(f"\n🖼️  GALERÍA:")
        print(f"   Procesadas: {self.stats['galerias_procesadas']}")
        print(f"   Migradas:   {self.stats['galerias_migradas']}")
        
        print(f"\n🎨 VARIANTES:")
        print(f"   Procesadas: {self.stats['variantes_procesadas']}")
        print(f"   Migradas:   {self.stats['variantes_migradas']}")
        
        total_migradas = (
            self.stats['productos_migrados'] +
            self.stats['galerias_migradas'] +
            self.stats['variantes_migradas']
        )
        
        print(f"\n✅ TOTAL IMÁGENES MIGRADAS: {total_migradas}")
        
        if self.stats['errores']:
            print(f"\n❌ ERRORES ({len(self.stats['errores'])}):")
            for error in self.stats['errores'][:10]:  # Mostrar solo primeros 10
                print(f"   • {error}")
            if len(self.stats['errores']) > 10:
                print(f"   ... y {len(self.stats['errores']) - 10} errores más")
        else:
            print("\n✨ Sin errores!")
        
        print("\n" + "="*60)
    
    def run(self):
        """Ejecuta la migración completa"""
        print("\n🚀 INICIANDO MIGRACIÓN DE CLOUDINARY A RENDER")
        print(f"📁 MEDIA_ROOT: {os.getenv('MEDIA_ROOT', 'media_files/')}")
        
        # Confirmar antes de proceder
        response = input("\n¿Desea continuar con la migración? (s/n): ")
        if response.lower() not in ['s', 'si', 'yes', 'y']:
            print("❌ Migración cancelada")
            return
        
        # Ejecutar migraciones
        self.migrate_product_images()
        self.migrate_gallery_images()
        self.migrate_variant_images()
        
        # Mostrar resumen
        self.print_summary()
        
        print("\n✅ Migración completada!")
        print("💡 Ahora puedes eliminar las credenciales de Cloudinary de tu .env")


def main():
    """Función principal"""
    migrator = CloudinaryMigrator()
    migrator.run()


if __name__ == '__main__':
    main()
