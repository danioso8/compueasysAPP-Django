#!/bin/bash
# Restaurar datos sin problemas de signals

echo "📦 RESTAURANDO DATOS - VERSIÓN 2"
echo "================================"
echo ""

cd /var/www/CompuEasysApp
source venv/bin/activate

# 1. Modificar signal temporalmente
echo "🔧 [1/4] Deshabilitando signals temporalmente..."
cat > /var/www/CompuEasysApp/contable/signals.py << 'SIGNALEOF'
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, ContableUser

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear UserProfile automáticamente cuando se crea un User - DESHABILITADO TEMPORALMENTE"""
    pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar UserProfile cuando se guarda un User - DESHABILITADO TEMPORALMENTE"""
    pass
SIGNALEOF
echo "✅ Signals deshabilitados"
echo ""

# 2. Limpiar y restaurar
echo "🗑️  [2/4] Limpiando base de datos..."
python manage.py flush --noinput
echo "✅ Limpiada"
echo ""

echo "📥 [3/4] Restaurando datos..."
python manage.py loaddata backups/compueasys_backup_20260115_101646.json 2>&1 | grep -E "Installed|objects"
RESTORE_EXIT=$?
echo "✅ Proceso de restauración completado (exit code: $RESTORE_EXIT)"
echo ""

# 3. Restaurar signal original
echo "🔄 [4/4] Restaurando signals originales..."
cat > /var/www/CompuEasysApp/contable/signals.py << 'SIGNALEOF'
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, ContableUser

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear UserProfile automáticamente cuando se crea un User"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar UserProfile cuando se guarda un User"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
SIGNALEOF
echo "✅ Signals restaurados"
echo ""

# 4. Verificar datos
echo "📊 VERIFICACIÓN DE DATOS:"
echo "========================"
python manage.py shell << 'PYEOF'
from core.models import ProductStore, Category, Pedido, SimpleUser, Galeria, ProductVariant
from dashboard.models import StoreConfig, WompiConfig
from contable.models import Product as ProductContable

print(f"\n✅ CORE:")
print(f"   - Productos: {ProductStore.objects.count()}")
print(f"   - Categorías: {Category.objects.count()}")
print(f"   - Pedidos: {Pedido.objects.count()}")
print(f"   - Usuarios SimpleUser: {SimpleUser.objects.count()}")
print(f"   - Galerías: {Galeria.objects.count()}")
print(f"   - Variantes: {ProductVariant.objects.count()}")

print(f"\n✅ DASHBOARD:")
try:
    print(f"   - Configuraciones tienda: {StoreConfig.objects.count()}")
    print(f"   - Configuraciones Wompi: {WompiConfig.objects.count()}")
except:
    print(f"   - No disponible")

print(f"\n✅ CONTABLE:")
try:
    print(f"   - Productos contables: {ProductContable.objects.count()}")
except:
    print(f"   - No disponible")

print("\n" + "="*50)
PYEOF

echo ""
echo "================================"
echo "✅ RESTAURACIÓN FINALIZADA"
echo "================================"
echo ""
echo "🌍 URL: http://84.247.129.180:8001"
echo ""
