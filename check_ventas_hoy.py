"""
Script para verificar las ventas de hoy en el dashboard
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

# Obtener pedidos de hoy
hoy = timezone.now().date()
inicio_dia = datetime.combine(hoy, datetime.min.time())
if timezone.is_aware(timezone.now()):
    inicio_dia = timezone.make_aware(inicio_dia)

pedidos_hoy = Pedido.objects.filter(fecha__gte=inicio_dia)

print(f"\n{'='*70}")
print(f"📊 ANÁLISIS DE PEDIDOS HOY ({hoy})")
print(f"{'='*70}\n")

print(f"Total pedidos hoy: {pedidos_hoy.count()}")

# Calcular ventas según diferentes criterios
ventas_completados = pedidos_hoy.filter(
    estado_pago='completado'
).aggregate(total=Sum('total'))['total'] or Decimal(0)

ventas_entregados = pedidos_hoy.filter(
    estado='entregado'
).aggregate(total=Sum('total'))['total'] or Decimal(0)

# Esta es la lógica usada en el dashboard
ventas_total = pedidos_hoy.filter(
    Q(estado_pago='completado') | Q(estado='entregado')
).aggregate(total=Sum('total'))['total'] or Decimal(0)

print(f"\n💰 VENTAS:")
print(f"  - Con estado_pago='completado': ${ventas_completados:,.0f}")
print(f"  - Con estado='entregado': ${ventas_entregados:,.0f}")
print(f"  - TOTAL (lógica del dashboard): ${ventas_total:,.0f}")

print(f"\n📦 DETALLE DE PEDIDOS DE HOY:")
print(f"{'-'*70}")

if pedidos_hoy.count() == 0:
    print("  ⚠️  No hay pedidos registrados hoy")
else:
    for pedido in pedidos_hoy[:20]:  # Mostrar máximo 20
        completado_icon = "✅" if (pedido.estado_pago == 'completado' or pedido.estado == 'entregado') else "❌"
        print(f"  {completado_icon} #{pedido.id}: ${pedido.total:,.0f} - Estado: '{pedido.estado}' - Pago: '{pedido.estado_pago}'")
    
    if pedidos_hoy.count() > 20:
        print(f"  ... y {pedidos_hoy.count() - 20} pedidos más")

print(f"\n{'='*70}")
print(f"\n📌 DIAGNÓSTICO:")
if ventas_total == 0:
    print("  ⚠️  Las ventas de hoy son $0")
    if pedidos_hoy.count() == 0:
        print("  ➡️  Causa: No hay pedidos registrados hoy")
    else:
        print("  ➡️  Causa: Ningún pedido tiene estado_pago='completado' O estado='entregado'")
        print("  ➡️  Solución: Actualiza el estado de algún pedido para que aparezca en ventas")
else:
    print(f"  ✅ Las ventas de hoy deberían mostrar: ${ventas_total:,.0f}")
    print("  ➡️  Si el dashboard muestra $0, el problema es en el frontend (JavaScript)")

print(f"\n{'='*70}\n")
