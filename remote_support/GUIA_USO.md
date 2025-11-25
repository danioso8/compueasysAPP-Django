# 🛠️ CompuEasys Remote Support - Guía de Uso

## 📦 Archivos del Sistema

### Para el Cliente (Usuario final):
- **CompuEasys-SoporteRemoto.exe** (19 MB)
  - Ubicación web: `/media_files/upload/CompuEasys-SoporteRemoto.exe`
  - Se descarga desde el sitio web

### Para el Técnico (Tú):
- **CompuEasys-Servidor-Soporte.exe** (19 MB)
  - Ubicación: `D:\ESCRITORIO\CompueasysApp\remote_support\dist\`
  - Solo para uso interno

---

## 🚀 Cómo Usar el Sistema

### 🖥️ PASO 1: Iniciar Servidor (Técnico)

1. Ejecuta `CompuEasys-Servidor-Soporte.exe`
2. El servidor se iniciará en el puerto **9999**
3. Verás la ventana con el estado: "✅ Servidor activo"

### 👤 PASO 2: Cliente Se Conecta (Usuario)

1. El usuario descarga `CompuEasys-SoporteRemoto.exe` desde tu sitio web
2. Ejecuta el programa
3. Ingresa tu dirección IP (tú se la proporcionas):
   - **Red local**: Tu IP local (ej: `192.168.1.100`)
   - **Internet**: Tu IP pública o dominio
4. Hace clic en **"Conectar"**
5. Se genera un **código de 6 dígitos** (ej: `385621`)

### 🔐 PASO 3: Autorizar Conexión (Técnico)

1. En tu servidor verás aparecer el cliente en la lista
2. Selecciona el cliente
3. Haz clic en **"Conectar"**
4. Ingresa el código de 6 dígitos que te dio el cliente
5. ¡Conexión autorizada!

### 🎮 PASO 4: Control Remoto

Una vez conectado, puedes:

✅ **Ver la pantalla del cliente en tiempo real**
✅ **Hacer clic** en la pantalla remota (clic izquierdo y derecho)
✅ **Mover el mouse** sobre la pantalla remota
✅ **Ejecutar comandos** desde el panel de control
✅ **Chat/Log** de todas las acciones

---

## 🌐 Configuración de Red

### Conexión en Red Local (LAN)
- Ambos deben estar en la misma red WiFi/Ethernet
- El cliente usa tu IP local (ej: `192.168.1.100`)
- Ver tu IP: `ipconfig` en CMD (busca "IPv4")

### Conexión por Internet
1. **Abrir puerto 9999** en tu router (Port Forwarding)
   - Protocolo: TCP
   - Puerto externo: 9999
   - Puerto interno: 9999
   - IP destino: Tu PC
   
2. El cliente usa tu **IP pública**:
   - Ver IP pública: https://www.whatismyip.com
   - O usa un servicio como **No-IP** para dominio gratuito

---

## 🔒 Seguridad

✅ **Código único por sesión** - Cada conexión genera un código diferente
✅ **Autorización explícita** - El cliente debe compartir el código
✅ **Desconexión instantánea** - El cliente puede desconectarse en cualquier momento
✅ **Sin almacenamiento** - No se guardan datos de las sesiones

---

## 🐛 Solución de Problemas

### El cliente no puede conectarse:
1. Verifica que el servidor esté ejecutándose
2. Verifica la IP (debe ser correcta)
3. Verifica el firewall (debe permitir puerto 9999)
4. Si es por internet, verifica port forwarding

### No puedo controlar el mouse:
- El control de mouse está habilitado automáticamente
- Simplemente haz clic en la pantalla remota

### La pantalla se ve lenta:
- Es normal, actualiza cada 500ms
- Para mejorar, reduce la calidad de imagen en el código

---

## 📞 Funcionalidades Actuales

✅ Captura de pantalla en tiempo real
✅ Control de mouse (clic y movimiento)
✅ Ejecución de comandos remotos
✅ Múltiples clientes simultáneos
✅ Código de acceso seguro
✅ Panel de control con log
✅ Interfaz gráfica profesional

---

## 🎯 Ejemplo de Uso Completo

**Escenario**: Cliente tiene problema con su computadora

1. **Técnico**: Ejecuta `CompuEasys-Servidor-Soporte.exe`
2. **Técnico**: Le dice al cliente: "Descarga el programa desde www.compueasys.com"
3. **Cliente**: Descarga y ejecuta `CompuEasys-SoporteRemoto.exe`
4. **Técnico**: Le dice: "Conecta a 203.45.67.89" (su IP pública)
5. **Cliente**: Ingresa la IP y hace clic en "Conectar"
6. **Cliente**: Ve el código: `385621` y se lo dice al técnico
7. **Técnico**: Selecciona el cliente en la lista, clic en "Conectar"
8. **Técnico**: Ingresa `385621`
9. **✅ Conectado**: El técnico ya puede ver la pantalla y controlar el mouse
10. **Técnico**: Resuelve el problema haciendo clic en lo necesario
11. **Fin**: Ambos desconectan

---

## 💡 Consejos Pro

- **Mantén el servidor abierto** durante tus horas de soporte
- **Usa IP estática o dominio** para que sea siempre la misma
- **Prueba primero en red local** antes de usar por internet
- **Guarda ambos .exe** en una ubicación segura como respaldo

---

**CompuEasys Remote Support v1.0**
Sistema de soporte remoto personalizado con control total
