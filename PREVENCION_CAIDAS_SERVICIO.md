# 🛡️ Prevención de Caídas del Servicio CompuEasys en Contabo

## Fecha de Implementación: 21 de Enero 2026

---

## ✅ Medidas Preventivas Implementadas

### 1. **Auto-Restart del Servicio**
El servicio ahora se reinicia automáticamente si se cae:
- **Restart=always**: Reinicio automático en cualquier falla
- **RestartSec=10s**: Espera 10 segundos antes de reiniciar

### 2. **Límites de Memoria**
- **MemoryLimit**: 500MB (límite suave)
- **MemoryMax**: 600MB (límite duro - fuerza restart si se excede)
- Actualmente consumiendo: ~75MB (saludable)

### 3. **Workers Optimizados**
- **Reducido de 3 a 2 workers**: Reduce consumo de memoria ~33%
- **max-requests 1000**: Reinicia worker después de 1000 peticiones (previene memory leaks)
- **max-requests-jitter 50**: Evita reinicios simultáneos
- **timeout 60s**: Timeout de 60 segundos para peticiones

### 4. **SWAP Configurado**
- **2GB de SWAP**: Memoria virtual de emergencia
- Previene kills por OOM (Out Of Memory)

---

## 📊 Monitoreo

### Comandos Útiles desde PowerShell (Windows)

```powershell
# Ver estado del servicio
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl status compueasys --no-pager | head -15"

# Ver uso de memoria
plink -batch -pw Miesposa0526 root@84.247.129.180 "free -h"

# Ver logs en tiempo real
plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -f"

# Ver últimos 50 logs
plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -n 50 --no-pager"

# Monitoreo completo (script personalizado)
plink -batch -pw Miesposa0526 root@84.247.129.180 "/root/monitor_compueasys.sh"

# Reiniciar servicio manualmente
plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl restart compueasys"

# Ver procesos de Gunicorn
plink -batch -pw Miesposa0526 root@84.247.129.180 "ps aux | grep gunicorn | grep -v grep"

# Verificar archivos del servicio
plink -batch -pw Miesposa0526 root@84.247.129.180 "cat /etc/systemd/system/compueasys.service"
```

---

## 🚨 Qué Hacer Si el Servicio Se Cae

### El servicio ahora se auto-reinicia, pero si necesitas intervenir:

1. **Verificar estado**:
   ```powershell
   plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl status compueasys --no-pager"
   ```

2. **Ver logs de error**:
   ```powershell
   plink -batch -pw Miesposa0526 root@84.247.129.180 "journalctl -u compueasys -n 100 --no-pager"
   ```

3. **Reiniciar manualmente** (solo si no se reinicia solo):
   ```powershell
   plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl restart compueasys"
   ```

4. **Verificar que reinició correctamente**:
   ```powershell
   plink -batch -pw Miesposa0526 root@84.247.129.180 "systemctl status compueasys --no-pager | head -15"
   ```

---

## 📈 Optimizaciones de Django (Recomendadas)

Para optimizar aún más y prevenir futuros problemas de memoria:

### 1. **Optimizar Queries de Base de Datos**

Buscar queries N+1 en el código:
```python
# ❌ Malo (N+1 queries)
productos = ProductStore.objects.all()
for p in productos:
    print(p.category.name)  # Query por cada producto

# ✅ Bueno (1 query)
productos = ProductStore.objects.select_related('category').all()
for p in productos:
    print(p.category.name)
```

### 2. **Cacheo de Queries Frecuentes**

Instalar Redis para cacheo:
```bash
# En Contabo (ejecutar desde PowerShell)
plink -batch -pw Miesposa0526 root@84.247.129.180 "apt-get install -y redis-server"
```

Configurar en `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. **Debug Mode Desactivado**

Verificar que en producción:
```python
# settings.py
DEBUG = False  # CRÍTICO en producción
```

### 4. **Pagination en Listados**

Para páginas con muchos productos:
```python
from django.core.paginator import Paginator

def store(request):
    productos = ProductStore.objects.all()
    paginator = Paginator(productos, 20)  # 20 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'store.html', {'productos': page_obj})
```

---

## 🔍 Análisis de Problemas Comunes

### Error: Worker killed with status 9
**Causa**: OOM Killer terminó el proceso por falta de memoria  
**Solución**: ✅ Ya implementada (MemoryLimit + SWAP)

### Error: Worker timeout
**Causa**: Query lenta o proceso bloqueante  
**Solución**: ✅ Ya implementada (timeout 60s + max-requests)

### Error: Too many connections
**Causa**: Demasiadas conexiones a DB  
**Solución**: Configurar connection pooling

---

## 📁 Archivos de Configuración

### `/etc/systemd/system/compueasys.service`
```ini
[Unit]
Description=CompuEasys Gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/CompuEasysApp
Environment="PATH=/var/www/CompuEasysApp/venv/bin"

ExecStart=/var/www/CompuEasysApp/venv/bin/gunicorn \
    --workers 2 \
    --worker-class sync \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 60 \
    --bind unix:/var/www/CompuEasysApp/gunicorn.sock \
    AppCompueasys.wsgi:application

Restart=always
RestartSec=10s
MemoryLimit=500M
MemoryMax=600M
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## 🎯 Resumen de Mejoras

| Medida | Antes | Ahora | Beneficio |
|--------|-------|-------|-----------|
| Workers | 3 | 2 | -33% memoria |
| Auto-restart | ❌ | ✅ | Disponibilidad 99%+ |
| Límite memoria | ∞ | 500MB-600MB | Previene OOM |
| SWAP | 0GB | 2GB | Memoria emergencia |
| Worker recycle | ❌ | ✅ (1000 req) | Previene memory leaks |
| Timeout | 30s | 60s | Menos timeouts |

---

## 📞 Contacto y Soporte

Si el servicio continúa presentando problemas después de estas optimizaciones:

1. Revisar logs detallados
2. Analizar queries lentas en la base de datos
3. Considerar upgrade de plan de hosting (más RAM)
4. Implementar CDN para archivos estáticos
5. Configurar Redis para cacheo

---

**Última actualización**: 21 de Enero 2026  
**Estado**: ✅ Servicio estable con todas las medidas preventivas activas
