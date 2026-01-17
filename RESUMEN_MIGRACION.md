# ✅ RESUMEN DE BACKUP Y MIGRACIÓN - COMPUEASYS

**Fecha:** 15 de enero de 2026  
**Estado:** Backup de Base de Datos Completado ✅  
**Próximo Paso:** Migración a Contabo

---

## 🗄️ BACKUP DE BASE DE DATOS - COMPLETADO

### Ubicaciones del Backup Blindado

✅ **Backup Primario:** `backups/compueasys_backup_20260115_101646.json`
- Tamaño: 3.17 MB
- Registros: 8,801
- Formato: JSON completo

✅ **Backup Secundario:** `backups_secondary/compueasys_backup_20260115_101646.json`
- Tamaño: 3.17 MB
- Registros: 8,801
- Formato: JSON completo

✅ **Backup Archivado:** `backups_archive/20260115_101646/`
- Backups separados por aplicación
- Backup SQL
- Archivo comprimido ZIP (1.21 MB)

### Estadísticas de la Base de Datos

```
📊 Total de registros: 8,801

Por aplicación:
• CORE: 5,313 registros
  - ProductStore: 71 productos
  - Galeria: 258 imágenes de galería
  - ProductVariant: 25 variantes
  - StoreVisit: 4,698 visitas
  - Pedido: 90 órdenes
  - SimpleUser: 5 usuarios

• AUTH: 239 registros
  - User: 7 usuarios
  - Permission: 232 permisos

• CONTABLE: 28 registros
  - ContableUser: 2 usuarios
  - Company: 2 empresas
  - Plan: 3 planes

• DASHBOARD: 4 registros
  - WompiConfig: 1
  - StoreConfig: 1
  - Register_superuser: 2

• SESSIONS: 3,155 sesiones activas
```

---

## 📸 IMÁGENES - SITUACIÓN ACTUAL

### Estado de las Imágenes

❌ **Las imágenes NO están en local** - Están siendo servidas desde Render en producción
 
- URL de imágenes: `https://compueasys.onrender.com/media/`
- Total de archivos:
  - 71 imágenes de productos
  - 258 imágenes de galería
  - 25 imágenes de variantes
  - **Total: 354 archivos de imagen**

### Opciones para las Imágenes

**Opción 1: Mantener imágenes en Render (Recomendado para migración rápida)**
- Las imágenes ya están funcionando desde Render
- No requiere descarga ni migración de archivos
- Configuración actual en desarrollo ya apunta a Render

**Opción 2: Migrar imágenes a Contabo**
- Requiere acceso al servidor de Render para descargar
- Comandos necesarios desde servidor Render:
  ```bash
  # Conectarse al servidor Render vía SSH o usar Render CLI
  tar -czf media_backup.tar.gz /opt/render/project/src/media_files/
  # Descargar el archivo comprimido
  ```

**Opción 3: Usar almacenamiento en la nube (S3, Cloudinary)**
- Más robusto y escalable
- Requiere configuración adicional

---

## 🚀 ARCHIVOS GENERADOS PARA MIGRACIÓN

### 1. Scripts de Backup
- ✅ `backup_blindado.py` - Backup con 3 copias de seguridad
- ✅ `backup_django.py` - Backup usando Django
- ✅ `restore_backup.py` - Restaurar backups

### 2. Documentación de Migración
- ✅ `prepare_contabo_migration.py` - Genera guía y scripts
- ⏳ Pendiente: Ejecutar para generar:
  - Guía completa de migración paso a paso
  - Template de variables de entorno
  - Script de deployment automatizado

### 3. Herramientas de Migración
- ✅ `migrate_to_contabo.bat` - Script maestro (Windows)
- ✅ `backup_db.bat` - Acceso rápido a backup

---

## 📋 CHECKLIST DE MIGRACIÓN A CONTABO

### Pre-requisitos en Contabo
- [ ] Servidor VPS/Cloud configurado
- [ ] PostgreSQL 13+ instalado
- [ ] Base de datos creada
- [ ] Usuario de PostgreSQL con permisos
- [ ] Python 3.13+ instalado
- [ ] Git instalado
- [ ] Nginx o Apache configurado

### Paso 1: Subir Código y Backups
```bash
# Desde tu máquina local
scp -r backups/ root@tu-servidor-contabo:/root/
scp backups/compueasys_backup_*.json root@tu-servidor-contabo:/root/
```

### Paso 2: Configurar Base de Datos
```sql
CREATE DATABASE compueasys_db;
CREATE USER compueasys_user WITH PASSWORD 'password_seguro';
GRANT ALL PRIVILEGES ON DATABASE compueasys_db TO compueasys_user;
```

### Paso 3: Clonar Repositorio (o subir código)
```bash
cd /var/www/
git clone tu-repositorio compueasys
cd compueasys
```

### Paso 4: Configurar Entorno
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 5: Configurar Variables de Entorno
```bash
nano .env
```
Agregar:
```
DB_NAME=compueasys_db
DB_USERNAME=compueasys_user
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=nueva_clave_secreta
DEBUG=False
```

### Paso 6: Migrar y Restaurar
```bash
python manage.py migrate
python manage.py loaddata /root/compueasys_backup_*.json
```

### Paso 7: Configurar Archivos Estáticos
```bash
python manage.py collectstatic --noinput
```

### Paso 8: Configurar Nginx + Gunicorn
```bash
# Instalar Gunicorn
pip install gunicorn

# Crear servicio systemd
sudo nano /etc/systemd/system/compueasys.service

# Configurar Nginx
sudo nano /etc/nginx/sites-available/compueasys
```

### Paso 9: SSL con Certbot
```bash
sudo certbot --nginx -d tu-dominio.com
```

---

## 💡 RECOMENDACIONES IMPORTANTES

### 1. Imágenes
**Decisión requerida:** ¿Migrar imágenes o mantenerlas en Render?

- **Mantener en Render (más fácil):**
  - No cambia nada en el código actual
  - Settings.py en desarrollo ya apunta a Render
  - Solo necesitas el backup de BD

- **Migrar a Contabo (más control):**
  - Descargar desde Render
  - Subir a Contabo
  - Cambiar `MEDIA_URL` en settings.py

### 2. Backups Automáticos en Contabo
```bash
# Configurar cron para backup diario
0 2 * * * pg_dump compueasys_db > /root/backups/db_$(date +\%Y\%m\%d).sql
```

### 3. Monitoreo
- Configurar logs: `/var/log/compueasys/`
- Monitoreo de recursos: htop, netdata
- Alertas de errores: Sentry (opcional)

### 4. Seguridad
- Firewall configurado (UFW)
- Solo puertos necesarios abiertos (80, 443, 22)
- SSH con clave pública (deshabilitar password)
- Actualizar regularmente: `apt update && apt upgrade`

---

## 🆘 TROUBLESHOOTING COMÚN

### Error: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Error: "Permission denied" en media
```bash
sudo chown -R www-data:www-data /var/www/compueasys/media/
sudo chmod -R 755 /var/www/compueasys/media/
```

### Error: "502 Bad Gateway"
```bash
sudo systemctl status compueasys
sudo journalctl -u compueasys -f
```

---

## 📞 SIGUIENTE PASO INMEDIATO

### Ejecuta este comando para generar la guía completa:
```bash
python prepare_contabo_migration.py
```

Esto generará:
1. Guía detallada de migración (Markdown)
2. Template de .env para Contabo
3. Script de deployment automatizado

---

## 📊 RESUMEN EJECUTIVO

✅ **Completado:**
- Backup blindado de 8,801 registros en 3 ubicaciones
- Scripts de backup y restauración
- Inventario completo de la base de datos

⏳ **Pendiente:**
- Decisión sobre migración de imágenes (354 archivos)
- Ejecución de `prepare_contabo_migration.py`
- Configuración del servidor Contabo
- Deployment y pruebas

🎯 **Tiempo estimado de migración:** 2-4 horas
(Dependiendo de la experiencia con servidores Linux y si se migran imágenes)

---

**Generado automáticamente:** 15/01/2026  
**Sistema:** CompuEasys Migration Tool v1.0
