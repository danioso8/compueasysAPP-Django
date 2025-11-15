#!/usr/bin/env python3
"""
Script para diagnosticar y arreglar notificaciones fallidas
"""
import os
import sys
import django
import traceback

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import StockNotification, NotificationLog
from django.core.mail import send_mail
from django.conf import settings

def diagnose_email_issues():
    print("🔍 DIAGNOSTICANDO PROBLEMAS DE EMAIL")
    print("=" * 50)
    
    # 1. Verificar configuración
    print("📧 Configuración actual:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"   EMAIL_HOST_PASSWORD: {'✅ Configurado' if settings.EMAIL_HOST_PASSWORD else '❌ No configurado'}")
    print()
    
    # 2. Ver logs de errores
    print("📊 Logs de errores recientes:")
    failed_logs = NotificationLog.objects.filter(success=False).order_by('-sent_at')[:5]
    
    if failed_logs.exists():
        for log in failed_logs:
            print(f"   ❌ {log.sent_at}: {log.error_message}")
    else:
        print("   No hay logs de errores específicos")
    print()
    
    # 3. Probar envío básico
    print("🧪 Probando envío básico de email...")
    try:
        send_mail(
            subject='🧪 Test - CompuEasys',
            message='Test de configuración de email',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False
        )
        print("   ✅ Email básico enviado correctamente!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error en envío básico: {e}")
        print(f"   📝 Traceback:")
        traceback.print_exc()
        return False

def reset_failed_notifications():
    """
    Resetea las notificaciones fallidas para poder probarlas nuevamente
    """
    print("\n🔄 RESETEANDO NOTIFICACIONES FALLIDAS")
    print("=" * 50)
    
    # Buscar notificaciones fallidas
    failed_notifications = StockNotification.objects.filter(status='failed')
    
    if failed_notifications.exists():
        print(f"📋 Encontradas {failed_notifications.count()} notificaciones fallidas:")
        
        for notification in failed_notifications:
            print(f"   • {notification.email} - {notification.product.name}")
            
            # Resetear a pendiente
            notification.status = 'pending'
            notification.sent_at = None
            notification.save()
            
        print(f"\n✅ {failed_notifications.count()} notificaciones reseteadas a 'pending'")
        print("   Ahora puedes probar el sistema aumentando el stock del producto")
        
    else:
        print("ℹ️  No hay notificaciones fallidas para resetear")

def test_notification_manually():
    """
    Prueba envío manual de una notificación
    """
    print("\n🧪 PRUEBA MANUAL DE NOTIFICACIÓN")
    print("=" * 50)
    
    # Buscar notificación pendiente
    pending = StockNotification.objects.filter(status='pending').first()
    
    if not pending:
        print("❌ No hay notificaciones pendientes")
        print("💡 Crea una notificación desde el frontend primero")
        return
    
    print(f"📧 Probando envío a: {pending.email}")
    print(f"📦 Producto: {pending.product.name}")
    
    try:
        # Importar función del signal
        from core.signals import send_stock_notification_email
        
        # Enviar email
        send_stock_notification_email(pending)
        
        print("✅ ¡Email enviado manualmente!")
        print("📬 Revisa la bandeja de entrada")
        
        # Marcar como enviada
        pending.status = 'sent'
        pending.save()
        
    except Exception as e:
        print(f"❌ Error en envío manual: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Ejecutar diagnóstico completo
    email_works = diagnose_email_issues()
    
    if email_works:
        reset_failed_notifications()
        test_notification_manually()
    else:
        print("\n🔧 SOLUCIONES SUGERIDAS:")
        print("1. Verifica que EMAIL_HOST_PASSWORD esté correcto")
        print("2. Asegúrate de usar App Password de Gmail (no contraseña normal)")
        print("3. Verifica que tu cuenta Gmail tenga 2FA activado")
        print("4. Prueba con un proveedor diferente (Outlook, Yahoo)")
        
    print("\n" + "="*50)
    print("🏁 Diagnóstico completado")
    print("="*50)