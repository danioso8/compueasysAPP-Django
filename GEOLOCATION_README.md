# 🌍 Geolocalización por IP - Documentación

## 📋 Descripción

Sistema **modular y opcional** de geolocalización por IP que enriquece las visitas de tu tienda con información de ubicación (ciudad y país) de los visitantes.

### ✅ Características

- **100% Opcional**: Si falla o se elimina, el dashboard sigue funcionando normalmente
- **Sin API Key**: Usa ipapi.co (1,000 requests/día gratis)
- **Timeout corto**: 2 segundos máximo, no afecta rendimiento
- **Fallback seguro**: Si falla la API, simplemente no guarda ubicación
- **IPs locales ignoradas**: No consulta 127.0.0.1, localhost, 192.168.x.x

### 📁 Archivos Involucrados

1. **`core/geolocation_helper.py`** (PRINCIPAL)
   - Función `get_location_from_ip()`: Consulta la API
   - Función `create_visit_with_location()`: Helper universal para registrar visitas
   - **Puede eliminarse completamente sin romper nada**

2. **`core/views.py`** (4 líneas modificadas)
   - Import opcional en línea 17-21
   - Vista `home()`: líneas ~98-115
   - Vista `store()`: líneas ~298-305
   - Vista `product_detail()`: líneas ~586-608
   - Vista `cart()`: líneas ~1396-1415
   - Vista `checkout()`: líneas ~780-800

### 🔧 Cómo Funciona

```python
# Cuando un usuario visita tu tienda:
1. Se captura su IP real (considerando proxies)
2. Se intenta consultar ipapi.co con timeout de 2s
3. Si tiene éxito: se guarda city y country en la BD
4. Si falla: se registra la visita sin ubicación (normal)
```

### 🗑️ Cómo Eliminar la Funcionalidad

**Opción 1: Desactivar sin eliminar código (Recomendado)**
```python
# En core/views.py, cambiar línea 19:
GEOLOCATION_ENABLED = False  # Cambia True por False
```

**Opción 2: Eliminar completamente**

1. **Eliminar el archivo helper**:
   ```bash
   rm core/geolocation_helper.py
   # o en Windows:
   del core\geolocation_helper.py
   ```

2. **Limpiar imports en `core/views.py`**:
   Eliminar líneas 17-21:
   ```python
   # Eliminar estas líneas:
   try:
       from .geolocation_helper import create_visit_with_location
       GEOLOCATION_ENABLED = True
   except ImportError:
       GEOLOCATION_ENABLED = False
       create_visit_with_location = None
   ```

3. **Restaurar código de visitas** (en cada vista afectada):
   ```python
   # REEMPLAZAR esto:
   if GEOLOCATION_ENABLED and create_visit_with_location:
       try:
           create_visit_with_location(request, 'home', user_obj)
       except:
           StoreVisit.objects.create(...)
   else:
       StoreVisit.objects.create(...)
   
   # POR esto (código original):
   StoreVisit.objects.create(
       session_key=session_key,
       user=user_obj,
       visit_type='home',
       ip_address=ip_address,
       user_agent=user_agent
   )
   ```

### 📊 Datos Guardados

La geolocalización agrega estos campos al modelo `StoreVisit`:

- `city`: Ciudad (ej: "Bogotá", "Madrid")
- `country`: País (ej: "Colombia", "Spain")
- `ip_address`: Siempre se guarda (con o sin geolocalización)

### ⚠️ Limitaciones

- **Precisión**: ±50-200 km de error
- **VPNs/Proxies**: Mostrarán ubicación del servidor VPN
- **Límite API**: 1,000 requests/día (suficiente para mayoría de tiendas)
- **IPs móviles**: Menos precisas que IPs fijas

### 🔍 Verificar si Está Funcionando

1. **Ver en dashboard**: `?view=visitas` - columna "Ubicación"
2. **Revisar base de datos**:
   ```sql
   SELECT ip_address, city, country FROM core_storevisit 
   ORDER BY timestamp DESC LIMIT 10;
   ```
3. **Logs en consola**: Buscar "GEOLOCATION_ENABLED"

### 🆘 Troubleshooting

**Problema**: No se muestran ubicaciones
- **Causa**: IPs locales (127.0.0.1, 192.168.x.x)
- **Solución**: Probar desde Internet público o usar IP real

**Problema**: Error "requests module not found"
- **Solución**: `pip install requests` (ya debería estar)

**Problema**: Muy lento
- **Causa**: API ipapi.co caída
- **Solución**: El timeout de 2s previene esto automáticamente

### 📈 Alternativas Futuras

Si necesitas más precisión o mayor cuota:

1. **ipgeolocation.io**: 1,000/día gratis, requiere API key
2. **MaxMind GeoLite2**: Base de datos local, ilimitado
3. **ip-api.com**: 45/minuto gratis, sin HTTPS

### ✨ Resumen

- ✅ **Modular**: Fácil de agregar/quitar
- ✅ **No invasivo**: No rompe funcionalidad existente
- ✅ **Performante**: Timeout 2s, fallback seguro
- ✅ **Gratuito**: Sin API keys ni costos

---

**Desarrollado para CompuEasys App - Dashboard de Analytics**
