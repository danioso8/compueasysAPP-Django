/**
 * Cart Manager - Sistema simplificado de carrito de compras
 * Funcionalidades:
 * - Actualizar cantidades de productos
 * - Seleccionar/deseleccionar productos con checkboxes
 * - Recalcular totales automáticamente
 * - Vaciar carrito
 */

(function() {
  'use strict';

  // ========================================
  // 1. UTILIDADES
  // ========================================
  const Utils = {
    // Obtener token CSRF
    getCsrfToken() {
      const name = 'csrftoken';
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [key, value] = cookie.trim().split('=');
        if (key === name) return decodeURIComponent(value);
      }
      return '';
    },

    // Formatear precio con separadores de miles
    formatPrice(price) {
      return new Intl.NumberFormat('es-CO').format(Math.round(price));
    },

    // Mostrar toast notification con SweetAlert2
    showToast(message, type = 'success') {
      if (typeof Swal === 'undefined') {
        console.warn('SweetAlert2 no está disponible, usando alert básico');
        alert(message);
        return;
      }

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
  };

  // ========================================
  // 2. GESTOR DE TOTALES
  // ========================================
  const TotalsManager = {
    // Calcular totales basándose en productos seleccionados
    calculateTotals() {
      console.log('💰 Calculando totales...');
      
      let subtotal = 0;
      let totalItems = 0;
      const processedIndexes = new Set(); // Para evitar duplicados

      // Obtener todos los checkboxes seleccionados (excepto "seleccionar todo")
      const selectedCheckboxes = document.querySelectorAll('.cart-checkbox-modern:checked:not(#toggleSelectAll)');
      
      selectedCheckboxes.forEach(checkbox => {
        const itemIndex = checkbox.value;
        
        // Si ya procesamos este índice, saltar
        if (processedIndexes.has(itemIndex)) {
          console.log(`  ⚠️ Índice ${itemIndex} ya procesado, saltando duplicado`);
          return;
        }
        
        // Buscar el item correspondiente - priorizar desktop si está visible
        let item = document.querySelector(`.cart-item-modern[data-index="${itemIndex}"]`);
        
        // Si no está visible o no existe, buscar mobile
        if (!item || window.getComputedStyle(item.parentElement).display === 'none') {
          item = document.querySelector(`.cart-item-mobile[data-index="${itemIndex}"]`);
        }
        
        if (item) {
          // Obtener el precio del subtotal del item
          const subtotalElement = item.querySelector('.item-total-price, .mobile-total-price');
          if (subtotalElement) {
            const priceText = subtotalElement.textContent.replace(/[^0-9]/g, '');
            const itemSubtotal = parseInt(priceText) || 0;
            subtotal += itemSubtotal;
            totalItems++;
            processedIndexes.add(itemIndex);
            console.log(`  ✅ Item ${itemIndex}: $${itemSubtotal}`);
          }
        }
      });

      console.log(`  💵 Total: $${subtotal} (${totalItems} items)`);
      
      // Actualizar UI
      this.updateUI(subtotal, totalItems);
      
      return { subtotal, totalItems };
    },

    // Actualizar elementos de UI con los totales
    updateUI(subtotal, totalItems) {
      const formattedSubtotal = `$${Utils.formatPrice(subtotal)}`;
      
      // Actualizar subtotal
      const subtotalElements = document.querySelectorAll('#selected-subtotal');
      subtotalElements.forEach(el => {
        el.textContent = formattedSubtotal;
        this.animateElement(el);
      });

      // Actualizar total a pagar (mismo que subtotal si envío es gratis)
      const totalElements = document.querySelectorAll('#cart-total-amount');
      totalElements.forEach(el => {
        el.textContent = formattedSubtotal;
        this.animateElement(el);
      });

      console.log('✅ UI actualizada');
    },

    // Animar elemento cuando cambia
    animateElement(element) {
      element.style.transition = 'color 0.3s ease';
      element.style.color = '#10b981';
      setTimeout(() => {
        element.style.color = '';
      }, 600);
    }
  };

  // ========================================
  // 3. GESTOR DE CANTIDADES
  // ========================================
  const QuantityManager = {
    isUpdating: false,

    // Actualizar cantidad en el servidor
    async updateQuantity(productId, variantId, newQuantity) {
      if (this.isUpdating) {
        console.log('⏳ Actualización en progreso...');
        return;
      }

      this.isUpdating = true;
      console.log(`🔄 Actualizando cantidad: Producto ${productId}, Variante ${variantId}, Cantidad ${newQuantity}`);

      try {
        const formData = new FormData();
        formData.append('variant_id', variantId || '');
        formData.append('quantity', newQuantity);
        formData.append('action', 'set');
        formData.append('csrfmiddlewaretoken', Utils.getCsrfToken());

        const response = await fetch(`/update_cart/${productId}/`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('📥 Respuesta del servidor:', data);

        if (data.success) {
          // Actualizar subtotal del item en el DOM
          this.updateItemSubtotal(productId, variantId, data.item_subtotal);
          
          // Actualizar cantidad en inputs y displays
          this.updateQuantityDisplay(productId, variantId, data.quantity);
          
          // Recalcular totales
          TotalsManager.calculateTotals();
          
          Utils.showToast('Cantidad actualizada', 'success');
          return data;
        } else {
          throw new Error(data.message || 'Error al actualizar');
        }

      } catch (error) {
        console.error('❌ Error:', error);
        Utils.showToast(error.message || 'Error de conexión', 'error');
        return null;
      } finally {
        this.isUpdating = false;
      }
    },

    // Actualizar el subtotal de un item específico en el DOM
    updateItemSubtotal(productId, variantId, newSubtotal) {
      console.log(`📝 Actualizando subtotal del item: $${newSubtotal}`);
      
      const formattedPrice = `$${Utils.formatPrice(newSubtotal)}`;
      
      // Actualizar en vista desktop
      const desktopItems = document.querySelectorAll('.cart-item-modern');
      desktopItems.forEach(item => {
        const qtyControl = item.querySelector(`[data-product="${productId}"][data-variant="${variantId || ''}"]`);
        if (qtyControl) {
          const subtotalElement = item.querySelector('.item-total-price');
          if (subtotalElement) {
            subtotalElement.textContent = formattedPrice;
            TotalsManager.animateElement(subtotalElement);
            console.log(`  ✅ Desktop: Subtotal actualizado a ${formattedPrice}`);
          }
        }
      });
      
      // Actualizar en vista mobile
      const mobileItems = document.querySelectorAll('.cart-item-mobile');
      mobileItems.forEach(item => {
        const qtyControl = item.querySelector(`[data-product="${productId}"][data-variant="${variantId || ''}"]`);
        if (qtyControl) {
          const subtotalElement = item.querySelector('.mobile-total-price');
          if (subtotalElement) {
            subtotalElement.textContent = formattedPrice;
            TotalsManager.animateElement(subtotalElement);
            console.log(`  ✅ Mobile: Subtotal actualizado a ${formattedPrice}`);
          }
          
          // También actualizar el display de cantidad en mobile
          const qtyDisplay = item.querySelector('.mobile-qty-display');
          if (qtyDisplay) {
            const newQty = Math.round(newSubtotal / this.getUnitPrice(item));
            // No actualizamos aquí porque la cantidad viene en data.quantity
          }
        }
      });
    },
    
    // Obtener precio unitario del item
    getUnitPrice(item) {
      const unitPriceElement = item.querySelector('.mobile-unit-price, .price-per-unit');
      if (unitPriceElement) {
        const priceText = unitPriceElement.textContent.replace(/[^0-9]/g, '');
        return parseInt(priceText) || 0;
      }
      return 0;
    },
    
    // Actualizar display de cantidad en desktop y mobile
    updateQuantityDisplay(productId, variantId, newQuantity) {
      console.log(`🔢 Actualizando cantidad a: ${newQuantity}`);
      
      // Actualizar inputs en vista desktop
      const desktopInputs = document.querySelectorAll('.qty-input-modern');
      desktopInputs.forEach(input => {
        if (input.dataset.product === productId && (input.dataset.variant || '') === (variantId || '')) {
          input.value = newQuantity;
          console.log(`  ✅ Desktop input actualizado`);
        }
      });
      
      // Actualizar displays en vista mobile
      const mobileItems = document.querySelectorAll('.cart-item-mobile');
      mobileItems.forEach(item => {
        const qtyControl = item.querySelector(`[data-product="${productId}"][data-variant="${variantId || ''}"]`);
        if (qtyControl) {
          const qtyDisplay = item.querySelector('.mobile-qty-display');
          if (qtyDisplay) {
            qtyDisplay.textContent = newQuantity;
            console.log(`  ✅ Mobile display actualizado`);
          }
        }
      });
    }
  };

  // ========================================
  // 4. GESTOR DE CHECKBOXES
  // ========================================
  const CheckboxManager = {
    init() {
      console.log('☑️ Inicializando CheckboxManager...');
      
      // Checkbox "Seleccionar todo"
      const selectAllBtn = document.getElementById('toggleSelectAll');
      console.log('  🔍 Botón "Seleccionar todo":', selectAllBtn);
      
      if (selectAllBtn) {
        selectAllBtn.addEventListener('click', (e) => {
          e.preventDefault();
          console.log('  🖱️ Click en "Seleccionar todo"');
          this.toggleAll();
        });
        console.log('  ✅ Botón "Seleccionar todo" configurado');
      } else {
        console.warn('  ⚠️ Botón "Seleccionar todo" NO encontrado');
      }

      // Checkboxes individuales - sincronizar entre desktop y mobile
      const checkboxes = document.querySelectorAll('.cart-checkbox-modern:not(#toggleSelectAll)');
      console.log(`  📋 ${checkboxes.length} checkboxes encontrados`);
      
      if (checkboxes.length === 0) {
        console.warn('  ⚠️ NO se encontraron checkboxes');
      }
      
      checkboxes.forEach((checkbox, index) => {
        console.log(`  📌 Configurando checkbox ${index}: value=${checkbox.value}, id=${checkbox.id}`);
        
        checkbox.addEventListener('change', (e) => {
          const itemIndex = checkbox.value;
          const isChecked = checkbox.checked;
          
          console.log(`☑️ CHANGE EVENT - Checkbox ${itemIndex} → ${isChecked}`);
          
          // Sincronizar con el checkbox correspondiente (desktop ↔ mobile)
          this.syncCheckboxes(itemIndex, isChecked, checkbox);
          
          // Recalcular totales
          TotalsManager.calculateTotals();
          
          // Actualizar botón "Seleccionar todo"
          this.updateSelectAllButton();
        });
      });

      // Calcular totales iniciales
      console.log('  💰 Calculando totales iniciales...');
      TotalsManager.calculateTotals();
      this.updateSelectAllButton();
      
      console.log('  ✅ CheckboxManager inicializado');
    },

    // Sincronizar checkboxes entre desktop y mobile
    syncCheckboxes(itemIndex, isChecked, sourceCheckbox) {
      const allCheckboxes = document.querySelectorAll(`.cart-checkbox-modern[value="${itemIndex}"]:not(#toggleSelectAll)`);
      
      allCheckboxes.forEach(checkbox => {
        if (checkbox !== sourceCheckbox) {
          checkbox.checked = isChecked;
        }
      });
    },

    // Seleccionar/deseleccionar todos
    toggleAll() {
      console.log('🔄 Toggle all checkboxes...');
      
      // Obtener checkboxes únicos por valor (evitar duplicados desktop/mobile)
      const allCheckboxes = document.querySelectorAll('.cart-checkbox-modern:not(#toggleSelectAll)');
      const checkboxesByValue = new Map();
      
      allCheckboxes.forEach(cb => {
        if (!checkboxesByValue.has(cb.value)) {
          checkboxesByValue.set(cb.value, cb);
        }
      });
      
      // Verificar si todos están marcados
      const allChecked = Array.from(checkboxesByValue.values()).every(cb => cb.checked);
      const newState = !allChecked;
      
      console.log(`  Estado actual: ${allChecked ? 'todos marcados' : 'algunos desmarcados'}`);
      console.log(`  Nuevo estado: ${newState ? 'marcar todos' : 'desmarcar todos'}`);
      
      // Cambiar estado de TODOS los checkboxes
      allCheckboxes.forEach(checkbox => {
        checkbox.checked = newState;
      });

      TotalsManager.calculateTotals();
      this.updateSelectAllButton();
      
      Utils.showToast(
        newState ? 'Todos los productos seleccionados' : 'Productos deseleccionados',
        'success'
      );
    },

    // Actualizar estado del botón "Seleccionar todo"
    updateSelectAllButton() {
      const selectAllBtn = document.getElementById('toggleSelectAll');
      if (!selectAllBtn) return;

      // Obtener checkboxes únicos por valor
      const allCheckboxes = document.querySelectorAll('.cart-checkbox-modern:not(#toggleSelectAll)');
      const checkboxesByValue = new Map();
      
      allCheckboxes.forEach(cb => {
        if (!checkboxesByValue.has(cb.value)) {
          checkboxesByValue.set(cb.value, cb);
        }
      });
      
      const allChecked = Array.from(checkboxesByValue.values()).every(cb => cb.checked);
      
      const icon = selectAllBtn.querySelector('i');
      const text = selectAllBtn.querySelector('span');
      
      if (icon && text) {
        if (allChecked) {
          icon.className = 'bi bi-check-square-fill';
          text.textContent = 'Deseleccionar todo';
          selectAllBtn.classList.add('all-selected');
        } else {
          icon.className = 'bi bi-check-all';
          text.textContent = 'Seleccionar todo';
          selectAllBtn.classList.remove('all-selected');
        }
      }
    }
  };

  // ========================================
  // 5. GESTOR DE BOTONES DE CANTIDAD
  // ========================================
  const ButtonsManager = {
    init() {
      // Botones de aumentar
      document.addEventListener('click', async (e) => {
        if (e.target.closest('.qty-increase')) {
          const btn = e.target.closest('.qty-increase');
          await this.handleIncrease(btn);
        }
      });

      // Botones de disminuir
      document.addEventListener('click', async (e) => {
        if (e.target.closest('.qty-decrease')) {
          const btn = e.target.closest('.qty-decrease');
          await this.handleDecrease(btn);
        }
      });

      // Inputs de cantidad (cambio directo)
      document.addEventListener('change', async (e) => {
        if (e.target.classList.contains('qty-input-modern')) {
          await this.handleInputChange(e.target);
        }
      });
    },

    // Aumentar cantidad
    async handleIncrease(btn) {
      const productId = btn.dataset.product;
      const variantId = btn.dataset.variant || '';
      
      const input = btn.parentElement.querySelector('.qty-input-modern');
      if (!input) return;

      const currentQty = parseInt(input.value) || 1;
      const maxQty = parseInt(input.max) || 999;
      const newQty = Math.min(currentQty + 1, maxQty);

      if (newQty > currentQty) {
        input.value = newQty;
        await QuantityManager.updateQuantity(productId, variantId, newQty);
      }
    },

    // Disminuir cantidad
    async handleDecrease(btn) {
      const productId = btn.dataset.product;
      const variantId = btn.dataset.variant || '';
      
      const input = btn.parentElement.querySelector('.qty-input-modern');
      if (!input) return;

      const currentQty = parseInt(input.value) || 1;
      const newQty = Math.max(currentQty - 1, 1);

      if (newQty < currentQty) {
        input.value = newQty;
        await QuantityManager.updateQuantity(productId, variantId, newQty);
      }
    },

    // Cambio manual en el input
    async handleInputChange(input) {
      const productId = input.dataset.product;
      const variantId = input.dataset.variant || '';
      
      let newQty = parseInt(input.value) || 1;
      const minQty = parseInt(input.min) || 1;
      const maxQty = parseInt(input.max) || 999;

      // Validar rango
      newQty = Math.max(minQty, Math.min(newQty, maxQty));
      input.value = newQty;

      await QuantityManager.updateQuantity(productId, variantId, newQty);
    }
  };

  // ========================================
  // 6. GESTOR DE ELIMINACIÓN DE PRODUCTOS
  // ========================================
  const RemoveManager = {
    init() {
      console.log('🗑️ Inicializando RemoveManager...');
      
      // Botones de eliminar en desktop
      document.addEventListener('click', async (e) => {
        if (e.target.closest('.btn-remove-modern, .btn-remove-mobile')) {
          const btn = e.target.closest('.btn-remove-modern, .btn-remove-mobile');
          await this.handleRemove(btn);
        }
      });
      
      console.log('  ✅ RemoveManager inicializado');
    },

    async handleRemove(btn) {
      const productId = btn.dataset.product;
      const variantId = btn.dataset.variant || '';
      
      console.log(`🗑️ Eliminando producto ${productId}, variante ${variantId}`);
      
      // Confirmar con SweetAlert2 o confirm básico
      let confirmed = false;
      if (typeof Swal !== 'undefined') {
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
        confirmed = result.isConfirmed;
      } else {
        confirmed = confirm('¿Eliminar este producto del carrito?');
      }
      
      if (!confirmed) {
        return;
      }

      try {
        // Construir URL con variant_id como query parameter
        let url = `/remove_from_cart/${productId}/`;
        if (variantId) {
          url += `?variant_id=${variantId}`;
        }

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
        console.log('📥 Respuesta:', data);

        if (data.success) {
          Utils.showToast('Producto eliminado', 'success');
          
          // Recargar página después de 500ms
          setTimeout(() => {
            window.location.reload();
          }, 500);
        } else {
          throw new Error(data.message || 'Error al eliminar');
        }

      } catch (error) {
        console.error('❌ Error:', error);
        Utils.showToast(error.message || 'Error al eliminar', 'error');
      }
    }
  };

  // ========================================
  // 7. GESTOR DE VACIAR CARRITO
  // ========================================
  const ClearCartManager = {
    init() {
      const clearBtn = document.getElementById('btn-clear-cart');
      if (clearBtn) {
        clearBtn.addEventListener('click', () => this.confirmClear());
      }
    },

    async confirmClear() {
      if (typeof Swal === 'undefined') {
        if (!confirm('¿Estás seguro de que deseas vaciar el carrito?')) {
          return;
        }
      } else {
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
          backdrop: 'rgba(0,0,0,0.5)',
          showClass: {
            popup: 'animate__animated animate__fadeInDown animate__faster'
          },
          hideClass: {
            popup: 'animate__animated animate__fadeOutUp animate__faster'
          }
        });
        
        if (!result.isConfirmed) {
          return;
        }
      }

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

        const data = await response.json();

        if (data.success) {
          Utils.showToast('Carrito vaciado exitosamente', 'success');
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else {
          throw new Error(data.message || 'Error al vaciar el carrito');
        }
      } catch (error) {
        console.error('❌ Error:', error);
        Utils.showToast(error.message || 'Error al vaciar el carrito', 'error');
      }
    }
  };

  // ========================================
  // 8. GESTOR DE BOTÓN FINALIZAR
  // ========================================
  const CheckoutManager = {
    init() {
      const checkoutBtn = document.getElementById('finalizar-pedido-modern');
      if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => this.handleCheckout());
      }
    },

    handleCheckout() {
      const selectedCheckboxes = document.querySelectorAll('.cart-checkbox-modern:checked:not(#toggleSelectAll)');
      
      if (selectedCheckboxes.length === 0) {
        Utils.showToast('Selecciona al menos un producto', 'error');
        return;
      }

      // Redirigir a checkout
      window.location.href = '/checkout/';
    }
  };

  // ========================================
  // 9. INICIALIZACIÓN
  // ========================================
  document.addEventListener('DOMContentLoaded', () => {
    console.log('🛒 Inicializando Cart Manager...');
    console.log('==========================================');
    
    CheckboxManager.init();
    ButtonsManager.init();
    RemoveManager.init();
    ClearCartManager.init();
    CheckoutManager.init();
    
    console.log('==========================================');
    console.log('✅ Cart Manager listo');
  });

})();
