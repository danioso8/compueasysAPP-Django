#!/usr/bin/env python3
"""
Script para probar el envío completo de notificaciones de stock
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append('d:/ESCRITORIO/CompueasysApp')
django.setup()

from core.models import StockNotification, ProductStore, NotificationLog
from core.signals import send_stock_notification_email
import datetime

def test_complete_notification_flow():
    """
    Prueba completa del flujo de notificaciones
    """
    print("🧪 PRUEBA COMPLETA DE NOTIFICACIONES")
    print("=" * 50)
    
    # 1. Verificar notificaciones pendientes
    pending_notifications = StockNotification.objects.filter(status='pending')
    print(f"📋 Notificaciones pendientes: {pending_notifications.count()}")
    
    if not pending_notifications.exists():
        print("❌ No hay notificaciones pendientes")
        print("💡 Primero crea una notificación desde el frontend")
        return
    
    # 2. Seleccionar una notificación para probar
    notification = pending_notifications.first()
    product = notification.product
    
    print(f"🎯 Probando con:")
    print(f"   📦 Producto: {product.name}")
    print(f"   📧 Email: {notification.email}")
    print(f"   📊 Stock actual: {product.stock}")
    print(f"   🔔 Tipo: {notification.notification_type}")
    print()
    
    # 3. Probar envío directo del email
    try:
        print("📤 Enviando email de prueba...")
        
        # Enviar email usando la función del signal
        send_stock_notification_email(notification)
        
        # Marcar como enviada
        notification.status = 'sent'
        notification.sent_at = datetime.datetime.now()
        notification.save()
        
        # Crear log
        NotificationLog.objects.create(
            stock_notification=notification,
            success=True,
            email_subject=f'¡{product.name} ya está disponible!'
        )
        
        print("✅ ¡Email enviado exitosamente!")
        print(f"📬 Revisa la bandeja de entrada de: {notification.email}")
        print()
        
        # 4. Mostrar estadísticas
        total_logs = NotificationLog.objects.count()
        successful_logs = NotificationLog.objects.filter(success=True).count()
        
        print("📊 ESTADÍSTICAS:")
        print(f"   Total emails enviados: {total_logs}")
        print(f"   Emails exitosos: {successful_logs}")
        print(f"   Tasa de éxito: {(successful_logs/total_logs*100):.1f}%" if total_logs > 0 else "   Tasa de éxito: 0%")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR al enviar email: {e}")
        
        # Marcar como fallida
        notification.status = 'failed'
        notification.save()
        
        # Crear log de error
        NotificationLog.objects.create(
            stock_notification=notification,
            success=False,
            error_message=str(e),
            email_subject=f'Error: {product.name}'
        )
        
        print()
        print("🔧 POSIBLES SOLUCIONES:")
        print("   1. Ejecuta: python test_email_config.py")
        print("   2. Verifica la configuración de EMAIL_HOST_PASSWORD")
        print("   3. Revisa que el email de destino sea válido")
        
        return False

def show_notification_stats():
    """
    Muestra estadísticas de todas las notificaciones
    """
    print("\n📊 RESUMEN DE NOTIFICACIONES:")
    print("=" * 30)
    
    total = StockNotification.objects.count()
    pending = StockNotification.objects.filter(status='pending').count()
    sent = StockNotification.objects.filter(status='sent').count()
    failed = StockNotification.objects.filter(status='failed').count()
    
    print(f"Total notificaciones: {total}")
    print(f"• Pendientes: {pending}")
    print(f"• Enviadas: {sent}")
    print(f"• Fallidas: {failed}")
    
    if total > 0:
        print(f"\nÚltimas 3 notificaciones:")
        for n in StockNotification.objects.order_by('-created_at')[:3]:
            status_icon = {'pending': '⏳', 'sent': '✅', 'failed': '❌'}.get(n.status, '❓')
            print(f"  {status_icon} {n.email} - {n.product.name} ({n.status})")

if __name__ == "__main__":
    show_notification_stats()
    test_complete_notification_flow()