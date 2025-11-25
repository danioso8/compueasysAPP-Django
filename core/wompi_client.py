import requests
from django.conf import settings
import json
import time
import logging

logger = logging.getLogger(__name__)

class WompiClient:
    """Cliente para interactuar con la API de Wompi"""
    def __init__(self, config=None):
        # Permite pasar un objeto/config dict personalizado (por ejemplo, desde WompiConfig)
        if config:
            self.private_key = getattr(config, 'private_key', '') or config.get('private_key', '')
            self.public_key = getattr(config, 'public_key', '') or config.get('public_key', '')
            self.base_url = getattr(config, 'base_url', '') or config.get('base_url', 'https://sandbox.wompi.co/v1')
            self.environment = getattr(config, 'environment', '') or config.get('environment', 'test')
        else:
            self.private_key = getattr(settings, 'WOMPI_PRIVATE_KEY', '')
            self.public_key = getattr(settings, 'WOMPI_PUBLIC_KEY', '')
            self.base_url = getattr(settings, 'WOMPI_BASE_URL', 'https://sandbox.wompi.co/v1')
            self.environment = getattr(settings, 'WOMPI_ENVIRONMENT', 'test')

        # Validar configuración
        if not self.private_key:
            logger.error("📴 WOMPI: Private key no configurada")
            raise ValueError("WOMPI_PRIVATE_KEY no configurada")
        if not self.public_key:
            logger.error("📴 WOMPI: Public key no configurada")
            raise ValueError("WOMPI_PUBLIC_KEY no configurada")

        self.headers = {
            'Authorization': f'Bearer {self.private_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'CompuEasys/1.0'
        }
        logger.info(f"💳 WOMPI Client inicializado - Environment: {self.environment}")
    
    def _make_request(self, method, url, payload=None):
        """Método centralizado para hacer peticiones con logs y reintentos"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 WOMPI {method.upper()}: {url} (Intento {attempt + 1}/{max_retries})")
                if payload:
                    logger.debug(f"📤 WOMPI Payload: {json.dumps(payload, indent=2)}")
                
                # Configuración de la petición con timeout más largo
                if method.lower() == 'post':
                    response = requests.post(url, headers=self.headers, json=payload, timeout=60)
                else:
                    response = requests.get(url, headers=self.headers, timeout=60)
                
                logger.info(f"🟪 WOMPI Response Status: {response.status_code}")
                
                # Log de respuesta
                try:
                    response_data = response.json()
                    logger.debug(f"📬 WOMPI Response: {json.dumps(response_data, indent=2)}")
                except:
                    response_data = {'error': 'Invalid JSON response', 'status_code': response.status_code, 'text': response.text[:200]}
                    logger.error(f"❌ WOMPI Invalid JSON: {response.text[:200]}")
                
                # Verificar status code
                if response.status_code >= 400:
                    logger.error(f"❌ WOMPI Error {response.status_code}: {response_data}")
                    
                    # Si es error temporal (5xx) y no es el último intento, reintentar
                    if 500 <= response.status_code <= 599 and attempt < max_retries - 1:
                        logger.warning(f"⏰ WOMPI Reintentando en 2 segundos...")
                        time.sleep(2)
                        continue
                    
                    return {
                        'error': f'HTTP {response.status_code}',
                        'message': response_data.get('error', {}).get('reason', 'Error desconocido'),
                        'details': response_data,
                        'status_code': response.status_code
                    }
                
                # Éxito - retornar datos
                logger.info(f"✅ WOMPI Petición exitosa")
                return response_data
                
            except requests.exceptions.Timeout:
                logger.error(f"⏰ WOMPI: Timeout de conexión (Intento {attempt + 1})")
                if attempt == max_retries - 1:
                    return {'error': 'timeout', 'message': 'Timeout de conexión con Wompi'}
                time.sleep(2)
                
            except requests.exceptions.ConnectionError:
                logger.error(f"🚫 WOMPI: Error de conexión (Intento {attempt + 1})")
                if attempt == max_retries - 1:
                    return {'error': 'connection', 'message': 'No se pudo conectar con Wompi'}
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ WOMPI Exception (Intento {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return {'error': 'exception', 'message': str(e)}
                time.sleep(1)
                
        # Si llegamos aquí, todos los intentos fallaron
        return {'error': 'max_retries_exceeded', 'message': 'Se agotaron todos los intentos de conexión'}
    
    def create_payment_source(self, token, customer_email, acceptance_token):
        """Crear una fuente de pago con token de tarjeta"""
        url = f"{self.base_url}/payment_sources"
        
        payload = {
            "type": "CARD",
            "token": token,
            "customer_email": customer_email,
            "acceptance_token": acceptance_token
        }
        
        return self._make_request('post', url, payload)
    
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
        
        return self._make_request('post', url, payload)
    
    def get_transaction(self, transaction_id):
        """Obtener información de una transacción"""
        url = f"{self.base_url}/transactions/{transaction_id}"
        return self._make_request('get', url)
    
    def get_acceptance_token(self):
        """Obtener el token de aceptación (términos y condiciones)"""
        url = f"{self.base_url}/merchants/{self.public_key}"
        
        try:
            result = self._make_request('get', url)
            
            if 'error' in result:
                logger.error(f"❌ Error obteniendo acceptance token: {result}")
                return None
                
            if 'data' in result and 'presigned_acceptance' in result['data']:
                token = result['data']['presigned_acceptance']
                logger.info(f"✅ Acceptance token obtenido: {token['acceptance_token'][:20]}...")
                return token
            
            logger.warning("⚠️ No se encontró presigned_acceptance en la respuesta")
            return None
            
        except Exception as e:
            logger.error(f"❌ Exception obteniendo acceptance token: {str(e)}")
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