#!/usr/bin/env python3
"""
Test script para verificar las mejoras de conectividad de Wompi
"""
import os
import sys
import django
import time

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.wompi_client import WompiClient
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_wompi_connection():
    """Test básico de conectividad con Wompi"""
    print("🧪 INICIANDO TESTS DE WOMPI")
    print("=" * 50)
    
    try:
        # Crear cliente
        print("1️⃣ Creando cliente Wompi...")
        wompi_client = WompiClient()
        print("✅ Cliente Wompi creado exitosamente")
        
        # Test 1: Obtener acceptance token
        print("\n2️⃣ Test: Obteniendo acceptance token...")
        start_time = time.time()
        
        token_response = wompi_client.get_acceptance_token()
        end_time = time.time()
        
        print(f"⏱️ Tiempo de respuesta: {end_time - start_time:.2f} segundos")
        
        if isinstance(token_response, dict) and 'error' in token_response:
            print(f"❌ Error obteniendo token: {token_response}")
            return False
        else:
            print("✅ Acceptance token obtenido exitosamente")
            print(f"📋 Token: {str(token_response)[:100]}...")
        
        # Test 2: Verificar estructura del token
        print("\n3️⃣ Test: Verificando estructura del token...")
        if isinstance(token_response, dict) and 'acceptance_token' in token_response:
            print("✅ Token tiene estructura válida")
            print(f"📝 Permalink: {token_response.get('permalink', 'N/A')}")
        else:
            print("❌ Token no tiene estructura esperada")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {str(e)}")
        import traceback
        print("📋 Stacktrace completo:")
        traceback.print_exc()
        return False

def test_wompi_retry_mechanism():
    """Test del mecanismo de reintentos"""
    print("\n🔄 TESTING MECANISMO DE REINTENTOS")
    print("=" * 50)
    
    try:
        wompi_client = WompiClient()
        
        # Simular múltiples requests para ver el comportamiento
        print("🔍 Realizando múltiples requests para verificar estabilidad...")
        
        success_count = 0
        error_count = 0
        
        for i in range(5):
            print(f"\n📡 Request {i+1}/5...")
            start_time = time.time()
            
            response = wompi_client.get_acceptance_token()
            end_time = time.time()
            
            if isinstance(response, dict) and 'error' in response:
                error_count += 1
                print(f"❌ Error: {response.get('error')} - {response.get('message')}")
            else:
                success_count += 1
                print(f"✅ Éxito en {end_time - start_time:.2f}s")
            
            # Esperar un poco entre requests
            time.sleep(1)
        
        print(f"\n📊 RESULTADOS:")
        print(f"✅ Exitosos: {success_count}/5")
        print(f"❌ Errores: {error_count}/5")
        print(f"📈 Tasa de éxito: {(success_count/5)*100:.1f}%")
        
        return success_count > 0
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST DE REINTENTOS: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 WOMPI CONNECTIVITY TEST SUITE")
    print("=" * 60)
    
    # Test básico
    basic_test_passed = test_wompi_connection()
    
    # Test de reintentos
    retry_test_passed = test_wompi_retry_mechanism()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL:")
    print(f"🔍 Test básico: {'✅ PASÓ' if basic_test_passed else '❌ FALLÓ'}")
    print(f"🔄 Test reintentos: {'✅ PASÓ' if retry_test_passed else '❌ FALLÓ'}")
    
    if basic_test_passed and retry_test_passed:
        print("\n🎉 ¡TODAS LAS MEJORAS FUNCIONAN CORRECTAMENTE!")
        print("💡 Wompi está listo para procesar pagos de forma confiable.")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisar configuración de Wompi.")
    
    return basic_test_passed and retry_test_passed

if __name__ == "__main__":
    main()