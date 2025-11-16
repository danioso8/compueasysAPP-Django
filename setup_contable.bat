@echo off
setlocal

REM Deshabilitar alias de Python de Windows
set PATH=D:\ESCRITORIO\CompueasysApp\venv_new\Scripts;%PATH%

echo =========================================
echo  SISTEMA CONTABLE - INSTALACION COMPLETA
echo =========================================
echo.

echo [1/4] Creando migraciones...
call venv_new\Scripts\activate.bat
python manage.py makemigrations contable
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron crear las migraciones
    pause
    exit /b 1
)
echo.

echo [2/4] Aplicando migraciones...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron aplicar las migraciones
    pause
    exit /b 1
)
echo.

echo [3/4] Inicializando planes de suscripcion...
python manage.py init_plans
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron inicializar los planes
    pause
    exit /b 1
)
echo.

echo =========================================
echo  INSTALACION COMPLETADA EXITOSAMENTE
echo =========================================
echo.
echo El sistema contable esta listo para usarse:
echo.
echo   Registro: http://localhost:8000/contable/register/
echo   Login:    http://localhost:8000/contable/login/
echo   Home:     http://localhost:8000/
echo.
echo Presiona cualquier tecla para iniciar el servidor...
pause > nul

echo.
echo [4/4] Iniciando servidor Django...
python manage.py runserver

pause
endlocal
