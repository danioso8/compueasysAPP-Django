/**
 * ===== CHECKOUT MODERNO COMPUEASYS =====
 * Sistema avanzado de checkout con códigos de descuento
 */

(function() {
    'use strict';
    
    // ===== CONFIGURACIÓN =====
    const CONFIG = {
        selectors: {
            discountCode: '#discount_code',
            applyButton: '#apply_discount_btn',
            discountFeedback: '#discount_feedback',
            discountRow: '#discount_row',
            discountAmountDisplay: '#discount_amount_display',
            discountCodeApplied: '#discount_code_applied',
            subtotalAmount: '#subtotal_amount',
            shippingAmount: '#shipping_amount',
            totalFinal: '#total_final',
            checkoutForm: '#checkoutForm',
            submitButton: '#checkout_submit_btn',
            deliveryOptions: 'input[name="entrega_opcion"]',
            addressSection: '#addressSection',
            discountAppliedValue: '#discountAppliedValue',
            discountAmountValue: '#discountAmountValue',
            // Nuevos selectores para pagos
            paymentOptions: 'input[name="metodo_pago"]',
            cardPaymentSection: '#cardPaymentSection',
            cardElement: '#card-element',
            cardErrors: '#card-errors'
        },
        
        // Códigos de descuento predefinidos
        discountCodes: {
            'COMPUEASYS10': { 
                type: 'percentage', 
                value: 10, 
                description: '10% de descuento',
                minAmount: 50000 
            },
            'COMPUEASYS15': { 
                type: 'percentage', 
                value: 15, 
                description: '15% de descuento',
                minAmount: 100000 
            },
            'COMPUEASYS20': { 
                type: 'percentage', 
                value: 20, 
                description: '20% de descuento',
                minAmount: 200000 
            },
            'ENVIOGRATIS': { 
                type: 'shipping', 
                value: 0, 
                description: 'Envío gratuito',
                minAmount: 0 
            },
            'WELCOME5000': { 
                type: 'fixed', 
                value: 5000, 
                description: '$5.000 de descuento',
                minAmount: 30000 
            },
            'WELCOME10000': { 
                type: 'fixed', 
                value: 10000, 
                description: '$10.000 de descuento',
                minAmount: 50000 
            },
            'BLACK25': { 
                type: 'percentage', 
                value: 25, 
                description: '25% de descuento Black Friday',
                minAmount: 150000 
            },
            'CYBER30': { 
                type: 'percentage', 
                value: 30, 
                description: '30% de descuento Cyber Monday',
                minAmount: 250000 
            }
        },
        
        animation: {
            duration: 300,
            easing: 'ease-in-out'
        },
        
        messages: {
            invalidCode: '❌ Código de descuento inválido',
            minAmountNotReached: '❌ Monto mínimo no alcanzado para este descuento',
            discountApplied: '✅ Descuento aplicado correctamente',
            processingOrder: 'Procesando pedido...',
            validatingCode: 'Validando código...'
        }
    };
    
    // ===== ESTADO GLOBAL =====
    let state = {
        appliedDiscount: null,
        originalSubtotal: window.checkoutConfig?.cart_total || 0,
        shippingCost: window.checkoutConfig?.shipping_cost || 15000,
        freeShippingThreshold: window.checkoutConfig?.free_shipping_threshold || 100000,
        isProcessing: false,
        // Nuevos estados para Stripe
        stripe: null,
        elements: null,
        cardElement: null,
        paymentIntent: null,
        selectedPaymentMethod: 'contraentrega'
    };
    
    // ===== UTILIDADES =====
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    function formatCurrency(amount) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount).replace('COP', '$');
    }
    
    function safeEl(selector) {
        const element = document.querySelector(selector);
        if (!element) {
            console.warn(`Elemento no encontrado: ${selector}`);
        }
        return element;
    }
    
    function showFeedback(message, type = 'info', duration = 5000) {
        const feedbackEl = safeEl(CONFIG.selectors.discountFeedback);
        if (!feedbackEl) return;
        
        feedbackEl.textContent = message;
        feedbackEl.className = `discount-feedback ${type}`;
        feedbackEl.style.opacity = '1';
        
        if (duration > 0) {
            setTimeout(() => {
                feedbackEl.style.opacity = '0';
                setTimeout(() => {
                    feedbackEl.textContent = '';
                    feedbackEl.className = 'discount-feedback';
                }, 300);
            }, duration);
        }
    }
    
    function setButtonLoading(button, isLoading, loadingText = '') {
        if (!button) return;
        
        const textElement = button.querySelector('.btn-text') || button;
        const spinnerElement = button.querySelector('.btn-spinner');
        
        if (isLoading) {
            button.classList.add('loading');
            button.disabled = true;
            if (loadingText) textElement.textContent = loadingText;
            if (spinnerElement) spinnerElement.classList.remove('d-none');
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            if (spinnerElement) spinnerElement.classList.add('d-none');
        }
    }
    
    // ===== CÁLCULO DE TOTALES =====
    function calculateTotals() {
        const discountData = state.appliedDiscount;
        let subtotal = state.originalSubtotal;
        let discountAmount = 0;
        let shippingCost = state.shippingCost;
        
        // Aplicar descuento
        if (discountData) {
            switch (discountData.type) {
                case 'percentage':
                    discountAmount = Math.floor(subtotal * (discountData.value / 100));
                    break;
                case 'fixed':
                    discountAmount = discountData.value;
                    break;
                case 'shipping':
                    shippingCost = 0; // Envío gratis
                    break;
            }
        }
        
        // Verificar envío gratis por monto
        if (subtotal >= state.freeShippingThreshold) {
            shippingCost = 0;
        }
        
        const finalTotal = Math.max(0, subtotal - discountAmount + shippingCost);
        
        return {
            subtotal,
            discountAmount,
            shippingCost,
            finalTotal
        };
    }
    
    function updateTotalDisplay() {
        const totals = calculateTotals();
        
        // Actualizar elementos del DOM
        const subtotalEl = safeEl(CONFIG.selectors.subtotalAmount);
        const discountRowEl = safeEl(CONFIG.selectors.discountRow);
        const discountAmountEl = safeEl(CONFIG.selectors.discountAmountDisplay);
        const discountCodeEl = safeEl(CONFIG.selectors.discountCodeApplied);
        const shippingEl = safeEl(CONFIG.selectors.shippingAmount);
        const totalEl = safeEl(CONFIG.selectors.totalFinal);
        
        if (subtotalEl) subtotalEl.textContent = formatCurrency(totals.subtotal);
        
        if (discountRowEl && discountAmountEl && discountCodeEl) {
            if (state.appliedDiscount && totals.discountAmount > 0) {
                discountRowEl.classList.remove('d-none');
                discountAmountEl.textContent = `-${formatCurrency(totals.discountAmount)}`;
                discountCodeEl.textContent = state.appliedDiscount.code;
            } else {
                discountRowEl.classList.add('d-none');
            }
        }
        
        if (shippingEl) {
            shippingEl.innerHTML = totals.shippingCost === 0 ? 
                '<span class="text-success">Gratis</span>' : 
                formatCurrency(totals.shippingCost);
        }
        
        if (totalEl) totalEl.textContent = formatCurrency(totals.finalTotal);
        
        // Actualizar campos ocultos para el formulario
        const discountAppliedEl = safeEl(CONFIG.selectors.discountAppliedValue);
        const discountAmountValueEl = safeEl(CONFIG.selectors.discountAmountValue);
        
        if (discountAppliedEl) {
            discountAppliedEl.value = state.appliedDiscount ? state.appliedDiscount.code : '';
        }
        if (discountAmountValueEl) {
            discountAmountValueEl.value = totals.discountAmount;
        }
    }
    
    // ===== GESTIÓN DE DESCUENTOS =====
    function validateDiscountCode(code) {
        if (!code || typeof code !== 'string') {
            return { valid: false, error: CONFIG.messages.invalidCode };
        }
        
        const upperCode = code.trim().toUpperCase();
        const discountData = CONFIG.discountCodes[upperCode];
        
        if (!discountData) {
            return { valid: false, error: CONFIG.messages.invalidCode };
        }
        
        if (state.originalSubtotal < discountData.minAmount) {
            return { 
                valid: false, 
                error: `${CONFIG.messages.minAmountNotReached}. Mínimo: ${formatCurrency(discountData.minAmount)}` 
            };
        }
        
        return { 
            valid: true, 
            data: { 
                ...discountData, 
                code: upperCode 
            } 
        };
    }
    
    async function applyDiscountCode() {
        const codeInput = safeEl(CONFIG.selectors.discountCode);
        const applyBtn = safeEl(CONFIG.selectors.applyButton);
        
        if (!codeInput || state.isProcessing) return;
        
        const code = codeInput.value.trim();
        
        if (!code) {
            showFeedback('Por favor ingresa un código de descuento', 'error');
            codeInput.focus();
            return;
        }
        
        state.isProcessing = true;
        setButtonLoading(applyBtn, true, 'Aplicando...');
        showFeedback(CONFIG.messages.validatingCode, 'info', 0);
        
        try {
            // Simular delay de validación
            await new Promise(resolve => setTimeout(resolve, 800));
            
            const validation = validateDiscountCode(code);
            
            if (validation.valid) {
                state.appliedDiscount = validation.data;
                updateTotalDisplay();
                
                showFeedback(
                    `${CONFIG.messages.discountApplied}: ${validation.data.description}`,
                    'success'
                );
                
                // Deshabilitar input y cambiar botón
                codeInput.disabled = true;
                codeInput.style.background = '#e8f5e8';
                if (applyBtn) {
                    applyBtn.textContent = 'Aplicado ✓';
                    applyBtn.classList.replace('btn-outline-primary', 'btn-success');
                    applyBtn.disabled = true;
                }
                
                // Mostrar animación de éxito
                animateSuccess();
                
            } else {
                showFeedback(validation.error, 'error');
                codeInput.value = '';
                codeInput.focus();
            }
            
        } catch (error) {
            console.error('Error applying discount:', error);
            showFeedback('Error al aplicar descuento. Inténtalo de nuevo.', 'error');
        } finally {
            state.isProcessing = false;
            setButtonLoading(applyBtn, false);
        }
    }
    
    function animateSuccess() {
        const discountRow = safeEl(CONFIG.selectors.discountRow);
        if (discountRow) {
            discountRow.style.transform = 'scale(1.05)';
            discountRow.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                discountRow.style.transform = 'scale(1)';
            }, 300);
        }
    }
    
    // ===== GESTIÓN DE PAGOS CON STRIPE =====
    function initializeStripe() {
        if (!window.checkoutConfig?.stripe_publishable_key || typeof Stripe === 'undefined') {
            console.warn('Stripe no está configurado correctamente');
            return false;
        }
        
        try {
            state.stripe = Stripe(window.checkoutConfig.stripe_publishable_key);
            state.elements = state.stripe.elements({
                locale: 'es'
            });
            
            setupCardElement();
            console.log('✅ Stripe inicializado correctamente');
            return true;
        } catch (error) {
            console.error('Error inicializando Stripe:', error);
            return false;
        }
    }
    
    function setupCardElement() {
        const cardElementContainer = safeEl(CONFIG.selectors.cardElement);
        if (!cardElementContainer || !state.elements) return;
        
        // Configuración del elemento de tarjeta
        const cardElementOptions = {
            style: {
                base: {
                    fontSize: '16px',
                    color: '#343a40',
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    '::placeholder': {
                        color: '#6c757d'
                    },
                    iconColor: '#405cdb'
                },
                invalid: {
                    color: '#dc3545',
                    iconColor: '#dc3545'
                },
                complete: {
                    color: '#28a745',
                    iconColor: '#28a745'
                }
            },
            hidePostalCode: true
        };
        
        state.cardElement = state.elements.create('card', cardElementOptions);
        state.cardElement.mount(CONFIG.selectors.cardElement);
        
        // Event listeners para el elemento de tarjeta
        state.cardElement.on('change', handleCardChange);
        state.cardElement.on('ready', () => {
            console.log('💳 Card Element está listo');
        });
    }
    
    function handleCardChange(event) {
        const cardErrorsEl = safeEl(CONFIG.selectors.cardErrors);
        if (!cardErrorsEl) return;
        
        if (event.error) {
            cardErrorsEl.textContent = event.error.message;
            cardErrorsEl.style.opacity = '1';
        } else {
            cardErrorsEl.textContent = '';
            cardErrorsEl.style.opacity = '0';
        }
        
        // Actualizar estado visual del elemento
        const cardElementContainer = safeEl(CONFIG.selectors.cardElement);
        if (cardElementContainer) {
            if (event.error) {
                cardElementContainer.classList.add('has-error');
            } else {
                cardElementContainer.classList.remove('has-error');
            }
            
            if (event.complete) {
                cardElementContainer.classList.add('complete');
            } else {
                cardElementContainer.classList.remove('complete');
            }
        }
    }
    
    async function createPaymentIntent() {
        if (!window.checkoutConfig?.create_payment_intent_url) {
            throw new Error('URL de Payment Intent no configurada');
        }
        
        const totals = calculateTotals();
        const requestData = {
            amount: totals.finalTotal,
            currency: 'cop',
            discount_code: state.appliedDiscount?.code || '',
            discount_amount: totals.discountAmount
        };
        
        try {
            const response = await fetch(window.checkoutConfig.create_payment_intent_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            return data;
        } catch (error) {
            console.error('Error creando Payment Intent:', error);
            throw error;
        }
    }
    
    async function processCardPayment() {
        if (!state.stripe || !state.cardElement) {
            throw new Error('Stripe no está inicializado');
        }
        
        try {
            // Crear Payment Intent
            showFeedback('Procesando pago...', 'info', 0);
            const paymentIntentData = await createPaymentIntent();
            
            // Obtener datos del formulario para el billing
            const form = safeEl(CONFIG.selectors.checkoutForm);
            const formData = new FormData(form);
            
            const billingDetails = {
                name: formData.get('nombre') || '',
                email: formData.get('email') || '',
                phone: formData.get('telefono') || '',
                address: {
                    line1: formData.get('direccion') || '',
                    city: formData.get('ciudad') || '',
                    state: formData.get('departament') || '',
                    postal_code: formData.get('codigo_postal') || '',
                    country: 'CO'
                }
            };
            
            // Confirmar el pago
            const { error: stripeError, paymentIntent } = await state.stripe.confirmCardPayment(
                paymentIntentData.client_secret,
                {
                    payment_method: {
                        card: state.cardElement,
                        billing_details: billingDetails
                    }
                }
            );
            
            if (stripeError) {
                throw new Error(stripeError.message);
            }
            
            if (paymentIntent.status === 'succeeded') {
                // Agregar payment_intent_id al formulario
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'payment_intent_id';
                hiddenInput.value = paymentIntent.id;
                form.appendChild(hiddenInput);
                
                showFeedback('¡Pago procesado exitosamente!', 'success', 2000);
                return { success: true, paymentIntent };
            } else {
                throw new Error('El pago no pudo ser procesado');
            }
            
        } catch (error) {
            console.error('Error procesando pago:', error);
            showFeedback(`Error en el pago: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // ===== GESTIÓN DE MÉTODOS DE PAGO =====
    function handlePaymentMethodChange() {
        const paymentOptions = document.querySelectorAll(CONFIG.selectors.paymentOptions);
        const cardPaymentSection = safeEl(CONFIG.selectors.cardPaymentSection);
        
        if (!paymentOptions.length || !cardPaymentSection) return;
        
        const selectedMethod = Array.from(paymentOptions).find(radio => radio.checked);
        state.selectedPaymentMethod = selectedMethod ? selectedMethod.value : 'contraentrega';
        
        if (state.selectedPaymentMethod === 'tarjeta') {
            // Mostrar sección de tarjeta
            cardPaymentSection.classList.remove('d-none');
            cardPaymentSection.style.opacity = '0';
            cardPaymentSection.style.transform = 'translateY(-10px)';
            
            // Animar entrada
            setTimeout(() => {
                cardPaymentSection.style.transition = 'all 0.3s ease';
                cardPaymentSection.style.opacity = '1';
                cardPaymentSection.style.transform = 'translateY(0)';
            }, 50);
            
            // Inicializar Stripe si no está inicializado
            if (!state.stripe) {
                initializeStripe();
            }
        } else {
            // Ocultar sección de tarjeta
            cardPaymentSection.style.transition = 'all 0.3s ease';
            cardPaymentSection.style.opacity = '0';
            cardPaymentSection.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                cardPaymentSection.classList.add('d-none');
            }, 300);
        }
        
        console.log('💳 Método de pago seleccionado:', state.selectedPaymentMethod);
    }
    
    // ===== GESTIÓN DE ENTREGA =====
    function handleDeliveryOptionChange() {
        const addressSection = safeEl(CONFIG.selectors.addressSection);
        const deliveryOptions = document.querySelectorAll(CONFIG.selectors.deliveryOptions);
        
        if (!addressSection || !deliveryOptions.length) return;
        
        const selectedOption = Array.from(deliveryOptions).find(radio => radio.checked);
        const isDomicilio = selectedOption && selectedOption.value === 'domicilio';
        
        // Mostrar/ocultar sección de dirección
        if (isDomicilio) {
            addressSection.style.display = 'block';
            addressSection.style.opacity = '1';
            addressSection.style.transform = 'translateY(0)';
        } else {
            addressSection.style.opacity = '0.5';
            addressSection.style.transform = 'translateY(-10px)';
            // No ocultar completamente para mantener validación
        }
        
        // Actualizar costos de envío
        if (selectedOption && selectedOption.value === 'recoger_tienda') {
            state.shippingCost = 0;
        } else {
            state.shippingCost = window.checkoutConfig?.shipping_cost || 15000;
        }
        
        updateTotalDisplay();
    }
    
    // ===== VALIDACIÓN DE FORMULARIO =====
    function validateForm() {
        const form = safeEl(CONFIG.selectors.checkoutForm);
        if (!form) return false;
        
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        let firstInvalidField = null;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalidField) firstInvalidField = field;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        // Validaciones específicas
        const emailField = safeEl('#email');
        if (emailField && emailField.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailField.value)) {
                emailField.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalidField) firstInvalidField = emailField;
            }
        }
        
        const cedulaField = safeEl('#cedula');
        if (cedulaField && cedulaField.value) {
            const cedulaRegex = /^\d{7,10}$/;
            if (!cedulaRegex.test(cedulaField.value.replace(/\D/g, ''))) {
                cedulaField.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalidField) firstInvalidField = cedulaField;
            }
        }
        
        if (!isValid && firstInvalidField) {
            firstInvalidField.focus();
            firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        return isValid;
    }
    
    async function handleFormSubmit(event) {
        if (state.isProcessing) {
            event.preventDefault();
            return;
        }
        
        if (!validateForm()) {
            event.preventDefault();
            showFeedback('Por favor completa todos los campos requeridos correctamente', 'error');
            return;
        }
        
        const submitBtn = safeEl(CONFIG.selectors.submitButton);
        state.isProcessing = true;
        setButtonLoading(submitBtn, true, CONFIG.messages.processingOrder);
        
        try {
            // Si es pago con tarjeta, procesar el pago primero
            if (state.selectedPaymentMethod === 'tarjeta') {
                event.preventDefault(); // Prevenir envío normal del formulario
                
                const paymentResult = await processCardPayment();
                
                if (paymentResult.success) {
                    // Una vez procesado el pago, enviar el formulario
                    showFeedback('Finalizando pedido...', 'success', 0);
                    
                    // Simular un pequeño delay para mostrar el mensaje
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Enviar el formulario programáticamente
                    const form = safeEl(CONFIG.selectors.checkoutForm);
                    if (form) {
                        form.submit();
                    }
                }
            } else {
                // Para pago contra entrega, proceder normalmente
                showFeedback('Procesando pedido...', 'info', 0);
                await new Promise(resolve => setTimeout(resolve, 1000));
                showFeedback('Redirigiendo a confirmación...', 'success', 2000);
                // El formulario se enviará normalmente
            }
            
        } catch (error) {
            event.preventDefault();
            console.error('Error processing order:', error);
            showFeedback('Error al procesar el pedido. Inténtalo de nuevo.', 'error');
            state.isProcessing = false;
            setButtonLoading(submitBtn, false);
        }
    }
    
    // ===== EVENT LISTENERS =====
    function setupEventListeners() {
        // Aplicar descuento
        const applyBtn = safeEl(CONFIG.selectors.applyButton);
        if (applyBtn) {
            applyBtn.addEventListener('click', applyDiscountCode);
        }
        
        // Enter en campo de descuento
        const codeInput = safeEl(CONFIG.selectors.discountCode);
        if (codeInput) {
            codeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    applyDiscountCode();
                }
            });
            
            // Limpiar estado cuando se modifica el código
            codeInput.addEventListener('input', () => {
                if (state.appliedDiscount) {
                    // Resetear estado si se está editando un código ya aplicado
                    const applyButton = safeEl(CONFIG.selectors.applyButton);
                    if (applyButton) {
                        applyButton.textContent = 'Aplicar';
                        applyButton.classList.replace('btn-success', 'btn-outline-primary');
                        applyButton.disabled = false;
                    }
                    codeInput.disabled = false;
                    codeInput.style.background = '';
                    
                    state.appliedDiscount = null;
                    updateTotalDisplay();
                    showFeedback('', 'info', 0); // Limpiar feedback
                }
            });
        }
        
        // Opciones de entrega
        const deliveryOptions = document.querySelectorAll(CONFIG.selectors.deliveryOptions);
        deliveryOptions.forEach(option => {
            option.addEventListener('change', handleDeliveryOptionChange);
        });
        
        // Opciones de pago
        const paymentOptions = document.querySelectorAll(CONFIG.selectors.paymentOptions);
        paymentOptions.forEach(option => {
            option.addEventListener('change', handlePaymentMethodChange);
        });
        
        // Submit del formulario
        const form = safeEl(CONFIG.selectors.checkoutForm);
        if (form) {
            form.addEventListener('submit', handleFormSubmit);
        }
        
        // Validación en tiempo real
        const inputs = form?.querySelectorAll('input, select');
        inputs?.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.hasAttribute('required')) {
                    if (input.value.trim()) {
                        input.classList.remove('is-invalid');
                        input.classList.add('is-valid');
                    } else {
                        input.classList.remove('is-valid');
                        input.classList.add('is-invalid');
                    }
                }
            });
            
            input.addEventListener('input', () => {
                input.classList.remove('is-invalid', 'is-valid');
            });
        });
    }
    
    // ===== INICIALIZACIÓN =====
    function init() {
        console.log('🛒 Inicializando Checkout Moderno CompuEasys con Stripe');
        
        // Configurar estado inicial
        updateTotalDisplay();
        handleDeliveryOptionChange();
        handlePaymentMethodChange(); // Inicializar estado de pago
        
        // Configurar event listeners
        setupEventListeners();
        
        // Animaciones de entrada
        const sections = document.querySelectorAll('.checkout-section');
        sections.forEach((section, index) => {
            section.style.animationDelay = `${index * 100}ms`;
        });
        
        console.log('✅ Checkout inicializado correctamente');
        console.log('💰 Subtotal:', formatCurrency(state.originalSubtotal));
        console.log('🎁 Códigos disponibles:', Object.keys(CONFIG.discountCodes));
        console.log('💳 Stripe configurado:', !!window.checkoutConfig?.stripe_publishable_key);
    }
    
    // ===== INICIO AUTOMÁTICO =====
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // ===== EXPOSICIÓN GLOBAL PARA DEBUGGING =====
    window.CheckoutManager = {
        state,
        config: CONFIG,
        validateDiscountCode,
        applyDiscountCode,
        calculateTotals,
        updateTotalDisplay
    };
    
})();