
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


// ...existing code...
document.addEventListener('DOMContentLoaded', function () {
  // Al hacer click en una fila de producto, cargar datos
  document.querySelectorAll('.producto-row').forEach(function (row) {
    row.addEventListener('click', function () {
      const productId = row.getAttribute('data-product-id');
      if (!productId) return;
      fetch(`/dashboard/api/producto/${productId}/`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          console.error(data.error);
          return;
        }
        // Rellenar campos del formulario
        const form = document.getElementById('form-crear-producto');
        if (!form) return;
        document.getElementById('producto_id').value = data.id || '';
        document.getElementById('producto_name').value = data.name || '';
        document.getElementById('producto_description').value = data.description || '';
        if (document.getElementById('producto_price_buy')) document.getElementById('producto_price_buy').value = data.price_buy || '';
        if (document.getElementById('producto_price')) document.getElementById('producto_price').value = data.price || '';
        if (document.getElementById('producto_stock')) document.getElementById('producto_stock').value = data.stock || '';
        if (document.getElementById('producto_descuento')) document.getElementById('producto_descuento').value = data.descuento || '';
        if (document.getElementById('producto_iva')) document.getElementById('producto_iva').value = data.iva || '';
        if (document.getElementById('producto_proveedor')) document.getElementById('producto_proveedor').value = data.proveedor_id || '';
        if (document.getElementById('producto_categoria')) document.getElementById('producto_categoria').value = data.categoria_id || '';
        if (document.getElementById('producto_type')) document.getElementById('producto_type').value = data.type_id || '';

        // Mostrar imagen principal
        const mainImg = document.getElementById('preview-main-img');
        if (mainImg) {
          if (data.imagen) {
            mainImg.src = data.imagen;
            mainImg.style.display = 'block';
          } else {
            mainImg.style.display = 'none';
            mainImg.src = '';
          }
        }
        // Mostrar galería
        const gallery = document.getElementById('preview-gallery');
        if (gallery) {
          gallery.innerHTML = '';
          if (Array.isArray(data.gallery) && data.gallery.length) {
            data.gallery.forEach(function (g) {
              const img = document.createElement('img');
              img.src = g;
              img.style.maxWidth = '80px';
              img.style.maxHeight = '80px';
              img.style.objectFit = 'cover';
              img.style.border = '1px solid #ddd';
              gallery.appendChild(img);
            });
          }
        }

        // Cambiar UI a modo "Editar"
        const title = document.getElementById('form-title');
        if (title) title.textContent = 'Editar Producto';
        const submitBtn = document.getElementById('form-submit-btn');
        if (submitBtn) submitBtn.textContent = 'Actualizar';
        // si tienes URL de edición, puedes cambiar action:
        if (data.update_url && form.getAttribute('data-create-action')) {
          form.action = data.update_url;
        }
        // focus al nombre
        document.getElementById('producto_name').focus();
      })
      .catch(err => console.error('Error cargando producto:', err));
    });
  });

  // Botón "Nuevo" limpia el formulario y restaura acción original
  const clearBtn = document.getElementById('form-clear-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      const form = document.getElementById('form-crear-producto');
      if (!form) return;
      form.reset();
      document.getElementById('producto_id').value = '';
      const mainImg = document.getElementById('preview-main-img');
      if (mainImg) { mainImg.src = ''; mainImg.style.display = 'none'; }
      const gallery = document.getElementById('preview-gallery');
      if (gallery) gallery.innerHTML = '';
      const title = document.getElementById('form-title');
      if (title) title.textContent = 'Crear Producto';
      const submitBtn = document.getElementById('form-submit-btn');
      if (submitBtn) submitBtn.textContent = 'Guardar';
      // restablecer action si guardaste la acción original
      if (form.getAttribute('data-create-action')) {
        form.action = form.getAttribute('data-create-action');
      }
    });
  }
});
// ...existing code...