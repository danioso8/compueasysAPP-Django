/**
 * ========================================
 * NAVBAR MODERNO - CompuEasys
 * Versión 3.0 - Menú responsive con carrito
 * ========================================
 */

(function() {
  'use strict';
  
  // === Inicialización al cargar el DOM ===
  document.addEventListener("DOMContentLoaded", function () {
    initializeNavbar();
    initializeScrollIndicator();
    initializeCart();
    initializeActiveLink();
  });
  
  /**
   * Inicializa el navbar y menú mobile
   */
  function initializeNavbar() {
    const nav = document.querySelector(".navbar");
    const toggle = document.querySelector(".menu-toggle");
    const menu = document.getElementById("nav-menu");
    
    if (!toggle || !menu || !nav) {
      console.warn('Navbar: Elementos no encontrados');
      return;
    }
    
    // Crear overlay si no existe
    let overlay = document.querySelector('.nav-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'nav-overlay';
      overlay.setAttribute('aria-hidden', 'true');
      document.body.appendChild(overlay);
    }
    
    // === Funciones de control del menú ===
    
    function openMenu() {
      nav.classList.add("open");
      menu.classList.add("open");
      overlay.classList.add("active");
      document.body.style.overflow = 'hidden'; // Bloquear scroll
      toggle.setAttribute("aria-expanded", "true");
      toggle.setAttribute("aria-label", "Cerrar menú de navegación");
      
      // Focus trap: enfocar primer link
      const firstLink = menu.querySelector('a');
      if (firstLink) {
        setTimeout(() => firstLink.focus(), 100);
      }
    }
    
    function closeMenu() {
      nav.classList.remove("open");
      menu.classList.remove("open");
      overlay.classList.remove("active");
      document.body.style.overflow = ''; // Restaurar scroll
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Abrir menú de navegación");
    }
    
    function toggleMenu(e) {
      e.stopPropagation();
      if (nav.classList.contains("open")) {
        closeMenu();
      } else {
        openMenu();
      }
    }
    
    // === Event Listeners ===
    
    // Toggle al hacer clic en hamburguesa
    toggle.addEventListener("click", toggleMenu);
    
    // Cerrar al hacer clic en overlay
    overlay.addEventListener('click', closeMenu);
    
    // Cerrar al hacer clic en cualquier link del menú
    menu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
          closeMenu();
        }
      });
    });
    
    // Cerrar al redimensionar a desktop
    let resizeTimer;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function() {
        if (window.innerWidth > 768 && nav.classList.contains("open")) {
          closeMenu();
        }
      }, 150);
    });
    
    // Cerrar con tecla Escape
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && nav.classList.contains("open")) {
        closeMenu();
        toggle.focus(); // Devolver focus al botón
      }
    });
    
    // Efecto de scroll en navbar (glassmorphism)
    let lastScroll = 0;
    let ticking = false;
    
    window.addEventListener('scroll', function() {
      if (!ticking) {
        window.requestAnimationFrame(function() {
          const currentScroll = window.pageYOffset;
          
          if (currentScroll > 50) {
            nav.classList.add('scrolled');
          } else {
            nav.classList.remove('scrolled');
          }
          
          lastScroll = currentScroll;
          ticking = false;
        });
        
        ticking = true;
      }
    });
  }
  
  /**
   * Inicializa la barra de progreso de scroll
   */
  function initializeScrollIndicator() {
    const indicator = document.getElementById('scroll-indicator');
    if (!indicator) return;
    
    let ticking = false;
    
    window.addEventListener('scroll', function() {
      if (!ticking) {
        window.requestAnimationFrame(function() {
          const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
          const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
          const scrollPercent = (scrollTop / docHeight) * 100;
          
          indicator.style.width = scrollPercent + '%';
          ticking = false;
        });
        
        ticking = true;
      }
    });
  }
  
  /**
   * Inicializa el contador del carrito de compras
   */
  function initializeCart() {
    updateCartCount();
    
    // Escuchar eventos personalizados de actualización del carrito
    window.addEventListener('cartUpdated', function(e) {
      updateCartCount();
    });
    
    // Actualizar desde localStorage periódicamente
    setInterval(updateCartCount, 2000);
  }
  
  /**
   * Actualiza el contador del carrito
   */
  function updateCartCount() {
    const cartBadge = document.getElementById('cart-count');
    if (!cartBadge) return;
    
    try {
      // Intentar obtener del localStorage (si existe)
      const cart = localStorage.getItem('cart');
      let itemCount = 0;
      
      if (cart) {
        const cartData = JSON.parse(cart);
        
        // Contar items según estructura del carrito
        if (Array.isArray(cartData)) {
          itemCount = cartData.reduce((total, item) => {
            return total + (parseInt(item.quantity) || 0);
          }, 0);
        } else if (typeof cartData === 'object') {
          itemCount = Object.values(cartData).reduce((total, item) => {
            return total + (parseInt(item.quantity) || 0);
          }, 0);
        }
      }
      
      // Actualizar badge
      cartBadge.textContent = itemCount;
      cartBadge.setAttribute('data-count', itemCount);
      
      // Animación al cambiar
      if (itemCount > 0) {
        cartBadge.style.animation = 'none';
        setTimeout(() => {
          cartBadge.style.animation = 'pulse 2s infinite';
        }, 10);
      }
      
    } catch (error) {
      console.error('Error al actualizar contador del carrito:', error);
    }
  }
  
  /**
   * Marca el link activo según la URL actual
   */
  function initializeActiveLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-list a');
    
    navLinks.forEach(link => {
      const linkPath = new URL(link.href).pathname;
      
      if (linkPath === currentPath) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }
  
  // === API Pública (para uso desde otros scripts) ===
  
  window.CompuEasysNavbar = {
    /**
     * Actualiza manualmente el contador del carrito
     * @param {number} count - Nuevo número de items
     */
    setCartCount: function(count) {
      const cartBadge = document.getElementById('cart-count');
      if (cartBadge) {
        cartBadge.textContent = count;
        cartBadge.setAttribute('data-count', count);
      }
    },
    
    /**
     * Dispara evento de actualización del carrito
     */
    triggerCartUpdate: function() {
      window.dispatchEvent(new CustomEvent('cartUpdated'));
    },
    
    /**
     * Cierra el menú mobile programáticamente
     */
    closeMenu: function() {
      const nav = document.querySelector(".navbar");
      const menu = document.getElementById("nav-menu");
      const overlay = document.querySelector('.nav-overlay');
      
      if (nav) nav.classList.remove("open");
      if (menu) menu.classList.remove("open");
      if (overlay) overlay.classList.remove("active");
      document.body.style.overflow = '';
    }
  };
  
})();
