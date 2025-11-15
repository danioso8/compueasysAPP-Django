from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import ProductStore, StockNotification, NotificationLog
import datetime
import logging

logger = logging.getLogger(__name__)

class ProductStockTracker:
    """Rastrea cambios en el stock de productos"""
    _original_stock = {}

@receiver(pre_save, sender=ProductStore)
def store_original_stock(sender, instance, **kwargs):
    """
    Almacena el stock original antes de guardar
    """
    if instance.pk:  # Solo si el producto ya existe
        try:
            original = ProductStore.objects.get(pk=instance.pk)
            ProductStockTracker._original_stock[instance.pk] = original.stock
        except ProductStore.DoesNotExist:
            ProductStockTracker._original_stock[instance.pk] = 0

@receiver(post_save, sender=ProductStore)
def check_stock_changes(sender, instance, created, **kwargs):
    """
    Verifica cambios de stock y envía notificaciones automáticamente
    """
    if created:
        return  # No procesar productos nuevos
    
    original_stock = ProductStockTracker._original_stock.get(instance.pk, 0)
    current_stock = instance.stock
    
    # Verificar si el producto pasó de sin stock a tener stock
    if original_stock == 0 and current_stock > 0:
        logger.info(f"📦 Stock restored for {instance.name}: {original_stock} → {current_stock}")
        
        # Buscar notificaciones pendientes para este producto
        notifications_to_send = StockNotification.objects.filter(
            product=instance,
            status='pending',
            notification_type='stock_available'
        )
        
        if notifications_to_send.exists():
            logger.info(f"🔔 Sending {notifications_to_send.count()} stock notifications for {instance.name}")
            
            # Enviar notificaciones
            for notification in notifications_to_send:
                try:
                    send_stock_notification_email(notification)
                    
                    # Marcar como enviada
                    notification.status = 'sent'
                    notification.sent_at = datetime.datetime.now()
                    notification.save()
                    
                    # Log exitoso
                    NotificationLog.objects.create(
                        stock_notification=notification,
                        success=True,
                        email_subject=f'¡{instance.name} ya está disponible!'
                    )
                    
                    logger.info(f"✅ Notification sent to {notification.email}")
                    
                except Exception as e:
                    # Marcar como fallida
                    notification.status = 'failed'
                    notification.save()
                    
                    # Log del error
                    NotificationLog.objects.create(
                        stock_notification=notification,
                        success=False,
                        error_message=str(e),
                        email_subject=f'Error: {instance.name}'
                    )
                    
                    logger.error(f"❌ Failed to send notification to {notification.email}: {e}")
        else:
            logger.info(f"ℹ️ No pending notifications for {instance.name}")
    
    # Verificar bajadas de precio (si el precio cambió)
    if hasattr(instance, '_original_price') and instance._original_price != instance.price:
        check_price_drop_notifications(instance)
    
    # Limpiar el tracker
    if instance.pk in ProductStockTracker._original_stock:
        del ProductStockTracker._original_stock[instance.pk]

def send_stock_notification_email(notification):
    """
    Envía un email de notificación de stock disponible
    """
    try:
        # URL del producto
        base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
        product_url = f"{base_url}/product_detail/{notification.product.id}/"
        
        # Contexto para la plantilla
        context = {
            'product': notification.product,
            'email': notification.email,
            'site_name': 'CompuEasys',
            'year': datetime.datetime.now().year,
            'base_url': base_url,
            'product_url': product_url
        }
        
        # Renderizar plantilla HTML
        html_content = render_to_string('emails/stock_available.html', context)
        
        # Crear mensaje
        subject = f'¡{notification.product.name} ya está disponible! 🎉'
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=f'El producto {notification.product.name} ya está disponible en CompuEasys.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@compueasys.com'),
            to=[notification.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Enviar email
        msg.send()
        
        logger.info(f"📧 Email sent successfully to {notification.email}")
        
    except Exception as e:
        logger.error(f"❌ Error sending email to {notification.email}: {e}")
        raise e

def check_price_drop_notifications(product):
    """
    Verifica y envía notificaciones de bajada de precio
    """
    try:
        # Buscar notificaciones de precio pendientes
        price_notifications = StockNotification.objects.filter(
            product=product,
            status='pending',
            notify_price_drop=True
        ).exclude(target_price__isnull=True)
        
        for notification in price_notifications:
            # Verificar si el precio actual es menor o igual al objetivo
            if product.price <= notification.target_price:
                try:
                    # Enviar notificación de precio
                    send_price_drop_notification_email(notification)
                    
                    # Desactivar solo la notificación de precio, mantener stock si aplica
                    notification.notify_price_drop = False
                    notification.target_price = None
                    notification.save()
                    
                    logger.info(f"💰 Price drop notification sent to {notification.email}")
                    
                except Exception as e:
                    logger.error(f"❌ Error sending price notification: {e}")
                    
    except Exception as e:
        logger.error(f"❌ Error checking price drops: {e}")

def send_price_drop_notification_email(notification):
    """
    Envía notificación de bajada de precio
    """
    try:
        context = {
            'product': notification.product,
            'target_price': notification.target_price,
            'current_price': notification.product.price,
            'email': notification.email,
            'site_name': 'CompuEasys',
            'year': datetime.datetime.now().year,
            'base_url': getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
        }
        
        html_content = render_to_string('emails/price_drop.html', context)
        
        subject = f'🏷️ ¡{notification.product.name} bajó de precio!'
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=f'{notification.product.name} ahora cuesta ${notification.product.price:,.0f}',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@compueasys.com'),
            to=[notification.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        
        # Registrar log
        NotificationLog.objects.create(
            stock_notification=notification,
            success=True,
            email_subject=subject
        )
        
    except Exception as e:
        logger.error(f"❌ Error sending price drop email: {e}")
        raise e