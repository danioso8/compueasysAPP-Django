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

    // Debug: Verificar configuración al cargar
    console.group('🔧 WOMPI CONFIG DEBUG');
    console.log('window.checkout_config:', window.checkout_config);
    console.log('CONFIG.wompi_public_key:', CONFIG.wompi_public_key);
    console.log('CONFIG completo:', CONFIG);
    console.groupEnd();

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

        // 7. Guardar en estado
        checkoutData.subtotal = subtotalNumber;
        checkoutData.shipping = shippingCost;
        checkoutData.discount_amount = discountAmount;
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
        console.log('💳 WOMPI - Iniciando proceso de pago con tarjeta...');
        console.log('💳 WOMPI - Estado actual:', checkoutData);

        // Validar widget de Wompi
        if (!window.WidgetCheckout) {
            console.error('❌ WOMPI - Widget no disponible');
            showMessage('Error: Sistema de pagos no disponible. Recarga la página e intenta nuevamente.', 'error');
            checkoutData.processing = false;
            return;
        }

        // Validar configuración
        console.log('🔍 Validando configuración de Wompi...');
        console.log('window.checkout_config:', window.checkout_config);
        console.log('CONFIG.wompi_public_key:', CONFIG.wompi_public_key);
        
        if (!CONFIG.wompi_public_key || CONFIG.wompi_public_key.trim() === '') {
            console.error('❌ WOMPI - Clave pública no configurada');
            console.error('❌ Detalles del error:');
            console.error('   - window.checkout_config existe:', !!window.checkout_config);
            console.error('   - wompi_public_key en checkout_config:', window.checkout_config?.wompi_public_key);
            console.error('   - CONFIG.wompi_public_key:', CONFIG.wompi_public_key);
            showMessage('Error: Configuración de pagos incompleta. Contacta soporte.', 'error');
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

        console.log('🚀 WOMPI - Enviando datos:', transactionData);

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
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return response.json();
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
            const customerData = {
                email: transactionData.customer_email,
                fullName: document.getElementById('nombre')?.value?.trim() || '',
                phoneNumber: document.getElementById('telefono')?.value?.trim() || ''
            };

            console.log('👤 WOMPI - Datos del cliente:', customerData);

            // Crear configuración del widget
            const widgetConfig = {
                currency: transactionData.currency || 'COP',
                amountInCents: transactionData.amount_in_cents,
                reference: transactionData.reference,
                publicKey: transactionData.public_key,
                acceptanceToken: transactionData.acceptance_token.acceptance_token,
                customerData: customerData,
                redirectUrl: `${window.location.origin}${CONFIG.urls.pago_exitoso}`
            };

            console.log('⚙️ WOMPI - Configuración del widget:', widgetConfig);

            // Mostrar mensaje de preparación
            showMessage('Abriendo ventana de pago segura...', 'info');

            // Crear y abrir widget
            const checkout = new WidgetCheckout(widgetConfig);

            checkout.open(function(result) {
                console.log('📋 WOMPI - Resultado del widget:', result);

                if (result.transaction) {
                    const status = result.transaction.status;
                    const transactionId = result.transaction.id;

                    console.log(`🔍 WOMPI - Estado: ${status}, ID: ${transactionId}`);

                    if (status === 'APPROVED') {
                        console.log('✅ WOMPI - Pago aprobado');
                        showMessage('¡Pago exitoso! Redirigiendo...', 'success');
                        
                        // Redirigir con información de la transacción
                        const redirectUrl = `${CONFIG.urls.pago_exitoso}?transaction_id=${transactionId}&reference=${transactionData.reference}`;
                        setTimeout(() => {
                            window.location.href = redirectUrl;
                        }, 1500);
                        
                    } else if (status === 'DECLINED') {
                        console.log('❌ WOMPI - Pago rechazado');
                        showMessage('Pago rechazado. Verifica los datos de tu tarjeta e intenta nuevamente.', 'error');
                        checkoutData.processing = false;
                        
                    } else if (status === 'ERROR') {
                        console.log('🚫 WOMPI - Error en el pago');
                        showMessage('Error procesando el pago. Intenta nuevamente.', 'error');
                        checkoutData.processing = false;
                        
                    } else {
                        console.log(`⚠️ WOMPI - Estado desconocido: ${status}`);
                        showMessage('Estado de pago desconocido. Contacta soporte si fue descontado de tu tarjeta.', 'warning');
                        checkoutData.processing = false;
                    }
                } else {
                    console.log('❌ WOMPI - Pago cancelado por el usuario');
                    showMessage('Pago cancelado. Puedes intentar nuevamente cuando gustes.', 'info');
                    checkoutData.processing = false;
                }
            });

        } catch (error) {
            console.error('❌ WOMPI - Error abriendo widget:', error);
            showMessage(`Error abriendo el sistema de pagos: ${error.message}`, 'error');
            checkoutData.processing = false;
        }
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
        setupDiscountHandlers();
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