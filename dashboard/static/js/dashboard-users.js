/* ========================================
   DASHBOARD USUARIOS - Sistema de Gestión
   Gestión CRUD completa de usuarios (SimpleUser y RegisterSuperUser)
   ======================================== */

(function() {
    'use strict';

    // ============================
    // UTILIDADES
    // ============================

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

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    // ============================
    // CARGAR USUARIO PARA EDICIÓN
    // ============================

    async function loadUserForEditInline(userId, modelType) {
        console.log('📝 Cargando usuario para editar:', userId, modelType);
        
        try {
            const response = await fetch(`/dashboard/usuario/${userId}/${modelType}/detalles/`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Error al cargar usuario');
            }

            const user = data.user;
            
            // Llenar campos básicos
            document.getElementById('editUserId').value = user.id;
            document.getElementById('editUserModelType').value = user.model_type;
            document.getElementById('editUserName').value = user.name || '';
            document.getElementById('editUserEmail').value = user.email || '';
            document.getElementById('editUserPhone').value = user.phone || '';
            document.getElementById('editUserAddress').value = user.address || '';
            document.getElementById('editUserCity').value = user.city || '';
            document.getElementById('editUserUsername').value = user.username || '';
            
            // Limpiar contraseñas
            document.getElementById('editUserPassword').value = '';
            document.getElementById('editUserConfirmPassword').value = '';
            
            // Mostrar/ocultar secciones según tipo de usuario
            const permissionsSection = document.getElementById('permissionsSection');
            const simpleUserSection = document.getElementById('simpleUserSection');
            
            if (modelType === 'register_superuser') {
                // Usuario administrador
                permissionsSection.style.display = 'block';
                simpleUserSection.style.display = 'none';
                
                document.getElementById('editUserIsActive').checked = user.is_active !== false;
                document.getElementById('editUserIsStaff').checked = user.is_staff || false;
                document.getElementById('editUserIsSuperuser').checked = user.is_superuser || false;
            } else {
                // Usuario simple
                permissionsSection.style.display = 'none';
                simpleUserSection.style.display = 'block';
                
                document.getElementById('editSimpleUserIsActive').checked = user.is_active !== false;
            }
            
            // Mostrar modal
            const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
            modal.show();
            
            console.log('✅ Modal de edición mostrado');
            
        } catch (error) {
            console.error('❌ Error al cargar usuario:', error);
            showToast('Error al cargar usuario: ' + error.message, 'danger');
        }
    }

    // ============================
    // VER DETALLES DE USUARIO
    // ============================

    async function viewUserDetailsInline(userId, modelType) {
        console.log('👁️ Visualizando detalles del usuario:', userId, modelType);
        
        try {
            const response = await fetch(`/dashboard/usuario/${userId}/${modelType}/detalles/`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Error al cargar detalles');
            }

            const user = data.user;
            
            const detailsContent = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0"><i class="fas fa-user me-2"></i>Información Personal</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-borderless mb-0">
                                    <tr>
                                        <td class="text-muted" style="width: 40%"><strong>ID:</strong></td>
                                        <td>${user.id}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted"><strong>Nombre:</strong></td>
                                        <td>${user.name || '<em class="text-muted">Sin nombre</em>'}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted"><strong>Email:</strong></td>
                                        <td>${user.email}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted"><strong>Teléfono:</strong></td>
                                        <td>${user.phone || '<em class="text-muted">Sin teléfono</em>'}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-info text-white">
                                <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Información Adicional</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-borderless mb-0">
                                    <tr>
                                        <td class="text-muted" style="width: 40%"><strong>Username:</strong></td>
                                        <td>${user.username || '<em class="text-muted">Sin username</em>'}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted"><strong>Ciudad:</strong></td>
                                        <td>${user.city || '<em class="text-muted">Sin ciudad</em>'}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted"><strong>Dirección:</strong></td>
                                        <td>${user.address || '<em class="text-muted">Sin dirección</em>'}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted"><strong>Fecha registro:</strong></td>
                                        <td>${user.date_joined ? new Date(user.date_joined).toLocaleString('es-CO') : '<em class="text-muted">Sin fecha</em>'}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${modelType === 'register_superuser' ? `
                    <div class="card border-warning">
                        <div class="card-header bg-warning">
                            <h6 class="mb-0"><i class="fas fa-user-shield me-2"></i>Permisos de Administrador</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4 text-center">
                                    <p class="mb-1"><strong>Activo:</strong></p>
                                    <span class="badge bg-${user.is_active ? 'success' : 'secondary'} fs-6">
                                        ${user.is_active ? '✓ Activo' : '✗ Inactivo'}
                                    </span>
                                </div>
                                <div class="col-md-4 text-center">
                                    <p class="mb-1"><strong>Staff:</strong></p>
                                    <span class="badge bg-${user.is_staff ? 'primary' : 'secondary'} fs-6">
                                        ${user.is_staff ? '✓ Es Staff' : '✗ No Staff'}
                                    </span>
                                </div>
                                <div class="col-md-4 text-center">
                                    <p class="mb-1"><strong>Superusuario:</strong></p>
                                    <span class="badge bg-${user.is_superuser ? 'danger' : 'secondary'} fs-6">
                                        ${user.is_superuser ? '✓ Superusuario' : '✗ No Superusuario'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                ` : `
                    <div class="card border-info">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0"><i class="fas fa-user-check me-2"></i>Estado</h6>
                        </div>
                        <div class="card-body text-center">
                            <span class="badge bg-${user.is_active ? 'success' : 'secondary'} fs-5">
                                ${user.is_active ? '✓ Usuario Activo' : '✗ Usuario Inactivo'}
                            </span>
                        </div>
                    </div>
                `}
            `;
            
            document.getElementById('userDetailsContent').innerHTML = detailsContent;
            
            const modal = new bootstrap.Modal(document.getElementById('viewUserModal'));
            modal.show();
            
            console.log('✅ Modal de detalles mostrado');
            
        } catch (error) {
            console.error('❌ Error al visualizar usuario:', error);
            showToast('Error al cargar detalles: ' + error.message, 'danger');
        }
    }

    // ============================
    // ELIMINAR USUARIO
    // ============================

    function confirmDeleteUserInline(userId, modelType, userName) {
        if (modelType === 'register_superuser') {
            showToast('⚠️ No se pueden eliminar usuarios administradores por seguridad.', 'warning');
            return;
        }
        
        if (confirm(`⚠️ ¿Estás seguro de que quieres eliminar el usuario "${userName}"?\n\nEsta acción no se puede deshacer.`)) {
            deleteUserInline(userId, modelType);
        }
    }

    async function deleteUserInline(userId, modelType) {
        console.log('🗑️ Eliminando usuario:', userId, modelType);
        
        try {
            const response = await fetch('/dashboard/usuario/eliminar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    user_id: userId,
                    model_type: modelType
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('✅ ' + data.message, 'success');
                
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Error al eliminar usuario');
            }
        } catch (error) {
            console.error('❌ Error al eliminar usuario:', error);
            showToast('Error: ' + error.message, 'danger');
        }
    }

    // ============================
    // GUARDAR CAMBIOS
    // ============================

    async function saveUserChangesInline() {
        const form = document.getElementById('editUserForm');
        const formData = new FormData(form);
        
        // Validar contraseñas
        const password = document.getElementById('editUserPassword').value;
        const confirmPassword = document.getElementById('editUserConfirmPassword').value;
        
        if (password && password !== confirmPassword) {
            showToast('❌ Las contraseñas no coinciden', 'danger');
            return;
        }
        
        if (password && password.length < 6) {
            showToast('❌ La contraseña debe tener al menos 6 caracteres', 'warning');
            return;
        }

        // Validar email
        const email = formData.get('email');
        if (!email || !email.includes('@')) {
            showToast('❌ Email inválido', 'danger');
            return;
        }
        
        const modelType = formData.get('model_type');
        
        const userData = {
            user_id: formData.get('user_id'),
            model_type: modelType,
            name: formData.get('name'),
            email: email,
            phone: formData.get('phone'),
            address: formData.get('address'),
            city: formData.get('city'),
            username: formData.get('username')
        };
        
        // Agregar contraseña si se proporcionó
        if (password) {
            userData.password = password;
        }
        
        // Agregar permisos según tipo de usuario
        if (modelType === 'register_superuser') {
            userData.is_active = document.getElementById('editUserIsActive').checked;
            userData.is_staff = document.getElementById('editUserIsStaff').checked;
            userData.is_superuser = document.getElementById('editUserIsSuperuser').checked;
        } else {
            userData.is_active = document.getElementById('editSimpleUserIsActive').checked;
        }
        
        console.log('💾 Guardando cambios de usuario:', userData);
        
        try {
            const response = await fetch('/dashboard/usuario/editar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('✅ ' + data.message, 'success');
                
                // Cerrar modal
                const modalElement = document.getElementById('editUserModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
                
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Error al guardar cambios');
            }
        } catch (error) {
            console.error('❌ Error al guardar cambios:', error);
            showToast('Error: ' + error.message, 'danger');
        }
    }

    // ============================
    // INICIALIZACIÓN
    // ============================

    function init() {
        console.log('🚀 Inicializando gestión de usuarios...');
        
        // Event delegation para botones de usuarios
        document.addEventListener('click', function(e) {
            const target = e.target;
            
            // Botón editar
            if (target.matches('.edit-user-btn') || target.closest('.edit-user-btn')) {
                e.preventDefault();
                const btn = target.matches('.edit-user-btn') ? target : target.closest('.edit-user-btn');
                const userId = btn.dataset.userId;
                const modelType = btn.dataset.modelType;
                
                console.log('✏️ Edit user clicked:', { userId, modelType });
                loadUserForEditInline(userId, modelType);
            }
            
            // Botón ver detalles
            if (target.matches('.view-user-btn') || target.closest('.view-user-btn')) {
                e.preventDefault();
                const btn = target.matches('.view-user-btn') ? target : target.closest('.view-user-btn');
                const userId = btn.dataset.userId;
                const modelType = btn.dataset.modelType;
                
                console.log('👁️ View user clicked:', { userId, modelType });
                viewUserDetailsInline(userId, modelType);
            }
            
            // Botón eliminar
            if (target.matches('.delete-user-btn') || target.closest('.delete-user-btn')) {
                e.preventDefault();
                const btn = target.matches('.delete-user-btn') ? target : target.closest('.delete-user-btn');
                const userId = btn.dataset.userId;
                const modelType = btn.dataset.modelType;
                const userName = btn.dataset.userName;
                
                console.log('🗑️ Delete user clicked:', { userId, modelType, userName });
                confirmDeleteUserInline(userId, modelType, userName);
            }
        });
        
        // Listener para botón guardar
        const saveBtn = document.getElementById('saveUserChanges');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveUserChangesInline);
        }
        
        console.log('✅ Gestión de usuarios inicializada correctamente');
    }

    // ============================
    // EXPORTAR FUNCIONES GLOBALES
    // ============================

    window.DashboardUsers = {
        loadForEdit: loadUserForEditInline,
        viewDetails: viewUserDetailsInline,
        confirmDelete: confirmDeleteUserInline,
        saveChanges: saveUserChangesInline
    };

    // Alias para compatibilidad con código existente
    window.loadUserForEditInline = loadUserForEditInline;
    window.viewUserDetailsInline = viewUserDetailsInline;
    window.confirmDeleteUserInline = confirmDeleteUserInline;
    window.saveUserChangesInline = saveUserChangesInline;

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    console.log('✅ Dashboard Users JS cargado correctamente');

})();
