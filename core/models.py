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
    username = models.CharField(max_length=100,)
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
    # Estados del pedido
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('enviado', 'Enviado'),
        ('llegando', 'En camino'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Métodos de pago
    METODO_PAGO_CHOICES = [
        ('contraentrega', 'Contra entrega'),
        ('recoger_tienda', 'Recoger en tienda'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
        ('wompi', 'Pago Wompi'),
    ]
    
    # Estado de pago
    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
        ('reembolsado', 'Reembolsado'),
    ]

    # Información del usuario
    user = models.ForeignKey(SimpleUser, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    # Información de entrega
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20, blank=True, null=True)
    
    # Información financiera
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Información del pedido
    nota = models.TextField(blank=True, null=True, help_text="Nota del cliente al hacer el pedido")
    nota_admin = models.TextField(blank=True, null=True, help_text="Notas administrativas internas")
    detalles = models.TextField()  # Resumen del carrito en JSON
    
    # Estados y seguimiento
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='contraentrega')
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='pendiente')
    
    # Información de pago Wompi
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Códigos de descuento
    codigo_descuento = models.CharField(max_length=50, blank=True, null=True)
    
    # Fechas
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_enviado = models.DateTimeField(blank=True, null=True)
    fecha_entregado = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.id} - {self.user.email} - {self.get_estado_display()}"
    
    def get_estado_badge_class(self):
        """Retorna la clase CSS para el badge del estado"""
        estado_classes = {
            'pendiente': 'badge-warning',
            'confirmado': 'badge-info',
            'enviado': 'badge-primary',
            'llegando': 'badge-primary',
            'entregado': 'badge-success',
            'cancelado': 'badge-danger',
        }
        return estado_classes.get(self.estado, 'badge-secondary')
    
    def get_pago_badge_class(self):
        """Retorna la clase CSS para el badge del estado de pago"""
        pago_classes = {
            'pendiente': 'badge-warning',
            'procesando': 'badge-info',
            'completado': 'badge-success',
            'fallido': 'badge-danger',
            'reembolsado': 'badge-secondary',
        }
        return pago_classes.get(self.estado_pago, 'badge-secondary')


class PedidoDetalle(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(ProductStore, on_delete=models.CASCADE)
    variante = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)


class BonoDescuento(models.Model):
    """Modelo para gestionar bonos de descuento con códigos promocionales"""
    
    TIPO_DESCUENTO_CHOICES = [
        ('porcentaje', 'Porcentaje'),
        ('fijo', 'Valor Fijo'),
    ]
    
    codigo = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Código único del bono (ej: DESCUENTO50, NAVIDAD2025)"
    )
    descripcion = models.CharField(
        max_length=200, 
        help_text="Descripción del bono para uso interno"
    )
    tipo_descuento = models.CharField(
        max_length=10, 
        choices=TIPO_DESCUENTO_CHOICES, 
        default='porcentaje'
    )
    valor_descuento = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Porcentaje (0-100) o valor fijo en pesos"
    )
    valor_minimo_compra = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Valor mínimo de compra para aplicar el descuento"
    )
    fecha_inicio = models.DateTimeField(
        help_text="Fecha y hora desde cuando es válido el bono"
    )
    fecha_fin = models.DateTimeField(
        help_text="Fecha y hora hasta cuando es válido el bono"
    )
    usos_maximos = models.PositiveIntegerField(
        default=1,
        help_text="Número máximo de veces que se puede usar este código"
    )
    usos_realizados = models.PositiveIntegerField(
        default=0,
        help_text="Número de veces que ya se ha usado este código"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si el bono está activo o desactivado"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bono de Descuento"
        verbose_name_plural = "Bonos de Descuento"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        tipo_display = "%" if self.tipo_descuento == 'porcentaje' else "$"
        return f"{self.codigo} - {self.valor_descuento}{tipo_display}"
    
    def is_valid(self):
        """Verificar si el bono es válido actualmente"""
        from django.utils import timezone
        now = timezone.now()
        
        return (
            self.activo and
            self.fecha_inicio <= now <= self.fecha_fin and
            self.usos_realizados < self.usos_maximos
        )
    
    def can_be_used(self, total_compra):
        """Verificar si el bono puede ser usado para una compra específica"""
        return self.is_valid() and total_compra >= self.valor_minimo_compra
    
    def calcular_descuento(self, total_compra):
        """Calcular el monto de descuento para un total específico"""
        if not self.can_be_used(total_compra):
            return 0
        
        if self.tipo_descuento == 'porcentaje':
            descuento = (total_compra * self.valor_descuento) / 100
        else:  # 'fijo'
            descuento = self.valor_descuento
        
        # No permitir descuento mayor al total
        return min(descuento, total_compra)
    
    def usar_bono(self):
        """Registrar un uso del bono"""
        if self.usos_realizados < self.usos_maximos:
            self.usos_realizados += 1
            self.save()
            return True
        return False
    
    def get_estado_display(self):
        """Obtener el estado actual del bono para mostrar en UI"""
        if not self.activo:
            return "Desactivado"
        
        from django.utils import timezone
        now = timezone.now()
        
        if now < self.fecha_inicio:
            return "Programado"
        elif now > self.fecha_fin:
            return "Expirado"
        elif self.usos_realizados >= self.usos_maximos:
            return "Agotado"
        else:
            return "Activo"
    
    def get_estado_badge_class(self):
        """Obtener clase CSS para el badge del estado"""
        estado = self.get_estado_display()
        estado_classes = {
            'Activo': 'badge-success',
            'Programado': 'badge-info', 
            'Expirado': 'badge-secondary',
            'Agotado': 'badge-warning',
            'Desactivado': 'badge-danger',
        }
        return estado_classes.get(estado, 'badge-secondary')