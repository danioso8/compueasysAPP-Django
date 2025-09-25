<script>
document.addEventListener('DOMContentLoaded', function() {
    // Manejar clicks en los botones de agregar al carrito
    document.querySelectorAll('.add-to-cart-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            fetch("{% url 'add_to_cart' 0 %}".replace('0', productId))
                .then(response => response.json())
                .then(data => {
                    // Actualiza el contenido del modal con los productos del carrito
                    let html = '';
                    if (data.cart_items.length > 0) {
                        html += '<ul class="list-group mb-3">';
                        data.cart_items.forEach(function(item) {
                            html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                                ${item.product_name}
                                <span class="badge bg-primary rounded-pill">${item.quantity}</span>
                            </li>`;
                        });
                        html += '</ul>';
                        html += `<div class="text-end"><strong>Total: $${data.cart_total}</strong></div>`;
                    } else {
                        html = '<p>Tu carrito está vacío.</p>';
                    }
                    document.getElementById('cart-modal-body').innerHTML = html;
                    // Mostrar el modal
                    var cartModal = new bootstrap.Modal(document.getElementById('cartModal'));
                    cartModal.show();
                });
        });
    });
});
</script>