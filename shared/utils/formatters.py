"""
Formateadores de datos
"""
import re
from decimal import Decimal


def format_currency(amount, currency='COP', show_symbol=True):
    """
    Formatea un monto como moneda
    
    Args:
        amount: Monto a formatear
        currency: Código de moneda (COP, USD, EUR)
        show_symbol: Si debe mostrar el símbolo de moneda
    
    Returns:
        String formateado (ej: "$1.234.567" o "1.234.567 COP")
    """
    if amount is None:
        return '$ 0'
    
    # Convertir a Decimal para mayor precisión
    if isinstance(amount, (int, float, str)):
        amount = Decimal(str(amount))
    
    # Formatear con separadores de miles
    formatted = '{:,.0f}'.format(amount).replace(',', '.')
    
    # Agregar símbolo o código de moneda
    if show_symbol:
        symbols = {
            'COP': '$',
            'USD': 'US$',
            'EUR': '€'
        }
        symbol = symbols.get(currency, '$')
        return f"{symbol} {formatted}"
    else:
        return f"{formatted} {currency}"


def format_phone(phone, country_code='57'):
    """
    Formatea un número de teléfono
    
    Args:
        phone: Número sin formato
        country_code: Código de país (default: 57 para Colombia)
    
    Returns:
        String formateado (ej: "+57 300 123 4567")
    """
    if not phone:
        return ''
    
    # Limpiar el número
    clean = re.sub(r'[\s\-\(\)\+]', '', str(phone))
    
    # Si es celular colombiano (10 dígitos que empieza con 3)
    if len(clean) == 10 and clean.startswith('3'):
        return f"+{country_code} {clean[:3]} {clean[3:6]} {clean[6:]}"
    
    # Si es fijo colombiano (7 u 8 dígitos)
    elif len(clean) in [7, 8] and clean[0] in '12345678':
        return f"+{country_code} (1) {clean}"
    
    # Si ya tiene código de país
    elif clean.startswith(country_code):
        number = clean[len(country_code):]
        if len(number) == 10:
            return f"+{country_code} {number[:3]} {number[3:6]} {number[6:]}"
    
    # Devolver sin formato si no coincide
    return phone


def format_nit(nit):
    """
    Formatea un NIT colombiano
    
    Args:
        nit: NIT sin formato
    
    Returns:
        String formateado (ej: "123.456.789-0")
    """
    if not nit:
        return ''
    
    # Limpiar el NIT
    clean = re.sub(r'[\.\-\s]', '', str(nit))
    
    if len(clean) < 9:
        return nit
    
    # Separar dígito de verificación
    number = clean[:-1]
    digit = clean[-1]
    
    # Formatear con puntos de miles
    formatted_number = '{:,}'.format(int(number)).replace(',', '.')
    
    return f"{formatted_number}-{digit}"


def format_cedula(cedula):
    """
    Formatea una cédula colombiana
    
    Args:
        cedula: Cédula sin formato
    
    Returns:
        String formateado (ej: "12.345.678")
    """
    if not cedula:
        return ''
    
    # Limpiar la cédula
    clean = re.sub(r'[\.\,\s]', '', str(cedula))
    
    if not clean.isdigit():
        return cedula
    
    # Formatear con puntos de miles
    return '{:,}'.format(int(clean)).replace(',', '.')


def format_percentage(value, decimals=0):
    """
    Formatea un valor como porcentaje
    
    Args:
        value: Valor a formatear (0-100 o 0-1)
        decimals: Número de decimales
    
    Returns:
        String formateado (ej: "15.5%")
    """
    if value is None:
        return '0%'
    
    value = float(value)
    
    # Si el valor está entre 0 y 1, convertir a porcentaje
    if 0 <= value <= 1:
        value *= 100
    
    return f"{value:.{decimals}f}%"


def slugify_filename(filename):
    """
    Convierte un nombre de archivo a formato slug seguro
    
    Args:
        filename: Nombre original del archivo
    
    Returns:
        Nombre de archivo slugificado
    """
    import unicodedata
    from datetime import datetime
    
    # Separar nombre y extensión
    parts = filename.rsplit('.', 1)
    name = parts[0]
    ext = parts[1] if len(parts) > 1 else ''
    
    # Normalizar unicode
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    
    # Reemplazar caracteres especiales
    name = re.sub(r'[^\w\s-]', '', name).strip().lower()
    name = re.sub(r'[-\s]+', '-', name)
    
    # Añadir timestamp para evitar duplicados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if ext:
        return f"{name}_{timestamp}.{ext}"
    return f"{name}_{timestamp}"
