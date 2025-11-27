/* ========================================
   CARRITO MODERNO - JAVASCRIPT COMPLETO
======================================== */

(function() {
  'use strict';

  // Estado global del carrito
  const CartState = {
    isUpdating: false,
    selectedItems: new Set(),
    animations: window.matchMedia('(prefers-reduced-motion: no-preference)').matches
  };

  // Utilidades mejoradas
  const Utils = {
    // Obtener CSRF token
    getCsrfToken() {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
          return decodeURIComponent(value);
        }
      }
      return null;
    },

    // Formatear números con separadores de miles
    formatPrice(price) {
      return new Intl.NumberFormat('es-CO').format(price);
    },

    // Detectar qué vista está activa (desktop o móvil)
    getActiveView() {
      const desktopView = document.querySelector('.cart-desktop-view');
      const mobileView = document.querySelector('.cart-mobile-view');
      
      if (desktopView && getComputedStyle(desktopView).display !== 'none') {
        return 'desktop';
      } else if (mobileView && getComputedStyle(mobileView).display !== 'none') {
        return 'mobile';
      }
      return 'desktop'; // fallback
    },

    // Obtener solo elementos de la vista activa
    getActiveCartItems() {
      const activeView = this.getActiveView();
      if (activeView === 'desktop') {
        return document.querySelectorAll('.cart-desktop-view .cart-item-modern');
      } else {
        return document.querySelectorAll('.cart-mobile-view .cart-item-mobile');
      }
    },

    // Obtener checkboxes de la vista activa
    getActiveCheckboxes() {
      const activeView = this.getActiveView();
      if (activeView === 'desktop') {
        return document.querySelectorAll('.cart-desktop-view .cart-checkbox-modern');
      } else {
        return document.querySelectorAll('.cart-mobile-view .cart-checkbox-modern');
      }
    },

    // Mostrar notificaciones toast mejoradas
    showToast(message, type = 'success') {
      // Usar SweetAlert2 Toast
      const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
          toast.addEventListener('mouseenter', Swal.stopTimer)
          toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
      });

      let icon = 'success';
      if (type === 'error') icon = 'error';
      else if (type === 'warning') icon = 'warning';
      else if (type === 'info') icon = 'info';

      Toast.fire({
        icon: icon,
        title: message
      });
    },

    // Debounce para mejor performance
    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    // Animaciones
    async fadeOut(element, duration = 300) {
      return new Promise(resolve => {
        element.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
        element.style.opacity = '0';
        element.style.transform = 'translateX(-20px)';
        setTimeout(resolve, duration);
      });
    }
  };

  // Manejador de cantidades moderno
  const QuantityHandler = {
    updateQuantity: Utils.debounce(async function(productId, variantId, newQuantity) {
      if (CartState.isUpdating) return;
      
      CartState.isUpdating = true;
      
      // Mostrar estado de carga
      const cartItem = document.querySelector(`[data-product="${productId}"]${variantId ? `[data-variant="${variantId}"]` : ''}`);
      const parentCard = cartItem?.closest('.cart-item-modern, .cart-item-mobile');
      if (parentCard) parentCard.classList.add('loading');
      
      try {
        const formData = new FormData();
        formData.append('product_id', productId);
        if (variantId) formData.append('variant_id', variantId);
        formData.append('quantity', newQuantity);
        formData.append('csrfmiddlewaretoken', Utils.getCsrfToken());
        
        const response = await fetch(`/update_cart/${productId}/`, {
          method: 'POST',
          body: formData,
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        
        const data = await response.json();
        
        if (data.success) {
          
          // Actualizar precio individual del producto
          QuantityHandler.updatePriceDisplay(productId, variantId, data.item_subtotal);
          
          // Usar total del servidor (que ya calcula correctamente)
          CartSummary.updateTotals(data.cart_total, data.cart_count);
          
          Utils.showToast('Cantidad actualizada', 'success');
        } else {
          Utils.showToast(data.message || 'Error al actualizar cantidad', 'error');
        }
      } catch (error) {
        console.error('Error updating quantity:', error);
        Utils.showToast('Error de conexión', 'error');
      } finally {
        if (parentCard) parentCard.classList.remove('loading');
        CartState.isUpdating = false;
      }
    }, 500),

    updatePriceDisplay(productId, variantId, newSubtotal) {
      const selector = `[data-product="${productId}"]${variantId ? `[data-variant="${variantId}"]` : ''}`;
      const cartItems = document.querySelectorAll(selector);
      
      cartItems.forEach(item => {
        const parentCard = item.closest('.cart-item-modern, .cart-item-mobile');
        if (parentCard) {
          const desktopPrice = parentCard.querySelector('.item-total-price');
          const mobilePrice = parentCard.querySelector('.mobile-total-price');
          
          const formattedPrice = `$${Utils.formatPrice(newSubtotal)}`;
          
          if (desktopPrice) desktopPrice.textContent = formattedPrice;
          if (mobilePrice) mobilePrice.textContent = formattedPrice;
        }
      });
    },

    setupQuantityControls() {
      // Botones de incremento/decremento
      document.addEventListener('click', (e) => {
        if (e.target.closest('.qty-btn-modern, .mobile-qty-btn')) {
          e.preventDefault();
          const btn = e.target.closest('.qty-btn-modern, .mobile-qty-btn');
          const productId = btn.dataset.product;
          const variantId = btn.dataset.variant || null;
          const isIncrease = btn.classList.contains('qty-increase');
          const isDecrease = btn.classList.contains('qty-decrease');
          
          if (btn.classList.contains('mobile-qty-btn')) {
            // Mobile: usar display de cantidad
            const qtyDisplay = btn.parentElement.querySelector('.mobile-qty-display');
            if (qtyDisplay) {
              let currentQty = parseInt(qtyDisplay.textContent);
              if (isIncrease) currentQty++;
              else if (isDecrease && currentQty > 1) currentQty--;
              
              qtyDisplay.textContent = currentQty;
              QuantityHandler.updateQuantity(productId, variantId, currentQty);
            }
          } else {
            // Desktop: usar input
            const quantityInput = btn.parentElement.querySelector('.qty-input-modern');
            if (quantityInput) {
              let currentValue = parseInt(quantityInput.value) || 1;
              const maxValue = parseInt(quantityInput.max) || 999;
              
              if (isIncrease && currentValue < maxValue) currentValue++;
              else if (isDecrease && currentValue > 1) currentValue--;
              
              quantityInput.value = currentValue;
              QuantityHandler.updateQuantity(productId, variantId, currentValue);
            }
          }
        }
      });
      
      // Input directo de cantidad
      document.addEventListener('change', (e) => {
        if (e.target.classList.contains('qty-input-modern')) {
          const input = e.target;
          const productId = input.dataset.product;
          const variantId = input.dataset.variant || null;
          let newQuantity = parseInt(input.value) || 1;
          const maxValue = parseInt(input.max) || 999;
          
          if (newQuantity < 1) {
            newQuantity = 1;
            input.value = 1;
          } else if (newQuantity > maxValue) {
            newQuantity = maxValue;
            input.value = maxValue;
            Utils.showToast(`Máximo ${maxValue} unidades disponibles`, 'warning');
          }
          
          QuantityHandler.updateQuantity(productId, variantId, newQuantity);
        }
      });
    }
  };

  // Manejador para vaciar carrito
  const ClearCartHandler = {
    async clearCart() {
      const confirmed = await ClearCartHandler.showClearConfirmDialog();
      if (!confirmed) return;
      
      try {
        const response = await fetch('/clear_cart/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': Utils.getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Animar eliminación de todos los productos
        const activeItems = Utils.getActiveCartItems();
        for (const item of activeItems) {
          await Utils.fadeOut(item, 200);
        }
        
        // Mostrar estado vacío
        RemoveHandler.showEmptyState();
        
        // Actualizar totales
        CartSummary.updateTotals(0, 0);
        
        Utils.showToast('Carrito vaciado completamente', 'success');
        
      } catch (error) {
        console.error('Error clearing cart:', error);
        Utils.showToast('Error al vaciar carrito', 'error');
      }
    },
    
    async showClearConfirmDialog() {
      const result = await Swal.fire({
        title: '¿Vaciar carrito completo?',
        html: `
          <div style="text-align: left; margin-top: 20px;">
            <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); border: 1px solid #f59e0b; border-radius: 12px; padding: 16px;">
              <div style="display: flex; align-items: center; gap: 8px; color: #92400e; margin-bottom: 8px;">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <span style="font-weight: 600;">Advertencia importante</span>
              </div>
              <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.4;">
                Se eliminarán todos los productos de tu carrito de compras.
                Tendrás que agregarlos nuevamente si deseas continuar.
              </p>
            </div>
          </div>
        `,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        cancelButtonColor: '#6b7280',
        confirmButtonText: '<i class="bi bi-trash3-fill me-2"></i>Sí, vaciar carrito',
        cancelButtonText: '<i class="bi bi-x-circle me-2"></i>Cancelar',
        customClass: {
          popup: 'swal-modern',
          confirmButton: 'btn-confirm-modern',
          cancelButton: 'btn-cancel-modern'
        },
        backdrop: 'rgba(0,0,0,0.5)',
        showClass: {
          popup: 'animate__animated animate__fadeInDown animate__faster'
        },
        hideClass: {
          popup: 'animate__animated animate__fadeOutUp animate__faster'
        }
      });
      return result.isConfirmed;
    },
    
    setupClearButton() {
      const clearBtn = document.querySelector('#btn-clear-cart');
      if (clearBtn) {
        clearBtn.onclick = (e) => {
          e.preventDefault();
          ClearCartHandler.clearCart();
        };
      }
    }
  };
  const RemoveHandler = {
    async removeProduct(productId, variantId = null) {
      if (CartState.isUpdating) return;
      
      const confirmed = await RemoveHandler.showConfirmDialog();
      if (!confirmed) return;
      
      CartState.isUpdating = true;
      
      try {
        const url = variantId 
          ? `/remove_from_cart/${productId}/?variant_id=${variantId}`
          : `/remove_from_cart/${productId}/`;
          
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': Utils.getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
          // Animar eliminación solo en la vista activa
          const itemSelector = `[data-product="${productId}"]${variantId ? `[data-variant="${variantId}"]` : ''}`;
          const activeItems = Utils.getActiveCartItems();
          
          for (const activeItem of activeItems) {
            const productElement = activeItem.querySelector(itemSelector);
            if (productElement || 
                activeItem.dataset.product === productId.toString() || 
                activeItem.querySelector(`[data-product="${productId}"]`)) {
              await Utils.fadeOut(activeItem);
              activeItem.remove();
            }
          }
          
          // Actualizar totales usando los valores del servidor
          CartSummary.updateTotals(data.cart_total, data.cart_count);
          
          if (data.cart_count === 0) {
            RemoveHandler.showEmptyState();
          }
          
          Utils.showToast('Producto eliminado', 'success');
        } else {
          Utils.showToast(data.message || 'Error al eliminar', 'error');
        }
      } catch (error) {
        console.error('Error removing product:', error);
        Utils.showToast('Error de conexión', 'error');
      } finally {
        CartState.isUpdating = false;
      }
    },

    async showConfirmDialog() {
      const result = await Swal.fire({
        title: 'Confirmar eliminación',
        text: '¿Estás seguro de que quieres eliminar este producto del carrito?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        confirmButtonText: '<i class="bi bi-trash-fill me-2"></i>Eliminar',
        cancelButtonText: '<i class="bi bi-x-circle me-2"></i>Cancelar',
        backdrop: 'rgba(0,0,0,0.5)',
        showClass: {
          popup: 'animate__animated animate__zoomIn animate__faster'
        },
        hideClass: {
          popup: 'animate__animated animate__zoomOut animate__faster'
        }
      });
      return result.isConfirmed;
    },

    showEmptyState() {
      const cartContent = document.querySelector('.cart-content-main');
      const sidebar = document.querySelector('.cart-summary-sidebar');
      
      if (cartContent) {
        cartContent.innerHTML = `
          <div class="cart-empty-state-modern">
            <div class="empty-illustration">
              <div class="empty-cart-icon">
                <i class="bi bi-cart-x-fill"></i>
              </div>
            </div>
            <div class="empty-content">
              <h2 class="empty-title">Tu carrito está vacío</h2>
              <p class="empty-subtitle">¡Es hora de llenarlo! Explora nuestros productos.</p>
              <div class="empty-actions">
                <a href="/store/" class="btn-shop-now-modern">
                  <i class="bi bi-bag-plus-fill"></i>
                  <span>Explorar productos</span>
                </a>
                <a href="/" class="btn-go-home">
                  <i class="bi bi-house-fill"></i>
                  <span>Ir al inicio</span>
                </a>
              </div>
            </div>
          </div>
        `;
      }
      
      if (sidebar) sidebar.style.display = 'none';
    },

    setupRemoveButtons() {
      document.addEventListener('click', (e) => {
        if (e.target.closest('.btn-remove-modern, .btn-remove-mobile')) {
          e.preventDefault();
          const btn = e.target.closest('.btn-remove-modern, .btn-remove-mobile');
          const productId = btn.dataset.product;
          const variantId = btn.dataset.variant || null;
          
          RemoveHandler.removeProduct(productId, variantId);
        }
      });
    }
  };

  // Resumen del carrito
  const CartSummary = {
    updateTotals(subtotal, cartCount) {
      // Contador de productos
      const productCounts = document.querySelectorAll('.summary-products-count span, .cart-subtitle');
      productCounts.forEach(el => {
        if (el.parentElement?.classList.contains('summary-products-count')) {
          el.textContent = `${cartCount} ${cartCount === 1 ? 'producto' : 'productos'} seleccionados`;
        } else {
          el.textContent = `${cartCount} ${cartCount === 1 ? 'artículo' : 'artículos'} ${cartCount > 0 ? 'en tu carrito' : 'agregado'}`;
        }
      });
      
      const subtotalValue = typeof subtotal === 'string' ? parseFloat(subtotal) : subtotal;
      
      // Actualizar subtotal
      const subtotalElements = document.querySelectorAll('#selected-subtotal');
      subtotalElements.forEach(el => {
        el.textContent = `$${Utils.formatPrice(subtotalValue)}`;
      });
      
      let shippingCost = 0;
      let finalTotal = 0;
      
      // Solo calcular envío si hay productos seleccionados
      if (cartCount > 0 && subtotalValue > 0) {
        // Calcular envío (gratis si subtotal >= 100,000)
        shippingCost = subtotalValue >= 100000 ? 0 : 15000;
        finalTotal = subtotalValue + shippingCost;
      } else {
        // Sin productos seleccionados
        shippingCost = 0;
        finalTotal = 0;
      }
      
      // Actualizar indicador de envío
      const shippingElement = document.querySelector('.shipping-calculation');
      if (shippingElement) {
        const shippingValue = shippingElement.querySelector('.calculation-value');
        if (cartCount === 0) {
          // Sin productos seleccionados
          shippingValue.textContent = '$0';
        } else if (shippingCost === 0) {
          // Envío gratis
          shippingValue.innerHTML = '<span class="original-price">$15.000</span><span class="free-badge">¡GRATIS!</span>';
        } else {
          // Envío normal
          shippingValue.textContent = `$${Utils.formatPrice(shippingCost)}`;
        }
      }
      
      // Actualizar total final
      const totalElements = document.querySelectorAll('#cart-total-amount, .total-amount');
      totalElements.forEach(el => {
        el.textContent = `$${Utils.formatPrice(finalTotal)}`;
      });
      
      // Actualizar mensaje de ahorro
      const savingsInfo = document.querySelector('.savings-info');
      if (savingsInfo) {
        if (cartCount > 0 && shippingCost === 0 && subtotalValue >= 100000) {
          savingsInfo.style.display = 'flex';
          savingsInfo.innerHTML = '<i class="bi bi-piggy-bank-fill"></i><span>Ahorras $15.000 en envío</span>';
        } else {
          savingsInfo.style.display = 'none';
        }
      }
    },

    calculateInitialTotals() {
      // Calcular total inicial desde los elementos de la vista ACTIVA solamente
      let cartSubtotal = 0;
      let cartCount = 0;
      
      const activeItems = Utils.getActiveCartItems();
      
      activeItems.forEach(item => {
        const quantityInput = item.querySelector('.qty-input-modern');
        const quantityDisplay = item.querySelector('.mobile-qty-display');
        const priceElement = item.querySelector('.item-total-price, .mobile-total-price');
        
        if (priceElement) {
          const priceText = priceElement.textContent;
          const price = parseInt(priceText.replace(/\D/g, '')) || 0;
          
          cartSubtotal += price;
          cartCount += 1; // Contar productos únicos
        }
      });
      
      this.updateTotals(cartSubtotal, cartCount);
    },

    setupCheckoutButton() {
      const checkoutBtn = document.querySelector('#finalizar-pedido-modern');
      if (checkoutBtn) {
        checkoutBtn.onclick = () => {
          const selectedCheckboxes = document.querySelectorAll('.cart-checkbox-modern:checked');
          
          if (selectedCheckboxes.length === 0) {
            Utils.showToast('Selecciona al menos un producto', 'warning');
            return;
          }
          
          checkoutBtn.classList.add('loading');
          setTimeout(() => window.location.href = '/checkout/', 500);
        };
      }
    },

    setupCouponHandler() {
      const couponInput = document.querySelector('#coupon-code');
      const applyBtn = document.querySelector('#apply-coupon');
      
      if (couponInput && applyBtn) {
        const applyCoupon = async () => {
          const couponCode = couponInput.value.trim();
          
          if (!couponCode) {
            Utils.showToast('Ingresa un código de cupón', 'warning');
            couponInput.focus();
            return;
          }
          
          applyBtn.classList.add('loading');
          
          try {
            const response = await fetch('/apply_coupon/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Utils.getCsrfToken()
              },
              body: JSON.stringify({ coupon_code: couponCode })
            });
            
            const data = await response.json();
            
            if (data.success) {
              Utils.showToast('Cupón aplicado', 'success');
              CartSummary.updateTotals(data.new_total, data.cart_count);
              
              const discountLine = document.querySelector('.discount-calculation');
              if (discountLine) {
                discountLine.style.display = 'flex';
                discountLine.querySelector('.discount-value').textContent = `-$${Utils.formatPrice(data.discount_amount)}`;
              }
            } else {
              Utils.showToast(data.message || 'Cupón no válido', 'error');
            }
          } catch (error) {
            Utils.showToast('Error al aplicar cupón', 'error');
          } finally {
            applyBtn.classList.remove('loading');
          }
        };
        
        applyBtn.onclick = applyCoupon;
        couponInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') applyCoupon();
        });
      }
    }
  };

  // Selección de productos
  const SelectionHandler = {
    setupSelectAllButton() {
      const selectAllBtn = document.querySelector('#toggleSelectAll');
      if (selectAllBtn) {
        selectAllBtn.onclick = () => {
          const checkboxes = Utils.getActiveCheckboxes();
          const allChecked = Array.from(checkboxes).every(cb => cb.checked);
          
          // Cambiar estado de todos los checkboxes ACTIVOS
          checkboxes.forEach(cb => cb.checked = !allChecked);
          
          // Actualizar texto del botón
          selectAllBtn.innerHTML = allChecked 
            ? '<i class="bi bi-check-all"></i><span>Seleccionar todo</span>'
            : '<i class="bi bi-check2-square"></i><span>Deseleccionar todo</span>';
          
          // Recalcular totales según nueva selección
          if (!allChecked) {
            // Se marcaron todos - calcular total completo
            CartSummary.calculateInitialTotals();
          } else {
            // Se desmarcaron todos - mostrar $0
            CartSummary.updateTotals(0, 0);
          }
          
          SelectionHandler.updateSelectedItems();
        };
      }
    },

    updateSelectedItems() {
      // Contar solo checkboxes de la vista activa
      const checkedCount = Utils.getActiveCheckboxes().length;
      
      // Solo actualizar contador de productos seleccionados
      const productCounts = document.querySelectorAll('.summary-products-count span');
      productCounts.forEach(el => {
        el.textContent = `${checkedCount} ${checkedCount === 1 ? 'producto' : 'productos'} seleccionados`;
      });
      
      // NO calcular totales aquí - dejar que el servidor maneje los cálculos
      // Solo actualizar contador visual
    },

    setupCheckboxListeners() {
      document.addEventListener('change', (e) => {
        if (e.target.classList.contains('cart-checkbox-modern')) {
          // Recalcular totales basado en productos seleccionados de la vista ACTIVA
          let selectedSubtotal = 0;
          let selectedProductsCount = 0;
          
          // Usar solo checkboxes de la vista activa
          const activeCheckedBoxes = Array.from(Utils.getActiveCheckboxes())
            .filter(checkbox => checkbox.checked);
          
          activeCheckedBoxes.forEach(checkbox => {
            const parentCard = checkbox.closest('.cart-item-modern, .cart-item-mobile');
            if (parentCard) {
              selectedProductsCount++; // Un producto por checkbox
              
              const priceElement = parentCard.querySelector('.item-total-price, .mobile-total-price');
              
              if (priceElement) {
                const priceText = priceElement.textContent;
                const price = parseInt(priceText.replace(/\D/g, '')) || 0;
                
                selectedSubtotal += price;
              }
            }
          });
          
          CartSummary.updateTotals(selectedSubtotal, selectedProductsCount);
          SelectionHandler.updateSelectedItems();
        }
      });
    }
  };

  // Contador de nota
  const NoteHandler = {
    setupNoteCounter() {
      const textarea = document.querySelector('#cart-note');
      const counter = document.querySelector('#note-counter');
      
      if (textarea && counter) {
        textarea.addEventListener('input', () => {
          const length = textarea.value.length;
          const maxLength = 500;
          
          counter.textContent = length;
          
          if (length > maxLength * 0.9) counter.style.color = '#ef4444';
          else if (length > maxLength * 0.7) counter.style.color = '#f59e0b';
          else counter.style.color = '#3b82f6';
          
          if (length > maxLength) {
            textarea.value = textarea.value.substring(0, maxLength);
            counter.textContent = maxLength;
          }
        });
      }
    }
  };

  // Inicialización
  function initializeCart() {
    console.log('🛒 Inicializando carrito moderno...');
    
    QuantityHandler.setupQuantityControls();
    RemoveHandler.setupRemoveButtons();
    CartSummary.setupCheckoutButton();
    CartSummary.setupCouponHandler();
    SelectionHandler.setupSelectAllButton();
    SelectionHandler.setupCheckboxListeners();
    NoteHandler.setupNoteCounter();
    ClearCartHandler.setupClearButton(); // Nuevo manejador
    
    // Marcar todos los checkboxes por defecto
    const checkboxes = document.querySelectorAll('.cart-checkbox-modern');
    checkboxes.forEach(cb => cb.checked = true);
    
    // Calcular total inicial desde el DOM del servidor
    CartSummary.calculateInitialTotals();
    
    console.log('✅ Carrito moderno inicializado');
  }

  // Ejecutar cuando DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCart);
  } else {
    initializeCart();
  }

})();