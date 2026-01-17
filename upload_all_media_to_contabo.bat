@echo off
echo ================================================================================
echo SUBIENDO TODAS LAS IMAGENES A CONTABO
echo ================================================================================
echo.

echo [1/4] Subiendo imagenes de productos...
pscp -r -pw Miesposa0526 media_files\images\*.* root@84.247.129.180:/var/www/CompuEasysApp/media_files/images/

echo.
echo [2/4] Subiendo imagenes de galeria...
pscp -r -pw Miesposa0526 media_files\galeria\*.* root@84.247.129.180:/var/www/CompuEasysApp/media_files/galeria/

echo.
echo [3/4] Subiendo imagenes de variantes...
pscp -r -pw Miesposa0526 media_files\variant_images\*.* root@84.247.129.180:/var/www/CompuEasysApp/media_files/variant_images/

echo.
echo [4/4] Subiendo otras imagenes...
pscp -r -pw Miesposa0526 media_files\upload\*.* root@84.247.129.180:/var/www/CompuEasysApp/media_files/upload/

echo.
echo ================================================================================
echo CARGA COMPLETADA
echo ================================================================================
pause
