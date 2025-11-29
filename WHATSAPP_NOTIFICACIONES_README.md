# 📱 Sistema de Notificaciones WhatsApp Business

## ✅ Implementación Completada

Se ha implementado exitosamente el sistema de configuración de notificaciones de WhatsApp en el dashboard de CompuEasys.

## 🎯 Funcionalidades Implementadas

### 1. **Modelo de Configuración** (`WhatsAppConfig`)
- ✅ Número de WhatsApp del administrador
- ✅ Opciones de notificación configurables:
  - Nuevos pedidos
  - Cambios de estado de pedidos
  - Stock bajo (opcional)
- ✅ Plantilla de mensaje personalizable
- ✅ Sistema de activación/desactivación
- ✅ Patrón Singleton (solo una configuración)

### 2. **Interfaz de Configuración en Dashboard**
- ✅ Menú lateral: **Configuración de Tienda → Configurar WhatsApp**
- ✅ Formulario completo con validación
- ✅ Diseño profesional con Bootstrap
- ✅ Información de ayuda y ejemplos

## 📋 Cómo Usar

### Acceder a la Configuración

1. Inicia sesión en el dashboard como administrador
2. En el menú lateral, busca **"Configuración de Tienda"**
3. Haz clic en **"Configurar WhatsApp"** (ícono de WhatsApp)
4. Se abrirá el formulario de configuración

### Configurar el Número de WhatsApp

1. **Número de WhatsApp**: Ingresa tu número en formato internacional
   - Formato: `+57` seguido del número (sin espacios)
   - Ejemplo: `+573001234567`
   - ⚠️ **Importante**: Incluye el código de país (+57 para Colombia)

2. **Tipos de Notificaciones**: Activa las notificaciones que deseas recibir
   - ✅ **Nuevos Pedidos**: Te notifica cuando alguien hace un pedido
   - ✅ **Cambios de Estado**: Te avisa cuando actualizas el estado de un pedido
   - ⬜ **Stock Bajo**: Alerta cuando un producto tiene poco inventario (opcional)

3. **Plantilla de Mensaje**: Personaliza el mensaje que recibirás
   - Usa las variables disponibles:
     - `{order_id}` - Número del pedido
     - `{customer_name}` - Nombre del cliente
     - `{customer_phone}` - Teléfono del cliente
     - `{total}` - Total del pedido
     - `{payment_method}` - Método de pago
     - `{address}` - Dirección de entrega

4. **Activar Sistema**: Activa el switch para habilitar las notificaciones

5. Haz clic en **"Guardar Configuración"**

### Ejemplo de Plantilla de Mensaje

```
🛒 *Nuevo Pedido #{order_id}*

👤 Cliente: {customer_name}
📞 Teléfono: {customer_phone}
💰 Total: ${total}
📦 Método: {payment_method}
📍 Dirección: {address}

¡Revisa el dashboard para más detalles!
```

## 🔧 Archivos Modificados

### Backend (Django)

1. **`core/models.py`** - Línea 580+
   ```python
   class WhatsAppConfig(models.Model):
       admin_phone = models.CharField(max_length=20)
       notify_new_order = models.BooleanField(default=True)
       notify_status_change = models.BooleanField(default=True)
       notify_low_stock = models.BooleanField(default=False)
       message_template = models.TextField(...)
       is_active = models.BooleanField(default=True)
       
       @classmethod
       def get_config(cls):
           config, created = cls.objects.get_or_create(id=1, defaults={'admin_phone': '+57'})
           return config
   ```

2. **`dashboard/views.py`** - Línea 100+
   - Agregado manejador `view_param == 'whatsapp_config'`
   - Procesamiento de formulario POST
   - Context con `whatsapp_config`

3. **`core/migrations/0027_whatsappconfig.py`**
   - ✅ Migración aplicada exitosamente
   - Tabla `core_whatsappconfig` creada en base de datos

### Frontend (Templates)

1. **`dashboard/templates/dashboard/dashboard_home.html`**
   - **Línea 169**: Enlace en menú lateral "Configurar WhatsApp"
   - **Línea 1150+**: Formulario completo de configuración con:
     - Input para número de teléfono con validación
     - Switches para tipos de notificaciones
     - Textarea para plantilla de mensaje
     - Switch de activación/desactivación
     - Información de ayuda

## 🚀 Próximos Pasos (Pendientes)

### 1. Implementar Envío de Mensajes (Pendiente)

Para completar la funcionalidad, necesitas elegir e implementar un servicio de WhatsApp:

#### **Opción A: Twilio WhatsApp Business API** (Recomendado - Profesional)
- ✅ Oficial y confiable
- ✅ Soporte empresarial
- ❌ Requiere cuenta de pago
- 📚 Documentación: https://www.twilio.com/whatsapp

**Implementación:**
```python
# En requirements.txt agregar:
# twilio==8.x.x

# Crear core/whatsapp.py
from twilio.rest import Client
from core.models import WhatsAppConfig

def send_whatsapp_notification(order):
    config = WhatsAppConfig.get_config()
    
    if not config.is_active or not config.notify_new_order:
        return
    
    # Configurar Twilio (agregar a settings.py)
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    
    # Formatear mensaje
    message_text = config.message_template.format(
        order_id=order.id,
        customer_name=order.nombre,
        customer_phone=order.telefono,
        total=f"{order.total:,.0f}",
        payment_method=order.metodo_pago,
        address=f"{order.direccion}, {order.ciudad}"
    )
    
    # Enviar mensaje
    message = client.messages.create(
        from_='whatsapp:+14155238886',  # Número de Twilio
        body=message_text,
        to=f'whatsapp:{config.admin_phone}'
    )
    
    return message.sid
```

#### **Opción B: Baileys (WhatsApp Web API)** (Gratis - No Oficial)
- ✅ Gratis
- ✅ No requiere aprobación de WhatsApp
- ❌ No oficial (puede ser bloqueado)
- ❌ Requiere mantener sesión activa
- 📚 Documentación: https://github.com/WhiskeySockets/Baileys

**Implementación:**
```javascript
// Requiere un servidor Node.js separado
// Ver documentación de Baileys para implementación completa
```

#### **Opción C: WhatsApp Business API Oficial** (Empresarial)
- ✅ Solución oficial de Meta
- ✅ Mejor para empresas grandes
- ❌ Proceso de aprobación largo
- ❌ Requiere verificación de negocio
- 📚 Documentación: https://developers.facebook.com/docs/whatsapp

### 2. Integrar Notificaciones en Core Views

Una vez implementado el servicio de envío, agregar llamadas en:

**`core/views.py` - Función `pago_exitoso`** (después de crear el pedido):
```python
def pago_exitoso(request):
    # ... código existente ...
    
    # Después de crear el pedido
    new_order = Pedido(...)
    new_order.save()
    
    # AGREGAR AQUÍ: Enviar notificación WhatsApp
    try:
        from core.whatsapp import send_whatsapp_notification
        send_whatsapp_notification(new_order)
    except Exception as e:
        print(f"Error enviando WhatsApp: {e}")
        # No fallar el pedido por error en notificación
    
    # ... resto del código ...
```

**`dashboard/views.py` - Actualización de estado de pedido**:
```python
# Cuando se actualiza el estado de un pedido
if config.is_active and config.notify_status_change:
    message = f"📦 Pedido #{order.id} actualizado\n\n"
    message += f"Nuevo estado: {order.status}\n"
    message += f"Cliente: {order.nombre}"
    send_whatsapp_notification_custom(config.admin_phone, message)
```

### 3. Notificación de Stock Bajo (Opcional)

```python
# En core/signals.py o dashboard/views.py
from core.models import WhatsAppConfig, ProductStore

def check_low_stock():
    config = WhatsAppConfig.get_config()
    
    if not config.is_active or not config.notify_low_stock:
        return
    
    low_stock_products = ProductStore.objects.filter(stock__lte=5)
    
    if low_stock_products.exists():
        message = "⚠️ *Productos con Stock Bajo*\n\n"
        for product in low_stock_products[:5]:
            message += f"• {product.name}: {product.stock} unidades\n"
        
        send_whatsapp_notification_custom(config.admin_phone, message)
```

## 📊 Estado Actual

| Componente | Estado | Descripción |
|------------|--------|-------------|
| Modelo de Datos | ✅ Completado | WhatsAppConfig creado y migrado |
| Interfaz Dashboard | ✅ Completado | Formulario completo y funcional |
| Guardado de Config | ✅ Completado | POST handler implementado |
| Validación Frontend | ✅ Completado | Pattern validation en input |
| Envío de Mensajes | ⏳ Pendiente | Requiere servicio externo |
| Integración Pedidos | ⏳ Pendiente | Agregar llamadas después de implementar envío |

## 🔒 Seguridad

### Variables de Entorno Requeridas (cuando implementes envío)

Agregar al archivo `.env`:

```env
# Para Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886

# O para otro servicio
WHATSAPP_API_KEY=your_api_key
WHATSAPP_API_URL=https://api.example.com
```

## 📝 Notas Importantes

1. **Formato del Número**: Siempre usa formato internacional con `+` y código de país
2. **Testing**: Prueba primero con tu propio número antes de poner en producción
3. **Límites de API**: Verifica los límites de envío de tu proveedor de WhatsApp
4. **Privacidad**: Los datos de WhatsApp están protegidos en la base de datos
5. **Respaldo**: La configuración se mantiene aunque desactives las notificaciones

## 🆘 Troubleshooting

### El formulario no guarda
- Verifica que estés logueado como superuser
- Revisa los mensajes de error en la parte superior del formulario
- Comprueba que el formato del teléfono sea correcto (+57XXXXXXXXXX)

### No aparece la opción en el menú
- Verifica que tengas permisos de superuser
- Refresca la página del dashboard
- Verifica que `whatsapp_config` esté en el contexto de la vista

### Errores en consola
- Ejecuta `python manage.py check` para verificar configuración
- Revisa los logs de Django para más detalles

## 📞 Soporte

Para preguntas o problemas con la configuración, revisa:
- Este README
- La consola de Django para errores
- Los logs de aplicación

---

**Última actualización**: Implementación inicial completada
**Versión**: 1.0.0
**Estado**: ✅ Configuración lista - ⏳ Envío pendiente
