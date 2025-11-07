// ...existing code...

// ====== Funcionalidad de menús responsive ======
function initMenuToggle() {
  console.log('🔧 Initializing menu toggles...');
  
  // Verificar que los elementos existan
  const elements = {
    topNavbar: document.querySelector('.top-navbar'),
    menuToggleBtn: document.querySelector('.top-navbar .menu-toggle'),
    navLinks: document.querySelector('.top-navbar .nav-links'),
    navCategorias: document.querySelector('.nav-categorias'),
    toggleCategoriaBtn: document.getElementById('toggle-categoria'),
    navLinksCategoria: document.getElementById('nav-links-categorias')
  };
  
  console.log('🔧 Found elements:', elements);
  
  // Toggle menu principal (top-navbar)
  if (elements.menuToggleBtn && elements.navLinks && elements.topNavbar) {
    console.log('✅ Setting up top navbar toggle');
    elements.menuToggleBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // Toggle clases
      elements.navLinks.classList.toggle('open');
      elements.topNavbar.classList.toggle('open');
      
      // Actualizar aria-expanded
      const isExpanded = elements.navLinks.classList.contains('open');
      elements.menuToggleBtn.setAttribute('aria-expanded', isExpanded);
      
      console.log('🔧 Top navbar toggled:', isExpanded);
    });
  } else {
    console.error('❌ Top navbar elements not found:', {
      menuToggleBtn: !!elements.menuToggleBtn,
      navLinks: !!elements.navLinks,
      topNavbar: !!elements.topNavbar
    });
  }

  // Toggle menu de categorías  
  if (elements.toggleCategoriaBtn && elements.navLinksCategoria && elements.navCategorias) {
    console.log('✅ Setting up categories toggle');
    elements.toggleCategoriaBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // Toggle clases
      elements.navLinksCategoria.classList.toggle('open');
      elements.navCategorias.classList.toggle('open');
      
      // Actualizar aria-expanded
      const isExpanded = elements.navLinksCategoria.classList.contains('open');
      elements.toggleCategoriaBtn.setAttribute('aria-expanded', isExpanded);
      
      console.log('🔧 Categories menu toggled:', isExpanded);
    });
  } else {
    console.error('❌ Categories elements not found:', {
      toggleCategoriaBtn: !!elements.toggleCategoriaBtn,
      navLinksCategoria: !!elements.navLinksCategoria,
      navCategorias: !!elements.navCategorias
    });
  }

  // Cerrar menús cuando se hace click fuera
  document.addEventListener('click', function(e) {
    // Cerrar menu principal
    if (elements.topNavbar && elements.navLinks && elements.navLinks.classList.contains('open')) {
      if (!elements.topNavbar.contains(e.target)) {
        elements.navLinks.classList.remove('open');
        elements.topNavbar.classList.remove('open');
        if (elements.menuToggleBtn) elements.menuToggleBtn.setAttribute('aria-expanded', 'false');
      }
    }
    
    // Cerrar menu categorías
    if (elements.navCategorias && elements.navLinksCategoria && elements.navLinksCategoria.classList.contains('open')) {
      if (!elements.navCategorias.contains(e.target)) {
        elements.navLinksCategoria.classList.remove('open');
        elements.navCategorias.classList.remove('open');
        if (elements.toggleCategoriaBtn) elements.toggleCategoriaBtn.setAttribute('aria-expanded', 'false');
      }
    }
  });

  console.log('🔧 Menu toggles initialized successfully');
}

document.addEventListener("DOMContentLoaded", function () {
  console.log('🔧 Store.js loaded - initializing functionality');
  
  // ====== Inicializar funcionalidad de menús ======
  console.log('🔧 About to initialize menu toggles...');
  initMenuToggle();
  console.log('🔧 Menu toggles initialization complete');
  
  // Manejar el submit de todos los formularios de agregar al carrito
  document.querySelectorAll(".add-to-cart-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const url = form.action;
      const formData = new FormData(form);
      // debugger; // Descomenta solo cuando quieras detener el navegador

      fetch(url, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
        },
        body: formData,
      })
        .then((response) => response.text())
        .then((text) => {
          // Intentar parsear JSON; si viene HTML, se captura el error
          let data;
          try {
            data = JSON.parse(text);
          } catch (err) {
            console.error("Respuesta no JSON:", text);
            throw new Error("Respuesta inválida del servidor");
          }

          // Actualizar contador de carrito si existe
          const cartCountElem = document.getElementById("cart-count");
          if (cartCountElem && data.cart_count !== undefined) {
            cartCountElem.textContent = data.cart_count;
            if (window.Swal) {
              Swal.fire({
                icon: "success",
                title: "¡Agregado!",
                text: "Producto agregado al carrito",
                timer: 1500,
                showConfirmButton: false,
              });
            } else {
              // Fallback mínimo
              console.log("Producto agregado, nuevo contador:", data.cart_count);
            }
          }

          // Si usas modal, puedes actualizar el contenido aquí
          if (data.cart_items) {
            let html = "";
            if (data.cart_items.length > 0) {
              html += '<ul class="list-group mb-3">';
              data.cart_items.forEach(function (item) {
                html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                                ${item.product_name}
                                <span class="badge bg-primary rounded-pill">${item.quantity}</span>
                            </li>`;
              });
              html += "</ul>";
              html += `<div class="text-end"><strong>Total: $${data.cart_total}</strong></div>`;
            } else {
              html = "<p>Tu carrito está vacío.</p>";
            }
            const modalBody = document.getElementById("cart-modal-body");
            if (modalBody) modalBody.innerHTML = html;
            if (window.bootstrap && document.getElementById("cartModal")) {
              var cartModal = new bootstrap.Modal(document.getElementById("cartModal"));
              cartModal.show();
            }
          }
        })
        .catch((error) => {
          console.error("Error en add-to-cart fetch:", error);
          // Mensaje más amable
          if (window.Swal) {
            Swal.fire({
              icon: "error",
              title: "Error",
              text: "No se pudo agregar el producto al carrito. Intenta nuevamente.",
            });
          } else {
            alert("No se pudo agregar el producto al carrito. Intenta nuevamente.");
          }
        });
    });
  });

  // Manejar el cambio de variante para mostrar stock y botones
  var variantSelect = document.getElementById("variant-select");
  if (variantSelect) {
    variantSelect.addEventListener("change", function () {
      var selected = this.options[this.selectedIndex];
      var stock = selected.getAttribute("data-stock");
      if (stock == "0") {
        const agotado = document.getElementById("agotado-msg");
        if (agotado) agotado.style.display = "block";
        const btnCart = document.getElementById("btn-cart");
        const btnPedir = document.getElementById("btn-pedir");
        if (btnCart) btnCart.disabled = true;
        if (btnPedir) btnPedir.disabled = true;
      } else {
        const agotado = document.getElementById("agotado-msg");
        if (agotado) agotado.style.display = "none";
        const btnCart = document.getElementById("btn-cart");
        const btnPedir = document.getElementById("btn-pedir");
        if (btnCart) btnCart.disabled = false;
        if (btnPedir) btnPedir.disabled = false;
      }
    });
  }
});

// ====== Funcionalidad de menús responsive ======
function initMenuToggle() {
  // Toggle menu principal (top-navbar)
  const topNavbar = document.querySelector('.top-navbar');
  const menuToggle = topNavbar ? topNavbar.querySelector('.menu-toggle') : null;
  const navLinks = topNavbar ? topNavbar.querySelector('.nav-links') : null;

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // Toggle clases
      navLinks.classList.toggle('open');
      topNavbar.classList.toggle('open');
      
      // Actualizar aria-expanded
      const isExpanded = navLinks.classList.contains('open');
      menuToggle.setAttribute('aria-expanded', isExpanded);
      
      console.log('🔧 Top navbar toggled:', isExpanded);
    });
  }

  // Toggle menu de categorías  
  const navCategorias = document.querySelector('.nav-categorias');
  const toggleCategoria = document.getElementById('toggle-categoria');
  const navLinksCategoria = navCategorias ? navCategorias.querySelector('.nav-links-categorias') : null;

  if (toggleCategoria && navLinksCategoria && navCategorias) {
    toggleCategoria.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // Toggle clases
      navLinksCategoria.classList.toggle('open');
      navCategorias.classList.toggle('open');
      
      // Actualizar aria-expanded
      const isExpanded = navLinksCategoria.classList.contains('open');
      toggleCategoria.setAttribute('aria-expanded', isExpanded);
      
      console.log('🔧 Categories menu toggled:', isExpanded);
    });
  }

  // Cerrar menús cuando se hace click fuera
  document.addEventListener('click', function(e) {
    // Cerrar menu principal si está abierto
    if (topNavbar && navLinks && navLinks.classList.contains('open')) {
      if (!topNavbar.contains(e.target)) {
        navLinks.classList.remove('open');
        topNavbar.classList.remove('open');
        if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
      }
    }
    
    // Cerrar menu categorías si está abierto
    if (navCategorias && navLinksCategoria && navLinksCategoria.classList.contains('open')) {
      if (!navCategorias.contains(e.target)) {
        navLinksCategoria.classList.remove('open');
        navCategorias.classList.remove('open');
        if (toggleCategoria) toggleCategoria.setAttribute('aria-expanded', 'false');
      }
    }
  });

  // Cerrar menús con tecla Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      // Cerrar menu principal
      if (topNavbar && navLinks && navLinks.classList.contains('open')) {
        navLinks.classList.remove('open');
        topNavbar.classList.remove('open');
        if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
      }
      
      // Cerrar menu categorías
      if (navCategorias && navLinksCategoria && navLinksCategoria.classList.contains('open')) {
        navLinksCategoria.classList.remove('open');
        navCategorias.classList.remove('open');
        if (toggleCategoria) toggleCategoria.setAttribute('aria-expanded', 'false');
      }
    }
  });

  console.log('🔧 Menu toggles initialized successfully');
}