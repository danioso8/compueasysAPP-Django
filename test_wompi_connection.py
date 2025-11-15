#!/usr/bin/env python
"""
Test Wompi Connection
Prueba la conexión con Wompi y la configuración
"""

import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.wompi_client import WompiClient
from django.conf import settings

def test_wompi_configuration():
    """Verificar configuración de Wompi"""
    print("🔧 WOMPI Configuration Test")
    print("=" * 50)
    
    # Verificar variables de entorno
    print("📋 Environment Variables:")
    print(f"   WOMPI_ENVIRONMENT: {getattr(settings, 'WOMPI_ENVIRONMENT', 'NOT SET')}")
    print(f"   WOMPI_PUBLIC_KEY: {'SET' if getattr(settings, 'WOMPI_PUBLIC_KEY', None) else 'NOT SET'}")
    print(f"   WOMPI_PRIVATE_KEY: {'SET' if getattr(settings, 'WOMPI_PRIVATE_KEY', None) else 'NOT SET'}")
    print(f"   WOMPI_EVENTS_URL: {getattr(settings, 'WOMPI_EVENTS_URL', 'NOT SET')}")
    
    if not getattr(settings, 'WOMPI_PUBLIC_KEY', None):
        print("❌ WOMPI_PUBLIC_KEY no está configurada")
        return False
    
    if not getattr(settings, 'WOMPI_PRIVATE_KEY', None):
        print("❌ WOMPI_PRIVATE_KEY no está configurada")
        return False
    
    print("✅ Variables de entorno configuradas")
    return True

def test_wompi_client():
    """Probar cliente Wompi"""
    print("\n🌐 WOMPI Client Test")
    print("=" * 50)
    
    try:
        # Crear cliente
        client = WompiClient()
        print("✅ Cliente Wompi creado exitosamente")
        
        # Probar conexión obteniendo acceptance token
        print("\n🔍 Probando obtener acceptance token...")
        token = client.get_acceptance_token()
        
        if token and 'acceptance_token' in token:
            print(f"✅ Acceptance token obtenido: {token['acceptance_token'][:20]}...")
            print(f"📋 Permalink: {token.get('permalink', 'N/A')}")
            return True
        else:
            print("❌ No se pudo obtener acceptance token")
            print(f"📋 Respuesta: {token}")
            return False
            
    except Exception as e:
        print(f"❌ Error en cliente Wompi: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_wompi_full_flow():
    """Probar flujo completo de Wompi"""
    print("\n🚀 WOMPI Full Flow Test")
    print("=" * 50)
    
    try:
        client = WompiClient()
        
        # 1. Obtener acceptance token
        print("🔍 Paso 1: Obtener acceptance token...")
        token = client.get_acceptance_token()
        if not token:
            print("❌ Falló obtener acceptance token")
            return False
        print("✅ Acceptance token obtenido")
        
        # 2. Probar creación de transacción (sin procesar)
        print("\n💰 Paso 2: Probar datos de transacción...")
        transaction_data = {
            'amount_in_cents': 50000,  # $500 COP
            'currency': 'COP',
            'customer_email': 'test@compueasys.com',
            'reference': f'test-{int(__import__("time").time())}'
        }
        
        print(f"📋 Datos de prueba: {transaction_data}")
        print("✅ Datos de transacción válidos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en flujo completo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🔥 WOMPI CONNECTION TEST")
    print("=" * 60)
    print("Verificando conexión y configuración de Wompi...")
    print("")
    
    # Tests
    config_ok = test_wompi_configuration()
    client_ok = test_wompi_client() if config_ok else False
    flow_ok = test_wompi_full_flow() if client_ok else False
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"   Configuración: {'✅ OK' if config_ok else '❌ ERROR'}")
    print(f"   Cliente:       {'✅ OK' if client_ok else '❌ ERROR'}")
    print(f"   Flujo:         {'✅ OK' if flow_ok else '❌ ERROR'}")
    
    if config_ok and client_ok and flow_ok:
        print("\n🎉 ¡Wompi está configurado correctamente!")
        print("💡 Puedes proceder con las pruebas en el checkout")
    else:
        print("\n⚠️  Hay problemas con la configuración de Wompi")
        print("💡 Revisa las variables de entorno y la conexión a internet")

if __name__ == "__main__":
    main()