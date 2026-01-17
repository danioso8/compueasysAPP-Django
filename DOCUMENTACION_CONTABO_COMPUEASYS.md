# 📘 DOCUMENTACIÓN COMPLETA - CompuEasysApp en Contabo VPS

**Fecha de Migración:** 15 de Enero de 2026  
**Proyecto:** CompuEasysApp - E-commerce de Tecnología  
**Estado:** ✅ Migración Completada y Operacional

---

## 🌐 INFORMACIÓN DEL SERVIDOR

### Datos del VPS Contabo
- **IP Pública:** `84.247.129.180`
- **Dominio:** `compueasys.com`
- **Proveedor:** Contabo VPS
- **Sistema Operativo:** Debian/Ubuntu Linux
- **Recursos:** (Verificar en panel Contabo)

### Acceso SSH
```bash
# Conexión SSH
ssh root@84.247.129.180

# Contraseña SSH
Miesposa0526
```

**Conexión desde Windows (PuTTY/plink):**
```bash
plink -batch -pw Miesposa0526 root@84.247.129.180 "comando"
pscp -pw Miesposa0526 archivo.txt root@84.247.129.180:/ruta/destino/
```

---

## 📂 ESTRUCTURA DE DIRECTORIOS

### Directorio Principal
```
/var/www/CompuEasysApp/
├── AppCompueasys/          # Configuración Django
│   ├── settings.py         # Configuración principal
│   ├── urls.py            # URLs del proyecto
│   └── wsgi.py            # WSGI para Gunicorn
├── core/                   # App principal (e-commerce)
│   ├── models.py
│   ├── views.py
│   ├── static/            # CSS, JS, imágenes estáticas
│   └── templates/         # Templates HTML
├── dashboard/             # App de administración
├── contable/              # App de contabilidad
├── media_files/           # Archivos subidos por usuarios
│   ├── images/           # Imágenes de productos (18 MB)
│   ├── galeria/          # Galería de productos (77 MB)
│   ├── variant_images/   # Imágenes de variantes (248 KB)
│   ├── upload/           # Otros archivos (45 MB)
│   └── videos/           # Videos (36 MB)
├── staticfiles/           # Archivos estáticos recopilados
├── venv/                  # Entorno virtual Python
├── backup_db_daily.sh     # Script de backup automático
├── restore_backup.sh      # Script de restauración
└── manage.py              # Comando Django

### Directorio de Backups
/var/backups/compueasys/
├── backup_compueasys_db_YYYYMMDD_HHMMSS.sql.gz  # Backups diarios
├── backup.log             # Log de backups
└── cron.log              # Log de ejecuciones cron
```

---

## 🗄️ BASE DE DATOS POSTGRESQL

### Credenciales de Base de Datos
```bash
Host: localhost
Puerto: 5432
Base de Datos: compueasys_db
Usuario: compueasys_user
Contraseña: CompuEasys2026!
```

### Conexión Manual
```bash
# Conectar a PostgreSQL
psql -U compueasys_user -h localhost compueasys_db

# Listar tablas
\dt

# Ver datos
SELECT * FROM dashboard_register_superuser;
SELECT * FROM core_productstore LIMIT 5;
```

### Estadísticas de Datos Migrados
- **Total de objetos:** 5,315
- **Productos:** 71
- **Categorías:** 15
- **Pedidos:** 90
- **Galerías de imágenes:** 258
- **Usuarios simples:** Múltiples
- **Superusuarios:** 2

---

## 👤 CREDENCIALES DE ACCESO

### Superusuarios Dashboard
```
Usuario 1:
  Username: admin
  Password: CompuEasys2026!
  Email: admin@compueasys.com
  
Usuario 2:
  Username: danioso8
  Password: Miesposa0526@
  Email: danioso8@compueasys.com
```

### URLs de Acceso
- **Sitio público:** http://compueasys.com
- **Login dashboard:** http://compueasys.com/login_user/
- **Dashboard:** http://compueasys.com/dashboard/dashboard_home/
- **Admin Django:** http://compueasys.com/admin/
- **Tienda:** http://compueasys.com/store/

---

## ⚙️ SERVICIOS Y CONFIGURACIÓN

### Servicios Activos

#### 1. Gunicorn (Servidor WSGI)
```bash
# Servicio systemd
Nombre: compueasys.service
Ubicación: /etc/systemd/system/compueasys.service
PID actual: 343522

# Comandos de gestión
systemctl status compueasys
systemctl start compueasys
systemctl stop compueasys
systemctl restart compueasys
systemctl enable compueasys   # Auto-inicio

# Ver logs
journalctl -u compueasys -f
journalctl -u compueasys --since "1 hour ago"
```

**Configuración Gunicorn:**
```ini
[Unit]
Description=CompuEasys Gunicorn daemon
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/CompuEasysApp
Environment="PATH=/var/www/CompuEasysApp/venv/bin"
ExecStart=/var/www/CompuEasysApp/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/CompuEasysApp/gunicorn.sock \
    AppCompueasys.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### 2. Nginx (Servidor Web)
```bash
# Servicio
systemctl status nginx
systemctl restart nginx
systemctl reload nginx  # Recargar configuración sin downtime

# Configuración
Ubicación: /etc/nginx/sites-available/compueasys
Enlace simbólico: /etc/nginx/sites-enabled/compueasys

# Logs
Error log: /var/log/nginx/error.log
Access log: /var/log/nginx/access.log

# Probar configuración
nginx -t
```

**Configuración Nginx:**
```nginx
server {
    listen 80;
    server_name compueasys.com www.compueasys.com 84.247.129.180;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/CompuEasysApp/staticfiles/;
    }

    location /media/ {
        alias /var/www/CompuEasysApp/media_files/;
    }

    location / {
        proxy_pass http://unix:/var/www/CompuEasysApp/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. PostgreSQL
```bash
# Servicio
systemctl status postgresql
systemctl restart postgresql

# Versión
psql --version

# Ubicación de datos
/var/lib/postgresql/
```

---

## 🔐 FIREWALL (UFW)

### Puertos Abiertos
```bash
# Ver estado
ufw status

# Puertos configurados
22/tcp     # SSH
80/tcp     # HTTP
443/tcp    # HTTPS (cuando se configure SSL)
8001/tcp   # Puerto alternativo (si se usa)
5432/tcp   # PostgreSQL (solo localhost recomendado)
```

### Comandos UFW
```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw disable
ufw status numbered
ufw delete [número]
```

---

## 📦 BACKUPS AUTOMÁTICOS

### Configuración de Backup Diario

**Frecuencia:** Diario a las 2:00 AM  
**Retención:** 7 días  
**Ubicación:** `/var/backups/compueasys/`  
**Formato:** SQL comprimido con gzip

**Cron Job Configurado:**
```bash
0 2 * * * /var/www/CompuEasysApp/backup_db_daily.sh >> /var/backups/compueasys/cron.log 2>&1
```

### Comandos de Backup

**Ejecutar backup manual:**
```bash
/var/www/CompuEasysApp/backup_db_daily.sh
```

**Ver backups disponibles:**
```bash
ls -lht /var/backups/compueasys/
```

**Ver log de backups:**
```bash
cat /var/backups/compueasys/backup.log
tail -f /var/backups/compueasys/backup.log
```

**Restaurar backup:**
```bash
/var/www/CompuEasysApp/restore_backup.sh
# Seguir instrucciones interactivas

# O especificar archivo directamente
/var/www/CompuEasysApp/restore_backup.sh /var/backups/compueasys/backup_compueasys_db_20260115_192156.sql.gz
```

**Backup manual con pg_dump:**
```bash
export PGPASSWORD='CompuEasys2026!'
pg_dump -U compueasys_user -h localhost compueasys_db > backup_manual.sql
gzip backup_manual.sql
```

---

## 🐍 ENTORNO PYTHON

### Entorno Virtual
```bash
# Activar entorno virtual
source /var/www/CompuEasysApp/venv/bin/activate

# Desactivar
deactivate

# Verificar versión Python
python --version
# Python 3.12.x

# Ver paquetes instalados
pip list
```

### Paquetes Principales
```
Django==4.2.24
gunicorn==23.0.0
psycopg2-binary
requests
Pillow
whitenoise
django-cors-headers
```

### Comandos Django Útiles
```bash
# Activar entorno primero
cd /var/www/CompuEasysApp
source venv/bin/activate

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Shell de Django
python manage.py shell

# Ver información del proyecto
python manage.py check
python manage.py showmigrations
```

---

## 📝 ARCHIVOS DE CONFIGURACIÓN IMPORTANTES

### 1. settings.py
**Ubicación:** `/var/www/CompuEasysApp/AppCompueasys/settings.py`

**Configuraciones clave:**
```python
DEBUG = False
ALLOWED_HOSTS = ['compueasys.com', 'www.compueasys.com', '84.247.129.180']
CSRF_TRUSTED_ORIGINS = ['http://compueasys.com', 'http://www.compueasys.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'compueasys_db',
        'USER': 'compueasys_user',
        'PASSWORD': 'CompuEasys2026!',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/CompuEasysApp/staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/CompuEasysApp/media_files'
```

### 2. Variables de Entorno (.env)
**Ubicación:** `/var/www/CompuEasysApp/.env` (si existe)

```env
SECRET_KEY=tu-secret-key-aqui
DJANGO_DEVELOPMENT=False
DB_NAME=compueasys_db
DB_USERNAME=compueasys_user
DB_PASSWORD=CompuEasys2026!
DB_HOST=localhost
DB_PORT=5432
BASE_URL=http://compueasys.com
```

---

## 🔧 MANTENIMIENTO Y TROUBLESHOOTING

### Reiniciar Todo el Sistema
```bash
# Reiniciar servicios uno por uno
systemctl restart compueasys
systemctl restart nginx
systemctl restart postgresql

# Reiniciar servidor completo (usar con precaución)
reboot
```

### Ver Logs de Errores
```bash
# Logs de Gunicorn/Django
journalctl -u compueasys -n 100
journalctl -u compueasys -f  # Seguir en tiempo real

# Logs de Nginx
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Logs de PostgreSQL
tail -f /var/log/postgresql/postgresql-*.log
```

### Problemas Comunes

**1. Error 502 Bad Gateway**
```bash
# Verificar que Gunicorn esté corriendo
systemctl status compueasys

# Verificar socket de Gunicorn
ls -la /var/www/CompuEasysApp/gunicorn.sock

# Reiniciar servicio
systemctl restart compueasys
```

**2. Archivos estáticos no cargan**
```bash
# Recopilar archivos estáticos
cd /var/www/CompuEasysApp
source venv/bin/activate
python manage.py collectstatic --noinput

# Verificar permisos
chmod -R 755 /var/www/CompuEasysApp/staticfiles/
chmod -R 755 /var/www/CompuEasysApp/media_files/
```

**3. Error de base de datos**
```bash
# Verificar que PostgreSQL esté corriendo
systemctl status postgresql

# Probar conexión
psql -U compueasys_user -h localhost compueasys_db

# Restaurar desde backup si es necesario
/var/www/CompuEasysApp/restore_backup.sh
```

**4. Espacio en disco**
```bash
# Ver espacio disponible
df -h

# Ver uso por directorio
du -sh /var/www/CompuEasysApp/*
du -sh /var/backups/compueasys/*

# Limpiar backups antiguos manualmente
find /var/backups/compueasys -name "*.sql.gz" -mtime +7 -delete
```

---

## 📊 MONITOREO Y ESTADÍSTICAS

### Uso de Recursos
```bash
# CPU y memoria
htop
top

# Espacio en disco
df -h
du -sh /var/www/CompuEasysApp/media_files/*

# Procesos de Gunicorn
ps aux | grep gunicorn

# Conexiones a base de datos
psql -U compueasys_user -h localhost compueasys_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### Estadísticas de Nginx
```bash
# Contar requests en última hora
tail -n 10000 /var/log/nginx/access.log | wc -l

# Ver IPs más frecuentes
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# Ver páginas más visitadas
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10
```

---

## 🔐 SEGURIDAD

### Recomendaciones de Seguridad Implementadas
- ✅ Firewall UFW configurado
- ✅ Solo puertos necesarios abiertos
- ✅ DEBUG=False en producción
- ✅ ALLOWED_HOSTS configurado correctamente
- ✅ Backups automáticos diarios
- ✅ PostgreSQL solo escucha en localhost

### Tareas de Seguridad Pendientes
- ⏳ Configurar SSL/HTTPS con Let's Encrypt
- ⏳ Configurar fail2ban para protección SSH
- ⏳ Implementar rotación de logs
- ⏳ Configurar monitoreo de intrusiones
- ⏳ Cambiar contraseñas predeterminadas regularmente

### Instalar SSL (Pendiente)
```bash
# Instalar Certbot
apt install certbot python3-certbot-nginx

# Obtener certificado
certbot --nginx -d compueasys.com -d www.compueasys.com

# Auto-renovación
certbot renew --dry-run
```

---

## 📞 INFORMACIÓN DE CONTACTO Y SOPORTE

### DNS y Dominio
**Proveedor DNS:** Hostinger (o el que uses)  
**Configuración A Record:**
```
compueasys.com     → 84.247.129.180
www.compueasys.com → 84.247.129.180
```

### Integración Wompi (Pagos)
```python
WOMPI_PUBLIC_KEY = 'pub_prod_DMT4tAPNSvnvuHiVmwjIoyVwaam8N3k7'
WOMPI_PRIVATE_KEY = 'prv_prod_1X63CjcbCvba86WpWJOuXiqJnKvtMgeT'
WOMPI_EVENTS_SECRET = 'prod_events_cmDhDmWt3heMjSm5uB9QMRHJO8HxJLvv'
WOMPI_INTEGRITY_SECRET = 'prod_integrity_YW2t43XJOhLUAOONX5u6U8AO5sEosmTT'
```

---

## 📝 NOTAS IMPORTANTES

### Cambios Realizados en la Migración
1. ✅ Migración completa desde Render a Contabo
2. ✅ Base de datos PostgreSQL restaurada (5,315 objetos)
3. ✅ 176 MB de archivos media transferidos
4. ✅ Archivos estáticos recopilados
5. ✅ Servicios systemd configurados
6. ✅ Nginx configurado como reverse proxy
7. ✅ DNS apuntado a nueva IP
8. ✅ Backups automáticos diarios configurados
9. ✅ Superusuarios creados y verificados
10. ✅ Navbar actualizado (sin carrito)

### Próximos Pasos Recomendados
1. 🔒 Configurar SSL/HTTPS con Let's Encrypt
2. 📧 Configurar email SMTP para notificaciones
3. 📊 Implementar monitoreo de servidor (Netdata, Grafana)
4. 🔐 Configurar fail2ban para seguridad SSH
5. 📝 Configurar rotación de logs
6. 💾 Configurar backup remoto (S3, BackBlaze, etc.)
7. 🚀 Optimizar rendimiento (Redis cache, CDN)

---

## 🆘 COMANDOS RÁPIDOS DE EMERGENCIA

```bash
# Ver si el sitio responde
curl -I http://compueasys.com

# Reiniciar todo
systemctl restart compueasys nginx postgresql

# Ver últimos errores
journalctl -u compueasys -n 50 --no-pager

# Backup manual urgente
/var/www/CompuEasysApp/backup_db_daily.sh

# Restaurar último backup
/var/www/CompuEasysApp/restore_backup.sh $(ls -t /var/backups/compueasys/backup_*.sql.gz | head -1)

# Ver procesos de la aplicación
ps aux | grep -E 'gunicorn|nginx|postgres'

# Limpiar caché de Django
cd /var/www/CompuEasysApp && source venv/bin/activate && python manage.py clear_cache

# Ver espacio en disco
df -h
```

---

## 📄 CHECKLIST DE VERIFICACIÓN

### Verificación Diaria
- [ ] Sitio web responde: http://compueasys.com
- [ ] Login funciona correctamente
- [ ] Dashboard accesible
- [ ] Imágenes de productos cargan
- [ ] Backup diario se ejecutó (revisar log)

### Verificación Semanal
- [ ] Logs de errores están limpios
- [ ] Espacio en disco suficiente
- [ ] Backups funcionando correctamente
- [ ] Servicios activos (gunicorn, nginx, postgresql)

### Verificación Mensual
- [ ] Actualizar paquetes del sistema
- [ ] Revisar y limpiar logs antiguos
- [ ] Verificar backups pueden restaurarse
- [ ] Revisar uso de recursos
- [ ] Cambiar contraseñas importantes

---

**Última actualización:** 15 de Enero de 2026  
**Próxima revisión:** 15 de Febrero de 2026  
**Versión del documento:** 1.0

---

## 💡 TIPS Y MEJORES PRÁCTICAS

1. **Siempre hacer backup antes de cambios importantes**
2. **Probar comandos en entorno de desarrollo primero**
3. **Documentar todos los cambios realizados**
4. **Mantener logs limpios y rotados**
5. **Monitorear uso de recursos regularmente**
6. **Actualizar Django y dependencias periódicamente**
7. **Usar entorno virtual siempre**
8. **No editar archivos directamente en producción sin backup**

---

🎉 **CompuEasysApp está ahora 100% operacional en Contabo VPS** 🎉
