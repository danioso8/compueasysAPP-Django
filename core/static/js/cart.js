document.addEventListener("DOMContentLoaded", function () {
  // --- Checkbox para seleccionar productos y recalcular total ---
  document.querySelectorAll(".cart-checkbox").forEach(function (checkbox) {
    checkbox.addEventListener("change", updateCartTotal);
  });

  function updateCartTotal() {
    let total = 0;
    document.querySelectorAll(".cart-checkbox").forEach(function (checkbox) {
      if (checkbox.checked) {
        const row = document.querySelector(
          'tr[data-index="' + checkbox.value + '"]'
        );
        if (row) {
          const subtotalCell = row.querySelector(".item-subtotal");
          if (subtotalCell) {
            const subtotalText = subtotalCell.innerText.replace(/[^0-9]/g, "");
            total += parseInt(subtotalText || 0);
          }
        }
      }
    });
    const totalElement = document.getElementById("cart-total");
    if (totalElement) {
      totalElement.innerText = "$" + total.toLocaleString("es-CO");
    }
  }

  updateCartTotal();

  // --- Botón para finalizar pedido y enviar la nota ---
  var finalizarBtn = document.getElementById("finalizar-pedido");
  if (finalizarBtn) {
    finalizarBtn.addEventListener("click", function (e) {
      e.preventDefault();
      var nota = document.getElementById("cart-note").value;
      window.location.href = "/checkout/?note=" + encodeURIComponent(nota);
    });
  }

  // --- Manejo de cantidades con AJAX ---
  document.querySelectorAll(".cart-qty-form").forEach(function (form) {
    const input = form.querySelector(".cart-qty");
    const decreaseBtn = form.querySelector(".decrease");
    const increaseBtn = form.querySelector(".increase");
    const productId = form.dataset.product;
    const variantId = form.dataset.variant;

    decreaseBtn.addEventListener("click", function () {
      let qty = parseInt(input.value);
      if (qty > 1) {
        input.value = qty - 1;
        updateCart(productId, variantId, input.value, form);
      }
    });

    increaseBtn.addEventListener("click", function () {
      let qty = parseInt(input.value);
      let max = parseInt(input.getAttribute("max"));
      if (qty < max) {
        input.value = qty + 1;
        updateCart(productId, variantId, input.value, form);
      }
    });

    input.addEventListener("change", function () {
      let qty = parseInt(input.value);
      let max = parseInt(input.getAttribute("max"));
      if (qty < 1) input.value = 1;
      if (qty > max) input.value = max;
      updateCart(productId, variantId, input.value, form);
    });
  });

  // --- Función para actualizar el carrito vía AJAX ---
  function updateCart(productId, variantId, quantity, form) {
    fetch(`/update_cart/${productId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `variant_id=${variantId}&quantity=${quantity}&action=set`,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Actualiza subtotal de la fila
          if (data.subtotal !== undefined) {
            form.closest("tr").querySelector(".item-subtotal").textContent =
              "$" + Number(data.subtotal).toLocaleString("es-CO");
          }
          // Actualiza total del carrito
          if (data.cart_total !== undefined) {
            document.getElementById("cart-total").textContent =
              "$" + Number(data.cart_total).toLocaleString("es-CO");
          }
          // Actualiza contador de productos
          if (data.cart_count !== undefined) {
            document.querySelectorAll(".cart-count").forEach(function (el) {
              el.textContent = data.cart_count;
            });
          }
          // Si usas checkboxes, recalcula el total seleccionado
          if (typeof updateCartTotal === "function") {
            updateCartTotal();
          }
        }
      });
  }

  // --- Función para obtener el CSRF token ---
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
});