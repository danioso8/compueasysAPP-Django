"""
Validadores personalizados reutilizables
"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


def validate_phone(value):
    """
    Valida números de teléfono colombianos
    Acepta formatos: 3001234567, +573001234567, (1) 2345678
    """
    # Limpiar el número
    clean_number = re.sub(r'[\s\-\(\)\+]', '', value)
    
    # Validar formato colombiano
    patterns = [
        r'^3\d{9}$',  # Celular: 3001234567
        r'^573\d{9}$',  # Celular con código país: 573001234567
        r'^[1-8]\d{6,7}$',  # Fijo: 1234567 o 12345678
        r'^60[1-8]\d{6,7}$',  # Fijo con código país: 6011234567
    ]
    
    if not any(re.match(pattern, clean_number) for pattern in patterns):
        raise ValidationError(
            'Ingrese un número de teléfono válido (ej: 3001234567 o 6011234567)'
        )


def validate_email_custom(value):
    """Validador de email personalizado con restricciones adicionales"""
    # Usar validador estándar de Django
    validator = EmailValidator()
    validator(value)
    
    # Validaciones adicionales
    if value.count('@') != 1:
        raise ValidationError('El email debe contener exactamente un símbolo @')
    
    local_part, domain = value.split('@')
    
    # Validar parte local
    if len(local_part) < 3:
        raise ValidationError('La parte local del email debe tener al menos 3 caracteres')
    
    # Validar dominio
    if '.' not in domain:
        raise ValidationError('El dominio debe contener al menos un punto')
    
    # Bloquear dominios temporales (opcional)
    blocked_domains = ['tempmail.com', 'guerrillamail.com', '10minutemail.com']
    if domain.lower() in blocked_domains:
        raise ValidationError('No se permiten correos temporales')


def validate_nit(value):
    """
    Valida NIT colombiano
    Formato: 123456789-0
    """
    # Limpiar el NIT
    clean_nit = value.replace('.', '').replace('-', '').strip()
    
    if not clean_nit.isdigit():
        raise ValidationError('El NIT debe contener solo números')
    
    if len(clean_nit) < 9 or len(clean_nit) > 10:
        raise ValidationError('El NIT debe tener entre 9 y 10 dígitos')


def validate_cedula(value):
    """
    Valida cédula de ciudadanía colombiana
    Acepta números entre 1.000.000 y 9.999.999.999
    """
    # Limpiar la cédula
    clean_cedula = value.replace('.', '').replace(',', '').strip()
    
    if not clean_cedula.isdigit():
        raise ValidationError('La cédula debe contener solo números')
    
    cedula_int = int(clean_cedula)
    if cedula_int < 1000000 or cedula_int > 9999999999:
        raise ValidationError('Ingrese un número de cédula válido')


def validate_positive_number(value):
    """Valida que un número sea positivo"""
    if value < 0:
        raise ValidationError('El valor debe ser positivo')


def validate_percentage(value):
    """Valida que un valor esté entre 0 y 100"""
    if value < 0 or value > 100:
        raise ValidationError('El porcentaje debe estar entre 0 y 100')


def validate_non_future_date(value):
    """Valida que una fecha no sea futura"""
    from django.utils import timezone
    if value > timezone.now().date():
        raise ValidationError('La fecha no puede ser futura')


def validate_business_hours(value):
    """Valida que una hora esté dentro del horario laboral (6am - 10pm)"""
    from datetime import time
    if value < time(6, 0) or value > time(22, 0):
        raise ValidationError('La hora debe estar entre 6:00 AM y 10:00 PM')
