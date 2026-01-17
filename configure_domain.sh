#!/bin/bash

# Script para configurar compueasys.com con SSL
echo "======================================"
echo "Configurando compueasys.com con SSL"
echo "======================================"

DOMAIN="compueasys.com"
WWW_DOMAIN="www.compueasys.com"
APP_DIR="/var/www/CompuEasysApp"
EMAIL="danioso8@hotmail.com"

# 1. Instalar Certbot
echo "📦 Instalando Certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# 2. Configurar Nginx para el dominio (sin SSL primero)
echo "⚙️ Configurando Nginx..."
cat > /etc/nginx/sites-available/compueasys << 'EOF'
server {
    listen 80;
    server_name compueasys.com www.compueasys.com;
    
    client_max_body_size 20M;
    
    # Logs
    access_log /var/log/nginx/compueasys_access.log;
    error_log /var/log/nginx/compueasys_error.log;
    
    # Static files
    location /static/ {
        alias /var/www/CompuEasysApp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/CompuEasysApp/media_files/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://unix:/var/www/CompuEasysApp/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# 3. Habilitar configuración
echo "🔗 Habilitando sitio..."
ln -sf /etc/nginx/sites-available/compueasys /etc/nginx/sites-enabled/compueasys

# 4. Probar configuración Nginx
echo "✅ Probando configuración Nginx..."
nginx -t

# 5. Recargar Nginx
echo "🔄 Recargando Nginx..."
systemctl reload nginx

# 6. Obtener certificado SSL con Let's Encrypt
echo "🔒 Obteniendo certificado SSL..."
certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect

# 7. Verificar renovación automática
echo "⏰ Configurando renovación automática..."
systemctl enable certbot.timer
systemctl start certbot.timer

# 8. Actualizar Django settings
echo "🐍 Actualizando Django settings..."
cd $APP_DIR

# Backup del .env
cp .env.contabo .env.contabo.backup

# Actualizar ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS
cat >> .env.contabo << 'ENVEOF'

# Domain configuration
ALLOWED_HOSTS=compueasys.com,www.compueasys.com,84.247.129.180
CSRF_TRUSTED_ORIGINS=https://compueasys.com,https://www.compueasys.com
ENVEOF

# 9. Actualizar settings.py para usar las variables
cat > $APP_DIR/update_settings_domain.py << 'PYEOF'
import os

settings_file = '/var/www/CompuEasysApp/AppCompueasys/settings.py'

with open(settings_file, 'r') as f:
    content = f.read()

# Buscar y actualizar ALLOWED_HOSTS
if "ALLOWED_HOSTS = [" in content:
    # Encontrar la línea y reemplazarla
    import re
    content = re.sub(
        r"ALLOWED_HOSTS = \[.*?\]",
        "ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')",
        content,
        flags=re.DOTALL
    )

# Buscar y actualizar CSRF_TRUSTED_ORIGINS si existe, o agregarlo
if "CSRF_TRUSTED_ORIGINS" in content:
    content = re.sub(
        r"CSRF_TRUSTED_ORIGINS = \[.*?\]",
        "CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')",
        content,
        flags=re.DOTALL
    )
else:
    # Agregar después de ALLOWED_HOSTS
    content = re.sub(
        r"(ALLOWED_HOSTS = .*?\n)",
        r"\1\nCSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')\n",
        content
    )

# Asegurar SECURE_PROXY_SSL_HEADER para HTTPS
if "SECURE_PROXY_SSL_HEADER" not in content:
    # Agregar configuración de seguridad SSL
    ssl_config = """
# Security settings for HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Nginx maneja la redirección
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
"""
    content = re.sub(
        r"(ALLOWED_HOSTS = .*?\n.*?\n)",
        r"\1" + ssl_config + "\n",
        content
    )

with open(settings_file, 'w') as f:
    f.write(content)

print("✅ Settings.py actualizado correctamente")
PYEOF

python3 update_settings_domain.py

# 10. Reiniciar servicios
echo "🔄 Reiniciando servicios..."
systemctl restart compueasys
systemctl reload nginx

# 11. Abrir puerto 443 en firewall
echo "🔥 Configurando firewall..."
ufw allow 443/tcp

echo ""
echo "======================================"
echo "✅ ¡Configuración completada!"
echo "======================================"
echo ""
echo "🌐 Tu sitio está disponible en:"
echo "   https://compueasys.com"
echo "   https://www.compueasys.com"
echo ""
echo "🔒 Certificado SSL instalado y activo"
echo "⏰ Renovación automática configurada"
echo ""
echo "📝 Verifica que el DNS esté propagado:"
echo "   dig compueasys.com +short"
echo "   (debe mostrar: 84.247.129.180)"
echo ""
