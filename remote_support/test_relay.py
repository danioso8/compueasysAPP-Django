# Test del Servidor Relay - CompuEasys
# Verifica que el servidor relay esté funcionando correctamente

import requests
import json
import time

RELAY_URL = "https://compueasys.onrender.com/api/relay"

def test_relay_connection():
    """Verifica que el relay esté respondiendo"""
    print("🔍 Verificando conexión al servidor relay...")
    
    try:
        response = requests.get(f"{RELAY_URL}/list_sessions/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Relay activo!")
            print(f"📊 Sesiones activas: {len(data.get('sessions', []))}")
            return True
        else:
            print(f"⚠️ Respuesta inesperada: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor")
        return False
    except requests.exceptions.Timeout:
        print("⏱️ Timeout - El servidor no responde")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_client_registration():
    """Prueba el registro de un cliente"""
    print("\n🧪 Probando registro de cliente...")
    
    try:
        response = requests.post(
            f"{RELAY_URL}/register_client/",
            json={
                'client_id': 'test_client_123',
                'access_code': '999999'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Cliente registrado exitosamente")
                print(f"📋 Session ID: {data['session_id']}")
                return data['session_id']
            else:
                print(f"⚠️ Error en registro: {data.get('error')}")
                return None
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_technician_connection(access_code):
    """Prueba la conexión del técnico"""
    print("\n🔧 Probando conexión de técnico...")
    
    try:
        response = requests.post(
            f"{RELAY_URL}/connect_technician/",
            json={'access_code': access_code},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Técnico conectado exitosamente")
                print(f"📋 Session ID: {data['session_id']}")
                return True
            else:
                print(f"⚠️ Error: {data.get('error')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_full_test():
    """Ejecuta todos los tests"""
    print("=" * 50)
    print("🚀 Test Completo del Servidor Relay")
    print("=" * 50)
    
    # Test 1: Conexión básica
    if not test_relay_connection():
        print("\n❌ El servidor relay no está disponible")
        print("💡 Verifica que Render haya terminado el deployment")
        return False
    
    # Test 2: Registro de cliente
    session_id = test_client_registration()
    if not session_id:
        print("\n❌ No se pudo registrar el cliente")
        return False
    
    # Test 3: Conexión de técnico
    if not test_technician_connection('999999'):
        print("\n❌ No se pudo conectar el técnico")
        return False
    
    print("\n" + "=" * 50)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 50)
    print("\n🎉 El servidor relay está funcionando correctamente!")
    print("📍 URL del relay:", RELAY_URL)
    return True

if __name__ == "__main__":
    print("\n🛠️ CompuEasys Remote Support - Test del Relay\n")
    
    try:
        run_full_test()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
    
    print("\n✅ Test completado\n")
