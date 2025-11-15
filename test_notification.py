#!/usr/bin/env python3
import os
import sys
import json
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
sys.path.append('d:/ESCRITORIO/CompueasysApp')

import django
django.setup()

# URL del endpoint
url = 'http://127.0.0.1:8000/api/stock-notification/'

# Datos de prueba
data = {
    'product_id': 38,  # Convertidor Inalámbrico sin stock
    'email': 'test@example.com',
    'notification_type': 'stock_available',
    'notify_price_drop': True,
    'target_price': 50000,
    'notify_low_stock': False
}

print(f"🔄 Probando endpoint: {url}")
print(f"📊 Datos: {json.dumps(data, indent=2)}")

try:
    # Obtener CSRF token si es necesario
    session = requests.Session()
    
    # Hacer la petición
    response = session.post(
        url, 
        json=data,
        headers={
            'Content-Type': 'application/json'
        }
    )
    
    print(f"\n📝 Status Code: {response.status_code}")
    print(f"📤 Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ ¡Notificación creada exitosamente!")
        else:
            print(f"❌ Error: {result.get('message')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error de conexión: {e}")