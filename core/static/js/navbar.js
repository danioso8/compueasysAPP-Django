// Navbar moderno con overlay y animaciones
(function() {
  'use strict';
  
  document.addEventListener("DOMContentLoaded", function () {
    const nav = document.querySelector(".navbar");
    const toggle = document.querySelector(".menu-toggle");
    const menu = document.getElementById("nav-menu");
    
    if (!toggle || !menu || !nav) return;
    
    // Crear overlay si no existe
    let overlay = document.querySelector('.nav-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'nav-overlay';
      document.body.appendChild(overlay);
    }
    
    // Función para abrir menú
    function openMenu() {
      nav.classList.add("open");
      menu.classList.add("open");
      overlay.classList.add("active");
      document.body.style.overflow = 'hidden'; // Prevenir scroll
      toggle.setAttribute("aria-expanded", "true");
      toggle.setAttribute("aria-label", "Cerrar menú");
    }
    
    // Función para cerrar menú
    function closeMenu() {
      nav.classList.remove("open");
      menu.classList.remove("open");
      overlay.classList.remove("active");
      document.body.style.overflow = ''; // Restaurar scroll
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Abrir menú");
    }
    
    // Toggle del menú
    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      if (nav.classList.contains("open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });
    
    // Cerrar al hacer clic en overlay
    overlay.addEventListener('click', closeMenu);
    
    // Cerrar al hacer clic en un link del menú
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
      }, 100);
    });
    
    // Cerrar con tecla Escape
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && nav.classList.contains("open")) {
        closeMenu();
      }
    });
    
    // Efecto scroll en navbar
    let lastScroll = 0;
    window.addEventListener('scroll', function() {
      const currentScroll = window.pageYOffset;
      
      if (currentScroll > 50) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
      
      lastScroll = currentScroll;
    });
  });
})();
