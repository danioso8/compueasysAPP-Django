const departamentosCiudades = {{ departamentos|safe }};
const depSelect = document.getElementById('departament');
const ciudadSelect = document.getElementById('ciudad');
const ciudadSeleccionada = "{{ city_selected|escapejs }}";

function actualizarCiudades() {
    const dep = depSelect.value;
    ciudadSelect.innerHTML = '<option value="">Seleccione una ciudad</option>';
    if (departamentosCiudades[dep]) {
        departamentosCiudades[dep].forEach(function(ciudad) {
            const selected = ciudad === ciudadSeleccionada ? 'selected' : '';
            ciudadSelect.innerHTML += `<option value="${ciudad}" ${selected}>${ciudad}</option>`;
        });
    }
}

// Inicializa ciudades si ya hay un departamento seleccionado
if(depSelect.value) {
    actualizarCiudades();
}

depSelect.addEventListener('change', function() {
    actualizarCiudades();
});