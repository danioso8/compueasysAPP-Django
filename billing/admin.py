from django.contrib import admin
from .models import Invoice, InvoiceItem, MatiasConfiguration, MatiasSyncLog

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer_name', 'issue_date', 'total', 'payment_status', 'dian_status')
    list_filter = ('payment_status', 'dian_status', 'issue_date')
    search_fields = ('invoice_number', 'customer_name', 'customer_nit')
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('consecutive', 'invoice_number', 'issue_date', 'issue_time')
        }),
        ('Cliente', {
            'fields': ('customer_name', 'customer_nit', 'customer_email', 'customer_phone', 'customer_address')
        }),
        ('Totales', {
            'fields': ('subtotal', 'total_discount', 'total_tax', 'total', 'payment_status')
        }),
        ('Facturación Electrónica DIAN', {
            'fields': ('dian_status', 'cufe', 'qr_code', 'pdf_url', 'xml_url', 'matias_track_id'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product_code', 'description', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('invoice__issue_date',)
    search_fields = ('product_code', 'description', 'invoice__invoice_number')

@admin.register(MatiasConfiguration)
class MatiasConfigurationAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'test_mode', 'resolution_number', 'prefix', 'documents_available', 'last_balance_check')
    list_filter = ('is_active', 'test_mode')
    
    fieldsets = (
        ('Estado', {
            'fields': ('is_active', 'test_mode', 'connection_verified')
        }),
        ('Configuración de Facturación', {
            'fields': ('resolution_number', 'prefix', 'type_document_id', 'default_payment_method_id', 'default_means_payment_id')
        }),
        ('Balance de Documentos', {
            'fields': ('documents_available', 'documents_consumed_monthly', 'monthly_limit', 'plan_name')
        }),
        ('Opciones', {
            'fields': ('auto_send_email', 'generate_graphic_representation')
        }),
    )

@admin.register(MatiasSyncLog)
class MatiasSyncLogAdmin(admin.ModelAdmin):
    list_display = ('sync_type', 'status', 'invoice', 'created_at', 'matias_track_id')
    list_filter = ('sync_type', 'status', 'created_at')
    search_fields = ('matias_track_id', 'invoice__invoice_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
