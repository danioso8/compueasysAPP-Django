"""
Servicio de Email compartido
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


class EmailService:
    """Servicio para envío de emails con templates"""
    
    @staticmethod
    def send_email(
        to_emails,
        subject,
        template_name=None,
        context=None,
        html_content=None,
        text_content=None,
        from_email=None,
        attachments=None,
        cc=None,
        bcc=None
    ):
        """
        Envía un email con soporte para templates HTML
        
        Args:
            to_emails: Lista de destinatarios o string único
            subject: Asunto del email
            template_name: Nombre del template HTML (opcional)
            context: Contexto para el template (opcional)
            html_content: HTML directo (si no se usa template)
            text_content: Contenido texto plano
            from_email: Email del remitente (opcional, usa DEFAULT_FROM_EMAIL)
            attachments: Lista de archivos adjuntos
            cc: Lista de CC
            bcc: Lista de BCC
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Configurar from_email
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            
            # Convertir to_emails a lista si es string
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            
            # Generar contenido HTML desde template si se especifica
            if template_name and context:
                html_content = render_to_string(template_name, context)
                if not text_content:
                    text_content = strip_tags(html_content)
            
            # Si no hay texto plano, extraer del HTML
            if html_content and not text_content:
                text_content = strip_tags(html_content)
            
            # Crear email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content or '',
                from_email=from_email,
                to=to_emails,
                cc=cc or [],
                bcc=bcc or []
            )
            
            # Añadir contenido HTML si existe
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            # Añadir archivos adjuntos si existen
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, dict):
                        email.attach(
                            attachment.get('filename'),
                            attachment.get('content'),
                            attachment.get('mimetype')
                        )
                    else:
                        email.attach_file(attachment)
            
            # Enviar
            email.send(fail_silently=False)
            return True
            
        except Exception as e:
            # Log del error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def send_template_email(to_emails, template_key, context, organization=None):
        """
        Envía un email usando un template predefinido
        
        Args:
            to_emails: Destinatarios
            template_key: Key del template (appointment_reminder, invoice_sent, etc.)
            context: Contexto para el template
            organization: Organización (para personalización)
        
        Returns:
            bool: True si se envió correctamente
        """
        templates = {
            'appointment_reminder': {
                'subject': 'Recordatorio de Cita - {org_name}',
                'template': 'emails/appointment_reminder.html'
            },
            'invoice_sent': {
                'subject': 'Nueva Factura #{invoice_number}',
                'template': 'emails/invoice_sent.html'
            },
            'payment_received': {
                'subject': 'Pago Recibido - Gracias!',
                'template': 'emails/payment_received.html'
            },
            'welcome': {
                'subject': 'Bienvenido a {org_name}',
                'template': 'emails/welcome.html'
            },
            'password_reset': {
                'subject': 'Restablecer Contraseña',
                'template': 'emails/password_reset.html'
            }
        }
        
        template_config = templates.get(template_key)
        if not template_config:
            return False
        
        # Preparar contexto
        context['organization'] = organization
        context['org_name'] = organization.name if organization else 'OpticaApp'
        
        # Formatear subject
        subject = template_config['subject'].format(**context)
        
        return EmailService.send_email(
            to_emails=to_emails,
            subject=subject,
            template_name=template_config['template'],
            context=context
        )
    
    @staticmethod
    def send_bulk_emails(recipients_data, subject, template_name, common_context=None):
        """
        Envía emails en lote con contextos personalizados
        
        Args:
            recipients_data: Lista de dicts con 'email' y 'context'
            subject: Asunto (puede incluir variables del contexto)
            template_name: Nombre del template
            common_context: Contexto común para todos los emails
        
        Returns:
            dict: {'sent': count, 'failed': count}
        """
        sent = 0
        failed = 0
        
        for recipient in recipients_data:
            email = recipient.get('email')
            context = {**(common_context or {}), **recipient.get('context', {})}
            
            # Formatear subject con contexto
            personalized_subject = subject.format(**context)
            
            success = EmailService.send_email(
                to_emails=email,
                subject=personalized_subject,
                template_name=template_name,
                context=context
            )
            
            if success:
                sent += 1
            else:
                failed += 1
        
        return {'sent': sent, 'failed': failed}
