# 💳 Guía de Configuración de Stripe para CompuEasys

## 📋 Resumen
Esta guía te ayudará a configurar Stripe como proveedor de pagos para tu aplicación CompuEasys, permitiendo procesar pagos con tarjetas de crédito y débito de forma segura.

## 🎯 Características Implementadas
- ✅ Pagos con tarjeta de crédito y débito
- ✅ Interfaz moderna con Stripe Elements
- ✅ Validación en tiempo real
- ✅ Webhooks para confirmar pagos
- ✅ Integración completa con códigos de descuento
- ✅ Soporte para pesos colombianos (COP)
- ✅ Modo de prueba y producción

## 🚀 Paso 1: Crear Cuenta de Stripe

### 1.1 Registrarse en Stripe
1. Ve a [https://stripe.com/](https://stripe.com/)
2. Haz clic en "Start Now" o "Comenzar"
3. Crea tu cuenta con email y contraseña
4. Verifica tu email

### 1.2 Activar tu cuenta
1. Completa la información de tu negocio
2. Agrega información bancaria para recibir pagos
3. Verifica tu identidad (puede tomar 1-2 días)

## 🔑 Paso 2: Obtener Claves API

### 2.1 Claves de Prueba (para desarrollo)
1. Ve a [https://dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)
2. Copia las siguientes claves:
   - **Publishable key**: `pk_test_51...` 
   - **Secret key**: `sk_test_51...` (¡mantén esta privada!)

### 2.2 Claves de Producción (para producción)
1. Ve a [https://dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
2. Copia las claves de producción:
   - **Publishable key**: `pk_live_51...`
   - **Secret key**: `sk_live_51...`

## ⚙️ Paso 3: Configurar Variables de Entorno

### 3.1 Actualizar archivo .env
```bash
# ===== STRIPE CONFIGURATION =====
# Claves de PRUEBA (para desarrollo)
STRIPE_PUBLISHABLE_KEY=pk_test_51ABC123...
STRIPE_SECRET_KEY=sk_test_51XYZ789...

# Para producción, cambia por las claves live:
# STRIPE_PUBLISHABLE_KEY=pk_live_51...
# STRIPE_SECRET_KEY=sk_live_51...

# Webhook secret (configurar más adelante)
STRIPE_WEBHOOK_SECRET=whsec_1234...
```

### 3.2 Variables ya configuradas automáticamente
```python
# En settings.py - Ya configurado ✅
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY') 
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

PAYMENT_SETTINGS = {
    'currency': 'COP',  # Pesos colombianos
    'payment_methods': ['card'],
    'automatic_tax': False,
    'shipping_calculation': True,
}
```

## 🔔 Paso 4: Configurar Webhooks

### 4.1 ¿Qué son los Webhooks?
Los webhooks permiten a Stripe notificar a tu aplicación cuando se completa un pago exitosamente.

### 4.2 Crear Webhook en Stripe
1. Ve a [https://dashboard.stripe.com/test/webhooks](https://dashboard.stripe.com/test/webhooks)
2. Haz clic en "Add endpoint"
3. **Endpoint URL**: `https://tu-dominio.com/api/stripe-webhook/`
   - Para local: `http://localhost:8000/api/stripe-webhook/`
   - Para producción: `https://tu-app.onrender.com/api/stripe-webhook/`
4. **Events to send**: Selecciona estos eventos:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Haz clic en "Add endpoint"
6. Copia el **Signing secret** (empieza con `whsec_`)
7. Agrégalo a tu `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef...
   ```

## 💳 Paso 5: Tarjetas de Prueba

### 5.1 Tarjetas que Funcionan (Modo Test)
```
Visa exitosa: 4242 4242 4242 4242
Mastercard exitosa: 5555 5555 5555 4444
Visa declinada: 4000 0000 0000 0002
Mastercard declinada: 4000 0000 0000 9995

# Cualquier fecha futura y CVC funcionan
Fecha: 12/26
CVC: 123
```

### 5.2 Tarjetas Específicas para Colombia
```
# Visa Colombia
4000 0056 0000 0008

# Tarjeta que requiere autenticación 3D Secure
4000 0027 6000 0016
```

## 🧪 Paso 6: Pruebas

### 6.1 Modo de Prueba
- ✅ Usa claves `pk_test_` y `sk_test_`
- ✅ Usa tarjetas de prueba
- ✅ No se procesan pagos reales
- ✅ Perfecto para desarrollo

### 6.2 Flujo de Prueba Completo
1. **Agregar productos** al carrito
2. **Ir a checkout** y completar información
3. **Seleccionar "Tarjeta de Crédito/Débito"**
4. **Ingresar tarjeta de prueba**: `4242 4242 4242 4242`
5. **Aplicar código de descuento** (opcional): `COMPUEASYS10`
6. **Confirmar pedido**
7. **Verificar** que aparece "Pago exitoso"
8. **Verificar** webhook en dashboard de Stripe
9. **Verificar** que el pedido se guardó con `PaymentID`

## 📊 Paso 7: Monitoreo

### 7.1 Dashboard de Stripe
- **Pagos**: [https://dashboard.stripe.com/test/payments](https://dashboard.stripe.com/test/payments)
- **Customers**: [https://dashboard.stripe.com/test/customers](https://dashboard.stripe.com/test/customers)
- **Webhooks**: [https://dashboard.stripe.com/test/webhooks](https://dashboard.stripe.com/test/webhooks)
- **Logs**: [https://dashboard.stripe.com/test/logs](https://dashboard.stripe.com/test/logs)

### 7.2 Logs de Django
```python
# Los logs aparecen en la consola de Django
PaymentIntent pi_1ABC123 succeeded!
Pedido 15 marcado como pagado
```

## 🚀 Paso 8: Producción

### 8.1 Checklist antes de ir a producción
- [ ] Cuenta de Stripe activada y verificada
- [ ] Información bancaria agregada
- [ ] Cambiar claves test por claves live en `.env`
- [ ] Webhook configurado con URL de producción
- [ ] Probar con tarjeta real (monto pequeño)
- [ ] Monitorear primeros pagos

### 8.2 Variables para Producción
```bash
# En .env para producción
STRIPE_PUBLISHABLE_KEY=pk_live_51...
STRIPE_SECRET_KEY=sk_live_51...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 8.3 Webhook para Producción
```
URL: https://tu-app.onrender.com/api/stripe-webhook/
Events: payment_intent.succeeded, payment_intent.payment_failed
```

## 💡 Funciones Implementadas

### 💳 Frontend (checkout.html)
- **Stripe Elements**: Formulario seguro de tarjeta
- **Validación en tiempo real**: Números de tarjeta, fechas, CVC
- **UX moderna**: Animaciones, feedback visual
- **Códigos de descuento**: Integración completa
- **Responsive**: Funciona en móvil y desktop

### 🔧 Backend (views.py)
- **create_payment_intent**: Crea PaymentIntent en Stripe
- **stripe_webhook**: Maneja confirmaciones de pago
- **pago_exitoso**: Procesa pedidos con payment_intent_id
- **Integración completa**: Descuentos + Stripe + WhatsApp + Email

### 📁 Archivos Modificados
```
✅ requirements.txt - Agregado stripe==7.9.0
✅ settings.py - Configuración Stripe
✅ checkout.html - UI moderna con Stripe Elements  
✅ checkout.css - Estilos para formulario de tarjeta
✅ checkout.js - JavaScript para Stripe integration
✅ core/views.py - Vistas de Stripe y payment handling
✅ core/urls.py - URLs para endpoints de Stripe
✅ .env.example - Variables de entorno de Stripe
```

## 🛡️ Seguridad

### 🔐 Características de Seguridad
- **PCI DSS Compliant**: Stripe maneja datos sensibles
- **Encriptación SSL**: Toda comunicación encriptada
- **No almacenamos datos**: Los datos de tarjeta nunca tocan tu servidor
- **Webhook signatures**: Verificación de autenticidad
- **Environment variables**: Claves privadas protegidas

### 🚨 Mejores Prácticas
- ✅ NUNCA subas claves privadas a GitHub
- ✅ Usa claves test para desarrollo
- ✅ Verifica webhooks con signature
- ✅ Monitorea pagos en dashboard
- ✅ Mantén logs de errores

## 🎉 ¡Listo!

Tu sistema de pagos está completamente configurado y listo para usar. Los usuarios ahora pueden:

1. **Pagar contra entrega** (como antes)
2. **Pagar con tarjeta** (nuevo) - Visa, Mastercard
3. **Usar códigos de descuento** en ambos métodos
4. **Recibir confirmaciones** por email y WhatsApp
5. **Disfrutar de UX moderna** y segura

## 📞 Soporte

- **Documentación Stripe**: [https://stripe.com/docs](https://stripe.com/docs)
- **Stripe Support**: [https://support.stripe.com](https://support.stripe.com)
- **Dashboard**: [https://dashboard.stripe.com](https://dashboard.stripe.com)

---

¡Tu e-commerce ahora acepta pagos con tarjeta de forma profesional! 🚀💳