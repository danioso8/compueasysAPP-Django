document.addEventListener("DOMContentLoaded", function () {
  // Manejar el submit de todos los formularios de agregar al carrito
  document.querySelectorAll(".add-to-cart-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const url = form.action;
      const formData = new FormData(form);
      debugger;
      fetch(url, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
        },
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {         
          if (data.cart_count !== undefined) {           
              document.getElementById("cart-count")
            );
            document.getElementById("cart-count").textContent = data.cart_count;
            Swal.fire({
              icon: "success",
              title: "¡Agregado!",
              text: "Producto agregado al carrito",
              timer: 1500,
              showConfirmButton: false,
            });
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
            document.getElementById("cart-modal-body").innerHTML = html;
            var cartModal = new bootstrap.Modal(
              document.getElementById("cartModal")
            );
            cartModal.show();
          }
        })

        .catch((error) => {
          alert("Error al agregar al carrito");
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
        document.getElementById("agotado-msg").style.display = "block";
        document.getElementById("btn-cart").disabled = true;
        document.getElementById("btn-pedir").disabled = true;
      } else {
        document.getElementById("agotado-msg").style.display = "none";
        document.getElementById("btn-cart").disabled = false;
        document.getElementById("btn-pedir").disabled = false;
      }
    });
  }
});
