"""
Vistas para el módulo de Facturación - CompuEasys
Incluye Facturación Normal y Electrónica (Matias API)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction, models
from django.utils import timezone
from decimal import Decimal
import json

from .models import Invoice, InvoiceItem, MatiasConfiguration, MatiasSyncLog
from core.models import ProductStore
from .services.matias_client import matias_client


# ==================== CONFIGURACIÓN MATIAS API ====================

def matias_config(request):
    """Configuración de Matias API para facturación electrónica"""
    config, created = MatiasConfiguration.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        # Guardar configuración
        config.is_active = request.POST.get('is_active') == 'on'
        config.test_mode = request.POST.get('test_mode') == 'on'
        config.auto_send_email = request.POST.get('auto_send_email') == 'on'
        config.generate_graphic_representation = request.POST.get('generate_graphic_representation') == 'on'
        
        config.resolution_number = request.POST.get('resolution_number', '')
        config.prefix = request.POST.get('prefix', '')
        config.default_payment_method_id = int(request.POST.get('default_payment_method_id', 1))
        config.default_means_payment_id = int(request.POST.get('default_means_payment_id', 10))
        config.type_document_id = int(request.POST.get('type_document_id', 1))
        
        # Datos de resolución
        resolution_date = request.POST.get('resolution_date')
        if resolution_date:
            config.resolution_date = resolution_date
        
        config.technical_key = request.POST.get('technical_key', '')
        
        from_number = request.POST.get('from_number')
        if from_number:
            config.from_number = int(from_number)
        
        to_number = request.POST.get('to_number')
        if to_number:
            config.to_number = int(to_number)
        
        config.save()
        messages.success(request, 'Configuración de Matias API guardada exitosamente')
        return redirect('billing:matias_config')
    
    context = {
        'config': config,
        'matias_email': matias_client.email,
    }
    return render(request, 'billing/matias_config.html', context)


@require_POST
def matias_test_connection(request):
    """Prueba la conexión con Matias API"""
    success, message = matias_client.test_connection()
    
    if success:
        # Actualizar configuración
        config = MatiasConfiguration.objects.first()
        if config:
            config.connection_verified = True
            config.last_connection_test = timezone.now()
            config.last_error = ''
            config.save()
        
        return JsonResponse({
            'success': True,
            'message': message
        })
    else:
        # Guardar error
        config = MatiasConfiguration.objects.first()
        if config:
            config.connection_verified = False
            config.last_connection_test = timezone.now()
            config.last_error = message
            config.save()
        
        return JsonResponse({
            'success': False,
            'message': message
        })


# ==================== FACTURAS - LISTADO Y CRUD ====================

def invoice_list(request):
    """Lista todas las facturas"""
    invoices = Invoice.objects.all().order_by('-issue_date', '-consecutive')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        invoices = invoices.filter(payment_status=status_filter)
    
    dian_filter = request.GET.get('dian_status')
    if dian_filter:
        invoices = invoices.filter(dian_status=dian_filter)
    
    search = request.GET.get('search')
    if search:
        invoices = invoices.filter(
            models.Q(invoice_number__icontains=search) |
            models.Q(customer_name__icontains=search) |
            models.Q(customer_nit__icontains=search)
        )
    
    context = {
        'invoices': invoices,
        'status_filter': status_filter,
        'dian_filter': dian_filter,
        'search': search,
    }
    return render(request, 'billing/invoice_list.html', context)


def invoice_detail(request, invoice_id):
    """Detalle de una factura"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = invoice.items.all()
    
    context = {
        'invoice': invoice,
        'items': items,
    }
    return render(request, 'billing/invoice_detail.html', context)


@transaction.atomic
def invoice_create(request):
    """Crear una nueva factura"""
    if request.method == 'POST':
        try:
            # Obtener configuración
            config = MatiasConfiguration.objects.first()
            
            # Calcular consecutive
            last_invoice = Invoice.objects.order_by('-consecutive').first()
            consecutive = (last_invoice.consecutive + 1) if last_invoice else 1
            
            # Crear factura
            invoice = Invoice()
            invoice.consecutive = consecutive
            
            # Cliente
            invoice.customer_name = request.POST.get('customer_name')
            invoice.customer_nit = request.POST.get('customer_nit', '')
            invoice.customer_email = request.POST.get('customer_email', '')
            invoice.customer_phone = request.POST.get('customer_phone', '')
            invoice.customer_address = request.POST.get('customer_address', '')
            
            # Pago
            invoice.payment_form = int(request.POST.get('payment_form', 1))
            invoice.payment_method = int(request.POST.get('payment_method', 10))
            
            # Factura electrónica
            invoice.is_electronic = request.POST.get('is_electronic') == 'on'
            
            # Usuario
            invoice.created_by = request.session.get('superuser_username', 'Sistema')
            
            invoice.save()
            
            # Crear items
            items_data = json.loads(request.POST.get('items', '[]'))
            
            for item_data in items_data:
                item = InvoiceItem()
                item.invoice = invoice
                
                # Si tiene product_id, buscar el producto
                product_id = item_data.get('product_id')
                if product_id:
                    try:
                        product = ProductStore.objects.get(id=product_id)
                        item.product = product
                        item.product_code = str(product.id)
                        item.description = product.name
                        item.unit_price = Decimal(str(product.price))
                    except ProductStore.DoesNotExist:
                        pass
                
                # Si no tiene producto, usar datos manuales
                if not item.product_code:
                    item.product_code = item_data.get('code', 'N/A')
                    item.description = item_data.get('description', '')
                    item.unit_price = Decimal(str(item_data.get('unit_price', 0)))
                
                item.quantity = Decimal(str(item_data.get('quantity', 1)))
                item.discount_percentage = Decimal(str(item_data.get('discount_percentage', 0)))
                item.tax_percentage = Decimal(str(item_data.get('tax_percentage', 19)))
                
                item.save()
                
                # **DESCUENTO DE STOCK AUTOMÁTICO**
                if item.product:
                    product = item.product
                    quantity_to_deduct = int(item.quantity)
                    
                    if product.stock >= quantity_to_deduct:
                        product.stock -= quantity_to_deduct
                        
                        # Si queda 1 o menos, marcar como agotado
                        if product.stock <= 1:
                            product.agotado = True
                        
                        product.save()
                        print(f"✅ Stock actualizado: {product.name} - Nuevo stock: {product.stock}")
                    else:
                        messages.warning(request, f"Stock insuficiente para {product.name}. Facturado de todos modos.")
            
            # Calcular totales
            invoice.calculate_totals()
            
            messages.success(request, f'Factura {invoice.invoice_number} creada exitosamente')
            
            # Si es electrónica, redirigir a enviar
            if invoice.is_electronic:
                messages.info(request, 'No olvides enviar la factura a DIAN')
                return redirect('billing:invoice_detail', invoice_id=invoice.id)
            
            return redirect('billing:invoice_detail', invoice_id=invoice.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear factura: {str(e)}')
            print(f"Error creando factura: {e}")
            return redirect('billing:invoice_list')
    
    # GET - Mostrar formulario
    config = MatiasConfiguration.objects.first()
    
    context = {
        'config': config,
    }
    return render(request, 'billing/invoice_create.html', context)


def invoice_edit(request, invoice_id):
    """Editar una factura existente"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # No permitir editar si ya fue enviada a DIAN y aprobada
    if invoice.dian_status == 'approved':
        messages.error(request, 'No se puede editar una factura ya aprobada por DIAN')
        return redirect('billing:invoice_detail', invoice_id=invoice.id)
    
    if request.method == 'POST':
        # Actualizar datos
        invoice.customer_name = request.POST.get('customer_name')
        invoice.customer_nit = request.POST.get('customer_nit', '')
        invoice.customer_email = request.POST.get('customer_email', '')
        invoice.customer_phone = request.POST.get('customer_phone', '')
        invoice.customer_address = request.POST.get('customer_address', '')
        invoice.notes = request.POST.get('notes', '')
        
        invoice.save()
        messages.success(request, 'Factura actualizada exitosamente')
        return redirect('billing:invoice_detail', invoice_id=invoice.id)
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'billing/invoice_edit.html', context)


@require_POST
def invoice_delete(request, invoice_id):
    """Eliminar una factura"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # No permitir eliminar si está aprobada por DIAN
    if invoice.dian_status == 'approved':
        messages.error(request, 'No se puede eliminar una factura aprobada por DIAN')
        return redirect('billing:invoice_detail', invoice_id=invoice.id)
    
    invoice_number = invoice.invoice_number
    invoice.delete()
    
    messages.success(request, f'Factura {invoice_number} eliminada exitosamente')
    return redirect('billing:invoice_list')


# ==================== FACTURACIÓN ELECTRÓNICA - MATIAS API ====================

@require_POST
def send_invoice_matias(request, invoice_id):
    """Envía una factura a DIAN vía Matias API"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Verificar que es electrónica
    if not invoice.is_electronic:
        return JsonResponse({
            'success': False,
            'message': 'Esta factura no está marcada como electrónica'
        })
    
    # Verificar que no esté ya aprobada
    if invoice.dian_status == 'approved':
        return JsonResponse({
            'success': False,
            'message': 'Esta factura ya fue aprobada por DIAN'
        })
    
    # Obtener configuración
    config = MatiasConfiguration.objects.first()
    if not config or not config.is_active:
        return JsonResponse({
            'success': False,
            'message': 'La facturación electrónica no está configurada o activa'
        })
    
    # Construir payload para Matias API
    try:
        items = invoice.items.all()
        
        payload = {
            "type_document_id": config.type_document_id,
            "number": invoice.consecutive,
            "sync": True,
            "date": invoice.issue_date.strftime('%Y-%m-%d'),
            "time": invoice.issue_time.strftime('%H:%M:%S'),
            
            "resolution_number": config.resolution_number,
            "prefix": config.prefix,
            "resolution_date": config.resolution_date.strftime('%Y-%m-%d') if config.resolution_date else "",
            "technical_key": config.technical_key,
            "from_number": config.from_number or 1,
            "to_number": config.to_number or 1000000,
            
            "payment_method_id": invoice.payment_form,
            "means_payment_id": invoice.payment_method,
            
            "customer": {
                "identification_number": invoice.customer_nit or "222222222222",
                "type_document_identification_id": 13,  # CC por defecto
                "type_organization_id": 2,  # Persona Natural
                "name": invoice.customer_name,
                "phone": invoice.customer_phone or "3000000000",
                "address": invoice.customer_address or "Dirección no especificada",
                "email": invoice.customer_email or "cliente@example.com",
                "merchant_registration": invoice.customer_nit or "222222222222-1",
                "municipality_id": 149,  # Código DANE por defecto (ajustar según necesidad)
                "type_regime_id": 49,  # No responsable IVA
                "type_liability_id": 117,  # No responsable
                "organization_id": 1,
            },
            
            "lines": [],
            
            "legal_monetary_totals": {
                "line_extension_amount": float(invoice.subtotal),
                "tax_exclusive_amount": float(invoice.subtotal - invoice.total_discount),
                "tax_inclusive_amount": float(invoice.total),
                "allowance_total_amount": float(invoice.total_discount),
                "payable_amount": float(invoice.total),
            },
            
            "payments": [
                {
                    "payment_form_id": invoice.payment_form,
                    "payment_method_id": invoice.payment_form,
                    "means_payment_id": invoice.payment_method,
                    "value_paid": float(invoice.total),
                }
            ],
            
            "Ambiente": "2" if config.test_mode else "1",
        }
        
        # Agregar líneas de productos
        for item in items:
            line = {
                "invoiced_quantity": float(item.quantity),
                "line_extension_amount": float(item.subtotal),
                "free_of_charge_indicator": False,
                "description": item.description,
                "code": item.product_code,
                "type_item_identifications_id": 4,
                "price_amount": float(item.unit_price),
                "base_quantity": float(item.quantity),
                "quantity_units_id": 642,
            }
            
            # Agregar impuestos si aplican
            if item.tax_percentage > 0:
                line["tax_totals"] = [
                    {
                        "tax_id": 1,  # IVA
                        "tax_amount": float(item.tax_amount),
                        "taxable_amount": float(item.subtotal - item.discount_amount),
                        "percent": float(item.tax_percentage),
                    }
                ]
            
            payload["lines"].append(line)
        
        # Crear log de sincronización
        sync_log = MatiasSyncLog.objects.create(
            sync_type='invoice',
            status='pending',
            invoice=invoice,
            request_payload=payload
        )
        
        # Enviar a Matias API
        success, response_data = matias_client.send_invoice(payload)
        
        # Actualizar log
        sync_log.response_data = response_data
        sync_log.http_status_code = response_data.get('http_status', 200 if success else 500)
        
        if success:
            # Respuesta exitosa de Matias
            sync_log.status = 'success'
            sync_log.status_code = response_data.get('StatusCode', '00')
            sync_log.status_message = response_data.get('StatusMessage', 'Procesado correctamente')
            sync_log.matias_track_id = response_data.get('trackId', '')
            
            # Actualizar factura
            invoice.dian_status = 'approved' if response_data.get('StatusCode') == '00' else 'processing'
            invoice.cufe = response_data.get('cufe', '')
            invoice.qr_code = response_data.get('qrCode', '')
            invoice.pdf_url = response_data.get('pdfUrl', '')
            invoice.xml_url = response_data.get('xmlUrl', '')
            invoice.matias_track_id = response_data.get('trackId', '')
            invoice.dian_response = response_data
            invoice.save()
            
            sync_log.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Factura enviada exitosamente a DIAN',
                'cufe': invoice.cufe,
                'track_id': invoice.matias_track_id,
            })
        else:
            # Error en envío
            sync_log.status = 'error'
            sync_log.error_message = response_data.get('error', 'Error desconocido')
            sync_log.save()
            
            invoice.dian_status = 'error'
            invoice.dian_response = response_data
            invoice.save()
            
            error_msg = response_data.get('error', 'Error al enviar factura')
            if 'details' in response_data:
                details = response_data['details']
                if isinstance(details, dict) and 'Errors' in details:
                    errors_list = details['Errors']
                    error_msg = f"{error_msg}: {', '.join([e.get('Message', '') for e in errors_list])}"
            
            return JsonResponse({
                'success': False,
                'message': error_msg
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Excepción al enviar factura: {str(e)}'
        })


@require_POST
def matias_check_status(request, invoice_id):
    """Consulta el estado de una factura en DIAN"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if not invoice.matias_track_id:
        return JsonResponse({
            'success': False,
            'message': 'Esta factura no tiene trackId de Matias'
        })
    
    success, response_data = matias_client.check_invoice_status(invoice.matias_track_id)
    
    if success:
        # Actualizar estado
        status_code = response_data.get('StatusCode', '')
        if status_code == '00':
            invoice.dian_status = 'approved'
        elif status_code == '98':
            invoice.dian_status = 'processing'
        elif status_code == '99':
            invoice.dian_status = 'rejected'
        
        invoice.dian_response = response_data
        invoice.save()
        
        return JsonResponse({
            'success': True,
            'message': response_data.get('StatusMessage', 'Estado consultado'),
            'status': invoice.get_dian_status_display()
        })
    else:
        return JsonResponse({
            'success': False,
            'message': response_data.get('error', 'Error al consultar estado')
        })


def matias_download_pdf(request, invoice_id):
    """Descarga el PDF de la representación gráfica DIAN"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if invoice.pdf_url:
        return redirect(invoice.pdf_url)
    else:
        messages.error(request, 'Esta factura no tiene PDF disponible')
        return redirect('billing:invoice_detail', invoice_id=invoice.id)


def matias_download_xml(request, invoice_id):
    """Descarga el XML firmado de la factura DIAN"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if invoice.xml_url:
        return redirect(invoice.xml_url)
    else:
        messages.error(request, 'Esta factura no tiene XML disponible')
        return redirect('billing:invoice_detail', invoice_id=invoice.id)


# ==================== AJAX - BÚSQUEDA DE PRODUCTOS ====================

def search_products_ajax(request):
    """Busca productos de la tienda para agregar a factura"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    products = ProductStore.objects.filter(
        models.Q(name__icontains=query) |
        models.Q(description__icontains=query)
    ).filter(
        stock__gt=0  # Solo productos con stock
    )[:20]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'code': str(product.id),
            'price': float(product.price),
            'stock': product.stock,
            'image_url': product.imagen.url if product.imagen else None,
        })
    
    return JsonResponse({'products': results})


# ==================== PDF FACTURA NORMAL ====================

def invoice_pdf(request, invoice_id):
    """Genera PDF de factura normal (no electrónica)"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = invoice.items.all()
    
    # Aquí iría la lógica para generar PDF
    # Por ahora, mostrar template simple
    context = {
        'invoice': invoice,
        'items': items,
    }
    return render(request, 'billing/invoice_pdf.html', context)
