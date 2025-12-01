from django.db import models
from django.utils import timezone
# Modelo para datos de la tienda
class StoreInfo(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la tienda')
    direccion = models.CharField(max_length=255, verbose_name='Dirección', blank=True, null=True)
    telefono = models.CharField(max_length=30, verbose_name='Teléfono', blank=True, null=True)
    email = models.EmailField(verbose_name='Email', blank=True, null=True)
    descripcion = models.TextField(verbose_name='Descripción', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre




class WompiConfig(models.Model):
    nombre = models.CharField(max_length=100, default='Configuración Wompi')
    public_key = models.CharField(max_length=200)
    private_key = models.CharField(max_length=200)
    integrity_secret = models.CharField(max_length=200, blank=True, null=True, help_text='Clave secreta de integridad de Wompi')
    environment = models.CharField(max_length=20, choices=[('production', 'Producción'), ('test', 'Pruebas')], default='production')
    base_url = models.CharField(max_length=200, default='https://production.wompi.co/v1')
    is_active = models.BooleanField(default=True, verbose_name='Activar Wompi', help_text='Activar/desactivar Wompi como método de pago')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"WompiConfig ({self.environment})"


class StoreConfig(models.Model):
    """
    Configuración de la tienda (Singleton)
    """
    # Información Básica
    nombre_tienda = models.CharField(max_length=200, default='CompuEasys', verbose_name='Nombre de la Tienda')
    slogan = models.CharField(max_length=300, blank=True, null=True, verbose_name='Slogan')
    email_tienda = models.EmailField(blank=True, null=True, verbose_name='Email de Contacto')
    telefono_tienda = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    
    # Ubicación
    direccion_tienda = models.CharField(max_length=500, blank=True, null=True, verbose_name='Dirección')
    ciudad_tienda = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ciudad')
    pais_tienda = models.CharField(max_length=100, default='Colombia', verbose_name='País')
    
    # Redes Sociales
    facebook = models.URLField(blank=True, null=True, verbose_name='Facebook')
    instagram = models.URLField(blank=True, null=True, verbose_name='Instagram')
    twitter = models.URLField(blank=True, null=True, verbose_name='Twitter/X')
    whatsapp = models.CharField(max_length=20, blank=True, null=True, verbose_name='WhatsApp')
    
    # Horarios
    horario_semana = models.CharField(max_length=100, default='8:00 AM - 6:00 PM', verbose_name='Horario Lunes a Viernes')
    horario_sabado = models.CharField(max_length=100, default='9:00 AM - 2:00 PM', verbose_name='Horario Sábado')
    horario_domingo = models.CharField(max_length=100, default='Cerrado', verbose_name='Horario Domingo')
    
    # Logo y assets
    logo = models.ImageField(upload_to='store/', blank=True, null=True, verbose_name='Logo de la Tienda')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Tienda'
        verbose_name_plural = 'Configuración de Tienda'
    
    @classmethod
    def get_config(cls):
        """Obtiene o crea la configuración (Singleton)"""
        config, created = cls.objects.get_or_create(id=1)
        return config
    
    def __str__(self):
        return f"Configuración - {self.nombre_tienda}"


class register_superuser(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)  # Considera usar un sistema de hash para mayor seguridad
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username