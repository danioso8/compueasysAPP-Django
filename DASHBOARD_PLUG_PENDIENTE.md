# 🎨 Dashboard PLUG - Trabajo en Progreso

**Fecha**: 17 de Enero, 2026  
**Estado**: ⚠️ PENDIENTE - Diseño no aplicado correctamente  
**Prioridad**: Alta

## 📋 Resumen

Se intentó implementar un diseño de dashboard profesional estilo PLUG (basado en template de Tailwind CSS) con sidebar azul oscuro corporativo, pero los cambios no se están reflejando correctamente ni en local ni en producción.

## 🎯 Objetivo del Diseño

Crear un dashboard moderno estilo PLUG con las siguientes características:

### Diseño Deseado
- ✅ **Sidebar azul oscuro** (#1e3a5f) - Color corporativo profesional
- ✅ **Top navbar blanco** con barra de búsqueda y menú de usuario
- ✅ **Stats cards** con iconos de colores, tendencias y efectos hover
- ✅ **Tablas modernas** con headers limpios
- ✅ **Badges coloridos** para estados
- ✅ **Sistema de diseño completo** con CSS variables

### Referencia Visual
![PLUG Template](imagen-compartida-por-usuario.png)
- Sidebar oscuro a la izquierda
- Navbar fijo en la parte superior
- Cards con estadísticas coloridas
- Gráficos modernos
- Tablas limpias con datos bien organizados

## 📁 Archivos Creados

### 1. dashboard-tailwind-pro.css
**Ubicación**: `dashboard/static/css/dashboard-tailwind-pro.css`  
**Tamaño**: 11 KB  
**Estado**: ✅ Creado y subido a Contabo

**Características implementadas**:

```css
/* Variables CSS */
:root {
    --sidebar-bg: #1e3a5f;        /* Azul oscuro corporativo */
    --sidebar-hover: #2d4a72;     /* Hover más claro */
    --primary: #3b82f6;           /* Azul primario */
    --success: #10b981;           /* Verde success */
    --warning: #f59e0b;           /* Amarillo warning */
    --danger: #ef4444;            /* Rojo danger */
    --bg-light: #f8fafc;          /* Fondo claro */
}
```

**Componentes estilizados**:
- Top navbar (64px altura, fondo blanco, barra de búsqueda)
- Sidebar (260px ancho, fondo azul oscuro)
- Stat cards (hover lift, iconos coloridos, tendencias)
- Tables (headers con gradient opcional)
- Forms (inputs redondeados, focus states)
- Buttons (primary, secondary, outline)
- Badges (pills coloridos para status)
- Pagination moderna

**Responsive**:
- Mobile: <768px
- Tablet: 768-1024px
- Desktop: >1024px

### 2. Cambios en dashboard_home.html
**Línea 16**: Cambio de CSS

```html
<!-- ANTES -->
<link rel="stylesheet" href="{% static 'css/dashboard-corporate.css' %}" />

<!-- AHORA -->
<link rel="stylesheet" href="{% static 'css/dashboard-tailwind-pro.css' %}" />
```

**Estado**: ✅ Actualizado en archivo local y Contabo

## ⚠️ Problemas Encontrados

### Problema 1: Archivos Estáticos No Se Reflejan

**Síntoma**: Los cambios en CSS/JS no se ven en el navegador después de subirlos.

**Causa Root**: Django en producción sirve archivos estáticos desde `/var/www/CompuEasysApp/staticfiles/`, NO desde `app/static/`.

**Solución Descubierta**:

```powershell
# Paso 1: Subir archivo a static/
pscp -batch -pw Miesposa0526 "archivo.css" root@84.247.129.180:/var/www/CompuEasysApp/dashboard/static/css/

# Paso 2: CRÍTICO - Copiar a staticfiles/
pscp -batch -pw Miesposa0526 "archivo.css" root@84.247.129.180:/var/www/CompuEasysApp/staticfiles/css/

# Paso 3: Reiniciar servicio
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl restart compueasys"
```

**Alternativa - Usar collectstatic**:

```powershell
plink -batch -pw Miesposa0526 root@84.247.129.180 "/var/www/CompuEasysApp/venv/bin/python /var/www/CompuEasysApp/manage.py collectstatic --noinput"
```

### Problema 2: Diseño No Se Aplica Correctamente

**Síntoma**: A pesar de subir los archivos correctamente, el diseño PLUG no se ve como esperado.

**Estado Actual**: ⚠️ PENDIENTE DE INVESTIGACIÓN

**Posibles Causas**:
1. ❓ Conflicto con otros archivos CSS que se cargan después
2. ❓ Especificidad de CSS - otros estilos sobrescriben los nuevos
3. ❓ Caché del navegador muy agresivo
4. ❓ Estructura HTML no coincide con selectores CSS
5. ❓ Falta activar/desactivar otros CSS

## 🔍 Próximos Pasos para el Lunes

### Investigación Necesaria

1. **Revisar orden de carga de CSS** en `dashboard_home.html`:
   ```html
   <head>
       <!-- Bootstrap -->
       <link href="bootstrap.min.css" />
       <!-- Tailwind CDN -->
       <script src="tailwind"></script>
       <!-- Nuestro CSS - ¿Se carga al final? -->
       <link rel="stylesheet" href="dashboard-tailwind-pro.css" />
   </head>
   ```

2. **Verificar que las clases CSS coincidan** con el HTML:
   - El CSS usa `.sidebar`, `.top-navbar`, `.stat-card`
   - Verificar que el HTML tenga esas clases exactas

3. **Probar desactivando otros CSS** temporalmente:
   ```html
   <!-- Comentar estos -->
   <!-- <link rel="stylesheet" href="{% static 'css/dashboard.css' %}" /> -->
   <!-- <link rel="stylesheet" href="{% static 'css/dashboard-corporate.css' %}" /> -->
   ```

4. **Verificar estructura HTML del dashboard**:
   - ¿Tiene `<div class="sidebar">`?
   - ¿Tiene `<div class="top-navbar">`?
   - ¿Tiene `<div class="stat-card">`?

5. **Inspeccionar en navegador** (F12):
   - Network tab: verificar que `dashboard-tailwind-pro.css` se carga (200 OK)
   - Elements tab: ver qué estilos se aplican y cuáles se sobrescriben
   - Console: buscar errores de carga

### Acciones Concretas

#### Opción A: Revisar y Ajustar CSS Actual

1. Abrir `dashboard_home.html` y buscar la estructura HTML actual
2. Comparar con los selectores en `dashboard-tailwind-pro.css`
3. Ajustar clases o CSS según sea necesario
4. Probar localmente primero

#### Opción B: Crear desde Cero con Estructura PLUG

1. Crear nuevo template HTML con estructura exacta de PLUG
2. Aplicar el CSS que ya creamos
3. Migrar contenido dinámico de Django al nuevo template
4. Probar y ajustar

#### Opción C: Usar Template PLUG Real

1. Descargar template PLUG oficial (si es posible)
2. Integrar con Django
3. Adaptar a nuestra estructura de datos

## 📝 Comandos Importantes Documentados

### Deployment Completo

```powershell
# 1. Subir HTML
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompueasysApp\dashboard\templates\dashboard\dashboard_home.html" root@84.247.129.180:/var/www/CompuEasysApp/dashboard/templates/dashboard/

# 2. Subir CSS a static/
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompueasysApp\dashboard\static\css\dashboard-tailwind-pro.css" root@84.247.129.180:/var/www/CompuEasysApp/dashboard/static/css/

# 3. Subir CSS a staticfiles/ (CRÍTICO)
pscp -batch -pw Miesposa0526 "D:\ESCRITORIO\CompueasysApp\dashboard\static\css\dashboard-tailwind-pro.css" root@84.247.129.180:/var/www/CompuEasysApp/staticfiles/css/

# 4. Reiniciar servicio
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl restart compueasys"

# 5. Verificar estado
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl status compueasys --no-pager | head -10"
```

### Verificación de Archivos en Servidor

```powershell
# Ver si el CSS existe
plink -batch -pw Miesposa0526 root@84.247.129.180 "ls -lh /var/www/CompuEasysApp/staticfiles/css/dashboard-tailwind-pro.css"

# Ver todos los CSS
plink -batch -pw Miesposa0526 root@84.247.129.180 "ls -la /var/www/CompuEasysApp/staticfiles/css/"

# Ver logs del servicio
plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -n 50 --no-pager"
```

### Servidor Local

```powershell
# Activar entorno y correr servidor
cd D:\ESCRITORIO\CompueasysApp
.\venv_new\Scripts\Activate.ps1
py manage.py runserver

# URL: http://127.0.0.1:8000/dashboard/dashboard_home/
```

## 📊 Estado de Archivos

| Archivo | Local | Contabo static/ | Contabo staticfiles/ | Estado |
|---------|-------|-----------------|---------------------|--------|
| dashboard-tailwind-pro.css | ✅ | ✅ | ✅ | Subido pero no se aplica |
| dashboard_home.html | ✅ | ✅ | N/A | Actualizado |
| store.js | ✅ | ✅ | ✅ | Actualizado |

## 🎨 Especificaciones del Diseño

### Colores Definidos

```css
/* Sidebar */
--sidebar-bg: #1e3a5f;          /* Azul oscuro corporativo */
--sidebar-hover: #2d4a72;       /* Hover más claro */

/* Brand Colors */
--primary: #3b82f6;             /* Azul */
--primary-dark: #2563eb;        /* Azul oscuro */
--success: #10b981;             /* Verde */
--warning: #f59e0b;             /* Amarillo */
--danger: #ef4444;              /* Rojo */
--info: #06b6d4;                /* Cyan */

/* Neutrales */
--bg-light: #f8fafc;            /* Fondo claro */
--text-dark: #0f172a;           /* Texto oscuro */
--text-muted: #64748b;          /* Texto secundario */
--border: #e2e8f0;              /* Bordes */
```

### Tipografía

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

**Pesos usados**: 400, 500, 600, 700, 800

### Espaciado (8px Grid)

```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
```

### Sombras

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

## 🔧 Troubleshooting

### Si los cambios no se ven:

1. **Limpiar caché del navegador**: Ctrl+Shift+R (hard reload)
2. **Verificar que el archivo se cargue**: F12 → Network → buscar `dashboard-tailwind-pro.css`
3. **Inspeccionar elemento**: F12 → Elements → ver qué estilos se aplican
4. **Revisar console**: F12 → Console → buscar errores
5. **Verificar en servidor**: SSH y confirmar que archivo existe en staticfiles/

### Si hay errores 500:

```powershell
# Ver logs
plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -n 100 --no-pager"

# Revisar permisos
plink -batch -pw Miesposa0526 root@84.247.129.180 "ls -la /var/www/CompuEasysApp/staticfiles/css/"
```

## 💡 Notas Importantes

1. **SIEMPRE copiar a staticfiles/** cuando modifiques CSS/JS
2. El servidor de desarrollo (local) lee de `static/`, pero producción lee de `staticfiles/`
3. Inter font se carga desde Google Fonts CDN
4. Bootstrap 5.3.8 y Tailwind CSS se usan simultáneamente (puede haber conflictos)
5. Font Awesome 6.4.0 para iconos

## 📞 Contacto

**Servidor Contabo**:
- IP: 84.247.129.180
- Usuario: root
- Password: Miesposa0526
- Proyecto: /var/www/CompuEasysApp
- Servicio: compueasys (systemd)
- Python: /var/www/CompuEasysApp/venv/bin/python

---

**📅 Continuar el Lunes**: Revisar por qué el diseño no se aplica correctamente y ajustar según sea necesario.
