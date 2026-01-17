@echo off
REM Script para subir CompuEasysApp a Contabo via SCP
REM Servidor: root@84.247.129.180

echo ================================================================
echo   SUBIENDO COMPUEASYSAPP A CONTABO
echo ================================================================
echo.
echo Servidor: root@84.247.129.180
echo Proyecto: CompuEasysApp
echo.

SET SERVER=root@84.247.129.180
SET PROJECT_NAME=CompuEasysApp
SET REMOTE_PATH=/var/www/%PROJECT_NAME%

echo ================================================================
echo PASO 1: CREAR ESTRUCTURA EN SERVIDOR
echo ================================================================
echo.

REM Crear directorio del proyecto en el servidor
ssh %SERVER% "mkdir -p %REMOTE_PATH%"
ssh %SERVER% "mkdir -p /root/backups/%PROJECT_NAME%"
ssh %SERVER% "mkdir -p %REMOTE_PATH%/media"

echo   Estructura creada en servidor
echo.

echo ================================================================
echo PASO 2: SUBIR CODIGO FUENTE
echo ================================================================
echo.

REM Subir código del proyecto (excluyendo archivos innecesarios)
scp -r ^
  --exclude="venv_new" ^
  --exclude="__pycache__" ^
  --exclude="*.pyc" ^
  --exclude=".git" ^
  --exclude="db.sqlite3" ^
  --exclude="backups" ^
  --exclude="backups_secondary" ^
  --exclude="backups_archive" ^
  --exclude="media_files" ^
  --exclude="staticfiles" ^
  . %SERVER%:%REMOTE_PATH%/

echo   Codigo fuente subido
echo.

echo ================================================================
echo PASO 3: SUBIR BACKUPS DE BASE DE DATOS
echo ================================================================
echo.

REM Subir el backup más reciente
for /f "delims=" %%i in ('dir /b /od backups\compueasys_backup_*.json') do set LATEST_BACKUP=%%i

if defined LATEST_BACKUP (
    echo   Subiendo: %LATEST_BACKUP%
    scp backups\%LATEST_BACKUP% %SERVER%:/root/backups/%PROJECT_NAME%/
    echo   Backup subido
) else (
    echo   ERROR: No se encontro backup de base de datos
    pause
    exit /b 1
)

echo.

echo ================================================================
echo PASO 4: SUBIR ARCHIVOS MEDIA (IMAGENES)
echo ================================================================
echo.

REM Verificar si existen archivos media localmente
if exist "media_files\images" (
    echo   Subiendo imagenes de productos...
    scp -r media_files\images %SERVER%:%REMOTE_PATH%/media/
    echo   Imagenes de productos subidas
)

if exist "media_files\galeria" (
    echo   Subiendo imagenes de galeria...
    scp -r media_files\galeria %SERVER%:%REMOTE_PATH%/media/
    echo   Imagenes de galeria subidas
)

if exist "media_files\variant_images" (
    echo   Subiendo imagenes de variantes...
    scp -r media_files\variant_images %SERVER%:%REMOTE_PATH%/media/
    echo   Imagenes de variantes subidas
)

echo.

echo ================================================================
echo PASO 5: SUBIR ARCHIVOS DE CONFIGURACION
echo ================================================================
echo.

REM Subir archivos de configuración
scp env_contabo_template.txt %SERVER%:%REMOTE_PATH%/.env.example
scp deploy_to_contabo.sh %SERVER%:%REMOTE_PATH%/
ssh %SERVER% "chmod +x %REMOTE_PATH%/deploy_to_contabo.sh"

echo   Archivos de configuracion subidos
echo.

echo ================================================================
echo PASO 6: CONFIGURAR PERMISOS
echo ================================================================
echo.

ssh %SERVER% "chown -R www-data:www-data %REMOTE_PATH%/media"
ssh %SERVER% "chmod -R 755 %REMOTE_PATH%/media"

echo   Permisos configurados
echo.

echo ================================================================
echo RESUMEN DE SUBIDA
echo ================================================================
echo.
echo   Servidor: %SERVER%
echo   Ruta: %REMOTE_PATH%
echo   Backup: %LATEST_BACKUP%
echo.
echo Siguiente paso:
echo   1. Conectate al servidor: ssh %SERVER%
echo   2. Ve al directorio: cd %REMOTE_PATH%
echo   3. Configura .env: nano .env
echo   4. Ejecuta deployment: ./deploy_to_contabo.sh
echo.
echo ================================================================

pause
