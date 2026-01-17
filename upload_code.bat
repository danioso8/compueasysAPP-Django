@echo off
echo ================================================================
echo   SUBIENDO CODIGO COMPLETO A CONTABO
echo ================================================================
echo.

set SERVER=root@84.247.129.180
set PASSWORD=Miesposa0526
set LOCAL_PATH=D:\ESCRITORIO\CompueasysApp
set REMOTE_PATH=/var/www/CompuEasysApp

echo [1/6] Subiendo codigo fuente...
pscp -r -pw %PASSWORD% AppCompueasys contable core dashboard shared %SERVER%:%REMOTE_PATH%/
echo   OK
echo.

echo [2/6] Subiendo archivos de configuracion...
pscp -pw %PASSWORD% manage.py requirements.txt .env.contabo %SERVER%:%REMOTE_PATH%/
plink -pw %PASSWORD% %SERVER% "mv %REMOTE_PATH%/.env.contabo %REMOTE_PATH%/.env"
echo   OK
echo.

echo [3/6] Subiendo backups...
pscp -r -pw %PASSWORD% backups %SERVER%:%REMOTE_PATH%/
echo   OK
echo.

echo [4/6] Subiendo media files...
pscp -r -pw %PASSWORD% media_files %SERVER%:%REMOTE_PATH%/
echo   OK
echo.

echo [5/6] Subiendo archivos estaticos...
pscp -r -pw %PASSWORD% staticfiles %SERVER%:%REMOTE_PATH%/
echo   OK
echo.

echo [6/6] Configurando permisos...
plink -pw %PASSWORD% %SERVER% "chmod 755 %REMOTE_PATH% && chown -R www-data:www-data %REMOTE_PATH%/media_files %REMOTE_PATH%/staticfiles"
echo   OK
echo.

echo ================================================================
echo   CODIGO SUBIDO EXITOSAMENTE
echo ================================================================
echo.
pause
