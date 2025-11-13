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

ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']
render_external_host = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_external_host:
    ALLOWED_HOSTS.append(render_external_host)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',  # Descomentado - listo para usar
    'cloudinary',          # Descomentado - listo para usar
    'core',
    'contable.apps.ContableConfig',
    'bootstrap5',    
    'django.contrib.humanize',
    'dashboard',
]

MIDDLEWARE = [    
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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


WSGI_APPLICATION = 'AppCompueasys.wsgi.application'

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

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'compueasys@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')  # app password de Gmail
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', DEFAULT_FROM_EMAIL)

# ====== Cloudinary Configuration ======
# Configuración condicional para producción vs desarrollo
USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'False') == 'True'

if USE_CLOUDINARY:
    # Importar cloudinary solo cuando se necesite
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    
    # Configuración Cloudinary para producción
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True
    )
    
    # Storage backends para archivos media
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    
    # URLs para archivos media
    MEDIA_URL = '/media/'
    # Definir MEDIA_ROOT para compatibilidad (aunque no se use con Cloudinary)
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')
else:
    # Configuración local para desarrollo
    MEDIA_URL = '/media_files/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')

# ===== STRIPE CONFIGURATION =====
# Stripe keys para procesar pagos
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_51...')  # Clave pública de prueba
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_51...')  # Clave secreta de prueba
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_...')  # Webhook secret

# Configuración de pagos
# Configuración de Wompi (Reemplaza Stripe)
WOMPI_PUBLIC_KEY = os.getenv('WOMPI_PUBLIC_KEY', 'pub_test_AcFLWqPJHeGBBFxy3nyjJT25WjWgLKVa')
WOMPI_PRIVATE_KEY = os.getenv('WOMPI_PRIVATE_KEY', 'prv_test_AsyPjPPqCzvs5tJGg5RqFvKvATrbXE7N') 
WOMPI_ENVIRONMENT = os.getenv('WOMPI_ENVIRONMENT', 'test')
WOMPI_BASE_URL = os.getenv('WOMPI_BASE_URL', 'https://sandbox.wompi.co/v1')

PAYMENT_SETTINGS = {
    'currency': 'COP',  # Pesos colombianos
    'payment_methods': ['CARD', 'PSE'],  # Tarjetas y PSE
    'provider': 'wompi',
    'automatic_tax': False,
    'shipping_calculation': True,
}


