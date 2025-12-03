"""
Script de prueba para el sistema de geolocalización
Ejecutar: python test_geolocation.py
"""
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
import django
django.setup()

from core.geolocation_helper import get_location_from_ip, get_client_ip

def test_geolocation():
    print("🧪 Probando sistema de geolocalización...\n")
    
    # Prueba 1: IP pública conocida (Google DNS)
    print("1️⃣ Probando con IP pública (8.8.8.8 - Google):")
    result = get_location_from_ip('8.8.8.8')
    print(f"   📍 Ciudad: {result.get('city')}")
    print(f"   🌍 País: {result.get('country')}")
    print()
    
    # Prueba 2: IP local (debe ser ignorada)
    print("2️⃣ Probando con IP local (127.0.0.1):")
    result = get_location_from_ip('127.0.0.1')
    print(f"   📍 Ciudad: {result.get('city')} (debería ser None)")
    print(f"   🌍 País: {result.get('country')} (debería ser None)")
    print()
    
    # Prueba 3: Tu IP actual (si estás en producción)
    print("3️⃣ Para probar tu IP real, visita tu tienda desde Internet")
    print("   y revisa el dashboard en ?view=visitas")
    print()
    
    print("✅ Pruebas completadas!")
    print()
    print("📋 Próximos pasos:")
    print("   1. Visita tu tienda desde diferentes dispositivos")
    print("   2. Ve al dashboard (?view=visitas)")
    print("   3. Revisa la columna 'Ubicación'")
    print()
    print("⚠️  Nota: IPs locales (127.0.0.1, 192.168.x.x) no mostrarán ubicación")

if __name__ == '__main__':
    test_geolocation()
