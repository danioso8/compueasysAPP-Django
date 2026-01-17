# Guía de Migración CompuEasys a Contabo

**Fecha de generación:** 2026-01-15 10:26:56

## 📋 Pre-requisitos

### En Contabo:
1. ✅ Servidor VPS/Cloud configurado
2. ✅ PostgreSQL instalado y configurado
3. ✅ Base de datos creada
4. ✅ Usuario de base de datos con permisos completos
5. ✅ Firewall configurado (puerto 5432 para PostgreSQL)
6. ✅ Nginx/Apache configurado para servir archivos estáticos

### Localmente:
1. ✅ Backups completados (carpeta `backups/`)
2. ✅ Imágenes descargadas (carpeta `media_backup/`)
3. ✅ PostgreSQL client tools instalados (opcional)

---

## 🗄️ Paso 1: Configurar Base de Datos en Contabo

### 1.1 Conectarse al servidor Contabo

```bash
ssh root@tu-servidor-contabo.com
```

### 1.2 Crear base de datos y usuario

```sql
-- Conectar a PostgreSQL
sudo -u postgres psql

-- Crear base de datos
CREATE DATABASE compueasys_db;

-- Crear usuario
CREATE USER compueasys_user WITH PASSWORD 'tu_password_seguro';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE compueasys_db TO compueasys_user;

-- Configurar permisos del esquema
\c compueasys_db
GRANT ALL ON SCHEMA public TO compueasys_user;

-- Salir
\q
```

### 1.3 Configurar acceso remoto (si es necesario)

Editar `/etc/postgresql/[version]/main/postgresql.conf`:
```
listen_addresses = '*'
```

Editar `/etc/postgresql/[version]/main/pg_hba.conf`:
```
host    compueasys_db    compueasys_user    0.0.0.0/0    md5
```

Reiniciar PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## 📤 Paso 2: Restaurar Base de Datos

### Opción A: Usando Django (Recomendado)

```bash
# 1. Copiar backup JSON al servidor Contabo
scp backups/compueasys_backup_*.json root@tu-servidor:/root/

# 2. En el servidor, instalar dependencias
cd /path/to/compueasys
pip install -r requirements.txt

# 3. Configurar variables de entorno
nano .env
# Agregar:
# DB_NAME=compueasys_db
# DB_USERNAME=compueasys_user
# DB_PASSWORD=tu_password_seguro
# DB_HOST=localhost
# DB_PORT=5432
# DJANGO_DEVELOPMENT=False

# 4. Aplicar migraciones
python manage.py migrate

# 5. Restaurar datos
python manage.py loaddata /root/compueasys_backup_*.json
```

### Opción B: Usando pg_restore (si tienes dump SQL)

```bash
# Si tienes archivo .sql
psql -h localhost -U compueasys_user -d compueasys_db -f backup.sql

# Si tienes archivo .dump
pg_restore -h localhost -U compueasys_user -d compueasys_db backup.dump
```

---

## 📁 Paso 3: Migrar Imágenes

### 3.1 Copiar imágenes al servidor

```bash
# Desde tu máquina local, copiar media_backup al servidor
scp -r media_backup/ root@tu-servidor:/var/www/compueasys/media/

# O usar rsync (más eficiente)
rsync -avz --progress media_backup/ root@tu-servidor:/var/www/compueasys/media/
```

### 3.2 Configurar permisos

```bash
# En el servidor Contabo
sudo chown -R www-data:www-data /var/www/compueasys/media/
sudo chmod -R 755 /var/www/compueasys/media/
```

---

## ⚙️ Paso 4: Configurar Django en Contabo

### 4.1 Actualizar settings.py

```python
# En producción (Contabo), asegurar:
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com', 'tu-ip-contabo']

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USERNAME'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Archivos estáticos
STATIC_ROOT = '/var/www/compueasys/staticfiles/'
MEDIA_ROOT = '/var/www/compueasys/media/'
MEDIA_URL = '/media/'
```

### 4.2 Recolectar archivos estáticos

```bash
python manage.py collectstatic --noinput
```

---

## 🌐 Paso 5: Configurar Servidor Web (Nginx)

### 5.1 Configuración Nginx

Crear `/etc/nginx/sites-available/compueasys`:

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Archivos estáticos
    location /static/ {
        alias /var/www/compueasys/staticfiles/;
        expires 30d;
    }

    # Archivos media
    location /media/ {
        alias /var/www/compueasys/media/;
        expires 30d;
    }

    # Django app (Gunicorn)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5.2 Activar sitio

```bash
sudo ln -s /etc/nginx/sites-available/compueasys /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🚀 Paso 6: Configurar Gunicorn

### 6.1 Instalar Gunicorn

```bash
pip install gunicorn
```

### 6.2 Crear servicio systemd

Crear `/etc/systemd/system/compueasys.service`:

```ini
[Unit]
Description=CompuEasys Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/compueasys
Environment="PATH=/var/www/compueasys/venv/bin"
ExecStart=/var/www/compueasys/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    AppCompueasys.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 6.3 Iniciar servicio

```bash
sudo systemctl daemon-reload
sudo systemctl start compueasys
sudo systemctl enable compueasys
sudo systemctl status compueasys
```

---

## 🔒 Paso 7: Configurar SSL (Certbot)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Auto-renovación (ya configurado)
sudo certbot renew --dry-run
```

---

## ✅ Paso 8: Verificación Post-Migración

### 8.1 Verificar base de datos

```bash
python manage.py shell
>>> from core.models import ProductStore
>>> ProductStore.objects.count()  # Debe mostrar 71
>>> from core.models import StoreVisit
>>> StoreVisit.objects.count()  # Debe mostrar ~4,698
```

### 8.2 Verificar imágenes

```bash
# Contar archivos de imagen
find /var/www/compueasys/media/images -type f | wc -l  # ~71 productos
find /var/www/compueasys/media/galeria -type f | wc -l  # ~258 galerías
find /var/www/compueasys/media/variant_images -type f | wc -l  # ~25 variantes
```

### 8.3 Probar sitio web

1. Abrir navegador: `https://tu-dominio.com`
2. Verificar que las imágenes cargan correctamente
3. Probar funcionalidades principales:
   - Ver productos
   - Agregar al carrito
   - Checkout
   - Dashboard admin

---

## 🔄 Paso 9: Configurar Backups Automáticos en Contabo

### 9.1 Script de backup automático

Crear `/root/scripts/backup_compueasys.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/root/backups/compueasys"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Crear directorio
mkdir -p $BACKUP_DIR

# Backup base de datos
pg_dump -U compueasys_user compueasys_db > $BACKUP_DIR/db_$TIMESTAMP.sql

# Backup media files (opcional - puede ser grande)
# tar -czf $BACKUP_DIR/media_$TIMESTAMP.tar.gz /var/www/compueasys/media/

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete

echo "Backup completado: $TIMESTAMP"
```

### 9.2 Configurar cron

```bash
# Editar crontab
crontab -e

# Agregar backup diario a las 2 AM
0 2 * * * /root/scripts/backup_compueasys.sh >> /var/log/backup_compueasys.log 2>&1
```

---

## 📊 Checklist de Migración

- [ ] Base de datos PostgreSQL creada en Contabo
- [ ] Usuario y permisos configurados
- [ ] Backup restaurado (8,801 registros)
- [ ] Imágenes copiadas al servidor (354 archivos)
- [ ] Variables de entorno configuradas
- [ ] Migraciones aplicadas
- [ ] Archivos estáticos recolectados
- [ ] Nginx configurado y funcionando
- [ ] Gunicorn configurado como servicio
- [ ] SSL/HTTPS configurado
- [ ] Sitio web funcionando correctamente
- [ ] Backups automáticos configurados
- [ ] DNS apuntando al nuevo servidor

---

## 🆘 Troubleshooting

### Error: "FATAL: password authentication failed"
```bash
# Verificar pg_hba.conf
sudo nano /etc/postgresql/[version]/main/pg_hba.conf
# Asegurar línea: host all all 0.0.0.0/0 md5
sudo systemctl restart postgresql
```

### Error: "Permission denied" en media files
```bash
sudo chown -R www-data:www-data /var/www/compueasys/media/
sudo chmod -R 755 /var/www/compueasys/media/
```

### Error: "502 Bad Gateway" en Nginx
```bash
# Verificar que Gunicorn está corriendo
sudo systemctl status compueasys
# Ver logs
sudo journalctl -u compueasys -f
```

---

## 📞 Información de Contacto

**Proyecto:** CompuEasys  
**Fecha de migración:** 2026-01-15  
**Generado por:** Sistema de migración automática

---

**Nota:** Esta guía fue generada automáticamente. Ajusta los valores según tu configuración específica de Contabo.
