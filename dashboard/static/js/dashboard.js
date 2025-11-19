// ...existing code...
/*
  dashboard.js - manejo completo de:
   - carga de formulario crear/editar producto desde lista (fetch API)
   - previews imagen principal y galería (nuevas y existentes)
   - eliminar imágenes existentes (marca para eliminar con inputs ocultos)
   - manejar variantes (crear, mostrar existentes, eliminar con marca)
   - submit para crear/actualizar (ajusta action cuando se edita)
   - eliminación de productos con confirmación
   - utilidades: toasts, confirm, CSRF
   - funcionalidad móvil: menú sidebar responsive
*/

(function () {
  "use strict";

  /* ---------- Utilities ---------- */
  function getCookie(name) {
    const match = document.cookie.match(
      "(^|;)\\s*" + name + "\\s*=\\s*([^;]+)"
    );
    return match ? match.pop() : "";
  }
  function safeEl(id) {
    return document.getElementById(id);
  }
  function qsAll(sel) {
    return Array.from(document.querySelectorAll(sel));
  }
  function el(sel) {
    return document.querySelector(sel);
  }
  function escapeHtml(s) {
    return s === null || s === undefined
      ? ""
      : String(s)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;");
  }

  /* ---------- UI helpers (toasts/confirm) ---------- */
  function _ensureToastRoot() {
    let root = document.getElementById("dashboard-toast-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "dashboard-toast-root";
      root.innerHTML =
        '<div aria-live="polite" aria-atomic="true" class="position-fixed top-0 end-0 p-3" style="z-index:10800;"></div>';
      document.body.appendChild(root);
    }
    return root.querySelector(".position-fixed");
  }
  function showToast(title, message, variant = "primary", delay = 3000) {
    try {
      const container = _ensureToastRoot();
      const id = "toast-" + Date.now();
      const html = `
        <div id="${id}" class="toast align-items-center text-bg-${variant} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="d-flex">
            <div class="toast-body"><strong class="d-block">${escapeHtml(
              title
            )}</strong><div>${escapeHtml(message)}</div></div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" aria-label="Close"></button>
          </div>
        </div>`;
      container.insertAdjacentHTML("beforeend", html);
      const toastEl = document.getElementById(id);
      const btn = toastEl.querySelector("button");
      btn.addEventListener("click", () => toastEl.remove());
      if (window.bootstrap && typeof bootstrap.Toast === "function") {
        const bs = new bootstrap.Toast(toastEl, { delay });
        bs.show();
        toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
      } else {
        setTimeout(() => toastEl.remove(), delay);
      }
    } catch (e) {
      console.error("showToast error", e);
    }
  }
  function showConfirm(opts) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire({
        title: opts.title || "Confirmar",
        text: opts.text || "",
        icon: opts.icon || "warning",
        showCancelButton: true,
        confirmButtonText: opts.confirmText || "Sí",
        cancelButtonText: opts.cancelText || "Cancelar",
        reverseButtons: true,
      }).then((result) => {
        if (result.isConfirmed && typeof opts.onConfirm === "function")
          opts.onConfirm();
      });
    } else {
      const ok = confirm(
        (opts.title ? opts.title + "\n\n" : "") + (opts.text || "¿Continuar?")
      );
      if (ok && typeof opts.onConfirm === "function") opts.onConfirm();
    }
  }

  /* ---------- Main logic ---------- */
  document.addEventListener("DOMContentLoaded", function () {
    // CSRF token helper
    const csrfToken =
      (document.querySelector("[name=csrfmiddlewaretoken]") || {}).value ||
      getCookie("csrftoken");

    // Form elements (may be created server-side)
    const createForm = safeEl("form-crear-producto"); // form shared for create/edit in some templates
    const editForm = safeEl("form-editar-producto"); // optional separate edit form
    // prefer a single form element variable for handlers
    const form = createForm || editForm || null;

    // preview main image
    const previewMainImg =
      safeEl("preview-main-img") || safeEl("preview-main-img-edit");

    // gallery input and container (ids used in template)
    const galInput = safeEl("producto_galeria") || null;
    const galleryContainer =
      safeEl("preview-gallery") || safeEl("preview-gallery-edit") || null;

    // variantes container
    const variantesContainer = safeEl("variantes-container") || null;

    // store state for new gallery files (array of File)
    let galleryFiles = []; // files added in current session (for new uploads)
    // removed existing IDs will be tracked by adding hidden inputs to form when user clicks X

    /* ---------- Helpers for gallery previews ---------- */
    function rebuildGalInputFiles() {
      if (!galInput) return;
      const dt = new DataTransfer();
      galleryFiles.forEach((f) => dt.items.add(f));
      // assign to real input so server receives the files
      galInput.files = dt.files;
    }
    function renderGalleryPreviews() {
      if (!galleryContainer) return;
      // remove previews we created (data-new-index)
      Array.from(
        galleryContainer.querySelectorAll(".gallery-item[data-new-index]")
      ).forEach((n) => n.remove());
      galleryFiles.forEach((file, idx) => {
        const div = document.createElement("div");
        div.className = "gallery-item";
        div.dataset.newIndex = idx;
        div.style.position = "relative";
        div.style.marginRight = "8px";
        div.style.marginBottom = "8px";
        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        img.style.maxWidth = "120px";
        img.style.maxHeight = "120px";
        img.style.objectFit = "cover";
        img.style.borderRadius = "6px";
        div.appendChild(img);
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-sm btn-danger gallery-remove-new";
        btn.textContent = "×";
        btn.style.position = "absolute";
        btn.style.top = "4px";
        btn.style.right = "4px";
        btn.addEventListener("click", function () {
          galleryFiles.splice(idx, 1);
          rebuildGalInputFiles();
          renderGalleryPreviews();
        });
        div.appendChild(btn);
        galleryContainer.appendChild(div);
      });
    }

    if (galInput && galleryContainer) {
      // initialize change
      galInput.addEventListener("change", function (e) {
        const files = Array.from(e.target.files || []);
        // append new files to galleryFiles but avoid duplicates by name+size
        files.forEach((f) => {
          const exists = galleryFiles.some(
            (g) =>
              g.name === f.name &&
              g.size === f.size &&
              g.lastModified === f.lastModified
          );
          if (!exists) galleryFiles.push(f);
        });
        // ensure galInput.files reflects galleryFiles
        rebuildGalInputFiles();
        renderGalleryPreviews();
      });
    }

    /* ---------- Remove existing gallery images (editing) ---------- */
    function initExistingGalleryRemoveButtons() {
      if (!galleryContainer) return;
      galleryContainer
        .querySelectorAll(".gallery-remove-btn")
        .forEach((btn) => {
          btn.removeEventListener("click", existingGalleryRemoveHandler);
          btn.addEventListener("click", existingGalleryRemoveHandler);
        });
    }
    function existingGalleryRemoveHandler(e) {
      const id = this.dataset.galleryId;
      const formEl = this.closest("form");
      if (!id) {
        // fallback: remove DOM
        this.closest(".gallery-item")?.remove();
        return;
      }
      // add hidden input galeria_delete[] to form
      if (formEl) {
        const hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "galeria_delete[]";
        hidden.value = id;
        formEl.appendChild(hidden);
        // remove any existing hidden existings for that id
        const existing = formEl.querySelectorAll(
          'input[name="galeria_existing[]"]'
        );
        existing.forEach((inp) => {
          if (inp.value === id) inp.remove();
        });
      }
      // remove DOM element
      this.closest(".gallery-item")?.remove();
    }
    initExistingGalleryRemoveButtons();

    /* ---------- Variantes management ---------- */
    function initVariantRemoveHandlers() {
      if (!variantesContainer) return;
      // existing variants (have data-variant-id)
      variantesContainer
        .querySelectorAll(".variant-remove-btn")
        .forEach((btn) => {
          btn.removeEventListener("click", variantRemoveHandler);
          btn.addEventListener("click", variantRemoveHandler);
        });
      // new row remove buttons
      variantesContainer
        .querySelectorAll(".variant-remove-btn-new")
        .forEach((btn) => {
          btn.removeEventListener("click", variantRemoveNewHandler);
          btn.addEventListener("click", variantRemoveNewHandler);
        });
    }
    function variantRemoveHandler(e) {
      const id = this.dataset.variantId;
      const formEl = this.closest("form");
      if (formEl && id) {
        const hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "variante_delete[]";
        hidden.value = id;
        formEl.appendChild(hidden);
      }
      this.closest(".variante-row")?.remove();
    }
    function variantRemoveNewHandler(e) {
      this.closest(".variante-row")?.remove();
    }
    initVariantRemoveHandlers();

    // global agregarVariante exposed for template buttons
    window.agregarVariante = function () {
      if (!variantesContainer) return;
      const row = document.createElement("div");
      row.className = "variante-row d-flex gap-2 mb-2 align-items-center";
      row.innerHTML =
        '<button type="button" class="btn btn-sm btn-danger variant-remove-btn-new" style="margin-right:6px;">×</button>' +
        '<input type="text" name="variante_nombre[]" class="form-control" placeholder="Nombre variante">' +
        '<input type="number" name="variante_precio[]" class="form-control" placeholder="Precio" step="0.01">' +
        '<input type="number" name="variante_stock[]" class="form-control" placeholder="Stock">' +
        '<input type="text" name="variante_color[]" class="form-control" placeholder="Color">' +
        '<input type="text" name="variante_talla[]" class="form-control" placeholder="Talla">' +
        '<input type="file" name="variante_imagen[]" class="form-control">';
      variantesContainer.appendChild(row);
      // attach new-button handler
      const del = row.querySelector(".variant-remove-btn-new");
      if (del) del.addEventListener("click", variantRemoveNewHandler);
    };

    /* ---------- Fill form from fetched product data (used on edit click) ---------- */
    function fillProductFormFromData(data) {
      if (!data) return;
      // basic fields (IDs used in templates may vary; try both create/edit ids)
      const setIf = (id, val) => {
        const el = safeEl(id);
        if (el) el.value = val === null || val === undefined ? "" : val;
      };
      setIf("producto_id", data.id || "");
      setIf("producto_id_edit", data.id || "");
      setIf("producto_name", data.name || "");
      setIf("producto_name_edit", data.name || "");
      setIf("producto_description", data.description || "");
      setIf("producto_description_edit", data.description || "");
      setIf(
        "producto_price_buy",
        data.price_buy !== undefined ? data.price_buy : ""
      );
      setIf(
        "producto_price_buy_edit",
        data.price_buy !== undefined ? data.price_buy : ""
      );
      setIf("producto_price", data.price !== undefined ? data.price : "");
      setIf("producto_price_edit", data.price !== undefined ? data.price : "");
      setIf("producto_stock", data.stock !== undefined ? data.stock : "");
      setIf("producto_stock_edit", data.stock !== undefined ? data.stock : "");
      setIf(
        "producto_descuento",
        data.descuento !== undefined ? data.descuento : ""
      );
      setIf(
        "producto_descuento_edit",
        data.descuento !== undefined ? data.descuento : ""
      );
      setIf("producto_iva", data.iva !== undefined ? data.iva : "");
      setIf("producto_iva_edit", data.iva !== undefined ? data.iva : "");
      setIf("producto_proveedor", data.proveedor_id || "");
      setIf("producto_proveedor_edit", data.proveedor_id || "");
      setIf("producto_categoria", data.categoria_id || "");
      setIf("producto_categoria_edit", data.categoria_id || "");
      setIf("producto_type", data.type_id || "");
      setIf("producto_type_edit", data.type_id || "");

      // adjust form action to update endpoint (if server expects a different action)
      const theForm = form;
      if (theForm && data.id) {
        // if template expects query param editar=<id> to show edit mode, set action accordingly
        const baseAction =
          theForm.dataset.createAction || window.location.pathname;
        // prefer an explicit edit endpoint if your backend has one:
        // e.g. /dashboard/producto/<id>/editar/  (adjust if needed)
        try {
          theForm.action = `${window.location.pathname}?view=productos&editar=${data.id}`;
          // set submit button label if present
          const submitBtn =
            safeEl("form-submit-btn") || safeEl("form-submit-btn-edit") || null;
          if (submitBtn) submitBtn.textContent = "Actualizar";
        } catch (e) {
          /* ignore */
        }
      }

      // main image preview
      const mainImg = previewMainImg;
      if (mainImg) {
        if (data.imagen) {
          mainImg.src = data.imagen;
          mainImg.style.display = "block";
        } else {
          mainImg.src = "";
          mainImg.style.display = "none";
        }
      }

      // gallery: clear existing previews and render the existing images from API
      if (galleryContainer) {
        galleryContainer.innerHTML = "";
        const galleryArr = Array.isArray(data.gallery)
          ? data.gallery
          : data.gallery_urls || [];
        galleryArr.forEach(function (g) {
          const div = document.createElement("div");
          div.className = "gallery-item position-relative";
          div.style.position = "relative";
          div.style.marginRight = "8px";
          div.style.marginBottom = "8px";
          // show image
          const img = document.createElement("img");
          img.style.maxWidth = "120px";
          img.style.maxHeight = "120px";
          img.style.objectFit = "cover";
          img.style.borderRadius = "6px";
          // API may return objects { id, url } or strings
          if (typeof g === "string") {
            img.src = g;
            div.dataset.galleryId = "";
          } else {
            img.src = g.url || g.imagen || g.galeria || "";
            div.dataset.galleryId = g.id || "";
            if (g.id) div.dataset.galleryId = g.id;
          }
          div.appendChild(img);
          // remove btn
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "btn btn-sm btn-danger gallery-remove-btn";
          btn.textContent = "×";
          btn.style.position = "absolute";
          btn.style.top = "4px";
          btn.style.right = "4px";
          if (div.dataset.galleryId)
            btn.dataset.galleryId = div.dataset.galleryId;
          div.appendChild(btn);
          galleryContainer.appendChild(div);
        });
        // re-init handlers for these new remove buttons
        initExistingGalleryRemoveButtons();
        // re-render new previews (in case there are files already queued)
        renderGalleryPreviews();
      }

      // variantes: render server-provided variants
      if (variantesContainer) {
        variantesContainer.innerHTML = "";
        const vs = Array.isArray(data.variants)
          ? data.variants
          : data.variants_list || [];
        if (vs.length) {
          vs.forEach(function (v) {
            const rowDiv = document.createElement("div");
            rowDiv.className =
              "variante-row d-flex gap-2 mb-2 align-items-center";
            rowDiv.dataset.variantId = v.id || "";
            rowDiv.innerHTML =
              `<button type="button" class="btn btn-sm btn-danger variant-remove-btn" data-variant-id="${
                v.id || ""
              }" style="margin-right:6px;">×</button>` +
              `<input type="text" name="variante_nombre[]" class="form-control" value="${escapeHtml(
                v.nombre
              )}" placeholder="Nombre variante">` +
              `<input type="number" name="variante_precio[]" class="form-control" value="${escapeHtml(
                v.precio
              )}" step="0.01" placeholder="Precio">` +
              `<input type="number" name="variante_stock[]" class="form-control" value="${escapeHtml(
                v.stock
              )}" placeholder="Stock">` +
              `<input type="text" name="variante_color[]" class="form-control" value="${escapeHtml(
                v.color
              )}" placeholder="Color">` +
              `<input type="text" name="variante_talla[]" class="form-control" value="${escapeHtml(
                v.talla
              )}" placeholder="Talla">` +
              `<input type="file" name="variante_imagen[]" class="form-control">`;
            variantesContainer.appendChild(rowDiv);
            if (v.imagen) {
              const img = document.createElement("img");
              img.src = v.imagen;
              img.style.maxWidth = "80px";
              img.style.objectFit = "cover";
              img.style.marginLeft = "6px";
              rowDiv.appendChild(img);
            }
          });
        } else {
          // add an empty row
          const emptyRow = document.createElement("div");
          emptyRow.className =
            "variante-row d-flex gap-2 mb-2 align-items-center";
          emptyRow.innerHTML =
            '<button type="button" class="btn btn-sm btn-danger variant-remove-btn-new" style="display:none; margin-right:6px;">×</button>' +
            '<input type="text" name="variante_nombre[]" class="form-control" placeholder="Nombre variante">' +
            '<input type="number" name="variante_precio[]" class="form-control" placeholder="Precio" step="0.01">' +
            '<input type="number" name="variante_stock[]" class="form-control" placeholder="Stock">' +
            '<input type="text" name="variante_color[]" class="form-control" placeholder="Color">' +
            '<input type="text" name="variante_talla[]" class="form-control" placeholder="Talla">' +
            '<input type="file" name="variante_imagen[]" class="form-control">';
          variantesContainer.appendChild(emptyRow);
        }
        initVariantRemoveHandlers();
      }

      // focus name
      const nm = safeEl("producto_name") || safeEl("producto_name_edit");
      if (nm) nm.focus();
    }

    /* ---------- Click on product rows to open edit mode via API ---------- */
    const rows = qsAll(
      "tr[data-producto-id], tr[data-product-id], .producto-row"
    );
    rows.forEach(function (row) {
      row.style.cursor = "pointer";
      row.addEventListener(
        "click",
        function (e) {
          const tag =
            e.target && e.target.tagName ? e.target.tagName.toLowerCase() : "";
          if (tag === "a" || e.target.closest(".delete-product-btn")) return;
          const productId =
            row.getAttribute("data-producto-id") ||
            row.getAttribute("data-product-id") ||
            row.dataset.productoId ||
            row.dataset.productId;
          if (!productId) return;
          // if there's a form in DOM, use API to fill it; otherwise navigate to server-rendered edit page
          if (!form) {
            window.location.href = `${window.location.pathname}?view=productos&crear=1&editar=${productId}`;
            return;
          }
          const apiUrl = `/dashboard/api/producto/${productId}/`;
          fetch(apiUrl, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" },
          })
            .then((resp) => {
              if (!resp.ok) throw new Error("HTTP " + resp.status);
              return resp.json();
            })
            .then((data) => {
              if (!data || data.error) {
                window.location.href = `${window.location.pathname}?view=productos&crear=1&editar=${productId}`;
                return;
              }
              fillProductFormFromData(data);
              // ensure the form is shown in edit mode visually (if template toggles based on query param, optionally set history)
              try {
                history.replaceState(
                  {},
                  "",
                  `${window.location.pathname}?view=productos&crear=1&editar=${productId}`
                );
              } catch (e) {}
            })
            .catch((err) => {
              console.error("fetch product error", err);
              window.location.href = `${window.location.pathname}?view=productos&crear=1&editar=${productId}`;
            });
        },
        false
      );
    });

    /* ---------- Clear/New button ---------- */
    const clearBtn =
      safeEl("form-clear-btn") ||
      safeEl("form-clear-btn-create") ||
      safeEl("form-clear-btn-edit");
    if (clearBtn && form) {
      clearBtn.addEventListener("click", function () {
        form.reset();
        // clear product_id hidden(s)
        const hid1 = safeEl("producto_id");
        if (hid1) hid1.value = "";
        const hid2 = safeEl("producto_id_edit");
        if (hid2) hid2.value = "";
        // clear previews and state
        if (previewMainImg) {
          previewMainImg.src = "";
          previewMainImg.style.display = "none";
        }
        if (galleryContainer) {
          galleryContainer.innerHTML = "";
        }
        if (variantesContainer) {
          variantesContainer.innerHTML = "";
        }
        galleryFiles = [];
        // reset form action to create-action (if set)
        if (form.dataset && form.dataset.createAction)
          form.action = form.dataset.createAction;
        // reset submit label
        const submitBtn =
          safeEl("form-submit-btn") || safeEl("form-submit-btn-create");
        if (submitBtn) submitBtn.textContent = "Guardar";
      });
    }

    /* ---------- If URL has editar param on load, attempt load product into form ---------- */
    try {
      const params = new URLSearchParams(window.location.search);
      const editarId = params.get("editar");
      if (editarId && form) {
        const apiUrl = `/dashboard/api/producto/${editarId}/`;
        fetch(apiUrl, {
          method: "GET",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        })
          .then((r) => {
            if (!r.ok) throw new Error("HTTP " + r.status);
            return r.json();
          })
          .then((data) => {
            if (data && !data.error) fillProductFormFromData(data);
          })
          .catch((err) => console.error("initial fetch error", err));
      }
    } catch (e) {
      /* ignore */
    }

    /* ---------- Delete product flow (uses showConfirm) ---------- */
    function deleteProduct(productId, rowEl) {
      showConfirm({
        title: "Eliminar producto",
        text: "¿Eliminar este producto? Esta acción no se puede deshacer.",
        confirmText: "Eliminar",
        cancelText: "Cancelar",
        icon: "warning",
        onConfirm: function () {
          fetch(`/dashboard/producto/${productId}/eliminar/`, {
            method: "POST",
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "X-CSRFToken": csrfToken,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ id: productId }),
          })
            .then((r) => r.json().catch(() => ({})))
            .then((data) => {
              if (data && data.success) {
                if (rowEl) rowEl.remove();
                else {
                  const tr = document.querySelector(
                    `tr[data-producto-id="${productId}"], tr[data-product-id="${productId}"]`
                  );
                  if (tr) tr.remove();
                }
                showToast(
                  "Eliminado",
                  "Producto eliminado correctamente",
                  "success",
                  2000
                );
              } else {
                const err =
                  data && data.error
                    ? data.error
                    : "No se pudo eliminar el producto";
                   
              }
            })
            .catch((err) => {
              console.error("delete fetch error", err);
              showToast("Error", "Error eliminando producto", "danger", 4000);
            });
        },
      });
    }

    // attach delete handlers
    document
      .querySelectorAll(".delete-product-btn, .btn-eliminar-producto")
      .forEach((btn) => {
        btn.addEventListener("click", function (e) {
          e.preventDefault();
          const pid =
            this.dataset.productId || this.getAttribute("data-product-id");
          const row = this.closest("tr") || this.closest(".producto-row");
          if (!pid) return;
          deleteProduct(pid, row);
        });
      });

    // delegation for dynamic delete buttons (optional)
    document.addEventListener(
      "click",
      function (e) {
        const del =
          e.target.closest &&
          e.target.closest(".delete-product-btn, .btn-eliminar-producto");
        if (!del) return;
        e.preventDefault();
        const pid =
          del.dataset.productId || del.getAttribute("data-product-id");
        const row = del.closest("tr") || del.closest(".producto-row");
        if (!pid) return;
        deleteProduct(pid, row);
      },
      true
    );

    /* ---------- Before submit: ensure galleryFiles assigned to input (if using custom queued array) ---------- */
    if (form && galInput) {
      form.addEventListener(
        "submit",
        function () {
          rebuildGalInputFiles();
          // ensure any UI-specific hidden markers already exist (we create them when removing)
          // If you want to remove variants/galeria server-side, server must read galeria_delete[] and variante_delete[]
        },
        false
      );
    }

    /* re-init some handlers in case DOM updated dynamically */
    // (expose small public init fns for external use)
    window.__dashboard_reinit = function () {
      initExistingGalleryRemoveButtons();
      initVariantRemoveHandlers();
      // rebind row clicks if rows added later
    };

    console.log("[dashboard.js] initialized");
  }); // DOMContentLoaded end
})();
// ...existing code...

function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}

// ---------- Eliminar usuario desde lista (fetch API) ----------
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.eliminar-usuario-btn').forEach(btn => {
    btn.addEventListener('click', async function (e) {
      const userId = btn.dataset.userId;
      if (!userId) return;
      if (!confirm('¿Eliminar usuario?')) return;
      const csrftoken = getCookie('csrftoken');
      try {
        const res = await fetch(`/dashboard/eliminar_usuario/${userId}/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'Accept': 'application/json'
          },
          credentials: 'same-origin'
        });
        const data = await res.json().catch(() => null);
        if (res.ok && data && data.success) {
          const row = btn.closest('tr');
          if (row) row.remove();
          else location.reload();
        } else {
          alert((data && data.message) || 'Error eliminando usuario');
          console.error('Delete user error', data);
        }
      } catch (err) {
        console.error(err);
        alert('Error de red al eliminar usuario');
      }
    });
  });

  /* ---------- Modal de Detalles de Ventas por Categoría ---------- */
  document.addEventListener('click', function(e) {
    if (e.target.closest('.ver-detalle-categoria')) {
      const btn = e.target.closest('.ver-detalle-categoria');
      const categoriaNombre = btn.dataset.categoria;
      
      // Buscar los datos de la categoría en la tabla
      const row = btn.closest('tr');
      const celdas = row.querySelectorAll('td');
      
      if (celdas.length >= 5) {
        const ingresos = celdas[2].textContent.trim();
        const productos = celdas[3].textContent.trim();
        const pedidos = celdas[4].textContent.trim();
        
        // Actualizar el modal
        document.getElementById('modal-categoria-nombre').textContent = categoriaNombre;
        document.getElementById('modal-categoria-ingresos').textContent = ingresos;
        document.getElementById('modal-categoria-productos').textContent = productos;
        document.getElementById('modal-categoria-pedidos').textContent = pedidos;
        
        // Aquí podrías hacer una llamada AJAX para obtener más detalles
        // Por ahora, mostraremos un mensaje genérico
        const tbody = document.getElementById('modal-productos-detalle');
        tbody.innerHTML = `
          <tr>
            <td colspan="4" class="text-center text-muted">
              <i class="fas fa-info-circle me-2"></i>
              Para ver detalles específicos de productos, visite el análisis completo
            </td>
          </tr>
        `;
      }
    }
  });

  // ---------- Gestión de categorías ----------
  setupCategoryManagement();
});

/* ---------- Category Management Functions ---------- */
function setupCategoryManagement() {
  console.group('🔧 Category Management Setup');
  
  // Event listeners para los botones de categorías
  setupCategoryEventListeners();
  
  // Configurar formularios
  setupCategoryForms();
  
  console.groupEnd();
}

function setupCategoryEventListeners() {
  // Botones de editar categoría
  document.addEventListener('click', function(e) {
    if (e.target.matches('.edit-category-btn') || e.target.closest('.edit-category-btn')) {
      const btn = e.target.closest('.edit-category-btn');
      handleEditCategory(btn);
    }
    
    if (e.target.matches('.delete-category-btn') || e.target.closest('.delete-category-btn')) {
      const btn = e.target.closest('.delete-category-btn');
      handleDeleteCategoryConfirm(btn);
    }
  });
  
  // Botón de confirmar eliminación
  const confirmDeleteBtn = document.getElementById('confirm-delete-category');
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener('click', handleDeleteCategory);
  }
}

function setupCategoryForms() {
  // Formulario de crear categoría
  const createForm = document.getElementById('create-category-form');
  if (createForm) {
    createForm.addEventListener('submit', handleCreateCategory);
  }
  
  // Formulario de editar categoría
  const editForm = document.getElementById('edit-category-form');
  if (editForm) {
    editForm.addEventListener('submit', handleUpdateCategory);
  }
  
  // Auto-generar slug cuando se escriba el nombre (solo en crear)
  const nombreInput = document.getElementById('nombre_categoria');
  const slugInput = document.getElementById('slug_categoria');
  if (nombreInput && slugInput) {
    nombreInput.addEventListener('input', function() {
      if (!slugInput.value || slugInput.dataset.autoGenerated !== 'false') {
        slugInput.value = generateSlug(this.value);
        slugInput.dataset.autoGenerated = 'true';
      }
    });
    
    slugInput.addEventListener('input', function() {
      this.dataset.autoGenerated = 'false';
    });
  }
}

function generateSlug(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[áàäâ]/g, 'a')
    .replace(/[éèëê]/g, 'e')
    .replace(/[íìïî]/g, 'i')
    .replace(/[óòöô]/g, 'o')
    .replace(/[úùüû]/g, 'u')
    .replace(/[ñ]/g, 'n')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

async function handleCreateCategory(e) {
  e.preventDefault();
  console.log('🆕 Creating new category');
  
  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const spinner = submitBtn.querySelector('.spinner-border');
  
  // Mostrar loading
  setButtonLoading(submitBtn, spinner, true);
  
  const formData = new FormData(form);
  const csrftoken = getCookie('csrftoken');
  
  try {
    const response = await fetch('/dashboard/categorias/crear/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Accept': 'application/json'
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast('Categoría creada exitosamente', 'success');
      
      // Cerrar modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalNuevaCategoria'));
      if (modal) modal.hide();
      
      // Limpiar formulario
      form.reset();
      document.getElementById('slug_categoria').dataset.autoGenerated = 'true';
      
      // Actualizar tabla
      addCategoryToTable(data.categoria);
      
    } else {
      showToast(data.message || 'Error al crear la categoría', 'error');
      console.error('Create category error:', data);
    }
  } catch (error) {
    console.error('Create category network error:', error);
    showToast('Error de conexión al crear la categoría', 'error');
  } finally {
    setButtonLoading(submitBtn, spinner, false);
  }
}

function handleEditCategory(btn) {
  const categoryId = btn.dataset.categoryId;
  const categoryNombre = btn.dataset.categoryNombre;
  const categorySlug = btn.dataset.categorySlug;
  
  console.log('✏️ Editing category:', categoryId);
  
  // Llenar el formulario de edición
  document.getElementById('edit_categoria_id').value = categoryId;
  document.getElementById('edit_nombre_categoria').value = categoryNombre;
  document.getElementById('edit_slug_categoria').value = categorySlug;
}

async function handleUpdateCategory(e) {
  e.preventDefault();
  console.log('💾 Updating category');
  
  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const spinner = submitBtn.querySelector('.spinner-border');
  const categoryId = document.getElementById('edit_categoria_id').value;
  
  // Mostrar loading
  setButtonLoading(submitBtn, spinner, true);
  
  const formData = new FormData(form);
  const csrftoken = getCookie('csrftoken');
  
  try {
    const response = await fetch(`/dashboard/categorias/editar/${categoryId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Accept': 'application/json'
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast('Categoría actualizada exitosamente', 'success');
      
      // Cerrar modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarCategoria'));
      if (modal) modal.hide();
      
      // Actualizar tabla
      updateCategoryInTable(categoryId, data.categoria);
      
    } else {
      showToast(data.message || 'Error al actualizar la categoría', 'error');
      console.error('Update category error:', data);
    }
  } catch (error) {
    console.error('Update category network error:', error);
    showToast('Error de conexión al actualizar la categoría', 'error');
  } finally {
    setButtonLoading(submitBtn, spinner, false);
  }
}

function handleDeleteCategoryConfirm(btn) {
  const categoryId = btn.dataset.categoryId;
  const categoryNombre = btn.dataset.categoryNombre;
  
  console.log('🗑️ Confirming delete category:', categoryId);
  
  // Configurar modal de confirmación
  document.getElementById('delete-category-name').textContent = categoryNombre;
  document.getElementById('confirm-delete-category').dataset.categoryId = categoryId;
  
  // Mostrar modal
  const modal = new bootstrap.Modal(document.getElementById('modalEliminarCategoria'));
  modal.show();
}

async function handleDeleteCategory() {
  const btn = document.getElementById('confirm-delete-category');
  const categoryId = btn.dataset.categoryId;
  const spinner = btn.querySelector('.spinner-border');
  
  console.log('❌ Deleting category:', categoryId);
  
  // Mostrar loading
  setButtonLoading(btn, spinner, true);
  
  const csrftoken = getCookie('csrftoken');
  
  try {
    const response = await fetch(`/dashboard/categorias/eliminar/${categoryId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Accept': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast('Categoría eliminada exitosamente', 'success');
      
      // Cerrar modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalEliminarCategoria'));
      if (modal) modal.hide();
      
      // Remover de tabla
      removeCategoryFromTable(categoryId);
      
    } else {
      showToast(data.message || 'Error al eliminar la categoría', 'error');
      console.error('Delete category error:', data);
    }
  } catch (error) {
    console.error('Delete category network error:', error);
    showToast('Error de conexión al eliminar la categoría', 'error');
  } finally {
    setButtonLoading(btn, spinner, false);
  }
}

/* ---------- Table Management Functions ---------- */
function addCategoryToTable(categoria) {
  const tableBody = document.getElementById('categorias-table-body');
  const noDataRow = document.getElementById('no-categories-row');
  
  // Remover fila de "no hay categorías" si existe
  if (noDataRow) {
    noDataRow.remove();
  }
  
  // Crear nueva fila
  const newRow = createCategoryRow(categoria);
  tableBody.appendChild(newRow);
}

function updateCategoryInTable(categoryId, categoria) {
  const row = document.querySelector(`tr[data-category-id="${categoryId}"]`);
  if (row) {
    const newRow = createCategoryRow(categoria);
    row.parentNode.replaceChild(newRow, row);
  }
}

function removeCategoryFromTable(categoryId) {
  const row = document.querySelector(`tr[data-category-id="${categoryId}"]`);
  if (row) {
    row.remove();
    
    // Si no quedan categorías, mostrar mensaje
    const tableBody = document.getElementById('categorias-table-body');
    if (tableBody.children.length === 0) {
      const noDataRow = document.createElement('tr');
      noDataRow.id = 'no-categories-row';
      noDataRow.innerHTML = '<td colspan="5" class="text-center">No hay categorías registradas.</td>';
      tableBody.appendChild(noDataRow);
    }
  }
}

function createCategoryRow(categoria) {
  const row = document.createElement('tr');
  row.setAttribute('data-category-id', categoria.id);
  
  row.innerHTML = `
    <td>${categoria.id}</td>
    <td>${escapeHtml(categoria.nombre)}</td>
    <td>${escapeHtml(categoria.slug)}</td>
    <td>${categoria.products_count || 0}</td>
    <td>
      <button type="button" class="btn btn-sm btn-primary edit-category-btn" 
              data-category-id="${categoria.id}"
              data-category-nombre="${escapeHtml(categoria.nombre)}"
              data-category-slug="${escapeHtml(categoria.slug)}"
              data-bs-toggle="modal" data-bs-target="#modalEditarCategoria">
        <i class="fas fa-edit"></i> Editar
      </button>
      <button type="button" class="btn btn-sm btn-danger delete-category-btn" 
              data-category-id="${categoria.id}"
              data-category-nombre="${escapeHtml(categoria.nombre)}">
        <i class="fas fa-trash"></i> Eliminar
      </button>
    </td>
  `;
  
  return row;
}

/* ---------- Helper Functions ---------- */
function setButtonLoading(button, spinner, isLoading) {
  if (isLoading) {
    button.disabled = true;
    if (spinner) spinner.classList.remove('d-none');
  } else {
    button.disabled = false;
    if (spinner) spinner.classList.add('d-none');
  }
}

/* ---------- Funcionalidad Sidebar Desplegable ---------- */
document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const mainContent = document.querySelector('.main-content');
  
  // Cargar estado del sidebar desde localStorage
  const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (sidebarCollapsed) {
    sidebar.classList.add('collapsed');
    updateMainContentMargin(true);
  }
  
  // Toggle sidebar
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      const isCollapsed = sidebar.classList.toggle('collapsed');
      localStorage.setItem('sidebarCollapsed', isCollapsed);
      updateMainContentMargin(isCollapsed);
      
      // Animación del icono
      const icon = this.querySelector('i');
      if (icon) {
        icon.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
      }
    });
  }
  
  // Función para ajustar el margen del contenido principal
  function updateMainContentMargin(collapsed) {
    if (mainContent) {
      if (collapsed) {
        mainContent.style.marginLeft = '70px';
        mainContent.style.width = 'calc(100% - 70px)';
      } else {
        mainContent.style.marginLeft = '280px';
        mainContent.style.width = 'calc(100% - 280px)';
      }
    }
  }
  
  // Manejo responsive automático
  function handleResize() {
    if (window.innerWidth <= 768) {
      sidebar.classList.add('collapsed');
      updateMainContentMargin(true);
    } else {
      const shouldCollapse = localStorage.getItem('sidebarCollapsed') === 'true';
      if (shouldCollapse) {
        sidebar.classList.add('collapsed');
      } else {
        sidebar.classList.remove('collapsed');
      }
      updateMainContentMargin(shouldCollapse);
    }
  }
  
  // Escuchar cambios de tamaño de pantalla
  window.addEventListener('resize', handleResize);
  
  // Aplicar estado inicial
  handleResize();
  
  // Efecto hover mejorado para enlaces del sidebar
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('mouseenter', function() {
      if (!this.classList.contains('active')) {
        this.style.background = 'rgba(255, 255, 255, 0.15)';
      }
    });
    
    link.addEventListener('mouseleave', function() {
      if (!this.classList.contains('active')) {
        this.style.background = '';
      }
    });
  });
  
  // Animación de carga para los iconos
  const navIcons = document.querySelectorAll('.nav-icon');
  navIcons.forEach((icon, index) => {
    icon.style.opacity = '0';
    icon.style.transform = 'translateY(-10px)';
    
    setTimeout(() => {
      icon.style.transition = 'all 0.3s ease';
      icon.style.opacity = '1';
      icon.style.transform = 'translateY(0)';
    }, index * 50);
  });
});

/* ---------- Inicialización específica para móviles ---------- */
document.addEventListener('DOMContentLoaded', function() {
  console.log('🔧 Dashboard móvil: DOM cargado');
  
  // Función para manejar el menú móvil
  function initMobileMenu() {
    console.log('🔧 Iniciando menú móvil...');
    
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileOverlay = document.getElementById('mobileOverlay');
    const sidebar = document.getElementById('sidebar');
    
    console.log('🔧 Elementos encontrados:', {
      mobileMenuBtn: !!mobileMenuBtn,
      mobileOverlay: !!mobileOverlay,
      sidebar: !!sidebar
    });
    
    if (!mobileMenuBtn || !mobileOverlay || !sidebar) {
      console.warn('⚠️ Elementos del menú móvil no encontrados');
      return;
    }
    
    console.log('✅ Menú móvil: todos los elementos encontrados');
    
    // Abrir menú móvil
    mobileMenuBtn.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('📱 Abriendo menú móvil');
      sidebar.classList.add('mobile-open');
      mobileOverlay.classList.add('active');
      document.body.style.overflow = 'hidden'; // Prevenir scroll
    });
    
    // Cerrar menú móvil
    function closeMobileMenu() {
      console.log('📱 Cerrando menú móvil');
      sidebar.classList.remove('mobile-open');
      mobileOverlay.classList.remove('active');
      document.body.style.overflow = ''; // Restaurar scroll
    }
    
    mobileOverlay.addEventListener('click', closeMobileMenu);
    
    // Cerrar menú al hacer clic en un enlace de navegación
    const navLinks = sidebar.querySelectorAll('.nav-link');
    console.log(`🔧 Enlaces de navegación encontrados: ${navLinks.length}`);
    
    navLinks.forEach(link => {
      link.addEventListener('click', function() {
        // Solo cerrar en móvil
        if (window.innerWidth <= 768) {
          setTimeout(closeMobileMenu, 100);
        }
      });
    });
    
    // Cerrar menú al cambiar orientación o resize
    window.addEventListener('resize', function() {
      if (window.innerWidth > 768) {
        closeMobileMenu();
      }
    });
    
    console.log('✅ Menú móvil inicializado correctamente');
  }
  
  // Inicializar menú móvil
  initMobileMenu();
  
  // Prevenir zoom en iOS al hacer foco en inputs
  if (navigator.userAgent.match(/iPhone|iPad|iPod/i)) {
    const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="number"], input[type="tel"], input[type="url"], select, textarea');
    inputs.forEach(input => {
      input.addEventListener('focus', function() {
        if (input.style.fontSize !== '16px') {
          input.dataset.originalFontSize = input.style.fontSize;
          input.style.fontSize = '16px';
        }
      });
      
      input.addEventListener('blur', function() {
        if (input.dataset.originalFontSize) {
          input.style.fontSize = input.dataset.originalFontSize;
        } else {
          input.style.fontSize = '';
        }
      });
    });
  }
  
  // Mejorar experiencia táctil
  const touchElements = document.querySelectorAll('.btn, .nav-link, .pagination .page-link');
  touchElements.forEach(element => {
    element.style.touchAction = 'manipulation';
  });

  // ========== MANEJO DE BONOS DE DESCUENTO ==========
  
  // Función auxiliar para formatear fecha
  function formatDateTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }
  
  // Configurar atributos min para todos los inputs de fecha al cargar
  function configurarFechasMinimas() {
    const now = new Date();
    const minDate = new Date(now.getTime() - 5 * 60 * 1000); // 5 minutos atrás
    const minDateStr = formatDateTime(minDate);
    
    // Aplicar a todos los inputs datetime-local en modales de bonos
    const fechaInputs = document.querySelectorAll('#modalNuevoBono input[type="datetime-local"], #modalEditarBono input[type="datetime-local"]');
    fechaInputs.forEach(input => {
      if (input.id === 'fecha_inicio' || input.name === 'fecha_inicio') {
        input.min = minDateStr;
        console.log(`📅 Configurado min para ${input.id}:`, minDateStr);
      }
    });
  }
  
  // Ejecutar configuración inicial
  configurarFechasMinimas();
  
  // Configurar fechas por defecto cuando se abre el modal de crear bono
  const modalNuevoBono = document.getElementById('modalNuevoBono');
  if (modalNuevoBono) {
    modalNuevoBono.addEventListener('show.bs.modal', function () {
      console.log('🎯 Abriendo modal de crear bono');
      
      // Obtener fecha y hora actual
      const now = new Date();
      console.log('⏰ Fecha actual:', now.toLocaleString());
      
      // Para fecha de inicio: hora actual
      const fechaInicio = new Date(now);
      // Para fecha de fin: una semana después
      const fechaFin = new Date(now);
      fechaFin.setDate(fechaFin.getDate() + 7);
      
      // Establecer valores por defecto
      const fechaInicioInput = document.getElementById('fecha_inicio');
      const fechaFinInput = document.getElementById('fecha_fin');
      
      if (fechaInicioInput) {
        // Configurar valor mínimo para permitir fechas desde 5 minutos atrás
        const minDate = new Date(now.getTime() - 5 * 60 * 1000); // 5 minutos atrás
        const minDateStr = formatDateTime(minDate);
        const fechaInicioStr = formatDateTime(fechaInicio);
        
        fechaInicioInput.min = minDateStr;
        fechaInicioInput.value = fechaInicioStr;
        
        console.log('📅 Fecha mínima permitida:', minDate.toLocaleString());
        console.log('📅 Fecha inicio establecida:', fechaInicio.toLocaleString());
        console.log('📅 Valor min del input:', fechaInicioInput.min);
        console.log('📅 Valor del input:', fechaInicioInput.value);
        console.log('📅 Input es válido:', fechaInicioInput.checkValidity());
      }
      
      if (fechaFinInput) {
        // Para fecha fin, mínimo debe ser posterior a fecha inicio
        fechaFinInput.min = formatDateTime(fechaInicio);
        fechaFinInput.value = formatDateTime(fechaFin);
        console.log('📅 Fecha fin establecida:', fechaFinInput.value);
      }
      
      // Limpiar otros campos del formulario
      const form = modalNuevoBono.querySelector('form');
      if (form) {
        const inputs = form.querySelectorAll('input:not([type="datetime-local"]), select, textarea');
        inputs.forEach(input => {
          if (input.type === 'checkbox') {
            input.checked = input.getAttribute('checked') !== null;
          } else if (input.tagName === 'SELECT') {
            input.selectedIndex = 0;
          } else {
            input.value = input.defaultValue || '';
          }
        });
      }
    });
    
    // Validación de fechas en tiempo real
    const fechaInicioInput = document.getElementById('fecha_inicio');
    const fechaFinInput = document.getElementById('fecha_fin');
    
    if (fechaInicioInput && fechaFinInput) {
      // Validar cuando cambie fecha de inicio
      fechaInicioInput.addEventListener('change', function() {
        const fechaInicio = new Date(this.value);
        const fechaFinValue = fechaFinInput.value;
        
        // Actualizar el mínimo permitido para fecha fin
        fechaFinInput.min = formatDateTime(fechaInicio);
        
        if (fechaFinValue) {
          const fechaFin = new Date(fechaFinValue);
          if (fechaFin <= fechaInicio) {
            // Establecer fecha fin una hora después de fecha inicio
            const nuevaFechaFin = new Date(fechaInicio);
            nuevaFechaFin.setHours(nuevaFechaFin.getHours() + 1);
            fechaFinInput.value = formatDateTime(nuevaFechaFin);
            
            showToast('Fecha de fin ajustada automáticamente', 'info');
          }
        }
      });
      
      // Validar cuando cambie fecha de fin
      fechaFinInput.addEventListener('change', function() {
        const fechaFin = new Date(this.value);
        const fechaInicioValue = fechaInicioInput.value;
        
        if (fechaInicioValue) {
          const fechaInicio = new Date(fechaInicioValue);
          if (fechaFin <= fechaInicio) {
            showToast('La fecha de fin debe ser posterior a la fecha de inicio', 'error');
            this.focus();
          }
        }
      });
      
      // Configurar atributo min inicial para fecha de inicio
      const now = new Date();
      const minDate = new Date(now.getTime() - 5 * 60 * 1000); // 5 minutos atrás
      fechaInicioInput.min = formatDateTime(minDate);
    }
    
    // Función auxiliar disponible globalmente
    window.formatDateTime = formatDateTime;
  }

  /* ---------- Gestión de Usuarios ---------- */
  function initUserManagement() {
    console.group('🔧 User Management Debug');
    console.log('Inicializando gestión de usuarios');

    // Verificar que los botones existen
    const editBtns = document.querySelectorAll('.edit-user-btn');
    const deleteBtns = document.querySelectorAll('.delete-user-btn');
    const viewBtns = document.querySelectorAll('.view-user-btn');
    
    console.log('Botones encontrados:', {
      edit: editBtns.length,
      delete: deleteBtns.length,
      view: viewBtns.length
    });

    // Event listeners para botones de usuarios
    document.addEventListener('click', function(e) {
      console.log('Click detectado en:', e.target);
      
      if (e.target.matches('.edit-user-btn') || e.target.closest('.edit-user-btn')) {
        e.preventDefault();
        const btn = e.target.matches('.edit-user-btn') ? e.target : e.target.closest('.edit-user-btn');
        const userId = btn.dataset.userId;
        const modelType = btn.dataset.modelType;
        
        console.log('Edit user clicked:', { userId, modelType });
        loadUserForEdit(userId, modelType);
      }

      if (e.target.matches('.delete-user-btn') || e.target.closest('.delete-user-btn')) {
        e.preventDefault();
        const btn = e.target.matches('.delete-user-btn') ? e.target : e.target.closest('.delete-user-btn');
        const userId = btn.dataset.userId;
        const modelType = btn.dataset.modelType;
        const userName = btn.dataset.userName;
        
        console.log('Delete user clicked:', { userId, modelType, userName });
        confirmDeleteUser(userId, modelType, userName);
      }

      if (e.target.matches('.view-user-btn') || e.target.closest('.view-user-btn')) {
        e.preventDefault();
        const btn = e.target.matches('.view-user-btn') ? e.target : e.target.closest('.view-user-btn');
        const userId = btn.dataset.userId;
        const modelType = btn.dataset.modelType;
        
        console.log('View user clicked:', { userId, modelType });
        viewUserDetails(userId, modelType);
      }
    });

    // Event listener para guardar cambios del usuario
    const saveUserBtn = document.getElementById('saveUserChanges');
    if (saveUserBtn) {
      saveUserBtn.addEventListener('click', saveUserChanges);
      console.log('Save user button listener added');
    } else {
      console.warn('Save user button not found');
    }

    console.groupEnd();
  }

  async function loadUserForEdit(userId, modelType) {
    console.log('loadUserForEdit called with:', { userId, modelType });
    
    try {
      const response = await fetch(`/dashboard/usuario/${userId}/${modelType}/detalles/`, {
        method: 'GET',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
        }
      });

      const data = await response.json();
      console.log('User data received:', data);
      
      if (data.success) {
        const user = data.user;
        
        // Verificar que los elementos del formulario existan
        const elements = {
          editUserId: safeEl('editUserId'),
          editUserModelType: safeEl('editUserModelType'),
          editUserName: safeEl('editUserName'),
          editUserEmail: safeEl('editUserEmail'),
          editUserPhone: safeEl('editUserPhone'),
          editUserAddress: safeEl('editUserAddress'),
          editUserCity: safeEl('editUserCity'),
          editUserUsername: safeEl('editUserUsername'),
          editUserModal: safeEl('editUserModal')
        };
        
        console.log('Form elements found:', elements);
        
        // Llenar el formulario de edición
        if (elements.editUserId) elements.editUserId.value = user.id;
        if (elements.editUserModelType) elements.editUserModelType.value = user.model_type;
        if (elements.editUserName) elements.editUserName.value = user.name || '';
        if (elements.editUserEmail) elements.editUserEmail.value = user.email || '';
        if (elements.editUserPhone) elements.editUserPhone.value = user.phone || '';
        if (elements.editUserAddress) elements.editUserAddress.value = user.address || '';
        if (elements.editUserCity) elements.editUserCity.value = user.city || '';
        if (elements.editUserUsername) elements.editUserUsername.value = user.username || '';
        
        // Mostrar el modal
        if (elements.editUserModal) {
          console.log('Showing modal...');
          const modal = new bootstrap.Modal(elements.editUserModal);
          modal.show();
        } else {
          console.error('Modal element not found');
        }
      } else {
        console.error('Error in response:', data.error);
        showToast('Error al cargar usuario: ' + data.error, 'error');
      }
    } catch (error) {
      console.error('Error loading user:', error);
      showToast('Error de conexión al cargar usuario', 'error');
    }
  }

  async function saveUserChanges() {
    const form = safeEl('editUserForm');
    const formData = new FormData(form);
    
    const userData = {
      user_id: formData.get('user_id'),
      model_type: formData.get('model_type'),
      name: formData.get('name'),
      email: formData.get('email'),
      phone: formData.get('phone'),
      address: formData.get('address'),
      city: formData.get('city'),
      username: formData.get('username')
    };

    try {
      const response = await fetch('/dashboard/usuario/editar/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(userData)
      });

      const data = await response.json();
      
      if (data.success) {
        showToast(data.message, 'success');
        
        // Cerrar el modal
        const modal = bootstrap.Modal.getInstance(safeEl('editUserModal'));
        modal.hide();
        
        // Recargar la página para mostrar los cambios
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showToast('Error: ' + data.error, 'error');
      }
    } catch (error) {
      console.error('Error saving user:', error);
      showToast('Error de conexión al guardar usuario', 'error');
    }
  }

  function confirmDeleteUser(userId, modelType, userName) {
    const confirmMsg = modelType === 'register_superuser' 
      ? 'No se pueden eliminar usuarios administradores por seguridad.'
      : `¿Estás seguro de que quieres eliminar el usuario "${userName}"? Esta acción no se puede deshacer.`;
    
    if (modelType === 'register_superuser') {
      showToast(confirmMsg, 'warning');
      return;
    }

    if (confirm(confirmMsg)) {
      deleteUser(userId, modelType);
    }
  }

  async function deleteUser(userId, modelType) {
    try {
      const response = await fetch('/dashboard/usuario/eliminar/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
          user_id: userId,
          model_type: modelType
        })
      });

      const data = await response.json();
      
      if (data.success) {
        showToast(data.message, 'success');
        
        // Recargar la página para mostrar los cambios
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showToast('Error: ' + data.error, 'error');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      showToast('Error de conexión al eliminar usuario', 'error');
    }
  }

  async function viewUserDetails(userId, modelType) {
    try {
      const response = await fetch(`/dashboard/usuario/${userId}/${modelType}/detalles/`, {
        method: 'GET',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
        }
      });

      const data = await response.json();
      
      if (data.success) {
        const user = data.user;
        
        // Crear el contenido del modal
        const detailsContent = `
          <div class="row">
            <div class="col-md-6">
              <h6><i class="fas fa-user me-2"></i>Información Personal</h6>
              <table class="table table-sm">
                <tr><td><strong>ID:</strong></td><td>${user.id}</td></tr>
                <tr><td><strong>Nombre:</strong></td><td>${user.name || 'Sin nombre'}</td></tr>
                <tr><td><strong>Email:</strong></td><td>${user.email}</td></tr>
                <tr><td><strong>Teléfono:</strong></td><td>${user.phone || 'Sin teléfono'}</td></tr>
              </table>
            </div>
            <div class="col-md-6">
              <h6><i class="fas fa-info-circle me-2"></i>Información Adicional</h6>
              <table class="table table-sm">
                <tr><td><strong>Username:</strong></td><td>${user.username || 'Sin username'}</td></tr>
                <tr><td><strong>Ciudad:</strong></td><td>${user.city || 'Sin ciudad'}</td></tr>
                <tr><td><strong>Dirección:</strong></td><td>${user.address || 'Sin dirección'}</td></tr>
                <tr><td><strong>Fecha de Registro:</strong></td><td>${user.date_joined || 'Sin fecha'}</td></tr>
              </table>
            </div>
          </div>
          <div class="row mt-3">
            <div class="col-12">
              <h6><i class="fas fa-shield-alt me-2"></i>Permisos</h6>
              <div class="d-flex gap-2">
                ${user.is_admin 
                  ? '<span class="badge bg-danger"><i class="fas fa-crown me-1"></i>Administrador</span>' 
                  : '<span class="badge bg-primary"><i class="fas fa-user me-1"></i>Usuario Simple</span>'
                }
                <span class="badge bg-info">Tipo: ${user.model_type}</span>
              </div>
            </div>
          </div>
        `;
        
        // Mostrar el contenido en el modal
        safeEl('userDetailsContent').innerHTML = detailsContent;
        
        // Mostrar el modal
        const modal = new bootstrap.Modal(safeEl('viewUserModal'));
        modal.show();
      } else {
        showToast('Error al cargar detalles: ' + data.error, 'error');
      }
    } catch (error) {
      console.error('Error viewing user details:', error);
      showToast('Error de conexión al cargar detalles', 'error');
    }
  }

  // Inicializar gestión de usuarios cuando el documento esté listo
  document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Inicializando gestión de usuarios');
    initUserManagement();
  });
  
  // También llamar cuando se carga la página
  window.addEventListener('load', function() {
    console.log('Window loaded - Verificando gestión de usuarios');
    initUserManagement();
  });

  // También inicializar cuando cambie la vista
  window.addEventListener('popstate', function() {
    const currentView = new URLSearchParams(window.location.search).get('view');
    if (currentView === 'usuarios') {
      console.log('Vista de usuarios detectada en popstate');
      initUserManagement();
    }
  });
  
  // Función global para debugging
  window.debugUserManagement = function() {
    initUserManagement();
  };

});