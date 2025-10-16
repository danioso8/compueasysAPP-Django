
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



  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

document.querySelectorAll('.eliminar-usuario-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        if (!confirm('¿Seguro que deseas eliminar este usuario?')) return;
        const userId = btn.getAttribute('data-user-id');  
        alert(userId);   
        fetch(`/dashboard/usuario/${userId}/eliminar_usuario/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken              
            }
        })
        .then(response => response.json())       
        .then(data => {
           alert(data);
            if (data.success) {
                // Elimina la fila del usuario por id
                const fila = btn.closest('tr');
                if (fila) fila.remove();
            } else {
                alert('No se pudo eliminar el usuario.');
            }
        })
        .catch(() => alert('Error al eliminar el usuario.'));
    });
});