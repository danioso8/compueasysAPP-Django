@echo off
echo =========================================
echo   FIX PYTHON - AUTO SETUP
echo =========================================
echo.

cd /d D:\ESCRITORIO\CompueasysApp

echo [1/6] Eliminando entorno virtual antiguo...
if exist venv_new (
    rmdir /s /q venv_new
    echo OK - Entorno antiguo eliminado
) else (
    echo OK - No habia entorno antiguo
)

echo.
echo [2/6] Creando nuevo entorno virtual con Python 3.13...
C:\Python313\python.exe -m venv venv_new
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual
    exit /b 1
)
echo OK - Entorno virtual creado

echo.
echo [3/6] Instalando dependencias (esto puede tardar 1-2 minutos)...
call venv_new\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    exit /b 1
)
echo OK - Dependencias instaladas

echo.
echo [4/6] Creando migraciones del sistema contable...
python manage.py makemigrations contable
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron crear las migraciones
    exit /b 1
)
echo OK - Migraciones creadas

echo.
echo [5/6] Aplicando migraciones...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron aplicar las migraciones
    exit /b 1
)
echo OK - Migraciones aplicadas

echo.
echo [6/6] Inicializando planes de suscripcion...
python manage.py init_plans
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron inicializar los planes
    exit /b 1
)
echo OK - Planes inicializados

echo.
echo =========================================
echo   SETUP COMPLETADO EXITOSAMENTE!
echo =========================================
echo.
echo Sistema listo para usar en:
echo   http://localhost:8000/contable/register/
echo.
echo Para iniciar el servidor ejecuta:
echo   runserver.bat
echo.
