document.addEventListener("DOMContentLoaded", function () {
  const nav = document.querySelector(".navbar");
  const toggle = document.querySelector(".menu-toggle");
  const menu = document.getElementById("nav-menu");

  if (!toggle || !menu || !nav) return;

  toggle.addEventListener("click", function (e) {
    const isOpen = nav.classList.toggle("open");
    menu.classList.toggle("open", isOpen);
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    // cambiar label accesible
    toggle.setAttribute("aria-label", isOpen ? "Cerrar menú" : "Abrir menú");
  });

  // cerrar al redimensionar a desktop
  window.addEventListener("resize", function () {
    if (window.innerWidth > 768 && nav.classList.contains("open")) {
      nav.classList.remove("open");
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Abrir menú");
    }
  });

  // cerrar al hacer click fuera
  document.addEventListener("click", function (e) {
    if (!nav.contains(e.target) && nav.classList.contains("open")) {
      nav.classList.remove("open");
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Abrir menú");
    }
  });
});
