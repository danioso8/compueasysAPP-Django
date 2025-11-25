# 🚀 CompuEasys Remote Support - VERSIÓN CLOUD

## ☁️ Sistema de Soporte Remoto con Servidor Relay

**¡Sin necesidad de abrir puertos ni configurar router!**

Esta versión utiliza tu servidor Django en Render como intermediario (relay server), funcionando exactamente como AnyDesk o RustDesk, pero completamente personalizado para CompuEasys.

---

## 📦 Archivos del Sistema

### **Para el Cliente** (Usuario final):
- `CompuEasys-Cliente-Cloud.exe` (20 MB)
- Descarga desde: `/media_files/upload/CompuEasys-Cliente-Cloud.exe`
- Se conecta automáticamente a través de CompuEasys Cloud

### **Para el Técnico** (Tú):
- `CompuEasys-Servidor-Cloud.exe` (20 MB)
- Ubicación: `remote_support/dist/CompuEasys-Servidor-Cloud.exe`
- Panel de control profesional

---

## 🌟 Ventajas de la Versión Cloud

✅ **Sin configuración de red** - No necesitas abrir puertos
✅ **Sin router** - Funciona desde cualquier red
✅ **Sin IP pública** - El relay maneja todo
✅ **Conexión segura** - A través de HTTPS de Render
✅ **Código de acceso** - Sistema de seguridad de 6 dígitos
✅ **Control total** - Mouse, teclado, pantalla en tiempo real

---

## 🚀 Cómo Funciona

### Arquitectura:
```
Cliente → Render (relay) → Técnico
```

**Render actúa como puente** entre ambos, almacenando temporalmente:
- Códigos de acceso
- Imágenes de pantalla
- Comandos de control

---

## 📖 Guía de Uso Simplificada

### **1️⃣ Técnico (Tú)**

```bash
# Ejecuta el servidor
D:\ESCRITORIO\CompueasysApp\remote_support\dist\CompuEasys-Servidor-Cloud.exe
```

**El servidor se conectará automáticamente a:**
```
https://compueasysapp-django.onrender.com/api/relay
```

✅ Verás: "⚪ Sin conectar"

---

### **2️⃣ Cliente (Usuario)**

1. Descarga desde tu web: `CompuEasys-Cliente-Cloud.exe`
2. Ejecuta el programa
3. Hace clic en **"🔗 Conectar con Soporte"**
4. Ve un código de 6 dígitos: `385621` (ejemplo)
5. Te llama/escribe y te da el código

✅ Cliente ve: "🟢 Conectado - Esperando técnico"

---

### **3️⃣ Técnico Autoriza**

1. En tu servidor, clic en **"🔗 Conectar con Código"**
2. Ingresa el código: `385621`
3. ✅ **¡Conectado!**

Ahora puedes:
- 👁️ Ver la pantalla del cliente en tiempo real
- 🖱️ Hacer clic (izquierdo/derecho) en la pantalla
- ⌨️ Enviar texto desde el botón "Enviar Texto"
- 🔴 Desconectar cuando termines

---

## 🔧 Configuración del Servidor Django

### **Endpoints del Relay** (ya configurados):

```
/api/relay/register_client/       # Cliente registra sesión
/api/relay/connect_technician/    # Técnico se conecta con código
/api/relay/send_message/          # Enviar datos (pantalla/comandos)
/api/relay/receive_messages/      # Recibir datos pendientes
/api/relay/disconnect/            # Cerrar sesión
/api/relay/list_sessions/         # Ver clientes esperando
```

### **Archivo creado**: `core/relay_views.py`
- Maneja todas las conexiones
- Almacena sesiones en memoria
- Auto-limpia sesiones antiguas (>24h)

---

## 🔒 Seguridad

✅ **Código único** - Cada sesión genera código diferente
✅ **Autorización obligatoria** - El técnico debe ingresar el código
✅ **HTTPS** - Toda comunicación cifrada por Render
✅ **Sin almacenamiento** - Datos en memoria, no en base de datos
✅ **Desconexión instantánea** - Cliente puede cerrar en cualquier momento

---

## 📊 Flujo de Datos

### **1. Registro de Cliente:**
```json
POST /api/relay/register_client/
{
  "client_id": "PC-CLIENTE-123_1732563245",
  "access_code": "385621"
}
→ Respuesta: {"success": true, "session_id": "session_..."}
```

### **2. Conexión de Técnico:**
```json
POST /api/relay/connect_technician/
{
  "access_code": "385621"
}
→ Respuesta: {"success": true, "session_id": "session_..."}
```

### **3. Envío de Pantalla:**
```json
POST /api/relay/send_message/
{
  "session_id": "session_...",
  "sender": "client",
  "message": {
    "type": "screen",
    "data": "base64_image_data..."
  }
}
```

### **4. Recepción de Comandos:**
```json
POST /api/relay/receive_messages/
{
  "session_id": "session_...",
  "receiver": "client"
}
→ Respuesta: {
  "success": true,
  "messages": [
    {
      "sender": "technician",
      "message": {
        "action": "mouse_click",
        "x": 400,
        "y": 300,
        "button": "left"
      }
    }
  ]
}
```

---

## 🎯 Comparación: Versión Original vs Cloud

| Característica | Original | Cloud ☁️ |
|---------------|----------|----------|
| Configurar router | ✅ Sí | ❌ No |
| Abrir puertos | ✅ Sí (9999) | ❌ No |
| IP pública necesaria | ✅ Sí | ❌ No |
| Funciona en cualquier red | ❌ No | ✅ Sí |
| Detrás de firewall | ❌ No | ✅ Sí |
| Velocidad | ⚡ Muy rápida | 🔄 Buena |
| Escalabilidad | ❌ 1 a 1 | ✅ Múltiples clientes |
| Costo adicional | ❌ No | ❌ No (usa Render gratis) |

---

## 💻 Requisitos Técnicos

### **Cliente:**
- Windows 7/10/11
- 50 MB espacio libre
- Conexión a internet

### **Servidor (Técnico):**
- Windows 7/10/11
- 50 MB espacio libre
- Conexión a internet

### **Servidor Django (Render):**
- Ya desplegado en: `compueasysapp-django.onrender.com`
- Endpoints `/api/relay/` activos
- Sin necesidad de base de datos (usa memoria)

---

## 🐛 Solución de Problemas

### **Error: "No se puede conectar al servidor"**
✅ Verifica que Render esté activo:
```bash
curl https://compueasysapp-django.onrender.com/api/relay/list_sessions/
```

### **Cliente conectado pero técnico no puede unirse**
✅ Verifica el código de 6 dígitos (distingue mayúsculas)
✅ Asegúrate que el cliente aún esté conectado

### **Pantalla no se actualiza**
✅ Es normal, actualiza cada 500ms
✅ Verifica la conexión a internet de ambos

---

## 📈 Próximas Mejoras

🔄 Chat en tiempo real
📁 Transferencia de archivos
📹 Grabación de sesiones
📊 Estadísticas de uso
🔔 Notificaciones push
🌐 Soporte multi-idioma

---

## 🚀 Deploy en Producción

### **Ya está listo!** Solo necesitas:

1. ✅ Servidor Django desplegado en Render (HECHO)
2. ✅ Endpoints `/api/relay/` configurados (HECHO)
3. ✅ Ejecutables compilados (HECHO)
4. ✅ Enlace de descarga en web (HECHO)

### **Para actualizar:**

```bash
# 1. Modificar código si es necesario
cd D:\ESCRITORIO\CompueasysApp\remote_support

# 2. Recompilar cliente
D:/ESCRITORIO/CompueasysApp/venv_new/Scripts/python.exe -m PyInstaller --onefile --windowed --name="CompuEasys-Cliente-Cloud" --clean client_relay.py

# 3. Copiar a web
Copy-Item dist\CompuEasys-Cliente-Cloud.exe -Destination ..\media_files\upload\ -Force

# 4. Hacer git push (Render se actualiza solo)
git add .
git commit -m "Update relay server"
git push origin main
```

---

## 📞 URLs Importantes

- **Servidor Relay**: https://compueasysapp-django.onrender.com/api/relay/
- **Lista de sesiones**: https://compueasysapp-django.onrender.com/api/relay/list_sessions/
- **Descarga cliente**: https://tudominio.com/media_files/upload/CompuEasys-Cliente-Cloud.exe

---

## ✅ Checklist de Validación

Antes de usar en producción, verifica:

- [ ] Render está desplegado y activo
- [ ] Endpoints del relay responden correctamente
- [ ] Cliente se puede descargar desde la web
- [ ] Cliente se conecta y genera código
- [ ] Servidor técnico se conecta con código
- [ ] Pantalla se visualiza en tiempo real
- [ ] Clics de mouse funcionan
- [ ] Envío de texto funciona
- [ ] Desconexión funciona correctamente

---

**🛠️ CompuEasys Remote Support - Cloud Edition**
*Sistema profesional de soporte remoto sin complicaciones*

Versión: 2.0 Cloud
Fecha: Noviembre 2025
