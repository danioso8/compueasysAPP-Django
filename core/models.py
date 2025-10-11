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

class proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    cedulaOnita = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class ProductStore(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_buy = models.DecimalField(max_digits=10, decimal_places=0)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField(default=0)
    proveedor = models.ForeignKey(proveedor, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    type = models.ForeignKey(Type, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    iva = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    imagen = models.ImageField(upload_to='images/', height_field=None, width_field=None, max_length=None , blank=True, null=True)    
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class ProductVariant(models.Model):
    product = models.ForeignKey(ProductStore, on_delete=models.CASCADE, related_name='variants')
    nombre = models.CharField(max_length=100)  # Ej: "Rojo - M", "Azul - L"
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField(default=0)
    # Puedes agregar más campos como color, talla, etc.
    color = models.CharField(max_length=50, blank=True, null=True)
    talla = models.CharField(max_length=50, blank=True, null=True)
    imagen = models.ImageField(upload_to='variant_images/', blank=True, null=True)  # <-- NUEVO CAMPO

    def __str__(self):
        return f"{self.product.name} - {self.nombre}"

class Galeria(models.Model):
    galeria = models.ImageField(upload_to='galeria/')
    product = models.ForeignKey(ProductStore, related_name='galeria', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Imagen {self.id}"    

class SimpleUser(models.Model):
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)  # Considera usar un sistema de
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)  
    departamento = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=20, blank=True, null=True)
    

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
     nota = models.TextField(blank=True, null=True)
     fecha = models.DateTimeField(auto_now_add=True)
     detalles = models.TextField()  # Puedes guardar el resumen del carrito aquí
    
     def __str__(self):
        return f"Pedido {self.id} de {self.user.email}"


class PedidoDetalle(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(ProductStore, on_delete=models.CASCADE)
    variante = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)