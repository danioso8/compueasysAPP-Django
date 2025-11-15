#!/usr/bin/env python3
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append('d:/ESCRITORIO/CompueasysApp')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_config():
    """
    Prueba la configuración de email enviando un mensaje de prueba
    """
    print("🧪 PROBANDO CONFIGURACIÓN DE EMAIL")
    print("=" * 50)
    
    # Mostrar configuración actual
    print(f"📧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"📮 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"🔌 EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"🔒 EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"👤 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"🏷️ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🔑 EMAIL_HOST_PASSWORD configurado: {'✅' if settings.EMAIL_HOST_PASSWORD else '❌'}")
    print()
    
    if not settings.EMAIL_HOST_PASSWORD:
        print("❌ ERROR: EMAIL_HOST_PASSWORD no está configurado")
        print("📝 SOLUCIONES:")
        print("   1. Configura una variable de entorno: EMAIL_HOST_PASSWORD")
        print("   2. O actualiza directamente en settings.py")
        print("   3. Para Gmail, necesitas una 'App Password', no tu contraseña normal")
        print()
        print("🔗 Guía para Gmail App Password:")
        print("   https://support.google.com/accounts/answer/185833")
        return False
    
    # Intentar enviar email de prueba
    try:
        print("📤 Enviando email de prueba...")
        
        send_mail(
            subject='🧪 Prueba de configuración - CompuEasys',
            message='Este es un email de prueba para verificar la configuración de notificaciones.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Enviar a nosotros mismos
            html_message='''
                <h2>🎉 ¡Configuración exitosa!</h2>
                <p>El sistema de notificaciones de CompuEasys está funcionando correctamente.</p>
                <p><strong>Características activadas:</strong></p>
                <ul>
                    <li>✅ Notificaciones de stock disponible</li>
                    <li>✅ Alertas de bajada de precio</li>
                    <li>✅ Emails HTML responsivos</li>
                    <li>✅ Registro automático de logs</li>
                </ul>
                <p><em>Este es un mensaje de prueba enviado automáticamente.</em></p>
            ''',
            fail_silently=False
        )
        
        print("✅ ¡Email enviado exitosamente!")
        print(f"📬 Revisa la bandeja de entrada de: {settings.EMAIL_HOST_USER}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR al enviar email: {e}")
        print()
        print("🔧 POSIBLES SOLUCIONES:")
        print("   1. Verifica que EMAIL_HOST_PASSWORD sea correcto")
        print("   2. Para Gmail, asegúrate de usar 'App Password'")
        print("   3. Verifica que la cuenta tenga 2FA habilitado")
        print("   4. Revisa que el EMAIL_HOST y EMAIL_PORT sean correctos")
        return False

if __name__ == "__main__":
    test_email_config()