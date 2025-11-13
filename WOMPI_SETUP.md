# 💳 Guía de Configuración de Wompi para CompuEasys

## 📋 Resumen
Esta guía te ayudará a configurar Wompi como proveedor de pagos para tu aplicación CompuEasys, permitiendo procesar pagos con tarjetas de crédito y débito en Colombia de forma segura.

## 🎯 Características de Wompi
- ✅ Proveedor de pagos 100% colombiano
- ✅ Tarjetas de crédito y débito (Visa, Mastercard)
- ✅ PSE (Pagos Seguros en Línea)
- ✅ Corresponsalías Bancarias
- ✅ Integración moderna con widgets
- ✅ Comisiones competitivas en Colombia
- ✅ Soporte nativo en pesos colombianos (COP)

## 🚀 Paso 1: Crear Cuenta en Wompi

### 1.1 Registrarse en Wompi
1. Ve a [https://comercios.wompi.co/](https://comercios.wompi.co/)
2. Haz clic en "Crear cuenta"
3. Completa la información de tu empresa/negocio
4. Verifica tu email

### 1.2 Activar tu cuenta
1. Sube la documentación requerida:
   - Cédula o RUT
   - Cámara de comercio (si aplica)
   - Estados financieros
2. Espera la verificación (1-3 días hábiles)
3. Recibe confirmación de activación

## 🔑 Paso 2: Obtener Claves API

### 2.1 Acceder al Dashboard
1. Ve a [https://comercios.wompi.co/](https://comercios.wompi.co/)
2. Inicia sesión con tu cuenta
3. Ve a la sección "Desarrolladores" → "Configuración API"

### 2.2 Claves de Prueba (Sandbox)
```
Public Key Test: pub_test_abc123...
Private Key Test: prv_test_xyz789...
```

### 2.3 Claves de Producción (Live)
```
Public Key Live: pub_prod_abc123...
Private Key Live: prv_prod_xyz789...
```

## ⚙️ Paso 3: Configurar Variables de Entorno

### 3.1 Actualizar archivo .env
```bash
# ===== WOMPI CONFIGURATION =====
# Claves de PRUEBA (para desarrollo)
WOMPI_PUBLIC_KEY=pub_test_AcFLWqPJHeGBBFxy3nyjJT25WjWgLKVa
WOMPI_PRIVATE_KEY=prv_test_AsyPjPPqCzvs5tJGg5RqFvKvATrbXE7N
WOMPI_ENVIRONMENT=test_events_Y5xgnMtxikUVSnqAIIErboQwcRSD0gvW


# Para producción, cambiar por:
# WOMPI_PUBLIC_KEY=pub_prod_abc123...
# WOMPI_PRIVATE_KEY=prv_prod_xyz789...
# WOMPI_ENVIRONMENT=prod

# URL base de la API
WOMPI_BASE_URL=https://sandbox.wompi.co/v1
# Para producción: https://production.wompi.co/v1
```

## 📦 Paso 4: Instalación de Dependencias

### 4.1 Instalar SDK de Wompi
```bash
pip install requests  # Para hacer peticiones HTTP
```

## 🔧 Paso 5: Configuración Backend

### 5.1 Settings.py
```python
# En AppCompueasys/settings.py
import os

# Configuración Wompi
WOMPI_PUBLIC_KEY = os.getenv('WOMPI_PUBLIC_KEY')
WOMPI_PRIVATE_KEY = os.getenv('WOMPI_PRIVATE_KEY')
WOMPI_ENVIRONMENT = os.getenv('WOMPI_ENVIRONMENT', 'test')
WOMPI_BASE_URL = os.getenv('WOMPI_BASE_URL', 'https://sandbox.wompi.co/v1')

PAYMENT_SETTINGS = {
    'currency': 'COP',
    'payment_methods': ['CARD', 'PSE'],
    'provider': 'wompi',
    'automatic_tax': False,
    'shipping_calculation': True,
}
```

### 5.2 Wompi Helper Class
```python
# En core/wompi_client.py (nuevo archivo)
import requests
from django.conf import settings
import json

class WompiClient:
    def __init__(self):
        self.private_key = settings.WOMPI_PRIVATE_KEY
        self.public_key = settings.WOMPI_PUBLIC_KEY
        self.base_url = settings.WOMPI_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.private_key}',
            'Content-Type': 'application/json'
        }
    
    def create_transaction(self, amount_in_cents, currency, reference, customer_email):
        """Crear una transacción en Wompi"""
        url = f"{self.base_url}/transactions"
        
        payload = {
            "amount_in_cents": int(amount_in_cents),
            "currency": currency,
            "customer_email": customer_email,
            "reference": reference,
            "payment_method": {
                "type": "CARD",
                "installments": 1
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def get_transaction(self, transaction_id):
        """Obtener información de una transacción"""
        url = f"{self.base_url}/transactions/{transaction_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
```

### 5.3 Vistas actualizadas
```python
# En core/views.py - Nuevas vistas para Wompi

@csrf_exempt
@require_http_methods(["POST"])
def create_wompi_transaction(request):
    """Crear transacción de pago en Wompi"""
    try:
        data = json.loads(request.body)
        amount = data.get('amount')  # En centavos
        email = data.get('email')
        reference = f"compueasys-{data.get('reference', int(time.time()))}"
        
        wompi_client = WompiClient()
        transaction = wompi_client.create_transaction(
            amount_in_cents=amount,
            currency='COP',
            reference=reference,
            customer_email=email
        )
        
        return JsonResponse({
            'success': True,
            'transaction_id': transaction.get('data', {}).get('id'),
            'presigned_acceptance': transaction.get('data', {}).get('presigned_acceptance'),
            'transaction': transaction
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt 
@require_http_methods(["POST"])
def wompi_webhook(request):
    """Webhook para confirmaciones de Wompi"""
    try:
        data = json.loads(request.body)
        
        # Verificar que es un evento de transacción
        if data.get('event') == 'transaction.updated':
            transaction_data = data.get('data', {}).get('transaction', {})
            transaction_id = transaction_data.get('id')
            status = transaction_data.get('status')
            reference = transaction_data.get('reference')
            
            if status == 'APPROVED':
                # Buscar el pedido por referencia
                try:
                    # Extraer ID del pedido de la referencia
                    pedido_id = reference.replace('compueasys-', '')
                    pedido = Pedido.objects.get(id=pedido_id)
                    pedido.status = 'pagado'
                    pedido.transaction_id = transaction_id
                    pedido.save()
                    
                    print(f"Pedido {pedido_id} marcado como pagado con transacción {transaction_id}")
                    
                except Pedido.DoesNotExist:
                    print(f"Pedido no encontrado para referencia: {reference}")
            
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'ignored'})
        
    except Exception as e:
        print(f"Error en webhook de Wompi: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
```

## 🌐 Paso 6: Frontend Integration

### 6.1 JavaScript para Wompi Widget
```javascript
// En checkout.js - Reemplazar funcionalidad de Stripe

// Configuración de Wompi
const wompiConfig = {
    currency: 'COP',
    amountInCents: 0, // Se calculará dinámicamente
    reference: '',
    publicKey: document.querySelector('[name=wompi_public_key]').value,
    redirectUrl: window.location.origin + '/pago_exitoso/'
};

// Función para inicializar Wompi Widget
function initializeWompiWidget() {
    const checkout = new WidgetCheckout({
        currency: wompiConfig.currency,
        amountInCents: wompiConfig.amountInCents,
        reference: wompiConfig.reference,
        publicKey: wompiConfig.publicKey,
        redirectUrl: wompiConfig.redirectUrl,
        taxInCents: 0, // Opcional
        customerData: {
            email: document.getElementById('email').value,
            fullName: document.getElementById('nombre').value,
            phoneNumber: document.getElementById('telefono').value,
        }
    });
    
    checkout.open(function (result) {
        const transaction = result.transaction;
        console.log('Transacción:', transaction);
        
        if (transaction.status === 'APPROVED') {
            // Procesar pago exitoso
            window.location.href = `/pago_exitoso/?transaction_id=${transaction.id}`;
        } else {
            showToast('El pago no pudo ser procesado', 'error');
        }
    });
}

// Event listener para el botón de pago
document.getElementById('confirm-payment').addEventListener('click', function() {
    const paymentMethod = document.querySelector('input[name="metodo_pago"]:checked').value;
    
    if (paymentMethod === 'tarjeta') {
        // Calcular monto en centavos
        const totalElement = document.querySelector('.total-amount');
        const total = parseFloat(totalElement.textContent.replace(/[^0-9]/g, ''));
        const amountInCents = total * 100;
        
        // Configurar Wompi
        wompiConfig.amountInCents = amountInCents;
        wompiConfig.reference = `compueasys-${Date.now()}`;
        
        // Abrir widget de Wompi
        initializeWompiWidget();
    } else {
        // Procesar como contra entrega (código existente)
        processStandardPayment();
    }
});
```

### 6.2 Actualizar Template checkout.html
```html
<!-- Agregar script de Wompi -->
<script src="https://checkout.wompi.co/widget.js"></script>

<!-- Variable oculta con public key -->
<input type="hidden" name="wompi_public_key" value="{{ wompi_public_key }}">

<!-- Sección de métodos de pago -->
<div class="payment-methods">
    <div class="payment-option">
        <input type="radio" id="contraentrega" name="metodo_pago" value="contraentrega" checked>
        <label for="contraentrega">
            <i class="fas fa-hand-holding-usd"></i>
            Pago contra entrega
        </label>
    </div>
    
    <div class="payment-option">
        <input type="radio" id="tarjeta" name="metodo_pago" value="tarjeta">
        <label for="tarjeta">
            <i class="fas fa-credit-card"></i>
            Tarjeta de crédito/débito (Wompi)
        </label>
    </div>
    
    <div class="payment-option">
        <input type="radio" id="pse" name="metodo_pago" value="pse">
        <label for="pse">
            <i class="fas fa-university"></i>
            PSE - Pagos Seguros en Línea
        </label>
    </div>
</div>

<!-- Información de seguridad Wompi -->
<div class="payment-security" style="display: none;" id="wompi-security">
    <div class="security-badges">
        <img src="https://wompi.co/assets/security-badge.png" alt="Seguridad Wompi">
        <span>Procesamiento seguro con Wompi</span>
    </div>
</div>
```

## 🧪 Paso 7: Testing

### 7.1 Tarjetas de Prueba Wompi
```
# Visa exitosa
4242424242424242

# Mastercard exitosa  
5555555555554444

# Visa declinada
4000000000000002

# Cualquier fecha futura y CVC funcionan
Fecha: 12/26
CVC: 123
```

### 7.2 Flujo de Pruebas
1. **Agregar productos** al carrito
2. **Ir a checkout** 
3. **Seleccionar "Tarjeta de crédito/débito"**
4. **Completar información** del cliente
5. **Click en "Confirmar Pedido"**
6. **Widget de Wompi** se abre automáticamente
7. **Ingresar tarjeta de prueba**
8. **Confirmar pago**
9. **Verificar** redirección a página de éxito

## 📊 Paso 8: Monitoreo

### 8.1 Dashboard de Wompi
- **Transacciones**: Panel de comercios Wompi
- **Reportes**: Ventas, comisiones, disputas
- **Configuración**: Webhooks, métodos de pago
- **Soporte**: Chat en vivo, documentación

### 8.2 Webhooks Configuration
```
URL: https://tu-dominio.com/api/wompi-webhook/
Eventos: transaction.updated
```

## 🚀 Paso 9: Producción

### 9.1 Checklist para Producción
- [ ] Cuenta de Wompi activada y verificada
- [ ] Documentación empresarial aprobada
- [ ] Cambiar claves test por claves live
- [ ] Webhook configurado con URL de producción  
- [ ] Probar con tarjeta real (monto pequeño)
- [ ] Verificar que los fondos llegan a tu cuenta

### 9.2 Variables para Producción
```bash
# En .env para producción
WOMPI_PUBLIC_KEY=pub_prod_abc123...
WOMPI_PRIVATE_KEY=prv_prod_xyz789...
WOMPI_ENVIRONMENT=prod
WOMPI_BASE_URL=https://production.wompi.co/v1
```

## 💡 Ventajas de Wompi vs Stripe en Colombia

### ✅ Ventajas de Wompi:
- **Local**: Empresa colombiana, soporte en español
- **PSE**: Integración con bancos colombianos
- **Corresponsalías**: Pagos en efectivo en tiendas
- **Comisiones**: Mejores tarifas para Colombia
- **Cumplimiento**: Regulaciones locales colombianas
- **Soporte**: Atención en horarios colombianos

### 📈 Métodos de Pago Disponibles:
1. **Tarjetas**: Visa, Mastercard (crédito/débito)
2. **PSE**: Todos los bancos colombianos
3. **Efectivo**: Corresponsalías bancarias
4. **Billeteras**: Daviplata, Nequi (próximamente)

## 📞 Soporte Wompi

- **Documentación**: [https://docs.wompi.co](https://docs.wompi.co)
- **Soporte**: soporte@wompi.co
- **WhatsApp**: +57 1 234 5678
- **Dashboard**: [https://comercios.wompi.co](https://comercios.wompi.co)

---

¡Tu e-commerce ahora acepta pagos con la mejor solución para Colombia! 🇨🇴💳