# 📸 Guía de Migración a Cloudinary - CompuEasys

## 🎯 Objetivo
Evitar que las imágenes se borren en cada deploy de Render migrando a Cloudinary.

## 📋 Pasos para Configurar

### 1️⃣ Crear cuenta en Cloudinary
1. Ve a [cloudinary.com](https://cloudinary.com)
2. Crea una cuenta gratuita (10GB gratis)
3. Ve al **Dashboard** y anota:
   - Cloud Name
   - API Key 
   - API Secret

### 2️⃣ Configurar variables de entorno en Render

En tu panel de Render, ve a tu servicio y agrega estas variables:

```bash
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

### 3️⃣ Para desarrollo local

Copia `.env.example` a `.env` y configura:

```bash
USE_CLOUDINARY=False  # Para desarrollo local
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

### 4️⃣ Migrar imágenes existentes

**ANTES del primer deploy con Cloudinary:**

```bash
# Activar Cloudinary temporalmente en desarrollo
# En tu .env, cambiar a: USE_CLOUDINARY=True

python migrate_images.py
```

### 5️⃣ Deploy a Render

1. Commit y push todos los cambios
2. Render detectará el nuevo `requirements.txt`
3. Las nuevas imágenes se guardarán en Cloudinary automáticamente

## 🔄 Funcionamiento

### Desarrollo (Local)
- `USE_CLOUDINARY=False`
- Imágenes se guardan en `media_files/`
- Desarrollo normal

### Producción (Render)
- `USE_CLOUDINARY=True` 
- Imágenes se suben a Cloudinary
- URLs persistentes entre deploys

## 📁 Estructura de carpetas en Cloudinary

```
compueasys/
├── products/          # Imágenes principales de productos
└── gallery/           # Imágenes de galería
```

## 🚀 Beneficios

✅ **Imágenes persistentes** - No se borran en deploys  
✅ **CDN global** - Carga más rápida  
✅ **Optimización automática** - Mejor performance  
✅ **Gratis hasta 10GB** - Suficiente para empezar  
✅ **Backup automático** - Imágenes seguras  

## 🔧 Troubleshooting

### Error de migración
```bash
# Verificar configuración
python manage.py shell
>>> from django.conf import settings
>>> print(settings.USE_CLOUDINARY)
>>> import cloudinary
>>> print(cloudinary.config())
```

### Imágenes no aparecen
- Verificar que `USE_CLOUDINARY=True` en Render
- Check cloudinary dashboard por las imágenes
- Verificar URLs en admin Django

## 📞 Soporte
Si tienes problemas, revisa los logs de Render o contacta soporte.