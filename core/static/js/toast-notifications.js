/**
 * Sistema Moderno de Notificaciones Toast
 * Reemplaza los alerts nativos con notificaciones elegantes
 */

(function() {
    'use strict';
    
    // Crear contenedor de toasts si no existe
    function createToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    // Función principal para mostrar toast
    window.showToast = function(message, type = 'info', duration = 4000) {
        const container = createToastContainer();
        
        // Configuración de iconos y colores según tipo
        const config = {
            success: {
                icon: '<i class="fas fa-check-circle"></i>',
                class: 'toast-success',
                color: '#10b981'
            },
            error: {
                icon: '<i class="fas fa-times-circle"></i>',
                class: 'toast-error',
                color: '#ef4444'
            },
            warning: {
                icon: '<i class="fas fa-exclamation-triangle"></i>',
                class: 'toast-warning',
                color: '#f59e0b'
            },
            info: {
                icon: '<i class="fas fa-info-circle"></i>',
                class: 'toast-info',
                color: '#3b82f6'
            }
        };
        
        const toastConfig = config[type] || config.info;
        
        // Crear elemento toast
        const toast = document.createElement('div');
        toast.className = `toast ${toastConfig.class}`;
        toast.innerHTML = `
            <div class="toast-icon">${toastConfig.icon}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close" aria-label="Cerrar">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Agregar al contenedor con animación
        container.appendChild(toast);
        
        // Trigger reflow para animación
        toast.offsetHeight;
        toast.classList.add('show');
        
        // Función para cerrar toast
        function closeToast() {
            toast.classList.remove('show');
            toast.classList.add('hiding');
            setTimeout(() => {
                if (toast.parentNode === container) {
                    container.removeChild(toast);
                }
                // Limpiar contenedor si está vacío
                if (container.children.length === 0) {
                    container.remove();
                }
            }, 300);
        }
        
        // Botón cerrar
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', closeToast);
        
        // Auto-cerrar después de duración
        if (duration > 0) {
            setTimeout(closeToast, duration);
        }
        
        return toast;
    };
    
    // Atajos para tipos específicos
    window.showSuccess = function(message, duration) {
        return showToast(message, 'success', duration);
    };
    
    window.showError = function(message, duration) {
        return showToast(message, 'error', duration);
    };
    
    window.showWarning = function(message, duration) {
        return showToast(message, 'warning', duration);
    };
    
    window.showInfo = function(message, duration) {
        return showToast(message, 'info', duration);
    };
    
    // Función para confirmación moderna (reemplaza confirm())
    window.showConfirm = function(options) {
        return new Promise((resolve) => {
            const defaults = {
                title: '¿Estás seguro?',
                message: '¿Deseas continuar con esta acción?',
                confirmText: 'Confirmar',
                cancelText: 'Cancelar',
                type: 'warning'
            };
            
            const config = { ...defaults, ...options };
            
            // Crear overlay
            const overlay = document.createElement('div');
            overlay.className = 'confirm-overlay';
            
            // Configuración de iconos
            const icons = {
                success: '<i class="fas fa-check-circle"></i>',
                error: '<i class="fas fa-times-circle"></i>',
                warning: '<i class="fas fa-exclamation-triangle"></i>',
                info: '<i class="fas fa-info-circle"></i>'
            };
            
            // Crear modal de confirmación
            const modal = document.createElement('div');
            modal.className = `confirm-modal confirm-${config.type}`;
            modal.innerHTML = `
                <div class="confirm-icon">${icons[config.type] || icons.warning}</div>
                <div class="confirm-title">${config.title}</div>
                <div class="confirm-message">${config.message}</div>
                <div class="confirm-buttons">
                    <button class="btn-cancel">${config.cancelText}</button>
                    <button class="btn-confirm">${config.confirmText}</button>
                </div>
            `;
            
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            
            // Trigger animación
            setTimeout(() => {
                overlay.classList.add('show');
                modal.classList.add('show');
            }, 10);
            
            // Función para cerrar
            function close(result) {
                overlay.classList.remove('show');
                modal.classList.remove('show');
                setTimeout(() => {
                    overlay.remove();
                    resolve(result);
                }, 300);
            }
            
            // Event listeners
            modal.querySelector('.btn-confirm').addEventListener('click', () => close(true));
            modal.querySelector('.btn-cancel').addEventListener('click', () => close(false));
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close(false);
            });
            
            // Escape key
            function handleEscape(e) {
                if (e.key === 'Escape') {
                    close(false);
                    document.removeEventListener('keydown', handleEscape);
                }
            }
            document.addEventListener('keydown', handleEscape);
        });
    };
    
    // Sobrescribir alert nativo (opcional)
    const originalAlert = window.alert;
    window.alert = function(message) {
        // Detectar tipo por contenido
        let type = 'info';
        if (message.includes('✅') || message.toLowerCase().includes('éxito') || message.toLowerCase().includes('correcto')) {
            type = 'success';
        } else if (message.includes('❌') || message.toLowerCase().includes('error')) {
            type = 'error';
        } else if (message.includes('⚠️') || message.toLowerCase().includes('advertencia')) {
            type = 'warning';
        }
        
        // Limpiar emojis del mensaje
        const cleanMessage = message.replace(/[✅❌⚠️🔍❤️]/g, '').trim();
        
        showToast(cleanMessage, type);
    };
    
    console.log('✨ Sistema de notificaciones Toast cargado correctamente');
})();
