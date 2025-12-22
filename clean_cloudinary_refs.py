#!/usr/bin/env python
"""
Script para limpiar referencias a Cloudinary en la base de datos
y reemplazarlas con URLs locales del disco persistente de Render.

Este script es útil después de migrar de Cloudinary a almacenamiento local.

IMPORTANTE: Ejecutar solo si tienes las imágenes localmente.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import ProductStore, Galeria, ProductVariant
from django.db.models import Q

def clean_cloudinary_references():
    """
    Limpia las referencias a Cloudinary que devuelven 401 Unauthorized.
    
    Opciones:
    1. Eliminar las referencias (campo = None)
    2. Dejar las referencias pero marcar como no disponibles
    """
    
    print("=" * 60)
    print("LIMPIEZA DE REFERENCIAS A CLOUDINARY")
    print("=" * 60)
    print()
    
    # Contar referencias a Cloudinary
    products_with_cloudinary = ProductStore.objects.filter(
        Q(imagen__icontains='cloudinary') | Q(imagen__icontains='res.cloudinary.com')
    )
    
    gallery_with_cloudinary = Galeria.objects.filter(
        Q(galeria__icontains='cloudinary') | Q(galeria__icontains='res.cloudinary.com')
    )
    
    variants_with_cloudinary = ProductVariant.objects.filter(
        Q(imagen__icontains='cloudinary') | Q(imagen__icontains='res.cloudinary.com')
    )
    
    products_count = products_with_cloudinary.count()
    gallery_count = gallery_with_cloudinary.count()
    variants_count = variants_with_cloudinary.count()
    
    total = products_count + gallery_count + variants_count
    
    print(f"📊 Referencias encontradas:")
    print(f"   - Productos: {products_count}")
    print(f"   - Galería: {gallery_count}")
    print(f"   - Variantes: {variants_count}")
    print(f"   - TOTAL: {total}")
    print()
    
    if total == 0:
        print("✅ No hay referencias a Cloudinary. Todo limpio!")
        return
    
    print("⚠️  ADVERTENCIA:")
    print("   Estas imágenes están en Cloudinary y devuelven Error 401")
    print("   porque la cuenta excedió el límite gratuito.")
    print()
    print("📋 Opciones:")
    print("   1. Limpiar referencias (eliminar campo imagen)")
    print("   2. Mantener referencias (esperar a renovación el 1 Enero 2026)")
    print("   3. Cancelar (no hacer nada)")
    print()
    
    opcion = input("Selecciona una opción [1/2/3]: ").strip()
    
    if opcion == "1":
        print("\n🗑️  Limpiando referencias a Cloudinary...")
        
        # Limpiar productos
        for product in products_with_cloudinary:
            print(f"   - Limpiando producto: {product.name}")
            product.imagen = None
            product.save()
        
        # Limpiar galería
        for img in gallery_with_cloudinary:
            print(f"   - Limpiando galería ID: {img.id}")
            img.delete()  # Eliminar entrada de galería sin imagen
        
        # Limpiar variantes
        for variant in variants_with_cloudinary:
            print(f"   - Limpiando variante: {variant.nombre}")
            variant.imagen = None
            variant.save()
        
        print(f"\n✅ {total} referencias limpiadas exitosamente")
        print("💡 Ahora puedes subir nuevas imágenes desde el dashboard")
        
    elif opcion == "2":
        print("\n📌 Manteniendo referencias a Cloudinary")
        print("   Las imágenes estarán disponibles cuando:")
        print("   - La cuenta de Cloudinary se renueve (1 Enero 2026)")
        print("   - Se pague para aumentar el límite")
        print("\n   Mientras tanto, verás errores 401 en la consola del navegador.")
        
    else:
        print("\n❌ Operación cancelada. No se realizaron cambios.")

def show_cloudinary_urls():
    """Muestra todas las URLs de Cloudinary que están causando errores 401"""
    print("\n" + "=" * 60)
    print("URLs DE CLOUDINARY (Error 401)")
    print("=" * 60)
    
    products = ProductStore.objects.filter(
        Q(imagen__icontains='cloudinary') | Q(imagen__icontains='res.cloudinary.com')
    )
    
    if products.exists():
        print("\n📦 PRODUCTOS:")
        for p in products:
            print(f"   - {p.name}: {p.imagen.url if p.imagen else 'N/A'}")
    
    gallery = Galeria.objects.filter(
        Q(galeria__icontains='cloudinary') | Q(galeria__icontains='res.cloudinary.com')
    )
    
    if gallery.exists():
        print("\n🖼️  GALERÍA:")
        for g in gallery[:10]:  # Mostrar solo primeras 10
            print(f"   - ID {g.id}: {g.galeria.url if g.galeria else 'N/A'}")
        if gallery.count() > 10:
            print(f"   ... y {gallery.count() - 10} más")
    
    variants = ProductVariant.objects.filter(
        Q(imagen__icontains='cloudinary') | Q(imagen__icontains='res.cloudinary.com')
    )
    
    if variants.exists():
        print("\n🎨 VARIANTES:")
        for v in variants:
            print(f"   - {v.nombre}: {v.imagen.url if v.imagen else 'N/A'}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestión de referencias a Cloudinary')
    parser.add_argument('--show', action='store_true', help='Mostrar URLs de Cloudinary')
    parser.add_argument('--clean', action='store_true', help='Limpiar referencias interactivamente')
    
    args = parser.parse_args()
    
    if args.show:
        show_cloudinary_urls()
    elif args.clean:
        clean_cloudinary_references()
    else:
        # Por defecto, mostrar y preguntar si limpiar
        clean_cloudinary_references()
