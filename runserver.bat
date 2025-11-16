@echo off
echo =========================================
echo   INICIANDO SERVIDOR DJANGO
echo =========================================
echo.
cd /d D:\ESCRITORIO\CompueasysApp
call venv_new\Scripts\activate.bat
echo Servidor iniciando en http://localhost:8000/
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
python manage.py runserver
pause
