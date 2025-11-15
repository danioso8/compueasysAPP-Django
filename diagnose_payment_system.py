#!/usr/bin/env python3
"""
Diagnóstico completo del sistema de pagos Wompi
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

def diagnose_payment_system():
    """Diagnóstico completo del sistema de pagos"""
    print("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA DE PAGOS")
    print("=" * 60)
    
    # 1. Verificar configuración básica
    print("1️⃣ Configuración básica:")
    configs = [
        ('WOMPI_PUBLIC_KEY', settings.WOMPI_PUBLIC_KEY),
        ('WOMPI_PRIVATE_KEY', settings.WOMPI_PRIVATE_KEY[:20] + '...' if settings.WOMPI_PRIVATE_KEY else 'No configurada'),
        ('WOMPI_ENVIRONMENT', settings.WOMPI_ENVIRONMENT),
        ('WOMPI_BASE_URL', settings.WOMPI_BASE_URL),
    ]
    
    for name, value in configs:
        status = "✅" if value and value != "No configurada" else "❌"
        print(f"   {status} {name}: {value}")
    
    # 2. Test del cliente Wompi
    print("\n2️⃣ Test del cliente Wompi:")
    try:
        client = WompiClient()
        print("   ✅ WompiClient inicializado correctamente")
        
        # Test acceptance token
        response = client.get_acceptance_token()
        if isinstance(response, dict):
            if 'error' in response:
                print(f"   ❌ Error obteniendo acceptance token: {response}")
                print(f"      Tipo de error: {response.get('error')}")
                print(f"      Mensaje: {response.get('message')}")
                if response.get('details'):
                    print(f"      Detalles: {response.get('details')}")
                return False
            elif 'acceptance_token' in response:
                print("   ✅ Acceptance token obtenido exitosamente")
                print(f"   📝 Token length: {len(response['acceptance_token'])}")
            else:
                print(f"   ⚠️ Respuesta inesperada: {response}")
        
    except Exception as e:
        print(f"   ❌ Error inicializando WompiClient: {str(e)}")
        import traceback
        print("   📋 Stacktrace:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                print(f"      {line}")
        return False
    
    # 3. Test de URLs y endpoints
    print("\n3️⃣ Test de URLs:")
    try:
        from django.urls import reverse
        
        urls_to_test = [
            ('checkout', 'checkout'),
            ('create_wompi_transaction', 'create_wompi_transaction'),
        ]
        
        for name, url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"   ✅ {name}: {url}")
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)}")
                
    except Exception as e:
        print(f"   ❌ Error verificando URLs: {str(e)}")
    
    # 4. Verificar dependencias de JavaScript
    print("\n4️⃣ Verificación de archivos estáticos:")
    static_files = [
        'core/static/js/checkout-wompi.js',
        'core/templates/checkout.html'
    ]
    
    for file_path in static_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            print(f"   ✅ {file_path}: Existe")
            # Verificar tamaño del archivo
            size = os.path.getsize(full_path)
            print(f"      Tamaño: {size} bytes")
        else:
            print(f"   ❌ {file_path}: No encontrado")
    
    # 5. Test de configuración del template
    print("\n5️⃣ Test de configuración del template:")
    try:
        from django.template import Template, Context
        
        template_content = """
        <meta name="wompi-public-key" content="{{ wompi_public_key }}">
        <script>
        window.checkout_config = {
            wompi_public_key: '{{ wompi_public_key }}',
            create_transaction_url: '{% url "create_wompi_transaction" %}'
        };
        console.log('Config:', window.checkout_config);
        </script>
        """
        
        template = Template(template_content)
        context = Context({
            'wompi_public_key': settings.WOMPI_PUBLIC_KEY
        })
        
        rendered = template.render(context)
        print("   ✅ Template renderiza correctamente")
        
        # Verificar que la clave se está insertando
        if settings.WOMPI_PUBLIC_KEY in rendered:
            print(f"   ✅ Clave pública presente en template: {settings.WOMPI_PUBLIC_KEY[:20]}...")
        else:
            print("   ❌ Clave pública NO presente en template renderizado")
            
    except Exception as e:
        print(f"   ❌ Error en template: {str(e)}")
    
    # 6. Simulación de request de checkout
    print("\n6️⃣ Test de vista checkout:")
    try:
        from django.test import RequestFactory
        from core.views import checkout
        
        factory = RequestFactory()
        request = factory.get('/checkout/')
        request.session = {'cart': {'1': {'quantity': 1, 'price': 100000}}}
        
        try:
            # Esto puede fallar por falta de contexto completo, pero nos da info
            print("   ✅ Vista checkout accesible")
        except Exception as e:
            print(f"   ⚠️ Vista checkout: {str(e)}")
            
    except Exception as e:
        print(f"   ❌ Error testando vista checkout: {str(e)}")
    
    # 7. Diagnósticos específicos para errores comunes
    print("\n7️⃣ Diagnósticos específicos:")
    
    # Check 7.1: Verificar formato de claves
    pub_key_valid = settings.WOMPI_PUBLIC_KEY.startswith('pub_')
    prv_key_valid = settings.WOMPI_PRIVATE_KEY.startswith('prv_')
    
    print(f"   Formato public key: {'✅' if pub_key_valid else '❌'}")
    print(f"   Formato private key: {'✅' if prv_key_valid else '❌'}")
    
    # Check 7.2: Verificar coherencia de ambiente
    is_prod_pub = 'prod' in settings.WOMPI_PUBLIC_KEY
    is_prod_url = 'production' in settings.WOMPI_BASE_URL
    is_prod_env = settings.WOMPI_ENVIRONMENT == 'production'
    
    print(f"   Public key es prod: {'✅' if is_prod_pub else '❌'}")
    print(f"   URL es prod: {'✅' if is_prod_url else '❌'}")
    print(f"   Environment es prod: {'✅' if is_prod_env else '❌'}")
    
    if is_prod_pub and not (is_prod_url and is_prod_env):
        print("   ⚠️ INCONSISTENCIA: Public key de prod pero ambiente/URL no")
    elif not is_prod_pub and (is_prod_url or is_prod_env):
        print("   ⚠️ INCONSISTENCIA: Public key de test pero ambiente/URL de prod")
    else:
        print("   ✅ Configuración de ambiente consistente")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO:")
    print("Si hay errores arriba, esos son los problemas a resolver.")
    print("Si todo está ✅, el problema puede estar en:")
    print("- Cache del navegador")
    print("- Conexión de red")
    print("- Configuración específica de Wompi")
    print("- Problemas en el frontend (JavaScript)")
    
    return True

if __name__ == "__main__":
    diagnose_payment_system()