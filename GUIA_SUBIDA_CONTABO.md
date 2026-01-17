# GUÍA RÁPIDA - SUBIR COMPUEASYSAPP A CONTABO

**Servidor:** root@84.247.129.180  
**Proyecto:** CompuEasysApp

## 🔐 Paso 1: Verificar Clave SSH

La clave SSH ya debe estar configurada de OpticaApp. Para verificar:

```bash
ssh root@84.247.129.180
```

Si te pide contraseña, la clave SSH no está configurada. Para configurarla:

```bash
# En tu máquina local (si no existe ya)
ssh-keygen -t rsa -b 4096 -C "tu-email@ejemplo.com"

# Copiar clave al servidor
ssh-copy-id root@84.247.129.180
```

## 🚀 Paso 2: Subir Proyecto a Contabo

Ejecuta el script automatizado:

```bash
upload_to_contabo.bat
```

Esto subirá:
- ✅ Código fuente (sin venv, pycache, etc.)
- ✅ Backup de base de datos
- ✅ Imágenes (si existen localmente)
- ✅ Archivos de configuración

## ⚙️ Paso 3: Configurar en Servidor

Conéctate al servidor:

```bash
ssh root@84.247.129.180
```

Ejecuta el script de configuración inicial:

```bash
cd /var/www/CompuEasysApp
chmod +x setup_contabo.sh
./setup_contabo.sh
```

Este script hace TODO automáticamente:
- Instala PostgreSQL (si no está)
- Crea base de datos
- Configura entorno virtual
- Instala dependencias
- Restaura backup
- Configura Nginx
- Crea servicio systemd

## 📊 Paso 4: Verificar Instalación

```bash
# Ver estado del servicio
sudo systemctl status compueasys

# Ver logs en tiempo real
sudo journalctl -u compueasys -f

# Probar sitio
curl http://84.247.129.180
```

## 🌐 Paso 5: Configurar Dominio (Opcional)

Si tienes un dominio, configurar SSL:

```bash
sudo certbot --nginx -d compueasys.tu-dominio.com
```

## 🔄 Para Actualizar el Proyecto

Cuando hagas cambios y quieras actualizar:

```bash
# En tu máquina local
upload_to_contabo.bat

# En el servidor
cd /var/www/CompuEasysApp
./deploy_to_contabo.sh
```

## 📁 Estructura en Servidor

```
/var/www/CompuEasysApp/         # Código del proyecto
├── venv/                        # Entorno virtual
├── media/                       # Imágenes
├── staticfiles/                 # Archivos estáticos
├── .env                         # Variables de entorno
└── compueasys.sock             # Socket Unix

/root/backups/CompuEasysApp/    # Backups de BD
```

## ⚠️ IMPORTANTE - Sobre las Imágenes

Actualmente las imágenes están en Render, no en local. 

**Opción 1 (Más fácil):** Mantener imágenes en Render
- En `settings.py` usar: `MEDIA_URL = 'https://compueasys.onrender.com/media/'`

**Opción 2:** Descargar de Render primero
- Conectarte a Render y descargar media_files
- Luego ejecutar `upload_to_contabo.bat`

## 🎯 PROYECTOS PENDIENTES

Ya completados:
- ✅ OpticaApp
- ✅ CompuEasysApp (este)

Pendientes:
- ⏳ Inmobiliaria
- ⏳ Restaurante
- ⏳ Clínica Dental
- ⏳ Compraventa

## 🆘 Troubleshooting

### Error: "Permission denied"
```bash
sudo chown -R www-data:www-data /var/www/CompuEasysApp
```

### Error: "Module not found"
```bash
cd /var/www/CompuEasysApp
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "502 Bad Gateway"
```bash
sudo systemctl restart compueasys
sudo systemctl restart nginx
```

### Ver logs detallados
```bash
sudo journalctl -u compueasys -n 100 --no-pager
```
