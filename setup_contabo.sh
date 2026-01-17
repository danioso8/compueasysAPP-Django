#!/bin/bash
# Script de configuración inicial en Contabo para CompuEasysApp

set -e

echo "================================================================"
echo "CONFIGURACIÓN INICIAL COMPUEASYSAPP EN CONTABO"
echo "================================================================"
echo ""

PROJECT_NAME="CompuEasysApp"
PROJECT_DIR="/var/www/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "1. Verificando requisitos del sistema..."
echo "================================================"

# Verificar si PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL no está instalado${NC}"
    echo "Instalando PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    echo -e "${GREEN}PostgreSQL instalado${NC}"
else
    echo -e "${GREEN}PostgreSQL ya está instalado${NC}"
fi

# Verificar si Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 no está instalado${NC}"
    sudo apt install -y python3 python3-pip python3-venv
    echo -e "${GREEN}Python3 instalado${NC}"
else
    echo -e "${GREEN}Python3 ya está instalado${NC}"
fi

# Verificar si Nginx está instalado
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx no está instalado${NC}"
    read -p "¿Deseas instalar Nginx? (s/n): " install_nginx
    if [ "$install_nginx" = "s" ]; then
        sudo apt install -y nginx
        sudo systemctl start nginx
        sudo systemctl enable nginx
        echo -e "${GREEN}Nginx instalado${NC}"
    fi
else
    echo -e "${GREEN}Nginx ya está instalado${NC}"
fi

echo ""
echo "2. Configurando Base de Datos PostgreSQL"
echo "================================================"

read -p "Nombre de la base de datos [compueasys_db]: " DB_NAME
DB_NAME=${DB_NAME:-compueasys_db}

read -p "Usuario de la base de datos [compueasys_user]: " DB_USER
DB_USER=${DB_USER:-compueasys_user}

read -sp "Contraseña para $DB_USER: " DB_PASSWORD
echo ""

# Crear base de datos y usuario
sudo -u postgres psql <<EOF
-- Crear base de datos si no existe
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Crear usuario si no existe
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
EOF

echo -e "${GREEN}Base de datos configurada${NC}"
echo ""

echo "3. Configurando Entorno Virtual Python"
echo "================================================"

cd $PROJECT_DIR

if [ ! -d "$VENV_DIR" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate

echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Entorno virtual configurado${NC}"
echo ""

echo "4. Configurando Variables de Entorno"
echo "================================================"

# Generar SECRET_KEY
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

cat > $PROJECT_DIR/.env <<EOF
# Configuración de Producción - CompuEasysApp
SECRET_KEY=$SECRET_KEY
DEBUG=False
DJANGO_DEVELOPMENT=False

# Base de Datos
DB_NAME=$DB_NAME
DB_USERNAME=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Servidor
ALLOWED_HOSTS=84.247.129.180,compueasys.tu-dominio.com

# Email (configurar según necesites)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# Seguridad
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EOF

echo -e "${GREEN}Archivo .env creado${NC}"
echo ""

echo "5. Ejecutando Migraciones"
echo "================================================"

python manage.py migrate

echo -e "${GREEN}Migraciones aplicadas${NC}"
echo ""

echo "6. Restaurando Backup de Base de Datos"
echo "================================================"

# Buscar el backup más reciente
BACKUP_FILE=$(ls -t /root/backups/$PROJECT_NAME/*.json 2>/dev/null | head -1)

if [ -n "$BACKUP_FILE" ]; then
    echo "Restaurando desde: $BACKUP_FILE"
    python manage.py loaddata "$BACKUP_FILE"
    echo -e "${GREEN}Backup restaurado exitosamente${NC}"
else
    echo -e "${YELLOW}No se encontró archivo de backup${NC}"
fi

echo ""

echo "7. Recolectando Archivos Estáticos"
echo "================================================"

python manage.py collectstatic --noinput

echo -e "${GREEN}Archivos estáticos recolectados${NC}"
echo ""

echo "8. Creando Servicio Systemd"
echo "================================================"

sudo tee /etc/systemd/system/compueasys.service > /dev/null <<EOF
[Unit]
Description=CompuEasys Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 3 \\
    --bind unix:$PROJECT_DIR/compueasys.sock \\
    --timeout 120 \\
    AppCompueasys.wsgi:application

ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable compueasys
sudo systemctl start compueasys

echo -e "${GREEN}Servicio systemd configurado${NC}"
echo ""

echo "9. Configurando Nginx"
echo "================================================"

read -p "¿Configurar Nginx ahora? (s/n): " config_nginx

if [ "$config_nginx" = "s" ]; then
    read -p "Dominio o IP [84.247.129.180]: " DOMAIN
    DOMAIN=${DOMAIN:-84.247.129.180}

    sudo tee /etc/nginx/sites-available/compueasys > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 10M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/compueasys.sock;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_redirect off;
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/compueasys /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx

    echo -e "${GREEN}Nginx configurado${NC}"
fi

echo ""
echo "================================================================"
echo -e "${GREEN}✅ CONFIGURACIÓN COMPLETADA${NC}"
echo "================================================================"
echo ""
echo "Resumen de la instalación:"
echo "  • Base de datos: $DB_NAME"
echo "  • Usuario DB: $DB_USER"
echo "  • Directorio: $PROJECT_DIR"
echo "  • Servicio: compueasys.service"
echo ""
echo "Estado de servicios:"
sudo systemctl status compueasys --no-pager -l | head -5
echo ""
echo "Próximos pasos:"
echo "  1. Verificar el sitio: http://$DOMAIN"
echo "  2. Configurar SSL: sudo certbot --nginx -d tu-dominio.com"
echo "  3. Configurar backups automáticos"
echo ""
echo "================================================================"
