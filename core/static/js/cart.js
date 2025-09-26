document.addEventListener('DOMContentLoaded', function() {
    // Obtén todos los checkboxes y el total
    const checkboxes = document.querySelectorAll('input[name="selected_products"]');
    const totalSpan = document.querySelector('.cart-total');
    // Guarda los precios en un array
    const prices = Array.from(checkboxes).map(cb => {
        // Busca el precio en la misma fila
        const priceCell = cb.closest('tr').querySelectorAll('td')[2];
        // Quita símbolos y convierte a número
        return parseFloat(priceCell.textContent.replace(/[^0-9,]/g, '').replace(',', ''));
    });

    function updateTotal() {
        let total = 0;
        checkboxes.forEach((cb, idx) => {
            if (cb.checked) {
                total += prices[idx];
            }
        });
        // Formatea el total con separador de miles
        totalSpan.textContent = '$' + total.toLocaleString('es-CO');
    }

    checkboxes.forEach(cb => {
        cb.addEventListener('change', updateTotal);
    });

    // Inicializa el total por si acaso
    updateTotal();
});