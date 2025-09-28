from django.db import models
from django.contrib.auth.models import User

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
    stock = models.PositiveIntegerField(default=0)
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

class SimpleUser(models.Model):
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.email

class Pedido(models.Model):
     user = models.ForeignKey(SimpleUser, on_delete=models.CASCADE)
     nombre = models.CharField(max_length=100)
     direccion = models.CharField(max_length=255)
     ciudad = models.CharField(max_length=100)
     departamento = models.CharField(max_length=100)
     codigo_postal = models.CharField(max_length=20)
     total = models.DecimalField(max_digits=10, decimal_places=2)
     fecha = models.DateTimeField(auto_now_add=True)
     detalles = models.TextField()  # Puedes guardar el resumen del carrito aquí

     def __str__(self):
        return f"Pedido {self.id} de {self.user.email}"