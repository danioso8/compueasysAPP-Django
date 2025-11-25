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
    environment = models.CharField(max_length=20, choices=[('production', 'Producción'), ('test', 'Pruebas')], default='production')
    base_url = models.CharField(max_length=200, default='https://production.wompi.co/v1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"WompiConfig ({self.environment})"




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