@echo off
echo =========================================
echo   FIX PYTHON - RECREAR ENTORNO VIRTUAL
echo =========================================
echo.
echo Este script va a:
echo 1. Eliminar el entorno virtual antiguo (venv_new)
echo 2. Crear uno nuevo con Python 3.13
echo 3. Instalar todas las dependencias
echo 4. Configurar el sistema contable
echo.
echo ADVERTENCIA: Se eliminara la carpeta venv_new
echo.
pause

cd /d D:\ESCRITORIO\CompueasysApp

echo.
echo [1/6] Eliminando entorno virtual antiguo...
if exist venv_new (
    rmdir /s /q venv_new
    echo Entorno antiguo eliminado
) else (
    echo No se encontro entorno antiguo
)

echo.
echo [2/6] Creando nuevo entorno virtual con Python 3.13...
C:\Python313\python.exe -m venv venv_new
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual
    echo Verifica que Python 3.13 este instalado en C:\Python313\
    pause
    exit /b 1
)
echo Entorno virtual creado exitosamente

echo.
echo [3/6] Activando entorno e instalando dependencias...
call venv_new\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo [4/6] Creando migraciones del sistema contable...
python manage.py makemigrations contable
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron crear las migraciones
    pause
    exit /b 1
)

echo.
echo [5/6] Aplicando migraciones...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron aplicar las migraciones
    pause
    exit /b 1
)

echo.
echo [6/6] Inicializando planes de suscripcion...
python manage.py init_plans
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron inicializar los planes
    pause
    exit /b 1
)

echo.
echo =========================================
echo   CONFIGURACION COMPLETADA EXITOSAMENTE
echo =========================================
echo.
echo El sistema esta listo para usarse.
echo.
echo Para iniciar el servidor:
echo   runserver.bat
echo.
echo O manualmente:
echo   venv_new\Scripts\activate
echo   python manage.py runserver
echo.
pause

echo.
echo Quieres iniciar el servidor ahora? (S/N)
set /p respuesta=
if /i "%respuesta%"=="S" (
    echo.
    echo Iniciando servidor Django...
    python manage.py runserver
)
