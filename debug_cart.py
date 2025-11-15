#!/usr/bin/env python3
"""
Script para debuggear el problema del carrito duplicado
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import ProductStore as Product, ProductVariant
from decimal import Decimal

def debug_cart_calculation():
    print("🛒 DEBUGGING CART CALCULATION")
    print("=" * 50)
    
    # Simular un carrito con un producto de $25,000
    cart = {
        '1': {'quantity': 1, 'product_id': '1'}
    }
    
    print("Contenido del carrito simulado:")
    print(f"cart = {cart}")
    print()
    
    # Intentar obtener el primer producto disponible
    try:
        product = Product.objects.first()
        if not product:
            print("❌ No hay productos en la base de datos")
            return
            
        print(f"Producto encontrado: {product.name}")
        print(f"Precio del producto: ${product.price}")
        print()
        
        # Simular cálculo como en la vista
        cart_total = Decimal(0)
        cart_count = 0
        
        for k, v in cart.items():
            if isinstance(v, dict):
                q = v['quantity']
                # Usar el producto real
                p = product.price
            else:
                q = v
                p = product.price
            
            item_total = p * q
            cart_total += item_total
            cart_count += q
            
            print(f"Item {k}:")
            print(f"  - Precio: ${p}")
            print(f"  - Cantidad: {q}")
            print(f"  - Subtotal: ${item_total}")
            print()
        
        print(f"🔢 TOTAL CARRITO: ${cart_total}")
        print(f"📦 CANTIDAD TOTAL: {cart_count}")
        
        # Verificar si hay duplicación
        expected_total = product.price * 1  # 1 producto, cantidad 1
        print()
        print("VERIFICACIÓN:")
        print(f"Total esperado: ${expected_total}")
        print(f"Total calculado: ${cart_total}")
        
        if cart_total == expected_total:
            print("✅ Cálculo correcto - NO hay duplicación")
        else:
            print("❌ Error en el cálculo - POSIBLE duplicación")
            print(f"Diferencia: ${cart_total - expected_total}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_product_prices():
    print("\n🏷️ TESTING PRODUCT PRICES")
    print("=" * 50)
    
    products = Product.objects.all()[:5]
    
    for product in products:
        print(f"ID: {product.id} | Nombre: {product.name} | Precio: ${product.price}")
        
        # Verificar variantes
        variants = ProductVariant.objects.filter(product=product)
        if variants.exists():
            print("  Variantes:")
            for variant in variants:
                print(f"    - {variant.color or 'Sin color'} / {variant.talla or 'Sin talla'}: ${variant.precio}")
        print()

if __name__ == "__main__":
    test_product_prices()
    debug_cart_calculation()