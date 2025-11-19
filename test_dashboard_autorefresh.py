"""
Script de prueba para verificar el sistema de auto-refresh del dashboard
"""
import requests
import json
from datetime import datetime

def test_dashboard_stats_api():
    """Prueba el endpoint de estadísticas del dashboard"""
    
    print("🧪 TEST: Dashboard Stats API")
    print("=" * 60)
    
    url = "http://127.0.0.1:8000/dashboard/api/dashboard-stats/"
    
    print(f"\n📡 Llamando a: {url}")
    
    try:
        response = requests.get(url)
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n📊 Respuesta JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success'):
                print("\n✅ API respondió exitosamente")
                
                # Verificar estructura de datos
                stats = data.get('stats', {})
                
                print("\n🔍 Verificando estructura de datos:")
                
                # Estadísticas diarias
                diarias = stats.get('diarias', {})
                print(f"\n📅 Estadísticas Diarias:")
                print(f"   - pedidos_hoy: {diarias.get('pedidos_hoy')}")
                print(f"   - ventas_hoy: ${diarias.get('ventas_hoy'):,.2f}")
                print(f"   - productos_vendidos_hoy: {diarias.get('productos_vendidos_hoy')}")
                
                # Estadísticas de pedidos
                pedidos = stats.get('pedidos', {})
                print(f"\n📦 Estadísticas de Pedidos:")
                print(f"   - total: {pedidos.get('total')}")
                print(f"   - pendientes: {pedidos.get('pendientes')}")
                print(f"   - completados: {pedidos.get('completados')}")
                
                # Estadísticas financieras
                finanzas = stats.get('finanzas', {})
                print(f"\n💰 Estadísticas Financieras:")
                print(f"   - ingresos_totales: ${finanzas.get('ingresos_totales'):,.2f}")
                print(f"   - ingresos_pendientes: ${finanzas.get('ingresos_pendientes'):,.2f}")
                
                # Productos
                productos = stats.get('productos', {})
                print(f"\n📦 Estadísticas de Productos:")
                print(f"   - total: {productos.get('total')}")
                print(f"   - sin_stock: {productos.get('sin_stock')}")
                print(f"   - bajo_stock: {productos.get('bajo_stock')}")
                
                # Usuarios
                usuarios = stats.get('usuarios', {})
                print(f"\n👥 Estadísticas de Usuarios:")
                print(f"   - total: {usuarios.get('total')}")
                
                # Timestamp
                timestamp = stats.get('timestamp')
                print(f"\n⏰ Timestamp: {timestamp}")
                
                # Verificar si ventas_hoy tiene valor
                ventas_hoy = diarias.get('ventas_hoy', 0)
                if ventas_hoy > 0:
                    print(f"\n✅ VENTAS HOY TIENE VALOR: ${ventas_hoy:,.2f}")
                else:
                    print(f"\n⚠️ VENTAS HOY ES CERO - Posibles razones:")
                    print(f"   - No hay pedidos con estado 'entregado' hoy")
                    print(f"   - No hay pedidos con estado_pago 'completado' hoy")
                    print(f"   - Verificar filtros en la vista dashboard_stats")
                
            else:
                print(f"\n❌ API respondió con error: {data.get('error')}")
                
        else:
            print(f"\n❌ Error HTTP: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor Django está corriendo en http://127.0.0.1:8000/")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    print("\n" + "=" * 60)

def test_pedidos_today():
    """Verifica pedidos de hoy directamente"""
    print("\n🧪 TEST: Verificar Pedidos de Hoy")
    print("=" * 60)
    
    try:
        # Este sería un script separado que se ejecuta dentro del contexto de Django
        print("\n⚠️ Esta prueba requiere acceso directo a la base de datos Django")
        print("   Ejecuta este código en el shell de Django:")
        print("\n   python manage.py shell")
        print("\n   Luego ejecuta:")
        print("""
from core.models import Pedido
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

# Obtener pedidos de hoy
hoy = timezone.now().date()
inicio_dia = datetime.combine(hoy, datetime.min.time())
if timezone.is_aware(timezone.now()):
    inicio_dia = timezone.make_aware(inicio_dia)

pedidos_hoy = Pedido.objects.filter(fecha__gte=inicio_dia)

print(f"Total pedidos hoy: {pedidos_hoy.count()}")

# Ventas de hoy (solo completados)
ventas_hoy = pedidos_hoy.filter(
    estado_pago='completado'
).aggregate(total=Sum('total'))['total'] or Decimal(0)

print(f"Ventas de hoy (completados): ${ventas_hoy}")

# Ver todos los pedidos de hoy
for pedido in pedidos_hoy:
    print(f"  Pedido #{pedido.id}: ${pedido.total} - Estado: {pedido.estado} - Pago: {pedido.estado_pago}")
        """)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    print("\n" + "🚀 INICIANDO PRUEBAS DEL SISTEMA DE AUTO-REFRESH" + "\n")
    print(f"Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test 1: API de estadísticas
    test_dashboard_stats_api()
    
    # Test 2: Instrucciones para verificar pedidos
    test_pedidos_today()
    
    print("\n✅ PRUEBAS COMPLETADAS")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Abre la consola del navegador (F12) en el dashboard")
    print("   2. Busca los logs con emojis (🔍, ✅, 📊, etc.)")
    print("   3. Verifica que aparezca 'Actualizando ventas-hoy'")
    print("   4. Si ventas_hoy sigue en 0, verifica que haya pedidos con:")
    print("      - estado_pago='completado' O")
    print("      - estado='entregado'")
    print("      creados HOY\n")
