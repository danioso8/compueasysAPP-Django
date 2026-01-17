# 🚀 GUÍA DE CONFIGURACIÓN AUTO-DEPLOYMENT

## 📋 Resumen
Esta configuración permite que CompuEasys se actualice automáticamente cuando hagas `git push` a GitHub.

---

## 🔧 PASOS DE CONFIGURACIÓN EN CONTABO

### 1️⃣ Conectar al servidor
```bash
ssh root@84.247.129.180
# Password: Miesposa0526
```

### 2️⃣ Subir archivos al servidor
```bash
# Desde tu PC (PowerShell)
cd D:\ESCRITORIO\CompueasysApp

# Subir scripts
scp webhook_deploy.py root@84.247.129.180:/var/www/CompuEasysApp/
scp deploy_auto.sh root@84.247.129.180:/var/www/CompuEasysApp/
```

### 3️⃣ Configurar permisos en el servidor
```bash
# En el servidor SSH
cd /var/www/CompuEasysApp

# Dar permisos de ejecución
chmod +x deploy_auto.sh
chmod +x webhook_deploy.py

# Crear directorio de logs
sudo mkdir -p /var/log/compueasys
sudo touch /var/log/compueasys_deploy.log
sudo chown www-data:www-data /var/log/compueasys_deploy.log
```

### 4️⃣ Instalar Flask para el webhook
```bash
# Activar entorno virtual
source /var/www/CompuEasysApp/venv/bin/activate

# Instalar Flask
pip install flask
```

### 5️⃣ Crear servicio systemd para el webhook
```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/compueasys-webhook.service
```

**Contenido del archivo:**
```ini
[Unit]
Description=CompuEasys GitHub Webhook Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/CompuEasysApp
Environment="PATH=/var/www/CompuEasysApp/venv/bin"
ExecStart=/var/www/CompuEasysApp/venv/bin/python /var/www/CompuEasysApp/webhook_deploy.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6️⃣ Activar el servicio webhook
```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio
sudo systemctl enable compueasys-webhook

# Iniciar servicio
sudo systemctl start compueasys-webhook

# Verificar estado
sudo systemctl status compueasys-webhook
```

### 7️⃣ Configurar Nginx para el webhook
```bash
# Editar configuración de Nginx
sudo nano /etc/nginx/sites-available/compueasys
```

**Agregar antes del último `}`:**
```nginx
    # Webhook endpoint
    location /webhook {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

```bash
# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 🌐 CONFIGURACIÓN EN GITHUB

### 1️⃣ Ir a tu repositorio en GitHub
```
https://github.com/danioso8/compueasysAPP-Django/settings/hooks
```

### 2️⃣ Crear nuevo Webhook
- Click en "Add webhook"

### 3️⃣ Configurar el webhook
```
Payload URL: http://compueasys.com/webhook
Content type: application/json
Secret: compueasys_webhook_secret_2026
```

### 4️⃣ Seleccionar eventos
- ☑️ Just the push event

### 5️⃣ Activar webhook
- ☑️ Active
- Click "Add webhook"

---

## ✅ VERIFICACIÓN

### Probar el webhook manualmente
```bash
# En tu PC
cd D:\ESCRITORIO\CompueasysApp

# Hacer un cambio pequeño
echo "# Auto-deployment test" >> README.md

# Commit y push
git add README.md
git commit -m "Test: Auto-deployment"
git push origin main
```

### Ver logs en el servidor
```bash
# En SSH Contabo
# Logs del webhook
sudo journalctl -u compueasys-webhook -f

# Logs de deployment
tail -f /var/log/compueasys_deploy.log

# Logs de la aplicación
sudo journalctl -u compueasys -f
```

---

## 🔍 DIAGNÓSTICO

### Si el webhook no funciona:

1. **Verificar que el servicio esté corriendo:**
```bash
sudo systemctl status compueasys-webhook
```

2. **Ver errores:**
```bash
sudo journalctl -u compueasys-webhook --no-pager -n 50
```

3. **Probar webhook manualmente:**
```bash
curl http://compueasys.com/webhook/health
# Debería responder: {"status":"ok","service":"webhook-deploy"}
```

4. **Verificar en GitHub:**
- Ve a Settings → Webhooks → Tu webhook
- Click en el webhook
- Ver "Recent Deliveries" para ver intentos y respuestas

---

## 🎯 ALTERNATIVA SIMPLE (Sin Webhook)

Si prefieres algo más simple, puedes usar un cron job que revise cambios cada 5 minutos:

```bash
# Editar crontab
crontab -e

# Agregar esta línea
*/5 * * * * cd /var/www/CompuEasysApp && git fetch && [ $(git rev-parse HEAD) != $(git rev-parse @{u}) ] && /var/www/CompuEasysApp/deploy_auto.sh >> /var/log/compueasys_deploy.log 2>&1
```

---

## 📝 NOTAS IMPORTANTES

1. **Seguridad:** El webhook solo acepta requests firmados con el secret token
2. **Ramas:** Solo hace deployment de cambios en `main`
3. **Backups:** El script de deployment automático NO hace backups (hazlo manual antes de cambios grandes)
4. **Tiempo:** El deployment tarda ~30-60 segundos
5. **Logs:** Siempre revisa los logs después de un deployment

---

## 🆘 COMANDOS ÚTILES

```bash
# Reiniciar webhook
sudo systemctl restart compueasys-webhook

# Ver logs en tiempo real
sudo journalctl -u compueasys-webhook -f

# Deshabilitar auto-deployment
sudo systemctl stop compueasys-webhook
sudo systemctl disable compueasys-webhook

# Deployment manual
cd /var/www/CompuEasysApp
git pull origin main
sudo systemctl restart compueasys
```

---

✅ **Una vez configurado, solo necesitas hacer `git push` y el sitio se actualizará automáticamente!**
