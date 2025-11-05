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
});