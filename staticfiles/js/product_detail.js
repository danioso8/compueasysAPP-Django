/**
 * Modern Product Detail JavaScript
 * Features: Touch-optimized image gallery, fullscreen viewer, smooth animations
 */

(function() {
    'use strict';

    // Variables globales
    let currentImageIndex = 0;
    let galleryImages = [];
    let touchStartX = 0;
    let touchEndX = 0;
    let isFullscreenOpen = false;

    // Inicialización cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🖼️ Inicializando galería de producto...');
        
        initializeGallery();
        initializeImageSlider();
        initializeFullscreenViewer();
        initializeTouchGestures();
        initializeVariantSelection();
        initializeQuantityControls();
        
        console.log('✅ Galería de producto inicializada');
    });

    /**
     * Inicializar la galería de imágenes
     */
    function initializeGallery() {
        const mainImage = document.getElementById('main-product-image');
        const thumbnails = document.querySelectorAll('.thumbnail');
        
        if (!mainImage || thumbnails.length === 0) {
            console.warn('⚠️ Elementos de galería no encontrados');
            return;
        }

        // Recopilar todas las imágenes
        galleryImages = Array.from(thumbnails).map(thumb => thumb.src);
        
        // Si la imagen principal no está en la galería, agregarla al inicio
        if (!galleryImages.includes(mainImage.src)) {
            galleryImages.unshift(mainImage.src);
        }

        // Configurar thumbnails
        thumbnails.forEach((thumb, index) => {
            thumb.addEventListener('click', function() {
                selectImage(index);
            });

            // Agregar indicador de carga
            thumb.addEventListener('load', function() {
                this.style.opacity = '1';
            });
        });

        // Marcar el primer thumbnail como seleccionado
        if (thumbnails[0]) {
            thumbnails[0].classList.add('selected-thumb');
        }
    }

    /**
     * Inicializar controles del slider
     */
    function initializeImageSlider() {
        const prevBtn = document.getElementById('prev-img');
        const nextBtn = document.getElementById('next-img');

        if (prevBtn) {
            prevBtn.addEventListener('click', function() {
                navigateImage('prev');
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                navigateImage('next');
            });
        }

        // Navegación con teclado
        document.addEventListener('keydown', function(e) {
            if (!isFullscreenOpen) return;

            if (e.key === 'ArrowLeft') {
                navigateImage('prev');
            } else if (e.key === 'ArrowRight') {
                navigateImage('next');
            } else if (e.key === 'Escape') {
                closeFullscreen();
            }
        });
    }

    /**
     * Inicializar visor de pantalla completa
     */
    function initializeFullscreenViewer() {
        const mainImage = document.getElementById('main-product-image');
        
        if (!mainImage) return;

        // Crear overlay de pantalla completa
        const overlay = document.createElement('div');
        overlay.className = 'image-fullscreen-overlay';
        overlay.innerHTML = `
            <div class="fullscreen-image-container">
                <img class="fullscreen-image" src="" alt="Imagen del producto">
                <button class="fullscreen-close" aria-label="Cerrar">&times;</button>
                <button class="fullscreen-prev" aria-label="Imagen anterior">&#8249;</button>
                <button class="fullscreen-next" aria-label="Imagen siguiente">&#8250;</button>
            </div>
        `;
        document.body.appendChild(overlay);

        // Event listeners para el overlay
        const fullscreenImage = overlay.querySelector('.fullscreen-image');
        const closeBtn = overlay.querySelector('.fullscreen-close');
        const prevBtn = overlay.querySelector('.fullscreen-prev');
        const nextBtn = overlay.querySelector('.fullscreen-next');

        // Abrir en pantalla completa al hacer clic en la imagen principal
        mainImage.addEventListener('click', function() {
            openFullscreen(this.src);
        });

        // Cerrar fullscreen
        closeBtn.addEventListener('click', closeFullscreen);
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeFullscreen();
            }
        });

        // Navegación en fullscreen
        prevBtn.addEventListener('click', function() {
            navigateImage('prev');
            updateFullscreenImage();
        });

        nextBtn.addEventListener('click', function() {
            navigateImage('next');
            updateFullscreenImage();
        });
    }

    /**
     * Inicializar gestos táctiles
     */
    function initializeTouchGestures() {
        const imageSlider = document.querySelector('.image-slider');
        const fullscreenOverlay = document.querySelector('.image-fullscreen-overlay');

        if (imageSlider) {
            setupTouchGestures(imageSlider);
        }

        if (fullscreenOverlay) {
            setupTouchGestures(fullscreenOverlay);
        }
    }

    /**
     * Configurar gestos táctiles para un elemento
     */
    function setupTouchGestures(element) {
        element.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        element.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
    }

    /**
     * Manejar gestos de deslizamiento
     */
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Deslizar a la izquierda - siguiente imagen
                navigateImage('next');
            } else {
                // Deslizar a la derecha - imagen anterior
                navigateImage('prev');
            }
            
            if (isFullscreenOpen) {
                updateFullscreenImage();
            }
        }
    }

    /**
     * Seleccionar imagen por índice
     */
    function selectImage(index) {
        if (index < 0 || index >= galleryImages.length) return;

        currentImageIndex = index;
        
        const mainImage = document.getElementById('main-product-image');
        const thumbnails = document.querySelectorAll('.thumbnail');

        if (mainImage) {
            // Agregar efecto de carga
            mainImage.style.opacity = '0.5';
            
            mainImage.src = galleryImages[index];
            
            mainImage.onload = function() {
                this.style.opacity = '1';
            };
        }

        // Actualizar thumbnails seleccionados
        thumbnails.forEach((thumb, i) => {
            thumb.classList.toggle('selected-thumb', i === index);
        });
    }

    /**
     * Navegar a imagen anterior o siguiente
     */
    function navigateImage(direction) {
        const totalImages = galleryImages.length;
        
        if (direction === 'next') {
            currentImageIndex = (currentImageIndex + 1) % totalImages;
        } else {
            currentImageIndex = currentImageIndex === 0 ? totalImages - 1 : currentImageIndex - 1;
        }
        
        selectImage(currentImageIndex);
    }

    /**
     * Abrir imagen en pantalla completa
     */
    function openFullscreen(imageSrc) {
        const overlay = document.querySelector('.image-fullscreen-overlay');
        const fullscreenImage = overlay.querySelector('.fullscreen-image');
        
        if (!overlay || !fullscreenImage) return;

        // Encontrar el índice de la imagen actual
        currentImageIndex = galleryImages.findIndex(img => img === imageSrc);
        if (currentImageIndex === -1) currentImageIndex = 0;

        fullscreenImage.src = imageSrc;
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        isFullscreenOpen = true;
        
        console.log('📱 Fullscreen abierto');
    }

    /**
     * Cerrar pantalla completa
     */
    function closeFullscreen() {
        const overlay = document.querySelector('.image-fullscreen-overlay');
        
        if (!overlay) return;

        overlay.classList.remove('active');
        document.body.style.overflow = '';
        isFullscreenOpen = false;
        
        console.log('📱 Fullscreen cerrado');
    }

    /**
     * Actualizar imagen en fullscreen
     */
    function updateFullscreenImage() {
        const fullscreenImage = document.querySelector('.fullscreen-image');
        
        if (fullscreenImage && galleryImages[currentImageIndex]) {
            fullscreenImage.src = galleryImages[currentImageIndex];
        }
    }

    /**
     * Inicializar selección de variantes con imágenes
     */
    function initializeVariantSelection() {
        const variantOptions = document.querySelectorAll('.variant-option');
        const variantIdInput = document.getElementById('variant_id');
        const mainImage = document.getElementById('main-product-image');
        const mainPrice = document.getElementById('main-product-price');
        const stockIndicator = document.getElementById('available-stock');
        const previewContainer = document.getElementById('selected-variant-preview');
        const previewImage = document.getElementById('variant-preview-image');
        const previewColor = document.getElementById('variant-preview-color');
        const previewStock = document.getElementById('variant-preview-stock');
        const previewPrice = document.getElementById('variant-preview-price');
        
        variantOptions.forEach(variant => {
            variant.addEventListener('click', function() {
                console.log('🎨 Variante clickeada:', this.dataset);
                
                // Remover selección anterior
                variantOptions.forEach(v => v.classList.remove('selected'));
                
                // Seleccionar actual
                this.classList.add('selected');
                
                // Obtener datos de la variante
                const variantId = this.dataset.variantId;
                const variantImage = this.dataset.img;
                const variantColor = this.dataset.color;
                const variantPrice = this.dataset.price;
                const variantStock = this.dataset.stock;
                
                // Actualizar input oculto
                if (variantIdInput) {
                    variantIdInput.value = variantId;
                }
                
                // Actualizar imagen principal si hay imagen de variante
                if (variantImage && mainImage) {
                    console.log('🖼️ Cambiando imagen principal a:', variantImage);
                    
                    // Agregar efecto de carga
                    mainImage.style.opacity = '0.5';
                    
                    mainImage.src = variantImage;
                    
                    // Actualizar también la galería
                    const currentIndex = galleryImages.findIndex(img => img === variantImage);
                    if (currentIndex !== -1) {
                        currentImageIndex = currentIndex;
                        selectImage(currentIndex);
                    } else {
                        // Agregar imagen de variante a la galería si no está
                        galleryImages.unshift(variantImage);
                        currentImageIndex = 0;
                    }
                    
                    mainImage.onload = function() {
                        this.style.opacity = '1';
                    };
                }
                
                // Actualizar precio si está disponible
                if (variantPrice && mainPrice) {
                    const formatter = new Intl.NumberFormat('es-CO');
                    mainPrice.textContent = `$${formatter.format(variantPrice)} COP`;
                    
                    // Animación de precio
                    mainPrice.style.transform = 'scale(1.1)';
                    setTimeout(() => {
                        mainPrice.style.transform = 'scale(1)';
                    }, 200);
                }
                
                // Actualizar stock
                if (variantStock && stockIndicator) {
                    stockIndicator.textContent = `${variantStock} disponibles`;
                    
                    // Cambiar color según stock
                    const stockNum = parseInt(variantStock);
                    if (stockNum <= 0) {
                        stockIndicator.style.background = '#dc3545';
                        stockIndicator.textContent = 'Agotado';
                    } else if (stockNum <= 5) {
                        stockIndicator.style.background = '#ffc107';
                        stockIndicator.style.color = '#000';
                    } else {
                        stockIndicator.style.background = '#17a2b8';
                        stockIndicator.style.color = '#fff';
                    }
                }
                
                // Mostrar preview de variante seleccionada
                if (previewContainer) {
                    if (variantImage && previewImage) {
                        previewImage.src = variantImage;
                        previewImage.style.display = 'block';
                    } else {
                        previewImage.style.display = 'none';
                    }
                    
                    if (previewColor) {
                        previewColor.textContent = `Color: ${variantColor || 'No especificado'}`;
                    }
                    
                    if (previewStock) {
                        previewStock.textContent = `Stock: ${variantStock || '0'} unidades`;
                    }
                    
                    if (previewPrice && variantPrice) {
                        const formatter = new Intl.NumberFormat('es-CO');
                        previewPrice.textContent = `$${formatter.format(variantPrice)} COP`;
                    }
                    
                    previewContainer.style.display = 'block';
                }
                
                // Agregar efecto de pulso
                this.style.animation = 'pulse 0.3s ease-out';
                setTimeout(() => {
                    this.style.animation = '';
                }, 300);
                
                console.log('✅ Variante seleccionada correctamente');
            });
            
            // Efecto hover mejorado
            variant.addEventListener('mouseenter', function() {
                if (!this.classList.contains('selected')) {
                    this.style.transform = 'translateY(-2px) scale(1.02)';
                }
            });
            
            variant.addEventListener('mouseleave', function() {
                if (!this.classList.contains('selected')) {
                    this.style.transform = 'none';
                }
            });
        });
        
        // Auto-seleccionar primera variante si existe
        if (variantOptions.length > 0 && !document.querySelector('.variant-option.selected')) {
            setTimeout(() => {
                variantOptions[0].click();
            }, 500);
        }
    }

    /**
     * Inicializar controles de cantidad
     */
    function initializeQuantityControls() {
        const quantityInput = document.querySelector('.quantity-input');
        const increaseBtn = document.querySelector('.quantity-increase');
        const decreaseBtn = document.querySelector('.quantity-decrease');
        
        if (!quantityInput) return;

        // Botón de incrementar
        if (increaseBtn) {
            increaseBtn.addEventListener('click', function() {
                const currentValue = parseInt(quantityInput.value) || 1;
                const maxValue = parseInt(quantityInput.max) || 999;
                
                if (currentValue < maxValue) {
                    quantityInput.value = currentValue + 1;
                    animateButton(this);
                }
            });
        }

        // Botón de decrementar
        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', function() {
                const currentValue = parseInt(quantityInput.value) || 1;
                const minValue = parseInt(quantityInput.min) || 1;
                
                if (currentValue > minValue) {
                    quantityInput.value = currentValue - 1;
                    animateButton(this);
                }
            });
        }

        // Validar entrada manual
        quantityInput.addEventListener('input', function() {
            const value = parseInt(this.value);
            const min = parseInt(this.min) || 1;
            const max = parseInt(this.max) || 999;
            
            if (isNaN(value) || value < min) {
                this.value = min;
            } else if (value > max) {
                this.value = max;
            }
        });
    }

    /**
     * Animar botón al hacer clic
     */
    function animateButton(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 100);
    }

    /**
     * Agregar animación de pulso
     */
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .fullscreen-prev, .fullscreen-next {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 2rem;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 10;
        }
        
        .fullscreen-prev {
            left: 20px;
        }
        
        .fullscreen-next {
            right: 20px;
        }
        
        .fullscreen-prev:hover,
        .fullscreen-next:hover {
            background: white;
            transform: translateY(-50%) scale(1.1);
        }
    `;
    document.head.appendChild(style);

    // Prevenir doble envío del formulario de compra
    const purchaseForm = document.querySelector('.purchase-form');
    if (purchaseForm) {
        let isSubmitting = false;
        
        purchaseForm.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                console.log('⚠️ Prevented double form submission');
                return false;
            }
            
            isSubmitting = true;
            console.log('📦 Form submitted, preventing duplicate submissions...');
            
            // Deshabilitar botones temporalmente
            const submitButtons = this.querySelectorAll('button[type="submit"]');
            submitButtons.forEach(button => {
                button.disabled = true;
                button.style.opacity = '0.6';
            });
            
            // Reactivar después de 3 segundos (por si hay error)
            setTimeout(() => {
                isSubmitting = false;
                submitButtons.forEach(button => {
                    button.disabled = false;
                    button.style.opacity = '1';
                });
                console.log('✅ Form submission lock released');
            }, 3000);
        });
        
        console.log('🛡️ Double submission prevention enabled');
    }

})();