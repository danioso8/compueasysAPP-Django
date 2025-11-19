// ==========================================
// DASHBOARD CONTABLE - JAVASCRIPT
// ==========================================

(function() {
    'use strict';

    // Esperar a que el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        initCharts();
        initEventListeners();
    });

    // ==========================================
    // INICIALIZAR GRÁFICOS
    // ==========================================
    function initCharts() {
        // Gráfico de Ventas vs Compras
        const salesCtx = document.getElementById('salesChart');
        if (salesCtx) {
            new Chart(salesCtx, {
                type: 'line',
                data: {
                    labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio'],
                    datasets: [
                        {
                            label: 'Ventas',
                            data: [0, 0, 0, 0, 0, 0],
                            borderColor: 'rgb(37, 99, 235)',
                            backgroundColor: 'rgba(37, 99, 235, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Compras',
                            data: [0, 0, 0, 0, 0, 0],
                            borderColor: 'rgb(239, 68, 68)',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }

        // Gráfico de Distribución de Gastos
        const expensesCtx = document.getElementById('expensesChart');
        if (expensesCtx) {
            new Chart(expensesCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Nómina', 'Servicios', 'Compras', 'Otros'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            'rgb(37, 99, 235)',
                            'rgb(16, 185, 129)',
                            'rgb(245, 158, 11)',
                            'rgb(107, 114, 128)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });
        }
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================
    function initEventListeners() {
        // Cambio de empresa
        const companySwitchers = document.querySelectorAll('[href^="?switch_company"]');
        companySwitchers.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const companyId = this.getAttribute('href').split('=')[1];
                switchCompany(companyId);
            });
        });

        // Sidebar mobile toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.querySelector('.sidebar');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('show');
            });
        }

        // Cerrar sidebar al hacer clic fuera (móvil)
        document.addEventListener('click', function(e) {
            const sidebar = document.querySelector('.sidebar');
            const sidebarToggle = document.getElementById('sidebarToggle');
            
            if (window.innerWidth <= 992 && sidebar && sidebar.classList.contains('show')) {
                if (!sidebar.contains(e.target) && e.target !== sidebarToggle) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }

    // ==========================================
    // FUNCIONES AUXILIARES
    // ==========================================

    /**
     * Cambiar de empresa
     */
    function switchCompany(companyId) {
        fetch('/contable/api/switch-company/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ company_id: companyId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                showNotification('Error al cambiar de empresa', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error de conexión', 'error');
        });
    }

    /**
     * Mostrar notificación
     */
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 70px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    /**
     * Obtener cookie CSRF
     */
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

    /**
     * Formatear números como moneda
     */
    function formatCurrency(amount) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(amount);
    }

    /**
     * Formatear fechas
     */
    function formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('es-CO', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(date);
    }

    // Exponer funciones globalmente si es necesario
    window.dashboardContable = {
        showNotification,
        formatCurrency,
        formatDate
    };

})();
