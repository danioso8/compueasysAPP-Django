/* ========================================
   DASHBOARD AUTO-REFRESH SYSTEM
   Sistema de actualización automática cada 15 segundos
   ======================================== */

(function() {
    'use strict';

    const REFRESH_INTERVAL = 15000; // 15 segundos
    let refreshTimer = null;
    let lastPedidosCount = null;

    // Utilidades
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

    // Función para actualizar la lista de pedidos
    async function refreshPedidosList() {
        try {
            // Obtener filtros actuales
            const estadoFilter = document.getElementById('estadoFilter')?.value || '';
            const pagoFilter = document.getElementById('pagoFilter')?.value || '';
            const searchInput = document.getElementById('searchPedido')?.value || '';

            // Construir URL con filtros
            const url = new URL('/dashboard/api/pedidos-list/', window.location.origin);
            if (estadoFilter) url.searchParams.set('estado', estadoFilter);
            if (pagoFilter) url.searchParams.set('pago', pagoFilter);
            if (searchInput) url.searchParams.set('search', searchInput);

            const response = await fetch(url);
            if (!response.ok) throw new Error('Error al obtener pedidos');

            const data = await response.json();
            
            // Actualizar tabla
            const tbody = document.getElementById('pedidosTableBody');
            if (tbody && data.html) {
                tbody.innerHTML = data.html;
                console.log('✅ Pedidos actualizados automáticamente');
            }
        } catch (error) {
            console.error('❌ Error al refrescar pedidos:', error);
        }
    }

    // Función para verificar cambios en pedidos
    async function checkPedidosChanges() {
        try {
            const response = await fetch('/dashboard/api/pedidos-count/');
            if (!response.ok) throw new Error('Error al verificar cambios');

            const data = await response.json();
            
            if (lastPedidosCount !== null && data.count !== lastPedidosCount) {
                // Hubo cambios - actualizar lista
                await refreshPedidosList();
            }
            
            lastPedidosCount = data.count;
        } catch (error) {
            console.error('❌ Error al verificar cambios:', error);
        }
    }

    // Función para actualizar estadísticas del dashboard
    async function updateDashboardStats() {
        console.log('🔄 Solicitando estadísticas del dashboard...');
        try {
            const response = await fetch('/dashboard/api/dashboard-stats/');
            if (!response.ok) {
                console.error('❌ Response no OK:', response.status, response.statusText);
                throw new Error('Error al obtener estadísticas');
            }

            const data = await response.json();
            console.log('✅ Datos recibidos:', data);
            
            if (data.success && data.stats) {
                updateStatsUI(data.stats);
            } else {
                console.error('❌ Respuesta sin success o stats:', data);
            }
        } catch (error) {
            console.error('❌ Error al actualizar estadísticas:', error);
        }
    }

    // Actualizar valores en la UI con animación
    function updateStatsUI(stats) {
        console.log('📊 Actualizando UI con stats:', stats);
        
        // Estadísticas diarias
        if (stats.diarias) {
            console.log('  📅 Diarias:', stats.diarias);
            updateValue('pedidos-hoy', stats.diarias.pedidos_hoy);
            updateValue('ventas-hoy', '$' + formatNumber(stats.diarias.ventas_hoy));
            updateValue('productos-vendidos-hoy', stats.diarias.productos_vendidos_hoy);
            updateValue('ingresos-pendientes-hoy', '$' + formatNumber(stats.diarias.ingresos_pendientes_hoy || 0));
            updateValue('nuevos-clientes-hoy', stats.diarias.nuevos_clientes_hoy || 0);
        }

        // Estadísticas de pedidos
        if (stats.pedidos) {
            updateValue('total-pedidos', stats.pedidos.total);
            updateValue('pedidos-pendientes', stats.pedidos.pendientes);
            updateValue('pedidos-completados', stats.pedidos.completados);
        }

        // Estadísticas de finanzas
        if (stats.finanzas) {
            updateValue('ingresos-totales', '$' + formatNumber(stats.finanzas.ingresos_totales));
            updateValue('ingresos-pendientes', '$' + formatNumber(stats.finanzas.ingresos_pendientes));
        }

        // Estadísticas de productos
        if (stats.productos) {
            updateValue('total-productos', stats.productos.total);
            updateValue('productos-sin-stock', stats.productos.sin_stock);
            updateValue('productos-bajo-stock', stats.productos.bajo_stock);
        }

        // Estadísticas de usuarios
        if (stats.usuarios) {
            updateValue('total-usuarios', stats.usuarios.total);
        }

        if (stats.productos) {
            updateValue('total-productos', stats.productos.total);
        }

        if (stats.usuarios) {
            updateValue('total-usuarios', stats.usuarios.total);
        }

        console.log('📊 Estadísticas actualizadas:', new Date().toLocaleTimeString());
    }

    // Actualizar un valor individual con animación
    function updateValue(statName, newValue) {
        const element = document.querySelector(`[data-stat="${statName}"]`);
        if (!element) {
            // No mostrar advertencia - el elemento simplemente no está en la página actual
            return;
        }

        const oldValue = element.textContent.trim();
        const newValueStr = String(newValue);

        // Solo logear si el valor cambió realmente
        if (oldValue !== newValueStr) {
            console.log(`🔄 Actualizando ${statName}: "${oldValue}" → "${newValueStr}"`);
            
            // Animar cambio
            element.classList.add('stat-updated');
            element.textContent = newValueStr;

            setTimeout(() => {
                element.classList.remove('stat-updated');
            }, 600);
        }
    }

    // Mostrar notificación flotante
    function showRealtimeNotification(title, message, type = 'info') {
        // Remover notificaciones anteriores
        const existing = document.querySelectorAll('.realtime-notification');
        existing.forEach(n => n.remove());

        const colors = {
            success: 'bg-success',
            info: 'bg-info',
            warning: 'bg-warning',
            danger: 'bg-danger'
        };

        const notification = document.createElement('div');
        notification.className = `realtime-notification alert ${colors[type] || colors.info} alert-dismissible fade show`;
        notification.innerHTML = `
            <strong><i class="fas fa-sync-alt me-2"></i>${title}</strong>
            <div>${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remover después de 4 segundos
        setTimeout(() => {
            notification.classList.add('hide');
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    // Formatear números
    function formatNumber(num) {
        return Number(num).toLocaleString('es-CO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    // Iniciar auto-refresh para pedidos
    function startPedidosAutoRefresh() {
        // Primera carga
        checkPedidosChanges();

        // Configurar intervalo
        refreshTimer = setInterval(checkPedidosChanges, REFRESH_INTERVAL);
        console.log('✅ Auto-refresh de pedidos iniciado (15s)');
    }

    // Iniciar auto-refresh para dashboard home
    function startDashboardAutoRefresh() {
        // Primera carga
        updateDashboardStats();

        // Configurar intervalo
        refreshTimer = setInterval(updateDashboardStats, REFRESH_INTERVAL);
        console.log('✅ Auto-refresh de dashboard iniciado (15s)');
    }

    // Detener auto-refresh
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
            console.log('⏹️ Auto-refresh detenido');
        }
    }

    // Inicializar según la vista actual
    function init() {
        const urlParams = new URLSearchParams(window.location.search);
        const currentView = urlParams.get('view');

        if (currentView === 'pedidos') {
            startPedidosAutoRefresh();
        } else if (!currentView || currentView === '') {
            // Vista home del dashboard
            startDashboardAutoRefresh();
        }

        // Detener al cambiar de página
        window.addEventListener('beforeunload', stopAutoRefresh);
    }

    // Exportar funciones globales
    window.DashboardAutoRefresh = {
        start: startPedidosAutoRefresh,
        startDashboard: startDashboardAutoRefresh,
        stop: stopAutoRefresh,
        refresh: checkPedidosChanges,
        refreshStats: updateDashboardStats
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
