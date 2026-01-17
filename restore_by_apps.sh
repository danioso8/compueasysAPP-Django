#!/bin/bash
# Restaurar usando backups separados por app

echo "📦 RESTAURANDO DATOS POR APPS"
echo "============================="
echo ""

cd /var/www/CompuEasysApp
source venv/bin/activate

# Limpiar BD
echo "🗑️  Limpiando base de datos..."
python manage.py flush --noinput
echo "✅ BD limpiada"
echo ""

# Restaurar en orden correcto
echo "📥 Restaurando datos app por app..."
echo ""

echo "  [1/6] Contenttypes..."
python manage.py loaddata backups_archive/20260115_101646/contenttypes_20260115_101646.json 2>&1 | tail -5

echo "  [2/6] Auth (usuarios Django)..."
python manage.py loaddata backups_archive/20260115_101646/auth_20260115_101646.json 2>&1 | tail -5

echo "  [3/6] Sessions..."
python manage.py loaddata backups_archive/20260115_101646/sessions_20260115_101646.json 2>&1 | tail -5

echo "  [4/6] Contable..."
python manage.py loaddata backups_archive/20260115_101646/contable_20260115_101646.json 2>&1 | tail -5

echo "  [5/6] Dashboard..."
python manage.py loaddata backups_archive/20260115_101646/dashboard_20260115_101646.json 2>&1 | tail -5

echo "  [6/6] Core (productos, pedidos, etc)..."
python manage.py loaddata backups_archive/20260115_101646/core_20260115_101646.json 2>&1 | tail -10

echo ""
echo "✅ Restauración completada"
echo ""

# Verificar
echo "📊 VERIFICACIÓN:"
echo "==============="
python manage.py shell << 'PYEOF'
from core.models import ProductStore, Category, Pedido, SimpleUser, Galeria
from django.contrib.auth.models import User

print(f"\n🛍️  PRODUCTOS:")
print(f"   - ProductStore: {ProductStore.objects.count()}")
print(f"   - Categorías: {Category.objects.count()}")
print(f"   - Galerías: {Galeria.objects.count()}")

print(f"\n👥 USUARIOS:")
print(f"   - SimpleUser: {SimpleUser.objects.count()}")
print(f"   - Django Users: {User.objects.count()}")

print(f"\n📦 PEDIDOS:")
print(f"   - Total: {Pedido.objects.count()}")

if ProductStore.objects.exists():
    product = ProductStore.objects.first()
    print(f"\n✅ Producto de ejemplo:")
    print(f"   - Nombre: {product.name}")
    print(f"   - Precio: ${product.price}")
    print(f"   - Stock: {product.stock}")

print("\n" + "="*50)
PYEOF

echo ""
echo "============================="
echo "✅ PROCESO FINALIZADO"
echo "============================="
echo ""
echo "🌍 CompuEasysApp: http://84.247.129.180:8001"
echo ""
