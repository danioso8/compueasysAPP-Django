@echo off
echo ========================================
echo  DEPLOYMENT BILLING MODULE TO CONTABO
echo ========================================
echo.

REM Variables del servidor
set SERVER_IP=84.247.129.180
set SERVER_USER=root
set SERVER_PASS=Miesposa0526
set SERVER_PATH=/var/www/CompuEasysApp
set LOCAL_PATH=D:\ESCRITORIO\CompueasysApp

echo [1/8] Subiendo modulo billing completo...
echo.

REM Crear directorio billing en servidor si no existe
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "mkdir -p %SERVER_PATH%/billing"
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "mkdir -p %SERVER_PATH%/billing/services"
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "mkdir -p %SERVER_PATH%/billing/templates"
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "mkdir -p %SERVER_PATH%/billing/templates/billing"
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "mkdir -p %SERVER_PATH%/billing/migrations"

REM Subir archivos principales del módulo billing
echo Subiendo __init__.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\__init__.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/

echo Subiendo apps.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\apps.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/

echo Subiendo models.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\models.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/

echo Subiendo views.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\views.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/

echo Subiendo urls.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\urls.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/

echo Subiendo admin.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\admin.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/

echo Subiendo signals.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\signals.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/

echo.
echo [2/8] Subiendo servicios (Matias API client)...
echo Subiendo matias_client.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\services\matias_client.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/services/

REM Crear __init__.py en services
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "touch %SERVER_PATH%/billing/services/__init__.py"

echo.
echo [3/8] Subiendo templates...
echo Subiendo invoice_list.html...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\templates\billing\invoice_list.html" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/templates/billing/

echo Subiendo invoice_detail.html...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\templates\billing\invoice_detail.html" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/templates/billing/

echo Subiendo matias_config.html...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\templates\billing\matias_config.html" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/templates/billing/

echo Subiendo invoice_create.html...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\billing\templates\billing\invoice_create.html" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/billing/templates/billing/

echo.
echo [4/8] Creando archivo de migraciones inicial...
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "touch %SERVER_PATH%/billing/migrations/__init__.py"

echo.
echo [5/8] Actualizando settings.py...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\AppCompueasys\settings.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/AppCompueasys/

echo.
echo [6/8] Actualizando urls.py principal...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\AppCompueasys\urls.py" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/AppCompueasys/

echo.
echo [7/8] Actualizando dashboard template con menu facturacion...
pscp -batch -pw %SERVER_PASS% "%LOCAL_PATH%\dashboard\templates\dashboard\dashboard_home.html" %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/dashboard/templates/dashboard/

echo.
echo [8/8] Ejecutando migraciones en servidor...
echo.
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && source venv/bin/activate && python manage.py makemigrations billing && python manage.py migrate billing"

echo.
echo ========================================
echo.
echo Migrando toda la base de datos (por si acaso)...
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && source venv/bin/activate && python manage.py migrate"

echo.
echo ========================================
echo  REINICIANDO SERVICIO COMPUEASYS
echo ========================================
echo.
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "systemctl restart compueasys"

timeout /t 5 /nobreak

echo.
echo Verificando estado del servicio...
echo.
plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "systemctl status compueasys --no-pager -l | head -20"

echo.
echo ========================================
echo  DEPLOYMENT COMPLETADO
echo ========================================
echo.
echo Modulo billing desplegado en: http://compueasys.com/billing/invoices/
echo Dashboard actualizado en: http://compueasys.com/dashboard/
echo.
echo IMPORTANTE: Configurar credenciales de Matias API en:
echo - Acceder a: http://compueasys.com/billing/matias/config/
echo - Configurar: Resolucion DIAN, Email, Password
echo.
echo Para ver logs en tiempo real ejecuta:
echo plink -batch -pw %SERVER_PASS% %SERVER_USER%@%SERVER_IP% "journalctl -u compueasys -f"
echo.
pause
