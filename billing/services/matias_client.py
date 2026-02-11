"""
Cliente para integración con Matias API v3.0.0
Facturación Electrónica DIAN - Colombia
"""
import requests
import os
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Optional, Tuple


class MatiasAPIClient:
    """Cliente para interactuar con Matias API"""
    
    def __init__(self):
        self.email = os.getenv('MATIAS_EMAIL', 'demo@lopezsoft.net.co')
        self.password = os.getenv('MATIAS_PASSWORD', 'DEMO123456')
        self.api_base_url = os.getenv('MATIAS_API_BASE_URL', 'https://api-v2.matias-api.com/api/ubl2.1')
        self.auth_url = 'https://api-v2.matias-api.com/oauth/token'
        
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self) -> Optional[str]:
        """
        Obtiene un token de acceso OAuth2 de Matias API
        
        Returns:
            str: Token de acceso o None si hay error
        """
        # Si ya tenemos un token válido, retornarlo
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # Solicitar nuevo token
        try:
            payload = {
                "grant_type": "password",
                "client_id": 2,
                "client_secret": "lYflu65FMrsZG3p4tLtSIZKTLrDt66KKZ1LilNdK",
                "username": self.email,
                "password": self.password,
                "scope": "*"
            }
            
            response = requests.post(
                self.auth_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)  # Por defecto 1 hora
                
                # Guardar cuándo expira (con margen de 5 minutos)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                
                return self.access_token
            else:
                print(f"Error obteniendo token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Excepción al obtener token: {str(e)}")
            return None
    
    def send_invoice(self, invoice_data: Dict) -> Tuple[bool, Dict]:
        """
        Envía una factura a Matias API para validación DIAN
        
        Args:
            invoice_data: Diccionario con los datos de la factura en formato UBL 2.1
        
        Returns:
            Tuple[bool, Dict]: (éxito, datos_respuesta)
        """
        token = self.get_access_token()
        if not token:
            return False, {'error': 'No se pudo obtener token de autenticación'}
        
        try:
            url = f"{self.api_base_url}/invoice"
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                url,
                json=invoice_data,
                headers=headers,
                timeout=60
            )
            
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                # Respuesta exitosa
                return True, response_data
            elif response.status_code == 422:
                # Errores de validación
                return False, {
                    'http_status': 422,
                    'error': 'Errores de validación',
                    'details': response_data
                }
            else:
                # Otros errores HTTP
                return False, {
                    'http_status': response.status_code,
                    'error': response.text,
                    'details': response_data
                }
                
        except requests.Timeout:
            return False, {'error': 'Timeout - La petición tardó demasiado'}
        except Exception as e:
            return False, {'error': f'Excepción: {str(e)}'}
    
    def check_invoice_status(self, track_id: str) -> Tuple[bool, Dict]:
        """
        Consulta el estado de una factura en DIAN usando el trackId
        
        Args:
            track_id: ID de seguimiento devuelto por Matias
        
        Returns:
            Tuple[bool, Dict]: (éxito, datos_respuesta)
        """
        token = self.get_access_token()
        if not token:
            return False, {'error': 'No se pudo obtener token de autenticación'}
        
        try:
            url = f"{self.api_base_url}/invoice/status/{track_id}"
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                return True, response_data
            else:
                return False, {
                    'http_status': response.status_code,
                    'error': response.text,
                    'details': response_data
                }
                
        except Exception as e:
            return False, {'error': f'Excepción: {str(e)}'}
    
    def get_balance(self) -> Tuple[bool, Dict]:
        """
        Consulta el balance de documentos disponibles en Matias
        
        Returns:
            Tuple[bool, Dict]: (éxito, datos_balance)
        """
        token = self.get_access_token()
        if not token:
            return False, {'error': 'No se pudo obtener token de autenticación'}
        
        try:
            url = f"{self.api_base_url}/balance"
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                return True, response_data
            else:
                return False, {
                    'http_status': response.status_code,
                    'error': response.text
                }
                
        except Exception as e:
            return False, {'error': f'Excepción: {str(e)}'}
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Prueba la conexión con Matias API
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        token = self.get_access_token()
        if not token:
            return False, "No se pudo obtener token de autenticación. Verifica las credenciales en .env"
        
        # Intentar obtener balance como prueba
        success, data = self.get_balance()
        if success:
            return True, "Conexión exitosa con Matias API"
        else:
            error_msg = data.get('error', 'Error desconocido')
            return False, f"Error en conexión: {error_msg}"


# Instancia global del cliente
matias_client = MatiasAPIClient()
