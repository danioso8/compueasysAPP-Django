@echo off
REM Script maestro para migración completa a Contabo
echo ================================================================
echo   MIGRACION COMPLETA COMPUEASYS - RENDER A CONTABO
echo ================================================================
echo.
echo Este proceso realizara:
echo   1. Backup blindado de la base de datos (3 copias)
echo   2. Descarga de todas las imagenes desde Render
echo   3. Preparacion de archivos para Contabo
echo.
pause
echo.

REM Activar entorno virtual
call .\venv_new\Scripts\activate

echo ================================================================
echo PASO 1: BACKUP BLINDADO DE BASE DE DATOS
echo ================================================================
echo.
python backup_blindado.py
echo.
echo Presiona cualquier tecla para continuar con la descarga de imagenes...
pause > nul
echo.

echo ================================================================
echo PASO 2: DESCARGA DE IMAGENES DESDE RENDER
echo ================================================================
echo.
python download_render_images.py
echo.
echo Presiona cualquier tecla para continuar con la preparacion...
pause > nul
echo.

echo ================================================================
echo PASO 3: PREPARAR ARCHIVOS DE MIGRACION
echo ================================================================
echo.
python prepare_contabo_migration.py
echo.

echo ================================================================
echo MIGRACION COMPLETADA
echo ================================================================
echo.
echo Archivos generados:
echo   - backups/             (Backups de base de datos)
echo   - backups_secondary/   (Backup secundario)
echo   - backups_archive/     (Backup archivado con apps separadas)
echo   - media_backup/        (Imagenes descargadas)
echo   - CONTABO_MIGRATION_GUIDE_*.md (Guia de migracion)
echo.
echo Siguiente paso: Lee la guia de migracion generada
echo.
pause
