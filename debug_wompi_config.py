#!/usr/bin/env python3
"""
Script de diagnóstico para el problema de configuración de Wompi
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.conf import settings
from core.views import checkout
from django.http import HttpRequest
from django.test import RequestFactory
import json

def debug_wompi_config():
    """Debuggear la configuración de Wompi en checkout"""
    print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN WOMPI")
    print("=" * 60)
    
    # 1. Verificar settings
    print("1️⃣ Configuración Django Settings:")
    print(f"   WOMPI_PUBLIC_KEY: {repr(settings.WOMPI_PUBLIC_KEY)}")
    print(f"   WOMPI_PRIVATE_KEY: {repr(settings.WOMPI_PRIVATE_KEY[:20] + '...' if settings.WOMPI_PRIVATE_KEY else 'None')}")
    print(f"   WOMPI_ENVIRONMENT: {repr(settings.WOMPI_ENVIRONMENT)}")
    print(f"   WOMPI_EVENTS_URL: {repr(settings.WOMPI_EVENTS_URL)}")
    
    # 2. Simular request de checkout
    print("\n2️⃣ Simulando request de checkout:")
    factory = RequestFactory()
    request = factory.get('/checkout/')
    request.session = {'cart': {'1': 1}}  # Cart simulado
    
    try:
        # Esto no va a funcionar completamente porque necesita más contexto,
        # pero podemos ver si hay errores básicos
        print("   ✅ Request factory creado")
        
        # 3. Verificar que WompiClient se inicializa
        from core.wompi_client import WompiClient
        client = WompiClient()
        print("   ✅ WompiClient se inicializa correctamente")
        
        # 4. Verificar acceptance token
        print("\n3️⃣ Test de acceptance token:")
        token_response = client.get_acceptance_token()
        
        if isinstance(token_response, dict) and 'error' in token_response:
            print(f"   ❌ Error obteniendo token: {token_response}")
        else:
            print("   ✅ Acceptance token obtenido exitosamente")
            if isinstance(token_response, dict) and 'acceptance_token' in token_response:
                print(f"   📝 Token length: {len(token_response['acceptance_token'])}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        print("   📋 Stacktrace:")
        print("   " + "\n   ".join(traceback.format_exc().split('\n')))
    
    # 5. Verificar configuración del template
    print("\n4️⃣ Template configuration que debería enviarse:")
    template_config = {
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY,
        'wompi_environment': settings.WOMPI_ENVIRONMENT,
        'create_transaction_url': '/create-wompi-transaction/'  # URL simulada
    }
    
    print("   📋 Configuración del template:")
    for key, value in template_config.items():
        print(f"      {key}: {repr(value)}")
    
    # 6. Simulación del JavaScript CONFIG
    print("\n5️⃣ Simulación JavaScript CONFIG:")
    js_config = {
        'wompi_public_key': template_config['wompi_public_key'] or '',
        'urls': {
            'create_transaction': template_config['create_transaction_url'] or '/api/create-wompi-transaction/',
        }
    }
    
    print("   📋 CONFIG JavaScript resultante:")
    for key, value in js_config.items():
        print(f"      {key}: {repr(value)}")
    
    # 7. Diagnóstico final
    print("\n" + "=" * 60)
    print("📊 DIAGNÓSTICO FINAL:")
    
    issues = []
    
    if not settings.WOMPI_PUBLIC_KEY:
        issues.append("❌ WOMPI_PUBLIC_KEY vacía")
    elif not settings.WOMPI_PUBLIC_KEY.startswith('pub_'):
        issues.append("⚠️ WOMPI_PUBLIC_KEY no parece válida (no inicia con 'pub_')")
    else:
        print("✅ WOMPI_PUBLIC_KEY configurada correctamente")
    
    if not settings.WOMPI_PRIVATE_KEY:
        issues.append("❌ WOMPI_PRIVATE_KEY vacía")
    elif not settings.WOMPI_PRIVATE_KEY.startswith('prv_'):
        issues.append("⚠️ WOMPI_PRIVATE_KEY no parece válida (no inicia con 'prv_')")
    else:
        print("✅ WOMPI_PRIVATE_KEY configurada correctamente")
    
    if issues:
        print("\n🚨 PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("\n🎉 CONFIGURACIÓN PARECE CORRECTA")
        print("\n💡 Si el error persiste, el problema puede estar en:")
        print("   - Cache del navegador")
        print("   - JavaScript con errores antes de llegar a la validación")
        print("   - Template no actualizado")
        print("   - Archivo estático no recargado")
        return True

if __name__ == "__main__":
    debug_wompi_config()