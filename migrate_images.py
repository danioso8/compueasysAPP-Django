#!/usr/bin/env python
"""
Script para migrar imágenes locales a Cloudinary
Ejecutar después de configurar Cloudinary en producción
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

import cloudinary.uploader
from core.models import ProductStore, Galeria

def migrate_images_to_cloudinary():
    """Migra todas las imágenes de productos y galerías a Cloudinary"""
    print("🔄 Iniciando migración de imágenes a Cloudinary...")
    
    migrated_count = 0
    error_count = 0
    
    # Migrar imágenes principales de productos
    products = ProductStore.objects.filter(imagen__isnull=False).exclude(imagen='')
    print(f"📦 Encontrados {products.count()} productos con imágenes")
    
    for product in products:
        try:
            if product.imagen and hasattr(product.imagen, 'path'):
                # Solo migrar si es archivo local
                if product.imagen.path and os.path.exists(product.imagen.path):
                    print(f"📤 Subiendo imagen de producto: {product.name}")
                    
                    # Subir a Cloudinary
                    response = cloudinary.uploader.upload(
                        product.imagen.path,
                        folder="compueasys/products",
                        public_id=f"product_{product.id}_{product.name.replace(' ', '_')}",
                        resource_type="image"
                    )
                    
                    # Actualizar URL en el modelo
                    product.imagen = response['secure_url']
                    product.save()
                    
                    print(f"✅ Migrado: {product.name} -> {response['secure_url']}")
                    migrated_count += 1
                
        except Exception as e:
            print(f"❌ Error migrando {product.name}: {str(e)}")
            error_count += 1
    
    # Migrar imágenes de galería
    galerias = Galeria.objects.filter(galeria__isnull=False).exclude(galeria='')
    print(f"🖼️ Encontradas {galerias.count()} imágenes de galería")
    
    for galeria in galerias:
        try:
            if galeria.galeria and hasattr(galeria.galeria, 'path'):
                if galeria.galeria.path and os.path.exists(galeria.galeria.path):
                    print(f"📤 Subiendo imagen de galería del producto: {galeria.product.name}")
                    
                    response = cloudinary.uploader.upload(
                        galeria.galeria.path,
                        folder="compueasys/gallery",
                        public_id=f"gallery_{galeria.id}_{galeria.product.name.replace(' ', '_')}",
                        resource_type="image"
                    )
                    
                    galeria.galeria = response['secure_url']
                    galeria.save()
                    
                    print(f"✅ Migrada galería: {galeria.product.name} -> {response['secure_url']}")
                    migrated_count += 1
                    
        except Exception as e:
            print(f"❌ Error migrando galería: {str(e)}")
            error_count += 1
    
    print(f"\n🎉 Migración completada!")
    print(f"✅ Imágenes migradas: {migrated_count}")
    print(f"❌ Errores: {error_count}")
    
    if error_count == 0:
        print("🔥 ¡Todas las imágenes fueron migradas exitosamente!")
        print("🚀 Ya puedes hacer deploy sin perder imágenes")
    else:
        print("⚠️ Revisa los errores arriba y vuelve a ejecutar si es necesario")

if __name__ == "__main__":
    migrate_images_to_cloudinary()