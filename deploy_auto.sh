#!/bin/bash
# Script de auto-deployment optimizado
# Ubicación: /var/www/CompuEasysApp/deploy_auto.sh

set -e
LOG_FILE="/var/log/compueasys_deploy.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 🚀 Iniciando auto-deployment..." | tee -a $LOG_FILE

cd /var/www/CompuEasysApp

# 1. Git pull
echo "$(date '+%Y-%m-%d %H:%M:%S') - 📥 Obteniendo cambios de GitHub..." | tee -a $LOG_FILE
git pull origin main 2>&1 | tee -a $LOG_FILE

# 2. Activar entorno virtual
source venv/bin/activate

# 3. Instalar dependencias (solo si requirements.txt cambió)
if git diff HEAD@{1} --name-only | grep -q "requirements.txt"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 📦 Instalando dependencias..." | tee -a $LOG_FILE
    pip install -r requirements.txt --quiet 2>&1 | tee -a $LOG_FILE
fi

# 4. Aplicar migraciones (solo si hay nuevas)
echo "$(date '+%Y-%m-%d %H:%M:%S') - 🔄 Verificando migraciones..." | tee -a $LOG_FILE
python manage.py migrate --noinput 2>&1 | tee -a $LOG_FILE

# 5. Recolectar estáticos (solo si cambiaron archivos static)
if git diff HEAD@{1} --name-only | grep -q "static\|staticfiles"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 📁 Recolectando archivos estáticos..." | tee -a $LOG_FILE
    python manage.py collectstatic --noinput 2>&1 | tee -a $LOG_FILE
fi

# 6. Reiniciar Gunicorn
echo "$(date '+%Y-%m-%d %H:%M:%S') - 🔄 Reiniciando servicios..." | tee -a $LOG_FILE
sudo systemctl restart compueasys 2>&1 | tee -a $LOG_FILE

# 7. Verificar estado
sleep 2
if systemctl is-active --quiet compueasys; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Deployment completado exitosamente" | tee -a $LOG_FILE
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ Error: Servicio no inició" | tee -a $LOG_FILE
    sudo journalctl -u compueasys -n 20 2>&1 | tee -a $LOG_FILE
    exit 1
fi
