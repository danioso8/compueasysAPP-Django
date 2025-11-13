import requests
from django.conf import settings
import json
import time

class WompiClient:
    """Cliente para interactuar con la API de Wompi"""
    
    def __init__(self):
        self.private_key = settings.WOMPI_PRIVATE_KEY
        self.public_key = settings.WOMPI_PUBLIC_KEY
        self.base_url = settings.WOMPI_BASE_URL
        self.environment = settings.WOMPI_ENVIRONMENT
        
        self.headers = {
            'Authorization': f'Bearer {self.private_key}',
            'Content-Type': 'application/json'
        }
    
    def create_payment_source(self, token, customer_email, acceptance_token):
        """Crear una fuente de pago con token de tarjeta"""
        url = f"{self.base_url}/payment_sources"
        
        payload = {
            "type": "CARD",
            "token": token,
            "customer_email": customer_email,
            "acceptance_token": acceptance_token
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def create_transaction(self, amount_in_cents, currency, customer_email, payment_source_id, reference=None):
        """Crear una transacción de pago"""
        url = f"{self.base_url}/transactions"
        
        if not reference:
            reference = f"compueasys-{int(time.time())}"
        
        payload = {
            "amount_in_cents": int(amount_in_cents),
            "currency": currency,
            "customer_email": customer_email,
            "reference": reference,
            "payment_source_id": payment_source_id
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_transaction(self, transaction_id):
        """Obtener información de una transacción"""
        url = f"{self.base_url}/transactions/{transaction_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_acceptance_token(self):
        """Obtener el token de aceptación (términos y condiciones)"""
        url = f"{self.base_url}/merchants/{self.public_key}"
        
        try:
            response = requests.get(url)
            result = response.json()
            
            if 'data' in result and 'presigned_acceptance' in result['data']:
                return result['data']['presigned_acceptance']
            return None
            
        except Exception as e:
            return None
    
    def validate_webhook_signature(self, payload, signature, timestamp):
        """Validar la firma del webhook de Wompi"""
        # Implementar validación de firma si Wompi la proporciona
        # Por ahora retorna True para permitir el procesamiento
        return True
    
    def create_pse_transaction(self, amount_in_cents, customer_email, bank_code, user_type, user_legal_id, reference=None):
        """Crear una transacción PSE"""
        url = f"{self.base_url}/transactions"
        
        if not reference:
            reference = f"compueasys-pse-{int(time.time())}"
        
        payload = {
            "amount_in_cents": int(amount_in_cents),
            "currency": "COP",
            "customer_email": customer_email,
            "reference": reference,
            "payment_method": {
                "type": "PSE",
                "user_type": user_type,  # 0 = persona natural, 1 = persona jurídica
                "user_legal_id": user_legal_id,
                "user_legal_id_type": "CC",  # CC, NIT, CE, etc.
                "financial_institution_code": bank_code,
                "payment_description": f"Compra en CompuEasys - {reference}"
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_pse_banks(self):
        """Obtener lista de bancos disponibles para PSE"""
        url = f"{self.base_url}/pse/financial_institutions"
        
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            return {'error': str(e)}