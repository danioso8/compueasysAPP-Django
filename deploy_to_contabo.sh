#!/bin/bash
# Script de deployment para Contabo
# Ejecutar en el servidor Contabo

set -e  # Salir si hay errores

echo "=================================="
echo "DEPLOYMENT COMPUEASYS - CONTABO"
echo "=================================="
echo ""

# Variables
APP_DIR="/var/www/compueasys"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="/root/backups/pre-deployment"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "1. Creando backup pre-deployment..."
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -U compueasys_user compueasys_db > $BACKUP_DIR/pre_deploy_$TIMESTAMP.sql
echo -e "${GREEN}✅ Backup creado${NC}"
echo ""

echo "2. Activando entorno virtual..."
source $VENV_DIR/bin/activate
echo -e "${GREEN}✅ Entorno activado${NC}"
echo ""

echo "3. Instalando dependencias..."
pip install -r $APP_DIR/requirements.txt --quiet
echo -e "${GREEN}✅ Dependencias instaladas${NC}"
echo ""

echo "4. Aplicando migraciones..."
cd $APP_DIR
python manage.py migrate --noinput
echo -e "${GREEN}✅ Migraciones aplicadas${NC}"
echo ""

echo "5. Recolectando archivos estáticos..."
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Archivos estáticos recolectados${NC}"
echo ""

echo "6. Reiniciando servicios..."
sudo systemctl restart compueasys
sudo systemctl restart nginx
echo -e "${GREEN}✅ Servicios reiniciados${NC}"
echo ""

echo "7. Verificando estado..."
sleep 2
if systemctl is-active --quiet compueasys; then
    echo -e "${GREEN}✅ CompuEasys está corriendo${NC}"
else
    echo -e "${RED}❌ Error: CompuEasys no está corriendo${NC}"
    sudo journalctl -u compueasys -n 50
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx está corriendo${NC}"
else
    echo -e "${RED}❌ Error: Nginx no está corriendo${NC}"
    exit 1
fi

echo ""
echo "=================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETADO${NC}"
echo "=================================="
echo ""
echo "Verifica el sitio: https://tu-dominio.com"
