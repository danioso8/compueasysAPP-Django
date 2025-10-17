// ...existing code...
document.addEventListener("DOMContentLoaded", function () {
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
// ...existing code...