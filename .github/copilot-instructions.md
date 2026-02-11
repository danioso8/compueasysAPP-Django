# GitHub Copilot Instructions for CompuEasys App

## Project Overview

**CompuEasys App** es una aplicación web de e-commerce desarrollada en Django 4.2.24 con Python 3.13.5, diseñada para gestión de inventario, ventas y administración de productos tecnológicos. La aplicación utiliza arquitectura MTV (Model-Template-View) de Django con un frontend responsivo basado en Bootstrap.

## Arquitectura del Proyecto

### Estructura de Apps Django
```
AppCompueasys/        # Configuración principal del proyecto
├── core/            # App principal: e-commerce público
├── contable/        # App de contabilidad/productos
├── dashboard/       # App de administración (backend)
└── media_files/     # Archivos estáticos subidos
```

### Tecnologías Stack
- **Backend**: Django 4.2.24, Python 3.13.5
- **Frontend**: Bootstrap 5.3.8, JavaScript ES6+, SweetAlert2
- **Base de Datos**: PostgreSQL (producción), SQLite (desarrollo)
- **Deployment**: Render.com con WhiteNoise para archivos estáticos
- **Authentication**: Django auth personalizado con decoradores custom

### Modelos Principales (`core/models.py`)
```python
# Productos principales con variantes
ProductStore          # Productos base con precio, stock, categoría
ProductVariant        # Variantes de productos (colores, tallas)
Category             # Categorías de productos
Type                 # Tipos de productos
proveedor            # Proveedores
Galeria              # Imágenes adicionales de productos
SimpleUser           # Usuarios del e-commerce
Pedido              # Órdenes de compra
```

## Patrones de Desarrollo Específicos

### 1. Decoradores de Autenticación
```python
# Usar SIEMPRE este patrón para vistas de dashboard
@superuser_required
def dashboard_view(request):
    # Lógica de vista
    pass

# Definición del decorador personalizado
def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('superuser_id'):
            return view_func(request, *args, **kwargs)
        return redirect('/login_user/?next=' + request.path)
    return _wrapped_view
```

### 2. Manejo de Vistas con Múltiples Views
```python
def dashboard_home(request):
    # SIEMPRE inicializar todas las variables al principio
    Pedidos = []
    categorias = []
    productos = []
    usuarios = []
    
    # Obtener view desde GET parameter
    view_param = request.GET.get('view', 'usuarios')
    
    # Procesar POST data
    if request.method == 'POST':
        # Lógica POST
        pass
    
    # Preparar datos específicos según view_param
    if view_param == 'usuarios':
        # Lógica usuarios
    elif view_param == 'productos':
        # Lógica productos
    
    return render(request, 'dashboard/dashboard_home.html', {
        'view': view_param,
        'usuarios': usuarios,
        'productos': productos,
        # ... otros datos
    })
```

### 3. Frontend JavaScript Patterns
```javascript
// Estructura principal en dashboard.js
(function () {
  "use strict";
  
  // Utilities SIEMPRE al principio
  function getCookie(name) { /* ... */ }
  function safeEl(id) { /* ... */ }
  
  // Event Listeners
  function setupEventListeners() {
    // Usar event delegation para elementos dinámicos
    document.addEventListener('click', function(e) {
      if (e.target.matches('.edit-product-btn')) {
        // Lógica edición
      }
    });
  }
  
  // CSRF token en todas las peticiones AJAX
  function makeAjaxRequest(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(data)
    });
  }
})();
```

### 4. Template Patterns
```html
<!-- SIEMPRE cargar static al principio -->
{% load static %}

<!-- Responsive design con Bootstrap -->
<div class="container-fluid">
  <div class="row">
    <!-- Sidebar fijo -->
    <aside class="col-lg-3 col-md-4 sidebar-fixed">
      <!-- Navegación -->
    </aside>
    
    <!-- Contenido principal responsive -->
    <main class="col-lg-9 col-md-8 main-content">
      <!-- Contenido dinámico según view parameter -->
      {% if view == 'productos' %}
        <!-- Vista productos -->
      {% elif view == 'usuarios' %}
        <!-- Vista usuarios -->
      {% endif %}
    </main>
  </div>
</div>
```

### 5. Configuración Settings.py
```python
# Configuración dual para desarrollo/producción
if os.getenv('DJANGO_DEVELOPMENT') == 'True':
    # Configuración desarrollo (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Configuración producción (PostgreSQL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            # Variables de entorno para producción
        }
    }
```

## Debugging y Desarrollo

### 1. Debugging Console Logs
```javascript
// Patrón para debugging en dashboard.js
console.group('🔧 Dashboard Debug');
console.log('Action:', action);
console.log('Data:', data);
console.log('Element:', element);
console.groupEnd();
```

### 2. Error Handling en Views
```python
try:
    # Operación que puede fallar
    product.save()
    messages.success(request, 'Producto guardado exitosamente')
except Exception as e:
    messages.error(request, f'Error al guardar: {str(e)}')
    # Log del error para debugging
    print(f"Error in dashboard_home: {e}")
```

### 3. Responsive CSS Patterns
```css
/* Mobile-first approach */
.dashboard-container {
  padding: 1rem;
}

/* Tablet breakpoint */
@media (min-width: 768px) {
  .dashboard-container {
    padding: 2rem;
  }
}

/* Desktop breakpoint */
@media (min-width: 992px) {
  .sidebar {
    position: fixed;
    height: 100vh;
  }
}
```

## Reglas de Codificación

### 1. Nombres de Variables
- **Python**: snake_case (`product_store`, `user_list`)
- **JavaScript**: camelCase (`productForm`, `galleryImages`)
- **CSS**: kebab-case (`product-card`, `sidebar-fixed`)
- **Templates**: Django naming (`{{ product.name }}`, `{% url 'product_detail' %}`)

### 2. Estructura de Archivos
```
app_name/
├── models.py          # Modelos de datos
├── views.py           # Lógica de vistas (función-based views)
├── urls.py            # Configuración de URLs
├── static/
│   ├── css/          # Estilos específicos del app
│   ├── js/           # JavaScript específico
│   └── img/          # Imágenes del app
└── templates/
    └── app_name/     # Templates con namespace
```

### 3. Manejo de Formularios
```python
# En views.py - patrón para formularios complejos
if request.method == 'POST':
    # Extraer datos del form
    nombre = request.POST.get('nombre', '')
    precio = request.POST.get('precio', 0)
    
    # Validación
    if not nombre:
        messages.error(request, 'El nombre es requerido')
        return render(request, template, context)
    
    # Crear/Actualizar objeto
    product = ProductStore.objects.create(
        name=nombre,
        price=precio,
        # ... otros campos
    )
```

### 4. AJAX y CSRF
```javascript
// SIEMPRE incluir CSRF token en requests AJAX
const csrftoken = getCookie('csrftoken');

fetch('/dashboard/endpoint/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrftoken
  },
  body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    showToast('Operación exitosa', 'success');
  } else {
    showToast('Error: ' + data.message, 'error');
  }
});
```

## Deployment y Producción

### 1. Variables de Entorno (.env)
```env
SECRET_KEY=your-secret-key
DJANGO_DEVELOPMENT=False
DB_NAME=database_name
DB_USERNAME=db_user
DB_PASSWORD=db_password
DB_HOST=db_host
DB_PORT=5432
RENDER_EXTERNAL_HOSTNAME=your-app.onrender.com
```

### 2. Archivos Estáticos
```python
# settings.py para producción
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files con posible migración a S3
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')
```

## Convenciones Específicas del Proyecto

### 1. Navegación Dashboard
- Usar parámetro GET `view` para cambiar secciones: `?view=productos`
- Sidebar con enlaces directos a diferentes vistas
- Breadcrumbs para navegación contextual

### 2. Manejo de Imágenes
```python
# Modelos con ImageField
imagen = models.ImageField(upload_to='images/', blank=True, null=True)

# En templates para mostrar imágenes
{% if producto.imagen %}
  <img src="{{ producto.imagen.url }}" alt="{{ producto.name }}">
{% else %}
  <img src="{% static 'img/no-image.png' %}" alt="No image">
{% endif %}
```

### 3. Mensajes de Usuario
```python
# En views.py
from django.contrib import messages

messages.success(request, 'Operación completada exitosamente')
messages.error(request, 'Error en la operación')
messages.warning(request, 'Advertencia importante')
messages.info(request, 'Información relevante')
```

### 4. Filtros y Búsquedas
```python
# Patrón para filtros en dashboard
categoria_id = request.GET.get('categoria', '')
if categoria_id:
    productos = productos.filter(category_id=categoria_id)

# JavaScript para filtros dinámicos
document.getElementById('filtro-categoria').addEventListener('change', function() {
    const categoria = this.value;
    const url = new URL(window.location);
    url.searchParams.set('categoria', categoria);
    window.location.href = url.toString();
});
```

## Testing y Calidad

### 1. Validation Patterns
```python
# Validación de datos en views
def validate_product_data(request):
    errors = []
    
    if not request.POST.get('name'):
        errors.append('Nombre es requerido')
    
    try:
        precio = float(request.POST.get('price', 0))
        if precio <= 0:
            errors.append('Precio debe ser mayor a 0')
    except ValueError:
        errors.append('Precio inválido')
    
    return errors
```

### 2. Error Handling
```javascript
// Manejo de errores en JavaScript
function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    showToast(`Error: ${error.message}`, 'error');
}

try {
    // Operación riesgosa
    const result = await someAsyncOperation();
} catch (error) {
    handleError(error, 'someAsyncOperation');
}
```

---

## 🚀 Deployment a Contabo

### Información del Servidor
- **IP**: 84.247.129.180
- **Usuario**: root
- **Password**: Miesposa0526
- **Ruta del proyecto**: /var/www/CompuEasysApp
- **Servicio**: compueasys (systemd)

### Proceso de Deployment Manual

**IMPORTANTE**: El servidor NO tiene repositorio git configurado. Los archivos fueron subidos manualmente.

#### Subir cambios a Contabo (Desde PowerShell en Windows):

```powershell
# 1. Subir archivo específico
pscp -batch -pw Miesposa0526 "ruta\local\archivo" root@84.247.129.180:/var/www/CompuEasysApp/ruta/destino/

# Ejemplos:
# Subir template HTML
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\templates\store.html" root@84.247.129.180:/var/www/CompuEasysApp/core/templates/

# Subir JavaScript
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\static\js\store.js" root@84.247.129.180:/var/www/CompuEasysApp/core/static/js/

# Subir archivo Python (views, models, etc)
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\views.py" root@84.247.129.180:/var/www/CompuEasysApp/core/

# 2. Reiniciar servicio después de cambios
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl restart compueasys"

# 3. Verificar estado del servicio
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl status compueasys --no-pager -l | head -15"

# 4. Ver logs en caso de error
plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -n 50 --no-pager"
```

#### Workflow Completo de Deployment:

1. **Hacer cambios localmente** y probarlos
2. **Subir a GitHub** (para respaldo):
   ```bash
   git add .
   git commit -m "Descripción del cambio"
   git push origin main
   ```
3. **Subir archivos modificados a Contabo** usando `pscp`
4. **⚠️ IMPORTANTE - Archivos Estáticos**: Si modificaste CSS/JS/imágenes, también cópialos a staticfiles:
   ```powershell
   # Ejemplo para CSS de dashboard
   pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompueasysApp\dashboard\static\css\archivo.css" root@84.247.129.180:/var/www/CompuEasysApp/staticfiles/css/
   
   # Ejemplo para JS de core
   pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompueasysApp\core\static\js\archivo.js" root@84.247.129.180:/var/www/CompuEasysApp/staticfiles/js/
   ```
5. **Reiniciar servicio** en Contabo
6. **Verificar** que el sitio funcione correctamente

**🔴 NOTA CRÍTICA**: Django en producción sirve archivos estáticos desde `/var/www/CompuEasysApp/staticfiles/`, NO desde `app/static/`. Por eso debemos copiar manualmente o ejecutar collectstatic.

#### Archivos Comunes a Actualizar:

```powershell
# Templates (HTML)
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\templates\*.html" root@84.247.129.180:/var/www/CompuEasysApp/core/templates/

# Static Files (CSS/JS)
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\static\js\*.js" root@84.247.129.180:/var/www/CompuEasysApp/core/static/js/
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\static\css\*.css" root@84.247.129.180:/var/www/CompuEasysApp/core/static/css/

# Python Files
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\views.py" root@84.247.129.180:/var/www/CompuEasysApp/core/
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompuEasysApp\core\models.py" root@84.247.129.180:/var/www/CompuEasysApp/core/
```

#### Comandos SSH Útiles:

```powershell
# Conectar por SSH
plink -batch -pw Miesposa0526 root@84.247.129.180

# Ejecutar comando remoto
plink -batch -pw Miesposa0526 root@84.247.129.180 "comando"

# Ver archivos en servidor
plink -batch -pw Miesposa0526 root@84.247.129.180 "ls -la /var/www/CompuEasysApp/core/templates/"

# Ver logs del servicio
plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -f"
```

#### Troubleshooting:

```powershell
# Si el servicio no inicia
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl status compueasys -l"

# Ver últimos 100 logs
plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -n 100 --no-pager"

# Reiniciar Nginx (si hay problemas de proxy)
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl restart nginx"

# Verificar permisos de archivos
plink -batch -pw Miesposa0526 root@84.247.129.180 "chown -R root:www-data /var/www/CompuEasysApp"

# 🔴 ARCHIVOS ESTÁTICOS NO SE REFLEJAN - Ejecutar collectstatic
plink -batch -pw Miesposa0526 root@84.247.129.180 "/var/www/CompuEasysApp/venv/bin/python /var/www/CompuEasysApp/manage.py collectstatic --noinput"

# O copiar manualmente a staticfiles
pscp -batch -pw Miesposa0526 "ruta\local\archivo.css" root@84.247.129.180:/var/www/CompuEasysApp/staticfiles/css/
pscp -batch -pw Miesposa0526 "ruta\local\archivo.js" root@84.247.129.180:/var/www/CompuEasysApp/staticfiles/js/
```

### Auto-Deployment (Opcional)

Para configurar auto-deployment con GitHub Webhooks, ver [AUTO_DEPLOYMENT_SETUP.md](AUTO_DEPLOYMENT_SETUP.md)

---

**Nota**: Estos patrones han sido desarrollados y validados durante el desarrollo del proyecto CompuEasys. Seguir estas convenciones garantiza consistencia con el código existente y facilita el mantenimiento del proyecto.