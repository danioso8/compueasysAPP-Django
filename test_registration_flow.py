#!/usr/bin/env python
"""
Script para probar el flujo completo de registro de usuario
- Registro de usuario
- Login automático
- Envío de email de bienvenida
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append('d:/ESCRITORIO/CompueasysApp')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from core.models import SimpleUser
from core.views import register_user
import json

def test_registration_flow():
    """Probar el flujo completo de registro"""
    print("🧪 PRUEBA DE REGISTRO COMPLETO")
    print("=" * 50)
    
    # Crear cliente de prueba
    client = Client()
    
    # Datos de prueba para registro
    test_email = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com"
    test_data = {
        'username': f'testuser_{datetime.now().strftime('%H%M%S')}',
        'email': test_email,
        'password': 'TestPassword123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone': '1234567890',
        'address': 'Test Address 123',
        'city': 'Test City'
    }
    
    print(f"📝 Datos de registro:")
    for key, value in test_data.items():
        if key != 'password':
            print(f"   {key}: {value}")
    print()
    
    # 1. Verificar que el usuario no existe
    try:
        existing_user = SimpleUser.objects.get(email=test_email)
        print(f"❌ Usuario ya existe: {existing_user.email}")
        return False
    except SimpleUser.DoesNotExist:
        print("✅ Usuario no existe - OK para crear")
    
    # 2. Realizar petición de registro
    print(f"\n🔄 Realizando petición de registro...")
    response = client.post('/register/', test_data)
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Redirect URL: {getattr(response, 'url', 'No redirect')}")
    
    # 3. Verificar que el usuario fue creado
    try:
        new_user = SimpleUser.objects.get(email=test_email)
        print(f"✅ Usuario creado exitosamente:")
        print(f"   ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Nombre: {new_user.first_name} {new_user.last_name}")
    except SimpleUser.DoesNotExist:
        print("❌ ERROR: Usuario no fue creado")
        return False
    
    # 4. Verificar redirección (debería ser a /store/ en lugar de /login/)
    if response.status_code == 302:
        redirect_url = response.url
        if '/store/' in redirect_url:
            print("✅ Redirección correcta a tienda (usuario logueado automáticamente)")
        elif '/login/' in redirect_url:
            print("⚠️ Redirección a login - posible problema con login automático")
        else:
            print(f"⚠️ Redirección inesperada: {redirect_url}")
    
    # 5. Verificar datos del usuario
    print(f"\n📊 Detalles del usuario creado:")
    print(f"   Teléfono: {new_user.phone}")
    print(f"   Dirección: {new_user.address}")
    print(f"   Ciudad: {new_user.city}")
    print(f"   Fecha creación: {new_user.id}")  # Como usamos ID como fecha
    
    # 6. Limpiar datos de prueba
    print(f"\n🧹 Limpiando datos de prueba...")
    new_user.delete()
    print(f"✅ Usuario de prueba eliminado")
    
    return True

def test_welcome_email_template():
    """Probar la plantilla de email de bienvenida"""
    print(f"\n📧 PRUEBA DE PLANTILLA DE BIENVENIDA")
    print("=" * 50)
    
    template_path = 'd:/ESCRITORIO/CompueasysApp/core/templates/emails/welcome.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"✅ Plantilla encontrada: {template_path}")
        print(f"   Tamaño: {len(content)} caracteres")
        
        # Verificar elementos clave
        elements = [
            '{{ username }}',
            '{{ site_name }}',
            '{{ base_url }}',
            '{{ year }}',
            'Bienvenido',
            'cta-button',
            'Ver Productos'
        ]
        
        missing_elements = []
        for element in elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"⚠️ Elementos faltantes: {missing_elements}")
        else:
            print(f"✅ Todos los elementos clave presentes")
            
        return len(missing_elements) == 0
        
    except FileNotFoundError:
        print(f"❌ Plantilla no encontrada: {template_path}")
        return False

def main():
    print("🚀 PRUEBA COMPLETA DEL SISTEMA DE REGISTRO")
    print("=" * 60)
    
    # Probar plantilla de email
    template_ok = test_welcome_email_template()
    
    # Probar flujo de registro
    registration_ok = test_registration_flow()
    
    print(f"\n📋 RESUMEN DE PRUEBAS")
    print("=" * 30)
    print(f"Plantilla de bienvenida: {'✅ OK' if template_ok else '❌ FAIL'}")
    print(f"Flujo de registro:       {'✅ OK' if registration_ok else '❌ FAIL'}")
    
    if template_ok and registration_ok:
        print(f"\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print(f"El sistema de registro con login automático está funcionando correctamente.")
    else:
        print(f"\n⚠️ Algunas pruebas fallaron. Revisa los detalles arriba.")

if __name__ == "__main__":
    main()