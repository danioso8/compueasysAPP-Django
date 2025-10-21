// Versión completa: manejo de clicks en filas, carga API producto, relleno de formulario,
// renderizado de galería y variantes, utilidades y helpers.

function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : '';
}
function safeEl(id) { return document.getElementById(id); }
function qsAll(sel) { return Array.from(document.querySelectorAll(sel)); }

document.addEventListener('DOMContentLoaded', function () {
  console.log('[dashboard.js] DOM ready');

  const csrfToken = (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || getCookie('csrftoken');

  // Detectar filas de producto (compatibilidad con data-producto-id y data-product-id)
  const rows = qsAll('tr[data-producto-id], tr[data-product-id], .producto-row');
  console.log('[dashboard.js] filas detectadas:', rows.length);

  rows.forEach(function (row) {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function (e) {
      const targetTag = e.target && e.target.tagName ? e.target.tagName.toLowerCase() : '';
      const productId = row.getAttribute('data-producto-id') || row.getAttribute('data-product-id') || row.dataset.productoId || row.dataset.productId;
      if (!productId) return;

      // Si el click fue sobre un <a>, impedir navegación por defecto y manejar por JS
      if (targetTag === 'a') e.preventDefault();

      const form = safeEl('form-crear-producto');
      if (!form) {
        // Forzar render del formulario por servidor
        window.location.href = `${window.location.pathname}?view=productos&crear=1&editar=${productId}`;
        return;
      }

      const apiUrl = `/dashboard/api/producto/${productId}/`;
      console.log('[dashboard.js] fetching', apiUrl);
      fetch(apiUrl, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (resp) {
          if (!resp.ok) throw new Error('HTTP ' + resp.status);
          return resp.json();
        })
        .then(function (data) {
          if (!data || data.error) {
            console.warn('[dashboard.js] api returned error or empty, fallback to server render', data);
            window.location.href = `${window.location.pathname}?view=productos&crear=1&editar=${productId}`;
            return;
          }

          // Rellenar campos básicos
          const setIf = function (id, val) { const el = safeEl(id); if (el) el.value = (val === null || val === undefined) ? '' : val; };
          setIf('producto_id', data.id || '');
          setIf('producto_name', data.name || '');
          setIf('producto_description', data.description || '');
          setIf('producto_price_buy', (data.price_buy !== undefined) ? data.price_buy : '');
          setIf('producto_price', (data.price !== undefined) ? data.price : '');
          setIf('producto_stock', (data.stock !== undefined) ? data.stock : '');
          setIf('producto_descuento', (data.descuento !== undefined) ? data.descuento : '');
          setIf('producto_iva', (data.iva !== undefined) ? data.iva : '');
          setIf('producto_proveedor', data.proveedor_id || '');
          setIf('producto_categoria', data.categoria_id || '');
          setIf('producto_type', data.type_id || '');

          // Imagen principal preview
          const mainImg = safeEl('preview-main-img');
          if (mainImg) {
            if (data.imagen) {
              mainImg.src = data.imagen;
              mainImg.style.display = 'block';
            } else {
              mainImg.src = '';
              mainImg.style.display = 'none';
            }
          }

          // Galería: limpiar y añadir imágenes
          const gallery = safeEl('preview-gallery');
          if (gallery) {
            gallery.innerHTML = '';
            const galleryArr = Array.isArray(data.gallery) ? data.gallery : (data.gallery_urls || []);
            galleryArr.forEach(function (url) {
              const img = document.createElement('img');
              img.src = url;
              img.style.maxWidth = '80px';
              img.style.maxHeight = '80px';
              img.style.objectFit = 'cover';
              img.style.marginRight = '6px';
              gallery.appendChild(img);
            });
          }

          // Variantes: renderizar desde data.variants si existe
          const variantesContainer = safeEl('variantes-container');
          if (variantesContainer) {
            variantesContainer.innerHTML = '';
            if (Array.isArray(data.variants) && data.variants.length) {
              data.variants.forEach(function (v) {
                const rowDiv = document.createElement('div');
                rowDiv.className = 'variante-row d-flex gap-2 mb-2 align-items-center';
                // usar template literal con escaped values (simple escape)
                const esc = (s) => (s === null || s === undefined) ? '' : String(s).replace(/"/g, '&quot;');
                rowDiv.innerHTML =
                  `<input type="text" name="variante_nombre[]" class="form-control" value="${esc(v.nombre)}" placeholder="Nombre variante">` +
                  `<input type="number" name="variante_precio[]" class="form-control" value="${esc(v.precio)}" step="0.01" placeholder="Precio">` +
                  `<input type="number" name="variante_stock[]" class="form-control" value="${esc(v.stock)}" placeholder="Stock">` +
                  `<input type="text" name="variante_color[]" class="form-control" value="${esc(v.color)}" placeholder="Color">` +
                  `<input type="text" name="variante_talla[]" class="form-control" value="${esc(v.talla)}" placeholder="Talla">` +
                  `<input type="file" name="variante_imagen[]" class="form-control">`;
                variantesContainer.appendChild(rowDiv);
                if (v.imagen) {
                  const img = document.createElement('img');
                  img.src = v.imagen;
                  img.style.maxWidth = '80px';
                  img.style.objectFit = 'cover';
                  img.style.marginLeft = '6px';
                  rowDiv.appendChild(img);
                }
              });
            } else {
              // Mantener al menos una fila vacía
              const emptyRow = document.createElement('div');
              emptyRow.className = 'variante-row d-flex gap-2 mb-2 align-items-center';
              emptyRow.innerHTML =
                '<input type="text" name="variante_nombre[]" class="form-control" placeholder="Nombre variante">' +
                '<input type="number" name="variante_precio[]" class="form-control" placeholder="Precio" step="0.01">' +
                '<input type="number" name="variante_stock[]" class="form-control" placeholder="Stock">' +
                '<input type="text" name="variante_color[]" class="form-control" placeholder="Color">' +
                '<input type="text" name="variante_talla[]" class="form-control" placeholder="Talla">' +
                '<input type="file" name="variante_imagen[]" class="form-control">';
              variantesContainer.appendChild(emptyRow);
            }
          }

          // UI modo edición
          safeEl('form-title') && (safeEl('form-title').textContent = 'Editar Producto');
          safeEl('form-submit-btn') && (safeEl('form-submit-btn').textContent = 'Actualizar');
          safeEl('producto_name') && safeEl('producto_name').focus();
        })
        .catch(function (err) {
          console.error('[dashboard.js] fetch error:', err);
          window.location.href = `${window.location.pathname}?view=productos&crear=1&editar=${productId}`;
        });
    }, false);
  });

  // Botón "Nuevo" limpia formulario
  const clearBtn = safeEl('form-clear-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      const form = safeEl('form-crear-producto'); if (!form) return;
      form.reset();
      safeEl('producto_id') && (safeEl('producto_id').value = '');
      if (safeEl('preview-main-img')) { safeEl('preview-main-img').src = ''; safeEl('preview-main-img').style.display = 'none'; }
      if (safeEl('preview-gallery')) safeEl('preview-gallery').innerHTML = '';
      if (safeEl('variantes-container')) safeEl('variantes-container').innerHTML = '';
      safeEl('form-title') && (safeEl('form-title').textContent = 'Crear Producto');
      safeEl('form-submit-btn') && (safeEl('form-submit-btn').textContent = 'Guardar');
      if (form.getAttribute('data-create-action')) form.action = form.getAttribute('data-create-action');
    });
  }

  // Exponer función global para agregar variantes desde template
  window.agregarVariante = function () {
    const container = safeEl('variantes-container');
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'variante-row d-flex gap-2 mb-2 align-items-center';
    row.innerHTML =
      '<input type="text" name="variante_nombre[]" class="form-control" placeholder="Nombre variante">' +
      '<input type="number" name="variante_precio[]" class="form-control" placeholder="Precio" step="0.01">' +
      '<input type="number" name="variante_stock[]" class="form-control" placeholder="Stock">' +
      '<input type="text" name="variante_color[]" class="form-control" placeholder="Color">' +
      '<input type="text" name="variante_talla[]" class="form-control" placeholder="Talla">' +
      '<input type="file" name="variante_imagen[]" class="form-control">';
    container.appendChild(row);
  };

  // Si URL contiene editar=<id>, intentar cargar al inicio (si el formulario está presente)
  try {
    const params = new URLSearchParams(window.location.search);
    const editarId = params.get('editar');
    if (editarId && safeEl('form-crear-producto')) {
      const apiUrl = `/dashboard/api/producto/${editarId}/`;
      fetch(apiUrl, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (data) {
          if (!data || data.error) return;
          // Reuse the same filling logic: set basic fields, gallery and variants
          const setIf = function (id, val) { const el = safeEl(id); if (el) el.value = (val === null || val === undefined) ? '' : val; };
          setIf('producto_id', data.id || '');
          setIf('producto_name', data.name || '');
          setIf('producto_description', data.description || '');
          setIf('producto_price_buy', (data.price_buy !== undefined) ? data.price_buy : '');
          setIf('producto_price', (data.price !== undefined) ? data.price : '');
          setIf('producto_stock', (data.stock !== undefined) ? data.stock : '');
          setIf('producto_descuento', (data.descuento !== undefined) ? data.descuento : '');
          setIf('producto_iva', (data.iva !== undefined) ? data.iva : '');
          setIf('producto_proveedor', data.proveedor_id || '');
          setIf('producto_categoria', data.categoria_id || '');
          setIf('producto_type', data.type_id || '');

          if (safeEl('preview-main-img')) {
            if (data.imagen) { safeEl('preview-main-img').src = data.imagen; safeEl('preview-main-img').style.display = 'block'; }
            else { safeEl('preview-main-img').src = ''; safeEl('preview-main-img').style.display = 'none'; }
          }

          if (safeEl('preview-gallery')) {
            safeEl('preview-gallery').innerHTML = '';
            const galleryArr = Array.isArray(data.gallery) ? data.gallery : (data.gallery_urls || []);
            galleryArr.forEach(function (url) {
              const img = document.createElement('img');
              img.src = url;
              img.style.maxWidth = '80px'; img.style.objectFit = 'cover'; img.style.marginRight = '6px';
              safeEl('preview-gallery').appendChild(img);
            });
          }

          if (safeEl('variantes-container')) {
            safeEl('variantes-container').innerHTML = '';
            if (Array.isArray(data.variants) && data.variants.length) {
              data.variants.forEach(function (v) {
                const rowDiv = document.createElement('div');
                rowDiv.className = 'variante-row d-flex gap-2 mb-2 align-items-center';
                const esc = (s) => (s === null || s === undefined) ? '' : String(s).replace(/"/g, '&quot;');
                rowDiv.innerHTML =
                  `<input type="text" name="variante_nombre[]" class="form-control" value="${esc(v.nombre)}" placeholder="Nombre variante">` +
                  `<input type="number" name="variante_precio[]" class="form-control" value="${esc(v.precio)}" step="0.01" placeholder="Precio">` +
                  `<input type="number" name="variante_stock[]" class="form-control" value="${esc(v.stock)}" placeholder="Stock">` +
                  `<input type="text" name="variante_color[]" class="form-control" value="${esc(v.color)}" placeholder="Color">` +
                  `<input type="text" name="variante_talla[]" class="form-control" value="${esc(v.talla)}" placeholder="Talla">` +
                  `<input type="file" name="variante_imagen[]" class="form-control">`;
                safeEl('variantes-container').appendChild(rowDiv);
                if (v.imagen) {
                  const img = document.createElement('img');
                  img.src = v.imagen;
                  img.style.maxWidth = '80px';
                  img.style.objectFit = 'cover';
                  img.style.marginLeft = '6px';
                  rowDiv.appendChild(img);
                }
              });
            } else {
              const emptyRow = document.createElement('div');
              emptyRow.className = 'variante-row d-flex gap-2 mb-2 align-items-center';
              emptyRow.innerHTML =
                '<input type="text" name="variante_nombre[]" class="form-control" placeholder="Nombre variante">' +
                '<input type="number" name="variante_precio[]" class="form-control" placeholder="Precio" step="0.01">' +
                '<input type="number" name="variante_stock[]" class="form-control" placeholder="Stock">' +
                '<input type="text" name="variante_color[]" class="form-control" placeholder="Color">' +
                '<input type="text" name="variante_talla[]" class="form-control" placeholder="Talla">' +
                '<input type="file" name="variante_imagen[]" class="form-control">';
              safeEl('variantes-container').appendChild(emptyRow);
            }
          }

          safeEl('form-title') && (safeEl('form-title').textContent = 'Editar Producto');
          safeEl('form-submit-btn') && (safeEl('form-submit-btn').textContent = 'Actualizar');
        })
        .catch(function (err) { console.error('[dashboard.js] inicial fetch error:', err); });
    }
  } catch (e) {
    console.error('[dashboard.js] url parse error', e);
  }
});

// ...existing code...

document.addEventListener('DOMContentLoaded', function () {
    // ...existing code...
  
  // Handler para eliminar producto (delegación no necesaria si botones ya creados)
  document.querySelectorAll('.btn-eliminar-producto').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const productId = this.dataset.productId;
      const rowEl = this.closest('.producto-row');
      deleteProduct(productId, rowEl);
    });
  });
  // ...existing code...

/* --- Alertas modernas (Bootstrap Toasts) --- */
function _ensureToastRoot() {
  let root = document.getElementById('dashboard-toast-root');
  if (!root) {
    root = document.createElement('div');
    root.id = 'dashboard-toast-root';
    root.innerHTML = '<div aria-live="polite" aria-atomic="true" class="position-fixed top-0 end-0 p-3" style="z-index:10800;"></div>';
    document.body.appendChild(root);
  }
  return root.querySelector('.position-fixed');
}

function showToast(title, message, variant = 'primary', delay = 3500) {
  try {
    const container = _ensureToastRoot();
    const id = 'toast-' + Date.now();
    const toastHtml = `
      <div id="${id}" class="toast align-items-center text-bg-${variant} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">
            <strong class="d-block">${title}</strong>
            <div>${message}</div>
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>`;
    container.insertAdjacentHTML('beforeend', toastHtml);
    const el = document.getElementById(id);
    const bsToast = new bootstrap.Toast(el, { delay: delay });
    bsToast.show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
  } catch (e) {
    // fallback clásico
    console.log('showToast fallback', title, message);
    alert(title + '\n' + message);
  }
}

/* Confirmación moderna: usa SweetAlert2 si está cargado, si no usa confirm() */
function showConfirm(options) {
  // options: { title, text, confirmText, cancelText, onConfirm }
  if (window.Swal && typeof Swal.fire === 'function') {
    Swal.fire({
      title: options.title || 'Confirmar',
      text: options.text || '',
      icon: options.icon || 'warning',
      showCancelButton: true,
      confirmButtonText: options.confirmText || 'Sí',
      cancelButtonText: options.cancelText || 'Cancelar',
      reverseButtons: true,
    }).then((result) => {
      if (result.isConfirmed && typeof options.onConfirm === 'function') options.onConfirm();
    });
  } else {
    const ok = confirm((options.title ? options.title + '\n\n' : '') + (options.text || '¿Continuar?'));
    if (ok && typeof options.onConfirm === 'function') options.onConfirm();
  }
}

/* --- Reemplazo de alert() en delete flow --- */
// ...existing code...
function deleteProduct(productId, rowEl) {
   showConfirm({
    title: 'Eliminar producto',    
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    onConfirm: function () {
      const csrf = (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || getCookie('csrftoken');
      fetch(`/dashboard/producto/${productId}/eliminar/`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: productId })
      })
      .then(r => r.json().catch(()=>({})))
      .then(data => {
        if (data && data.success) {
          if (rowEl) rowEl.remove();
          else {
            const tr = document.querySelector(`tr[data-producto-id="${productId}"], tr[data-product-id="${productId}"]`);
            if (tr) tr.remove();
          }
          Swal.fire({
                icon: "success",
                title: "Eliminado!",
                text: "Producto eliminado correctamente",
                timer: 1500,
                showConfirmButton: false,
              });
        } else {
          const err = (data && data.error) ? data.error : 'No se pudo eliminar el producto';
           Swal.fire({
                icon: "success",
                title: "Eliminado!",
                text: "Producto eliminado correctamente",
                timer: 1500,
                showConfirmButton: false,
              });
        }
      })
      .catch(err => {      
        Swal.fire('Error', 'Error eliminando producto', 'danger');
      });
    }
  });
}
// ...existing code...

  // Adjuntar listeners a botones existentes
  document.querySelectorAll('.delete-product-btn').forEach(function(btn){
    btn.addEventListener('click', function(e){
      e.preventDefault();
      const productId = btn.getAttribute('data-product-id');
      const row = btn.closest('tr');
      if (!productId) return;
      deleteProduct(productId, row);
    });
  });

  // También delegación global (por si filas se generan dinámicamente)
  document.addEventListener('click', function(e){
    const btn = e.target.closest && e.target.closest('.delete-product-btn');
    if (!btn) return;
    e.preventDefault();
    const productId = btn.getAttribute('data-product-id');
    const row = btn.closest('tr');
    if (!productId) return;
    deleteProduct(productId, row);
  }, true);

  // ...existing code...
});
// ...existing code...