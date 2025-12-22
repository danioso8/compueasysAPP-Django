/* ========================================
   STORE MODERNO JAVASCRIPT - COMPUEASYS
   Sistema avanzado de filtros y experiencia táctil
======================================== */

(function() {
  'use strict';

  // Estado global del store
  const StoreState = {
    filters: {
      category: '',
      priceMin: 0,
      priceMax: 5000000,
      inStock: true,
      outOfStock: true,  // Por defecto mostrar productos agotados
      search: ''
    },
    sort: 'name',
    view: 'grid',
    isLoading: false,
    searchTimeout: null,
    currentPage: 1,
    hasMore: true
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

    // Formatear precio
    formatPrice(price) {
      return new Intl.NumberFormat('es-CO').format(price);
    },

    // Debounce function
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

    // Mostrar notificación toast
    showToast(message, type = 'success') {
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
      const bgColor = type === 'success' ? '#10b981' : 
                     type === 'error' ? '#ef4444' : 
                     type === 'warning' ? '#f59e0b' : '#06b6d4';
      
      toast.style.cssText = `
        background: ${bgColor};
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

      requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
      });

      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }, 4000);
    },

    // Vibración táctil
    vibrate(pattern = [50]) {
      if ('vibrate' in navigator) {
        navigator.vibrate(pattern);
      }
    },

    // Detectar dispositivo táctil
    isTouchDevice() {
      return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
  };

  // Gestor de búsqueda
  const SearchManager = {
    init() {
      console.log('🔍 Initializing SearchManager...');
      
      const searchInput = document.getElementById('search-input');
      const searchClear = document.getElementById('search-clear');
      const searchSuggestions = document.getElementById('search-suggestions');

      if (!searchInput) return;

      // Búsqueda en tiempo real con debounce
      const debouncedSearch = Utils.debounce((query) => {
        this.performSearch(query);
      }, 300);

      searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        
        if (query.length === 0) {
          this.clearSearch();
          return;
        }

        this.showSearchClear(true);
        debouncedSearch(query);
      });

      // Limpiar búsqueda
      if (searchClear) {
        searchClear.addEventListener('click', () => {
          this.clearSearch();
        });
      }

      // Sugerencias al hacer foco
      searchInput.addEventListener('focus', () => {
        if (searchInput.value.length > 0) {
          this.showSuggestions();
        }
      });

      // Cerrar sugerencias al perder foco
      document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
          this.hideSuggestions();
        }
      });

      // Navegación con teclado
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.hideSuggestions();
        }
      });
    },

    performSearch(query) {
      console.log('🔍 Performing search:', query);
      
      StoreState.filters.search = query;
      StoreState.currentPage = 1;
      
      // Actualizar URL
      this.updateURL();
      
      // Mostrar sugerencias si hay query
      if (query.length > 2) {
        this.fetchSuggestions(query);
      }
      
      // Ejecutar filtrado
      FilterManager.applyFilters();
    },

    fetchSuggestions(query) {
      // Fetch sugerencias del backend
      fetch(`/api/search-suggestions/?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success && data.suggestions) {
          this.displaySuggestions(data.suggestions);
        }
      })
      .catch(error => {
        console.error('Error fetching suggestions:', error);
      });
    },

    displaySuggestions(suggestions) {
      const suggestionsContainer = document.getElementById('search-suggestions');
      if (!suggestionsContainer) return;

      if (suggestions.length === 0) {
        this.hideSuggestions();
        return;
      }

      suggestionsContainer.innerHTML = suggestions.map(suggestion => `
        <div class="suggestion-item" data-suggestion="${suggestion}">
          <i class="bi bi-search me-2"></i>
          ${suggestion}
        </div>
      `).join('');

      // Event listeners para sugerencias
      suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
          const suggestion = item.dataset.suggestion;
          document.getElementById('search-input').value = suggestion;
          this.performSearch(suggestion);
          this.hideSuggestions();
        });
      });

      this.showSuggestions();
    },

    showSuggestions() {
      const suggestionsContainer = document.getElementById('search-suggestions');
      if (suggestionsContainer) {
        suggestionsContainer.style.display = 'block';
      }
    },

    hideSuggestions() {
      const suggestionsContainer = document.getElementById('search-suggestions');
      if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
      }
    },

    showSearchClear(show) {
      const searchClear = document.getElementById('search-clear');
      if (searchClear) {
        searchClear.style.display = show ? 'flex' : 'none';
      }
    },

    clearSearch() {
      const searchInput = document.getElementById('search-input');
      if (searchInput) {
        searchInput.value = '';
        this.showSearchClear(false);
        this.hideSuggestions();
        
        StoreState.filters.search = '';
        this.updateURL();
        FilterManager.applyFilters();
      }
    },

    updateURL() {
      const params = new URLSearchParams();
      if (StoreState.filters.search) {
        params.set('q', StoreState.filters.search);
      }
      if (StoreState.filters.category) {
        params.set('category', StoreState.filters.category);
      }
      
      const newURL = `${window.location.pathname}?${params.toString()}`;
      window.history.pushState({}, '', newURL);
    }
  };

  // Gestor de filtros
  const FilterManager = {
    init() {
      console.log('🎯 Initializing FilterManager...');
      
      this.bindCategoryFilters();
      this.bindPriceFilters();
      this.bindStockFilters();
      this.bindFilterActions();
      this.bindSortOptions();
      this.bindViewToggle();
      
      // Inicializar filtros desde URL
      this.loadFiltersFromURL();
    },

    bindCategoryFilters() {
      const categoryInputs = document.querySelectorAll('input[name="category"]');
      categoryInputs.forEach(input => {
        input.addEventListener('change', (e) => {
          StoreState.filters.category = e.target.value;
          console.log('📦 Category filter changed:', StoreState.filters.category);
          this.applyFilters();
        });
      });
    },

    bindPriceFilters() {
      const priceMin = document.getElementById('price-min');
      const priceMax = document.getElementById('price-max');
      const priceRange = document.getElementById('price-range');

      if (priceMin && priceMax) {
        const debouncedPriceUpdate = Utils.debounce(() => {
          StoreState.filters.priceMin = parseInt(priceMin.value) || 0;
          StoreState.filters.priceMax = parseInt(priceMax.value) || 5000000;
          console.log('💰 Price filter changed:', StoreState.filters.priceMin, '-', StoreState.filters.priceMax);
          this.applyFilters();
        }, 500);

        priceMin.addEventListener('input', debouncedPriceUpdate);
        priceMax.addEventListener('input', debouncedPriceUpdate);
      }

      if (priceRange) {
        priceRange.addEventListener('input', (e) => {
          const value = parseInt(e.target.value);
          StoreState.filters.priceMax = value;
          if (priceMax) priceMax.value = value;
          console.log('💰 Price range changed:', value);
          this.applyFilters();
        });
      }
    },

    bindStockFilters() {
      const inStockCheckbox = document.querySelector('input[name="in_stock"]');
      const outOfStockCheckbox = document.querySelector('input[name="out_of_stock"]');

      // Sincronizar estado inicial con checkboxes del HTML
      if (inStockCheckbox) {
        StoreState.filters.inStock = inStockCheckbox.checked;
        inStockCheckbox.addEventListener('change', (e) => {
          StoreState.filters.inStock = e.target.checked;
          console.log('📦 In Stock filter changed:', StoreState.filters.inStock);
          this.applyFilters();
        });
      }

      if (outOfStockCheckbox) {
        StoreState.filters.outOfStock = outOfStockCheckbox.checked;
        outOfStockCheckbox.addEventListener('change', (e) => {
          StoreState.filters.outOfStock = e.target.checked;
          console.log('❌ Out of Stock filter changed:', StoreState.filters.outOfStock);
          this.applyFilters();
        });
      }
    },

    bindFilterActions() {
      const applyBtn = document.getElementById('apply-filters');
      const clearBtn = document.getElementById('clear-filters');

      if (applyBtn) {
        applyBtn.addEventListener('click', () => {
          console.log('✅ Apply filters clicked');
          this.applyFilters();
          Utils.vibrate([30]);
        });
      }

      if (clearBtn) {
        clearBtn.addEventListener('click', () => {
          console.log('🔄 Clear filters clicked');
          this.clearFilters();
          Utils.vibrate([50, 30]);
        });
      }
    },

    bindSortOptions() {
      const sortSelect = document.getElementById('sort-select');
      if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
          StoreState.sort = e.target.value;
          console.log('🔀 Sort changed:', StoreState.sort);
          this.applyFilters();
        });
      }
    },

    bindViewToggle() {
      const viewButtons = document.querySelectorAll('.view-btn');
      console.log('🔲 Binding view toggle buttons:', viewButtons.length, 'buttons found');
      
      if (viewButtons.length === 0) {
        console.warn('⚠️ No view buttons found in DOM');
        return;
      }
      
      viewButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const view = e.currentTarget.dataset.view;
          console.log('🔲 View button clicked:', view);
          this.switchView(view);
        });
      });
      
      console.log('✅ View toggle buttons bound successfully');
    },

    switchView(view) {
      StoreState.view = view;
      console.log('👁️ View changed to:', view);

      // Actualizar botones
      document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('active');
      });
      
      const activeBtn = document.querySelector(`[data-view="${view}"]`);
      if (activeBtn) {
        activeBtn.classList.add('active');
        console.log('✅ Active button updated:', view);
      } else {
        console.warn('⚠️ Active button not found for view:', view);
      }

      // Actualizar grid - aplicar clase a todos los products-grid dentro del container
      const productsGrids = document.querySelectorAll('.products-grid');
      console.log('🔲 Found', productsGrids.length, 'product grids to update');
      
      if (productsGrids.length > 0) {
        const newClass = view === 'list' ? 'products-list' : 'products-grid';
        productsGrids.forEach((grid, index) => {
          grid.className = newClass;
          console.log(`  Grid ${index + 1}: Changed to ${newClass}`);
        });
        console.log('✅ All grids updated successfully');
      } else {
        console.warn('⚠️ No product grids found to update');
      }

      Utils.vibrate([20]);
    },

    applyFilters() {
      if (StoreState.isLoading) return;
      
      console.log('🎯 Applying filters:', StoreState.filters);
      
      StoreState.isLoading = true;
      this.showLoading(true);

      // Construir parámetros de filtro
      const params = new URLSearchParams();
      
      if (StoreState.filters.search) {
        params.set('q', StoreState.filters.search);
      }
      if (StoreState.filters.category) {
        params.set('category', StoreState.filters.category);
      }
      if (StoreState.filters.priceMin > 0) {
        params.set('price_min', StoreState.filters.priceMin);
      }
      if (StoreState.filters.priceMax < 5000000) {
        params.set('price_max', StoreState.filters.priceMax);
      }
      if (StoreState.filters.inStock) {
        params.set('in_stock', 'true');
      }
      if (StoreState.filters.outOfStock) {
        params.set('out_of_stock', 'true');
      }
      if (StoreState.sort) {
        params.set('sort', StoreState.sort);
      }

      // Hacer petición AJAX
      fetch(`/api/filter-products/?${params.toString()}`, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          // Actualizar contenido
          const productsContainer = document.getElementById('products-container');
          if (productsContainer) {
            productsContainer.innerHTML = data.html;
          }
          
          // Actualizar contador de resultados
          this.updateResultsCount(data.count);
          
          // Re-inicializar lazy loading para nuevas imágenes
          LazyLoadManager.observeImages();
          
          // 🔧 RE-INICIALIZAR EVENT LISTENERS para nuevos productos
          this.reinitializeProductEvents();
          
          // Mostrar mensaje si hay resultados
          if (data.count > 0) {
            Utils.showToast(data.message || `${data.count} productos encontrados`, 'info');
          } else {
            Utils.showToast('No se encontraron productos con esos filtros', 'warning');
          }
          
        } else {
          console.error('Server error:', data.error || 'Unknown error');
          Utils.showToast(`Error del servidor: ${data.error || 'Error desconocido'}`, 'error');
        }
      })
      .catch(error => {
        console.error('Filter error:', error);
        Utils.showToast(`Error de conexión: ${error.message || 'Error desconocido'}`, 'error');
      })
      .finally(() => {
        this.showLoading(false);
        StoreState.isLoading = false;
      });
    },

    // Método legacy para compatibilidad - ahora se usa AJAX
    filterProducts() {
      console.log('🔄 Using legacy filter method - consider using AJAX');
      // Este método se mantiene para compatibilidad pero se recomienda usar AJAX
    },

    shouldShowProduct(card) {
      // Obtener datos del producto (en producción vendría del servidor)
      const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
      const category = card.querySelector('.card-category')?.textContent.toLowerCase() || '';
      const priceText = card.querySelector('.price-current')?.textContent || '';
      const price = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;
      const hasStock = !card.querySelector('.stock-badge.out-of-stock');

      // Filtro de búsqueda
      if (StoreState.filters.search) {
        const searchTerm = StoreState.filters.search.toLowerCase();
        if (!title.includes(searchTerm) && !category.includes(searchTerm)) {
          return false;
        }
      }

      // Filtro de categoría (simplificado para demo)
      if (StoreState.filters.category) {
        // En producción, esto se haría con datos del servidor
      }

      // Filtro de precio
      if (price < StoreState.filters.priceMin || price > StoreState.filters.priceMax) {
        return false;
      }

      // Filtro de stock
      if (!StoreState.filters.inStock && hasStock) {
        return false;
      }
      if (!StoreState.filters.outOfStock && !hasStock) {
        return false;
      }

      return true;
    },

    showProduct(card) {
      card.style.display = 'block';
      card.style.animation = 'fadeInUp 0.3s ease-out';
    },

    hideProduct(card) {
      card.style.display = 'none';
    },

    updateResultsCount(count) {
      const resultsCount = document.querySelector('.results-count');
      if (resultsCount) {
        resultsCount.textContent = `${count} producto${count !== 1 ? 's' : ''}`;
      }
    },

    showEmptyState() {
      let emptyState = document.querySelector('.empty-state');
      if (!emptyState) {
        const productsContainer = document.getElementById('products-container');
        if (productsContainer) {
          emptyState = document.createElement('div');
          emptyState.className = 'empty-state';
          emptyState.innerHTML = `
            <div class="empty-icon">
              <i class="bi bi-search"></i>
            </div>
            <h3 class="empty-title">No se encontraron productos</h3>
            <p class="empty-subtitle">
              Intenta ajustar los filtros o la búsqueda
            </p>
            <div class="empty-actions">
              <button class="btn-primary" onclick="FilterManager.clearFilters()">
                Limpiar filtros
              </button>
            </div>
          `;
          productsContainer.appendChild(emptyState);
        }
      }
      
      if (emptyState) {
        emptyState.style.display = 'flex';
      }
    },

    hideEmptyState() {
      const emptyState = document.querySelector('.empty-state');
      if (emptyState) {
        emptyState.style.display = 'none';
      }
    },

    clearFilters() {
      // Reset filtros
      StoreState.filters = {
        category: '',
        priceMin: 0,
        priceMax: 5000000,
        inStock: true,
        outOfStock: true,  // Mantener productos agotados visibles
        search: ''
      };

      // Reset UI
      document.querySelectorAll('input[name="category"]').forEach(input => {
        input.checked = input.value === '';
      });

      const priceMin = document.getElementById('price-min');
      const priceMax = document.getElementById('price-max');
      if (priceMin) priceMin.value = '';
      if (priceMax) priceMax.value = '';

      const searchInput = document.getElementById('search-input');
      if (searchInput) {
        searchInput.value = '';
        SearchManager.showSearchClear(false);
      }

      // Reset stock filters checkboxes
      const inStockCheckbox = document.querySelector('input[name="in_stock"]');
      const outOfStockCheckbox = document.querySelector('input[name="out_of_stock"]');
      if (inStockCheckbox) inStockCheckbox.checked = true;
      if (outOfStockCheckbox) outOfStockCheckbox.checked = true;

      // Aplicar filtros limpios
      this.applyFilters();
      
      Utils.showToast('Filtros eliminados', 'info');
    },

    // Re-inicializar eventos para productos cargados dinámicamente
    reinitializeProductEvents() {
      console.log('🔄 Re-inicializando eventos de productos...');
      
      // Re-inicializar CartManager para los nuevos botones de "Agregar al carrito"
      // (Los event listeners ya están en el document, pero verificamos)
      
      // Re-inicializar lazy loading
      if (window.LazyLoadManager && LazyLoadManager.observeImages) {
        LazyLoadManager.observeImages();
      }
      
      // Re-inicializar tooltips de Bootstrap si existen
      const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
      if (window.bootstrap && bootstrap.Tooltip) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
          return new bootstrap.Tooltip(tooltipTriggerEl);
        });
      }
      
      console.log('✅ Eventos de productos re-inicializados');
    },

    showLoading(show) {
      const loadingState = document.getElementById('loading-state');
      if (loadingState) {
        loadingState.style.display = show ? 'flex' : 'none';
      }
    },

    loadFiltersFromURL() {
      const params = new URLSearchParams(window.location.search);
      
      if (params.has('q')) {
        StoreState.filters.search = params.get('q');
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
          searchInput.value = StoreState.filters.search;
          SearchManager.showSearchClear(true);
        }
      }

      if (params.has('category')) {
        StoreState.filters.category = params.get('category');
        const categoryInput = document.querySelector(`input[name="category"][value="${StoreState.filters.category}"]`);
        if (categoryInput) {
          categoryInput.checked = true;
        }
      }
    }
  };

  // Gestor de sidebar móvil
  const SidebarManager = {
    init() {
      console.log('📱 Initializing SidebarManager...');
      
      const filtersToggle = document.getElementById('filters-toggle');
      const sidebarClose = document.getElementById('sidebar-close');
      const sidebar = document.getElementById('filters-sidebar');

      if (filtersToggle && sidebar) {
        filtersToggle.addEventListener('click', () => {
          this.toggleSidebar();
        });
      }

      if (sidebarClose && sidebar) {
        sidebarClose.addEventListener('click', () => {
          this.closeSidebar();
        });
      }

      // Cerrar con overlay click
      document.addEventListener('click', (e) => {
        if (sidebar && sidebar.classList.contains('open')) {
          if (!sidebar.contains(e.target) && !filtersToggle.contains(e.target)) {
            this.closeSidebar();
          }
        }
      });
    },

    toggleSidebar() {
      const sidebar = document.getElementById('filters-sidebar');
      if (sidebar) {
        sidebar.classList.toggle('open');
        Utils.vibrate([30]);
      }
    },

    closeSidebar() {
      const sidebar = document.getElementById('filters-sidebar');
      if (sidebar) {
        sidebar.classList.remove('open');
      }
    }
  };

  // Gestor de carrito
  const CartManager = {
    init() {
      console.log('🛒 Initializing CartManager...');
      
      document.addEventListener('click', (e) => {
        if (e.target.closest('.add-to-cart-form')) {
          e.preventDefault();
          this.handleAddToCart(e.target.closest('.add-to-cart-form'));
        }
        
        // Manejar botón de notificación de stock
        if (e.target.closest('.btn-notify-stock')) {
          e.preventDefault();
          const button = e.target.closest('.btn-notify-stock');
          const productId = button.dataset.productId || button.dataset.product;
          this.handleStockNotification(productId);
        }
      });

      // Actualizar contador del carrito desde session storage si existe
      this.updateCartCount();
      
      // Inicializar comportamiento del carrito flotante
      this.initFloatingCart();
    },

    initFloatingCart() {
      const floatingCart = document.querySelector('.floating-cart');
      const cartPreview = document.getElementById('cart-preview');
      let scrollTimeout;
      
      if (!floatingCart) return;

      // Efecto de movimiento suave al hacer scroll
      let lastScrollY = window.scrollY;
      
      window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        // Agregar clase durante el scroll
        floatingCart.classList.add('scrolling');
        
        // Remover clase después del scroll
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          floatingCart.classList.remove('scrolling');
        }, 150);
        
        // Efecto de parallax sutil
        const scrollDifference = currentScrollY - lastScrollY;
        if (Math.abs(scrollDifference) > 5) {
          floatingCart.style.transform = `translateY(${scrollDifference * 0.1}px)`;
          
          setTimeout(() => {
            floatingCart.style.transform = '';
          }, 300);
        }
        
        lastScrollY = currentScrollY;
      }, { passive: true });

      // Cargar preview del carrito al hacer hover
      const cartToggleBtn = document.querySelector('.cart-toggle-btn');
      if (cartToggleBtn) {
        cartToggleBtn.addEventListener('mouseenter', () => {
          this.loadCartPreview();
        });
      }

      // Cerrar preview al perder el hover con delay
      let hoverTimeout;
      floatingCart.addEventListener('mouseenter', () => {
        clearTimeout(hoverTimeout);
      });

      floatingCart.addEventListener('mouseleave', () => {
        hoverTimeout = setTimeout(() => {
          if (cartPreview) {
            cartPreview.style.opacity = '0';
            cartPreview.style.visibility = 'hidden';
          }
        }, 200);
      });
    },

    async loadCartPreview() {
      console.log('🔄 [CartPreview] Iniciando actualización...');
      
      try {
        // Obtener el HTML actualizado del carrito desde el servidor
        const response = await fetch('/cart-preview/', {
          method: 'GET',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
          }
        });

        if (response.ok) {
          const data = await response.json();
          console.log('📦 [CartPreview] Datos recibidos:', {
            success: data.success,
            cart_count: data.cart_count,
            has_html: !!data.cart_items_html,
            html_length: data.cart_items_html?.length
          });
          
          if (!data.success) {
            console.error('❌ [CartPreview] Servidor retornó error:', data.error);
            return;
          }
          
          // Buscar elementos del DOM
          const cartItemsContainer = document.getElementById('cart-items-container');
          const cartSidebarContent = document.querySelector('.cart-sidebar-content');
          const cartSidebarFooter = document.querySelector('.cart-sidebar-footer');
          
          console.log('🔍 [CartPreview] Elementos DOM:', {
            cartItemsContainer: !!cartItemsContainer,
            cartSidebarContent: !!cartSidebarContent,
            cartSidebarFooter: !!cartSidebarFooter
          });
          
          if (data.cart_count > 0 && data.cart_items_html) {
            // HAY PRODUCTOS EN EL CARRITO
            console.log('✅ [CartPreview] Actualizando con', data.cart_count, 'productos');
            
            if (cartItemsContainer) {
              // Actualizar HTML de los items
              cartItemsContainer.innerHTML = data.cart_items_html;
              console.log('✅ [CartPreview] HTML insertado en cart-items-container');
              
              // Asegurar que el contenedor esté visible
              if (cartSidebarContent) {
                cartSidebarContent.style.display = 'block';
                
                // Remover mensaje de vacío si existe
                const emptyState = cartSidebarContent.querySelector('.cart-empty-state');
                if (emptyState) {
                  console.log('🗑️ [CartPreview] Removiendo mensaje de carrito vacío');
                  emptyState.remove();
                }
              }
              
              // Mostrar footer con totales
              if (cartSidebarFooter) {
                cartSidebarFooter.classList.remove('d-none');
                cartSidebarFooter.style.display = 'block';
                
                // Actualizar total
                const cartTotalAmount = document.getElementById('cart-total-amount');
                if (cartTotalAmount && data.cart_total) {
                  cartTotalAmount.textContent = data.cart_total;
                  console.log('✅ [CartPreview] Total actualizado:', data.cart_total);
                }
              }
            } else {
              console.error('❌ [CartPreview] No se encontró #cart-items-container');
            }
          } else {
            // CARRITO VACÍO
            console.log('ℹ️ [CartPreview] Carrito vacío, mostrando mensaje');
            
            if (cartSidebarContent) {
              cartSidebarContent.innerHTML = `
                <div class="cart-empty-state">
                  <i class="bi bi-cart-x"></i>
                  <h4>Tu carrito está vacío</h4>
                  <p>Agrega productos para empezar a comprar</p>
                  <a href="/store" class="btn-continue-shopping">
                    <i class="bi bi-shop me-2"></i>Ir a la tienda
                  </a>
                </div>
              `;
            }
            
            // Ocultar footer
            if (cartSidebarFooter) {
              cartSidebarFooter.classList.add('d-none');
              cartSidebarFooter.style.display = 'none';
            }
          }
          
          console.log('✅ [CartPreview] Actualización completada');
        } else {
          console.error('❌ [CartPreview] Error HTTP:', response.status, response.statusText);
        }
      } catch (error) {
        console.error('❌ [CartPreview] Error en fetch:', error);
      }
    },

    async handleAddToCart(form) {
      const productId = form.dataset.product;
      const submitBtn = form.querySelector('.btn-add-cart');
      
      if (!productId || !submitBtn) return;

      console.log('🛒 Adding to cart:', productId);

      // UI feedback
      const originalContent = submitBtn.innerHTML;
      submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> <span>Agregando...</span>';
      submitBtn.disabled = true;

      try {
        const formData = new FormData();
        formData.append('quantity', '1');
        formData.append('csrfmiddlewaretoken', Utils.getCsrfToken());

        const response = await fetch(`/add-to-cart/${productId}/`, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.ok) {
          const data = await response.json();
          
          // Feedback exitoso
          submitBtn.innerHTML = '<i class="bi bi-check"></i> <span>¡Agregado!</span>';
          submitBtn.style.background = '#10b981';
          
          Utils.showToast('Producto agregado al carrito', 'success');
          Utils.vibrate([30, 20, 30]);
          
          // Actualizar todos los contadores inmediatamente
          if (data.cart_count !== undefined) {
            const count = data.cart_count;
            console.log('🔢 Actualizando contadores con:', count);
            
            // Badge del navbar
            const navCartCount = document.querySelector('.action-btn.cart-btn .cart-count');
            if (navCartCount) {
              navCartCount.textContent = count;
              navCartCount.style.display = count > 0 ? 'block' : 'none';
              console.log('✅ Nav cart count actualizado:', count);
            }
            
            // Badge del cart flotante (PRINCIPAL - arriba derecha)
            const cartFloatBadge = document.getElementById('cart-badge-float');
            if (cartFloatBadge) {
              cartFloatBadge.textContent = count;
              cartFloatBadge.style.display = count > 0 ? 'block' : 'none';
              // Forzar re-render
              cartFloatBadge.classList.add('pulse-animation');
              console.log('✅ Float cart badge actualizado:', count);
            } else {
              console.warn('⚠️ cart-badge-float NO encontrado en DOM');
            }
            
            // Badge del sidebar
            const cartCountSidebar = document.getElementById('cart-count-sidebar');
            if (cartCountSidebar) {
              cartCountSidebar.textContent = count;
              console.log('✅ Sidebar cart count actualizado:', count);
            }
          }
          
          // Actualizar contador completo (como backup)
          this.updateCartCount();
          
          // Efecto de rebote en ambos carritos
          const floatingCart = document.querySelector('.cart-float-modern');
          if (floatingCart) {
            floatingCart.classList.add('bounce');
            setTimeout(() => {
              floatingCart.classList.remove('bounce');
            }, 600);
          }
          
          const navCartBtn = document.querySelector('.action-btn.cart-btn');
          if (navCartBtn) {
            navCartBtn.classList.add('bounce');
            setTimeout(() => {
              navCartBtn.classList.remove('bounce');
            }, 600);
          }
          
          // Actualizar preview del carrito INMEDIATAMENTE
          console.log('🔄 Llamando a loadCartPreview después de agregar producto...');
          await this.loadCartPreview();
          
          // Restaurar botón después de 2 segundos
          setTimeout(() => {
            submitBtn.innerHTML = originalContent;
            submitBtn.style.background = '';
            submitBtn.disabled = false;
          }, 2000);
          
        } else {
          throw new Error('Error al agregar al carrito');
        }
        
      } catch (error) {
        console.error('Cart error:', error);
        Utils.showToast('Error al agregar al carrito', 'error');
        
        // Restaurar botón
        submitBtn.innerHTML = originalContent;
        submitBtn.disabled = false;
      }
    },

    async updateCartCount() {
      try {
        // Obtener el count real del servidor
        const response = await fetch('/api/cart-count/', {
          method: 'GET',
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          const count = data.count || 0;
          
          console.log('🛒 Actualizando contadores de carrito:', count);
          
          // Actualizar carrito flotante
          const cartBadge = document.querySelector('.cart-badge');
          const cartCountText = document.querySelector('.cart-count-text');
          
          if (cartBadge) {
            cartBadge.textContent = count;
            cartBadge.style.display = count > 0 ? 'flex' : 'none';
          }
          
          if (cartCountText) {
            cartCountText.textContent = count;
          }
          
          // Actualizar contador del header
          const headerCartCount = document.querySelector('.cart-count');
          if (headerCartCount) {
            headerCartCount.textContent = count;
            headerCartCount.style.display = count > 0 ? 'flex' : 'none';
            console.log('✅ Header cart count actualizado:', count);
          }
          
          // Actualizar badge del cart flotante
          const cartFloatBadge = document.getElementById('cart-badge-float');
          if (cartFloatBadge) {
            cartFloatBadge.textContent = count;
            cartFloatBadge.style.display = count > 0 ? 'block' : 'none';
            console.log('✅ Float cart badge actualizado:', count);
          }
          
          // Actualizar contador del sidebar
          const cartCountSidebar = document.getElementById('cart-count-sidebar');
          if (cartCountSidebar) {
            cartCountSidebar.textContent = count;
          }
          
          // Animar contador si cambió
          if (count > 0) {
            const floatingCart = document.querySelector('.floating-cart');
            if (floatingCart) {
              floatingCart.classList.add('bounce');
              setTimeout(() => {
                floatingCart.classList.remove('bounce');
              }, 600);
            }
          }
        } else {
          // Fallback - usar sessionStorage si el endpoint no responde
          console.warn('⚠️ No se pudo obtener cart count del servidor, usando fallback');
          const count = parseInt(sessionStorage.getItem('cartCount') || '0');
          
          const cartBadge = document.querySelector('.cart-badge');
          const cartCountText = document.querySelector('.cart-count-text');
          const headerCartCount = document.querySelector('.cart-count');
          
          if (cartBadge) {
            cartBadge.textContent = count;
            cartBadge.style.display = count > 0 ? 'flex' : 'none';
          }
          if (cartCountText) cartCountText.textContent = count;
          if (headerCartCount) headerCartCount.textContent = count;
        }
        
      } catch (error) {
        console.error('❌ Error updating cart count:', error);
        // Fallback en caso de error
        const count = parseInt(sessionStorage.getItem('cartCount') || '0');
        const headerCartCount = document.querySelector('.cart-count');
        if (headerCartCount) headerCartCount.textContent = count;
      }
    },

    // Manejar notificación de stock
    async handleStockNotification(productId) {
      if (!productId) {
        console.error('❌ Product ID not found');
        return;
      }

      console.log('🔔 Handling stock notification for product:', productId);

      // Crear y mostrar modal de notificación
      const modal = this.createNotificationModal(productId);
      document.body.appendChild(modal);

      // Mostrar modal
      const bsModal = new bootstrap.Modal(modal);
      bsModal.show();

      // Limpiar modal cuando se cierre
      modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
      });
    },

    // Crear modal para registrar notificación
    createNotificationModal(productId) {
      const modal = document.createElement('div');
      modal.className = 'modal fade';
      modal.id = 'stockNotificationModal';
      modal.innerHTML = `
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header bg-primary text-white">
              <h5 class="modal-title">
                <i class="bi bi-bell"></i> Notificarme cuando esté disponible
              </h5>
              <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                Te enviaremos un email cuando este producto esté disponible nuevamente.
              </div>
              
              <form id="notificationForm">
                <div class="mb-3">
                  <label for="email" class="form-label">
                    <i class="bi bi-envelope"></i> Email de notificación
                  </label>
                  <input type="email" class="form-control" id="email" required 
                         placeholder="tu-email@ejemplo.com">
                  <div class="form-text">
                    Recibirás notificaciones en este email
                  </div>
                </div>
                
                <div class="notification-options">
                  <h6><i class="bi bi-gear"></i> Opciones adicionales</h6>
                  
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notifyPriceDrop">
                    <label class="form-check-label" for="notifyPriceDrop">
                      <i class="bi bi-tag"></i> Notificarme también si baja el precio
                    </label>
                  </div>
                  
                  <div class="price-target" style="display: none;">
                    <label for="targetPrice" class="form-label">
                      <i class="bi bi-currency-dollar"></i> Notificar si el precio es menor a:
                    </label>
                    <div class="input-group">
                      <span class="input-group-text">$</span>
                      <input type="number" class="form-control" id="targetPrice" 
                             placeholder="Precio objetivo">
                      <span class="input-group-text">COP</span>
                    </div>
                  </div>
                  
                  <div class="form-check mt-2">
                    <input class="form-check-input" type="checkbox" id="notifyLowStock">
                    <label class="form-check-label" for="notifyLowStock">
                      <i class="bi bi-exclamation-triangle text-warning"></i> Notificarme cuando haya poco stock
                    </label>
                  </div>
                </div>
              </form>
              
              <div id="notificationFeedback"></div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                <i class="bi bi-x"></i> Cancelar
              </button>
              <button type="button" class="btn btn-primary" id="submitNotification">
                <i class="bi bi-bell"></i> Activar Notificaciones
              </button>
            </div>
          </div>
        </div>
      `;

      // Event listeners del modal
      this.setupModalEventListeners(modal, productId);

      return modal;
    },

    // Configurar event listeners del modal
    setupModalEventListeners(modal, productId) {
      const form = modal.querySelector('#notificationForm');
      const submitBtn = modal.querySelector('#submitNotification');
      const priceDrop = modal.querySelector('#notifyPriceDrop');
      const priceTarget = modal.querySelector('.price-target');

      // Mostrar/ocultar precio objetivo
      priceDrop.addEventListener('change', () => {
        priceTarget.style.display = priceDrop.checked ? 'block' : 'none';
      });

      // Enviar notificación
      submitBtn.addEventListener('click', async () => {
        await this.submitNotification(modal, productId);
      });

      // Enter en el form
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        submitBtn.click();
      });
    },

    // Enviar registro de notificación
    async submitNotification(modal, productId) {
      const email = modal.querySelector('#email').value.trim();
      const notifyPriceDrop = modal.querySelector('#notifyPriceDrop').checked;
      const targetPrice = modal.querySelector('#targetPrice').value;
      const notifyLowStock = modal.querySelector('#notifyLowStock').checked;
      const submitBtn = modal.querySelector('#submitNotification');
      const feedback = modal.querySelector('#notificationFeedback');

      if (!email) {
        this.showFeedback(feedback, 'Por favor ingresa tu email', 'danger');
        return;
      }

      // Mostrar loading
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Registrando...';
      submitBtn.disabled = true;

      try {
        const response = await fetch('/api/stock-notification/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': Utils.getCsrfToken()
          },
          body: JSON.stringify({
            product_id: productId,
            email: email,
            notification_type: 'stock_available',
            notify_price_drop: notifyPriceDrop,
            target_price: targetPrice || null,
            notify_low_stock: notifyLowStock
          })
        });

        const data = await response.json();

        if (data.success) {
          this.showFeedback(feedback, data.message, 'success');
          Utils.showToast('¡Notificación activada exitosamente!', 'success');
          
          // Cerrar modal después de 2 segundos
          setTimeout(() => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
          }, 2000);
          
        } else {
          this.showFeedback(feedback, data.message, 'danger');
        }

      } catch (error) {
        console.error('❌ Error submitting notification:', error);
        this.showFeedback(feedback, 'Error de conexión. Intenta nuevamente.', 'danger');
      } finally {
        // Restaurar botón
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    },

    // Mostrar feedback en el modal
    showFeedback(container, message, type) {
      container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show">
          <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
          ${message}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      `;
    }
  };

  // Gestor de lazy loading
  const LazyLoadManager = {
    init() {
      console.log('🖼️ Initializing LazyLoadManager...');
      
      if ('IntersectionObserver' in window) {
        this.observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              this.loadImage(entry.target);
              this.observer.unobserve(entry.target);
            }
          });
        }, {
          rootMargin: '50px'
        });

        this.observeImages();
      }
    },

    observeImages() {
      const images = document.querySelectorAll('.card-image[data-src]');
      images.forEach(img => this.observer.observe(img));
    },

    loadImage(img) {
      const src = img.dataset.src;
      if (src) {
        img.src = src;
        img.removeAttribute('data-src');
        img.classList.add('loaded');
      }
    }
  };

  // Gestor de gestos táctiles
  const GestureManager = {
    init() {
      if (!Utils.isTouchDevice()) return;
      
      console.log('👆 Initializing GestureManager...');
      
      document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
      document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
      document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    },

    handleTouchStart(e) {
      this.startX = e.touches[0].clientX;
      this.startY = e.touches[0].clientY;
    },

    handleTouchMove(e) {
      if (!this.startX || !this.startY) return;

      const diffX = e.touches[0].clientX - this.startX;
      const diffY = e.touches[0].clientY - this.startY;

      // Swipe horizontal en productos para acciones rápidas
      const productCard = e.target.closest('.product-card');
      if (productCard && Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        e.preventDefault();
        
        if (diffX > 0) {
          // Swipe derecha - agregar a favoritos
          this.showQuickAction(productCard, 'favorite');
        } else {
          // Swipe izquierda - agregar al carrito
          this.showQuickAction(productCard, 'cart');
        }
      }
    },

    handleTouchEnd() {
      this.startX = null;
      this.startY = null;
    },

    showQuickAction(card, action) {
      // Remover acciones previas
      const existingAction = card.querySelector('.quick-action');
      if (existingAction) existingAction.remove();

      const actionEl = document.createElement('div');
      actionEl.className = 'quick-action';
      
      if (action === 'favorite') {
        actionEl.innerHTML = '<i class="bi bi-heart-fill"></i> Favorito';
        actionEl.style.background = '#f59e0b';
      } else {
        actionEl.innerHTML = '<i class="bi bi-cart-plus"></i> Agregar';
        actionEl.style.background = '#10b981';
      }
      
      actionEl.style.cssText += `
        position: absolute;
        top: 50%;
        right: 16px;
        transform: translateY(-50%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        z-index: 10;
        animation: slideInRight 0.3s ease-out;
      `;
      
      card.appendChild(actionEl);
      Utils.vibrate([50]);
      
      // Remover después de 2 segundos
      setTimeout(() => {
        if (actionEl.parentNode) {
          actionEl.parentNode.removeChild(actionEl);
        }
      }, 2000);
    }
  };

  // Animations CSS
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    @keyframes slideInRight {
      from {
        opacity: 0;
        transform: translateY(-50%) translateX(20px);
      }
      to {
        opacity: 1;
        transform: translateY(-50%) translateX(0);
      }
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    .spin {
      animation: spin 1s linear infinite;
    }
    
    .card-image.loaded {
      animation: fadeInImage 0.3s ease-out;
    }
    
    @keyframes fadeInImage {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    /* Scroll suave para el carrito flotante */
    .floating-cart {
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Efecto de hover mejorado */
    .cart-toggle-btn {
      position: relative;
      overflow: hidden;
    }
    
    .cart-toggle-btn::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 0;
      height: 0;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 50%;
      transform: translate(-50%, -50%);
      transition: width 0.3s ease, height 0.3s ease;
    }
    
    .cart-toggle-btn:hover::before {
      width: 120px;
      height: 120px;
    }
  `;
  document.head.appendChild(style);

  // ============================================
  // MOBILE MENU MANAGER - NUEVO Y LIMPIO
  // ============================================
  const MobileMenuManager = {
    init() {
      const toggle = document.getElementById('mobile-menu-toggle');
      const navbar = document.querySelector('.secondary-navbar');
      const overlay = document.getElementById('mobile-menu-overlay');
      
      if (!toggle || !navbar) {
        console.warn('⚠️ Mobile menu elements not found');
        return;
      }

      // Función para cerrar menú
      const closeMenu = () => {
        toggle.classList.remove('active');
        navbar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        document.body.classList.remove('menu-open');
      };

      // Función para abrir menú
      const openMenu = () => {
        toggle.classList.add('active');
        navbar.classList.add('active');
        if (overlay) overlay.classList.add('active');
        document.body.classList.add('menu-open');
      };

      // Toggle al hacer click en hamburguesa
      toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = navbar.classList.contains('active');
        if (isOpen) {
          closeMenu();
        } else {
          openMenu();
        }
        console.log('🍔 Menu toggled:', !isOpen ? 'OPEN' : 'CLOSED');
      });

      // Cerrar al hacer click en overlay
      if (overlay) {
        overlay.addEventListener('click', closeMenu);
      }

      // Cerrar al hacer click en un link del menú
      const links = navbar.querySelectorAll('.nav-links a');
      links.forEach(link => {
        link.addEventListener('click', closeMenu);
      });

      console.log('✅ Mobile Menu initialized');
    }
  };

  // Inicialización cuando el DOM está listo
  document.addEventListener('DOMContentLoaded', () => {
    console.group('🏪 Store Manager Initialization');
    console.log('Initializing modern store experience...');

    // Inicializar todos los gestores
    SearchManager.init();
    FilterManager.init();
    SidebarManager.init();
    CartManager.init();
    LazyLoadManager.init();
    GestureManager.init();
    MobileMenuManager.init();

    console.log('✅ Store experience initialized successfully');
    console.groupEnd();
  });

  // Exponer managers globalmente para debugging
  window.StoreManagers = {
    Search: SearchManager,
    Filter: FilterManager,
    Sidebar: SidebarManager,
    Cart: CartManager,
    LazyLoad: LazyLoadManager,
    Gesture: GestureManager,
    MobileMenu: MobileMenuManager
  };

})();