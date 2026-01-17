#!/bin/bash
# Script final para iniciar CompuEasysApp en Contabo

echo "🚀 INICIANDO COMPUEASYSAPP EN CONTABO"
echo "===================================="
echo ""

cd /var/www/CompuEasysApp

# 1. Crear servicio systemd correctamente
echo "📝 [1/5] Creando servicio systemd..."
cat > /tmp/compueasys.service << 'EOF'
[Unit]
Description=CompuEasys Gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/CompuEasysApp
Environment="PATH=/var/www/CompuEasysApp/venv/bin"
ExecStart=/var/www/CompuEasysApp/venv/bin/gunicorn --workers 3 --bind unix:/var/www/CompuEasysApp/gunicorn.sock AppCompueasys.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

mv /tmp/compueasys.service /etc/systemd/system/compueasys.service
echo "✅ Servicio creado"
echo ""

# 2. Crear configuración Nginx
echo "🌐 [2/5] Configurando Nginx..."
cat > /tmp/compueasys << 'EOF'
server {
    listen 8001;
    server_name 84.247.129.180;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/CompuEasysApp/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/CompuEasysApp/media_files/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/CompuEasysApp/gunicorn.sock;
    }
}
EOF

mv /tmp/compueasys /etc/nginx/sites-available/compueasys
ln -sf /etc/nginx/sites-available/compueasys /etc/nginx/sites-enabled/
nginx -t
echo "✅ Nginx configurado"
echo ""

# 3. Configurar permisos
echo "🔒 [3/5] Configurando permisos..."
chown -R www-data:www-data /var/www/CompuEasysApp/media_files
chown -R www-data:www-data /var/www/CompuEasysApp/staticfiles
chmod 755 /var/www/CompuEasysApp
echo "✅ Permisos configurados"
echo ""

# 4. Iniciar servicios
echo "⚡ [4/5] Iniciando servicios..."
systemctl unmask compueasys 2>/dev/null || true
systemctl daemon-reload
systemctl start compueasys
systemctl enable compueasys
systemctl restart nginx
echo "✅ Servicios iniciados"
echo ""

# 5. Verificar estado
echo "📊 [5/5] Verificando estado..."
systemctl status compueasys --no-pager
echo ""

echo "===================================="
echo "✅ COMPUEASYSAPP DESPLEGADO"
echo "===================================="
echo ""
echo "🌍 URL: http://84.247.129.180:8001"
echo ""
echo "📝 Ver logs en tiempo real:"
echo "   journalctl -u compueasys -f"
echo ""
