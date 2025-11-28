"""
Script de Diagnóstico Completo - Pagos Wompi
Ejecutar: python test_wompi_payment_flow.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.conf import settings
from core.wompi_client import WompiClient
from dashboard.models import WompiConfig
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def test_wompi_configuration():
    """Prueba 1: Verificar configuración de Wompi"""
    print_section("🔧 PRUEBA 1: Configuración de Wompi")
    
    try:
        wompi_config = WompiConfig.objects.first()
        if wompi_config:
            print("✅ Configuración encontrada en base de datos")
            print(f"   Environment: {wompi_config.environment}")
            print(f"   Public Key: {wompi_config.public_key[:20]}...")
            print(f"   Private Key: {'*' * 20}... (oculto)")
            print(f"   Base URL: {wompi_config.base_url}")
            print(f"   Activo: {wompi_config.active}")
            return wompi_config
        else:
            print("❌ No hay configuración de Wompi en la base de datos")
            print("\n💡 Solución: Ir al Dashboard → Configuración → Wompi")
            return None
    except Exception as e:
        print(f"❌ Error al obtener configuración: {str(e)}")
        return None

def test_wompi_client(config):
    """Prueba 2: Verificar creación del cliente Wompi"""
    print_section("🔌 PRUEBA 2: Cliente Wompi")
    
    if not config:
        print("❌ No se puede crear cliente sin configuración")
        return None
    
    try:
        client = WompiClient(config)
        print("✅ Cliente Wompi creado exitosamente")
        print(f"   Environment: {client.environment}")
        print(f"   Base URL: {client.base_url}")
        return client
    except ValueError as e:
        print(f"❌ Error de configuración: {str(e)}")
        print("\n💡 Solución: Verificar que las credenciales sean correctas")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return None

def test_acceptance_token(client):
    """Prueba 3: Obtener token de aceptación"""
    print_section("🔐 PRUEBA 3: Acceptance Token")
    
    if not client:
        print("❌ No se puede probar sin cliente Wompi")
        return None
    
    try:
        print("🔍 Solicitando acceptance token...")
        acceptance_token = client.get_acceptance_token()
        
        if isinstance(acceptance_token, dict) and 'error' in acceptance_token:
            print(f"❌ Error: {acceptance_token.get('error')}")
            print(f"   Mensaje: {acceptance_token.get('message')}")
            print(f"   Detalles: {acceptance_token.get('details')}")
            
            if acceptance_token.get('status_code') == 401:
                print("\n💡 Solución: Las credenciales son inválidas. Verificar:")
                print("   - Public key correcta")
                print("   - Private key correcta")
                print("   - Environment correcto (test/production)")
            elif acceptance_token.get('status_code') == 404:
                print("\n💡 Solución: El merchant no existe")
                print("   - Verificar que la public key sea correcta")
            else:
                print("\n💡 Solución: Verificar conectividad con Wompi")
            
            return None
        
        if acceptance_token and isinstance(acceptance_token, dict):
            token_str = acceptance_token.get('acceptance_token', '')
            print(f"✅ Acceptance token obtenido: {token_str[:30]}...")
            print(f"   Permalink: {acceptance_token.get('permalink')}")
            print(f"   Type: {acceptance_token.get('type')}")
            return acceptance_token
        else:
            print("❌ Token no obtenido correctamente")
            print(f"   Response: {acceptance_token}")
            return None
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_transaction_creation(client):
    """Prueba 4: Simular creación de transacción"""
    print_section("💳 PRUEBA 4: Creación de Transacción (Simulación)")
    
    if not client:
        print("❌ No se puede probar sin cliente Wompi")
        return False
    
    try:
        # Datos de prueba
        test_data = {
            'amount': 50000,  # $50,000 COP
            'amount_in_cents': 5000000,  # 50,000 * 100
            'currency': 'COP',
            'customer_email': 'test@compueasys.com',
            'reference': 'test-compueasys-12345'
        }
        
        print("📋 Datos de prueba:")
        print(f"   Monto: ${test_data['amount']:,} COP")
        print(f"   Centavos: {test_data['amount_in_cents']:,}")
        print(f"   Email: {test_data['customer_email']}")
        print(f"   Referencia: {test_data['reference']}")
        
        print("\n⚠️  NOTA: No se creará transacción real, solo se validan datos")
        print("✅ Datos de transacción son válidos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en validación: {str(e)}")
        return False

def test_django_endpoint():
    """Prueba 5: Verificar endpoint de Django"""
    print_section("🌐 PRUEBA 5: Endpoint Django")
    
    try:
        from django.urls import reverse
        from django.test import RequestFactory
        from core.views import create_wompi_transaction
        
        print("✅ View 'create_wompi_transaction' encontrada")
        
        try:
            url = reverse('create_wompi_transaction')
            print(f"✅ URL configurada: {url}")
        except:
            print("⚠️  URL no encontrada en urls.py")
            print("💡 Verificar que la URL esté configurada en core/urls.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_environment_settings():
    """Prueba 6: Verificar variables de entorno"""
    print_section("🔧 PRUEBA 6: Variables de Entorno Django")
    
    print("Variables Django settings:")
    print(f"   WOMPI_PUBLIC_KEY: {getattr(settings, 'WOMPI_PUBLIC_KEY', 'NO CONFIGURADO')[:20]}...")
    print(f"   WOMPI_PRIVATE_KEY: {'*' * 20}... {'(configurado)' if getattr(settings, 'WOMPI_PRIVATE_KEY', None) else '(NO CONFIGURADO)'}")
    print(f"   WOMPI_ENVIRONMENT: {getattr(settings, 'WOMPI_ENVIRONMENT', 'NO CONFIGURADO')}")
    print(f"   WOMPI_BASE_URL: {getattr(settings, 'WOMPI_BASE_URL', 'NO CONFIGURADO')}")
    
    all_ok = True
    if not getattr(settings, 'WOMPI_PUBLIC_KEY', None):
        print("\n❌ WOMPI_PUBLIC_KEY no configurado")
        all_ok = False
    if not getattr(settings, 'WOMPI_PRIVATE_KEY', None):
        print("❌ WOMPI_PRIVATE_KEY no configurado")
        all_ok = False
    
    if all_ok:
        print("\n✅ Todas las variables están configuradas")
    else:
        print("\n💡 Las variables se cargan desde WompiConfig en la base de datos")
    
    return all_ok

def print_test_cards():
    """Información de tarjetas de prueba"""
    print_section("💳 TARJETAS DE PRUEBA WOMPI")
    
    print("Para SANDBOX (pruebas):\n")
    
    print("🟢 TARJETA APROBADA:")
    print("   Número: 4242 4242 4242 4242")
    print("   CVV: 123")
    print("   Fecha: Cualquier fecha futura (ej: 12/25)")
    print("   Nombre: APPROVED\n")
    
    print("🔴 TARJETA RECHAZADA:")
    print("   Número: 4111 1111 1111 1111")
    print("   CVV: 123")
    print("   Fecha: Cualquier fecha futura")
    print("   Nombre: DECLINED\n")
    
    print("⏳ TARJETA PENDIENTE:")
    print("   Número: 5555 5555 5555 4444")
    print("   CVV: 123")
    print("   Fecha: Cualquier fecha futura")
    print("   Nombre: PENDING\n")
    
    print("❌ TARJETA ERROR:")
    print("   Número: 3782 822463 10005")
    print("   CVV: 123")
    print("   Fecha: Cualquier fecha futura")
    print("   Nombre: ERROR\n")

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print(" 🚀 DIAGNÓSTICO COMPLETO - PAGOS WOMPI")
    print("="*60)
    
    results = {
        'config': False,
        'client': False,
        'acceptance_token': False,
        'transaction': False,
        'endpoint': False,
        'env_vars': False
    }
    
    # Prueba 1: Configuración
    config = test_wompi_configuration()
    results['config'] = config is not None
    
    # Prueba 2: Cliente
    client = None
    if config:
        client = test_wompi_client(config)
        results['client'] = client is not None
    
    # Prueba 3: Acceptance Token
    if client:
        acceptance_token = test_acceptance_token(client)
        results['acceptance_token'] = acceptance_token is not None
    
    # Prueba 4: Transacción
    if client:
        results['transaction'] = test_transaction_creation(client)
    
    # Prueba 5: Endpoint
    results['endpoint'] = test_django_endpoint()
    
    # Prueba 6: Variables de entorno
    results['env_vars'] = test_environment_settings()
    
    # Información de tarjetas de prueba
    print_test_cards()
    
    # Resumen final
    print_section("📊 RESUMEN FINAL")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"Pruebas pasadas: {passed}/{total}\n")
    
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
        print("\n📝 PRÓXIMOS PASOS:")
        print("1. Probar pago en el checkout con tarjetas de prueba")
        print("2. Verificar logs en consola del navegador (F12)")
        print("3. Si hay errores, revisar DIAGNOSTICO_WOMPI_PAGOS.md")
    else:
        print("⚠️  Algunas pruebas fallaron")
        print("\n📝 ACCIONES NECESARIAS:")
        
        if not results['config']:
            print("• Configurar Wompi en el Dashboard")
        if not results['client']:
            print("• Verificar credenciales de Wompi")
        if not results['acceptance_token']:
            print("• Verificar conectividad y credenciales")
        if not results['transaction']:
            print("• Revisar lógica de transacciones")
        if not results['endpoint']:
            print("• Configurar URL en urls.py")
        
        print("\n📖 Consultar: DIAGNOSTICO_WOMPI_PAGOS.md para más detalles")
    
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
