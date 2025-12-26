/**
 * CompuEasys Checkout - Versión Nueva y Limpia
 * Versión: 4.0 - SIN COMISIÓN WOMPI
 * - Contra Entrega: Domicilio + Efectivo (envío $15k, gratis > $100k)
 * - Tarjeta + Domicilio: Domicilio + Tarjeta (envío $15k, gratis > $100k)
 * - Recoger Efectivo: Tienda + Efectivo (sin envío)
 * - Recoger Tarjeta: Tienda + Tarjeta (sin envío)
 */

console.log('🚀 CHECKOUT v4.0 - SIN COMISIÓN WOMPI - Cargando...');

(function() {
    "use strict";
    
    // ==========================================
    // CONFIGURACIÓN Y ESTADO GLOBAL
    // ==========================================
    
    let CONFIG = null;
    let checkoutState = {
        selectedOption: 'contra_entrega', // opción por defecto
        subtotal: 0,
        shipping: 0,
        discount: 0,

        total: 0,
        processing: false
    };
    
    const SHIPPING_COST = 15000;
    const FREE_SHIPPING_THRESHOLD = 100000;
    
    // ==========================================
    // INICIALIZACIÓN DE CONFIGURACIÓN
    // ==========================================
    
    function initializeConfig() {
        console.log('🔧 Inicializando configuración...');
        
        let wompiKey = '';
        
        // Obtener clave de Wompi desde window.checkout_config o meta tag
        if (window.checkout_config && window.checkout_config.wompi_public_key) {
            wompiKey = window.checkout_config.wompi_public_key;
        } else {
            const metaKey = document.querySelector('meta[name="wompi-public-key"]');
            if (metaKey) {
                wompiKey = metaKey.getAttribute('content');
            }
        }
        
        CONFIG = {
            wompi_public_key: wompiKey,
            urls: {
                create_transaction: window.checkout_config?.create_transaction_url || '/api/create-wompi-transaction/',
                success: window.checkout_config?.success_url || window.location.origin + '/pago_exitoso/'
            },
            cart_total: window.checkout_config?.cart_total || 0
        };
        
        console.log('✅ Configuración inicializada:', CONFIG);
        return CONFIG;
    }
    
    // ==========================================
    // UTILIDADES
    // ==========================================
    
    function formatCurrency(amount) {
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
    
    // ==========================================
    // LÓGICA DE CÁLCULOS
    // ==========================================
    
    function calculateShipping(option, subtotal) {
        console.log(`📊 Calculando envío - Opción: ${option}, Subtotal: ${subtotal}`);
        
        switch (option) {
            case 'contra_entrega':
            case 'tarjeta_domicilio':
                // Envío a domicilio - gratis si > 100k
                const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_COST;
                console.log(`📦 ${option} - Envío: ${shipping}`);
                return shipping;
                
            case 'recoger_efectivo':
            case 'recoger_tarjeta':
                // Recoger en tienda - siempre gratis
                console.log('🏪 Recoger en tienda - Envío: 0');
                return 0;
                
            default:
                console.warn('⚠️ Opción desconocida:', option);
                return 0;
        }
    }
    
    function updateTotals() {
        console.log('🧮 Actualizando totales...');
        
        // Obtener subtotal del DOM
        const subtotalElement = document.getElementById('subtotal_amount');
        if (!subtotalElement) {
            console.error('❌ Elemento subtotal no encontrado');
            return;
        }
        
        // Extraer valor numérico del subtotal
        const subtotalText = subtotalElement.textContent;
        const subtotalValue = parseInt(subtotalText.replace(/[^0-9]/g, ''));
        
        console.log(`💰 Subtotal extraído: ${subtotalValue} de texto: "${subtotalText}"`);
        
        if (!subtotalValue || subtotalValue <= 0) {
            console.error('❌ Subtotal inválido:', subtotalValue);
            checkoutState.subtotal = 0;
        } else {
            checkoutState.subtotal = subtotalValue;
        }
        
        // Calcular envío según opción seleccionada
        checkoutState.shipping = calculateShipping(checkoutState.selectedOption, checkoutState.subtotal);
        
        // Calcular total (SIN comisión Wompi - eliminada completamente)
        checkoutState.total = checkoutState.subtotal - checkoutState.discount + checkoutState.shipping;
        
        console.log(`🧾 Cálculo final:`);
        console.log(`   Subtotal: ${checkoutState.subtotal}`);
        console.log(`   Descuento: ${checkoutState.discount}`);
        console.log(`   Envío: ${checkoutState.shipping}`);
        console.log(`   TOTAL: ${checkoutState.total}`);
        
        // Actualizar DOM
        updateShippingDisplay();
        updateTotalDisplay();
        updateOptionPrices();
        
        console.log('✅ Totales actualizados:', checkoutState);
    }
    
    function updateShippingDisplay() {
        const shippingElement = document.getElementById('shipping_amount');
        if (shippingElement) {
            if (checkoutState.shipping === 0) {
                shippingElement.textContent = 'GRATIS';
                shippingElement.className = 'shipping-amount free';
            } else {
                shippingElement.textContent = formatCurrency(checkoutState.shipping);
                shippingElement.className = 'shipping-amount';
            }
        }
    }
    

    
    function updateTotalDisplay() {
        const totalElement = document.getElementById('total_final');
        if (totalElement) {
            totalElement.textContent = formatCurrency(checkoutState.total);
        }
    }
    
    function updateOptionPrices() {
        // Actualizar precio mostrado en la opción contra entrega
        const contraEntregaPrice = document.getElementById('contra_entrega_price');
        if (contraEntregaPrice) {
            const shippingForContraEntrega = calculateShipping('contra_entrega', checkoutState.subtotal);
            const shippingSpan = contraEntregaPrice.querySelector('.shipping-cost');
            if (shippingSpan) {
                if (shippingForContraEntrega === 0) {
                    shippingSpan.textContent = 'GRATIS';
                    shippingSpan.className = 'shipping-cost free';
                } else {
                    shippingSpan.textContent = `+ ${formatCurrency(shippingForContraEntrega)}`;
                    shippingSpan.className = 'shipping-cost';
                }
            }
        }
        
        // Actualizar precio mostrado en la opción tarjeta domicilio
        const tarjetaDomicilioPrice = document.getElementById('tarjeta_domicilio_price');
        if (tarjetaDomicilioPrice) {
            const shippingForTarjetaDomicilio = calculateShipping('tarjeta_domicilio', checkoutState.subtotal);
            const shippingSpan = tarjetaDomicilioPrice.querySelector('.shipping-cost');
            if (shippingSpan) {
                if (shippingForTarjetaDomicilio === 0) {
                    shippingSpan.textContent = 'GRATIS';
                    shippingSpan.className = 'shipping-cost free';
                } else {
                    shippingSpan.textContent = `+ ${formatCurrency(shippingForTarjetaDomicilio)}`;
                    shippingSpan.className = 'shipping-cost';
                }
            }
        }
    }
    
    // ==========================================
    // MANEJO DE OPCIONES DE PAGO/ENTREGA
    // ==========================================
    
    function handleOptionChange(selectedOption) {
        console.log(`🔄 Cambiando a opción: ${selectedOption}`);
        
        checkoutState.selectedOption = selectedOption;
        
        // Actualizar clases CSS para indicar selección
        updateOptionSelection();
        
        // Ocultar todas las secciones de información
        hideAllInfoSections();
        
        // Mostrar sección correspondiente
        switch (selectedOption) {
            case 'contra_entrega':
                console.log('📦 Opción: Contra Entrega');
                showMessage('📦 Entrega a domicilio - Pago en efectivo al recibir', 'info');
                break;
                
            case 'tarjeta_domicilio':
                console.log('💳🏠 Opción: Tarjeta + Domicilio');
                showCardInfo();
                showMessage('💳 Pago con tarjeta - Entrega a domicilio', 'info');
                break;
                
            case 'recoger_efectivo':
                console.log('🏪 Opción: Recoger + Efectivo');
                showPickupInfo();
                showMessage('🏪 Recoger en tienda - Pago en efectivo', 'info');
                break;
                
            case 'recoger_tarjeta':
                console.log('💳 Opción: Recoger + Tarjeta');
                showPickupInfo();
                showCardInfo();
                showMessage('💳 Recoger en tienda - Pago con tarjeta', 'info');
                break;
                
            default:
                console.warn('⚠️ Opción desconocida:', selectedOption);
        }
        
        // Actualizar totales
        updateTotals();
    }
    
    function updateOptionSelection() {
        // Remover clase selected de todas las cards
        document.querySelectorAll('.option-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Agregar clase selected a la card correspondiente
        const selectedRadio = document.querySelector(`input[value="${checkoutState.selectedOption}"]`);
        if (selectedRadio) {
            const parentCard = selectedRadio.closest('.option-card');
            if (parentCard) {
                parentCard.classList.add('selected');
                console.log(`✅ Card seleccionada: ${checkoutState.selectedOption}`);
            }
        }
    }
    
    function hideAllInfoSections() {
        const pickupSection = document.getElementById('pickupInfoSection');
        const cardSection = document.getElementById('cardPaymentSection');
        
        if (pickupSection) {
            pickupSection.classList.add('d-none');
        }
        if (cardSection) {
            cardSection.classList.add('d-none');
        }
    }
    
    function showPickupInfo() {
        const pickupSection = document.getElementById('pickupInfoSection');
        if (pickupSection) {
            pickupSection.classList.remove('d-none');
            console.log('✅ Información de punto de recogida mostrada');
        }
    }
    
    function showCardInfo() {
        const cardSection = document.getElementById('cardPaymentSection');
        if (cardSection) {
            cardSection.classList.remove('d-none');
            console.log('✅ Información de pago con tarjeta mostrada');
        }
    }
    
    // ==========================================
    // VERIFICACIÓN DE WOMPI
    // ==========================================
    
    function checkWompiAvailability(callback, maxAttempts = 5, attempt = 1) {
        console.log(`🔍 Verificando Wompi - Intento ${attempt}/${maxAttempts}`);
        
        if (typeof window.WidgetCheckout !== 'undefined') {
            console.log('✅ Wompi disponible');
            if (callback) callback(true);
            return true;
        }
        
        if (attempt >= maxAttempts) {
            console.error('❌ Wompi no disponible después de', maxAttempts, 'intentos');
            if (callback) callback(false);
            return false;
        }
        
        console.log(`⏳ Wompi no disponible, reintentando en 500ms...`);
        setTimeout(() => {
            checkWompiAvailability(callback, maxAttempts, attempt + 1);
        }, 500);
        
        return false;
    }
    
    function processCardPaymentWithRetry() {
        console.log('🔄 Iniciando proceso de pago con verificación de Wompi...');
        
        checkWompiAvailability((isAvailable) => {
            if (isAvailable) {
                processCardPayment();
            } else {
                console.error('❌ Wompi no está disponible');
                showMessage('El sistema de pagos no está disponible. Por favor recarga la página e intenta nuevamente.', 'error');
                setButtonProcessing(false);
                checkoutState.processing = false;
            }
        });
    }
    
    function validateForm() {
        console.log('✅ Validando formulario...');
        
        const requiredFields = ['nombre', 'email', 'telefono', 'cedula'];
        
        // Validar dirección para opciones con entrega a domicilio
        if (checkoutState.selectedOption === 'contra_entrega' || checkoutState.selectedOption === 'tarjeta_domicilio') {
            requiredFields.push('direccion', 'ciudad');
        }
        
        for (let fieldId of requiredFields) {
            const field = document.getElementById(fieldId);
            if (!field || !field.value.trim()) {
                showMessage(`Por favor completa el campo: ${fieldId}`, 'error');
                field?.focus();
                return false;
            }
        }
        
        return true;
    }
    
    function processOrder() {
        console.log('🚀 Procesando pedido...');
        
        if (checkoutState.processing) {
            console.warn('⚠️ Ya se está procesando un pedido');
            return;
        }
        
        if (!validateForm()) {
            console.error('❌ Validación de formulario falló');
            return;
        }
        
        // Actualizar estado del botón
        setButtonProcessing(true);
        checkoutState.processing = true;
        
        console.log(`📋 Procesando opción: ${checkoutState.selectedOption}`);
        console.log(`💰 Total a procesar: ${formatCurrency(checkoutState.total)}`);
        
        switch (checkoutState.selectedOption) {
            case 'contra_entrega':
            case 'recoger_efectivo':
                processStandardPayment();
                break;
                
            case 'tarjeta_domicilio':
            case 'recoger_tarjeta':
                processCardPaymentWithRetry();
                break;
                
            default:
                console.error('❌ Opción de pago desconocida');
                setButtonProcessing(false);
                checkoutState.processing = false;
        }
    }
    
    function setButtonProcessing(isProcessing) {
        const submitBtn = document.getElementById('checkout_submit_btn');
        const submitText = submitBtn?.querySelector('.submit-text');
        const spinner = submitBtn?.querySelector('.btn-spinner');
        
        if (submitBtn) {
            if (isProcessing) {
                submitBtn.classList.add('processing');
                submitBtn.disabled = true;
                if (spinner) spinner.classList.remove('d-none');
            } else {
                submitBtn.classList.remove('processing');
                submitBtn.disabled = false;
                if (spinner) spinner.classList.add('d-none');
            }
        }
    }
    
    function processStandardPayment() {
        console.log('📄 Procesando pago estándar (efectivo)...');
        
        const form = document.getElementById('checkoutForm');
        if (!form) {
            showMessage('Error: Formulario no encontrado', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        // Agregar campos ocultos necesarios
        // Mapear la opción seleccionada a método de pago y forma de entrega
        let metodoPago, formaEntrega;
        
        switch(checkoutState.selectedOption) {
            case 'contra_entrega':
                metodoPago = 'contraentrega';
                formaEntrega = 'domicilio';
                break;
            case 'recoger_efectivo':
                metodoPago = 'recoger_tienda';
                formaEntrega = 'tienda';
                break;
            case 'recoger_tarjeta':
                metodoPago = 'tarjeta';
                formaEntrega = 'tienda';
                break;
            default:
                metodoPago = 'efectivo';
                formaEntrega = 'domicilio';
        }
        
        console.log('📋 Enviando:', { metodoPago, formaEntrega, total: checkoutState.total, shipping: checkoutState.shipping });
        
        addHiddenField(form, 'metodo_pago', metodoPago);
        addHiddenField(form, 'forma_entrega', formaEntrega);
        addHiddenField(form, 'total_final', checkoutState.total);
        addHiddenField(form, 'shipping_cost', checkoutState.shipping);
        
        showMessage('📄 Pedido confirmado! Redirigiendo...', 'success');
        
        setTimeout(() => {
            console.log('📤 Enviando formulario...');
            form.submit();
        }, 1500);
    }
    
    function processCardPayment() {
        console.log('💳 Procesando pago con tarjeta (Wompi)...');
        
        // Validar widget de Wompi
        console.log('🔍 Verificando widget de Wompi...');
        console.log('window.WidgetCheckout:', typeof window.WidgetCheckout);
        
        if (typeof window.WidgetCheckout === 'undefined') {
            console.error('❌ Widget de Wompi no cargado');
            showMessage('Error: El sistema de pagos no está disponible. Por favor recarga la página.', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        if (!CONFIG.wompi_public_key) {
            console.error('❌ Clave pública de Wompi no configurada');
            console.log('CONFIG completo:', CONFIG);
            showMessage('Error: Configuración de pagos incompleta', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        console.log('✅ Validaciones iniciales exitosas');
        console.log('🔑 Public key disponible:', CONFIG.wompi_public_key ? '✅' : '❌');
        
        console.log('✅ Iniciando proceso Wompi...');
        
        const customerEmail = document.getElementById('email')?.value?.trim();
        if (!customerEmail) {
            showMessage('Email requerido para pago con tarjeta', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        // Preparar datos de transacción
        const transactionData = {
            amount: checkoutState.total,
            customer_email: customerEmail,
            pago_entrega: checkoutState.selectedOption,
            shipping_cost: checkoutState.shipping
        };
        
        console.log('📤 Enviando transacción a Wompi:', transactionData);
        console.log('💰 Total del checkout state:', checkoutState.total);
        console.log('📧 Email del cliente:', customerEmail);
        
        // Validar que el total es válido
        if (!checkoutState.total || checkoutState.total <= 0) {
            console.error('❌ Total inválido en checkout state:', checkoutState.total);
            showMessage('Error: Total de la compra inválido', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        // Crear transacción
        fetch(CONFIG.urls.create_transaction, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(transactionData)
        })
        .then(response => {
            console.log(`📡 Response status: ${response.status}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response.json();
        })
        .then(data => {
            console.log('📬 Response data:', data);
            
            if (data.success) {
                console.log('✅ Transacción creada, abriendo widget Wompi');
                console.log('📊 Datos completos para widget:', {
                    amount_in_cents: data.amount_in_cents,
                    reference: data.reference,
                    customer_email: data.customer_email,
                    public_key: data.public_key?.substring(0, 20) + '...',
                    acceptance_token: data.acceptance_token?.substring(0, 20) + '...'
                });
                
                console.log('🔍 DEBUG: Data JSON completo:', JSON.stringify(data, null, 2));
                
                // Validar datos críticos antes de abrir widget
                if (!data.amount_in_cents || data.amount_in_cents <= 0) {
                    console.error('❌ Monto en centavos inválido desde backend:', data.amount_in_cents);
                    showMessage('Error: Monto de transacción inválido desde servidor', 'error');
                    setButtonProcessing(false);
                    checkoutState.processing = false;
                    return;
                }
                
                if (!data.reference) {
                    console.error('❌ Referencia no recibida desde backend');
                    showMessage('Error: Referencia de transacción no recibida', 'error');
                    setButtonProcessing(false);
                    checkoutState.processing = false;
                    return;
                }
                
                if (!data.acceptance_token) {
                    console.error('❌ Acceptance token no recibido correctamente:', data.acceptance_token);
                    showMessage('Error: Token de aceptación no válido', 'error');
                    setButtonProcessing(false);
                    checkoutState.processing = false;
                    return;
                }
                
                if (!data.public_key) {
                    console.error('❌ Public key no recibida desde backend');
                    showMessage('Error: Clave pública no recibida', 'error');
                    setButtonProcessing(false);
                    checkoutState.processing = false;
                    return;
                }
                
                console.log('✅ Todas las validaciones pasaron, abriendo widget...');
                openWompiWidget(data);
            } else {
                console.error('❌ Error creando transacción:', data);
                
                // Mensaje claro para todos los tipos de error
                let errorMessage = 'No se pudo realizar el pago. ';
                
                if (data.error_type === 'timeout') {
                    errorMessage += 'El servicio de pagos no responde. Por favor intenta más tarde o usa otro método de pago.';
                } else if (data.error_type === 'connection') {
                    errorMessage += 'No se pudo conectar con el servicio de pagos. Verifica tu conexión a internet.';
                } else if (data.error_type === 'service_unavailable') {
                    errorMessage += 'El servicio de pagos está temporalmente no disponible. Por favor intenta más tarde o usa otro método de pago.';
                } else if (data.error) {
                    errorMessage += data.error + '. Por favor intenta con otro método de pago.';
                } else {
                    errorMessage += 'Por favor intenta más tarde o usa otro método de pago.';
                }
                
                showMessage(errorMessage, 'error');
                setButtonProcessing(false);
                checkoutState.processing = false;
            }
        })
        .catch(error => {
            console.error('❌ Error de conexión completo:', error);
            
            // Mensaje claro y útil para el usuario
            showMessage('No se pudo realizar el pago. Por favor verifica tu conexión a internet e intenta nuevamente, o usa otro método de pago.', 'error');
            
            setButtonProcessing(false);
            checkoutState.processing = false;
        });
    }
    
    function openWompiWidget(transactionData) {
        console.log('🔓 Abriendo widget de Wompi...');
        console.log('📊 Datos de transacción recibidos:', transactionData);
        
        // Verificar que el widget esté disponible
        if (typeof window.WidgetCheckout === 'undefined') {
            console.error('❌ WidgetCheckout no está definido en window');
            showMessage('Error: Widget de pagos no cargado. Recarga la página.', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        // Usar la public key del backend si está disponible, si no usar la de CONFIG
        const publicKey = transactionData.public_key || CONFIG.wompi_public_key;
        
        // Validar que tenemos los datos necesarios
        if (!transactionData.amount_in_cents || transactionData.amount_in_cents <= 0) {
            console.error('❌ Monto en centavos inválido:', transactionData.amount_in_cents);
            showMessage('Error: Monto de transacción inválido', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        if (!transactionData.reference) {
            console.error('❌ Referencia de transacción faltante');
            showMessage('Error: Referencia de transacción no generada', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        if (!publicKey) {
            console.error('❌ Public key no disponible');
            console.log('Backend key:', transactionData.public_key);
            console.log('CONFIG key:', CONFIG.wompi_public_key);
            showMessage('Error: Clave de configuración faltante', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        if (!transactionData.acceptance_token) {
            console.error('❌ Acceptance token no disponible:', transactionData.acceptance_token);
            showMessage('Error: Token de aceptación no disponible', 'error');
            setButtonProcessing(false);
            checkoutState.processing = false;
            return;
        }
        
        try {
            console.log('🎯 Configurando widget Wompi...');
            console.log('💰 Monto en centavos:', transactionData.amount_in_cents);
            console.log('🔑 Public key:', publicKey?.substring(0, 20) + '...');
            console.log('📄 Reference:', transactionData.reference);
            console.log('📧 Customer email:', transactionData.customer_email);
            
            // Construir URL de redirección completa
            let redirectUrl = CONFIG.urls.success;
            if (!redirectUrl.startsWith('http')) {
                redirectUrl = window.location.origin + redirectUrl;
            }
            console.log('🔗 Redirect URL:', redirectUrl);
            
            const widgetConfig = {
                currency: 'COP',
                amountInCents: parseInt(transactionData.amount_in_cents),
                reference: transactionData.reference,
                publicKey: publicKey,
                redirectUrl: redirectUrl
            };
            
            // Agregar customerEmail si está disponible
            if (transactionData.customer_email) {
                widgetConfig.customerEmail = transactionData.customer_email;
            }
            
            // Agregar acceptance token
            const acceptanceToken = transactionData.acceptance_token;
            widgetConfig.acceptanceToken = acceptanceToken;
            console.log('🔐 Acceptance token agregado:', acceptanceToken.substring(0, 20) + '...');
            
            // Agregar firma de integridad (REQUERIDO en producción)
            if (transactionData.integrity) {
                widgetConfig.signature = {
                    integrity: transactionData.integrity
                };
                console.log('🔐 Firma de integridad agregada:', transactionData.integrity.substring(0, 20) + '...');
            } else {
                console.warn('⚠️ No se recibió firma de integridad. Esto es REQUERIDO en producción.');
            }
            
            console.log('🔧 Configuración final del widget:', {
                ...widgetConfig,
                publicKey: widgetConfig.publicKey?.substring(0, 20) + '...',
                acceptanceToken: widgetConfig.acceptanceToken?.substring(0, 20) + '...'
            });
            
            const widget = new WidgetCheckout(widgetConfig);
            
            console.log('✅ Widget creado exitosamente, abriendo...');
            
            widget.open((result) => {
                console.log('🔄 Callback del widget ejecutado:', result);
                
                // Verificar el resultado del widget
                if (result.transaction) {
                    const status = result.transaction.status;
                    const transactionId = result.transaction.id;
                    console.log('📊 Estado de la transacción:', status);
                    console.log('🔑 ID de transacción:', transactionId);
                    
                    if (status === 'APPROVED') {
                        console.log('✅ Pago aprobado');
                        showMessage('Pago aprobado! Creando tu pedido...', 'success');
                        
                        // Crear el pedido en el backend
                        const form = document.getElementById('checkoutForm');
                        if (form) {
                            // Agregar información de la transacción de Wompi
                            let metodoPago, formaEntrega;
                            
                            switch(checkoutState.selectedOption) {
                                case 'tarjeta_domicilio':
                                    metodoPago = 'wompi_tarjeta';
                                    formaEntrega = 'domicilio';
                                    break;
                                case 'recoger_tarjeta':
                                    metodoPago = 'wompi_tarjeta';
                                    formaEntrega = 'tienda';
                                    break;
                                default:
                                    metodoPago = 'wompi_tarjeta';
                                    formaEntrega = 'domicilio';
                            }
                            
                            addHiddenField(form, 'metodo_pago', metodoPago);
                            addHiddenField(form, 'forma_entrega', formaEntrega);
                            addHiddenField(form, 'total_final', checkoutState.total);
                            addHiddenField(form, 'shipping_cost', checkoutState.shipping);
                            addHiddenField(form, 'wompi_transaction_id', transactionId);
                            addHiddenField(form, 'wompi_reference', transactionData.reference);
                            
                            console.log('📤 Enviando formulario de pedido...');
                            setTimeout(() => {
                                form.submit();
                            }, 1500);
                        } else {
                            console.error('❌ Formulario no encontrado');
                            showMessage('Pago aprobado pero hay un problema. Por favor contacta con soporte citando el ID: ' + transactionId, 'warning');
                            setButtonProcessing(false);
                            checkoutState.processing = false;
                        }
                    } else if (status === 'DECLINED') {
                        console.log('❌ Pago rechazado');
                        showMessage('Tu tarjeta fue rechazada. Por favor verifica los datos o intenta con otra tarjeta.', 'error');
                        setButtonProcessing(false);
                        checkoutState.processing = false;
                    } else if (status === 'ERROR') {
                        console.log('❌ Error en el pago');
                        showMessage('Hubo un error procesando el pago. Por favor intenta nuevamente.', 'error');
                        setButtonProcessing(false);
                        checkoutState.processing = false;
                    } else if (status === 'PENDING') {
                        console.log('⏳ Pago pendiente:', status);
                        showMessage('El pago está en proceso de verificación. Recibirás un correo cuando se confirme.', 'info');
                        setButtonProcessing(false);
                        checkoutState.processing = false;
                    } else {
                        console.log('⏳ Estado desconocido:', status);
                        showMessage('El pago está en proceso. Por favor verifica tu email.', 'info');
                        setButtonProcessing(false);
                        checkoutState.processing = false;
                    }
                } else {
                    console.log('⚠️ Widget cerrado sin resultado');
                    showMessage('Cancelaste el proceso de pago', 'warning');
                    setButtonProcessing(false);
                    checkoutState.processing = false;
                }
            });
            
        } catch (error) {
            console.error('❌ Error configurando widget Wompi:');
            console.error('Error object:', error);
            console.error('Error message:', error?.message || 'Sin mensaje');
            console.error('Error stack:', error?.stack || 'Sin stack trace');
            
            // Mensaje claro para el usuario
            showMessage('No se pudo realizar el pago. El servicio de pagos podría estar temporalmente no disponible. Por favor intenta más tarde o usa otro método de pago.', 'error');
            
            setButtonProcessing(false);
            checkoutState.processing = false;
        }
    }
    
    function addHiddenField(form, name, value) {
        let field = form.querySelector(`input[name="${name}"]`);
        if (!field) {
            field = document.createElement('input');
            field.type = 'hidden';
            field.name = name;
            form.appendChild(field);
        }
        field.value = value;
    }
    
    // ==========================================
    // CONFIGURACIÓN DE EVENT LISTENERS
    // ==========================================
    
    function setupEventListeners() {
        console.log('🎯 Configurando event listeners...');
        
        // Event listeners para opciones de pago/entrega
        const paymentOptions = document.querySelectorAll('input[name="pago_entrega"]');
        paymentOptions.forEach(option => {
            option.addEventListener('change', function() {
                if (this.checked) {
                    handleOptionChange(this.value);
                }
            });
        });
        
        // Event listener para botón de confirmar
        const submitBtn = document.getElementById('checkout_submit_btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', function(e) {
                e.preventDefault();
                processOrder();
            });
            console.log('✅ Event listener del botón configurado');
        }
        
        console.log(`✅ ${paymentOptions.length} opciones de pago configuradas`);
    }
    
    // ==========================================
    // INICIALIZACIÓN
    // ==========================================
    
    function init() {
        console.log('🚀 Iniciando CompuEasys Checkout v4.0...');
        
        // Inicializar configuración
        CONFIG = initializeConfig();
        
        // Verificar elementos esenciales
        const form = document.getElementById('checkoutForm');
        const subtotal = document.getElementById('subtotal_amount');
        const submitBtn = document.getElementById('checkout_submit_btn');
        
        console.group('🔍 Verificación de elementos DOM');
        console.log('Formulario:', form ? '✅' : '❌');
        console.log('Subtotal:', subtotal ? '✅' : '❌');
        console.log('Botón submit:', submitBtn ? '✅' : '❌');
        console.log('Widget Wompi:', window.WidgetCheckout ? '✅' : '❌');
        console.groupEnd();
        
        if (!form || !subtotal || !submitBtn) {
            console.error('❌ Elementos esenciales faltantes');
            return;
        }
        
        // Configurar event listeners
        setupEventListeners();
        
        // Inicializar totales
        updateTotals();
        
        // Configurar opción inicial
        handleOptionChange('contra_entrega');
        
        console.log('✅ Checkout inicializado correctamente');
        
        // Debug de configuración para Wompi
        console.group('🔍 Debug Configuración Wompi');
        console.log('CONFIG completo:', CONFIG);
        console.log('Widget disponible:', !!window.WidgetCheckout);
        console.log('Tipo de WidgetCheckout:', typeof window.WidgetCheckout);
        console.log('WidgetCheckout constructor:', window.WidgetCheckout);
        console.log('Public key:', CONFIG.wompi_public_key ? `${CONFIG.wompi_public_key.substring(0, 20)}...` : 'NO CONFIGURADA');
        console.log('URLs:', CONFIG.urls);
        console.groupEnd();
        
        // Verificar si el script de Wompi se cargó correctamente
        if (typeof window.WidgetCheckout === 'undefined') {
            console.error('❌ CRITICAL: Widget de Wompi no se cargó');
            console.log('🔧 Intentando cargar widget de Wompi...');
            
            // Intentar cargar el script dinámicamente si no está disponible
            const script = document.createElement('script');
            script.src = 'https://checkout.wompi.co/widget.js';
            script.onload = () => {
                console.log('✅ Script de Wompi cargado dinámicamente');
            };
            script.onerror = () => {
                console.error('❌ Error cargando script de Wompi');
            };
            document.head.appendChild(script);
        }
        
        // Exponer funciones para debugging
        window.CheckoutDebug = {
            state: checkoutState,
            config: CONFIG,
            updateTotals: updateTotals,
            test: () => {
                console.log('🧪 Estado del checkout:', checkoutState);
                console.log('🧪 Configuración:', CONFIG);
            }
        };
    }
    
    // ==========================================
    // PUNTO DE ENTRADA
    // ==========================================
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

console.log('✅ CHECKOUT v4.0 - Script cargado');