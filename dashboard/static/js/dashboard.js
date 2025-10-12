
function openEditModal(id, username, email) {
    document.getElementById('editModal').style.display = 'block';
    document.getElementById('modal_user_id').value = id;
    document.getElementById('modal_username').value = username;
    document.getElementById('modal_email').value = email;
}
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}
window.onclick = function(event) {
    var modal = document.getElementById('editModal');
    if (event.target == modal) {
        closeEditModal();
    }
}


function agregarVariante() {
    var container = document.getElementById('variantes-container');
    var row = document.createElement('div');
    row.className = 'variante-row';
    row.innerHTML =
        '<input type="text" name="variante_nombre[]" placeholder="Nombre variante" />' +
        '<input type="text" name="variante_precio[]" placeholder="Precio variante" />' +
        '<input type="number" name="variante_stock[]" placeholder="Stock variante" />' +
        '<input type="text" name="variante_color[]" placeholder="Color variante" />' +
        '<input type="text" name="variante_talla[]" placeholder="Talla variante" />' +
        '<input type="file" name="variante_imagen[]" />';
    container.appendChild(row);
}