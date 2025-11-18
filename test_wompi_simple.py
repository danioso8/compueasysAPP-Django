"""
Script simple para verificar configuración de Wompi
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.conf import settings
from core.wompi_client import WompiClient

print("="*60)
print("🔍 DIAGNÓSTICO DE WOMPI")
print("="*60)

# 1. Verificar variables de configuración
print("\n1️⃣ CONFIGURACIÓN:")
print(f"   WOMPI_PUBLIC_KEY: {settings.WOMPI_PUBLIC_KEY[:20]}...")
print(f"   WOMPI_PRIVATE_KEY: {settings.WOMPI_PRIVATE_KEY[:20]}...")
print(f"   WOMPI_ENVIRONMENT: {settings.WOMPI_ENVIRONMENT}")
print(f"   WOMPI_BASE_URL: {settings.WOMPI_BASE_URL}")

# 2. Intentar crear cliente
print("\n2️⃣ CLIENTE:")
try:
    client = WompiClient()
    print("   ✅ Cliente Wompi creado correctamente")
except Exception as e:
    print(f"   ❌ Error creando cliente: {e}")
    exit(1)

# 3. Probar obtener acceptance token
print("\n3️⃣ ACCEPTANCE TOKEN:")
try:
    token = client.get_acceptance_token()
    if token and 'acceptance_token' in token:
        print(f"   ✅ Token obtenido: {token['acceptance_token'][:50]}...")
        print(f"   📄 Permalink: {token.get('permalink', 'N/A')[:60]}...")
    elif isinstance(token, dict) and 'error' in token:
        print(f"   ❌ Error: {token.get('error')}")
        print(f"   📝 Mensaje: {token.get('message')}")
    else:
        print(f"   ⚠️ Respuesta inesperada: {token}")
except Exception as e:
    print(f"   ❌ Excepción: {e}")

print("\n" + "="*60)
print("✅ Diagnóstico completado")
print("="*60)
