import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import StockNotification, ProductStore

# Verificar estado actual
notifications = StockNotification.objects.filter(status='pending')
print(f"Notificaciones pendientes: {notifications.count()}")

if notifications.exists():
    notification = notifications.first()
    product = notification.product
    
    print(f"Producto: {product.name}")
    print(f"Stock actual: {product.stock}")
    print(f"Email: {notification.email}")
    
    # Cambiar stock
    print("\nCambiando stock de 0 a 5...")
    product.stock = 5
    product.save()
    
    print("Stock actualizado!")
    
    # Verificar notificación
    notification.refresh_from_db()
    print(f"Estado notificacion: {notification.status}")
else:
    print("No hay notificaciones pendientes")