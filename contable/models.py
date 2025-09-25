from django.db import models

# Create your models here.


class categoriaContable(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


    def __str__(self):
        return self.descripcion or f"Imagen {self.id}"

class ProductContsble (models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    categoria = models.CharField(max_length=50, default='General')
    iva = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    imagen = models.ImageField(upload_to='images/', height_field=None, width_field=None, max_length=None , blank=True, null=True)
    
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name