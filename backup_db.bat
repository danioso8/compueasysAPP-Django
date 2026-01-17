@echo off
REM Script para hacer backup de la base de datos de Render
echo ================================================
echo   BACKUP BASE DE DATOS COMPUEASYS - RENDER
echo ================================================
echo.

REM Activar entorno virtual
call .\venv_new\Scripts\activate

REM Ejecutar script de backup Django
python backup_django.py

pause
