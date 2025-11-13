/**
 * CompuEasys Checkout - Versión Reconstruida
 * Versión: 3.0 - Simple y Funcional
 */

(function() {
    "use strict";

    // Configuración
    const CONFIG = {
        wompi_public_key: window.checkout_config?.wompi_public_key || '',
        urls: {
            create_transaction: window.checkout_config?.create_transaction_url || '/api/create-wompi-transaction/',
            pago_exitoso: '/pago_exitoso/'
        }
    };

    // Estado del checkout
    let checkoutData = {
        subtotal: 0,
        shipping: 0,
        total: 0,
        paymentMethod: 'contraentrega',
        processing: false
    };

    // Utilidades básicas
    function formatMoney(amount) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(amount);
    }

    function showMessage(text, type = 'info') {
        if (window.Swal) {
            Swal.fire({
                icon: type,
                title: text,
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            });
        } else {
            alert(text);
        }
    }

    function getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return '';
    }

    // Función principal: calcular totales
    function calculateTotals() {
        console.log('💰 Calculando totales...');

        // 1. Obtener subtotal del HTML
        const subtotalEl = document.getElementById('subtotal_amount');
        if (!subtotalEl) {
            console.error('❌ No se encontró #subtotal_amount');
            return;
        }

        // 2. Extraer número del subtotal
        const subtotalText = subtotalEl.textContent || '0';
        const subtotalNumber = parseFloat(subtotalText.replace(/[^0-9]/g, '')) || 0;
        
        console.log('📊 Subtotal:', subtotalNumber);

        // 3. Determinar método de pago
        const paymentRadio = document.querySelector('input[name="metodo_pago"]:checked');
        const paymentMethod = paymentRadio ? paymentRadio.value : 'contraentrega';
        
        console.log('🎯 Método de pago:', paymentMethod);

        // 4. Calcular envío
        let shippingCost = 0;
        
        if (paymentMethod === 'recoger_tienda') {
            // Recoger en tienda = SIEMPRE gratis
            shippingCost = 0;
            console.log('🏪 Recoger en tienda: Envío GRATIS');
        } else {
            // Para entrega a domicilio
            if (subtotalNumber < 100000) {
                shippingCost = 15000;
                console.log('📦 Envío: $15,000 (compra menor a $100,000)');
            } else {
                shippingCost = 0;
                console.log('📦 Envío GRATIS (compra mayor o igual a $100,000)');
            }
        }

        // 5. Calcular total
        const totalAmount = subtotalNumber + shippingCost;
        
        console.log('🧮 Cálculo final:', {
            subtotal: subtotalNumber,
            shipping: shippingCost,
            total: totalAmount
        });

        // 6. Guardar en estado
        checkoutData.subtotal = subtotalNumber;
        checkoutData.shipping = shippingCost;
        checkoutData.total = totalAmount;
        checkoutData.paymentMethod = paymentMethod;

        // 7. Actualizar UI
        updateUI();
    }

    // Actualizar interfaz de usuario
    function updateUI() {
        console.log('🖥️ Actualizando UI...');

        // Actualizar envío
        const shippingEl = document.getElementById('shipping_amount');
        if (shippingEl) {
            if (checkoutData.shipping === 0) {
                if (checkoutData.paymentMethod === 'recoger_tienda') {
                    shippingEl.innerHTML = '<span class="text-success">GRATIS <small>(Recoger en tienda)</small></span>';
                } else {
                    shippingEl.innerHTML = '<span class="text-success">GRATIS <small>(Compra mayor a $100,000)</small></span>';
                }
            } else {
                shippingEl.textContent = formatMoney(checkoutData.shipping);
            }
            console.log('✅ Envío actualizado:', checkoutData.shipping);
        }

        // Actualizar total
        const totalEl = document.getElementById('total_final');
        if (totalEl) {
            totalEl.textContent = formatMoney(checkoutData.total);
            console.log('✅ Total actualizado:', checkoutData.total);
        }
    }

    // Manejar cambio de método de pago
    function handlePaymentMethodChange() {
        console.log('🔄 Cambio de método de pago detectado');
        
        // Mostrar/ocultar sección de tarjeta
        const cardSection = document.getElementById('cardPaymentSection');
        const selectedMethod = document.querySelector('input[name="metodo_pago"]:checked');
        
        if (selectedMethod && cardSection) {
            if (selectedMethod.value === 'tarjeta') {
                cardSection.style.display = 'block';
                cardSection.classList.remove('d-none');
                showMessage('💳 Complete la información para pagar con tarjeta', 'info');
            } else {
                cardSection.style.display = 'none';
                cardSection.classList.add('d-none');
                
                if (selectedMethod.value === 'recoger_tienda') {
                    showMessage('🏪 Recoger en tienda - Pago en efectivo o transferencia', 'success');
                } else if (selectedMethod.value === 'contraentrega') {
                    showMessage('📦 Pago contra entrega - Efectivo al recibir', 'info');
                }
            }
        }

        // Recalcular totales
        calculateTotals();
    }

    // Procesar el pedido
    function processOrder() {
        if (checkoutData.processing) {
            return;
        }

        console.log('🚀 Procesando pedido...');

        // Validar formulario básico
        const requiredFields = ['nombre', 'email', 'telefono', 'direccion', 'ciudad'];
        for (let fieldId of requiredFields) {
            const field = document.getElementById(fieldId);
            if (!field || !field.value.trim()) {
                showMessage(`Por favor completa el campo: ${fieldId}`, 'error');
                field?.focus();
                return;
            }
        }

        checkoutData.processing = true;

        // Procesar según método de pago
        const paymentMethod = document.querySelector('input[name="metodo_pago"]:checked')?.value;

        if (paymentMethod === 'tarjeta') {
            processCardPayment();
        } else {
            processStandardPayment();
        }
    }

    // Procesar pago con tarjeta (Wompi)
    function processCardPayment() {
        console.log('💳 Procesando pago con tarjeta...');

        if (!window.WidgetCheckout) {
            showMessage('Error: Widget de pagos no disponible', 'error');
            checkoutData.processing = false;
            return;
        }

        // Crear transacción
        const transactionData = {
            amount: checkoutData.total,
            customer_email: document.getElementById('email')?.value || ''
        };

        fetch(CONFIG.urls.create_transaction, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(transactionData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                openWompiWidget(data);
            } else {
                showMessage('Error creando transacción: ' + (data.error || 'Error desconocido'), 'error');
                checkoutData.processing = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Error de conexión. Intenta de nuevo.', 'error');
            checkoutData.processing = false;
        });
    }

    // Abrir widget de Wompi
    function openWompiWidget(transactionData) {
        const checkout = new WidgetCheckout({
            currency: 'COP',
            amountInCents: transactionData.amount_in_cents,
            reference: transactionData.reference,
            publicKey: CONFIG.wompi_public_key,
            customerData: {
                email: transactionData.customer_email,
                fullName: document.getElementById('nombre')?.value || '',
                phoneNumber: document.getElementById('telefono')?.value || ''
            },
            redirectUrl: `${window.location.origin}${CONFIG.urls.pago_exitoso}`
        });

        checkout.open(function(result) {
            if (result.transaction && result.transaction.status === 'APPROVED') {
                // Pago exitoso
                window.location.href = CONFIG.urls.pago_exitoso + '?transaction_id=' + result.transaction.id;
            } else {
                showMessage('Pago cancelado o falló', 'error');
                checkoutData.processing = false;
            }
        });
    }

    // Procesar pago estándar (contra entrega / recoger en tienda)
    function processStandardPayment() {
        console.log('📦 Procesando pago estándar...');

        const form = document.getElementById('checkoutForm');
        if (!form) {
            showMessage('Error: formulario no encontrado', 'error');
            checkoutData.processing = false;
            return;
        }

        // Agregar método de pago al formulario
        let methodInput = form.querySelector('input[name="metodo_pago"]');
        if (!methodInput) {
            methodInput = document.createElement('input');
            methodInput.type = 'hidden';
            methodInput.name = 'metodo_pago';
            form.appendChild(methodInput);
        }
        methodInput.value = checkoutData.paymentMethod;

        // Enviar formulario
        showMessage('¡Pedido confirmado! Serás redirigido...', 'success');
        setTimeout(() => {
            form.submit();
        }, 1000);
    }

    // Configurar event listeners
    function setupEventListeners() {
        console.log('🎯 Configurando event listeners...');

        // Métodos de pago
        const paymentMethods = document.querySelectorAll('input[name="metodo_pago"]');
        paymentMethods.forEach(method => {
            method.addEventListener('change', handlePaymentMethodChange);
        });

        // Botón de confirmar
        const submitBtn = document.getElementById('checkout_submit_btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', function(e) {
                e.preventDefault();
                processOrder();
            });
        }

        console.log('✅ Event listeners configurados');
    }

    // Inicialización
    function init() {
        console.log('🚀 Iniciando CompuEasys Checkout v3.0...');

        // Verificar elementos esenciales
        const form = document.getElementById('checkoutForm');
        const subtotal = document.getElementById('subtotal_amount');
        const methods = document.querySelectorAll('input[name="metodo_pago"]');

        if (!form) console.error('❌ Formulario #checkoutForm no encontrado');
        if (!subtotal) console.error('❌ Elemento #subtotal_amount no encontrado');
        if (methods.length === 0) console.error('❌ Métodos de pago no encontrados');

        // Configurar todo
        setupEventListeners();
        calculateTotals();

        console.log('✅ Checkout inicializado correctamente');
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Exponer funciones para debugging
    window.CheckoutDebug = {
        state: checkoutData,
        config: CONFIG,
        calculate: calculateTotals,
        process: processOrder,
        
        // Test simple
        test: function() {
            console.log('🧪 Estado actual del checkout:');
            console.log('- Subtotal:', checkoutData.subtotal);
            console.log('- Envío:', checkoutData.shipping);
            console.log('- Total:', checkoutData.total);
            console.log('- Método:', checkoutData.paymentMethod);
            
            // Verificar elementos
            const elements = {
                'Formulario': '#checkoutForm',
                'Subtotal': '#subtotal_amount',
                'Envío': '#shipping_amount',
                'Total': '#total_final',
                'Botón': '#checkout_submit_btn'
            };
            
            console.log('\n📋 Elementos HTML:');
            Object.entries(elements).forEach(([name, selector]) => {
                const el = document.querySelector(selector);
                console.log(`- ${name}:`, el ? '✅ Encontrado' : '❌ No encontrado');
            });
        }
    };

})();