#!/bin/bash
# Script para restaurar datos de CompuEasysApp

echo "📦 RESTAURANDO DATOS DE COMPUEASYSAPP"
echo "===================================="
echo ""

cd /var/www/CompuEasysApp
source venv/bin/activate

# 1. Limpiar base de datos
echo "🗑️  [1/3] Limpiando base de datos..."
python manage.py flush --noinput
echo "✅ Base de datos limpiada"
echo ""

# 2. Restaurar datos
echo "📥 [2/3] Restaurando datos (8,801 registros)..."
python manage.py loaddata backups/compueasys_backup_20260115_101646.json
echo "✅ Datos restaurados"
echo ""

# 3. Verificar datos
echo "📊 [3/3] Verificando datos..."
echo ""
echo "Productos en BD:"
python manage.py shell -c "from core.models import ProductStore; print(f'  - {ProductStore.objects.count()} productos')"

echo "Categorías:"
python manage.py shell -c "from core.models import Category; print(f'  - {Category.objects.count()} categorías')"

echo "Pedidos:"
python manage.py shell -c "from core.models import Pedido; print(f'  - {Pedido.objects.count()} pedidos')"

echo "Usuarios:"
python manage.py shell -c "from core.models import SimpleUser; print(f'  - {SimpleUser.objects.count()} usuarios')"

echo "Galerías:"
python manage.py shell -c "from core.models import Galeria; print(f'  - {Galeria.objects.count()} imágenes')"

echo ""
echo "===================================="
echo "✅ RESTAURACIÓN COMPLETADA"
echo "===================================="
echo ""
echo "🌍 Accede a: http://84.247.129.180:8001"
echo ""
