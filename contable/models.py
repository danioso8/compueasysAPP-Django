from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import EmailValidator, MinValueValidator
import uuid

# ==========================================
# MÓDULOS DE ADMINISTRACIÓN Y SEGURIDAD
# ==========================================

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


# ============================================================================
# MODELO DE USUARIO INDEPENDIENTE PARA CONTABLE
# ============================================================================

class ContableUserManager(BaseUserManager):
    """Manager personalizado para ContableUser"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Crear un usuario normal"""
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crear un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, password, **extra_fields)


class ContableUser(AbstractBaseUser, PermissionsMixin):
    """
    Usuario independiente para el sistema contable.
    Completamente separado del User de Django y SimpleUser del e-commerce.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    
    # Campos de estado
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Campos de verificación
    email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Relaciones con nombres personalizados para evitar conflictos
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='contable_users',
        related_query_name='contable_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='contable_users',
        related_query_name='contable_user',
    )
    
    objects = ContableUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'contable_user'
        verbose_name = 'Usuario Contable'
        verbose_name_plural = 'Usuarios Contables'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name


# ============================================================================
# MODELOS DE SUSCRIPCIÓN Y USUARIOS
# ============================================================================

class Plan(models.Model):
    """Planes de suscripción del sistema contable"""
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('pro', 'Profesional'),
        ('enterprise', 'Empresarial'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_users = models.IntegerField(default=1)
    max_companies = models.IntegerField(default=1)
    max_invoices_month = models.IntegerField(default=50)
    features = models.JSONField(default=dict)  # Características específicas del plan
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.display_name
    
    class Meta:
        verbose_name = 'Plan de Suscripción'
        verbose_name_plural = 'Planes de Suscripción'


class Company(models.Model):
    """Empresas en el sistema multiempresa"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nombre de la Empresa')
    legal_name = models.CharField(max_length=200, verbose_name='Razón Social')
    tax_id = models.CharField(max_length=50, unique=True, verbose_name='NIT/RUT')
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Colombia')
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    # Configuración contable
    fiscal_year_start = models.DateField(default=timezone.now)
    currency = models.CharField(max_length=3, default='COP')
    tax_regime = models.CharField(max_length=50, default='Común')
    
    # Plan y estado
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='companies')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']


class UserProfile(models.Model):
    """Perfil extendido de usuario con roles y permisos"""
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('accountant', 'Contador'),
        ('admin', 'Administrador'),
        ('auditor', 'Auditor'),
        ('superuser', 'Superusuario'),
    ]
    
    user = models.OneToOneField(ContableUser, on_delete=models.CASCADE, related_name='profile')
    companies = models.ManyToManyField(Company, related_name='users', through='CompanyMembership')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Seguridad (movido a ContableUser, mantenido aquí para compatibilidad temporal)
    reset_token = models.CharField(max_length=100, blank=True)
    reset_token_expires = models.DateTimeField(null=True, blank=True)
    
    # Configuración personal
    language = models.CharField(max_length=5, default='es')
    timezone = models.CharField(max_length=50, default='America/Bogota')
    theme = models.CharField(max_length=20, default='light')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'


class CompanyMembership(models.Model):
    """Relación entre usuarios y empresas con roles específicos"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role_in_company = models.CharField(max_length=20, choices=UserProfile.ROLE_CHOICES)
    permissions = models.JSONField(default=dict)  # Permisos específicos por módulo
    is_default = models.BooleanField(default=False)  # Empresa por defecto al iniciar sesión
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user_profile', 'company']
        verbose_name = 'Membresía de Empresa'
        verbose_name_plural = 'Membresías de Empresa'


class AuditLog(models.Model):
    """Registro de auditoría del sistema"""
    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
        ('view', 'Visualizar'),
        ('export', 'Exportar'),
    ]
    
    user = models.ForeignKey(ContableUser, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']


# ==========================================
# CONTABILIDAD GENERAL
# ==========================================

class AccountingPeriod(models.Model):
    """Períodos contables"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='periods')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(ContableUser, on_delete=models.SET_NULL, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['company', 'start_date', 'end_date']
        ordering = ['-start_date']


class ChartOfAccounts(models.Model):
    """Plan de cuentas (catálogo de cuentas)"""
    ACCOUNT_TYPES = [
        ('asset', 'Activo'),
        ('liability', 'Pasivo'),
        ('equity', 'Patrimonio'),
        ('income', 'Ingresos'),
        ('expense', 'Gastos'),
        ('cost', 'Costos'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accounts')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    accepts_entries = models.BooleanField(default=True)  # Si acepta movimientos directos
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['company', 'code']
        ordering = ['code']
        verbose_name = 'Cuenta Contable'
        verbose_name_plural = 'Plan de Cuentas'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """Asientos contables (Libro Diario)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT)
    entry_number = models.CharField(max_length=50)
    entry_date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    is_posted = models.BooleanField(default=False)
    is_reversed = models.BooleanField(default=False)
    reversed_entry = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(ContableUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['company', 'entry_number']
        ordering = ['-entry_date', '-entry_number']
        verbose_name = 'Asiento Contable'
        verbose_name_plural = 'Asientos Contables'


class JournalEntryLine(models.Model):
    """Líneas de asientos contables"""
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT)
    description = models.CharField(max_length=200)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        verbose_name = 'Línea de Asiento'
        verbose_name_plural = 'Líneas de Asientos'


# ==========================================
# CLIENTES Y PROVEEDORES
# ==========================================

class Customer(models.Model):
    """Clientes"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_terms = models.IntegerField(default=30, help_text='Días de crédito')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'code']
        ordering = ['name']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Supplier(models.Model):
    """Proveedores"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    payment_terms = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'code']
        ordering = ['name']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# ==========================================
# PRODUCTOS E INVENTARIO
# ==========================================

class Product(models.Model):
    """Catálogo de productos"""
    UNIT_TYPES = [
        ('unit', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('liter', 'Litro'),
        ('meter', 'Metro'),
        ('box', 'Caja'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES, default='unit')
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19)  # IVA
    current_stock = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'sku']
        ordering = ['name']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
    
    def __str__(self):
        return f"{self.sku} - {self.name}"


class InventoryMovement(models.Model):
    """Movimientos de inventario"""
    MOVEMENT_TYPES = [
        ('entry', 'Entrada'),
        ('exit', 'Salida'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Traslado'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inventory_movements')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(ContableUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'


# ==========================================
# FACTURACIÓN Y VENTAS
# ==========================================

class Invoice(models.Model):
    """Facturas de venta"""
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('paid', 'Pagada'),
        ('partial', 'Pago Parcial'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Anulada'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Montos
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    
    created_by = models.ForeignKey(ContableUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['company', 'invoice_number']
        ordering = ['-invoice_date', '-invoice_number']
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"


class InvoiceLine(models.Model):
    """Líneas de factura"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        verbose_name = 'Línea de Factura'
        verbose_name_plural = 'Líneas de Factura'


class Payment(models.Model):
    """Pagos recibidos"""
    PAYMENT_METHODS = [
        ('cash', 'Efectivo'),
        ('bank_transfer', 'Transferencia Bancaria'),
        ('card', 'Tarjeta'),
        ('check', 'Cheque'),
        ('other', 'Otro'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(ContableUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'


# ==========================================
# COMPRAS
# ==========================================

class PurchaseOrder(models.Model):
    """Órdenes de compra"""
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('received', 'Recibida'),
        ('partial', 'Recepción Parcial'),
        ('cancelled', 'Anulada'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    order_number = models.CharField(max_length=50)
    order_date = models.DateField()
    expected_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(ContableUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['company', 'order_number']
        ordering = ['-order_date']
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'


class PurchaseOrderLine(models.Model):
    """Líneas de orden de compra"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19)
    line_total = models.DecimalField(max_digits=15, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0)


# ==========================================
# NÓMINA
# ==========================================

class Employee(models.Model):
    """Empleados"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    employee_code = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    hire_date = models.DateField()
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    base_salary = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'employee_code']
        ordering = ['last_name', 'first_name']
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
    
    def __str__(self):
        return f"{self.employee_code} - {self.first_name} {self.last_name}"


class Payroll(models.Model):
    """Nóminas"""
    PERIOD_TYPES = [
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobada'),
        ('paid', 'Pagada'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payrolls')
    payroll_number = models.CharField(max_length=50)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_by = models.ForeignKey(ContableUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'payroll_number']
        ordering = ['-start_date']
        verbose_name = 'Nómina'
        verbose_name_plural = 'Nóminas'


class PayrollLine(models.Model):
    """Líneas de nómina (detalles por empleado)"""
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='lines')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    base_salary = models.DecimalField(max_digits=15, decimal_places=2)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bonuses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=15, decimal_places=2)
    health_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    pension_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2)


# ==========================================
# ACTIVOS FIJOS
# ==========================================

class FixedAsset(models.Model):
    """Activos fijos"""
    DEPRECIATION_METHODS = [
        ('straight_line', 'Línea Recta'),
        ('declining_balance', 'Saldo Decreciente'),
        ('sum_of_years', 'Suma de Dígitos'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fixed_assets')
    asset_code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=15, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    useful_life_years = models.IntegerField()
    depreciation_method = models.CharField(max_length=20, choices=DEPRECIATION_METHODS, default='straight_line')
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    location = models.CharField(max_length=200, blank=True)
    responsible = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['company', 'asset_code']
        ordering = ['name']
        verbose_name = 'Activo Fijo'
        verbose_name_plural = 'Activos Fijos'
    
    def __str__(self):
        return f"{self.asset_code} - {self.name}"


class Depreciation(models.Model):
    """Registro de depreciaciones"""
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='depreciations')
    period_start = models.DateField()
    period_end = models.DateField()
    depreciation_amount = models.DecimalField(max_digits=15, decimal_places=2)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-period_start']
        verbose_name = 'Depreciación'
        verbose_name_plural = 'Depreciaciones'


# ==========================================
# REPORTES Y CONFIGURACIONES
# ==========================================

class TaxRate(models.Model):
    """Tasas de impuestos"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_rates')
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Tasa de Impuesto'
        verbose_name_plural = 'Tasas de Impuestos'


class BankAccount(models.Model):
    """Cuentas bancarias"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50)
    currency = models.CharField(max_length=3, default='COP')
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'


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