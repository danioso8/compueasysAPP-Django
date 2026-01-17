"""
Funciones helper reutilizables
"""
import requests
from django.conf import settings


def get_client_ip(request):
    """
    Obtiene la IP del cliente desde la request
    
    Args:
        request: HttpRequest de Django
    
    Returns:
        IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def send_whatsapp_message(phone, message, organization_id=None):
    """
    Envía un mensaje de WhatsApp usando Baileys
    
    Args:
        phone: Número de teléfono (con código país)
        message: Mensaje a enviar
        organization_id: ID de la organización (opcional)
    
    Returns:
        dict: Respuesta del servidor WhatsApp
    """
    try:
        whatsapp_url = getattr(settings, 'WHATSAPP_SERVER_URL', 'http://localhost:3000')
        
        # Limpiar el número
        clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        
        # Agregar @s.whatsapp.net si no lo tiene
        if '@' not in clean_phone:
            clean_phone = f"{clean_phone}@s.whatsapp.net"
        
        payload = {
            'session_id': str(organization_id) if organization_id else '1',
            'phone': clean_phone,
            'message': message
        }
        
        response = requests.post(
            f"{whatsapp_url}/send-message",
            json=payload,
            timeout=10
        )
        
        return {
            'success': response.status_code == 200,
            'data': response.json() if response.status_code == 200 else None,
            'error': None if response.status_code == 200 else response.text
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }


def send_sms(phone, message):
    """
    Envía un SMS (integración con proveedor SMS)
    
    Args:
        phone: Número de teléfono
        message: Mensaje a enviar
    
    Returns:
        dict: Respuesta del proveedor SMS
    """
    # TODO: Implementar integración con proveedor SMS
    # Ejemplo: Twilio, AWS SNS, etc.
    return {
        'success': False,
        'error': 'SMS provider not configured'
    }


def calculate_age(birth_date):
    """
    Calcula la edad a partir de una fecha de nacimiento
    
    Args:
        birth_date: Fecha de nacimiento (date object)
    
    Returns:
        Edad en años (int)
    """
    from datetime import date
    today = date.today()
    age = today.year - birth_date.year
    
    # Ajustar si aún no ha cumplido años este año
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def get_business_days(start_date, end_date, holidays=None):
    """
    Calcula los días hábiles entre dos fechas
    
    Args:
        start_date: Fecha inicial
        end_date: Fecha final
        holidays: Lista de fechas festivas (opcional)
    
    Returns:
        Número de días hábiles (int)
    """
    from datetime import timedelta
    
    if holidays is None:
        holidays = []
    
    business_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Si no es fin de semana (0=Lunes, 6=Domingo) y no es festivo
        if current_date.weekday() < 5 and current_date not in holidays:
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days


def truncate_text(text, max_length=100, suffix='...'):
    """
    Trunca un texto a una longitud máxima
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a añadir cuando se trunca
    
    Returns:
        Texto truncado
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_divide(numerator, denominator, default=0):
    """
    División segura que maneja división por cero
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si hay división por cero
    
    Returns:
        Resultado de la división o default
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def clean_dict(data, remove_none=True, remove_empty=False):
    """
    Limpia un diccionario removiendo valores None o vacíos
    
    Args:
        data: Diccionario a limpiar
        remove_none: Si debe remover valores None
        remove_empty: Si debe remover strings vacíos
    
    Returns:
        Diccionario limpio
    """
    cleaned = {}
    
    for key, value in data.items():
        if remove_none and value is None:
            continue
        if remove_empty and value == '':
            continue
        cleaned[key] = value
    
    return cleaned


def batch_iterator(queryset, batch_size=1000):
    """
    Itera sobre un queryset en lotes para optimizar memoria
    
    Args:
        queryset: QuerySet de Django
        batch_size: Tamaño del lote
    
    Yields:
        Lotes de objetos
    """
    total = queryset.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield queryset[start:end]
