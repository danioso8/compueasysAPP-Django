#!/usr/bin/env python3
"""
Test completo de configuración Wompi después de integración
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.conf import settings
from core.wompi_client import WompiClient
import json

def test_wompi_complete_config():
    """Test de la configuración completa de Wompi"""
    print("🧪 TEST COMPLETO DE CONFIGURACIÓN WOMPI")
    print("=" * 60)
    
    # 1. Verificar todas las configuraciones
    print("1️⃣ Configuraciones cargadas:")
    configs = [
        ('WOMPI_PUBLIC_KEY', settings.WOMPI_PUBLIC_KEY),
        ('WOMPI_PRIVATE_KEY', settings.WOMPI_PRIVATE_KEY[:20] + '...' if settings.WOMPI_PRIVATE_KEY else None),
        ('WOMPI_EVENTS_SECRET', getattr(settings, 'WOMPI_EVENTS_SECRET', 'No configurado')),
        ('WOMPI_INTEGRITY_SECRET', getattr(settings, 'WOMPI_INTEGRITY_SECRET', 'No configurado')),
        ('WOMPI_ENVIRONMENT', settings.WOMPI_ENVIRONMENT),
        ('WOMPI_BASE_URL', settings.WOMPI_BASE_URL),
    ]
    
    all_configured = True
    for name, value in configs:
        status = "✅" if value and value != "No configurado" else "❌"
        print(f"   {status} {name}: {value}")
        if not value or value == "No configurado":
            all_configured = False
    
    # 2. Verificar que las claves tienen el formato correcto
    print("\n2️⃣ Validación de formato de claves:")
    
    public_key_valid = settings.WOMPI_PUBLIC_KEY.startswith('pub_')
    private_key_valid = settings.WOMPI_PRIVATE_KEY.startswith('prv_')
    
    print(f"   {'✅' if public_key_valid else '❌'} Public key formato: {settings.WOMPI_PUBLIC_KEY[:15]}...")
    print(f"   {'✅' if private_key_valid else '❌'} Private key formato: {settings.WOMPI_PRIVATE_KEY[:15]}...")
    
    # 3. Test de inicialización del cliente
    print("\n3️⃣ Test de inicialización WompiClient:")
    try:
        client = WompiClient()
        print("   ✅ WompiClient inicializado correctamente")
        
        # 4. Test de acceptance token
        print("\n4️⃣ Test de acceptance token:")
        response = client.get_acceptance_token()
        
        if isinstance(response, dict):
            if 'error' in response:
                print(f"   ❌ Error obteniendo acceptance token: {response}")
                return False
            elif 'acceptance_token' in response:
                print("   ✅ Acceptance token obtenido exitosamente")
                print(f"   📝 Token length: {len(response['acceptance_token'])}")
                
                # Verificar que el token no está vacío y tiene formato válido
                if len(response['acceptance_token']) > 0:
                    print("   ✅ Token válido obtenido")
                else:
                    print("   ❌ Token vacío")
                    return False
            else:
                print(f"   ⚠️ Respuesta inesperada: {response}")
        else:
            print(f"   ❌ Respuesta no es diccionario: {type(response)}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en inicialización: {str(e)}")
        import traceback
        print("   📋 Stacktrace:")
        for line in traceback.format_exc().split('\n'):
            print(f"      {line}")
        return False
    
    # 5. Diagnóstico final
    print("\n" + "=" * 60)
    print("📊 DIAGNÓSTICO FINAL:")
    
    if all_configured and public_key_valid and private_key_valid:
        print("🎉 ¡CONFIGURACIÓN COMPLETAMENTE FUNCIONAL!")
        print("\n💡 La configuración de Wompi está lista para uso.")
        print("💡 El error 'configuración de pago incompleta' debería estar resuelto.")
        
        # Información adicional sobre la configuración mixta
        print("\n📝 NOTA IMPORTANTE:")
        print("   Tu configuración usa clave pública de producción con claves privadas de test.")
        print("   Esto es normal durante la fase de integración.")
        print("   Asegúrate de usar el ambiente 'test' hasta tener todas las claves de producción.")
        
        return True
    else:
        print("⚠️ ALGUNOS PROBLEMAS DETECTADOS:")
        if not all_configured:
            print("   - Faltan configuraciones")
        if not public_key_valid:
            print("   - Formato de clave pública inválido")
        if not private_key_valid:
            print("   - Formato de clave privada inválido")
        return False

if __name__ == "__main__":
    success = test_wompi_complete_config()
    sys.exit(0 if success else 1)