/* ========================================
   DASHBOARD PEDIDOS - Sistema de Gestión
   Gestión completa de pedidos, estados y visualización
   ======================================== */

(function() {
    'use strict';

    // ============================
    // UTILIDADES
    // ============================

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
               getCookie('csrftoken');
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function formatCurrency(amount) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(amount);
    }

    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // ============================
    // VISUALIZACIÓN DE PEDIDOS
    // ============================

    function loadPedidoDetails(pedidoId) {
        console.group('👁️ Cargar Detalles del Pedido');
        console.log('ID del pedido:', pedidoId);
        
        const modalElement = document.getElementById('pedidoModal');
        const modalContent = document.getElementById('pedidoModalContent');
        
        if (!modalContent || !modalElement) {
            console.error('❌ No se encontró el modal o su contenedor');
            console.groupEnd();
            return;
        }

        // Mostrar spinner mientras carga
        modalContent.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2 text-muted">Cargando detalles del pedido...</p>
            </div>
        `;

        // Abrir el modal manualmente añadiendo clases de Bootstrap
        modalElement.classList.add('show');
        modalElement.style.display = 'block';
        modalElement.setAttribute('aria-modal', 'true');
        modalElement.removeAttribute('aria-hidden');
        
        // Agregar backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        backdrop.id = 'pedidoModalBackdrop';
        document.body.appendChild(backdrop);
        document.body.classList.add('modal-open');
        
        console.log('✅ Modal abierto');
        console.groupEnd();

        fetch(`/dashboard/pedido/${pedidoId}/detalle/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modalContent.innerHTML = buildPedidoDetailHTML(data.pedido);
            } else {
                modalContent.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Error al cargar los detalles: ${data.error || 'Error desconocido'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modalContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> 
                    Error de conexión. Por favor intenta de nuevo.
                </div>
            `;
        });
    }

    function buildPedidoDetailHTML(pedido) {
        return `
            <div class="row">
                <!-- Información del cliente -->
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header bg-primary text-white">
                            <h6 class="mb-0"><i class="fas fa-user"></i> Información del Cliente</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Nombre:</strong> ${pedido.nombre}</p>
                            <p><strong>Email:</strong> ${pedido.email || 'No proporcionado'}</p>
                            <p><strong>Teléfono:</strong> ${pedido.telefono || 'No proporcionado'}</p>
                            <p class="mb-0"><strong>Fecha del pedido:</strong> ${new Date(pedido.fecha).toLocaleString('es-CO')}</p>
                        </div>
                    </div>
                </div>

                <!-- Información de entrega -->
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0"><i class="fas fa-map-marker-alt"></i> Información de Entrega</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Dirección:</strong> ${pedido.direccion}</p>
                            <p><strong>Ciudad:</strong> ${pedido.ciudad}</p>
                            <p><strong>Departamento:</strong> ${pedido.departamento}</p>
                            ${pedido.codigo_postal ? `<p><strong>Código Postal:</strong> ${pedido.codigo_postal}</p>` : ''}
                            ${pedido.nota ? `<p class="mb-0"><strong>Nota del cliente:</strong><br><em>"${pedido.nota}"</em></p>` : '<p class="mb-0 text-muted">Sin notas del cliente</p>'}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Notas Administrativas -->
            <div class="row mb-3">
                <div class="col-12">
                    <div class="card border-warning">
                        <div class="card-header bg-warning">
                            <h6 class="mb-0"><i class="fas fa-clipboard"></i> Notas Administrativas (Internas)</h6>
                        </div>
                        <div class="card-body">
                            <div class="mb-2">
                                <textarea id="nota_admin_${pedido.id}" class="form-control" rows="3" 
                                          placeholder="Agregar notas internas sobre el pedido (no visibles para el cliente)...">${pedido.nota_admin || ''}</textarea>
                            </div>
                            <button type="button" class="btn btn-sm btn-primary" onclick="window.DashboardPedidos.updateAdminNotes(${pedido.id})">
                                <i class="fas fa-save"></i> Guardar Notas
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Estados y pago -->
            <div class="row mb-3">
                <div class="col-md-4">
                    <div class="card border-primary h-100">
                        <div class="card-body text-center">
                            <h6 class="text-primary mb-3"><i class="fas fa-box"></i> Estado del Pedido</h6>
                            <span class="badge bg-${getEstadoBadgeColor(pedido.estado)} fs-6 mb-2">
                                ${pedido.estado_display}
                            </span>
                            <div class="dropdown mt-3">
                                <button class="btn btn-sm btn-outline-primary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                    Cambiar Estado
                                </button>
                                <ul class="dropdown-menu">
                                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="window.DashboardPedidos.updateEstado(${pedido.id}, 'pendiente')">
                                        <i class="fas fa-clock text-warning"></i> Pendiente
                                    </a></li>
                                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="window.DashboardPedidos.updateEstado(${pedido.id}, 'confirmado')">
                                        <i class="fas fa-check-circle text-info"></i> Confirmado
                                    </a></li>
                                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="window.DashboardPedidos.updateEstado(${pedido.id}, 'enviado')">
                                        <i class="fas fa-shipping-fast text-primary"></i> Enviado
                                    </a></li>
                                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="window.DashboardPedidos.updateEstado(${pedido.id}, 'llegando')">
                                        <i class="fas fa-truck text-primary"></i> Llegando
                                    </a></li>
                                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="window.DashboardPedidos.updateEstado(${pedido.id}, 'entregado')">
                                        <i class="fas fa-check-double text-success"></i> Entregado
                                    </a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="javascript:void(0)" onclick="window.DashboardPedidos.updateEstado(${pedido.id}, 'cancelado')">
                                        <i class="fas fa-times-circle"></i> Cancelar Pedido
                                    </a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-info h-100">
                        <div class="card-body text-center">
                            <h6 class="text-info mb-3"><i class="fas fa-wallet"></i> Método de Pago</h6>
                            <span class="badge bg-${getMetodoPagoBadgeColor(pedido.metodo_pago)} fs-6">
                                ${pedido.metodo_pago_display}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-success h-100">
                        <div class="card-body text-center">
                            <h6 class="text-success mb-3"><i class="fas fa-dollar-sign"></i> Estado del Pago</h6>
                            <span class="badge bg-${getPagoBadgeColor(pedido.estado_pago)} fs-6">
                                ${pedido.estado_pago_display}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            ${pedido.transaction_id ? `
                <div class="alert alert-info mb-3">
                    <h6><i class="fas fa-credit-card"></i> Información de Pago Digital</h6>
                    <p class="mb-1"><strong>ID de Transacción:</strong> <code>${pedido.transaction_id}</code></p>
                    ${pedido.payment_reference ? `<p class="mb-0"><strong>Referencia:</strong> <code>${pedido.payment_reference}</code></p>` : ''}
                </div>
            ` : ''}

            <!-- Productos del pedido -->
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h6 class="mb-0"><i class="fas fa-shopping-bag"></i> Productos del Pedido</h6>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-sm table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Producto</th>
                                    <th class="text-center">Cantidad</th>
                                    <th class="text-end">Precio Unit.</th>
                                    <th class="text-end">Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${pedido.items && pedido.items.length > 0 ? pedido.items.map(item => `
                                    <tr>
                                        <td>
                                            <strong>${item.nombre}</strong>
                                            ${item.variante ? `<br><small class="text-muted"><i class="fas fa-tag"></i> Variante: ${item.variante}</small>` : ''}
                                        </td>
                                        <td class="text-center">
                                            <span class="badge bg-secondary">${item.cantidad}</span>
                                        </td>
                                        <td class="text-end">${formatCurrency(item.precio)}</td>
                                        <td class="text-end"><strong>${formatCurrency(item.precio * item.cantidad)}</strong></td>
                                    </tr>
                                `).join('') : '<tr><td colspan="4" class="text-center text-muted py-4">No hay productos registrados</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="card-footer bg-light">
                    <div class="row">
                        <div class="col-md-8"></div>
                        <div class="col-md-4">
                            ${pedido.subtotal ? `<p class="mb-1 d-flex justify-content-between">
                                <span>Subtotal:</span> <strong>${formatCurrency(pedido.subtotal)}</strong>
                            </p>` : ''}
                            ${pedido.codigo_descuento ? `<p class="mb-1 text-success d-flex justify-content-between">
                                <span>Descuento (${pedido.codigo_descuento}):</span> 
                                <strong>-${formatCurrency(pedido.descuento)}</strong>
                            </p>` : ''}
                            ${pedido.envio > 0 ? `<p class="mb-1 d-flex justify-content-between">
                                <span>Envío:</span> <strong>${formatCurrency(pedido.envio)}</strong>
                            </p>` : `<p class="mb-1 text-success d-flex justify-content-between">
                                <span>Envío:</span> <strong>GRATIS</strong>
                            </p>`}
                            <hr>
                            <h5 class="mb-0 d-flex justify-content-between">
                                <span>Total:</span> <strong class="text-success">${formatCurrency(pedido.total)}</strong>
                            </h5>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // ============================
    // FUNCIONES DE BADGE
    // ============================

    function getEstadoBadgeColor(estado) {
        const colors = {
            'pendiente': 'warning',
            'confirmado': 'info',
            'enviado': 'primary',
            'llegando': 'primary',
            'entregado': 'success',
            'cancelado': 'danger'
        };
        return colors[estado] || 'secondary';
    }

    function getMetodoPagoBadgeColor(metodo) {
        const colors = {
            'contraentrega': 'warning',
            'recoger_tienda': 'info',
            'tarjeta': 'primary',
            'wompi': 'primary'
        };
        return colors[metodo] || 'secondary';
    }

    function getPagoBadgeColor(estado) {
        const colors = {
            'pendiente': 'warning',
            'procesando': 'info',
            'completado': 'success',
            'fallido': 'danger',
            'reembolsado': 'secondary'
        };
        return colors[estado] || 'secondary';
    }

    // ============================
    // ACTUALIZACIÓN DE ESTADOS
    // ============================

    function updateEstado(pedidoId, nuevoEstado) {
        let confirmMessage;
        
        if (nuevoEstado === 'cancelado') {
            confirmMessage = `⚠️ ¿Estás seguro de CANCELAR el pedido #${pedidoId}?\n\n` +
                           `Esta acción:\n` +
                           `• Devolverá el stock de todos los productos al inventario\n` +
                           `• Excluirá este pedido de las estadísticas de ventas\n` +
                           `• No podrá deshacerse una vez confirmada`;
        } else {
            const estados = {
                'pendiente': 'Pendiente',
                'confirmado': 'Confirmado',
                'enviado': 'Enviado',
                'llegando': 'Llegando',
                'entregado': 'Entregado'
            };
            confirmMessage = `¿Cambiar el estado del pedido #${pedidoId} a "${estados[nuevoEstado]}"?`;
        }
        
        if (!confirm(confirmMessage)) {
            return;
        }

        console.log('🔄 Actualizando estado del pedido:', pedidoId, 'a', nuevoEstado);

        // Mostrar loader
        const loader = document.createElement('div');
        loader.className = 'alert alert-info position-fixed';
        loader.style.top = '20px';
        loader.style.right = '20px';
        loader.style.zIndex = '9999';
        loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Actualizando estado...';
        document.body.appendChild(loader);

        fetch('/dashboard/pedido/update-estado/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pedido_id: pedidoId,
                nuevo_estado: nuevoEstado
            })
        })
        .then(response => response.json())
        .then(data => {
            loader.remove();
            
            if (data.success) {
                let successMessage;
                if (nuevoEstado === 'cancelado') {
                    successMessage = '✅ Pedido cancelado - Stock devuelto al inventario';
                } else {
                    successMessage = `✅ Estado actualizado correctamente`;
                }
                
                showAlert(successMessage, 'success');
                
                // Recargar después de 1 segundo
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                showAlert('❌ Error: ' + (data.error || 'Error desconocido'), 'danger');
            }
        })
        .catch(error => {
            loader.remove();
            console.error('Error:', error);
            showAlert('❌ Error de conexión. Intenta de nuevo.', 'danger');
        });
    }

    // ============================
    // CONFIRMAR PAGO
    // ============================

    function confirmarPago(pedidoId) {
        if (!confirm(`¿Confirmar el pago del pedido #${pedidoId}?\n\nEsto actualizará el estado de pago a "completado" y se reflejará en las ventas del día.`)) {
            return;
        }

        console.log('💰 Confirmando pago del pedido:', pedidoId);

        // Mostrar loader
        const loader = document.createElement('div');
        loader.className = 'alert alert-info position-fixed';
        loader.style.top = '20px';
        loader.style.right = '20px';
        loader.style.zIndex = '9999';
        loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Confirmando pago...';
        document.body.appendChild(loader);

        fetch('/dashboard/pedido/confirmar-pago/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pedido_id: pedidoId
            })
        })
        .then(response => response.json())
        .then(data => {
            loader.remove();
            
            if (data.success) {
                showAlert('✅ ' + data.message, 'success');
                
                // Recargar después de 1 segundo
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                showAlert('❌ Error: ' + (data.error || 'Error desconocido'), 'danger');
            }
        })
        .catch(error => {
            loader.remove();
            console.error('Error:', error);
            showAlert('❌ Error de conexión. Intenta de nuevo.', 'danger');
        });
    }

    // ============================
    // NOTAS ADMINISTRATIVAS
    // ============================

    function updateAdminNotes(pedidoId) {
        const notasTextarea = document.getElementById(`nota_admin_${pedidoId}`);
        if (!notasTextarea) {
            showAlert('❌ No se encontró el campo de notas', 'danger');
            return;
        }

        const notas = notasTextarea.value.trim();

        console.log('📝 Actualizando notas del pedido:', pedidoId);

        fetch('/dashboard/pedido/update-notes/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pedido_id: pedidoId,
                notas_admin: notas
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('✅ Notas administrativas guardadas correctamente', 'success');
            } else {
                showAlert('❌ Error al guardar: ' + (data.error || 'Error desconocido'), 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('❌ Error de conexión. Intenta de nuevo.', 'danger');
        });
    }

    // ============================
    // EXPORTAR FUNCIONES GLOBALES
    // ============================

    window.DashboardPedidos = {
        viewDetails: loadPedidoDetails,
        updateEstado: updateEstado,
        updateAdminNotes: updateAdminNotes,
        confirmarPago: confirmarPago
    };
    
    // Exportar directamente para compatibilidad
    window.loadPedidoDetails = loadPedidoDetails;
    window.viewPedidoDetails = loadPedidoDetails; // Alias
    window.updateEstado = updateEstado;
    window.updateAdminNotes = updateAdminNotes;
    window.confirmarPago = confirmarPago;

    // ============================
    // INICIALIZACIÓN
    // ============================
    
    // Configurar event listeners para cerrar el modal y dropdowns
    document.addEventListener('DOMContentLoaded', function() {
        // Manejar dropdowns de estado manualmente
        document.addEventListener('click', function(e) {
            const dropdownToggle = e.target.closest('[data-bs-toggle="dropdown"]');
            if (dropdownToggle) {
                e.preventDefault();
                e.stopPropagation();
                
                const dropdownMenu = dropdownToggle.nextElementSibling;
                if (dropdownMenu && dropdownMenu.classList.contains('dropdown-menu')) {
                    // Cerrar otros dropdowns abiertos
                    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                        if (menu !== dropdownMenu) {
                            menu.classList.remove('show');
                        }
                    });
                    
                    // Toggle este dropdown
                    dropdownMenu.classList.toggle('show');
                }
            } else if (!e.target.closest('.dropdown-menu')) {
                // Cerrar dropdowns si se hace click fuera
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });
        
        const modal = document.getElementById('pedidoModal');
        if (modal) {
            // Event listener para botones de cerrar
            modal.addEventListener('click', function(e) {
                if (e.target.matches('[data-bs-dismiss="modal"]') || e.target.closest('[data-bs-dismiss="modal"]')) {
                    // Cerrar modal
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    modal.removeAttribute('aria-modal');
                    modal.setAttribute('aria-hidden', 'true');
                    
                    // Remover backdrop
                    const backdrop = document.getElementById('pedidoModalBackdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                    document.body.classList.remove('modal-open');
                }
            });
            
            // Cerrar con ESC
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && modal.classList.contains('show')) {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    modal.removeAttribute('aria-modal');
                    modal.setAttribute('aria-hidden', 'true');
                    
                    const backdrop = document.getElementById('pedidoModalBackdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                    document.body.classList.remove('modal-open');
                }
            });
        }
    });

    console.log('✅ Dashboard Pedidos JS cargado correctamente');

})();
