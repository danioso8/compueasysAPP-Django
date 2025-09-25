document.addEventListener('DOMContentLoaded', function() {
    const mainImg = document.getElementById('main-product-image');
    const thumbnails = document.querySelectorAll('.thumbnail');

    thumbnails.forEach(function(thumbnail) {
        thumbnail.addEventListener('click', function() {
            // Intercambia src entre la miniatura y la imagen principal
            const tempSrc = mainImg.src;
            mainImg.src = this.src;
            this.src = tempSrc;

            // Opcional: resalta la miniatura seleccionada
            thumbnails.forEach(img => img.classList.remove('selected-thumb'));
            this.classList.add('selected-thumb');
        });
    });
});



