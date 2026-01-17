"""
Generadores de códigos y tokens
"""
import secrets
import string
import uuid
from datetime import datetime


def generate_code(length=8, prefix='', suffix='', uppercase=True, include_numbers=True):
    """
    Genera un código alfanumérico único
    
    Args:
        length: Longitud del código (sin contar prefix/suffix)
        prefix: Prefijo opcional
        suffix: Sufijo opcional
        uppercase: Si debe ser mayúsculas
        include_numbers: Si debe incluir números
    
    Returns:
        Código generado (ej: "ORD-A1B2C3D4")
    """
    chars = string.ascii_uppercase if uppercase else string.ascii_lowercase
    if include_numbers:
        chars += string.digits
    
    code = ''.join(secrets.choice(chars) for _ in range(length))
    
    parts = []
    if prefix:
        parts.append(prefix)
    parts.append(code)
    if suffix:
        parts.append(suffix)
    
    return '-'.join(parts)


def generate_invoice_number(organization_id, prefix='FV'):
    """
    Genera un número de factura secuencial
    
    Args:
        organization_id: ID de la organización
        prefix: Prefijo (FV para factura de venta)
    
    Returns:
        Número de factura (ej: "FV-2026-00001")
    """
    from django.db import connection
    
    year = datetime.now().year
    
    # Obtener el siguiente número secuencial
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTRING(invoice_number FROM '[0-9]+$') AS INTEGER)), 0) + 1
            FROM billing_invoice
            WHERE organization_id = %s AND invoice_number LIKE %s
        """, [organization_id, f"{prefix}-{year}-%"])
        
        next_number = cursor.fetchone()[0]
    
    return f"{prefix}-{year}-{next_number:05d}"


def generate_token(length=32):
    """
    Genera un token seguro para autenticación
    
    Args:
        length: Longitud del token
    
    Returns:
        Token hexadecimal
    """
    return secrets.token_hex(length)


def generate_uuid():
    """
    Genera un UUID v4
    
    Returns:
        UUID como string
    """
    return str(uuid.uuid4())


def generate_password(length=12, include_special=True):
    """
    Genera una contraseña segura aleatoria
    
    Args:
        length: Longitud de la contraseña
        include_special: Si debe incluir caracteres especiales
    
    Returns:
        Contraseña generada
    """
    chars = string.ascii_letters + string.digits
    if include_special:
        chars += '!@#$%^&*()_+-='
    
    # Asegurar que tenga al menos una mayúscula, minúscula, número
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    
    if include_special:
        password.append(secrets.choice('!@#$%^&*()_+-='))
    
    # Completar el resto
    password.extend(secrets.choice(chars) for _ in range(length - len(password)))
    
    # Mezclar
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def generate_verification_code(length=6):
    """
    Genera un código de verificación numérico
    
    Args:
        length: Longitud del código
    
    Returns:
        Código numérico (ej: "123456")
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_qr_data(data_type, data):
    """
    Genera datos formateados para código QR
    
    Args:
        data_type: Tipo de datos (url, vcard, payment, etc.)
        data: Diccionario con los datos
    
    Returns:
        String formateado para QR
    """
    if data_type == 'url':
        return data.get('url', '')
    
    elif data_type == 'vcard':
        return f"""BEGIN:VCARD
VERSION:3.0
FN:{data.get('name', '')}
TEL:{data.get('phone', '')}
EMAIL:{data.get('email', '')}
ORG:{data.get('organization', '')}
END:VCARD"""
    
    elif data_type == 'payment':
        # Formato para pagos en Colombia (QR Bancolombia, Nequi, etc.)
        return f"bancolombia://pay?amount={data.get('amount', 0)}&ref={data.get('reference', '')}"
    
    else:
        return str(data)
