#!/bin/bash
cd /var/www/CompuEasysApp
source venv/bin/activate

python manage.py shell << 'PYEOF'
from core.models import ProductStore, Category, Pedido, SimpleUser, Galeria
from django.contrib.auth.models import User

print("\n📊 ESTADO DE LA BASE DE DATOS:")
print("="*50)
print(f"✅ Productos: {ProductStore.objects.count()}")
print(f"✅ Categorías: {Category.objects.count()}")
print(f"✅ Pedidos: {Pedido.objects.count()}")
print(f"✅ Usuarios SimpleUser: {SimpleUser.objects.count()}")
print(f"✅ Django Users: {User.objects.count()}")
print(f"✅ Galerías: {Galeria.objects.count()}")
print("="*50)

if ProductStore.objects.exists():
    p = ProductStore.objects.first()
    print(f"\n🛍️  Producto de ejemplo:")
    print(f"   Nombre: {p.name}")
    print(f"   Precio: ${p.price}")
PYEOF
