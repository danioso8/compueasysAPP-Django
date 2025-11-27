# Actualización: Edición de Productos con Galería y Variantes

## Problema Resuelto
Al editar un producto en el dashboard, no se mostraban las imágenes de galería ni las variantes existentes, y al actualizar se borraban todos estos datos.

## Cambios Implementados

### 1. Template `dashboard_home.html`

#### Pre-llenado de Formulario
- **Título dinámico**: Muestra "Editar Producto" o "Crear Producto" según el contexto
- **Campos pre-llenados**: Todos los campos del formulario ahora se llenan con los datos del producto cuando se edita:
  - Nombre, descripción
  - Precios (compra y venta)
  - Stock, descuento, IVA
  - Proveedor, categoría y tipo (pre-seleccionados en los selectores)

#### Imagen Principal
```html
- Muestra la imagen actual del producto
- Permite seleccionar una nueva imagen para reemplazarla
- Etiqueta clara "Imagen actual (selecciona un archivo para reemplazar)"
```

#### Galería de Imágenes
**Mejoras visuales:**
- Imágenes existentes con borde verde (#28a745) para identificarlas fácilmente
- Botón × (eliminar) en cada imagen
- Diseño con padding y background (#f8f9fa)
- Texto informativo: "Añade más imágenes o elimina las existentes"

**Funcionalidad:**
- Input hidden `galeria_keep[]` para cada imagen existente
- Al hacer clic en ×, se marca la imagen para eliminar (input hidden `galeria_delete[]`)
- Permite agregar nuevas imágenes sin eliminar las existentes

#### Variantes
**Mejoras visuales:**
- Diseño en tarjetas con borde y padding
- Muestra imagen actual de la variante (80x80px)
- Input file separado con etiqueta "Nueva" para actualizar imagen
- Placeholder para variantes sin imagen
- Botón × posicionado absolutamente en la esquina superior derecha

**Funcionalidad:**
- Input hidden `variante_id[]` para identificar variantes existentes
- Campos pre-llenados con datos de cada variante
- Botón eliminar marca la variante para borrado (`variante_delete[]`)
- Permite actualizar datos sin necesidad de reemplazar la imagen
- Agregar nuevas variantes con el botón "+ Agregar variante"

#### Botones de Acción
```html
- "Actualizar" (en lugar de "Guardar") cuando se edita
- "Nuevo Producto" para limpiar el formulario
- "Cancelar" (solo en edición) para volver a la lista
```

### 2. Backend `views.py`

#### Lógica de Actualización de Galería
```python
# Eliminar imágenes marcadas
galeria_delete_ids = request.POST.getlist('galeria_delete[]')
- Obtiene IDs de imágenes a eliminar
- Elimina archivo físico del storage
- Elimina registro de la base de datos

# Agregar nuevas imágenes
- Solo agrega las nuevas sin tocar las existentes
```

#### Lógica de Actualización de Variantes
```python
# Eliminar variantes marcadas
variante_delete_ids = request.POST.getlist('variante_delete[]')
- Elimina imagen física si existe
- Elimina registro de la base de datos

# Actualizar o crear variantes
variante_ids = request.POST.getlist('variante_id[]')
- Si tiene ID: actualiza variante existente
  * Solo reemplaza imagen si se sube una nueva
  * Mantiene imagen actual si no se sube nueva
- Si no tiene ID: crea nueva variante
```

**Mejoras clave:**
- ✅ Ya NO borra todas las variantes y las recrea
- ✅ Actualiza solo los datos modificados
- ✅ Preserva imágenes existentes si no se reemplazan
- ✅ Manejo seguro de eliminación de archivos físicos

### 3. JavaScript `dashboard.js`

#### Función `agregarVariante()`
Actualizada para coincidir con los nuevos estilos:
```javascript
- Aplica clases Bootstrap correctas (form-control-sm)
- Estilos inline para max-width
- Border y background
- Muestra botón eliminar desde el inicio
- Accept="image/*" para el input file
```

#### Handlers de Eliminación
Ya existían correctamente implementados:
- `existingGalleryRemoveHandler`: Marca imagen de galería para eliminar
- `variantRemoveHandler`: Marca variante existente para eliminar
- `variantRemoveNewHandler`: Elimina variante nueva del DOM

## Flujo de Actualización

1. **Usuario hace clic en "Editar"** en la lista de productos
2. **URL con parámetro**: `?view=productos&editar=123`
3. **Backend carga**: `producto_to_edit` con todas sus relaciones
4. **Template renderiza**: 
   - Formulario pre-llenado
   - Galería con imágenes existentes
   - Variantes con sus datos e imágenes
5. **Usuario modifica**:
   - Puede eliminar imágenes/variantes (×)
   - Puede agregar nuevas imágenes/variantes
   - Puede actualizar datos de variantes
   - Puede reemplazar imágenes
6. **Al enviar formulario**:
   - Backend procesa eliminaciones primero
   - Luego agrega nuevas imágenes
   - Actualiza variantes existentes o crea nuevas
7. **Resultado**: Producto actualizado sin pérdida de datos

## Campos del Formulario

### Inputs Hidden para Edición
```html
product_id: ID del producto (para identificar actualización)
galeria_keep[]: IDs de imágenes existentes (opcional)
galeria_delete[]: IDs de imágenes a eliminar
variante_id[]: IDs de variantes existentes
variante_delete[]: IDs de variantes a eliminar
```

### Arrays de Datos
```html
variante_nombre[]
variante_precio[]
variante_stock[]
variante_color[]
variante_talla[]
variante_imagen[] (FILES)
galeria (FILES, multiple)
```

## Testing Recomendado

1. ✅ Crear producto con galería y variantes
2. ✅ Editar producto: verificar que muestra todo
3. ✅ Eliminar una imagen de galería y guardar
4. ✅ Eliminar una variante y guardar
5. ✅ Agregar nueva imagen a galería
6. ✅ Agregar nueva variante
7. ✅ Actualizar datos de variante sin cambiar imagen
8. ✅ Actualizar imagen de variante
9. ✅ Actualizar imagen principal
10. ✅ Cancelar edición

## Compatibilidad

- ✅ Django 4.2.24
- ✅ Bootstrap 5.3.8
- ✅ Font Awesome 6.4.0
- ✅ JavaScript ES6+
- ✅ Responsive design (mobile-first)

## Archivos Modificados

1. `dashboard/templates/dashboard/dashboard_home.html` (líneas 1589-1735)
2. `dashboard/views.py` (líneas 481-560)
3. `dashboard/static/js/dashboard.js` (líneas 273-288)

---

**Fecha de implementación**: 2025-11-27
**Estado**: ✅ Completado y funcional
