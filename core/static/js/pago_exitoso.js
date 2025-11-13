/**
 * Pago Exitoso - JavaScript Interactivo
 * Funcionalidades: Confetti, animaciones, efectos y interacciones
 */

(function() {
    'use strict';
    
    // Configuración global
    const CONFIG = {
        confetti: {
            particleCount: 150,
            duration: 3000,
            colors: ['#28a745', '#20c997', '#ffc107', '#17a2b8', '#6f42c1']
        },
        animation: {
            duration: 800,
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
        }
    };
    
    // Variables globales
    let confettiAnimationId = null;
    let confettiParticles = [];
    let canvas = null;
    let ctx = null;
    
    /**
     * Inicialización cuando el DOM está listo
     */
    function initializeApp() {
        try {
            setupConfetti();
            setupAnimations();
            setupInteractions();
            startConfettiShow();
            setupOrderTracking();
            setupAnalytics();
            
            console.log('🎉 Pago exitoso: Aplicación inicializada');
        } catch (error) {
            console.error('Error inicializando la aplicación:', error);
            // Continuar con funcionalidades básicas
            setupBasicInteractions();
        }
    }
    
    /**
     * Configuración básica de interacciones como fallback
     */
    function setupBasicInteractions() {
        const whatsappBtn = document.getElementById('whatsapp-btn');
        if (whatsappBtn) {
            whatsappBtn.addEventListener('click', function() {
                console.log('WhatsApp button clicked');
            });
        }
    }
    
    /**
     * Configuración del canvas de confetti
     */
    function setupConfetti() {
        try {
            canvas = document.getElementById('confetti-canvas');
            if (!canvas) {
                console.log('Canvas de confetti no encontrado, continuando sin efectos');
                return;
            }
            
            ctx = canvas.getContext('2d');
            if (!ctx) {
                console.log('Contexto 2D no disponible, deshabilitando confetti');
                return;
            }
            
            resizeCanvas();
            
            // Redimensionar canvas cuando cambie la ventana
            window.addEventListener('resize', debounce(resizeCanvas, 100));
        } catch (error) {
            console.error('Error configurando confetti:', error);
        }
    }
    
    /**
     * Redimensionar canvas
     */
    function resizeCanvas() {
        if (!canvas || !ctx) return;
        
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    /**
     * Clase Partícula de Confetti
     */
    class ConfettiParticle {
        constructor() {
            this.reset();
            this.y = Math.random() * canvas.height - canvas.height;
        }
        
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = -10;
            this.vx = (Math.random() - 0.5) * 4;
            this.vy = Math.random() * 3 + 2;
            this.rotation = Math.random() * 360;
            this.rotationSpeed = (Math.random() - 0.5) * 10;
            this.size = Math.random() * 8 + 4;
            this.color = CONFIG.confetti.colors[Math.floor(Math.random() * CONFIG.confetti.colors.length)];
            this.shape = Math.random() < 0.5 ? 'circle' : 'square';
            this.opacity = 1;
            this.gravity = 0.1;
            this.wind = Math.random() * 0.5 - 0.25;
        }
        
        update() {
            this.x += this.vx + this.wind;
            this.y += this.vy;
            this.vy += this.gravity;
            this.rotation += this.rotationSpeed;
            
            // Reset particle if it goes off screen (mantener opacidad constante)
            if (this.y > canvas.height + 10) {
                this.reset();
            }
            
            // Wrap around horizontally
            if (this.x < -10) this.x = canvas.width + 10;
            if (this.x > canvas.width + 10) this.x = -10;
        }
        
        draw() {
            ctx.save();
            ctx.globalAlpha = 1; // Siempre opacidad completa para mantener confetti visible
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation * Math.PI / 180);
            
            ctx.fillStyle = this.color;
            
            if (this.shape === 'circle') {
                ctx.beginPath();
                ctx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
                ctx.fill();
            } else {
                ctx.fillRect(-this.size / 2, -this.size / 2, this.size, this.size);
            }
            
            ctx.restore();
        }
    }
    
    /**
     * Iniciar show de confetti
     */
    function startConfettiShow() {
        if (!canvas || !ctx) return;
        
        // Crear partículas
        confettiParticles = [];
        for (let i = 0; i < CONFIG.confetti.particleCount; i++) {
            confettiParticles.push(new ConfettiParticle());
        }
        
        // Iniciar animación
        animateConfetti();
        
        // Mantener confetti visible permanentemente
        console.log('🎉 Confetti iniciado - permanecerá visible');
    }
    
    /**
     * Animar confetti
     */
    function animateConfetti() {
        if (!canvas || !ctx) return;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        confettiParticles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        confettiAnimationId = requestAnimationFrame(animateConfetti);
    }
    
    /**
     * Detener confetti (función mantenida para compatibilidad, pero no hace fade out)
     */
    function stopConfetti() {
        // Ya no detenemos el confetti para mantenerlo visible permanentemente
        console.log('🎉 stopConfetti llamado, pero el confetti permanecerá visible');
        
        // Comentado: ya no cancelamos la animación para mantener confetti visible
        // if (confettiAnimationId) {
        //     cancelAnimationFrame(confettiAnimationId);
        //     confettiAnimationId = null;
        // }
        
        // Comentado: eliminamos todo el fade out para mantener confetti
        // const fadeOut = () => { ... };
    }
    
    /**
     * Configurar animaciones AOS
     */
    function setupAnimations() {
        // Inicializar AOS si está disponible
        if (typeof AOS !== 'undefined') {
            AOS.init({
                duration: CONFIG.animation.duration,
                easing: CONFIG.animation.easing,
                once: true,
                offset: 100,
                delay: 100
            });
        }
        
        // Animaciones personalizadas
        animateCounters();
        animateSuccessIcon();
    }
    
    /**
     * Animar contadores (si hay)
     */
    function animateCounters() {
        const counters = document.querySelectorAll('[data-count]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const target = parseInt(counter.getAttribute('data-count'));
                    animateNumber(counter, target);
                    observer.unobserve(counter);
                }
            });
        });
        
        counters.forEach(counter => observer.observe(counter));
    }
    
    /**
     * Animar número
     */
    function animateNumber(element, target) {
        const duration = 2000;
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const updateNumber = () => {
            current += increment;
            if (current < target) {
                element.textContent = Math.floor(current);
                requestAnimationFrame(updateNumber);
            } else {
                element.textContent = target;
            }
        };
        
        updateNumber();
    }
    
    /**
     * Animar icono de éxito
     */
    function animateSuccessIcon() {
        const successIcon = document.querySelector('.success-icon');
        if (!successIcon) return;
        
        // Agregar clase de animación después de un retraso
        setTimeout(() => {
            successIcon.classList.add('animate-success');
        }, 500);
    }
    
    /**
     * Configurar interacciones
     */
    function setupInteractions() {
        setupButtonEffects();
        setupWhatsAppButton();
        setupStepCards();
        setupKeyboardNavigation();
    }
    
    /**
     * Efectos de botones
     */
    function setupButtonEffects() {
        const buttons = document.querySelectorAll('.btn-whatsapp, .btn-secondary-custom, .btn-outline-custom');
        
        buttons.forEach(button => {
            // Efecto ripple
            button.addEventListener('click', createRippleEffect);
            
            // Loading state
            button.addEventListener('click', function(e) {
                if (this.classList.contains('btn-loading')) {
                    e.preventDefault();
                    return;
                }
                
                // Simular loading para algunos botones
                if (this.classList.contains('btn-whatsapp')) {
                    showButtonLoading(this, 1000);
                }
            });
        });
    }
    
    /**
     * Crear efecto ripple
     */
    function createRippleEffect(e) {
        const button = e.currentTarget;
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple 600ms linear;
            left: ${x}px;
            top: ${y}px;
            width: 20px;
            height: 20px;
            margin-left: -10px;
            margin-top: -10px;
            pointer-events: none;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
    
    /**
     * Mostrar loading en botón
     */
    function showButtonLoading(button, duration = 2000) {
        const originalText = button.innerHTML;
        button.classList.add('btn-loading');
        button.innerHTML = 'Abriendo WhatsApp...';
        
        setTimeout(() => {
            button.classList.remove('btn-loading');
            button.innerHTML = originalText;
        }, duration);
    }
    
    /**
     * Configurar botón de WhatsApp
     */
    function setupWhatsAppButton() {
        const whatsappBtn = document.getElementById('whatsapp-btn');
        if (!whatsappBtn) return;
        
        whatsappBtn.addEventListener('click', function(e) {
            // Analytics
            trackEvent('whatsapp_click', {
                source: 'success_page',
                timestamp: Date.now()
            });
            
            // Feedback visual
            showToast('Abriendo WhatsApp...', 'info');
        });
    }
    
    /**
     * Configurar tarjetas de pasos
     */
    function setupStepCards() {
        const stepCards = document.querySelectorAll('.step-card');
        
        stepCards.forEach((card, index) => {
            // Animación de entrada escalonada
            card.style.animationDelay = `${index * 100}ms`;
            
            // Hover effects mejorados
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-10px) rotateY(5deg)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) rotateY(0)';
            });
        });
    }
    
    /**
     * Configurar navegación por teclado
     */
    function setupKeyboardNavigation() {
        document.addEventListener('keydown', function(e) {
            // Esc para cerrar modales o efectos
            if (e.key === 'Escape') {
                closeAllModals();
            }
            
            // Enter o Space en botones focusados
            if (e.key === 'Enter' || e.key === ' ') {
                const focused = document.activeElement;
                if (focused && focused.classList.contains('btn')) {
                    focused.click();
                }
            }
        });
    }
    
    /**
     * Configurar seguimiento de pedido
     */
    function setupOrderTracking() {
        // Simular actualizaciones de estado del pedido
        const statusElements = document.querySelectorAll('.status-confirmed');
        
        statusElements.forEach(element => {
            // Animación de check
            const checkIcon = element.querySelector('i');
            if (checkIcon) {
                setTimeout(() => {
                    checkIcon.style.transform = 'scale(1.2)';
                    setTimeout(() => {
                        checkIcon.style.transform = 'scale(1)';
                    }, 200);
                }, 1000);
            }
        });
    }
    
    /**
     * Configurar analytics
     */
    function setupAnalytics() {
        // Track page view
        trackEvent('success_page_view', {
            timestamp: Date.now(),
            user_agent: navigator.userAgent,
            referrer: document.referrer
        });
        
        // Track time on page
        const startTime = Date.now();
        window.addEventListener('beforeunload', () => {
            const timeOnPage = Date.now() - startTime;
            trackEvent('success_page_time', { duration: timeOnPage });
        });
    }
    
    /**
     * Utilidades
     */
    
    /**
     * Debounce function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Mostrar toast notification
     */
    function showToast(message, type = 'info') {
        // Crear elemento toast si no existe
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1100';
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Inicializar y mostrar toast
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            // Remover elemento después de que se oculte
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        } else {
            // Fallback sin Bootstrap
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
    }
    
    /**
     * Track events (placeholder para analytics)
     */
    function trackEvent(eventName, properties = {}) {
        console.log(`📊 Analytics: ${eventName}`, properties);
        
        // Aquí podrías integrar con Google Analytics, Mixpanel, etc.
        // gtag('event', eventName, properties);
        // mixpanel.track(eventName, properties);
    }
    
    /**
     * Cerrar todos los modales
     */
    function closeAllModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
    
    /**
     * CSS dinámico para animaciones
     */
    function injectCSS() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
            
            .animate-success {
                animation: successBounce 0.6s ease-out;
            }
            
            @keyframes successBounce {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * Verificar compatibilidad del navegador
     */
    function checkBrowserSupport() {
        const features = {
            canvas: !!document.createElement('canvas').getContext,
            requestAnimationFrame: !!window.requestAnimationFrame,
            intersectionObserver: !!window.IntersectionObserver
        };
        
        if (!features.canvas) {
            console.warn('Canvas no soportado, deshabilitando confetti');
        }
        
        if (!features.requestAnimationFrame) {
            console.warn('RequestAnimationFrame no soportado');
        }
        
        return features;
    }
    
    // Inicialización
    document.addEventListener('DOMContentLoaded', function() {
        // Verificar soporte del navegador
        const browserSupport = checkBrowserSupport();
        
        // Inyectar CSS
        injectCSS();
        
        // Inicializar aplicación
        initializeApp();
        
        // Log de inicialización
        console.log('🎉 Pago Exitoso JS cargado exitosamente', {
            browserSupport,
            timestamp: new Date().toISOString()
        });
    });
    
    // Manejo de errores globales
    window.addEventListener('error', function(e) {
        console.error('Error en pago_exitoso.js:', e.error);
        trackEvent('js_error', {
            message: e.message,
            filename: e.filename,
            lineno: e.lineno
        });
    });
    
})();