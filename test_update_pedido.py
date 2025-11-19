"""
Script para actualizar un pedido de prueba y verificar que las ventas se actualicen
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import Pedido
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum, Q
from decimal import Decimal

# Obtener pedidos de hoy que estén pendientes
hoy = timezone.now().date()
inicio_dia = datetime.combine(hoy, datetime.min.time())
if timezone.is_aware(timezone.now()):
    inicio_dia = timezone.make_aware(inicio_dia)

pedidos_pendientes = Pedido.objects.filter(
    fecha__gte=inicio_dia,
    estado='pendiente'
)

print(f"\n{'='*70}")
print(f"🧪 TEST: Actualizar Pedido para Verificar Ventas")
print(f"{'='*70}\n")

if pedidos_pendientes.count() == 0:
    print("❌ No hay pedidos pendientes hoy para actualizar")
else:
    # Tomar el primer pedido pendiente
    pedido = pedidos_pendientes.first()
    print(f"📦 Pedido seleccionado:")
    print(f"   ID: #{pedido.id}")
    print(f"   Total: ${pedido.total:,.0f}")
    print(f"   Estado actual: '{pedido.estado}'")
    print(f"   Estado pago actual: '{pedido.estado_pago}'")
    
    # Actualizar a completado
    print(f"\n🔄 Actualizando pedido...")
    pedido.estado_pago = 'completado'
    pedido.save()
    
    print(f"✅ Pedido actualizado:")
    print(f"   Estado pago nuevo: '{pedido.estado_pago}'")
    
    # Recalcular ventas
    ventas_total = Pedido.objects.filter(
        fecha__gte=inicio_dia
    ).filter(
        Q(estado_pago='completado') | Q(estado='entregado')
    ).aggregate(total=Sum('total'))['total'] or Decimal(0)
    
    print(f"\n💰 VENTAS DE HOY ACTUALIZADAS: ${ventas_total:,.0f}")
    print(f"\n{'='*70}")
    print(f"\n✅ RESULTADO:")
    print(f"   El dashboard ahora debería mostrar: ${ventas_total:,.0f} en 'Ventas Hoy'")
    print(f"   Espera ~15 segundos para que el auto-refresh actualice la vista")
    print(f"   O recarga la página manualmente (F5)")
    print(f"\n{'='*70}\n")
