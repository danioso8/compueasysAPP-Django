"""Test de conexión del cliente al relay"""
import requests
import platform
import time

relay_url = "https://compueasys.onrender.com/api/relay"

print("\n🧪 TEST DE CONEXIÓN DEL CLIENTE")
print("=" * 50)

# Generar código de acceso
access_code = "999888"
client_id = f"{platform.node()}_{int(time.time())}"

print(f"\n📋 Datos de prueba:")
print(f"   Client ID: {client_id}")
print(f"   Código: {access_code}")
print(f"   URL: {relay_url}/register_client/")

try:
    print(f"\n📡 Enviando petición POST...")
    response = requests.post(
        f"{relay_url}/register_client/",
        json={
            'client_id': client_id,
            'access_code': access_code
        },
        timeout=10
    )
    
    print(f"\n📊 Respuesta del servidor:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ CONEXIÓN EXITOSA!")
        print(f"   Success: {data.get('success')}")
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Message: {data.get('message')}")
    else:
        print(f"\n❌ ERROR {response.status_code}")
        print(f"   Response: {response.text}")
        
except requests.exceptions.Timeout:
    print(f"\n⏱️ TIMEOUT - El servidor no respondió a tiempo")
except requests.exceptions.ConnectionError as e:
    print(f"\n🔌 ERROR DE CONEXIÓN")
    print(f"   {str(e)}")
except Exception as e:
    print(f"\n❌ ERROR INESPERADO")
    print(f"   Tipo: {type(e).__name__}")
    print(f"   Mensaje: {str(e)}")

print("\n" + "=" * 50)
