"""
Modelos de Facturación para CompuEasys
Incluye Facturación Normal y Facturación Electrónica (Matias API)
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from core.models import ProductStore


class MatiasConfiguration(models.Model):
    """
    Configuración global de Matias API para facturación electrónica DIAN.
    
    IMPORTANTE: Las credenciales OAuth2 (email/password) se configuran en .env:
    - MATIAS_EMAIL
    - MATIAS_PASSWORD
    - MATIAS_API_BASE_URL
    
    Este modelo almacena la configuración específica de facturación:
    - Resolución DIAN (número, prefijo)
    - Opciones de facturación (método de pago, etc.)
    - Estado de activación
    """
    
    # Estado
    is_active = models.BooleanField(
        default=False,
        verbose_name="Facturación Electrónica Activa",
        help_text="Habilitar/deshabilitar facturación electrónica"
    )
    test_mode = models.BooleanField(
        default=True,
        verbose_name="Modo de Prueba",
        help_text="Modo de prueba (ambiente 2=pruebas, 1=producción)"
    )
    
   # Opciones
    auto_send_email = models.BooleanField(
        default=True,
        help_text="Enviar automáticamente facturas por email al cliente"
    )
    generate_graphic_representation = models.BooleanField(
        default=False,
        help_text="Generar representación gráfica (PDF) en Matias"
    )
    
    # Configuración de pago por defecto
    default_payment_method_id = models.IntegerField(
        default=1,
        choices=[
            (1, 'Contado'),
            (2, 'Crédito'),
        ],
        help_text="Método de pago por defecto"
    )
    default_means_payment_id = models.IntegerField(
        default=10,
        help_text="Medio de pago por defecto (10=Efectivo, 48=TarjetaCrédito, 49=TarjetaDébito, 31=Transferencia)"
    )
    
    # Resolución DIAN
    resolution_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Número de Resolución DIAN",
        help_text="Número de resolución DIAN registrado en Matias"
    )
    prefix = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Prefijo",
        help_text="Prefijo de facturación registrado en Matias (ej: FE, SETP)"
    )
    resolution_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Resolución"
    )
    technical_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Clave Técnica",
        help_text="Clave técnica proporcionada por la DIAN"
    )
    from_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Número Inicial",
        help_text="Primer número del rango autorizado"
    )
    to_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Número Final",
        help_text="Último número del rango autorizado"
    )
    
    # Tipo de documento
    type_document_id = models.IntegerField(
        default=1,
        choices=[
            (1, 'Factura de Venta Nacional (01)'),
            (7, 'Documento Soporte (07)'),
        ],
        help_text="Tipo de documento por defecto"
    )
    
    # Balance y límites
    documents_available = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Documentos disponibles para emitir"
    )
    documents_consumed_monthly = models.IntegerField(
        default=0,
        help_text="Documentos consumidos este mes"
    )
    monthly_limit = models.IntegerField(
        default=0,
        help_text="Límite mensual de documentos"
    )
    plan_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre del plan en Matias"
    )
    last_balance_check = models.DateTimeField(null=True, blank=True)
    
    # Estado de conexión
    connection_verified = models.BooleanField(
        default=False,
        help_text="Conexión verificada exitosamente"
    )
    last_connection_test = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, help_text="Último error de conexión")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración Matias API"
        verbose_name_plural = "Configuraciones Matias API"
        db_table = "billing_matias_configuration"
    
    def __str__(self):
        status = "✅ Activa" if self.is_active else "⚠️ Inactiva"
        return f"Matias Config - CompuEasys [{status}]"


class Invoice(models.Model):
    """
    Factura - Puede ser Normal o Electrónica (DIAN)
    """
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagada'),
        ('cancelled', 'Cancelada'),
    ]
    
    DIAN_STATUS_CHOICES = [
        ('pending', 'Pendiente envío DIAN'),
        ('processing', 'Procesando en DIAN'),
        ('approved', 'Aprobada por DIAN'),
        ('rejected', 'Rechazada por DIAN'),
        ('error', 'Error en envío'),
        ('not_applicable', 'No aplica (Factura Normal)'),
    ]
    
    # Información Básica
    consecutive = models.PositiveIntegerField(
        verbose_name="Consecutivo",
        help_text="Número consecutivo interno"
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de Factura",
        help_text="Prefijo + Consecutivo (ej: FE-001)"
    )
    issue_date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Emisión"
    )
    issue_time = models.TimeField(
        default=timezone.now,
        verbose_name="Hora de Emisión"
    )
    
    # Cliente
    customer_name = models.CharField(
        max_length=300,
        verbose_name="Nombre del Cliente"
    )
    customer_nit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="NIT/CC del Cliente"
    )
    customer_email = models.EmailField(
        blank=True,
        verbose_name="Email del Cliente"
    )
    customer_phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Teléfono del Cliente"
    )
    customer_address = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Dirección del Cliente"
    )
    
    # Formas de Pago
    payment_form = models.IntegerField(
        default=1,
        choices=[
            (1, 'Contado'),
            (2, 'Crédito'),
        ],
        verbose_name="Forma de Pago"
    )
    payment_method = models.IntegerField(
        default=10,
        verbose_name="Medio de Pago",
        help_text="10=Efectivo, 31=Transferencia, 48=TarjetaCrédito, 49=TarjetaDébito"
    )
    
    # Totales
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Subtotal (sin impuestos)"
    )
    total_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total Descuentos"
    )
    total_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total Impuestos (IVA)"
    )
    total_other_taxes = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Otros Impuestos"
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total a Pagar"
    )
    
    # Estado de Pago
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Estado de Pago"
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Pago"
    )
    
    # Facturación Electrónica DIAN
    is_electronic = models.BooleanField(
        default=False,
        verbose_name="Es Factura Electrónica",
        help_text="Marcar si se enviará a DIAN vía Matias API"
    )
    dian_status = models.CharField(
        max_length=20,
        choices=DIAN_STATUS_CHOICES,
        default='not_applicable',
        verbose_name="Estado DIAN"
    )
    cufe = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="CUFE",
        help_text="Código Único de Factura Electrónica"
    )
    qr_code = models.TextField(
        blank=True,
        verbose_name="Código QR",
        help_text="Data URL del código QR generado por DIAN"
    )
    pdf_url = models.URLField(
        blank=True,
        max_length=500,
        verbose_name="URL del PDF DIAN"
    )
    xml_url = models.URLField(
        blank=True,
        max_length=500,
        verbose_name="URL del XML DIAN"
    )
    matias_track_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Matias Track ID",
        help_text="ID de seguimiento en Matias API"
    )
    dian_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Respuesta DIAN (JSON)",
        help_text="Respuesta completa de Matias API"
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        verbose_name="Notas/Observaciones"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó la factura"
    )
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        db_table = "billing_invoice"
        ordering = ['-issue_date', '-consecutive']
        indexes = [
            models.Index(fields=['-issue_date']),
            models.Index(fields=['customer_nit']),
            models.Index(fields=['dian_status']),
        ]
    
    def __str__(self):
        return f"Factura {self.invoice_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        # Si no tiene invoice_number, generarlo
        if not self.invoice_number:
            # Obtener configuración para el prefijo
            try:
                config = MatiasConfiguration.objects.first()
                prefix = config.prefix if config and config.prefix else 'FV'
            except:
                prefix = 'FV'
            
            self.invoice_number = f"{prefix}-{self.consecutive:05d}"
        
        # Si es electrónica y está pendiente, cambiar estado
        if self.is_electronic and self.dian_status == 'not_applicable':
            self.dian_status = 'pending'
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calcula los totales basándose en los items"""
        items = self.items.all()
        
        self.subtotal = sum(item.subtotal for item in items)
        self.total_discount = sum(item.discount_amount for item in items)
        self.total_tax = sum(item.tax_amount for item in items)
        self.total = self.subtotal - self.total_discount + self.total_tax + self.total_other_taxes
        
        self.save()


class InvoiceItem(models.Model):
    """
    Item/Línea de Factura - Productos facturados
    """
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Factura"
    )
    product = models.ForeignKey(
        ProductStore,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Producto",
        help_text="Producto de la tienda (si aplica)"
    )
    
    # Información del producto (se guarda en el momento de la factura)
    product_code = models.CharField(
        max_length=100,
        verbose_name="Código del Producto"
    )
    description = models.CharField(
        max_length=500,
        verbose_name="Descripción"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Cantidad"
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Precio Unitario"
    )
    
    # Descuentos e Impuestos
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Porcentaje de Descuento"
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Valor del Descuento"
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('19.00'),
        verbose_name="Porcentaje de IVA"
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Valor del IVA"
    )
    
    # Totales
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Subtotal (antes de descuento e IVA)"
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total Línea (con descuento e IVA)"
    )
    
    class Meta:
        verbose_name = "Item de Factura"
        verbose_name_plural = "Items de Factura"
        db_table = "billing_invoice_item"
        ordering = ['id']
    
    def __str__(self):
        return f"{self.description} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calcular totales automáticamente
        self.subtotal = self.quantity * self.unit_price
        self.discount_amount = self.subtotal * (self.discount_percentage / Decimal('100'))
        base_after_discount = self.subtotal - self.discount_amount
        self.tax_amount = base_after_discount * (self.tax_percentage / Decimal('100'))
        self.line_total = base_after_discount + self.tax_amount
        
        super().save(*args, **kwargs)


class MatiasSyncLog(models.Model):
    """
    Log de sincronización con Matias API
    Registra cada intento de envío de documento electrónico
    """
    
    SYNC_TYPES = [
        ('invoice', 'Factura'),
        ('credit_note', 'Nota Crédito'),
        ('debit_note', 'Nota Débito'),
        ('status_check', 'Consulta Estado'),
    ]
    
    SYNC_STATUS = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('in_process_dian', 'En Proceso DIAN (StatusCode 98)'),
        ('success', 'Exitoso'),
        ('error', 'Error'),
        ('rejected', 'Rechazado por DIAN'),
        ('timeout', 'Timeout - Aplicar Contingencia'),
        ('duplicate', 'Documento Duplicado'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=SYNC_STATUS, default='pending')
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matias_syncs'
    )
    
    # Respuesta de Matias API
    matias_track_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="trackId devuelto por Matias para consultas"
    )
    status_code = models.CharField(
        max_length=10,
        blank=True,
        help_text="Código de respuesta (00=OK, 98=EnProceso, 99=Rechazado)"
    )
    status_message = models.TextField(
        blank=True,
        help_text="Mensaje de respuesta de Matias/DIAN"
    )
    
    # Response completo
    request_payload = models.JSONField(
        null=True,
        blank=True,
        help_text="Payload enviado a Matias"
    )
    response_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Respuesta completa de Matias API"
    )
    
    # Errores
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error (si aplica)"
    )
    http_status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="Código HTTP de la respuesta"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Log de Sincronización Matias"
        verbose_name_plural = "Logs de Sincronización Matias"
        db_table = "billing_matias_sync_log"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()} [{self.created_at.strftime('%Y-%m-%d %H:%M')}]"
