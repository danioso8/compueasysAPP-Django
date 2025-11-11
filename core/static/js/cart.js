/* ========================================
   CARRITO MODERNO - JAVASCRIPT MEJORADO
======================================== */

(function() {
  'use strict';

  // Estado global del carrito
  const CartState = {
    isUpdating: false,
    touchStartX: 0,
    touchStartY: 0,
    selectedItems: new Set(),
    animations: window.matchMedia('(prefers-reduced-motion: no-preference)').matches
  };

  // Utilidades
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

    // Mostrar notificaciones toast
    showToast(message, type = 'success') {
      // Crear elemento toast si no existe
      let toastContainer = document.getElementById('toast-container');
      if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 10000;
          display: flex;
          flex-direction: column;
          gap: 10px;
          pointer-events: none;
        `;
        document.body.appendChild(toastContainer);
      }

      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.style.cssText = `
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#f59e0b'};
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateX(100%);
        transition: transform 0.3s ease-in-out, opacity 0.3s ease-in-out;
        pointer-events: auto;
        font-weight: 500;
        max-width: 300px;
        word-wrap: break-word;
      `;
      toast.textContent = message;

      toastContainer.appendChild(toast);

      // Animación de entrada
      requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
      });

      // Auto eliminar después de 4 segundos
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }, 4000);

      // Click para cerrar
      toast.addEventListener('click', () => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      });
    },

    // Agregar clase de loading
    setLoading(element, loading = true) {
      if (loading) {
        element.classList.add('loading');
        element.style.pointerEvents = 'none';
      } else {
        element.classList.remove('loading');
        element.style.pointerEvents = '';
      }
    },

    // Vibración táctil (si está disponible)
    vibrate(pattern = [50]) {
      if ('vibrate' in navigator) {
        navigator.vibrate(pattern);
      }
    },

    // Detectar si es dispositivo táctil
    isTouchDevice() {
      return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
  };

  // Gestor de animaciones
  const AnimationManager = {
    // Animar cambio de cantidad
    animateQuantityChange(element, newValue) {
      if (!CartState.animations) return;
      
      element.style.transform = 'scale(1.2)';
      element.style.transition = 'transform 0.2s ease-out';
      
      setTimeout(() => {
        element.textContent = newValue;
        element.style.transform = 'scale(1)';
      }, 100);
    },

    // Animar eliminación de item
    animateItemRemoval(itemElement) {
      if (!CartState.animations) {
        itemElement.remove();
        return Promise.resolve();
      }

      return new Promise((resolve) => {
        itemElement.style.transition = 'all 0.3s ease-out';
        itemElement.style.transform = 'translateX(-100%)';
        itemElement.style.opacity = '0';
        itemElement.style.height = '0';
        itemElement.style.margin = '0';
        itemElement.style.padding = '0';

        setTimeout(() => {
          itemElement.remove();
          resolve();
        }, 300);
      });
    },

    // Animar actualización de precio
    animatePriceUpdate(element, newPrice) {
      if (!element) {
        console.warn('Element not found for price update');
        return;
      }

      // 🔍 DEBUG: Ver valores exactos recibidos
      console.log(`💰 animatePriceUpdate called:`, {
        element: element.className,
        newPrice: newPrice,
        typeOfPrice: typeof newPrice
      });

      const formattedPrice = `$${Utils.formatPrice(newPrice)}`;
      
      console.log(`💰 Formatted price: ${formattedPrice}`);

      if (!CartState.animations) {
        element.textContent = formattedPrice;
        return;
      }

      element.style.transition = 'color 0.3s ease-out';
      element.style.color = '#10b981';
      element.textContent = formattedPrice;

      setTimeout(() => {
        element.style.color = '';
      }, 1000);
    }
  };

  // Gestor del carrito
  const CartManager = {
    // Actualizar carrito vía AJAX
    async updateCart(productId, variantId, quantity, action = 'set') {
      if (CartState.isUpdating) {
        console.log('⏳ Cart update already in progress, skipping...');
        return;
      }
      
      CartState.isUpdating = true;
      console.log('🔄 Updating cart:', { productId, variantId, quantity, action });

      try {
        const formData = new FormData();
        formData.append('variant_id', variantId || '');
        formData.append('quantity', quantity);
        formData.append('action', action);
        formData.append('csrfmiddlewaretoken', Utils.getCsrfToken());

        const response = await fetch(`/update_cart/${productId}/`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('📥 Cart update response:', data);

        if (data.success) {
          this.updateUI(productId, variantId, data);
          Utils.showToast('Carrito actualizado', 'success');
          Utils.vibrate([30]);
          return data;
        } else {
          throw new Error(data.message || 'Error al actualizar el carrito');
        }

      } catch (error) {
        console.error('❌ Error updating cart:', error);
        Utils.showToast(error.message || 'Error de conexión', 'error');
        Utils.vibrate([50, 50, 50]);
        return { success: false, error: error.message };
      } finally {
        CartState.isUpdating = false;
      }
    },

    // Actualizar UI después de cambios en el carrito
    updateUI(productId, variantId, data) {
      console.log('🔄 Updating UI:', { productId, variantId, data });
      
      // Actualizar subtotal del item - mejorar selectores
      if (data.subtotal !== undefined) {
        // Buscar en vista de escritorio
        const desktopRow = document.querySelector(`tr.cart-row[data-index]`);
        let found = false;
        
        // Buscar la fila que contiene este producto específico
        document.querySelectorAll('.cart-row').forEach(row => {
          const quantityControl = row.querySelector(`[data-product="${productId}"][data-variant="${variantId || ''}"]`);
          if (quantityControl) {
            // 🔍 DEBUG: Ver qué fila se está actualizando  
            console.log('🖥️ Updating desktop row for product:', productId, 'variant:', variantId);
            
            const subtotalElement = row.querySelector('.item-subtotal');
            if (subtotalElement) {
              AnimationManager.animatePriceUpdate(subtotalElement, data.subtotal);
              console.log('✅ Updated desktop subtotal:', data.subtotal);
              found = true;
            }
            
            // 🔄 También actualizar el input de cantidad en escritorio
            const qtyInput = row.querySelector('.qty-input');
            if (qtyInput && data.quantity !== undefined) {
              qtyInput.value = data.quantity;
              console.log('✅ Updated desktop quantity input:', data.quantity);
            }
          }
        });

        // Buscar en vista móvil
        document.querySelectorAll('.cart-item-card').forEach(card => {
          const quantityControl = card.querySelector(`[data-product="${productId}"][data-variant="${variantId || ''}"]`);
          if (quantityControl) {
            // 🔍 DEBUG: Ver qué carta se está actualizando
            console.log('📱 Updating mobile card for product:', productId, 'variant:', variantId);
            
            const subtotalElement = card.querySelector('.total-price');
            if (subtotalElement) {
              AnimationManager.animatePriceUpdate(subtotalElement, data.subtotal);
              console.log('✅ Updated mobile subtotal:', data.subtotal);
              found = true;
            }
            
            // 🔄 También actualizar la cantidad mostrada en móvil
            const qtyDisplay = card.querySelector('.qty-display');
            if (qtyDisplay && data.quantity !== undefined) {
              qtyDisplay.textContent = data.quantity;
              console.log('✅ Updated mobile quantity display:', data.quantity);
            }
          }
        });
        
        if (!found) {
          console.warn('⚠️ No subtotal elements found for product:', productId, 'variant:', variantId);
        }
      }

      // Actualizar total del carrito
      if (data.cart_total !== undefined) {
        const totalElements = document.querySelectorAll('#cart-total, .total-value');
        totalElements.forEach(element => {
          AnimationManager.animatePriceUpdate(element, data.cart_total);
        });
        console.log('✅ Updated cart total:', data.cart_total);

        // Actualizar total seleccionado
        this.updateSelectedTotal();
      }

      // Actualizar contador de productos
      if (data.cart_count !== undefined) {
        const countElements = document.querySelectorAll('.cart-count, .cart-badge');
        countElements.forEach(element => {
          if (element.classList.contains('cart-badge')) {
            const text = data.cart_count === 1 ? 'producto' : 'productos';
            element.textContent = `${data.cart_count} ${text}`;
          } else {
            element.textContent = data.cart_count;
          }
        });
        console.log('✅ Updated cart count:', data.cart_count);
      }
    },

    // Actualizar total de productos seleccionados
    updateSelectedTotal() {
      console.log('💰 Calculating selected total...');
      
      // 🔍 DEBUG: Verificar checkboxes duplicados ANTES de calcular
      const allCheckboxes = document.querySelectorAll('.cart-checkbox');
      const selectedCheckboxes = document.querySelectorAll('.cart-checkbox:checked:not(#select-all)');
      
      console.log(`🔍 DEBUGGING CHECKBOXES:`);
      console.log(`Total checkboxes found: ${allCheckboxes.length}`);
      console.log(`Selected checkboxes found: ${selectedCheckboxes.length}`);
      
      // Verificar duplicados por valor
      const checkboxValues = Array.from(selectedCheckboxes).map(cb => cb.value);
      const uniqueValues = [...new Set(checkboxValues)];
      
      console.log(`Checkbox values:`, checkboxValues);
      console.log(`Unique values:`, uniqueValues);
      console.log(`¿Hay duplicados?`, checkboxValues.length !== uniqueValues.length);
      
      if (checkboxValues.length !== uniqueValues.length) {
        console.error('🚨 CHECKBOXES DUPLICADOS DETECTADOS!');
        
        // Mostrar detalles de cada checkbox
        selectedCheckboxes.forEach((checkbox, index) => {
          const parent = checkbox.closest('.cart-row, .cart-item-card');
          const isDesktop = parent?.classList.contains('cart-row');
          const isMobile = parent?.classList.contains('cart-item-card');
          
          console.log(`Checkbox ${index}:`, {
            value: checkbox.value,
            checked: checkbox.checked,
            isDesktop,
            isMobile,
            parentClass: parent?.className
          });
        });
        
        // ✅ NO SALIR - Continuar con valores únicos para calcular correctamente
        console.log('🔄 Continuing with unique values to calculate total...');
      }
      
      let total = 0;
      
      // 🔍 Detectar qué vista está activa (desktop o móvil)
      const desktopView = document.querySelector('.cart-desktop-view');
      const mobileView = document.querySelector('.cart-mobile-view');
      
      const isDesktopVisible = desktopView && window.getComputedStyle(desktopView).display !== 'none';
      const isMobileVisible = mobileView && window.getComputedStyle(mobileView).display !== 'none';
      
      console.log('📱 View detection:', { isDesktopVisible, isMobileVisible });
      
      // Usar solo valores únicos para evitar duplicados
      uniqueValues.forEach((itemIndex, index) => {
        let subtotalElement = null;
        
        // 🖥️ Si la vista desktop está visible, buscar solo ahí
        if (isDesktopVisible && !isMobileVisible) {
          const desktopRow = document.querySelector(`tr[data-index="${itemIndex}"]`);
          if (desktopRow) {
            subtotalElement = desktopRow.querySelector('.item-subtotal');
            console.log(`�️ Using DESKTOP subtotal for item ${itemIndex}`);
          }
        }
        // 📱 Si la vista móvil está visible, buscar solo ahí
        else if (isMobileVisible && !isDesktopVisible) {
          const mobileCard = document.querySelector(`.cart-item-card[data-index="${itemIndex}"]`);
          if (mobileCard) {
            subtotalElement = mobileCard.querySelector('.total-price');
            console.log(`📱 Using MOBILE subtotal for item ${itemIndex}`);
          }
        }
        // 🔄 Si ambas vistas están visibles (caso raro), priorizar desktop
        else {
          const desktopRow = document.querySelector(`tr[data-index="${itemIndex}"]`);
          if (desktopRow) {
            subtotalElement = desktopRow.querySelector('.item-subtotal');
            console.log(`🔄 Both views visible, using DESKTOP subtotal for item ${itemIndex}`);
          }
        }
        
        if (subtotalElement) {
          // Extraer SOLO números del texto (sin símbolos de moneda ni comas)
          const text = subtotalElement.textContent;
          const cleanNumber = text.replace(/[^0-9]/g, '');
          const value = parseInt(cleanNumber) || 0;
          
          total += value;
          console.log(`✅ Item ${itemIndex}: ${text} → cleaned: ${cleanNumber} → adding: ${value}`);
        } else {
          console.warn(`⚠️ No subtotal found for item ${itemIndex}`);
        }
      });

      console.log(`💳 Final calculated total: ${total}`);

      // Actualizar elementos de total en la UI
      const formattedTotal = `$${Utils.formatPrice(total)}`;
      
      const selectedTotalElement = document.getElementById('selected-total');
      if (selectedTotalElement) {
        selectedTotalElement.textContent = formattedTotal;
        console.log('✅ Updated selected-total element to:', formattedTotal);
      }
      
      const cartTotalElement = document.getElementById('cart-total');
      if (cartTotalElement) {
        cartTotalElement.textContent = formattedTotal;
        console.log('✅ Updated cart-total element to:', formattedTotal);
      }
    },

    // Eliminar item del carrito
    async removeItem(productId, variantId = '') {
      const confirmed = await this.showConfirmDialog('¿Eliminar este producto del carrito?');
      if (!confirmed) return;

      Utils.vibrate([50]);

      try {
        let url = `/remove_from_cart/${productId}/`;
        if (variantId && variantId !== '') {
          url += `?variant_id=${variantId}`;
        }
        
        console.log('Removing item with URL:', url);
        window.location.href = url;
      } catch (error) {
        console.error('Error removing item:', error);
        Utils.showToast('Error al eliminar el producto', 'error');
      }
    },

    // Mostrar diálogo de confirmación moderno
    showConfirmDialog(message) {
      return new Promise((resolve) => {
        // Crear modal simple si no existe Bootstrap
        let confirmResult = false;
        
        // Intentar usar Bootstrap modal si está disponible
        const modal = document.getElementById('confirmModal');
        if (modal && typeof bootstrap !== 'undefined') {
          const modalInstance = new bootstrap.Modal(modal);
          const confirmBtn = document.getElementById('confirmDelete');
          
          modal.querySelector('.modal-body p').textContent = message;
          
          const handleConfirm = () => {
            modalInstance.hide();
            confirmBtn.removeEventListener('click', handleConfirm);
            resolve(true);
          };

          const handleCancel = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            resolve(false);
          };

          confirmBtn.addEventListener('click', handleConfirm);
          modal.addEventListener('hidden.bs.modal', handleCancel, { once: true });
          
          modalInstance.show();
        } else {
          // Fallback a confirm nativo
          resolve(confirm(message));
        }
      });
    },

    // Vaciar carrito completo
    async clearCart() {
      const confirmed = await this.showConfirmDialog('¿Vaciar todo el carrito?');
      if (!confirmed) return;

      Utils.vibrate([100]);
      window.location.href = '/clear_cart/';
    }
  };

  // Gestor de controles de cantidad
  const QuantityManager = {
    // Inicializar controles de cantidad
    init() {
      // Controles de escritorio
      this.initDesktopControls();
      
      // Controles móviles
      this.initMobileControls();
      
      // Inputs directos
      this.initDirectInputs();
    },

    initDesktopControls() {
      document.addEventListener('click', (e) => {
        if (e.target.closest('.qty-btn')) {
          e.preventDefault();
          this.handleQuantityButton(e.target.closest('.qty-btn'));
        }
      });
    },

    initMobileControls() {
      document.addEventListener('click', (e) => {
        if (e.target.closest('.qty-btn-mobile')) {
          e.preventDefault();
          this.handleMobileQuantityButton(e.target.closest('.qty-btn-mobile'));
        }
      });
    },

    initDirectInputs() {
      document.addEventListener('change', (e) => {
        if (e.target.classList.contains('qty-input')) {
          this.handleDirectInput(e.target);
        }
      });
    },

    async handleQuantityButton(button) {
      const isDecrease = button.classList.contains('qty-decrease');
      const productId = button.dataset.product;
      const variantId = button.dataset.variant || '';
      
      console.log('🔢 Handling quantity button:', { isDecrease, productId, variantId });
      
      const input = button.parentNode.querySelector('.qty-input');
      if (!input) {
        console.error('❌ Input not found for quantity button');
        return;
      }

      let currentQuantity = parseInt(input.value);
      let newQuantity = currentQuantity;
      const maxQuantity = parseInt(input.getAttribute('max')) || 99;

      if (isDecrease) {
        newQuantity = Math.max(1, currentQuantity - 1);
      } else {
        newQuantity = Math.min(maxQuantity, currentQuantity + 1);
      }

      console.log(`📊 Quantity change: ${currentQuantity} → ${newQuantity}`);

      if (newQuantity === currentQuantity) {
        console.log('⚠️ No quantity change needed');
        return;
      }

      input.value = newQuantity;
      Utils.setLoading(button.parentNode, true);

      try {
        const result = await CartManager.updateCart(productId, variantId, newQuantity);
        if (!result.success) {
          // Revertir el cambio si falló
          input.value = currentQuantity;
        }
      } finally {
        Utils.setLoading(button.parentNode, false);
      }
    },

    async handleMobileQuantityButton(button) {
      const isDecrease = button.classList.contains('qty-decrease');
      const productId = button.dataset.product;
      const variantId = button.dataset.variant || '';
      
      console.log('📱 Handling mobile quantity button:', { isDecrease, productId, variantId });
      
      const qtyDisplay = button.parentNode.querySelector('.qty-display');
      if (!qtyDisplay) {
        console.error('❌ Quantity display not found for mobile button');
        return;
      }

      let currentQuantity = parseInt(qtyDisplay.textContent);
      let newQuantity = currentQuantity;
      const maxQuantity = parseInt(button.dataset.max) || 99;

      if (isDecrease) {
        newQuantity = Math.max(1, currentQuantity - 1);
      } else {
        newQuantity = Math.min(maxQuantity, currentQuantity + 1);
      }

      console.log(`📊 Mobile quantity change: ${currentQuantity} → ${newQuantity}`);

      if (newQuantity === currentQuantity) {
        console.log('⚠️ No quantity change needed');
        return;
      }

      AnimationManager.animateQuantityChange(qtyDisplay, newQuantity);
      Utils.setLoading(button.parentNode, true);

      try {
        const result = await CartManager.updateCart(productId, variantId, newQuantity);
        if (!result.success) {
          // Revertir el cambio si falló
          qtyDisplay.textContent = currentQuantity;
        }
      } finally {
        Utils.setLoading(button.parentNode, false);
      }
    },

    async handleDirectInput(input) {
      const productId = input.dataset.product;
      const variantId = input.dataset.variant;
      const maxQuantity = parseInt(input.getAttribute('max'));
      
      let newQuantity = parseInt(input.value);
      
      // Validar límites
      if (newQuantity < 1) {
        newQuantity = 1;
        input.value = 1;
      }
      
      if (newQuantity > maxQuantity) {
        newQuantity = maxQuantity;
        input.value = maxQuantity;
        Utils.showToast(`Stock máximo: ${maxQuantity}`, 'warning');
      }

      Utils.setLoading(input.parentNode, true);

      try {
        await CartManager.updateCart(productId, variantId, newQuantity);
      } finally {
        Utils.setLoading(input.parentNode, false);
      }
    }
  };

  // Gestor de selección de productos
  const SelectionManager = {
    init() {
      console.log('🔲 Initializing SelectionManager...');
      
      // Checkbox "Seleccionar todo"
      const selectAllCheckbox = document.getElementById('select-all');
      if (selectAllCheckbox) {
        console.log('✅ Select-all checkbox found');
        selectAllCheckbox.addEventListener('change', this.handleSelectAll.bind(this));
      } else {
        console.warn('⚠️ Select-all checkbox not found');
      }

      // Checkboxes individuales - DEBUGGING INTENSIVO
      document.addEventListener('change', (e) => {
        console.log('🔍 CHANGE EVENT DETECTED:', {
          target: e.target,
          classList: e.target.classList.toString(),
          id: e.target.id,
          value: e.target.value,
          checked: e.target.checked,
          hasCartCheckboxClass: e.target.classList.contains('cart-checkbox')
        });
        
        if (e.target.classList.contains('cart-checkbox') && e.target.id !== 'select-all') {
          console.log('✅ INDIVIDUAL CHECKBOX EVENT TRIGGERED');
          console.log('📦 Individual checkbox changed:', e.target.value);
          this.handleIndividualSelection(e.target);
        } else {
          console.log('❌ Event ignored - not a cart checkbox or is select-all');
        }
      });

      // Debugging inicial - verificar duplicados
      const allCheckboxes = document.querySelectorAll('.cart-checkbox');
      console.log(`Found ${allCheckboxes.length} total checkboxes`);
      
      // Verificar duplicados por valor en la inicialización
      const valueCount = {};
      allCheckboxes.forEach((checkbox, index) => {
        if (checkbox.id !== 'select-all') {
          const value = checkbox.value;
          valueCount[value] = (valueCount[value] || 0) + 1;
        }
        console.log(`Checkbox ${index}: value=${checkbox.value}, checked=${checkbox.checked}, id=${checkbox.id}`);
      });
      
      // Reportar duplicados encontrados
      Object.entries(valueCount).forEach(([value, count]) => {
        if (count > 1) {
          console.warn(`⚠️ DUPLICATE checkboxes detected for value ${value}: ${count} instances`);
        }
      });

      // Inicializar estado
      this.updateSelectAllState();
      CartManager.updateSelectedTotal();
      
      // 🧪 TEST: Agregar click listeners directamente a cada checkbox para debugging
      console.log('🧪 Adding direct click listeners for testing...');
      const testCheckboxes = document.querySelectorAll('.cart-checkbox:not(#select-all)');
      testCheckboxes.forEach((checkbox, index) => {
        checkbox.addEventListener('click', (e) => {
          console.log(`🧪 DIRECT CLICK EVENT on checkbox ${index}:`, {
            value: e.target.value,
            checked: e.target.checked,
            event: e
          });
        });
      });
      
      console.log(`🧪 Added direct click listeners to ${testCheckboxes.length} checkboxes`);
    },

    handleSelectAll(e) {
      const isChecked = e.target.checked;
      const checkboxes = document.querySelectorAll('.cart-checkbox:not(#select-all)');
      
      console.log('Select all clicked, isChecked:', isChecked, 'found checkboxes:', checkboxes.length);
      
      checkboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
        if (isChecked) {
          CartState.selectedItems.add(checkbox.value);
        } else {
          CartState.selectedItems.delete(checkbox.value);
        }
      });

      CartManager.updateSelectedTotal();
      Utils.vibrate([30]);
    },

    handleIndividualSelection(checkbox) {
      console.log('🚀 handleIndividualSelection CALLED');
      console.log('Individual selection changed:', checkbox.value, 'checked:', checkbox.checked);
      
      // 🔄 SINCRONIZAR checkboxes duplicados (desktop + móvil) - SIMPLIFICADO
      const itemValue = checkbox.value;
      const isChecked = checkbox.checked;
      
      console.log(`🔍 Looking for checkboxes with value: ${itemValue}`);
      
      // Encontrar TODOS los checkboxes con el mismo valor y sincronizarlos
      const allCheckboxesWithSameValue = document.querySelectorAll(`.cart-checkbox[value="${itemValue}"]:not(#select-all)`);
      
      console.log(`📦 Found ${allCheckboxesWithSameValue.length} checkboxes with value ${itemValue}:`);
      allCheckboxesWithSameValue.forEach((cb, index) => {
        console.log(`  Checkbox ${index}:`, {
          element: cb,
          currentChecked: cb.checked,
          shouldBe: isChecked,
          isSameAsOriginal: cb === checkbox
        });
      });
      
      // Sincronizar todos los checkboxes con el mismo valor
      allCheckboxesWithSameValue.forEach((cb, index) => {
        if (cb !== checkbox) { // No cambiar el checkbox que disparó el evento
          cb.checked = isChecked;
          console.log(`🔄 Synced checkbox ${index}: set to ${cb.checked}`);
        }
      });

      // Actualizar estado interno
      if (isChecked) {
        CartState.selectedItems.add(itemValue);
        console.log(`✅ Added item ${itemValue} to selected items`);
      } else {
        CartState.selectedItems.delete(itemValue);
        console.log(`❌ Removed item ${itemValue} from selected items`);
      }
      
      console.log('🎯 Current selected items:', Array.from(CartState.selectedItems));

      console.log('🔄 Calling updateSelectAllState...');
      this.updateSelectAllState();
      
      console.log('🔄 About to update total after individual selection...');
      CartManager.updateSelectedTotal();
      console.log('✅ Total update completed after individual selection');
      
      Utils.vibrate([20]);
    },

    updateSelectAllState() {
      const selectAllCheckbox = document.getElementById('select-all');
      if (!selectAllCheckbox) return;

      // 🔍 Contar solo valores únicos de checkboxes, no checkboxes duplicados
      const allIndividualCheckboxes = document.querySelectorAll('.cart-checkbox:not(#select-all)');
      const checkedCheckboxes = document.querySelectorAll('.cart-checkbox:not(#select-all):checked');
      
      // Obtener valores únicos
      const uniqueValues = new Set(Array.from(allIndividualCheckboxes).map(cb => cb.value));
      const checkedUniqueValues = new Set(Array.from(checkedCheckboxes).map(cb => cb.value));
      
      const uniqueCount = uniqueValues.size;
      const checkedUniqueCount = checkedUniqueValues.size;
      
      console.log('🔲 Select-all state check:', {
        totalUniqueItems: uniqueCount,
        checkedUniqueItems: checkedUniqueCount,
        totalCheckboxes: allIndividualCheckboxes.length,
        checkedCheckboxes: checkedCheckboxes.length
      });

      if (checkedUniqueCount === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
        console.log('🔲 Select-all: UNCHECKED (no items selected)');
      } else if (checkedUniqueCount === uniqueCount) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
        console.log('🔲 Select-all: CHECKED (all items selected)');
      } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
        console.log('🔲 Select-all: INDETERMINATE (some items selected)');
      }
    }
  };

  // Gestor de gestos táctiles
  const TouchManager = {
    init() {
      if (!Utils.isTouchDevice()) return;

      document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
      document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
      document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    },

    handleTouchStart(e) {
      CartState.touchStartX = e.touches[0].clientX;
      CartState.touchStartY = e.touches[0].clientY;
    },

    handleTouchMove(e) {
      const touch = e.touches[0];
      const deltaX = touch.clientX - CartState.touchStartX;
      const deltaY = touch.clientY - CartState.touchStartY;

      // Detectar swipe horizontal en items del carrito
      const cartItem = e.target.closest('.cart-item-card');
      if (cartItem && Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        e.preventDefault();
        
        if (deltaX < -100) { // Swipe izquierda = eliminar
          this.showSwipeAction(cartItem, 'delete');
        }
      }
    },

    handleTouchEnd() {
      // Limpiar cualquier indicador de swipe
      document.querySelectorAll('.swipe-indicator').forEach(indicator => {
        indicator.remove();
      });
    },

    showSwipeAction(cartItem, action) {
      // Remover indicadores existentes
      cartItem.querySelectorAll('.swipe-indicator').forEach(indicator => {
        indicator.remove();
      });

      if (action === 'delete') {
        const indicator = document.createElement('div');
        indicator.className = 'swipe-indicator';
        indicator.innerHTML = '<i class="bi bi-trash3"></i> Desliza para eliminar';
        indicator.style.cssText = `
          position: absolute;
          right: 16px;
          top: 50%;
          transform: translateY(-50%);
          background: #ef4444;
          color: white;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 12px;
          z-index: 10;
          animation: swipePulse 0.5s ease-in-out;
        `;
        
        cartItem.style.position = 'relative';
        cartItem.appendChild(indicator);
        
        Utils.vibrate([50, 20, 50]);
      }
    }
  };

  // Funciones globales para el HTML
  window.removeItem = (productId, variantId = '') => {
    console.log('removeItem called with:', { productId, variantId });
    CartManager.removeItem(productId, variantId);
  };

  window.clearCart = () => {
    console.log('clearCart called');
    CartManager.clearCart();
  };
  
  // 🧪 FUNCIÓN DE TEST GLOBAL para debugging
  window.testCheckboxes = () => {
    console.log('🧪 TESTING CHECKBOXES MANUALLY...');
    const checkboxes = document.querySelectorAll('.cart-checkbox:not(#select-all)');
    console.log(`Found ${checkboxes.length} checkboxes to test`);
    
    checkboxes.forEach((checkbox, index) => {
      console.log(`Checkbox ${index}:`, {
        value: checkbox.value,
        checked: checkbox.checked,
        classList: checkbox.classList.toString(),
        id: checkbox.id || 'no-id'
      });
    });
    
    // Simular cambio en el primer checkbox
    if (checkboxes.length > 0) {
      const firstCheckbox = checkboxes[0];
      console.log('🧪 Simulating click on first checkbox...');
      firstCheckbox.checked = !firstCheckbox.checked;
      
      // Disparar evento change manualmente
      const changeEvent = new Event('change', { bubbles: true });
      firstCheckbox.dispatchEvent(changeEvent);
    }
  };

  // Inicialización cuando el DOM está listo
  document.addEventListener('DOMContentLoaded', () => {
    console.group('🛒 Cart Manager Initialization');
    console.log('Initializing modern cart experience...');

    // Inicializar todos los gestores
    QuantityManager.init();
    SelectionManager.init();
    TouchManager.init();

    // Debugging inicial
    console.log('Cart items found:', document.querySelectorAll('.cart-item-card, .cart-row').length);
    console.log('Checkboxes found:', document.querySelectorAll('.cart-checkbox').length);
    console.log('Remove buttons found:', document.querySelectorAll('.btn-remove').length);

    // Botón finalizar pedido
    const finalizarBtn = document.getElementById('finalizar-pedido');
    if (finalizarBtn) {
      finalizarBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const nota = document.getElementById('cart-note')?.value || '';
        Utils.vibrate([30, 20, 30]);
        console.log('Navigating to checkout with note:', nota);
        window.location.href = `/checkout/?note=${encodeURIComponent(nota)}`;
      });
    }

    // Test de funciones globales
    if (typeof window.removeItem === 'function') {
      console.log('✅ removeItem function available globally');
    } else {
      console.error('❌ removeItem function not available');
    }

    // Agregar estilos CSS dinámicos para animaciones
    if (!document.getElementById('cart-dynamic-styles')) {
      const styles = document.createElement('style');
      styles.id = 'cart-dynamic-styles';
      styles.textContent = `
        @keyframes swipePulse {
          from { opacity: 0; transform: translateY(-50%) scale(0.8); }
          to { opacity: 1; transform: translateY(-50%) scale(1); }
        }
        
        .loading {
          position: relative;
          pointer-events: none;
        }
        
        .loading::after {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 16px;
          height: 16px;
          margin: -8px 0 0 -8px;
          border: 2px solid #2563eb;
          border-top: 2px solid transparent;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `;
      document.head.appendChild(styles);
    }

    console.log('✅ Cart experience initialized successfully');
    console.groupEnd();

    // Verificar que el carrito se cargó correctamente
    const cartItems = document.querySelectorAll('.cart-item-card, tr.cart-row');
    if (cartItems.length > 0) {
      console.log(`🛒 Found ${cartItems.length} items in cart`);
      Utils.showToast('Carrito cargado correctamente', 'success');
      
      // Calcular total inicial y verificar elementos de UI
      setTimeout(() => {
        CartManager.updateSelectedTotal();
        
        // Verificar que los totales se muestran correctamente
        const selectedTotal = document.getElementById('selected-total');
        const cartTotal = document.getElementById('cart-total');
        
        if (selectedTotal && cartTotal) {
          console.log('💰 Total elements found and updated');
        } else {
          console.warn('⚠️ Total elements not found, cart may not display correctly');
        }
      }, 100);
    } else {
      console.log('📦 Empty cart detected');
    }
  });

})();