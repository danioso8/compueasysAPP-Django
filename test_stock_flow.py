#!/usr/bin/env python3
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append('d:/ESCRITORIO/CompueasysApp')
django.setup()

from core.models import StockNotification, ProductStore

print("=== ESTADO ACTUAL DEL SISTEMA ===\n")

# Verificar notificaciones pendientes
notifications = StockNotification.objects.filter(status='pending')
print(f"📋 Notificaciones pendientes: {notifications.count()}")

for n in notifications:
    print(f"   • {n.email} para '{n.product.name}'")
    print(f"     Stock actual: {n.product.stock}")
    print(f"     ID del producto: {n.product.id}")
    print(f"     Status: {n.status}")
    print()

# Ahora voy a aumentar el stock del producto ID 38 (que tiene notificación pendiente)
if notifications.exists():
    notification = notifications.first()
    product = notification.product
    
    print(f"🔧 AUMENTANDO STOCK DE: {product.name}")
    print(f"   Stock antes: {product.stock}")
    
    # Aumentar stock de 0 a 5
    product.stock = 5
    product.save()  # Esto debe disparar el signal
    
    print(f"   Stock después: {product.stock}")
    print("   ✅ Stock actualizado - el signal debería haber enviado el email")
    
    # Verificar el estado de la notificación después
    notification.refresh_from_db()
    print(f"   📧 Estado de notificación: {notification.status}")
    
else:
    print("❌ No hay notificaciones pendientes para probar")
    print("   Primero crea una notificación usando el frontend")