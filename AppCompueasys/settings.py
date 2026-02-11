from pathlib import Path
from dotenv import load_dotenv
from os.path import join
import os
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-5ykh0i3xxbu298h!xo-bh#k+97m!f=qb_7rt3x@zhhji$-pfb%')
DEBUG = True

# ALLOWED_HOSTS configuration
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '.onrender.com,localhost,127.0.0.1').split(',')
render_external_host = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_external_host and render_external_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_external_host)

# CSRF Trusted Origins for production
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')

# Security settings for HTTPS (when SSL is configured)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Nginx handles redirection
SESSION_COOKIE_SECURE = False  # Set to True when SSL is active
CSRF_COOKIE_SECURE = False  # Set to True when SSL is active

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'contable.apps.ContableConfig',
    'billing.apps.BillingConfig',
    'django_bootstrap5',    
    'django.contrib.humanize',
    'dashboard',
    'channels',  # Para WebSockets
]

MIDDLEWARE = [    
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'contable.middleware.ContableAuthMiddleware',  # Middleware personalizado para contable
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AppCompueasys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'core', 'templates'),
            os.path.join(BASE_DIR, 'dashboard', 'templates'),
            os.path.join(BASE_DIR, 'billing', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



# Configuración para Channels
ASGI_APPLICATION = 'AppCompueasys.asgi.application'
WSGI_APPLICATION = 'AppCompueasys.wsgi.application'

# Channel layers (por defecto en memoria, para producción usar Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Base de datos principal: configuración flexible
import dj_database_url

# Usar DB de producción localmente si está configurado
USE_PRODUCTION_DB = os.getenv('USE_PRODUCTION_DB', 'False') == 'True'

if os.getenv('DJANGO_DEVELOPMENT') == 'True' and not USE_PRODUCTION_DB:
    # Desarrollo local con SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Producción o desarrollo con DB de producción
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        DATABASES = {
            'default': dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True
            )
        }
    else:
        # Fallback a variables individuales
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DB_NAME'),
                'USER': os.getenv('DB_USERNAME'),
                'PASSWORD': os.getenv('DB_PASSWORD'),
                'HOST': os.getenv('DB_HOST'),
                'PORT': os.getenv('DB_PORT'),
                'OPTIONS': {
                    'sslmode': 'require',
                },
            }
        }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
LOGIN_REDIRECT_URL = '/dashboard/'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


STATICFILES_DIRS = [
     join(BASE_DIR, 'core', 'static'),
     join(BASE_DIR, 'dashboard', 'static'),
     join(BASE_DIR, 'contable', 'static'),
]

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')  # Cambiado para email real
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'  # Para algunos proveedores
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'compueasys@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'hucewtoa stbqrcnk')  # App Password sin espacios
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'CompuEasys <{EMAIL_HOST_USER}>')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', EMAIL_HOST_USER)
EMAIL_TIMEOUT = 30  # Timeout en segundos

# Base URL para enlaces en emails
# En producción usa la URL del dominio, en desarrollo usa localhost
if os.getenv('DJANGO_DEVELOPMENT') == 'True':
    BASE_URL = 'http://127.0.0.1:8000'
else:
    BASE_URL = os.getenv('BASE_URL', 'http://compueasys.com')

# ====== MEDIA FILES CONFIGURATION ======
# Configuración para archivos media (imágenes, videos, etc.)

# Configuración para archivos media locales
if os.getenv('DJANGO_DEVELOPMENT') == 'True':
    # Desarrollo local
    if USE_PRODUCTION_DB:
        # Cargar imágenes locales (ya migradas de Render)
        MEDIA_URL = '/media/'
        MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')
        print("🌐 DESARROLLO: Usando imágenes locales (migradas de Render)")
        print(f"📸 MEDIA_URL: {MEDIA_URL}")
    else:
        # Desarrollo puro con DB local
        MEDIA_URL = '/media/'
        MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')
        print("🔧 DESARROLLO: Usando imágenes locales")
else:
    # Producción en Contabo con archivos locales
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/CompuEasysApp/media_files')
    print(f"🚀 PRODUCCIÓN: MEDIA_ROOT = {MEDIA_ROOT}")
    
    # Crear directorio si no existe
    if not os.path.exists(MEDIA_ROOT):
        try:
            os.makedirs(MEDIA_ROOT, exist_ok=True)
            print(f"✅ Directorio MEDIA_ROOT creado: {MEDIA_ROOT}")
        except Exception as e:
            print(f"❌ Warning: No se pudo crear MEDIA_ROOT: {e}")

# ===== WOMPI CONFIGURATION =====
# Configuración completa de Wompi Colombia

# === PRODUCCIÓN WOMPI ===
WOMPI_PUBLIC_KEY = os.getenv('WOMPI_PUBLIC_KEY', 'pub_prod_DMT4tAPNSvnvuHiVmwjIoyVwaam8N3k7')
WOMPI_PRIVATE_KEY = os.getenv('WOMPI_PRIVATE_KEY', 'prv_prod_1X63CjcbCvba86WpWJOuXiqJnKvtMgeT')
WOMPI_EVENTS_SECRET = os.getenv('WOMPI_EVENTS_SECRET', 'prod_events_cmDhDmWt3heMjSm5uB9QMRHJO8HxJLvv')
WOMPI_INTEGRITY_SECRET = os.getenv('WOMPI_INTEGRITY_SECRET', 'prod_integrity_YW2t43XJOhLUAOONX5u6U8AO5sEosmTT')
WOMPI_ENVIRONMENT = os.getenv('WOMPI_ENVIRONMENT', 'prod')
WOMPI_BASE_URL = os.getenv('WOMPI_BASE_URL', 'https://production.wompi.co/v1')

# URL para eventos de Wompi
WOMPI_EVENTS_URL = f"{WOMPI_BASE_URL}/merchants/events"

PAYMENT_SETTINGS = {
    'currency': 'COP',  # Pesos colombianos
    'payment_methods': ['CARD', 'PSE'],  # Tarjetas y PSE
    'provider': 'wompi',
    'automatic_tax': False,
    'shipping_calculation': True,
}


