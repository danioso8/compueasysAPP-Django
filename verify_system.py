#!/usr/bin/env python
"""
Verificar configuración completa del sistema de emails y registro
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append('d:/ESCRITORIO/CompueasysApp')
django.setup()

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.views import send_welcome_email, send_purchase_email
import inspect

def check_email_config():
    """Verificar configuración de email"""
    print("📧 CONFIGURACIÓN DE EMAIL")
    print("=" * 40)
    
    config_items = [
        ('EMAIL_BACKEND', getattr(settings, 'EMAIL_BACKEND', 'No configurado')),
        ('EMAIL_HOST', getattr(settings, 'EMAIL_HOST', 'No configurado')),
        ('EMAIL_PORT', getattr(settings, 'EMAIL_PORT', 'No configurado')),
        ('EMAIL_USE_TLS', getattr(settings, 'EMAIL_USE_TLS', 'No configurado')),
        ('EMAIL_HOST_USER', getattr(settings, 'EMAIL_HOST_USER', 'No configurado')),
        ('EMAIL_HOST_PASSWORD', '***configurado***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'No configurado'),
    ]
    
    for key, value in config_items:
        status = "✅" if value != 'No configurado' else "❌"
        print(f"  {status} {key}: {value}")
    
    return all(item[1] != 'No configurado' for item in config_items)

def check_email_templates():
    """Verificar plantillas de email"""
    print(f"\n📄 PLANTILLAS DE EMAIL")
    print("=" * 40)
    
    templates = [
        'emails/welcome.html',
        'emails/stock_available.html', 
        'emails/price_drop.html'
    ]
    
    all_good = True
    for template in templates:
        template_path = f'd:/ESCRITORIO/CompueasysApp/core/templates/{template}'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"  ✅ {template} ({len(content)} caracteres)")
        else:
            print(f"  ❌ {template} - NO ENCONTRADA")
            all_good = False
    
    return all_good

def check_email_functions():
    """Verificar funciones de envío de email"""
    print(f"\n🔧 FUNCIONES DE EMAIL")
    print("=" * 40)
    
    # Verificar send_welcome_email
    try:
        sig = inspect.signature(send_welcome_email)
        params = list(sig.parameters.keys())
        print(f"  ✅ send_welcome_email({', '.join(params)})")
    except Exception as e:
        print(f"  ❌ send_welcome_email: {e}")
        return False
    
    # Verificar send_purchase_email
    try:
        sig = inspect.signature(send_purchase_email)
        params = list(sig.parameters.keys())
        print(f"  ✅ send_purchase_email({', '.join(params)})")
    except Exception as e:
        print(f"  ❌ send_purchase_email: {e}")
        return False
    
    return True

def check_registration_improvements():
    """Verificar mejoras en el registro"""
    print(f"\n👤 MEJORAS EN REGISTRO")
    print("=" * 40)
    
    # Leer el archivo de views para verificar cambios
    views_path = 'd:/ESCRITORIO/CompueasysApp/core/views.py'
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        improvements = [
            ('Auto-login después registro', 'request.session[\'user_id\'] = new_user.id' in content),
            ('Redirección a store', 'return redirect(\'/store/\')' in content),
            ('Envío email bienvenida', 'send_welcome_email(' in content),
            ('Mensajes de éxito', 'messages.success(' in content),
            ('Import de messages', 'from django.contrib import messages' in content),
        ]
        
        all_good = True
        for description, check in improvements:
            status = "✅" if check else "❌"
            print(f"  {status} {description}")
            if not check:
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"  ❌ Error leyendo views.py: {e}")
        return False

def test_template_rendering():
    """Probar renderizado de plantillas"""
    print(f"\n🎨 TEST DE RENDERIZADO")
    print("=" * 40)
    
    try:
        # Test welcome template
        context = {
            'username': 'TestUser',
            'site_name': 'CompuEasys',
            'base_url': 'http://localhost:8000',
            'year': '2024'
        }
        
        html_content = render_to_string('emails/welcome.html', context)
        text_content = strip_tags(html_content)
        
        print(f"  ✅ Welcome template renderizada")
        print(f"     HTML: {len(html_content)} caracteres")
        print(f"     Texto: {len(text_content)} caracteres")
        
        # Verificar que variables fueron reemplazadas
        if 'TestUser' in html_content and 'CompuEasys' in html_content:
            print(f"  ✅ Variables correctamente reemplazadas")
        else:
            print(f"  ⚠️ Posible problema con reemplazo de variables")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error renderizando template: {e}")
        return False

def main():
    print("🚀 VERIFICACIÓN COMPLETA DEL SISTEMA")
    print("=" * 60)
    
    # Tests
    email_config_ok = check_email_config()
    email_templates_ok = check_email_templates()
    email_functions_ok = check_email_functions()
    registration_ok = check_registration_improvements()
    template_render_ok = test_template_rendering()
    
    print(f"\n📊 RESUMEN FINAL")
    print("=" * 30)
    print(f"Configuración Email: {'✅' if email_config_ok else '❌'}")
    print(f"Plantillas Email:    {'✅' if email_templates_ok else '❌'}")
    print(f"Funciones Email:     {'✅' if email_functions_ok else '❌'}")
    print(f"Mejoras Registro:    {'✅' if registration_ok else '❌'}")
    print(f"Renderizado:         {'✅' if template_render_ok else '❌'}")
    
    if all([email_config_ok, email_templates_ok, email_functions_ok, registration_ok, template_render_ok]):
        print(f"\n🎉 ¡TODO ESTÁ CONFIGURADO CORRECTAMENTE!")
        print(f"\n📝 PRÓXIMOS PASOS:")
        print(f"1. Ejecuta: python manage.py runserver")
        print(f"2. Prueba el registro en: http://localhost:8000/register/")
        print(f"3. Verifica que:")
        print(f"   • Se crea el usuario")
        print(f"   • Login automático (vas a /store/)")
        print(f"   • Recibes email de bienvenida")
        print(f"4. Prueba las notificaciones de stock:")
        print(f"   • Ve a un producto sin stock")
        print(f"   • Solicita notificación")
        print(f"   • Actualiza stock desde dashboard")
        print(f"   • Verifica email de notificación")
    else:
        print(f"\n⚠️ Hay algunos problemas que necesitan atención.")

if __name__ == "__main__":
    main()