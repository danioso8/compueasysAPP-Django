"""
Helper modular para geolocalización por IP
Este archivo puede ser eliminado sin afectar el funcionamiento del sistema
"""
import requests
from typing import Optional, Dict


def get_location_from_ip(ip_address: str) -> Dict[str, Optional[str]]:
    """
    Obtiene la ubicación geográfica de una IP usando múltiples APIs
    
    Args:
        ip_address: Dirección IP a consultar
        
    Returns:
        Diccionario con 'city' y 'country', o valores None si falla
        
    Nota: Esta función es completamente opcional y segura de eliminar
    """
    # Valores por defecto si falla
    result = {
        'city': None,
        'country': None,
        'latitude': None,
        'longitude': None
    }
    
    # No consultar IPs locales o privadas
    if not ip_address or ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.'):
        return result
    
    # Lista de APIs para intentar (en orden de prioridad)
    apis = [
        {
            'url': f'https://ipapi.co/{ip_address}/json/',
            'timeout': 3,
            'extract': lambda data: {
                'city': data.get('city'),
                'country': data.get('country_name'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude')
            }
        },
        {
            'url': f'http://ip-api.com/json/{ip_address}',
            'timeout': 3,
            'extract': lambda data: {
                'city': data.get('city'),
                'country': data.get('country'),
                'latitude': data.get('lat'),
                'longitude': data.get('lon')
            }
        }
    ]
    
    # Intentar con cada API hasta que una funcione
    for api in apis:
        try:
            response = requests.get(api['url'], timeout=api['timeout'])
            
            if response.status_code == 200:
                data = response.json()
                result = api['extract'](data)
                
                # Si obtuvimos al menos ciudad o país, retornar
                if result.get('city') or result.get('country'):
                    return result
                    
        except requests.RequestException:
            continue
        except Exception:
            continue
    
    # Si todas las APIs fallaron, retornar resultado vacío
    return result


def enrich_visit_with_location(visit_data: dict, ip_address: str) -> dict:
    """
    Enriquece los datos de una visita con información de geolocalización
    
    Args:
        visit_data: Diccionario con datos de la visita
        ip_address: IP del visitante
        
    Returns:
        Diccionario con datos actualizados (incluye city y country si se obtuvieron)
        
    Nota: Esta función es segura - si falla, devuelve los datos originales
    """
    try:
        location = get_location_from_ip(ip_address)
        
        # Solo agregar si se obtuvo información válida
        if location.get('city'):
            visit_data['city'] = location['city']
        if location.get('country'):
            visit_data['country'] = location['country']
            
    except Exception:
        # Si hay cualquier error, continuar sin ubicación
        pass
    
    return visit_data


def get_client_ip(request) -> str:
    """
    Obtiene la IP real del cliente, considerando proxies y balanceadores
    
    Args:
        request: Django request object
        
    Returns:
        IP address como string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def create_visit_with_location(request, visit_type, user_obj=None, product_id=None):
    """
    Función helper universal para crear visitas con geolocalización opcional
    
    Args:
        request: Django request object
        visit_type: Tipo de visita ('home', 'store', 'product_detail', 'cart', 'checkout')
        user_obj: Usuario autenticado (opcional)
        product_id: ID del producto si es product_detail (opcional)
        
    Returns:
        Objeto StoreVisit creado o None si es un bot
        
    Nota: Esta función es modular - si se elimina el archivo, usar el código directo
    """
    from core.models import StoreVisit
    
    # Obtener o crear session_key
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Filtrar bots conocidos para no contaminar las estadísticas
    bot_ips_prefixes = [
        '173.252.',  # Facebook/Meta
        '69.171.',   # Facebook/Meta  
        '69.63.',    # Facebook/Meta
        '66.220.',   # Facebook/Meta
    ]
    
    bot_user_agents = [
        'facebookexternalhit',
        'Facebot',
        'Twitterbot',
        'LinkedInBot',
        'WhatsApp',
        'Slackbot',
        'TelegramBot'
    ]
    
    # No registrar si es un bot conocido
    if any(ip_address.startswith(prefix) for prefix in bot_ips_prefixes):
        return None
    
    if any(bot in user_agent for bot in bot_user_agents):
        return None
    
    # Preparar datos base de la visita
    visit_data = {
        'session_key': session_key,
        'user': user_obj,
        'visit_type': visit_type,
        'ip_address': ip_address,
        'user_agent': user_agent
    }
    
    # Agregar product_id si se proporcionó
    if product_id:
        visit_data['product_id'] = product_id
    
    # Intentar agregar geolocalización (opcional, falla silenciosamente)
    try:
        visit_data = enrich_visit_with_location(visit_data, ip_address)
    except:
        pass  # Continuar sin ubicación si falla
    
    # Crear y retornar la visita
    return StoreVisit.objects.create(**visit_data)
