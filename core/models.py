from django.db import models


# Create your models here.



class Category(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
class Type(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)

    def __str__(self):
        return self.name



class ProductStore(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    type = models.ForeignKey(Type, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    iva = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    imagen = models.ImageField(upload_to='images/', height_field=None, width_field=None, max_length=None , blank=True, null=True)    
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    
class Galeria(models.Model):
    galeria = models.ImageField(upload_to='galeria/')
    product = models.ForeignKey(ProductStore, related_name='galeria', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Imagen {self.id}"    