@echo off
echo ================================================================
echo   CONFIGURANDO NGINX Y GUNICORN EN CONTABO
echo ================================================================
echo.

set SERVER=root@84.247.129.180
set PASSWORD=Miesposa0526
set APP_PATH=/var/www/CompuEasysApp

echo [1/4] Instalando Gunicorn...
plink -pw %PASSWORD% %SERVER% "cd %APP_PATH% && source venv/bin/activate && pip install gunicorn"
echo   OK - Gunicorn instalado
echo.

echo [2/4] Creando servicio systemd...
plink -pw %PASSWORD% %SERVER% "cat > /etc/systemd/system/compueasys.service << 'EOF'
[Unit]
Description=CompuEasys Gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/CompuEasysApp
Environment=\"PATH=/var/www/CompuEasysApp/venv/bin\"
ExecStart=/var/www/CompuEasysApp/venv/bin/gunicorn --workers 3 --bind unix:/var/www/CompuEasysApp/gunicorn.sock AppCompueasys.wsgi:application

[Install]
WantedBy=multi-user.target
EOF"
echo   OK - Servicio systemd creado
echo.

echo [3/4] Configurando Nginx...
plink -pw %PASSWORD% %SERVER% "cat > /etc/nginx/sites-available/compueasys << 'EOF'
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
EOF"
plink -pw %PASSWORD% %SERVER% "ln -sf /etc/nginx/sites-available/compueasys /etc/nginx/sites-enabled/"
plink -pw %PASSWORD% %SERVER% "nginx -t"
echo   OK - Nginx configurado
echo.

echo [4/4] Recolectando archivos estaticos y reiniciando servicios...
plink -pw %PASSWORD% %SERVER% "cd %APP_PATH% && source venv/bin/activate && python manage.py collectstatic --noinput"
plink -pw %PASSWORD% %SERVER% "systemctl daemon-reload"
plink -pw %PASSWORD% %SERVER% "systemctl start compueasys"
plink -pw %PASSWORD% %SERVER% "systemctl enable compueasys"
plink -pw %PASSWORD% %SERVER% "systemctl restart nginx"
echo   OK - Servicios iniciados
echo.

echo ================================================================
echo   DEPLOYMENT COMPLETADO
echo ================================================================
echo.
echo CompuEasysApp disponible en: http://84.247.129.180:8001
echo.
echo Comandos utiles:
echo   Ver logs: plink -pw %PASSWORD% %SERVER% "journalctl -u compueasys -f"
echo   Estado: plink -pw %PASSWORD% %SERVER% "systemctl status compueasys"
echo.
pause
