#!/usr/bin/env python3
"""
Debug del problema de configuración en el frontend
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.conf import settings
from django.http import HttpRequest
from django.template import Template, Context

def debug_frontend_config():
    """Debug de la configuración que se pasa al frontend"""
    print("🔍 DEBUG CONFIGURACIÓN FRONTEND")
    print("=" * 50)
    
    # 1. Verificar settings directamente
    print("1️⃣ Settings Django:")
    print(f"   WOMPI_PUBLIC_KEY: '{settings.WOMPI_PUBLIC_KEY}'")
    print(f"   Length: {len(settings.WOMPI_PUBLIC_KEY)}")
    print(f"   Type: {type(settings.WOMPI_PUBLIC_KEY)}")
    
    # 2. Simular el template
    print("\n2️⃣ Simulación del template:")
    template_content = """
    <script>
        console.log('Template wompi_public_key: {{ wompi_public_key }}');
        window.checkout_config = {
            wompi_public_key: '{{ wompi_public_key }}',
            csrf_token: '{{ csrf_token }}'
        };
        console.log('window.checkout_config:', window.checkout_config);
    </script>
    """
    
    template = Template(template_content)
    context = Context({
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY,
        'csrf_token': 'test_csrf_token'
    })
    
    rendered = template.render(context)
    print("   Template renderizado:")
    for line in rendered.strip().split('\n'):
        print(f"   {line.strip()}")
    
    # 3. Verificar que no hay caracteres extraños
    print("\n3️⃣ Análisis de caracteres:")
    key = settings.WOMPI_PUBLIC_KEY
    print(f"   Primer carácter: '{key[0]}' (ord: {ord(key[0])})")
    print(f"   Último carácter: '{key[-1]}' (ord: {ord(key[-1])})")
    print(f"   Contiene espacios: {' ' in key}")
    newline_check = '\n' in key
    print(f"   Contiene saltos de línea: {newline_check}")
    print(f"   Contiene caracteres especiales: {any(ord(c) > 127 for c in key)}")
    
    # 4. Test específico del JavaScript
    print("\n4️⃣ Test simulado del JavaScript:")
    js_config = {
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY or '',
    }
    
    print(f"   window.checkout_config simulado: {js_config}")
    print(f"   wompi_public_key: '{js_config['wompi_public_key']}'")
    print(f"   Evaluación: {'✅ VÁLIDA' if js_config['wompi_public_key'] and js_config['wompi_public_key'].strip() else '❌ INVÁLIDA'}")
    
    # 5. JavaScript condition simulation
    wompi_key = js_config['wompi_public_key']
    condition1 = not wompi_key
    condition2 = wompi_key.strip() == '' if wompi_key else True
    
    print(f"\n5️⃣ Condiciones JavaScript:")
    print(f"   !CONFIG.wompi_public_key: {condition1}")
    print(f"   CONFIG.wompi_public_key.trim() === '': {condition2}")
    print(f"   Condición completa (falla): {condition1 or condition2}")
    
    if condition1 or condition2:
        print("\n❌ ¡PROBLEMA DETECTADO!")
        print("   El JavaScript va a mostrar 'Clave pública no configurada'")
        
        if condition1:
            print("   Causa: wompi_public_key es falsy (vacía/undefined/null)")
        if condition2:
            print("   Causa: wompi_public_key contiene solo espacios")
            
    else:
        print("\n✅ Configuración debería funcionar en JavaScript")

if __name__ == "__main__":
    debug_frontend_config()