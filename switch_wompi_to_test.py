"""
Script para cambiar Wompi a modo TEST/SANDBOX
Ejecutar: python switch_wompi_to_test.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from dashboard.models import WompiConfig

def switch_to_test_mode():
    """Cambiar Wompi a modo TEST para pruebas"""
    print("🔄 Cambiando Wompi a modo TEST...")
    
    config = WompiConfig.objects.first()
    
    if not config:
        print("❌ No hay configuración de Wompi")
        print("\n📝 Crear configuración manualmente:")
        print("1. Ir al Dashboard")
        print("2. Configuración → Wompi")
        print("3. Ingresar credenciales de TEST")
        return
    
    print(f"\n📊 Configuración actual:")
    print(f"   Environment: {config.environment}")
    print(f"   Base URL: {config.base_url}")
    print(f"   Public Key: {config.public_key[:20]}...")
    
    # Cambiar a modo TEST
    config.environment = 'test'
    config.base_url = 'https://sandbox.wompi.co/v1'
    
    # Si las credenciales son de producción, advertir
    if config.public_key.startswith('pub_prod_'):
        print("\n⚠️  ADVERTENCIA: La public key parece ser de PRODUCCIÓN")
        print("   Para pruebas necesitas credenciales de TEST")
        print("\n   Credenciales de TEST de Wompi:")
        print("   Public Key de ejemplo: pub_test_xxxxxxxxxx")
        print("   Private Key de ejemplo: prv_test_xxxxxxxxxx")
        print("\n   👉 Obtener credenciales de TEST:")
        print("   1. Ir a https://wompi.com")
        print("   2. Iniciar sesión")
        print("   3. Ir a Configuración → API Keys")
        print("   4. Copiar las claves de TEST/SANDBOX")
        
        respuesta = input("\n¿Deseas continuar de todos modos? (s/n): ")
        if respuesta.lower() != 's':
            print("❌ Operación cancelada")
            return
    
    config.save()
    
    print(f"\n✅ Configuración actualizada:")
    print(f"   Environment: {config.environment}")
    print(f"   Base URL: {config.base_url}")
    
    print("\n📝 PRÓXIMOS PASOS:")
    print("1. Si necesitas credenciales de TEST, actualízalas en el Dashboard")
    print("2. Ejecutar: python test_wompi_payment_flow.py")
    print("3. Probar pago en checkout con tarjetas de prueba")
    print("\n💳 TARJETA DE PRUEBA APROBADA:")
    print("   Número: 4242 4242 4242 4242")
    print("   CVV: 123")
    print("   Fecha: 12/25 (cualquier fecha futura)")
    print("   Nombre: APPROVED")

def switch_to_production_mode():
    """Cambiar Wompi a modo PRODUCCIÓN (pagos reales)"""
    print("⚠️  ¡CUIDADO! Vas a cambiar a modo PRODUCCIÓN")
    print("   En este modo se procesarán pagos REALES")
    
    respuesta = input("\n¿Estás seguro? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Operación cancelada")
        return
    
    config = WompiConfig.objects.first()
    
    if not config:
        print("❌ No hay configuración de Wompi")
        return
    
    config.environment = 'production'
    config.base_url = 'https://production.wompi.co/v1'
    config.save()
    
    print("\n✅ Wompi configurado en modo PRODUCCIÓN")
    print("   ⚠️  Los pagos que se realicen serán REALES")
    print("   ⚠️  Se cobrarán las tarjetas realmente")

def show_current_config():
    """Mostrar configuración actual"""
    config = WompiConfig.objects.first()
    
    if not config:
        print("❌ No hay configuración de Wompi")
        return
    
    print("\n📊 CONFIGURACIÓN ACTUAL:")
    print(f"   Nombre: {config.nombre}")
    print(f"   Environment: {config.environment}")
    print(f"   Base URL: {config.base_url}")
    print(f"   Public Key: {config.public_key[:30]}...")
    print(f"   Private Key: {'*' * 30}... (oculta)")
    print(f"   Actualizado: {config.updated_at}")
    
    if config.environment == 'test':
        print("\n✅ Modo TEST activo - Pagos de prueba")
        if config.public_key.startswith('pub_prod_'):
            print("   ⚠️  Advertencia: Public key parece ser de producción")
    else:
        print("\n⚠️  Modo PRODUCCIÓN activo - Pagos reales")

def main():
    print("\n" + "="*60)
    print(" 🔧 WOMPI - CAMBIAR MODO TEST/PRODUCCIÓN")
    print("="*60)
    
    show_current_config()
    
    print("\n\n📋 OPCIONES:")
    print("1. Cambiar a modo TEST (recomendado para pruebas)")
    print("2. Cambiar a modo PRODUCCIÓN (pagos reales)")
    print("3. Ver configuración actual")
    print("4. Salir")
    
    opcion = input("\nSelecciona una opción (1-4): ")
    
    if opcion == '1':
        switch_to_test_mode()
    elif opcion == '2':
        switch_to_production_mode()
    elif opcion == '3':
        show_current_config()
    elif opcion == '4':
        print("👋 ¡Hasta luego!")
    else:
        print("❌ Opción inválida")

if __name__ == '__main__':
    main()
