#!/usr/bin/env python3
"""
Webhook para auto-deployment desde GitHub
Colocar en: /var/www/CompuEasysApp/webhook_deploy.py
Ejecutar con: python webhook_deploy.py
"""

from flask import Flask, request, jsonify
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)

# CONFIGURACIÓN
SECRET_TOKEN = "compueasys_webhook_secret_2026"  # Cambiar por un token seguro
REPO_PATH = "/var/www/CompuEasysApp"
BRANCH = "main"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint que GitHub llama al hacer push"""
    
    # Verificar firma de GitHub (seguridad)
    signature = request.headers.get('X-Hub-Signature-256')
    if signature:
        mac = hmac.new(
            SECRET_TOKEN.encode(),
            msg=request.data,
            digestmod=hashlib.sha256
        )
        expected_signature = 'sha256=' + mac.hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({'error': 'Invalid signature'}), 403
    
    # Obtener datos del push
    data = request.json
    
    # Verificar que sea push a la rama main
    if 'ref' in data and data['ref'] == f'refs/heads/{BRANCH}':
        print(f"✅ Push detectado en rama {BRANCH}")
        
        try:
            # Ejecutar deployment
            result = subprocess.run(
                ['/var/www/CompuEasysApp/deploy_auto.sh'],
                cwd=REPO_PATH,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos máximo
            )
            
            if result.returncode == 0:
                return jsonify({
                    'status': 'success',
                    'message': 'Deployment completado',
                    'output': result.stdout
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Deployment falló',
                    'error': result.stderr
                }), 500
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    return jsonify({'status': 'ignored', 'message': 'Not a main branch push'}), 200

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud"""
    return jsonify({'status': 'ok', 'service': 'webhook-deploy'}), 200

if __name__ == '__main__':
    # Puerto 8001 para el webhook
    app.run(host='0.0.0.0', port=8001, debug=False)
