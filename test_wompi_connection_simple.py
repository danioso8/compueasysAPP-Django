#!/usr/bin/env python3
"""
Script para probar la conexión con Wompi
"""
import sys
import os
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.wompi_client import WompiClient
from django.conf import settings

def test_wompi_connection():
    print('🧪 PROBANDO CONEXIÓN WOMPI')
    print('=' * 50)
    print(f'Public Key: {settings.WOMPI_PUBLIC_KEY[:20]}...')
    print(f'Environment: {settings.WOMPI_ENVIRONMENT}')
    print(f'Base URL: {settings.WOMPI_BASE_URL}')
    print('=' * 50)

    try:
        # Crear cliente
        print('📱 Creando cliente Wompi...')
        client = WompiClient()
        print('✅ Cliente Wompi creado exitosamente')
        
        # Probar acceptance token
        print('🔑 Obteniendo acceptance token...')
        acceptance_token = client.get_acceptance_token()
        
        if isinstance(acceptance_token, dict) and 'error' in acceptance_token:
            print(f'❌ Error obteniendo token: {acceptance_token}')
            return False
        elif acceptance_token:
            print(f'✅ Token obtenido exitosamente')
            print(f'   Token preview: {str(acceptance_token)[:100]}...')
            return True
        else:
            print('❌ No se recibió token')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == '__main__':
    test_wompi_connection()