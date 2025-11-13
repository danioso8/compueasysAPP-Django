/**
 * CompuEasys Checkout con Wompi Integration
 * Versión: 2.0 - Optimizada para Wompi Colombia
 */

(function () {
  "use strict";

  // Configuración global
  console.log('🔧 Configuración inicial:', window.checkout_config);
  const CONFIG = {
    wompi_public_key: window.checkout_config?.wompi_public_key || '',
    urls: {
      create_transaction: window.checkout_config?.create_transaction_url || '/api/create-wompi-transaction/',
      pago_exitoso: '/pago_exitoso/'
    }
  };
  
  console.log('🔧 CONFIG final:', CONFIG);

  // Estado global del checkout
  let checkoutState = {
    selectedPayment: 'contraentrega',
    discountApplied: false,
    discountCode: '',
    discountAmount: 0,
    cartTotal: 0,
    finalTotal: 0,
    shipping: 0,
    subtotal: 0,
    isProcessing: false
  };

  // Utilidades
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function safeEl(selector) {
    const element = document.querySelector(selector);
    if (!element) {
      console.warn(`🚨 Elemento no encontrado: ${selector}`);
    }
    return element;
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      minimumFractionDigits: 0,
    }).format(amount);
  }

  function showToast(message, type = 'info') {
    const toastConfig = {
      icon: type,
      title: message,
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
    };

    if (type === 'success') {
      toastConfig.iconColor = '#28a745';
    } else if (type === 'error') {
      toastConfig.iconColor = '#dc3545';
    }

    Swal.fire(toastConfig);
  }

  function showLoading(show = true) {
    const overlay = safeEl('#loading-overlay');
    if (overlay) {
      overlay.style.display = show ? 'flex' : 'none';
    }
  }

  // Validación de formularios
  function validateCheckoutForm() {
    const requiredFields = [
      { id: 'nombre', name: 'Nombre completo' },
      { id: 'email', name: 'Email' },
      { id: 'telefono', name: 'Teléfono' },
      { id: 'direccion', name: 'Dirección' },
      { id: 'ciudad', name: 'Ciudad' },
      { id: 'departament', name: 'Departamento' }
    ];

    for (const field of requiredFields) {
      const element = safeEl(`#${field.id}`);
      if (!element || !element.value.trim()) {
        showToast(`Por favor completa el campo: ${field.name}`, 'error');
        if (element) element.focus();
        return false;
      }
    }

    // Validar email
    const email = safeEl('#email')?.value;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showToast('Por favor ingresa un email válido', 'error');
      safeEl('#email')?.focus();
      return false;
    }

    // Validar teléfono (Colombia)
    const telefono = safeEl('#telefono')?.value;
    const phoneRegex = /^[0-9]{10}$/;
    if (!phoneRegex.test(telefono.replace(/\s+/g, ''))) {
      showToast('Por favor ingresa un número de teléfono válido (10 dígitos)', 'error');
      safeEl('#telefono')?.focus();
      return false;
    }

    return true;
  }

  // Cálculos de totales
  function calculateTotals() {
    try {
      const subtotalElement = safeEl('.cart-subtotal');
      if (!subtotalElement) return;

      // Obtener subtotal del carrito
      const subtotalText = subtotalElement.textContent || '0';
      checkoutState.subtotal = parseFloat(subtotalText.replace(/[^0-9]/g, ''));

      // Aplicar descuento
      let discountAmount = 0;
      if (checkoutState.discountApplied) {
        discountAmount = checkoutState.discountAmount;
      }

      // Calcular envío
      const shippingCost = checkoutState.subtotal >= 100000 ? 0 : 15000;
      checkoutState.shipping = shippingCost;

      // Calcular total final
      checkoutState.finalTotal = checkoutState.subtotal - discountAmount + shippingCost;
      checkoutState.cartTotal = checkoutState.finalTotal;

      // Actualizar UI
      updateTotalsDisplay();

    } catch (error) {
      console.error('Error calculating totals:', error);
    }
  }

  function updateTotalsDisplay() {
    // Actualizar subtotal
    const subtotalEl = safeEl('.total-subtotal');
    if (subtotalEl) {
      subtotalEl.textContent = formatCurrency(checkoutState.subtotal);
    }

    // Actualizar descuento
    const discountEl = safeEl('.total-discount');
    if (discountEl) {
      if (checkoutState.discountApplied && checkoutState.discountAmount > 0) {
        discountEl.textContent = `-${formatCurrency(checkoutState.discountAmount)}`;
        discountEl.closest('.discount-row')?.style.setProperty('display', 'flex');
      } else {
        discountEl.closest('.discount-row')?.style.setProperty('display', 'none');
      }
    }

    // Actualizar envío
    const shippingEl = safeEl('.total-shipping');
    if (shippingEl) {
      shippingEl.textContent = checkoutState.shipping > 0 ? formatCurrency(checkoutState.shipping) : 'GRATIS';
    }

    // Actualizar total final
    const totalEl = safeEl('.total-amount');
    if (totalEl) {
      totalEl.textContent = formatCurrency(checkoutState.finalTotal);
    }
  }

  // Manejo de códigos de descuento
  function applyDiscount() {
    const codeInput = safeEl('#discount-code');
    if (!codeInput) return;

    const code = codeInput.value.trim().toUpperCase();
    
    if (!code) {
      showToast('Por favor ingresa un código de descuento', 'error');
      return;
    }

    // Códigos válidos (puedes cambiarlos según tus necesidades)
    const validCodes = {
      'COMPUEASYS10': { type: 'percentage', value: 10 },
      'DESCUENTO15': { type: 'percentage', value: 15 },
      'WELCOME20': { type: 'percentage', value: 20 },
      'FIRST5000': { type: 'fixed', value: 5000 },
      'SAVE10000': { type: 'fixed', value: 10000 }
    };

    if (validCodes[code]) {
      const discount = validCodes[code];
      let discountAmount = 0;

      if (discount.type === 'percentage') {
        discountAmount = Math.round(checkoutState.subtotal * (discount.value / 100));
      } else if (discount.type === 'fixed') {
        discountAmount = Math.min(discount.value, checkoutState.subtotal);
      }

      checkoutState.discountApplied = true;
      checkoutState.discountCode = code;
      checkoutState.discountAmount = discountAmount;

      // Actualizar UI del código
      const discountSection = safeEl('.discount-input-section');
      const appliedSection = safeEl('.discount-applied-section');
      
      if (discountSection && appliedSection) {
        discountSection.style.display = 'none';
        appliedSection.style.display = 'flex';
        
        const appliedCodeEl = safeEl('.applied-discount-code');
        const appliedAmountEl = safeEl('.applied-discount-amount');
        
        if (appliedCodeEl) appliedCodeEl.textContent = code;
        if (appliedAmountEl) {
          appliedAmountEl.textContent = discount.type === 'percentage' 
            ? `-${discount.value}%` 
            : `-${formatCurrency(discountAmount)}`;
        }
      }

      calculateTotals();
      showToast(`¡Descuento aplicado! ${formatCurrency(discountAmount)} de descuento`, 'success');

    } else {
      showToast('Código de descuento inválido', 'error');
    }
  }

  function removeDiscount() {
    checkoutState.discountApplied = false;
    checkoutState.discountCode = '';
    checkoutState.discountAmount = 0;

    // Restaurar UI
    const discountSection = safeEl('.discount-input-section');
    const appliedSection = safeEl('.discount-applied-section');
    
    if (discountSection && appliedSection) {
      discountSection.style.display = 'flex';
      appliedSection.style.display = 'none';
    }

    const codeInput = safeEl('#discount-code');
    if (codeInput) codeInput.value = '';

    calculateTotals();
    showToast('Descuento removido', 'info');
  }

  // Wompi Integration
  function initializeWompi(transactionData) {
    if (!window.WidgetCheckout) {
      console.error('Wompi Widget no está disponible');
      showToast('Error: Widget de pagos no disponible', 'error');
      return;
    }

    const checkout = new WidgetCheckout({
      currency: 'COP',
      amountInCents: transactionData.amount_in_cents,
      reference: transactionData.reference,
      publicKey: CONFIG.wompi_public_key,
      customerData: {
        email: transactionData.customer_email,
        fullName: safeEl('#nombre')?.value || '',
        phoneNumber: safeEl('#telefono')?.value || '',
      },
      shippingAddress: {
        addressLine1: safeEl('#direccion')?.value || '',
        city: safeEl('#ciudad')?.value || '',
        region: safeEl('#departament')?.value || '',
        postalCode: safeEl('#codigo_postal')?.value || '',
        country: 'CO'
      },
      redirectUrl: `${window.location.origin}${CONFIG.urls.pago_exitoso}`,
      taxInCents: 0
    });

    checkout.open(function (result) {
      console.log('Wompi Result:', result);
      
      if (result.transaction && result.transaction.status === 'APPROVED') {
        // Pago exitoso - procesar pedido
        processSuccessfulPayment(result.transaction);
      } else if (result.transaction && result.transaction.status === 'DECLINED') {
        showToast('El pago fue declinado. Por favor intenta con otro método de pago.', 'error');
        checkoutState.isProcessing = false;
      } else if (result.transaction && result.transaction.status === 'ERROR') {
        showToast('Ocurrió un error durante el proceso de pago.', 'error');
        checkoutState.isProcessing = false;
      } else {
        // Usuario cerró el widget
        showToast('Pago cancelado', 'info');
        checkoutState.isProcessing = false;
      }
    });
  }

  function processSuccessfulPayment(transaction) {
    // Crear formulario para enviar datos del pago exitoso
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = CONFIG.urls.pago_exitoso;

    // Agregar CSRF token
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = getCookie('csrftoken');
    form.appendChild(csrfInput);

    // Datos del cliente
    const formData = {
      'nombre': safeEl('#nombre')?.value || '',
      'email': safeEl('#email')?.value || '',
      'telefono': safeEl('#telefono')?.value || '',
      'direccion': safeEl('#direccion')?.value || '',
      'ciudad': safeEl('#ciudad')?.value || '',
      'departament': safeEl('#departament')?.value || '',
      'codigo_postal': safeEl('#codigo_postal')?.value || '',
      'note': safeEl('#note')?.value || '',
      'metodo_pago': 'wompi',
      'transaction_id': transaction.id,
      'discount_applied': checkoutState.discountCode,
      'discount_amount': checkoutState.discountAmount
    };

    // Agregar campos al formulario
    Object.keys(formData).forEach(key => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = formData[key];
      form.appendChild(input);
    });

    // Enviar formulario
    document.body.appendChild(form);
    form.submit();
  }

  // Procesamiento de pagos
  function processPayment() {
    if (checkoutState.isProcessing) {
      return;
    }

    if (!validateCheckoutForm()) {
      return;
    }

    const paymentMethod = document.querySelector('input[name="metodo_pago"]:checked')?.value;
    
    if (!paymentMethod) {
      showToast('Por favor selecciona un método de pago', 'error');
      return;
    }

    checkoutState.isProcessing = true;
    checkoutState.selectedPayment = paymentMethod;

    if (paymentMethod === 'tarjeta') {
      processWompiPayment();
    } else {
      processStandardPayment();
    }
  }

  function processWompiPayment() {
    showLoading(true);
    
    // Preparar datos para crear transacción
    const transactionData = {
      amount: checkoutState.finalTotal,
      customer_email: safeEl('#email')?.value || '',
      discount_code: checkoutState.discountCode,
      discount_amount: checkoutState.discountAmount
    };

    // Crear transacción en el backend
    fetch(CONFIG.urls.create_transaction, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(transactionData)
    })
    .then(response => response.json())
    .then(data => {
      showLoading(false);
      
      if (data.success) {
        // Inicializar widget de Wompi
        initializeWompi(data);
      } else {
        showToast(data.error || 'Error creando transacción', 'error');
        checkoutState.isProcessing = false;
      }
    })
    .catch(error => {
      showLoading(false);
      console.error('Error:', error);
      showToast('Error de conexión. Por favor intenta de nuevo.', 'error');
      checkoutState.isProcessing = false;
    });
  }

  function processStandardPayment() {
    // Procesar pago contra entrega (método existente)
    const form = safeEl('#checkout-form');
    if (!form) {
      showToast('Error: formulario no encontrado', 'error');
      checkoutState.isProcessing = false;
      return;
    }

    // Agregar datos de descuento al formulario
    if (checkoutState.discountApplied) {
      addHiddenInput(form, 'discount_applied', checkoutState.discountCode);
      addHiddenInput(form, 'discount_amount', checkoutState.discountAmount);
    }

    addHiddenInput(form, 'metodo_pago', 'contraentrega');
    
    // Enviar formulario
    form.submit();
  }

  function addHiddenInput(form, name, value) {
    // Remover input existente si existe
    const existing = form.querySelector(`input[name="${name}"]`);
    if (existing) {
      existing.remove();
    }

    // Crear nuevo input
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    form.appendChild(input);
  }

  // Manejo de métodos de pago
  function handlePaymentMethodChange() {
    const paymentMethods = document.querySelectorAll('input[name="metodo_pago"]');
    const cardSection = safeEl('#cardPaymentSection');

    console.log('🔧 Configurando manejo de métodos de pago...');
    console.log('🔧 Payment methods encontrados:', paymentMethods.length);
    console.log('🔧 Card section encontrada:', !!cardSection);

    paymentMethods.forEach(method => {
      method.addEventListener('change', function() {
        console.log('🔧 Método de pago cambiado a:', this.value);
        
        if (this.value === 'tarjeta') {
          if (cardSection) {
            cardSection.classList.remove('d-none');
            cardSection.style.display = 'block';
            console.log('✅ Sección de tarjeta mostrada');
          } else {
            console.error('❌ No se encontró la sección de tarjeta');
          }
        } else {
          if (cardSection) {
            cardSection.classList.add('d-none');
            cardSection.style.display = 'none';
            console.log('✅ Sección de tarjeta ocultada');
          }
        }
      });
    });

    // Verificar estado inicial
    const selectedMethod = document.querySelector('input[name="metodo_pago"]:checked');
    if (selectedMethod) {
      console.log('🔧 Método inicial seleccionado:', selectedMethod.value);
      if (selectedMethod.value === 'tarjeta' && cardSection) {
        cardSection.classList.remove('d-none');
        cardSection.style.display = 'block';
      }
    }
  }

  // Event Listeners
  function setupEventListeners() {
    console.log('🔧 Configurando event listeners para Wompi Checkout...');

    // Botón de confirmar pago
    const confirmBtn = safeEl('#confirm-payment');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', function(e) {
        e.preventDefault();
        processPayment();
      });
    }

    // Aplicar descuento
    const applyDiscountBtn = safeEl('#apply-discount');
    if (applyDiscountBtn) {
      applyDiscountBtn.addEventListener('click', applyDiscount);
    }

    // Remover descuento
    const removeDiscountBtn = safeEl('#remove-discount');
    if (removeDiscountBtn) {
      removeDiscountBtn.addEventListener('click', removeDiscount);
    }

    // Enter en input de descuento
    const discountInput = safeEl('#discount-code');
    if (discountInput) {
      discountInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          applyDiscount();
        }
      });
    }

    // Cambios en métodos de pago
    handlePaymentMethodChange();

    console.log('✅ Event listeners configurados');
  }

  // Inicialización
  function init() {
    console.log('🚀 Inicializando Wompi Checkout...');
    
    // Verificar configuración
    if (!CONFIG.wompi_public_key) {
      console.error('🚨 Wompi public key no configurada');
      console.error('🔧 CONFIG actual:', CONFIG);
      console.error('🔧 window.checkout_config:', window.checkout_config);
      showToast('Error de configuración: clave pública de Wompi no encontrada', 'error');
      return;
    }

    console.log('✅ Wompi configurado con clave:', CONFIG.wompi_public_key.substring(0, 20) + '...');
    
    // Calcular totales iniciales
    calculateTotals();

    // Configurar event listeners
    setupEventListeners();

    console.log('✅ Wompi Checkout inicializado correctamente');
  }

  // Auto-inicialización cuando el DOM está listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Exponer funciones globales para debugging
  window.WompiCheckout = {
    state: checkoutState,
    config: CONFIG,
    applyDiscount,
    removeDiscount,
    calculateTotals,
    processPayment
  };

})();