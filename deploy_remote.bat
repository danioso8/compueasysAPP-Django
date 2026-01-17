@echo off
echo ================================================================
echo   CONFIGURANDO COMPUEASYSAPP EN CONTABO
echo ================================================================
echo.

set SERVER=root@84.247.129.180
set PASSWORD=Miesposa0526
set APP_PATH=/var/www/CompuEasysApp

echo [1/5] Copiando archivo .env...
pscp -pw %PASSWORD% ".env.contabo" %SERVER%:%APP_PATH%/.env
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo copiar .env
    pause
    exit /b 1
)
echo   OK - Archivo .env copiado
echo.

echo [2/5] Instalando Python y dependencias...
plink -pw %PASSWORD% %SERVER% "cd %APP_PATH% && apt update && apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx"
echo   OK - Dependencias instaladas
echo.

echo [3/5] Creando base de datos PostgreSQL...
plink -pw %PASSWORD% %SERVER% "sudo -u postgres psql -c \"CREATE DATABASE compueasys_db;\" 2>/dev/null || echo 'DB ya existe'"
plink -pw %PASSWORD% %SERVER% "sudo -u postgres psql -c \"CREATE USER compueasys_user WITH PASSWORD 'CompuEasys2026!';\" 2>/dev/null || echo 'Usuario ya existe'"
plink -pw %PASSWORD% %SERVER% "sudo -u postgres psql -c \"ALTER ROLE compueasys_user SET client_encoding TO 'utf8';\""
plink -pw %PASSWORD% %SERVER% "sudo -u postgres psql -c \"ALTER ROLE compueasys_user SET default_transaction_isolation TO 'read committed';\""
plink -pw %PASSWORD% %SERVER% "sudo -u postgres psql -c \"ALTER ROLE compueasys_user SET timezone TO 'UTC';\""
plink -pw %PASSWORD% %SERVER% "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE compueasys_db TO compueasys_user;\""
echo   OK - Base de datos configurada
echo.

echo [4/5] Configurando entorno Python...
plink -pw %PASSWORD% %SERVER% "cd %APP_PATH% && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
echo   OK - Entorno Python configurado
echo.

echo [5/5] Restaurando base de datos...
plink -pw %PASSWORD% %SERVER% "cd %APP_PATH% && source venv/bin/activate && python manage.py migrate && python manage.py loaddata backups/compueasys_backup_20260115_101646.json"
echo   OK - Base de datos restaurada
echo.

echo ================================================================
echo   CONFIGURACION COMPLETADA
echo ================================================================
echo.
echo Siguiente paso: Configurar Nginx y Gunicorn
echo.
echo Ejecuta: deploy_nginx.bat
echo.
pause
