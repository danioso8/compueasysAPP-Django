
from django.db import models
from django.contrib.auth.models import User

class Tenant(models.Model):
    nombre = models.CharField(max_length=100)
    email_contacto = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

# Create your models here.



class StoreVisit(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    user = models.ForeignKey('SimpleUser', blank=True, null=True, on_delete=models.SET_NULL)
    visit_type = models.CharField(max_length=20, default='store', choices=[
        ('home', 'Home Page'),
        ('store', 'Store/Tienda'),
        ('product_detail', 'Product Detail'),
        ('cart', 'Carrito'),
        ('checkout', 'Checkout/Pago')
    ])
    product_id = models.IntegerField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

class Category(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
class Type(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class proveedor(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    cedulaOnita = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class ProductStore(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
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
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
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
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
    galeria = models.ImageField(upload_to='galeria/')
    product = models.ForeignKey(ProductStore, related_name='galeria', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Imagen {self.id}"    

class SimpleUser(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
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
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
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
        ('contraentrega', 'Contra Entrega (Efectivo)'),
        ('recoger_tienda', 'Recoger en Tienda (Efectivo)'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
        ('wompi', 'Pago Wompi'),
        ('efectivo', 'Pago en Efectivo'),  # Mantener por compatibilidad
    ]
    
    # Forma de entrega
    FORMA_ENTREGA_CHOICES = [
        ('domicilio', 'Entrega a Domicilio'),
        ('tienda', 'Recoger en Tienda'),
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
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo')
    forma_entrega = models.CharField(max_length=20, choices=FORMA_ENTREGA_CHOICES, default='domicilio')
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


class VerificationToken(models.Model):
    """Modelo para tokens de verificación por email"""
    user = models.ForeignKey(SimpleUser, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=6, help_text="Código de 6 dígitos")
    token_type = models.CharField(max_length=20, choices=[
        ('profile_update', 'Actualización de Perfil'),
        ('password_change', 'Cambio de Contraseña'),
        ('email_change', 'Cambio de Email'),
    ])
    pending_data = models.JSONField(help_text="Datos pendientes de aplicar")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Token de Verificación"
        verbose_name_plural = "Tokens de Verificación"
        ordering = ['-created_at']
    
    def is_valid(self):
        """Verificar si el token es válido"""
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Token {self.token} - {self.get_token_type_display()}"


class Conversation(models.Model):
    """Modelo para conversaciones entre usuarios y soporte"""
    user = models.ForeignKey(SimpleUser, on_delete=models.CASCADE, related_name='conversations')
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=[
        ('open', 'Abierta'),
        ('closed', 'Cerrada'),
        ('waiting_customer', 'Esperando Cliente'),
        ('waiting_support', 'Esperando Soporte'),
    ], default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Conversación"
        verbose_name_plural = "Conversaciones"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversación #{self.id} - {self.subject}"
    
    @property
    def last_message(self):
        last_msg = self.messages.last()
        return last_msg.message[:50] + "..." if last_msg and len(last_msg.message) > 50 else last_msg.message if last_msg else "No hay mensajes"
    
    @property
    def unread_count(self):
        return self.messages.filter(is_admin=True, is_read=False).count()


class ConversationMessage(models.Model):
    """Modelo para mensajes dentro de conversaciones"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(SimpleUser, on_delete=models.CASCADE, null=True, blank=True)
    admin_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_admin = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mensaje de Conversación"
        verbose_name_plural = "Mensajes de Conversación"
        ordering = ['created_at']
    
    def __str__(self):
        sender = "Admin" if self.is_admin else self.user.email if self.user else "Usuario"
        return f"{sender}: {self.message[:50]}..."

class StockNotification(models.Model):
    """
    Modelo para notificaciones de stock
    Permite a los usuarios registrarse para recibir alertas cuando un producto esté disponible
    """
    NOTIFICATION_TYPES = [
        ('stock_available', 'Producto Disponible'),
        ('price_drop', 'Bajada de Precio'),
        ('back_in_stock', 'Regreso en Stock'),
        ('low_stock', 'Stock Bajo'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('failed', 'Falló'),
    ]
    
    product = models.ForeignKey(ProductStore, on_delete=models.CASCADE, related_name='stock_notifications')
    email = models.EmailField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='stock_available')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(SimpleUser, on_delete=models.CASCADE, null=True, blank=True)
    
    # Opciones adicionales de notificación
    notify_price_drop = models.BooleanField(default=False)
    target_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    notify_low_stock = models.BooleanField(default=False)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    
    class Meta:
        unique_together = ['product', 'email', 'notification_type']
        verbose_name = "Notificación de Stock"
        verbose_name_plural = "Notificaciones de Stock"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.product.name} para {self.email}"

class NotificationLog(models.Model):
    """
    Registro de todas las notificaciones enviadas
    """
    stock_notification = models.ForeignKey(StockNotification, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    email_subject = models.CharField(max_length=200)
    
    class Meta:
        verbose_name = "Log de Notificación"
        verbose_name_plural = "Logs de Notificaciones"
        ordering = ['-sent_at']
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.email_subject} - {self.sent_at.strftime('%d/%m/%Y %H:%M')}"


class Project(models.Model):
    """
    Modelo para gestionar proyectos de desarrollo
    """
    STATUS_CHOICES = [
        ('planning', 'En Planificación'),
        ('development', 'En Desarrollo'),
        ('testing', 'En Pruebas'),
        ('completed', 'Completado'),
        ('paused', 'Pausado'),
    ]
    
    # Información básica
    name = models.CharField(max_length=200, verbose_name="Nombre del Proyecto")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(verbose_name="Descripción")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name="Estado")
    
    # Imágenes
    main_image = models.ImageField(upload_to='projects/', blank=True, null=True, verbose_name="Imagen Principal")
    screenshot_1 = models.ImageField(upload_to='projects/screenshots/', blank=True, null=True, verbose_name="Captura 1")
    screenshot_2 = models.ImageField(upload_to='projects/screenshots/', blank=True, null=True, verbose_name="Captura 2")
    screenshot_3 = models.ImageField(upload_to='projects/screenshots/', blank=True, null=True, verbose_name="Captura 3")
    
    # Tecnologías
    frontend_tech = models.CharField(max_length=300, verbose_name="Tecnología Frontend", 
                                     help_text="Ej: React, Vue.js, Bootstrap")
    backend_tech = models.CharField(max_length=300, verbose_name="Tecnología Backend",
                                    help_text="Ej: Django, Node.js, Python")
    database = models.CharField(max_length=200, verbose_name="Base de Datos",
                                help_text="Ej: PostgreSQL, MySQL, MongoDB")
    authentication = models.CharField(max_length=200, verbose_name="Sistema de Autenticación",
                                      help_text="Ej: JWT, OAuth, Django Auth")
    
    # Componentes principales
    main_components = models.TextField(verbose_name="Componentes Principales",
                                       help_text="Separa cada componente con una línea")
    
    # Información adicional
    client = models.CharField(max_length=200, blank=True, verbose_name="Cliente")
    project_url = models.URLField(blank=True, verbose_name="URL del Proyecto")
    github_url = models.URLField(blank=True, verbose_name="Repositorio GitHub")
    
    # Fechas
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(blank=True, null=True, verbose_name="Fecha de Finalización")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Control
    is_featured = models.BooleanField(default=False, verbose_name="Proyecto Destacado")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.IntegerField(default=0, verbose_name="Orden de Visualización")
    
    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-order', '-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_components_list(self):
        """Devuelve los componentes como una lista"""
        return [comp.strip() for comp in self.main_components.split('\n') if comp.strip()]