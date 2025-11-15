/**
 * CompuEasys Checkout - Versión Reconstruida
 * Versión: 3.0 - Simple y Funcional
 */

console.log('🚀 CHECKOUT-WOMPI.JS - Archivo cargándose...');

(function() {
    "use strict";
    
    console.log('📦 CHECKOUT-WOMPI.JS - IIFE iniciándose...');

    // Configuración con fallback más robusto
    let CONFIG = null;
    
    function initializeConfig() {
        // Intentar obtener configuración del window
        let wompiKey = '';
        
        if (window.checkout_config && window.checkout_config.wompi_public_key) {
            wompiKey = window.checkout_config.wompi_public_key;
        } else {
            // Fallback: buscar en meta tags
            const metaKey = document.querySelector('meta[name="wompi-public-key"]');
            if (metaKey) {
                wompiKey = metaKey.getAttribute('content');
            }
        }
        
        CONFIG = {
            wompi_public_key: wompiKey,
            urls: {
                create_transaction: window.checkout_config?.create_transaction_url || '/api/create-wompi-transaction/',
                pago_exitoso: '/pago_exitoso/'
            }
        };

        // Debug: Verificar configuración al cargar
        console.group('🔧 WOMPI CONFIG DEBUG');
        console.log('window.checkout_config:', window.checkout_config);
        console.log('META wompi key:', document.querySelector('meta[name="wompi-public-key"]')?.getAttribute('content'));
        console.log('CONFIG.wompi_public_key:', CONFIG.wompi_public_key);
        console.log('CONFIG completo:', CONFIG);
        console.groupEnd();
        
        return CONFIG;
    }

    // Inicializar configuración
    CONFIG = initializeConfig();

    // Verificar carga del widget de Wompi
    function checkWompiWidgetLoad() {
        console.log('🔍 Verificando carga del widget de Wompi...');
        
        if (window.WidgetCheckout) {
            console.log('✅ Widget de Wompi cargado correctamente');
            return true;
        } else {
            console.warn('⚠️ Widget de Wompi no disponible aún');
            
            // Verificar si el script está presente
            const script = document.querySelector('script[src*="wompi.co"]');
            if (script) {
                console.log('✅ Script de Wompi encontrado en el DOM');
            } else {
                console.error('❌ Script de Wompi NO encontrado en el DOM');
            }
            
            return false;
        }
    }

    // Verificar widget al cargar
    setTimeout(checkWompiWidgetLoad, 1000);

    // Re-verificar cada 5 segundos si no está disponible
    const widgetCheckInterval = setInterval(() => {
        if (checkWompiWidgetLoad()) {
            clearInterval(widgetCheckInterval);
        }
    }, 5000);

    // Estado del checkout
    let checkoutData = {
        subtotal: 0,
        shipping: 0,
        discount: 0,
        discountCode: '',
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

    // FUNCIONES DE DESCUENTO
    function validateDiscountCode(code, cartTotal) {
        console.log('🎫 Validando código de descuento:', { code, cartTotal });
        
        return fetch('/api/validate-discount-code/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                codigo: code,
                cart_total: cartTotal
            })
        })
        .then(response => {
            console.log('📡 Respuesta del servidor:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📋 Datos recibidos:', data);
            return data;
        })
        .catch(error => {
            console.error('❌ Error validating discount:', error);
            return { valid: false, message: 'Error de conexión' };
        });
    }

    function applyDiscount(code, amount) {
        console.log('✅ Aplicando descuento:', { code, amount });
        
        checkoutData.discountCode = code;
        checkoutData.discount = amount;
        
        // Actualizar campos hidden
        document.getElementById('discountAppliedValue').value = code;
        document.getElementById('discountAmountValue').value = amount;
        
        // Mostrar fila de descuento
        const discountRow = document.getElementById('discount_row');
        const discountCodeEl = document.getElementById('discount_code_applied');
        const discountAmountEl = document.getElementById('discount_amount_display');
        
        if (discountRow && discountCodeEl && discountAmountEl) {
            discountRow.classList.remove('d-none');
            discountCodeEl.textContent = code;
            discountAmountEl.textContent = formatMoney(-amount);
        }
        
        // Recalcular totales
        calculateTotals();
    }

    function removeDiscount() {
        console.log('❌ Removiendo descuento');
        
        checkoutData.discountCode = '';
        checkoutData.discount = 0;
        
        // Limpiar campos hidden
        document.getElementById('discountAppliedValue').value = '';
        document.getElementById('discountAmountValue').value = '0';
        
        // Ocultar fila de descuento
        const discountRow = document.getElementById('discount_row');
        if (discountRow) {
            discountRow.classList.add('d-none');
        }
        
        // Limpiar campo de input
        const codeInput = document.getElementById('discount_code');
        if (codeInput) {
            codeInput.value = '';
        }
        
        // Recalcular totales
        calculateTotals();
    }

    function showDiscountFeedback(message, isSuccess) {
        const feedbackEl = document.getElementById('discount_feedback');
        if (feedbackEl) {
            feedbackEl.innerHTML = `
                <div class="alert alert-${isSuccess ? 'success' : 'danger'} alert-sm mt-2">
                    <i class="bi bi-${isSuccess ? 'check-circle' : 'exclamation-triangle'}"></i>
                    ${message}
                </div>
            `;
        }
    }

    function setupDiscountHandlers() {
        console.log('🔧 Configurando manejadores de descuento...');
        
        const discountInput = document.getElementById('discount_code');
        const applyBtn = document.getElementById('apply_discount_btn');
        
        console.log('🔍 Elementos encontrados:', {
            input: !!discountInput,
            button: !!applyBtn
        });
        
        if (!discountInput || !applyBtn) {
            console.error('⚠️ Elementos de descuento no encontrados');
            return;
        }
        
        console.log('✅ Event listeners configurados para descuento');
        
        // Evento para aplicar descuento
        applyBtn.addEventListener('click', async function() {
            console.log('🎯 Click en botón aplicar descuento');
            
            const code = discountInput.value.trim().toUpperCase();
            console.log('📝 Código ingresado:', code);
            
            if (!code) {
                showDiscountFeedback('Por favor ingresa un código de descuento', false);
                return;
            }
            
            // Mostrar loading
            const btnText = this.querySelector('.btn-text');
            const btnSpinner = this.querySelector('.btn-spinner');
            
            if (btnText && btnSpinner) {
                btnText.classList.add('d-none');
                btnSpinner.classList.remove('d-none');
            }
            this.disabled = true;
            
            try {
                const result = await validateDiscountCode(code, checkoutData.subtotal);
                
                if (result.valid) {
                    applyDiscount(code, result.discount_amount);
                    showDiscountFeedback(result.message, true);
                } else {
                    showDiscountFeedback(result.message, false);
                }
            } catch (error) {
                showDiscountFeedback('Error al validar código. Intenta de nuevo.', false);
            } finally {
                // Restaurar botón
                if (btnText && btnSpinner) {
                    btnText.classList.remove('d-none');
                    btnSpinner.classList.add('d-none');
                }
                this.disabled = false;
            }
        });
        
        // Evento para remover descuento cuando se modifica el input
        discountInput.addEventListener('input', function() {
            if (checkoutData.discountCode && this.value !== checkoutData.discountCode) {
                removeDiscount();
                document.getElementById('discount_feedback').innerHTML = '';
            }
        });
        
        // Permitir aplicar con Enter
        discountInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyBtn.click();
            }
        });
        
        console.log('✅ Event handlers de descuento configurados');
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

        // 4. Determinar forma de entrega
        const deliveryRadio = document.querySelector('input[name="forma_entrega"]:checked');
        const deliveryMethod = deliveryRadio ? deliveryRadio.value : 'domicilio';
        
        console.log('🚚 Forma de entrega:', deliveryMethod);
        console.log('🎯 Método de pago:', paymentMethod);

        // 5. Calcular envío basado en forma de entrega
        let shippingCost = 0;
        
        if (deliveryMethod === 'tienda') {
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

        // 5. Aplicar descuento si existe
        let discountAmount = 0;
        if (checkoutData.discount > 0) {
            // El descuento ya viene calculado desde el servidor
            discountAmount = checkoutData.discount;
            console.log('💰 Descuento aplicado:', {
                codigo: checkoutData.discountCode,
                descuento: discountAmount
            });
        }

        // 6. Calcular total
        const totalAmount = Math.max(0, subtotalNumber + shippingCost - discountAmount);
        
        console.log('🧮 Cálculo final:', {
            subtotal: subtotalNumber,
            shipping: shippingCost,
            discount: discountAmount,
            total: totalAmount
        });

        // 7. Actualizar campo hidden de forma de entrega
        const deliveryHiddenField = document.getElementById('formaEntregaValue');
        if (deliveryHiddenField) {
            deliveryHiddenField.value = deliveryMethod;
        }

        // 8. Guardar en estado
        checkoutData.subtotal = subtotalNumber;
        checkoutData.shipping = shippingCost;
        checkoutData.discount_amount = discountAmount;
        checkoutData.total = totalAmount;
        checkoutData.paymentMethod = paymentMethod;
        checkoutData.deliveryMethod = deliveryMethod;

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
                if (checkoutData.deliveryMethod === 'tienda') {
                    shippingEl.innerHTML = '<span class="text-success">GRATIS <small>(Recoger en tienda)</small></span>';
                } else {
                    shippingEl.innerHTML = '<span class="text-success">GRATIS <small>(Compra mayor a $100,000)</small></span>';
                }
            } else {
                shippingEl.textContent = formatMoney(checkoutData.shipping);
            }
            console.log('✅ Envío actualizado:', checkoutData.shipping);
        }

        // Actualizar descuento
        const discountEl = document.getElementById('discount_display');
        if (discountEl && checkoutData.discount_amount > 0) {
            discountEl.innerHTML = `
                <div class="d-flex justify-content-between">
                    <span>Descuento (${checkoutData.discountCode}):</span>
                    <span class="text-success">-${formatMoney(checkoutData.discount_amount)}</span>
                </div>
            `;
            discountEl.style.display = 'block';
        } else if (discountEl) {
            discountEl.style.display = 'none';
        }

        // Actualizar total
        const totalEl = document.getElementById('total_final');
        if (totalEl) {
            totalEl.textContent = formatMoney(checkoutData.total);
            console.log('✅ Total actualizado:', checkoutData.total);
        }
    }

    // Manejar cambio de forma de entrega
    function handleDeliveryMethodChange() {
        console.log('🚚 Cambio de forma de entrega detectado');
        
        const selectedDelivery = document.querySelector('input[name="forma_entrega"]:checked');
        const efectivoDesc = document.getElementById('efectivo_description');
        const efectivoNote = document.getElementById('efectivo_note');
        
        if (selectedDelivery && efectivoDesc && efectivoNote) {
            if (selectedDelivery.value === 'tienda') {
                efectivoDesc.textContent = 'Paga al recoger en la tienda';
                efectivoNote.textContent = 'Efectivo o transferencia en el punto de venta';
            } else {
                efectivoDesc.textContent = 'Paga al recibir tu pedido';
                efectivoNote.textContent = 'Efectivo o transferencia al momento de la entrega';
            }
        }
        
        // Recalcular totales
        calculateTotals();
    }

    // Procesar el pedido
    function processOrder() {
        if (checkoutData.processing) {
            console.warn('⚠️ Procesamiento ya en curso, ignorando click adicional');
            return;
        }

        console.log('🚀 Procesando pedido con tarjeta...');

        // Debug del estado actual
        console.log('🔍 Estado actual del checkout:', checkoutData);
        console.log('🔍 Formulario actual:', {
            email: document.getElementById('email')?.value,
            nombre: document.getElementById('nombre')?.value,
            telefono: document.getElementById('telefono')?.value,
            direccion: document.getElementById('direccion')?.value,
            ciudad: document.getElementById('ciudad')?.value
        });

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

        // Siempre procesar con tarjeta (única opción)
        console.log('🎯 Procesando pago con tarjeta (única opción disponible)...');
        processCardPayment();
    }

    // Procesar pago con tarjeta (Wompi)
    function processCardPayment() {
        console.log('💳 WOMPI - Iniciando proceso de pago con tarjeta...');
        console.log('💳 WOMPI - Estado actual:', checkoutData);

        // Validar widget de Wompi
        console.log('🔍 Verificando disponibilidad del widget de Wompi...');
        console.log('window.WidgetCheckout:', typeof window.WidgetCheckout);
        console.log('Script Wompi cargado:', !!document.querySelector('script[src*="wompi.co"]'));
        
        if (!window.WidgetCheckout) {
            console.error('❌ WOMPI - Widget no disponible');
            console.error('Posibles causas:');
            console.error('1. Script de Wompi no cargó');
            console.error('2. Bloqueador de anuncios interfiriendo');
            console.error('3. Problema de conexión');
            showMessage('Error: Sistema de pagos no disponible. Verifica tu conexión e intenta nuevamente.', 'error');
            checkoutData.processing = false;
            return;
        }

        console.log('✅ Widget de Wompi disponible');

        // Validar configuración
        console.log('🔍 Validando configuración de Wompi...');
        
        // Si la configuración no es válida, intentar reinicializarla
        if (!CONFIG.wompi_public_key || CONFIG.wompi_public_key.trim() === '') {
            console.warn('⚠️ Configuración inválida, reintentando inicialización...');
            CONFIG = initializeConfig();
        }
        
        console.log('window.checkout_config:', window.checkout_config);
        console.log('CONFIG.wompi_public_key:', CONFIG.wompi_public_key);
        
        if (!CONFIG.wompi_public_key || CONFIG.wompi_public_key.trim() === '') {
            console.error('❌ WOMPI - Clave pública no configurada');
            console.error('❌ Detalles del error:');
            console.error('   - window.checkout_config existe:', !!window.checkout_config);
            console.error('   - wompi_public_key en checkout_config:', window.checkout_config?.wompi_public_key);
            console.error('   - Meta tag wompi-public-key:', document.querySelector('meta[name="wompi-public-key"]')?.getAttribute('content'));
            console.error('   - CONFIG.wompi_public_key:', CONFIG.wompi_public_key);
            showMessage('Error: Configuración de pagos incompleta. Recarga la página e intenta nuevamente.', 'error');
            checkoutData.processing = false;
            return;
        }

        console.log('✅ WOMPI - Configuración validada correctamente');

        // Validar datos del cliente
        const customerEmail = document.getElementById('email')?.value?.trim();
        const customerName = document.getElementById('nombre')?.value?.trim();
        
        if (!customerEmail) {
            showMessage('Por favor ingresa tu correo electrónico', 'error');
            checkoutData.processing = false;
            return;
        }

        if (!customerName) {
            showMessage('Por favor ingresa tu nombre completo', 'error');
            checkoutData.processing = false;
            return;
        }

        // Mostrar indicador de carga
        showMessage('Creando transacción segura...', 'info');

        // Preparar datos de transacción
        const transactionData = {
            amount: checkoutData.total,
            customer_email: customerEmail,
            discount_code: checkoutData.discountCode || '',
            discount_amount: checkoutData.discount_amount || 0
        };

        console.log('🚀 WOMPI - Enviando datos de transacción:', transactionData);
        console.log('🔍 WOMPI - Total del checkout:', checkoutData.total);
        console.log('🔍 WOMPI - Email del cliente:', customerEmail);
        
        // Validar datos antes de enviar
        if (!transactionData.amount || transactionData.amount <= 0) {
            showMessage('Error: El monto del pedido no es válido. Verifica tu carrito.', 'error');
            checkoutData.processing = false;
            return;
        }
        
        if (!transactionData.customer_email) {
            showMessage('Error: Email requerido para procesar el pago.', 'error');
            checkoutData.processing = false;
            return;
        }

        // Crear transacción en el servidor
        fetch(CONFIG.urls.create_transaction, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(transactionData)
        })
        .then(response => {
            console.log(`📡 WOMPI - Respuesta del servidor: ${response.status}`);
            console.log('📡 WOMPI - Headers de respuesta:', response.headers);
            
            // Capturar el texto de la respuesta para debugging
            return response.text().then(text => {
                console.log('📡 WOMPI - Texto de respuesta:', text);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${text}`);
                }
                
                try {
                    return JSON.parse(text);
                } catch (e) {
                    throw new Error(`Respuesta no válida del servidor: ${text}`);
                }
            });
        })
        .then(data => {
            console.log('📋 WOMPI - Datos recibidos:', data);
            
            if (data.success) {
                console.log('✅ WOMPI - Transacción creada exitosamente');
                openWompiWidget(data);
            } else {
                console.error('❌ WOMPI - Error en transacción:', data);
                
                let errorMsg = 'Error creando transacción';
                if (data.error) {
                    errorMsg = data.error;
                    
                    // Mensajes específicos para errores comunes
                    if (data.error.includes('configuración')) {
                        errorMsg = 'Error de configuración del sistema de pagos. Contacta soporte.';
                    } else if (data.error.includes('acceptance token')) {
                        errorMsg = 'Error conectando con el sistema de pagos. Intenta nuevamente.';
                    } else if (data.error.includes('Monto inválido')) {
                        errorMsg = 'El monto del pedido no es válido. Verifica tu carrito.';
                    }
                }
                
                if (data.details) {
                    console.error('📝 WOMPI - Detalles del error:', data.details);
                }
                
                showMessage(errorMsg, 'error');
                checkoutData.processing = false;
            }
        })
        .catch(error => {
            console.error('❌ WOMPI - Error de conexión:', error);
            
            let errorMsg = 'Error de conexión con el sistema de pagos.';
            let showRetry = true;
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMsg = 'Sin conexión a internet. Verifica tu conexión e intenta nuevamente.';
            } else if (error.message.includes('HTTP 500')) {
                errorMsg = 'Error temporal del servidor de pagos. Reintentando automáticamente...';
                showRetry = false;
                
                // Auto-reintentar después de 3 segundos
                setTimeout(() => {
                    console.log('🔄 WOMPI - Auto-reintentando...');
                    createTransactionWithWompi(customerEmail);
                }, 3000);
                
            } else if (error.message.includes('HTTP 400')) {
                errorMsg = 'Datos de pago inválidos. Verifica la información e intenta nuevamente.';
                showRetry = false;
            } else if (error.message.includes('timeout')) {
                errorMsg = 'La conexión con el sistema de pagos tardó demasiado. Intenta nuevamente.';
            } else if (error.message.includes('connection')) {
                errorMsg = 'No se pudo conectar con el sistema de pagos. Verifica tu internet e intenta nuevamente.';
            }
            
            const finalMessage = showRetry ? 
                errorMsg + ' Si el problema persiste, contacta soporte.' : 
                errorMsg;
            
            showMessage(finalMessage, 'error');
            checkoutData.processing = false;
        });
    }

    // Abrir widget de Wompi
    function openWompiWidget(transactionData) {
        console.log('🔓 WOMPI - Abriendo widget de pago...');
        console.log('🔓 WOMPI - Datos de transacción:', transactionData);

        try {
            // Verificar que el widget de Wompi esté disponible
            if (typeof WidgetCheckout === 'undefined' || !window.WidgetCheckout) {
                throw new Error('Widget de Wompi no disponible. Verifica tu conexión e intenta nuevamente.');
            }

            // Validar datos requeridos
            if (!transactionData.amount_in_cents || transactionData.amount_in_cents <= 0) {
                throw new Error('Monto inválido para el pago');
            }

            if (!transactionData.reference) {
                throw new Error('Referencia de transacción no válida');
            }

            if (!transactionData.acceptance_token?.acceptance_token) {
                throw new Error('Token de aceptación no disponible');
            }

            // Preparar datos del cliente
            const phoneNumber = document.getElementById('telefono')?.value?.trim() || '';
            
            // Preparar datos del cliente
            const phoneNumber = document.getElementById('telefono')?.value?.trim() || '';
            
            // Procesar número de teléfono
            let cleanPhoneNumber = phoneNumber;
            if (phoneNumber) {
                // Limpiar el número de espacios, guiones y paréntesis
                cleanPhoneNumber = phoneNumber.replace(/[\s\-\(\)]/g, '');
                
                // Si empieza con +57 o 57, removerlo
                if (cleanPhoneNumber.startsWith('+57')) {
                    cleanPhoneNumber = cleanPhoneNumber.substring(3);
                } else if (cleanPhoneNumber.startsWith('57')) {
                    cleanPhoneNumber = cleanPhoneNumber.substring(2);
                }
            } else {
                cleanPhoneNumber = '3001234567'; // Número por defecto
            }

            // Crear configuración del widget SIMPLE
            const widgetConfig = {
                currency: 'COP',
                amountInCents: transactionData.amount_in_cents,
                reference: transactionData.reference,
                publicKey: transactionData.public_key,
                acceptanceToken: transactionData.acceptance_token.acceptance_token,
                customerEmail: transactionData.customer_email,
                customerData: {
                    email: transactionData.customer_email,
                    fullName: document.getElementById('nombre')?.value?.trim() || 'Cliente',
                    phoneNumber: cleanPhoneNumber,
                    phoneNumberPrefix: '+57'
                }
            };
            
            console.log('⚙️ WOMPI - Configuración SIMPLE del widget:', {
                currency: widgetConfig.currency,
                amountInCents: widgetConfig.amountInCents,
                reference: widgetConfig.reference,
                publicKey: widgetConfig.publicKey ? 'presente' : 'faltante',
                acceptanceToken: widgetConfig.acceptanceToken ? 'presente' : 'faltante',
                customerEmail: widgetConfig.customerEmail,
                customerData: widgetConfig.customerData
            });            // Validar configuración del widget
            if (!widgetConfig.publicKey) {
                throw new Error('Clave pública de Wompi no disponible');
            }

            if (!widgetConfig.acceptanceToken) {
                throw new Error('Token de aceptación no disponible');
            }

            // Mostrar mensaje de preparación
            showMessage('Abriendo ventana de pago segura...', 'info');

            // LOG COMPLETO ANTES DE CREAR WIDGET
            console.log('🔍 WOMPI - DATOS COMPLETOS ANTES DE CREAR WIDGET:');
            console.log('🔍 transactionData recibido:', transactionData);
            console.log('🔍 widgetConfig final:', JSON.stringify(widgetConfig, null, 2));
            
            // Verificar que WidgetCheckout existe
            if (typeof WidgetCheckout === 'undefined') {
                throw new Error('WidgetCheckout no está disponible. El script de Wompi no se cargó correctamente.');
            }

            // Crear y abrir widget
            console.log('🔄 WOMPI - Creando widget...');
            console.log('🔄 WOMPI - Verificando WidgetCheckout:', typeof WidgetCheckout);
            console.log('🔄 WOMPI - window.WidgetCheckout:', typeof window.WidgetCheckout);
            
            const checkout = new WidgetCheckout(widgetConfig);
            console.log('✅ WOMPI - Widget creado exitosamente');

            console.log('🚀 WOMPI - Abriendo widget...');
            checkout.open(function(result) {
                console.log('📋 WOMPI - Resultado completo del widget:', result);
                console.log('📋 WOMPI - Tipo de resultado:', typeof result);
                
                // Analizar el resultado más detalladamente
                if (result && result.transaction) {
                    const transaction = result.transaction;
                    const status = transaction.status;
                    const transactionId = transaction.id;
                    
                    console.log('📋 WOMPI - Transacción completa:', transaction);
                    console.log(`🔍 WOMPI - Estado: ${status}, ID: ${transactionId}`);
                    
                    // Log adicional de información de la transacción
                    if (transaction.status_message) {
                        console.log('💬 WOMPI - Mensaje de estado:', transaction.status_message);
                    }
                    if (transaction.payment_method) {
                        console.log('💳 WOMPI - Método de pago:', transaction.payment_method);
                    }

                    if (status === 'APPROVED') {
                        console.log('✅ WOMPI - Pago aprobado');
                        showMessage('¡Pago exitoso! Redirigiendo...', 'success');
                        
                        // Crear formulario para enviar datos al backend
                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = CONFIG.urls.pago_exitoso;
                        
                        // Agregar CSRF token
                        const csrfInput = document.createElement('input');
                        csrfInput.type = 'hidden';
                        csrfInput.name = 'csrfmiddlewaretoken';
                        csrfInput.value = getCsrfToken();
                        form.appendChild(csrfInput);
                        
                        // Agregar transaction_id
                        const transactionInput = document.createElement('input');
                        transactionInput.type = 'hidden';
                        transactionInput.name = 'transaction_id';
                        transactionInput.value = transactionId;
                        form.appendChild(transactionInput);
                        
                        // Agregar todos los datos del formulario original
                        const formData = new FormData(document.getElementById('checkoutForm'));
                        for (let [key, value] of formData.entries()) {
                            const input = document.createElement('input');
                            input.type = 'hidden';
                            input.name = key;
                            input.value = value;
                            form.appendChild(input);
                        }
                        
                        // Enviar al cuerpo y submittear
                        document.body.appendChild(form);
                        form.submit();
                        
                    } else if (status === 'DECLINED') {
                        console.log('❌ WOMPI - Pago rechazado');
                        let declineMessage = 'Pago rechazado. Verifica los datos de tu tarjeta e intenta nuevamente.';
                        
                        // Mensaje más específico si hay información disponible
                        if (transaction.status_message) {
                            declineMessage = `Pago rechazado: ${transaction.status_message}`;
                        }
                        
                        showMessage(declineMessage, 'error');
                        checkoutData.processing = false;
                        
                    } else if (status === 'ERROR') {
                        console.log('🚫 WOMPI - Error en el pago');
                        let errorMessage = 'Error procesando el pago. Intenta nuevamente.';
                        
                        // Mensaje más específico si hay información disponible
                        if (transaction.status_message) {
                            errorMessage = `Error en el pago: ${transaction.status_message}`;
                        }
                        
                        showMessage(errorMessage, 'error');
                        checkoutData.processing = false;
                        
                    } else {
                        console.log(`⚠️ WOMPI - Estado desconocido: ${status}`);
                        let unknownMessage = 'Estado de pago desconocido. Contacta soporte si fue descontado de tu tarjeta.';
                        
                        if (transaction.status_message) {
                            unknownMessage = `Estado desconocido: ${transaction.status_message}`;
                        }
                        
                        showMessage(unknownMessage, 'warning');
                        checkoutData.processing = false;
                    }
                } else if (result && result.error) {
                    // Manejo específico de errores del widget
                    console.log('❌ WOMPI - Error del widget:', result.error);
                    let errorMessage = 'Error en el sistema de pagos.';
                    
                    if (result.error.message) {
                        errorMessage = `Error: ${result.error.message}`;
                    } else if (typeof result.error === 'string') {
                        errorMessage = `Error: ${result.error}`;
                    }
                    
                    showMessage(errorMessage, 'error');
                    checkoutData.processing = false;
                } else {
                    console.log('❌ WOMPI - Pago cancelado o resultado inválido:', result);
                    showMessage('Pago cancelado. Puedes intentar nuevamente cuando gustes.', 'info');
                    checkoutData.processing = false;
                }
            });

        } catch (error) {
            console.error('❌ WOMPI - Error abriendo widget:', error);
            console.error('❌ Stack trace:', error.stack);
            console.error('❌ Tipo de error:', error.constructor.name);
            
            let errorMessage = 'Error abriendo el sistema de pagos';
            
            // Verificar que error.message existe antes de usar .includes()
            const errorMsg = error.message || error.toString() || 'Error desconocido';
            
            // Mensajes específicos según el tipo de error
            if (errorMsg.includes('Widget de Wompi no disponible')) {
                errorMessage = 'El sistema de pagos no se cargó correctamente. Recarga la página e intenta nuevamente.';
            } else if (errorMsg.includes('WidgetCheckout is not defined')) {
                errorMessage = 'Error de carga del sistema de pagos. Verifica tu conexión a internet e intenta nuevamente.';
            } else if (errorMsg.includes('publicKey')) {
                errorMessage = 'Error de configuración del sistema de pagos. Contacta soporte.';
            } else if (errorMsg.includes('acceptanceToken')) {
                errorMessage = 'Error obteniendo permisos de pago. Intenta nuevamente.';
            } else if (errorMsg.includes('phoneNumberPrefix')) {
                errorMessage = 'Error con el número de teléfono. Verifica que sea un número válido.';
            } else if (errorMsg.includes('obligatorios no están presentes')) {
                errorMessage = 'Faltan datos requeridos para el pago. Verifica que todos los campos estén completos.';
            } else {
                errorMessage = `Error en sistema de pagos: ${errorMsg}`;
            }
            
            showMessage(errorMessage, 'error');
            checkoutData.processing = false;
            
            // Debug adicional
            console.group('🔍 WOMPI DEBUG ERROR');
            console.log('window.WidgetCheckout existe:', typeof window.WidgetCheckout !== 'undefined');
            console.log('Script de Wompi cargado:', document.querySelector('script[src*="wompi.co"]') !== null);
            console.log('Configuración:', CONFIG);
            console.log('TransactionData:', transactionData);
            console.groupEnd();
        }
    }
    // Configurar event listeners
    function setupEventListeners() {
        console.log('🎯 Configurando event listeners...');

        // Formas de entrega
        const deliveryMethods = document.querySelectorAll('input[name="forma_entrega"]');
        deliveryMethods.forEach(method => {
            method.addEventListener('change', handleDeliveryMethodChange);
        });

        // Solo un método de pago (tarjeta) - no necesita event listeners especiales
        console.log('💳 Método de pago único: Tarjeta (siempre activo)');

        // Botón de confirmar
        const submitBtn = document.getElementById('checkout_submit_btn');
        if (submitBtn) {
            console.log('✅ Botón submit encontrado y configurando event listener');
            submitBtn.addEventListener('click', function(e) {
                console.log('🎯 BOTÓN SUBMIT CLICKEADO - Iniciando proceso');
                e.preventDefault();
                processOrder();
            });
        } else {
            console.error('❌ Botón submit NO encontrado con ID: checkout_submit_btn');
        }

        console.log('✅ Event listeners configurados');
    }

    // Inicialización
    function init() {
        console.log('🚀 Iniciando CompuEasys Checkout v3.0...');

        // Verificar elementos esenciales
        const form = document.getElementById('checkoutForm');
        const subtotal = document.getElementById('subtotal_amount');
        const cardSection = document.getElementById('cardPaymentSection');
        const submitBtn = document.getElementById('checkout_submit_btn');

        console.group('🔍 Verificación de Elementos DOM');
        console.log('Formulario:', form ? '✅' : '❌', form);
        console.log('Subtotal:', subtotal ? '✅' : '❌', subtotal);
        console.log('Sección tarjeta:', cardSection ? '✅' : '❌', cardSection);
        console.log('Botón submit:', submitBtn ? '✅' : '❌', submitBtn);
        console.log('💳 Método de pago: TARJETA (único disponible)');
        console.groupEnd();

        if (!form) console.error('❌ Formulario #checkoutForm no encontrado');
        if (!subtotal) console.error('❌ Elemento #subtotal_amount no encontrado');
        if (!cardSection) console.error('❌ Sección de tarjeta no encontrada');

        // Configurar todo
        setupEventListeners();
        setupDiscountHandlers();
        calculateTotals();

        console.log('✅ Checkout inicializado correctamente');
        
        // Resumen de estado
        console.group('📋 Estado Final del Checkout');
        console.log('CONFIG:', CONFIG);
        console.log('checkoutData:', checkoutData);
        console.log('Widget Wompi disponible:', !!window.WidgetCheckout);
        console.groupEnd();
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
        validateDiscount: validateDiscountCode,
        
        // Test simple
        test: function() {
            console.log('🧪 Estado actual del checkout:');
            console.log('- Subtotal:', checkoutData.subtotal);
            console.log('- Envío:', checkoutData.shipping);
            console.log('- Descuento:', checkoutData.discount_amount || 0);
            console.log('- Total:', checkoutData.total);
            console.log('- Método:', checkoutData.paymentMethod);
            console.log('- Código descuento:', checkoutData.discount?.code || 'Ninguno');
            
            // Verificar elementos
            const elements = {
                'Formulario': '#checkoutForm',
                'Subtotal': '#subtotal_amount',
                'Envío': '#shipping_amount',
                'Total': '#total_final',
                'Botón': '#checkout_submit_btn',
                'Código descuento': '#discount_code',
                'Botón aplicar': '#apply_discount',
                'Área descuento': '#discount_display'
            };
            
            console.log('\n📋 Elementos HTML:');
            Object.entries(elements).forEach(([name, selector]) => {
                const el = document.querySelector(selector);
                console.log(`- ${name}:`, el ? '✅ Encontrado' : '❌ No encontrado');
            });
        }
    };

})();