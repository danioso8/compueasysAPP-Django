# 🔍 Diagnóstico y Solución - Pagos con Tarjeta Wompi

## 📋 Estado Actual del Sistema

### ✅ Componentes Implementados:
1. **WompiClient** (`core/wompi_client.py`) - Cliente Python para API Wompi
2. **create_wompi_transaction** (`core/views.py`) - Endpoint para crear transacciones
3. **checkout-wompi.js** - JavaScript del checkout con widget Wompi
4. **Widget Wompi** - Integrado en checkout.html

## 🐛 Problemas Comunes y Soluciones

### Problema 1: Widget no se abre o no carga
**Síntomas:**
- El botón de pago no responde
- Console muestra "WidgetCheckout no está definido"
- Widget se abre pero no muestra opciones de pago

**Soluciones:**
1. Verificar que el script de Wompi se carga correctamente:
```html
<script src="https://checkout.wompi.co/widget.js"></script>
```

2. Verificar public key en consola del navegador:
```javascript
console.log('Public key:', window.checkout_config?.wompi_public_key);
```

3. Asegurarse de que el widget se carga después de Wompi:
```javascript
// El código debe esperar a que Wompi esté disponible
if (typeof window.WidgetCheckout === 'undefined') {
    console.error('Widget de Wompi no cargado');
}
```

### Problema 2: Error de acceptance_token
**Síntomas:**
- Error: "Acceptance token no disponible"
- Response 500 al crear transacción

**Soluciones:**
1. Verificar que las credenciales de Wompi sean correctas en el Dashboard
2. Verificar endpoint del merchant:
```python
url = f"{self.base_url}/merchants/{self.public_key}"
```

3. Verificar response del endpoint:
```python
# Debe retornar: data.presigned_acceptance.acceptance_token
```

### Problema 3: Tarjeta rechazada o error en el pago
**Síntomas:**
- Widget se abre pero el pago falla
- Error: "Tarjeta rechazada" o "Transacción no autorizada"

**Soluciones para SANDBOX (pruebas):**
1. Usar tarjetas de prueba de Wompi:
```
Tarjeta APROBADA:
Número: 4242 4242 4242 4242
CVV: 123
Fecha: Cualquier fecha futura
Nombre: APPROVED

Tarjeta RECHAZADA:
Número: 4111 1111 1111 1111
CVV: 123
Fecha: Cualquier fecha futura
Nombre: DECLINED
```

2. Verificar que el environment sea "test":
```python
settings.WOMPI_ENVIRONMENT = 'test'  # No 'production'
```

3. Verificar que la URL base sea sandbox:
```python
settings.WOMPI_BASE_URL = 'https://sandbox.wompi.co/v1'
```

### Problema 4: Timeout o errores de conexión
**Síntomas:**
- Error: "Timeout de conexión"
- Error: "No se pudo conectar con Wompi"

**Soluciones:**
1. Verificar conectividad con Wompi:
```bash
curl -I https://sandbox.wompi.co/v1/merchants/pub_test_xxxxx
```

2. Aumentar timeout en WompiClient:
```python
response = requests.post(url, headers=self.headers, json=payload, timeout=60)
```

3. Verificar que no haya firewall bloqueando:
- Permitir conexiones salientes a wompi.co
- Permitir puerto 443 (HTTPS)

### Problema 5: Monto en centavos incorrecto
**Síntomas:**
- Error: "Monto inválido"
- Widget muestra monto incorrecto

**Solución:**
Verificar conversión a centavos:
```python
amount_in_cents = int(amount * 100)  # $50,000 COP = 5,000,000 centavos
```

## 🔧 Script de Diagnóstico Rápido

Ejecutar en consola del navegador (F12):
```javascript
// 1. Verificar que Wompi esté cargado
console.log('Wompi disponible:', typeof WidgetCheckout !== 'undefined');

// 2. Verificar configuración
console.log('Config:', window.checkout_config);

// 3. Verificar public key
console.log('Public key:', document.querySelector('meta[name="wompi-public-key"]')?.content);

// 4. Probar conexión con backend
fetch('/api/create-wompi-transaction/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({
        amount: 50000,
        customer_email: 'test@example.com'
    })
})
.then(r => r.json())
.then(data => console.log('Response:', data))
.catch(err => console.error('Error:', err));
```

## 🧪 Testing en Producción

Para probar pagos reales:

1. **Cambiar a credenciales de producción**:
```python
WOMPI_PUBLIC_KEY = 'pub_prod_xxxxx'  # Clave real de producción
WOMPI_PRIVATE_KEY = 'prv_prod_xxxxx'  # Clave privada de producción
WOMPI_ENVIRONMENT = 'production'
WOMPI_BASE_URL = 'https://production.wompi.co/v1'
```

2. **Usar tarjetas reales** (se cobrarán los montos)

3. **Verificar webhook**:
```python
# Configurar URL pública para recibir notificaciones de Wompi
WOMPI_WEBHOOK_URL = 'https://tu-dominio.com/api/wompi-webhook/'
```

## 📊 Monitoreo y Logs

### Logs importantes a revisar:
```bash
# En el servidor Django
python manage.py runserver

# Buscar en consola:
"🔵 WOMPI Transaction Request"
"✅ WOMPI Client creado"
"🔍 WOMPI Obteniendo acceptance token"
"🚀 WOMPI Response"
```

### Logs en navegador:
- Abrir DevTools (F12)
- Pestaña Console
- Buscar: "WOMPI", "Widget", "Transaction"

## ✅ Checklist de Verificación

Antes de reportar un problema, verificar:

- [ ] Credenciales de Wompi configuradas correctamente en Dashboard
- [ ] Script de Wompi se carga en checkout.html
- [ ] Public key visible en meta tag del HTML
- [ ] Endpoint `/api/create-wompi-transaction/` responde
- [ ] Acceptance token se obtiene correctamente
- [ ] Widget se abre al hacer clic en "Confirmar Pedido"
- [ ] Usando tarjetas de prueba correctas (si es sandbox)
- [ ] Environment configurado como "test" (para pruebas)
- [ ] No hay errores de CORS en consola
- [ ] Conexión a internet estable

## 🆘 Próximos Pasos si el Problema Persiste

1. **Capturar logs completos**:
   - Console del navegador (F12 → Console → Copiar todo)
   - Logs del servidor Django
   - Network tab (F12 → Network → Filtrar por "wompi")

2. **Verificar credenciales directamente**:
```bash
# Probar endpoint de Wompi directamente
curl -H "Authorization: Bearer prv_test_xxxxx" \
     https://sandbox.wompi.co/v1/merchants/pub_test_xxxxx
```

3. **Contactar soporte de Wompi**:
   - Email: soporte@wompi.com
   - Documentación: https://docs.wompi.co
   - Slack: Wompi Developers

## 📱 Información de Contacto

Si necesitas ayuda adicional, proporciona:
1. Console logs completos
2. Network tab del navegador (peticiones fallidas)
3. Logs del servidor Django
4. Environment actual (test/production)
5. Versión de Django y librerías
