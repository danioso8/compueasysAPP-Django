try:
    from dashboard.models import WompiConfig
    wompi_config = WompiConfig.objects.first()
    if wompi_config:
        from django.conf import settings
        settings.WOMPI_PUBLIC_KEY = wompi_config.public_key
        settings.WOMPI_PRIVATE_KEY = wompi_config.private_key
        settings.WOMPI_ENVIRONMENT = wompi_config.environment
        settings.WOMPI_BASE_URL = wompi_config.base_url
except Exception as e:
    print(f"[WOMPI CONFIG] No se pudo cargar configuración global: {e}")
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q, Sum
from django.db import models
from django.http import JsonResponse

# Geolocalización opcional - puede ser removido sin afectar funcionalidad
try:
    from .geolocation_helper import create_visit_with_location
    GEOLOCATION_ENABLED = True
except ImportError:
    GEOLOCATION_ENABLED = False
    create_visit_with_location = None
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail  
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import urllib.parse
from django.http import JsonResponse, HttpResponseRedirect
from dashboard.models import register_superuser
from .models import Category, StoreVisit, Type, Galeria, SimpleUser, Pedido, ProductVariant, ProductStore as Product, PedidoDetalle, BonoDescuento, Conversation, ConversationMessage, StockNotification, NotificationLog

# Importar modelos temporalmente definidos en views hasta que se haga la migración
class VerificationToken:
    """Modelo temporal para tokens de verificación"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def objects(cls):
        class Manager:
            def create(self, **kwargs): pass
            def filter(self, **kwargs): return []
            def get(self, **kwargs): return None
        return Manager()
    
    @classmethod
    def objects(cls):
        class Manager:
            def create(self, **kwargs): pass
            def filter(self, **kwargs): return []
            def get(self, **kwargs): return None
        return Manager()
from decimal import Decimal

from django.conf import settings
import json
import requests
import logging
import time
from .wompi_client import WompiClient

logger = logging.getLogger(__name__)

# Create your views here.
def home(request):
    # Registrar visita a la tienda principal
    from core.models import StoreVisit
    
    # Obtener o crear session_key
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    user_obj = None
    
    # Verificar si hay usuario autenticado
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user_obj = SimpleUser.objects.get(id=user_id)
        except SimpleUser.DoesNotExist:
            pass
    
    # Obtener información del cliente
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    # Registrar visita con geolocalización opcional
    if GEOLOCATION_ENABLED and create_visit_with_location:
        try:
            create_visit_with_location(request, 'home', user_obj)
        except:
            # Fallback: registrar sin geolocalización
            StoreVisit.objects.create(
                session_key=session_key,
                user=user_obj,
                visit_type='home'
            )
    else:
        # Sin geolocalización (normal)
        StoreVisit.objects.create(
            session_key=session_key,
            user=user_obj,
            visit_type='home'
        )
    
    # Procesar carrito para el sidebar
    cart = request.session.get('cart', {})
    cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
    
    cart_items = []
    cart_total = Decimal(0)
    for key, item in cart.items():
        if '-' in str(key):
            product_id_cart, variant_id = str(key).split('-')
        else:
            product_id_cart = str(key)
            variant_id = None

        quantity = item['quantity'] if isinstance(item, dict) else item

        try:
            product_cart = Product.objects.get(id=product_id_cart)
        except Product.DoesNotExist:
            continue

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id)
            except ProductVariant.DoesNotExist:
                variant = None

        price = variant.precio if variant else product_cart.price
        subtotal = price * quantity
        cart_items.append({
            'product': product_cart,
            'variant': variant,
            'quantity': quantity,
            'price': price,
            'subtotal': subtotal,
        })
        cart_total += subtotal
    
    context = {
        'cart_count': cart_count,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'user': user_obj,
        'is_logged_in': bool(user_obj)
    }
    
    return render(request, 'home.html', context)

# --- Consulta y actualización de estado de transacción Wompi ---
from django.views.decorators.http import require_GET
@require_GET
def wompi_check_transaction(request, transaction_id):
    """
    Consulta el estado de una transacción Wompi y actualiza el Pedido relacionado si existe.
    URL: /api/wompi-check-transaction/<transaction_id>/
    """
    client = WompiClient()
    url = f"{client.base_url}/transactions/{transaction_id}"
    response = client._make_request('get', url)
    if response and 'data' in response:
        data = response['data']
        # Buscar el pedido por transaction_id
        pedido = Pedido.objects.filter(transaction_id=transaction_id).first()
        if pedido:
            # Actualizar estado de pago y pedido según status de Wompi
            status = data.get('status', '').lower()
            if status == 'approved':
                pedido.estado_pago = 'completado'
                pedido.estado = 'pagado'
            elif status == 'pending':
                pedido.estado_pago = 'pendiente'
            elif status == 'declined':
                pedido.estado_pago = 'rechazado'
                pedido.estado = 'cancelado'
            elif status == 'voided':
                pedido.estado_pago = 'anulado'
                pedido.estado = 'cancelado'
            elif status == 'error':
                pedido.estado_pago = 'error'
            pedido.save()
        return JsonResponse({'success': True, 'wompi_status': data.get('status'), 'pedido_id': pedido.id if pedido else None})
    return JsonResponse({'success': False, 'error': response.get('error', 'No se pudo consultar la transacción')}, status=400)

def wompi_test(request):
    """Vista de test para verificar configuración de Wompi"""
    context = {
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY,
        'wompi_environment': settings.WOMPI_ENVIRONMENT,
    }
    return render(request, 'wompi_test.html', context)

def wompi_widget_test(request):
    """Vista de test específica para el widget de Wompi"""
    context = {
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY,
        'wompi_environment': settings.WOMPI_ENVIRONMENT,
        'wompi_base_url': settings.WOMPI_BASE_URL,
    }
    return render(request, 'wompi_widget_test.html', context)

def login_user(request):
    if request.method == 'POST':
        # Soportar tanto 'username' como 'email'
        username = request.POST.get('username') or request.POST.get('email')
        password = request.POST.get('password')
        
        # Verificar si es un login desde checkout (AJAX)
        is_checkout_login = request.POST.get('checkout_login') == 'true'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Primero verificar si es un superusuario
        superuser_qs = register_superuser.objects.filter(username=username)
        if superuser_qs.exists():
            superuser = superuser_qs.first()
            if superuser.password == password:
                request.session['superuser_id'] = superuser.id
                request.session['superuser_username'] = superuser.username
                
                if is_ajax and is_checkout_login:
                    return JsonResponse({
                        'success': False,
                        'message': 'Los superusuarios deben usar el login del dashboard'
                    })
                
                # Obtener el parámetro 'next' para redirigir correctamente
                next_url = request.GET.get('next', '/dashboard/dashboard_home/')
                return redirect(next_url)
            else:
                if is_ajax and is_checkout_login:
                    return JsonResponse({'success': False, 'message': 'Contraseña incorrecta'})
                return render(request, 'login_user.html', {'error_message': 'Contraseña incorrecta'})
        
        # Si no es superusuario, verificar si es usuario simple (usando email)
        simple_user_qs = SimpleUser.objects.filter(email=username)
        if simple_user_qs.exists():
            simple_user = simple_user_qs.first()
            # Verificar contraseña (nota: en producción debería usar hash)
            if simple_user.password == password:
                # Crear sesión de usuario simple
                request.session['simple_user_id'] = simple_user.id
                request.session['user_id'] = simple_user.id  # Alias para compatibilidad
                request.session['simple_user_email'] = simple_user.email
                request.session['simple_user_name'] = simple_user.name
                
                # Si es login desde checkout, retornar JSON
                if is_ajax and is_checkout_login:
                    return JsonResponse({
                        'success': True,
                        'message': 'Login exitoso',
                        'user': {
                            'name': simple_user.name or '',
                            'email': simple_user.email or '',
                            'telefono': simple_user.telefono or '',
                            'direccion': simple_user.address or '',
                            'ciudad': simple_user.city or '',
                            'departamento': simple_user.departamento or '',
                            'codigo_postal': simple_user.codigo_postal or ''
                        }
                    })
                
                return redirect('/mis-pedidos/')
            else:
                if is_ajax and is_checkout_login:
                    return JsonResponse({'success': False, 'message': 'Contraseña incorrecta'})
                return render(request, 'login_user.html', {'error_message': 'Contraseña incorrecta'})
        
        # Si no se encontró el usuario en ninguna tabla
        if is_ajax and is_checkout_login:
            return JsonResponse({'success': False, 'message': 'Usuario no encontrado'})
        return render(request, 'login_user.html', {'error_message': 'Usuario no encontrado'})
        
    return render(request, 'login_user.html')

def store(request):
    """
    Vista principal de la tienda con filtros modernos y AJAX
    """
    # Registrar visita a la tienda
    from core.models import StoreVisit
    
    # Obtener o crear session_key
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    user_obj = None
    
    # Verificar si hay usuario autenticado (soportar ambos nombres de sesión)
    user_id = request.session.get('user_id') or request.session.get('simple_user_id')
    if user_id:
        try:
            user_obj = SimpleUser.objects.get(id=user_id)
        except SimpleUser.DoesNotExist:
            pass
    
    # Registrar visita con geolocalización opcional
    if GEOLOCATION_ENABLED and create_visit_with_location:
        try:
            create_visit_with_location(request, 'store', user_obj)
        except:
            StoreVisit.objects.create(session_key=session_key, user=user_obj, visit_type='store')
    else:
        StoreVisit.objects.create(session_key=session_key, user=user_obj, visit_type='store')
    
    # Obtener parámetros de filtro
    query = request.GET.get('q', '')
    print(query)
    category_id = request.GET.get('category', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    in_stock = request.GET.get('in_stock', 'true')
    out_of_stock = request.GET.get('out_of_stock', 'true')  # Cambiar a 'true' para mostrar agotados
    sort_by = request.GET.get('sort', 'name')
    page = request.GET.get('page', 1)

    # Base queryset
    products = Product.objects.all().select_related('category')
    categories = Category.objects.all().order_by('nombre')
    
    # Aplicar filtros
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__nombre__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if price_min:
        try:
            products = products.filter(price__gte=int(price_min))
        except (ValueError, TypeError):
            pass
    
    if price_max:
        try:
            products = products.filter(price__lte=int(price_max))
        except (ValueError, TypeError):
            pass
    
    # Filtro de stock
    stock_filters = []
    if in_stock == 'true':
        stock_filters.append(Q(stock__gt=0))
    if out_of_stock == 'true':
        stock_filters.append(Q(stock=0))
    
    if stock_filters:
        stock_query = stock_filters[0]
        for filter_q in stock_filters[1:]:
            stock_query |= filter_q
        products = products.filter(stock_query)
    
    # Ordenamiento
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-id')
    elif sort_by == 'stock':
        products = products.order_by('-stock')
    
    # Procesar carrito completo para el sidebar
    cart = request.session.get('cart', {})
    cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
    
    cart_items = []
    cart_total = Decimal(0)
    for key, item in cart.items():
        if '-' in str(key):
            product_id_cart, variant_id = str(key).split('-')
        else:
            product_id_cart = str(key)
            variant_id = None

        quantity = item['quantity'] if isinstance(item, dict) else item

        try:
            product_cart = Product.objects.get(id=product_id_cart)
        except Product.DoesNotExist:
            continue

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id)
            except ProductVariant.DoesNotExist:
                variant = None

        price = variant.precio if variant else product_cart.price
        subtotal = price * quantity
        cart_items.append({
            'product': product_cart,
            'variant': variant,
            'quantity': quantity,
            'price': price,
            'subtotal': subtotal,
        })
        cart_total += subtotal
    
    # Agrupar productos por categoría
    from collections import defaultdict
    products_by_category = defaultdict(list)
    
    # Evaluar el queryset y agrupar
    products_list = list(products)
    
    for product in products_list:
        category_name = product.category.nombre if product.category else 'Sin categoría'
        products_by_category[category_name].append(product)
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        products_html = render_to_string('partials/products_grid.html', {
            'products': products,
        }, request)
        
        return JsonResponse({
            'success': True,
            'html': products_html,
            'count': products.count(),
            'cart_count': cart_count
        })
    
    # Context para template
    context = {
        'products': products_list,
        'products_by_category': dict(products_by_category),
        'categories': categories,
        'cart_count': cart_count,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'query': query,
        'current_category_id': category_id,
        'price_min': price_min,
        'price_max': price_max,
        'sort_by': sort_by,
        'filters': {
            'query': query,
            'category': category_id,
            'price_min': price_min,
            'price_max': price_max,
            'in_stock': in_stock,
            'out_of_stock': out_of_stock,
        },
        'user': user_obj,
        'is_logged_in': bool(user_obj)
    }
    
    return render(request, 'store.html', context)

def store_modern(request):
    """
    Vista moderna para la tienda con filtros avanzados y AJAX
    """
    # Obtener parámetros de filtro
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    in_stock = request.GET.get('in_stock', 'true')
    out_of_stock = request.GET.get('out_of_stock', 'false')
    sort_by = request.GET.get('sort', 'name')
    page = request.GET.get('page', 1)

    # Base queryset
    products = Product.objects.all().select_related('category')
    categories = Category.objects.all()
    
    # Aplicar filtros
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__nombre__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if price_min:
        try:
            products = products.filter(price__gte=int(price_min))
        except (ValueError, TypeError):
            pass
    
    if price_max:
        try:
            products = products.filter(price__lte=int(price_max))
        except (ValueError, TypeError):
            pass
    
    # Filtro de stock
    stock_filters = []
    if in_stock == 'true':
        stock_filters.append(Q(stock__gt=0))
    if out_of_stock == 'true':
        stock_filters.append(Q(stock=0))
    
    if stock_filters:
        stock_query = stock_filters[0]
        for filter_q in stock_filters[1:]:
            stock_query |= filter_q
        products = products.filter(stock_query)
    
    # Ordenamiento
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-id')
    elif sort_by == 'stock':
        products = products.order_by('-stock')
    
    # Contar carrito
    cart = request.session.get('cart', {})
    cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        products_html = render_to_string('partials/products_grid.html', {
            'products': products,
        }, request)
        
        return JsonResponse({
            'success': True,
            'html': products_html,
            'count': products.count(),
            'cart_count': cart_count
        })
    
    # Context para template
    context = {
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
        'query': query,
        'current_category_id': category_id,
        'price_min': price_min,
        'price_max': price_max,
        'sort_by': sort_by,
        'filters': {
            'query': query,
            'category': category_id,
            'price_min': price_min,
            'price_max': price_max,
            'in_stock': in_stock,
            'out_of_stock': out_of_stock,
        }
    }
    
    return render(request, 'store_modern.html', context)
   
def product_detail(request, product_id):
    # Registrar visita al producto
    from core.models import StoreVisit
    
    # Obtener o crear session_key
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    user_obj = None
    
    # Verificar si hay usuario autenticado
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user_obj = SimpleUser.objects.get(id=user_id)
        except SimpleUser.DoesNotExist:
            pass
    
    # Obtener información del cliente
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Registrar visita con geolocalización opcional
    if GEOLOCATION_ENABLED and create_visit_with_location:
        try:
            create_visit_with_location(request, 'product_detail', user_obj, product_id=product_id)
        except:
            StoreVisit.objects.create(
                session_key=session_key,
                user=user_obj,
                visit_type='product_detail',
                product_id=product_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
    else:
        StoreVisit.objects.create(
            session_key=session_key,
            user=user_obj,
            visit_type='product_detail',
            product_id=product_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    try:
        product = Product.objects.get(id=product_id)        
        Galeria_images = product.galeria.all()
        cart = request.session.get('cart', {})
        cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
        
        # Procesar items del carrito con información completa
        cart_items = []
        cart_total = Decimal(0)
        for key, item in cart.items():
            # Soporta claves tipo "17-1" o solo "17"
            if '-' in str(key):
                product_id_cart, variant_id = str(key).split('-')
            else:
                product_id_cart = str(key)
                variant_id = None

            quantity = item['quantity'] if isinstance(item, dict) else item

            try:
                product_cart = Product.objects.get(id=product_id_cart)
            except Product.DoesNotExist:
                continue

            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                except ProductVariant.DoesNotExist:
                    variant = None

            price = variant.precio if variant else product_cart.price
            subtotal = price * quantity
            cart_items.append({
                'product': product_cart,
                'variant': variant,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal,
            })
            cart_total += subtotal
        
        # Obtener productos relacionados con lógica mejorada
        # ORDEN EXACTO: 1) Nombre similar, 2) Misma categoría, 3) Todas las categorías
        # CADA GRUPO: Primero con stock, luego agotados
        related_products = []
        used_ids = [product.id]
        
        # ===== PASO 1: Productos relacionados por NOMBRE =====
        product_words = [word.lower() for word in product.name.split() if len(word) > 3]
        
        if product_words:
            name_query = Q()
            for word in product_words:
                name_query |= Q(name__icontains=word)
            
            # 1A) Con stock - nombres similares
            name_with_stock = list(Product.objects.filter(
                name_query, stock__gt=0
            ).exclude(id__in=used_ids).order_by('-created_at')[:5])
            
            for p in name_with_stock:
                related_products.append(p)
                used_ids.append(p.id)
            
            # 1B) Agotados - nombres similares
            name_no_stock = list(Product.objects.filter(
                name_query, stock=0
            ).exclude(id__in=used_ids).order_by('-created_at')[:3])
            
            for p in name_no_stock:
                related_products.append(p)
                used_ids.append(p.id)
        
        # ===== PASO 2: Productos de la MISMA CATEGORÍA =====
        if product.category:
            # 2A) Con stock - misma categoría
            category_with_stock = list(Product.objects.filter(
                category=product.category, stock__gt=0
            ).exclude(id__in=used_ids).order_by('-created_at')[:8])
            
            for p in category_with_stock:
                related_products.append(p)
                used_ids.append(p.id)
            
            # 2B) Agotados - misma categoría
            category_no_stock = list(Product.objects.filter(
                category=product.category, stock=0
            ).exclude(id__in=used_ids).order_by('-created_at')[:4])
            
            for p in category_no_stock:
                related_products.append(p)
                used_ids.append(p.id)
        
        # ===== PASO 3: TODAS las demás categorías =====
        # 3A) Con stock - todas las categorías
        all_with_stock = list(Product.objects.filter(
            stock__gt=0
        ).exclude(id__in=used_ids).order_by('category', '-created_at')[:15])
        
        for p in all_with_stock:
            related_products.append(p)
            used_ids.append(p.id)
        
        # 3B) Agotados - todas las categorías
        all_no_stock = list(Product.objects.filter(
            stock=0
        ).exclude(id__in=used_ids).order_by('category', '-created_at')[:15])
        
        for p in all_no_stock:
            related_products.append(p)
            used_ids.append(p.id)
        
        # Fallback: Si no hay productos relacionados
        if len(related_products) == 0:
            related_products = list(Product.objects.exclude(
                id=product.id
            ).order_by('-stock', '-created_at')[:30])
        
        # Preparar URLs de galería de forma segura para JavaScript
        import json
        gallery_urls = []
        if Galeria_images:
            for img in Galeria_images:
                if img.galeria and img.galeria.url:
                    gallery_urls.append(img.galeria.url)
        elif product.imagen and product.imagen.url:
            gallery_urls.append(product.imagen.url)
        
        gallery_urls_json = json.dumps(gallery_urls)
        
        context = {
            'product': product, 
            'Galeria_images': Galeria_images,
            'cart_count': cart_count,
            'cart_items': cart_items,
            'cart_total': cart_total,
            'related_products': related_products,
            'gallery_urls_json': gallery_urls_json
            }       
        return render(request, 'product_detail.html', context)
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)

def checkout(request, note=None):
    # Registrar visita al checkout
    from core.models import StoreVisit
    
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    user_obj = None
    # Verificar si hay usuario autenticado (soportar ambos nombres de sesión)
    user_id = request.session.get('user_id') or request.session.get('simple_user_id')
    if user_id:
        try:
            user_obj = SimpleUser.objects.get(id=user_id)
        except SimpleUser.DoesNotExist:
            pass
    
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Registrar visita con geolocalización opcional
    if GEOLOCATION_ENABLED and create_visit_with_location:
        try:
            create_visit_with_location(request, 'checkout', user_obj)
        except:
            StoreVisit.objects.create(
                session_key=session_key,
                user=user_obj,
                visit_type='checkout',
                ip_address=ip_address,
                user_agent=user_agent
            )
    else:
        StoreVisit.objects.create(
            session_key=session_key,
            user=user_obj,
            visit_type='checkout',
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    saved = request.session.get('saved_checkout', {})   
    departament_selected = saved.get('departamento', '') 
    city_selected = saved.get('ciudad', '')
    nota = request.GET.get('note', '') 
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = Decimal(0)
    for key, item in cart.items():
        # Soporta claves tipo "17-1" o solo "17"
        if '-' in str(key):
            product_id, variant_id = str(key).split('-')
        else:
            product_id = str(key)
            variant_id = None

        quantity = item['quantity'] if isinstance(item, dict) else item

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id)
            except ProductVariant.DoesNotExist:
                variant = None

        price = variant.precio if variant else product.price
        subtotal = price * quantity
        cart_items.append({
            'product': product,
            'variant': variant,
            'quantity': quantity,
            'subtotal': subtotal,
            
        })
        cart_total += subtotal

    saved = request.session.get('saved_checkout', {})
    departament_selected = saved.get('departament', '')
    city_selected = saved.get('ciudad', '')

    # Construye la lista de ciudades según el departamento seleccionado    
    ciudades = []
    if departament_selected and departament_selected in DEPARTAMENTOS_CIUDADES:
       ciudades = DEPARTAMENTOS_CIUDADES[departament_selected]

    # Datos del usuario para autocompletar
    user_data = {}
    user_has_complete_data = False
    
    if user_obj:
        user_data = {
            'nombre': user_obj.name or '',
            'email': user_obj.email or '',
            'telefono': user_obj.telefono or '',
            'direccion': user_obj.address or '',
            'ciudad': user_obj.city or '',
            'departamento': user_obj.departamento or '',
            'codigo_postal': user_obj.codigo_postal or '',
        }
        
        # Verificar si el usuario tiene TODOS los datos necesarios
        required_fields = ['nombre', 'email', 'telefono', 'direccion', 'ciudad', 'departamento']
        user_has_complete_data = all(user_data.get(field) for field in required_fields)
        
        # Actualizar 'saved' con los datos del usuario
        if user_has_complete_data:
            saved = user_data.copy()
            request.session['saved_checkout'] = saved
        
        # Si el usuario tiene datos, usar sus datos como valores seleccionados
        if user_obj.departamento and not departament_selected:
            departament_selected = user_obj.departamento
            if departament_selected in DEPARTAMENTOS_CIUDADES:
                ciudades = DEPARTAMENTOS_CIUDADES[departament_selected]
        if user_obj.city and not city_selected:
            city_selected = user_obj.city

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'nota': nota,
        'departament_selected': departament_selected,
        'departamentos': DEPARTAMENTOS_CIUDADES,
        'ciudades': ciudades,
        'cart_count': sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()]),
        'saved': saved,
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY,
        'user_data': user_data,
        'is_logged_in': bool(user_obj) and user_has_complete_data  # Solo mostrar resumen si tiene datos completos
    }
    return render(request, 'checkout.html', context)

def pago_exitoso(request):
    nota = request.POST.get('note', '')
    if request.method == 'POST':
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        ciudad = request.POST.get('ciudad')
        departamento = request.POST.get('departament')
        codigo_postal = request.POST.get('codigo_postal')
        
        # Obtener información de descuento y pago
        discount_code = request.POST.get('discount_applied', '').strip()
        discount_amount_frontend = Decimal(str(request.POST.get('discount_amount', 0)))
        
        # VALIDAR BONO DE DESCUENTO EN BACKEND
        discount_amount = Decimal('0')
        bono_aplicado = None
        
        if discount_code:
            try:
                # Buscar el bono por código
                bono = BonoDescuento.objects.get(codigo__iexact=discount_code)
                
                # Calcular total del carrito sin descuento
                cart_subtotal = sum(
                    Decimal(str(item['variant'].precio if item['variant'] else item['product'].price)) * int(item['quantity'])
                    for item in cart_items
                )
                
                # Validar si el bono puede ser usado
                if bono.can_be_used(cart_subtotal):
                    # Calcular descuento real
                    discount_amount = Decimal(str(bono.calcular_descuento(cart_subtotal)))
                    bono_aplicado = bono
                    print(f"✅ Bono {discount_code} aplicado: ${discount_amount}")
                else:
                    print(f"❌ Bono {discount_code} no válido para esta compra")
                    discount_code = ''  # Limpiar código inválido
            
            except BonoDescuento.DoesNotExist:
                print(f"❌ Bono {discount_code} no encontrado")
                discount_code = ''  # Limpiar código inexistente
            except Exception as e:
                print(f"❌ Error validando bono {discount_code}: {e}")
                discount_code = ''
        
        # Verificar que el descuento del frontend coincida (seguridad)
        if abs(discount_amount - discount_amount_frontend) > Decimal('0.01'):
            print(f"⚠️ Descrepancia en descuento: Frontend=${discount_amount_frontend}, Backend=${discount_amount}")
            # Usar el cálculo del backend por seguridad
            
        transaction_id = request.POST.get('transaction_id', '').strip()
        metodo_pago = request.POST.get('metodo_pago', 'contraentrega')
        forma_entrega = request.POST.get('forma_entrega', 'domicilio')
        
        # Obtener información adicional de Wompi
        wompi_transaction_id = request.POST.get('wompi_transaction_id', '').strip()
        wompi_reference = request.POST.get('wompi_reference', '').strip()
        
        # Si hay transacción de Wompi, usarla como transaction_id principal
        if wompi_transaction_id:
            transaction_id = wompi_transaction_id
        
        # Log para debugging
        print(f"📋 Checkout - Método pago: {metodo_pago}, Forma entrega: {forma_entrega}")
        if wompi_transaction_id:
            print(f"💳 Pago Wompi - Transaction ID: {wompi_transaction_id}, Reference: {wompi_reference}")

        # Crear o actualizar SimpleUser con todos los datos del checkout
        user, created = SimpleUser.objects.get_or_create(
            email=email, 
            defaults={
                'telefono': telefono,
                'name': nombre,
                'username': email,
                'password': telefono,  # Temporal
                'address': direccion,
                'city': ciudad,
                'departamento': departamento,
                'codigo_postal': codigo_postal
            }
        )
        
        # Si el usuario ya existe, actualizar sus datos con la info del checkout
        if not created:
            user.telefono = telefono
            user.name = nombre
            user.address = direccion
            user.city = ciudad
            user.departamento = departamento
            user.codigo_postal = codigo_postal
            user.save()
            print(f"✅ Datos de usuario {email} actualizados con información del checkout")

        # Crear usuario Django si no existe
        if not User.objects.filter(username=email).exists():
            user_django = User.objects.create_user(
                username=email,
                email=email,
                password=telefono,  # El celular como contraseña temporal
                first_name=nombre
            )
        else:
            user_django = User.objects.get(username=email)

        # Obtener carrito y calcular total
        cart = request.session.get('cart', {})
        cart_items = []
        cart_subtotal = Decimal(0)
        detalles = ""
        for key, item in cart.items():
            # Soporta claves tipo "17-1" o solo "17"
            if '-' in str(key):
                product_id, variant_id = str(key).split('-')
            else:
                product_id = str(key)
                variant_id = None

            quantity = item['quantity'] if isinstance(item, dict) else item

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue

            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                except ProductVariant.DoesNotExist:
                    variant = None

            price = variant.precio if variant else product.price
            subtotal = price * quantity
            cart_items.append({'product': product, 'variant': variant, 'quantity': quantity, 'subtotal': subtotal})
            cart_subtotal += subtotal

        # Calcular envío según forma de entrega
        print(f"💰 Calculando envío - Forma entrega: {forma_entrega}, Subtotal: ${cart_subtotal}")
        if forma_entrega == 'tienda':
            shipping_cost = Decimal(0)  # Gratis para recoger en tienda
            print(f"🏪 Recoger en tienda - Envío: $0")
        else:
            shipping_cost = Decimal(15000) if cart_subtotal < Decimal(100000) else Decimal(0)
            print(f"📦 Domicilio - Envío: ${shipping_cost}")
        
        cart_total = cart_subtotal - discount_amount + shipping_cost

        # Organiza el detalle de productos para WhatsApp/email
        detalles = ""
        for item in cart_items:
            linea = f"- {item['product'].name}"
            if item['variant']:
                if item['variant'].color:
                    linea += f" | Color: {item['variant'].color}"
                if item['variant'].talla:
                    linea += f" | Talla: {item['variant'].talla}"
            linea += f" | Cantidad: {item['quantity']} | Subtotal: ${item['subtotal']}\n"
            detalles += linea
        
        # Agregar información de descuento al detalle si aplica
        if discount_code and discount_amount > 0:
            detalles += f"\n🎁 Descuento aplicado ({discount_code}): -${discount_amount:,.0f}\n"
        
        # Agregar información de envío
        if forma_entrega == 'tienda':
            detalles += f"🏪 Entrega: Recoger en tienda - Envío GRATIS\n"
            detalles += f"💰 Método de pago: {metodo_pago.title()}\n"
        elif shipping_cost > 0:
            detalles += f"📦 Entrega: Domicilio - Costo de envío: ${shipping_cost:,.0f}\n"
            detalles += f"💰 Método de pago: {metodo_pago.title()}\n"
        else:
            detalles += f"📦 Entrega: Domicilio - Envío GRATIS\n"
            detalles += f"💰 Método de pago: {metodo_pago.title()}\n"

        # Determinar estado inicial del pago
        estado_pago_inicial = 'pendiente'
        if metodo_pago in ['tarjeta', 'wompi', 'wompi_tarjeta'] and transaction_id:
            estado_pago_inicial = 'completado'
        
        # Construir nota con información de Wompi si aplica
        nota_final = nota if nota else ''
        if wompi_reference:
            nota_final = f"{nota_final} | Referencia Wompi: {wompi_reference}".strip('| ')
        if wompi_transaction_id:
            nota_final = f"{nota_final} | PAGADO - Wompi Transaction: {wompi_transaction_id}".strip('| ')

        # Guardar pedido con toda la información nueva
        pedido = Pedido.objects.create(
            user=user,
            nombre=nombre,
            email=email,  # Agregar email
            telefono=telefono,  # Agregar teléfono
            direccion=direccion,
            ciudad=ciudad,
            departamento=departamento,
            codigo_postal=codigo_postal,
            subtotal=cart_subtotal,  # Agregar subtotal
            envio=shipping_cost,  # Agregar envío
            descuento=discount_amount,  # Agregar descuento
            total=cart_total,
            detalles=detalles,
            nota=nota_final,  # Nota con información de Wompi
            estado='pendiente',  # Estado inicial
            metodo_pago=metodo_pago,  # Método de pago correcto
            forma_entrega=forma_entrega,  # Forma de entrega
            estado_pago=estado_pago_inicial,  # Estado de pago
            transaction_id=transaction_id if transaction_id else None,  # Transaction ID
            codigo_descuento=discount_code if discount_code else None,  # Código descuento
        )

        # USAR EL BONO SI FUE APLICADO EXITOSAMENTE
        if bono_aplicado and discount_amount > 0:
            try:
                bono_aplicado.usar_bono()
                print(f"✅ Bono {bono_aplicado.codigo} usado exitosamente. Usos: {bono_aplicado.usos_realizados}/{bono_aplicado.usos_maximos}")
            except Exception as e:
                print(f"❌ Error al usar bono {bono_aplicado.codigo}: {e}")

        # Guardar cada item en el detalle del pedido y descontar stock (¡DENTRO DEL CICLO!)
        for item in cart_items:
            PedidoDetalle.objects.create(
                pedido=pedido,
                producto=item['product'],
                variante=item['variant'],
                cantidad=item['quantity'],
                precio=item['variant'].precio if item['variant'] else item['product'].price,
            )
            # Descontar stock
            if item['variant']:
                variant = item['variant']
                # Asegúrate de tener la instancia real
                if not hasattr(variant, 'save'):
                    variant = ProductVariant.objects.get(id=variant.id)
                variant.stock = max(0, variant.stock - item['quantity'])
                variant.save()
            else:
                product = item['product']
                if not hasattr(product, 'save'):
                    product = Product.objects.get(id=product.id)
                product.stock = max(0, product.stock - item['quantity'])
                product.save()

        # Guardar info para futuros checkouts
        if request.POST.get('save_info'):
            request.session['saved_checkout'] = {
                'email': email,
                'nombre': nombre,
                'cedula': request.POST.get('cedula'),
                'direccion': direccion,
                'departament': departamento,
                'ciudad': ciudad,
                'codigo_postal': codigo_postal,
                'telefono': telefono,
            }
        else:
            request.session.pop('saved_checkout', None)
        # Limpiar carrito
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

        # Enviar correo al usuario con información de descuento
        subject = "Confirmación de tu compra en CompuEasys"
        
        # Construir resumen de totales
        total_summary = f"Subtotal: ${cart_subtotal:,.0f}\n"
        if discount_code and discount_amount > 0:
            total_summary += f"Descuento ({discount_code}): -${discount_amount:,.0f}\n"
        if shipping_cost > 0:
            total_summary += f"Envío: ${shipping_cost:,.0f}\n"
        else:
            total_summary += f"Envío: GRATIS\n"
        total_summary += f"TOTAL: ${cart_total:,.0f}\n"
        
        message = (
            f"¡Hola {nombre}!\n\n"
            f"Gracias por tu compra en CompuEasys.\n\n"
            f"Resumen de tu pedido:\n{detalles}\n"
            f"--- TOTALES ---\n{total_summary}\n"
            f"Dirección de envío: {direccion}, {ciudad}, {departamento}, CP: {codigo_postal}\n\n"
            f"Se ha creado una cuenta para ti con el email: {email}\n"
            f"Tu contraseña temporal es tu número de celular: {telefono}\n"
            f"Puedes cambiarla cuando quieras desde la tienda.\n\n"
            f"¡Gracias por confiar en nosotros!"
        )
        # Remitente seguro: DEFAULT_FROM_EMAIL o EMAIL_HOST_USER
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
        if not from_email:
            logger.error("No se ha configurado DEFAULT_FROM_EMAIL ni EMAIL_HOST_USER en settings.py")
        else:
            try:
                send_mail(subject, message, from_email, [email], fail_silently=False)
            except Exception as e:
                logger.exception("Error enviando correo de confirmación: %s", e)
                # no interrumpir flujo, solo loggear; opcionalmente notificar al admin

        # Generar link de WhatsApp ORDENADO con información de descuento
        total_line = f"*Subtotal:* ${cart_subtotal:,.0f}\n"
        if discount_code and discount_amount > 0:
            total_line += f"*Descuento ({discount_code}):* -${discount_amount:,.0f}\n"
        if shipping_cost > 0:
            total_line += f"*Envío:* ${shipping_cost:,.0f}\n"
        else:
            total_line += f"*Envío:* GRATIS\n"
        total_line += f"*TOTAL:* ${cart_total:,.0f}\n"
        
        mensaje = (
            f"🛒 *Nuevo pedido de {nombre}*\n\n"
            f"*Productos:*\n"
            f"{detalles}\n"
            f"--- TOTALES ---\n"
            f"{total_line}\n"
            f"*Datos de envío:*\n"
            f"Nombre: {nombre}\n"
            f"Dirección: {direccion}\n"
            f"Ciudad: {ciudad}\n"
            f"Departamento: {departamento}\n"
            f"Código Postal: {codigo_postal}\n"
            f"Teléfono: {telefono}\n"
        )
        if nota:
            mensaje += f"\n*Nota:* {nota}\n"

        mensaje_encoded = urllib.parse.quote(mensaje)
        whatsapp_url = f"https://wa.me/57{telefono}?text={mensaje_encoded}"

        return render(request, 'pago_exitoso.html', {
            'nombre': nombre,
            'whatsapp_url': whatsapp_url,
            'cart_total': cart_total,
            'discount_code': discount_code,
            'discount_amount': discount_amount
        })
    return HttpResponse("Invalid request", status=400)

def auctions(request):
    return render(request, 'auctions.html')

def services(request):
    return render(request, 'services.html')

def contactUs(request):
    return render(request, 'contactUs.html')

def aboutUs(request):
    return render(request, 'aboutUs.html')


def send_welcome_email(email, username):
    """
    Envía email de bienvenida a usuarios recién registrados
    """
    try:
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        import datetime
        
        # Obtener BASE_URL dinámicamente
        # En producción será https://compueasys.onrender.com
        # En desarrollo será http://127.0.0.1:8000
        base_url = getattr(settings, 'BASE_URL', 'https://compueasys.onrender.com')
        
        # Contexto para la plantilla
        context = {
            'username': username,
            'email': email,
            'site_name': 'CompuEasys',
            'year': datetime.datetime.now().year,
            'base_url': base_url
        }
        
        # Renderizar plantilla HTML
        html_content = render_to_string('emails/welcome.html', context)
        
        # Crear mensaje
        subject = f'¡Bienvenido a CompuEasys, {username}! 🎉'
        
        # Mensaje de texto plano como fallback
        text_content = f"""
        ¡Hola {username}!
        
        ¡Bienvenido a CompuEasys! Tu cuenta ha sido creada exitosamente.
        
        Ahora puedes:
        • Explorar nuestros productos tecnológicos
        • Recibir notificaciones cuando los productos estén disponibles
        • Realizar compras de forma segura
        • Acceder a ofertas exclusivas
        
        ¡Gracias por unirte a nuestra comunidad!
        
        El equipo de CompuEasys
        """
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@compueasys.com'),
            to=[email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Enviar email
        msg.send()
        
        logger.info(f"✅ Welcome email sent to {email}")
        
    except Exception as e:
        logger.error(f"❌ Error sending welcome email to {email}: {e}")

def register_user(request):
    if request.method == 'POST':       
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        # Si quieres que el usuario sea staff, usa True
       
        if User.objects.filter(username=username).exists():
            return render(request, 'register_user.html', {'error': 'El nombre de usuario ya está en uso'})
        if User.objects.filter(email=email).exists():
            return render(request, 'register_user.html', {'error': 'El correo electrónico ya está en uso'})
        
        # Crear usuario Django
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = username  # Usar username como nombre
        user.save()
        
        # Crear SimpleUser para el e-commerce
        simple_user, created = SimpleUser.objects.get_or_create(
            email=email,
            defaults={
                'telefono': phone,
                'address': address,
                'city': '',  # Se puede llenar después
                'username': username
            }
        )
        
        # Guarda info adicional en tu modelo register_superuser si lo necesitas
        register_superuser.objects.create(
            username=username,
            email=email,
            password=password,
            phone=phone,
            address=address,
            is_superuser=True,
            is_staff=True,
            is_active=True
        )
        
        # INICIAR SESIÓN AUTOMÁTICAMENTE
        user_authenticated = authenticate(request, username=username, password=password)
        if user_authenticated:
            login(request, user_authenticated)
            
            # Guardar información del usuario en la sesión
            request.session['user_info'] = {
                'user_id': simple_user.id,
                'email': email,
                'username': username,
                'phone': phone
            }
            
        # ENVIAR EMAIL DE BIENVENIDA
        send_welcome_email(email, username)
        
        # Redirigir al store con mensaje de bienvenida
        messages.success(request, f'¡Bienvenido {username}! Tu cuenta ha sido creada exitosamente.')
        return redirect('store')  # Cambiar de login_user a store
        
    return render(request, 'register_user.html')

def index(request):
    return render(request, "index.html")

# ...existing code...
def cart(request):
    # Registrar visita al carrito
    from core.models import StoreVisit
    
    # Obtener o crear session_key
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    user_obj = None
    
    # Verificar si hay usuario autenticado
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user_obj = SimpleUser.objects.get(id=user_id)
        except SimpleUser.DoesNotExist:
            pass
    
    # Obtener información del cliente
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Registrar visita con geolocalización opcional
    if GEOLOCATION_ENABLED and create_visit_with_location:
        try:
            create_visit_with_location(request, 'cart', user_obj)
        except:
            StoreVisit.objects.create(
                session_key=session_key,
                user=user_obj,
                visit_type='cart',
                ip_address=ip_address,
                user_agent=user_agent
            )
    else:
        StoreVisit.objects.create(
            session_key=session_key,
            user=user_obj,
            visit_type='cart',
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = Decimal(0)
    removed_keys = []

    for key, item in list(cart.items()):
        # Normalizar formato del item
        if isinstance(item, int):
            product_id = key
            quantity = item
            variant = None
        else:
            product_id = item.get('product_id', key)
            quantity = item.get('quantity', 1)
            variant_id = item.get('variant_id')
            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                except ProductVariant.DoesNotExist:
                    variant = None

        # Intentar obtener el producto; si no existe, eliminar la entrada del carrito y continuar
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            removed_keys.append(key)
            continue

        price = variant.precio if variant else product.price
        subtotal = price * quantity
        cart_items.append({
            'product': product,
            'variant': variant,
            'quantity': quantity,
            'subtotal': subtotal,
        })
        cart_total += subtotal

    # Limpiar items inválidos del session cart
    if removed_keys:
        for k in removed_keys:
            if k in cart:
                del cart[k]
        request.session['cart'] = cart
        request.session.modified = True

    # recalcular contador de carrito seguro
    cart_count = 0
    for v in cart.values():
        if isinstance(v, dict):
            cart_count += v.get('quantity', 0)
        else:
            try:
                cart_count += int(v)
            except Exception:
                pass

    # Obtener productos relacionados para mostrar en el carrito
    # Productos aleatorios de diferentes categorías
    related_products = Product.objects.filter(
        stock__gt=0
    ).order_by('?')[:12]  # 12 productos aleatorios para el slider
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
        'related_products': related_products
    }
    return render(request, 'cart.html', context)
# ...existing code...

def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        variant_id = request.POST.get('variant_id')
        key = f"{product_id}-{variant_id}" if variant_id else str(product_id)
        action = request.POST.get('action')
        quantity = int(request.POST.get('quantity', 1))
        
        if key in cart:
            # Obtener precio del producto/variante
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                    stock = variant.stock
                    price = variant.precio
                except ProductVariant.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Variante no encontrada'})
            else:
                try:
                    product = Product.objects.get(id=product_id)
                    stock = product.stock
                    price = product.price
                except Product.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Producto no encontrado'})
            
            # Actualizar cantidad
            if action == 'set':
                if quantity > stock:
                    quantity = stock
                if quantity < 1:
                    quantity = 1
                    
                if isinstance(cart[key], int):
                    cart[key] = quantity
                else:
                    cart[key]['quantity'] = quantity
            
            request.session['cart'] = cart
            request.session.modified = True

            subtotal = price * quantity            
         
            # Calcula total del carrito y cantidad total
            cart_total = Decimal(0)
            cart_count = 0
            
            for k, v in cart.items():
                if isinstance(v, dict):
                    q = v['quantity']
                    if v.get('variant_id'):
                        try:
                            pv = ProductVariant.objects.get(id=v['variant_id'])
                            p = pv.precio
                        except:
                            p = 0
                    else:
                        try:
                            p = Product.objects.get(id=v['product_id']).price
                        except:
                            p = 0
                else:
                    # Formato antiguo: k puede ser "product_id" o "product_id-variant_id"
                    q = v
                    try:
                        if '-' in k:
                            # Tiene variante
                            parts = k.split('-')
                            variant_id = parts[1]
                            pv = ProductVariant.objects.get(id=variant_id)
                            p = pv.precio
                        else:
                            # Solo producto
                            p = Product.objects.get(id=k).price
                    except:
                        p = 0
                
                item_total = p * q
                cart_total += item_total
                cart_count += q

            return JsonResponse({
                'success': True,
                'item_subtotal': float(subtotal),
                'quantity': quantity,        
                'cart_total': float(cart_total),
                'cart_count': cart_count
            })
               
        return JsonResponse({'success': False})
    return JsonResponse({'success': False}, status=400)

def add_to_cart(request, product_id):    
    try:
        product = Product.objects.get(id=product_id)     
    except Product.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        return HttpResponseRedirect('/store')

    variant_id = request.POST.get('variant_id')
    product_id = str(product_id)
    key = f"{product_id}-{variant_id}" if variant_id else product_id
    cart = request.session.get('cart', {})

    # Cantidad a añadir
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
    else:
        quantity = 1

    # Unifica formato antiguo a nuevo y suma cantidad
    if key in cart:
        if isinstance(cart[key], int):
            # Formato antiguo: convertir a nuevo formato Y sumar cantidad
            cart[key] = {
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': cart[key] + quantity,
            }
        else:
            # Formato nuevo: solo sumar cantidad
            cart[key]['quantity'] += quantity
    else:
        # Producto nuevo en el carrito
        cart[key] = {
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': quantity,
        }
        
    request.session['cart'] = cart
    request.session.modified = True

    cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'cart_count': cart_count})
    return HttpResponseRedirect('/store')

def add_to_cart_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    variant_id = request.POST.get('variant_id')
    product_id = str(product_id)
    key = f"{product_id}-{variant_id}" if variant_id else product_id
    cart = request.session.get('cart', {})

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
    else:
        quantity = 1
        
    # Unifica formato antiguo a nuevo y suma cantidad
    if key in cart:
        if isinstance(cart[key], int):
            # Formato antiguo: convertir a nuevo formato Y sumar cantidad
            cart[key] = {
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': cart[key] + quantity,
            }
        else:
            # Formato nuevo: solo sumar cantidad
            cart[key]['quantity'] += quantity
    else:
        # Producto nuevo en el carrito
        cart[key] = {
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': quantity,
        }
        
    request.session['cart'] = cart
    request.session.modified = True
    
    if 'go_to_cart' in request.POST:
        return redirect('cart')
    else:
        return redirect('product_detail', product_id=product_id)

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    variant_id = request.GET.get('variant_id')
    key = f"{product_id}-{variant_id}" if variant_id else str(product_id)
    
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Calcular nuevo total del carrito
            cart_total = Decimal(0)
            cart_count = 0
            for k, v in cart.items():
                if isinstance(v, dict):
                    quantity = v['quantity']
                    if v.get('variant_id'):
                        try:
                            variant = ProductVariant.objects.get(id=v['variant_id'])
                            price = variant.precio
                        except ProductVariant.DoesNotExist:
                            price = 0
                    else:
                        try:
                            product = Product.objects.get(id=v['product_id'])
                            price = product.price
                        except Product.DoesNotExist:
                            price = 0
                else:
                    quantity = v
                    try:
                        product = Product.objects.get(id=k)
                        price = product.price
                    except Product.DoesNotExist:
                        price = 0
                
                cart_total += price * quantity
                cart_count += quantity
            
            return JsonResponse({
                'success': True,
                'message': 'Producto eliminado correctamente',
                'cart_total': cart_total,
                'cart_count': cart_count
            })
    
    # Si es petición AJAX pero el producto no estaba en el carrito
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'El producto no estaba en el carrito'
        })
    
    # Si no es AJAX, hacer redirect normal
    return redirect('cart')

def clear_cart(request):
    if request.method == 'POST' or request.method == 'GET':
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Carrito vaciado correctamente',
                'cart_total': 0,
                'cart_count': 0
            })
    
    # Si no es AJAX, hacer redirect normal
    return redirect('cart')

# ...existing code...
def mis_pedidos(request):
    # Verificar si hay un usuario simple en sesión
    if 'simple_user_id' in request.session:
        try:
            simple_user_id = request.session['simple_user_id']
            simple_user = SimpleUser.objects.get(id=simple_user_id)
            pedidos = Pedido.objects.filter(user=simple_user).order_by('-fecha')
            
            # Calcular estadísticas
            pedidos_pendientes = pedidos.filter(estado='pending').count()
            total_gastado = pedidos.aggregate(
                total=models.Sum('total')
            )['total'] or 0
            
            # Obtener perfil del usuario
            user_profile = simple_user
            
            message = "" if pedidos.exists() else "Aún no tienes pedidos para visualizar."
        except SimpleUser.DoesNotExist:
            pedidos = []
            pedidos_pendientes = 0
            total_gastado = 0
            user_profile = None
            message = "Error: Usuario no encontrado."
    
    # También verificar con el sistema de autenticación de Django (para compatibilidad)
    elif request.user.is_authenticated:
        email = request.user.email
        try:
            simple_user = SimpleUser.objects.get(email=email)
            pedidos = Pedido.objects.filter(user=simple_user).order_by('-fecha')
            
            # Calcular estadísticas
            pedidos_pendientes = pedidos.filter(estado='pending').count()
            total_gastado = pedidos.aggregate(
                total=models.Sum('total')
            )['total'] or 0
            
            # Obtener perfil del usuario
            user_profile = simple_user
            
            message = "" if pedidos.exists() else "Aún no tienes pedidos para visualizar."
        except SimpleUser.DoesNotExist:
            pedidos = []
            pedidos_pendientes = 0
            total_gastado = 0
            user_profile = None
            message = "Aún no tienes pedidos para visualizar."
    else:
        # Redirigir a login si no hay usuario autenticado
        return redirect('login_user')

    context = {
        'pedidos': pedidos,
        'pedidos_pendientes': pedidos_pendientes,
        'total_gastado': total_gastado,
        'user_profile': user_profile,
        'message': message,
        'user': user_profile,
        'is_logged_in': bool(user_profile)
    }

    return render(request, 'mis_pedidos.html', context)


from django.http import FileResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime


def download_receipt(request, pedido_id):
    """
    Vista para generar y descargar el recibo de un pedido en formato PDF (ticket térmico)
    """
    try:
        # Obtener el pedido
        pedido = Pedido.objects.get(id=pedido_id)
        
        # Verificar que el usuario tenga acceso a este pedido
        if 'simple_user_id' in request.session:
            simple_user_id = request.session['simple_user_id']
            if pedido.user.id != simple_user_id:
                return JsonResponse({'error': 'No tienes permiso para ver este pedido'}, status=403)
        elif request.user.is_authenticated:
            try:
                simple_user = SimpleUser.objects.get(email=request.user.email)
                if pedido.user.id != simple_user.id:
                    return JsonResponse({'error': 'No tienes permiso para ver este pedido'}, status=403)
            except SimpleUser.DoesNotExist:
                return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        else:
            return redirect('login_user')
        
        # Crear el PDF en memoria
        buffer = BytesIO()
        
        # Configurar el documento con tamaño de ticket (80mm de ancho)
        width = 80 * mm
        height = 297 * mm  # Largo variable tipo A4
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(width, height),
            rightMargin=5*mm,
            leftMargin=5*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )
        
        # Contenedor para los elementos del PDF
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=3,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        normal_center = ParagraphStyle(
            'NormalCenter',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            spaceAfter=2
        )
        
        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=2
        )
        
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold'
        )
        
        # Encabezado
        elements.append(Paragraph("COMPUEASYS", title_style))
        elements.append(Paragraph("Tecnología y Soluciones", normal_center))
        elements.append(Paragraph("Tel: (601) 123-4567", normal_center))
        elements.append(Paragraph("www.compueasys.com", normal_center))
        elements.append(Spacer(1, 5*mm))
        
        # Línea separadora
        line_data = [['─' * 30]]
        line_table = Table(line_data, colWidths=[width-10*mm])
        line_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 3*mm))
        
        # Información del pedido
        info_data = [
            ['Pedido:', f'#{pedido.id}'],
            ['Fecha:', pedido.fecha.strftime('%d/%m/%Y %H:%M')],
            ['Estado:', pedido.estado or 'Pendiente'],
            ['Pago:', pedido.metodo_pago or 'Por confirmar'],
        ]
        
        info_table = Table(info_data, colWidths=[20*mm, 50*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 5*mm))
        
        # Línea separadora
        elements.append(line_table)
        elements.append(Spacer(1, 3*mm))
        
        # Título de productos
        elements.append(Paragraph("<b>PRODUCTOS</b>", normal_center))
        elements.append(Spacer(1, 3*mm))
        
        # Parsear detalles del pedido
        detalles_lineas = pedido.detalles.split('\n') if pedido.detalles else []
        productos_data = []
        
        for detalle in detalles_lineas:
            if detalle.strip():
                # Intentar parsear formato "Producto x cantidad - precio"
                import re
                match = re.match(r'(.+?)\s*x\s*(\d+)\s*-\s*\$([\\d,]+)', detalle)
                if match:
                    nombre = match.group(1).strip()
                    cantidad = match.group(2)
                    precio = match.group(3)
                    
                    # Agregar línea del producto
                    productos_data.append([nombre, ''])
                    productos_data.append([f'{cantidad} x ${precio}', ''])
                else:
                    # Formato simple
                    productos_data.append([detalle.strip(), ''])
        
        if productos_data:
            productos_table = Table(productos_data, colWidths=[width-10*mm])
            productos_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(productos_table)
        
        elements.append(Spacer(1, 5*mm))
        elements.append(line_table)
        elements.append(Spacer(1, 3*mm))
        
        # Total
        total_data = [
            ['TOTAL:', f"${pedido.total:,.0f}"]
        ]
        total_table = Table(total_data, colWidths=[35*mm, 35*mm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(total_table)
        
        elements.append(Spacer(1, 5*mm))
        elements.append(line_table)
        elements.append(Spacer(1, 3*mm))
        
        # Footer
        elements.append(Paragraph("<b>¡Gracias por tu compra!</b>", normal_center))
        elements.append(Paragraph("Conserva este recibo", normal_center))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("═" * 25, normal_center))
        
        # Construir el PDF
        doc.build(elements)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = FileResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recibo_pedido_{pedido.id}.pdf"'
        
        return response
        
    except Pedido.DoesNotExist:
        return JsonResponse({'error': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        print(f"Error generando PDF: {str(e)}")
        return JsonResponse({'error': f'Error generando el recibo: {str(e)}'}, status=500)


# ...existing code...

def logout_view(request):
    # Limpiar sesión de usuarios simples
    if 'simple_user_id' in request.session:
        del request.session['simple_user_id']
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'simple_user_email' in request.session:
        del request.session['simple_user_email'] 
    if 'simple_user_name' in request.session:
        del request.session['simple_user_name']
    
    # Limpiar sesión de superusuarios
    if 'superuser_id' in request.session:
        del request.session['superuser_id']
    if 'superuser_username' in request.session:
        del request.session['superuser_username']
    
    # Limpiar autenticación de Django también
    logout(request)
    
    # Redirigir a la página principal
    return redirect('store')



import logging
logger = logging.getLogger(__name__)

def enviarEmail(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

    nombre = request.POST.get('name')
    email = request.POST.get('email')
    mensaje = request.POST.get('message')

    subject = f"Nuevo mensaje de contacto de {nombre}"
    message = f"Nombre: {nombre}\nEmail: {email}\n\nMensaje:\n{mensaje}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [getattr(settings, 'CONTACT_EMAIL', from_email)]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as e:
        logger.exception("Error enviando email de contacto")
        return JsonResponse({'success': False, 'message': 'Error enviando correo.', 'error': str(e)}, status=500)

    return JsonResponse({'success': True, 'message': 'Correo enviado exitosamente.'})
# Datos de departamentos y ciudades
DEPARTAMENTOS_CIUDADES = {
    "Amazonas": ["Leticia", "Puerto Nariño"],
    "Antioquia": ["Medellín", "Envigado", "Bello", "Itagüí", "Rionegro", "Apartadó", "Turbo", "Caucasia", "La Ceja", "Copacabana", "Sabaneta", "Girardota", "Marinilla"],
    "Arauca": ["Arauca", "Arauquita", "Saravena", "Tame"],
    "Atlántico": ["Barranquilla", "Soledad", "Malambo", "Sabanalarga", "Baranoa", "Galapa", "Puerto Colombia"],
    "Bolívar": ["Cartagena", "Magangué", "Turbaco", "El Carmen de Bolívar", "Arjona", "San Juan Nepomuceno", "Mompox"],
    "Boyacá": ["Tunja", "Duitama", "Sogamoso", "Chiquinquirá", "Paipa", "Samacá", "Moniquirá"],
    "Caldas": ["Manizales", "La Dorada", "Villamaría", "Chinchiná", "Riosucio", "Anserma"],
    "Caquetá": ["Florencia", "Belén de los Andaquíes", "San Vicente del Caguán", "Puerto Rico"],
    "Casanare": ["Yopal", "Aguazul", "Villanueva", "Tauramena"],
    "Cauca": ["Popayán", "Santander de Quilichao", "Puerto Tejada", "Patía", "El Tambo"],
    "Cesar": ["Valledupar", "Aguachica", "Codazzi", "La Jagua de Ibirico", "Bosconia"],
    "Chocó": ["Quibdó", "Istmina", "Tadó", "Condoto", "Bahía Solano"],
    "Córdoba": ["Montería", "Lorica", "Sahagún", "Cereté", "Montelíbano", "Planeta Rica"],
    "Cundinamarca": ["Bogotá", "Soacha", "Fusagasugá", "Girardot", "Zipaquirá", "Chía", "Facatativá", "Mosquera", "Madrid", "Cajicá"],
    "Guainía": ["Inírida"],
    "Guaviare": ["San José del Guaviare", "Calamar"],
    "Huila": ["Neiva", "Pitalito", "Garzón", "La Plata"],
    "La Guajira": ["Riohacha", "Maicao", "Uribia", "Fonseca", "San Juan del Cesar"],
    "Magdalena": ["Santa Marta", "Ciénaga", "Fundación", "El Banco"],
    "Meta": ["Villavicencio", "Acacías", "Granada", "Puerto López"],
    "Nariño": ["Pasto", "Tumaco", "Ipiales", "Túquerres"],
    "Norte de Santander": ["Cúcuta", "Ocaña", "Pamplona", "Villa del Rosario", "Los Patios"],
    "Putumayo": ["Mocoa", "Puerto Asís", "Orito", "Sibundoy"],
    "Quindío": ["Armenia", "Calarcá", "Montenegro", "La Tebaida"],
    "Risaralda": ["Pereira", "Dosquebradas", "La Virginia", "Santa Rosa de Cabal"],
    "San Andrés y Providencia": ["San Andrés", "Providencia"],
    "Santander": ["Bucaramanga", "Floridablanca", "Girón", "Piedecuesta", "Barrancabermeja", "Socorro", "San Gil"],
    "Sucre": ["Sincelejo", "Corozal", "Sampués", "Tolú"],
    "Tolima": ["Ibagué", "Espinal", "Melgar", "Honda", "Líbano"],
    "Valle del Cauca": ["Cali", "Palmira", "Buenaventura", "Tuluá", "Buga", "Cartago", "Jamundí", "Yumbo"],
    "Vaupés": ["Mitú"],
    "Vichada": ["Puerto Carreño", "La Primavera"]
}

# Endpoints AJAX para el store moderno
def search_suggestions(request):
    """
    Endpoint para sugerencias de búsqueda en tiempo real
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Not AJAX'}, status=400)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        # Búsqueda en productos
        product_names = Product.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True).distinct()[:5]
        
        # Búsqueda en categorías
        category_names = Category.objects.filter(
            nombre__icontains=query
        ).values_list('nombre', flat=True).distinct()[:3]
        
        # Combinar sugerencias
        suggestions = list(product_names) + list(category_names)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions[:8]  # Máximo 8 sugerencias
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def filter_products_ajax(request):
    """
    Endpoint AJAX para filtrado dinámico de productos
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Not AJAX'}, status=400)
    
    try:
        # Obtener filtros
        query = request.GET.get('q', '')
        category_id = request.GET.get('category', '')
        price_min = request.GET.get('price_min', '')
        price_max = request.GET.get('price_max', '')
        in_stock = request.GET.get('in_stock', 'true') == 'true'
        out_of_stock = request.GET.get('out_of_stock', 'false') == 'true'
        sort_by = request.GET.get('sort', 'name')
        
        # Base queryset
        products = Product.objects.all().select_related('category')
        
        # Aplicar filtros
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__nombre__icontains=query)
            )
        
        if category_id:
            products = products.filter(category_id=category_id)
        
        if price_min:
            try:
                products = products.filter(price__gte=int(price_min))
            except (ValueError, TypeError):
                pass
        
        if price_max:
            try:
                products = products.filter(price__lte=int(price_max))
            except (ValueError, TypeError):
                pass
        
        # Filtro de stock - Respetar selecciones del usuario
        if in_stock and out_of_stock:
            # Mostrar ambos: productos con stock y sin stock
            pass  # No aplicar filtro, mostrar todos
        elif in_stock and not out_of_stock:
            # Solo productos con stock
            products = products.filter(stock__gt=0)
        elif not in_stock and out_of_stock:
            # Solo productos sin stock (agotados)
            products = products.filter(stock=0)
        elif not in_stock and not out_of_stock:
            # Usuario desmarcó ambos - no mostrar productos
            products = products.none()
        
        # Ordenamiento
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'name':
            products = products.order_by('name')
        elif sort_by == 'newest':
            products = products.order_by('-id')
        elif sort_by == 'stock':
            products = products.order_by('-stock')
        
        # Contar productos antes del slice
        total_count = products.count()
        
        # Limitar resultados para mejor rendimiento
        products = products[:50]
        
        # Renderizar HTML de productos
        from django.template.loader import render_to_string
        from collections import defaultdict
        
        # Si NO hay filtro de categoría, agrupar por categorías
        if not category_id:
            products_by_category = defaultdict(list)
            for product in products:
                category_name = product.category.nombre if product.category else 'Sin categoría'
                products_by_category[category_name].append(product)
            
            products_html = render_to_string('partials/products_grid_categorized.html', {
                'products_by_category': dict(products_by_category),
            }, request)
        else:
            # Si hay filtro de categoría, mostrar productos simples
            products_html = render_to_string('partials/products_grid.html', {
                'products': products,
            }, request)
        
        # Contar carrito
        cart = request.session.get('cart', {})
        cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
        
        return JsonResponse({
            'success': True,
            'html': products_html,
            'count': total_count,
            'cart_count': cart_count,
            'message': f'Se encontraron {total_count} productos'
        })
        
    except Exception as e:
        print(f"Error in filter_products_ajax: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

def cart_count_api(request):
    """
    Endpoint AJAX para obtener el número de items en el carrito
    """
    try:
        cart = request.session.get('cart', {})
        cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
        
        return JsonResponse({
            'success': True,
            'count': cart_count
        })
    except Exception as e:
        print(f"Error in cart_count_api: {e}")
        return JsonResponse({
            'success': False,
            'count': 0
        })

def cart_preview(request):
    """
    Endpoint AJAX para obtener el preview del carrito con HTML de los items
    """
    try:
        from django.template.loader import render_to_string
        
        cart = request.session.get('cart', {})
        cart_items = []
        cart_total = 0
        cart_count = 0
        
        print(f"🛒 Cart session data: {cart}")  # Debug
        
        for product_id, item_data in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                
                if isinstance(item_data, dict):
                    quantity = item_data.get('quantity', 1)
                    variant_id = item_data.get('variant_id')
                    
                    variant = None
                    if variant_id:
                        try:
                            variant = ProductVariant.objects.get(id=variant_id)
                        except ProductVariant.DoesNotExist:
                            pass
                    
                    price = variant.price if variant else product.price
                else:
                    quantity = item_data
                    variant = None
                    price = product.price
                
                subtotal = price * quantity
                cart_total += subtotal
                cart_count += quantity  # Sumar la cantidad de cada producto
                
                cart_items.append({
                    'product': product,
                    'variant': variant,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal
                })
                
                print(f"✅ Producto agregado: {product.name}, cantidad: {quantity}")  # Debug
            except Product.DoesNotExist:
                print(f"⚠️ Producto {product_id} no encontrado")  # Debug
                continue
        
        print(f"📊 Total items: {len(cart_items)}, Total count: {cart_count}, Total: {cart_total}")  # Debug
        
        # Renderizar el HTML completo del contenido del sidebar (incluyendo if/else de vacío)
        cart_content_html = render_to_string('cart_sidebar_content.html', {
            'cart_items': cart_items,
            'cart_count': cart_count,
            'cart_total': cart_total
        })
        
        print(f"📤 Enviando respuesta: count={cart_count}, total={cart_total}, HTML length={len(cart_content_html)}")  # Debug
        
        # Preparar items para JSON (mini cart mobile)
        cart_items_json = []
        for item in cart_items:
            cart_items_json.append({
                'id': item['product'].id,
                'name': item['product'].name,
                'quantity': item['quantity'],
                'price': f'${item["price"]:,.0f}',
                'subtotal': f'${item["subtotal"]:,.0f}',
                'image': item['variant'].imagen.url if item['variant'] and item['variant'].imagen else (item['product'].imagen.url if item['product'].imagen else None)
            })
        
        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'cart_total': f'${cart_total:,.0f} COP',
            'cart_content_html': cart_content_html,
            'cart_items': cart_items_json,  # Para mini cart mobile
            'debug': {
                'items_in_cart': len(cart_items),
                'total_quantity': cart_count
            }
        })
        
    except Exception as e:
        print(f"Error in cart_preview: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'cart_count': 0,
            'error': str(e)
        }, status=500)

def register_stock_notification(request):
    """
    Registrar notificación de stock para un producto
    """
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            product_id = data.get('product_id')
            email = data.get('email')
            notification_type = data.get('notification_type', 'stock_available')
            notify_price_drop = data.get('notify_price_drop', False)
            target_price = data.get('target_price')
            notify_low_stock = data.get('notify_low_stock', False)
            
            if not product_id or not email:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto y email son requeridos'
                })
            
            # Validar email
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({
                    'success': False,
                    'message': 'Email inválido'
                })
            
            # Obtener producto
            try:
                product = ProductStore.objects.get(id=product_id)
            except ProductStore.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado'
                })
            
            # Obtener usuario si está logueado
            user = None
            if request.session.get('simple_user_id'):
                try:
                    user = SimpleUser.objects.get(id=request.session['simple_user_id'])
                except SimpleUser.DoesNotExist:
                    pass
            
            # Crear o actualizar notificación
            notification, created = StockNotification.objects.get_or_create(
                product=product,
                email=email,
                notification_type=notification_type,
                defaults={
                    'user': user,
                    'notify_price_drop': notify_price_drop,
                    'target_price': target_price if target_price else None,
                    'notify_low_stock': notify_low_stock,
                }
            )
            
            if not created:
                # Actualizar notificación existente
                notification.status = 'pending'
                notification.notify_price_drop = notify_price_drop
                notification.target_price = target_price if target_price else None
                notification.notify_low_stock = notify_low_stock
                notification.save()
            
            # Mensaje de respuesta
            message = {
                'stock_available': f'Te notificaremos cuando "{product.name}" esté disponible',
                'price_drop': f'Te notificaremos si el precio de "{product.name}" baja',
                'back_in_stock': f'Te notificaremos cuando "{product.name}" regrese al stock',
            }.get(notification_type, 'Notificación registrada exitosamente')
            
            return JsonResponse({
                'success': True,
                'message': message,
                'notification_id': notification.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Datos JSON inválidos'
            })
        except Exception as e:
            print(f"Error in register_stock_notification: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

def send_stock_notifications(product_id, notification_type='stock_available'):
    """
    Enviar notificaciones automáticas cuando un producto vuelve a estar en stock
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils import timezone
        
        product = ProductStore.objects.get(id=product_id)
        
        # Obtener notificaciones pendientes
        notifications = StockNotification.objects.filter(
            product=product,
            notification_type=notification_type,
            status='pending'
        )
        
        sent_count = 0
        failed_count = 0
        
        for notification in notifications:
            try:
                # Personalizar mensaje según tipo de notificación
                if notification_type == 'stock_available':
                    subject = f'¡{product.name} ya está disponible! - CompuEasys'
                    template = 'emails/stock_available.html'
                elif notification_type == 'price_drop':
                    subject = f'¡Precio reducido en {product.name}! - CompuEasys'
                    template = 'emails/price_drop.html'
                elif notification_type == 'back_in_stock':
                    subject = f'¡{product.name} regresó al stock! - CompuEasys'
                    template = 'emails/back_in_stock.html'
                else:
                    subject = f'Notificación de {product.name} - CompuEasys'
                    template = 'emails/generic_notification.html'
                
                # Obtener BASE_URL dinámicamente
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'https://compueasys.onrender.com')
                product_url = f'{base_url}/product/{product.id}/'
                
                # Renderizar email HTML
                html_message = render_to_string(template, {
                    'product': product,
                    'notification': notification,
                    'product_url': product_url,
                    'base_url': base_url
                })
                
                # Mensaje de texto plano como fallback
                text_message = f"""
¡Hola!

Te notificamos que {product.name} ya está disponible.

Precio: ${product.price:,.0f} COP
Stock: {product.stock} unidades

Ver producto: {product_url}

¡No te lo pierdas!

Equipo CompuEasys
                """.strip()
                
                # Enviar email
                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email='notificaciones@compueasys.com',
                    recipient_list=[notification.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Marcar como enviada
                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save()
                
                # Crear log exitoso
                NotificationLog.objects.create(
                    stock_notification=notification,
                    success=True,
                    email_subject=subject
                )
                
                sent_count += 1
                
            except Exception as email_error:
                # Marcar como fallida
                notification.status = 'failed'
                notification.save()
                
                # Crear log de error
                NotificationLog.objects.create(
                    stock_notification=notification,
                    success=False,
                    error_message=str(email_error),
                    email_subject=subject
                )
                
                failed_count += 1
                print(f"Error enviando notificación a {notification.email}: {email_error}")
        
        print(f"Notificaciones enviadas: {sent_count}, Fallidas: {failed_count}")
        return {'sent': sent_count, 'failed': failed_count}
        
    except Exception as e:
        print(f"Error in send_stock_notifications: {e}")
        return {'sent': 0, 'failed': 0, 'error': str(e)}

def check_and_send_price_drop_notifications(product_id, old_price, new_price):
    """
    Verificar y enviar notificaciones de bajada de precio
    """
    try:
        product = ProductStore.objects.get(id=product_id)
        
        # Buscar notificaciones de precio
        price_notifications = StockNotification.objects.filter(
            product=product,
            notification_type='price_drop',
            status='pending',
            notify_price_drop=True
        )
        
        notifications_to_send = []
        
        for notification in price_notifications:
            # Si tiene precio objetivo y el nuevo precio es menor o igual
            if notification.target_price and new_price <= notification.target_price:
                notifications_to_send.append(notification)
            # Si no tiene precio objetivo pero el precio bajó
            elif not notification.target_price and new_price < old_price:
                notifications_to_send.append(notification)
        
        if notifications_to_send:
            return send_stock_notifications(product_id, 'price_drop')
        
        return {'sent': 0, 'failed': 0}
        
    except Exception as e:
        print(f"Error in check_and_send_price_drop_notifications: {e}")
        return {'sent': 0, 'failed': 0, 'error': str(e)}

def get_categories_ajax(request):
    """
    Endpoint para obtener categorías con conteo de productos
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Not AJAX'}, status=400)
    
    try:
        categories_data = []
        for category in Category.objects.all():
            product_count = Product.objects.filter(category=category).count()
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'product_count': product_count
            })
        
        return JsonResponse({
            'success': True,
            'categories': categories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ===== WOMPI PAYMENT VIEWS =====

@csrf_exempt
@require_http_methods(["POST"])
def create_wompi_transaction(request):
    """
    Crear una transacción de Wompi para procesar el pago
    """
    try:
        # Log de la petición
        print(f"🔵 WOMPI Transaction Request - Body: {request.body.decode('utf-8')}")
        
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        customer_email = data.get('customer_email', '').strip()
        discount_code = data.get('discount_code', '')
        discount_amount = float(data.get('discount_amount', 0))
        
        print(f"📊 WOMPI Data - Amount: {amount}, Email: {customer_email}")
        
        # Validar datos
        if amount <= 0:
            print("❌ WOMPI Error: Monto inválido")
            return JsonResponse({
                'error': 'Monto inválido',
                'details': f'Amount received: {amount}'
            }, status=400)
            
        if not customer_email:
            print("❌ WOMPI Error: Email requerido")
            return JsonResponse({
                'error': 'Email requerido'
            }, status=400)
        
        # Crear cliente Wompi con manejo de errores
        try:
            from dashboard.models import WompiConfig
            wompi_config = WompiConfig.objects.first()
            if wompi_config:
                wompi_client = WompiClient(wompi_config)
            else:
                wompi_client = WompiClient()
            print("✅ WOMPI Client creado exitosamente")
        except Exception as e:
            print(f"❌ WOMPI Error creando cliente: {str(e)}")
            return JsonResponse({
                'error': 'Error de configuración de Wompi',
                'details': str(e)
            }, status=500)
        
        # Obtener token de aceptación

        print("🔍 WOMPI Obteniendo acceptance token...")
        acceptance_token = wompi_client.get_acceptance_token()

        # Manejar errores del WompiClient mejorado
        if isinstance(acceptance_token, dict) and 'error' in acceptance_token:
            error_type = acceptance_token.get('error')
            error_message = acceptance_token.get('message', 'Error desconocido')
            print(f"❌ WOMPI Error ({error_type}): {error_message}")
            # Mensajes específicos según el tipo de error
            if error_type == 'timeout':
                return JsonResponse({
                    'error': 'Timeout de conexión con el sistema de pagos. Intenta nuevamente.',
                    'error_type': 'timeout',
                    'details': error_message
                }, status=504)
            elif error_type == 'connection':
                return JsonResponse({
                    'error': 'No se pudo conectar con el sistema de pagos. Verifica tu conexión.',
                    'error_type': 'connection',
                    'details': error_message
                }, status=503)
            elif error_type == 'max_retries_exceeded':
                return JsonResponse({
                    'error': 'El sistema de pagos no está disponible temporalmente. Intenta más tarde.',
                    'error_type': 'service_unavailable',
                    'details': error_message
                }, status=503)
            else:
                return JsonResponse({
                    'error': 'Error obteniendo términos de aceptación del sistema de pagos',
                    'error_type': error_type,
                    'details': error_message
                }, status=500)

        if not acceptance_token:
            print("❌ WOMPI Error: No se pudo obtener acceptance token")
            return JsonResponse({
                'error': 'Error obteniendo términos de aceptación',
                'details': 'No se pudo obtener el acceptance token de Wompi'
            }, status=500)

        # Si el token es un dict con 'acceptance_token', extraer el string
        if isinstance(acceptance_token, dict) and 'acceptance_token' in acceptance_token:
            print(f"✅ WOMPI Acceptance token obtenido: {acceptance_token['acceptance_token'][:20]}...")
            acceptance_token = acceptance_token['acceptance_token']
        else:
            print(f"✅ WOMPI Acceptance token obtenido: {str(acceptance_token)[:20]}...")
        
        # Convertir a centavos para Wompi
        amount_in_cents = int(amount * 100)
        reference = f"compueasys-{int(time.time())}"
        currency = 'COP'
        
        print(f"💰 WOMPI Final data - Cents: {amount_in_cents}, Reference: {reference}")
        
        # Generar firma de integridad (REQUERIDO para producción)
        integrity = None
        if wompi_config and wompi_config.integrity_secret:
            import hashlib
            # Formato: reference + amount_in_cents + currency + integrity_secret
            integrity_string = f"{reference}{amount_in_cents}{currency}{wompi_config.integrity_secret}"
            integrity = hashlib.sha256(integrity_string.encode('utf-8')).hexdigest()
            print(f"🔐 WOMPI Integrity hash generado: {integrity[:20]}...")
        else:
            print("⚠️ WOMPI Warning: No integrity_secret configurado. Esto es REQUERIDO en producción.")
        
        response_data = {
            'success': True,
            'amount_in_cents': amount_in_cents,
            'reference': reference,
            'customer_email': customer_email,
            'acceptance_token': acceptance_token,
            'public_key': settings.WOMPI_PUBLIC_KEY,
            'currency': currency,
            'discount_code': discount_code,
            'discount_amount': discount_amount,
            'environment': settings.WOMPI_ENVIRONMENT,
            'integrity': integrity  # Firma de integridad
        }
        
        print(f"🚀 WOMPI Response: {json.dumps(response_data, indent=2, default=str)}")
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError as e:
        print(f"❌ WOMPI JSON Error: {str(e)}")
        return JsonResponse({
            'error': 'Datos JSON inválidos',
            'details': str(e)
        }, status=400)
        
    except Exception as e:
        print(f"❌ WOMPI Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': 'Error interno del servidor',
            'details': str(e),
            'type': type(e).__name__
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def wompi_webhook(request):
    """
    Webhook para manejar eventos de Wompi
    """
    try:
        payload = request.body
        data = json.loads(payload)
        
        # Log del evento recibido
        logger.info(f"Wompi webhook received: {data}")
        
        # Verificar que es un evento de transacción
        if data.get('event') == 'transaction.updated':
            transaction_data = data.get('data', {}).get('transaction', {})
            transaction_id = transaction_data.get('id')
            status = transaction_data.get('status')
            reference = transaction_data.get('reference')
            amount_in_cents = transaction_data.get('amount_in_cents')
            
            logger.info(f"Transaction {transaction_id} status: {status}")
            
            if status == 'APPROVED':
                # Buscar el pedido por referencia
                try:
                    # La referencia debería ser algo como "compueasys-1234567890"
                    if reference and reference.startswith('compueasys-'):
                        # Buscar pedido que contenga la referencia en la nota o por ID
                        pedidos = Pedido.objects.filter(
                            nota__icontains=reference
                        )
                        
                        if not pedidos.exists():
                            # Intentar buscar por timestamp en la referencia
                            timestamp = reference.replace('compueasys-', '')
                            pedidos = Pedido.objects.filter(
                                nota__icontains=timestamp
                            )
                        
                        for pedido in pedidos:
                            # Actualizar estado del pedido a pagado
                            if 'PAGADO' not in pedido.nota:
                                pedido.nota += f" | PAGADO - Wompi Transaction: {transaction_id}"
                                pedido.save()
                                logger.info(f"Pedido {pedido.id} marcado como pagado con transacción {transaction_id}")
                        
                        if not pedidos.exists():
                            logger.warning(f"No se encontró pedido para referencia: {reference}")
                            
                except Exception as e:
                    logger.error(f"Error actualizando estado del pedido: {e}")
                    
            elif status == 'DECLINED' or status == 'ERROR':
                logger.warning(f"Transaction {transaction_id} fue {status}")
                
        else:
            logger.info(f"Evento no manejado: {data.get('event')}")
        
        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        logger.error("Error parsing webhook JSON")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JsonResponse({'status': 'error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def validate_discount_code(request):
    """Validar código de descuento via AJAX"""
    try:
        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip().upper()
        cart_total = Decimal(str(data.get('cart_total', 0)))
        
        if not codigo:
            return JsonResponse({
                'valid': False,
                'message': 'Código de descuento requerido',
                'discount_amount': 0
            })
        
        # Buscar el bono
        try:
            bono = BonoDescuento.objects.get(codigo__iexact=codigo)
        except BonoDescuento.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'message': 'Código de descuento no válido',
                'discount_amount': 0
            })
        
        # Validar si puede ser usado
        if not bono.can_be_used(cart_total):
            estado = bono.get_estado_display()
            if estado == 'Expirado':
                message = 'Este código ya expiró'
            elif estado == 'Agotado':
                message = 'Este código ya fue usado las veces máximas permitidas'
            elif estado == 'Desactivado':
                message = 'Este código está desactivado'
            elif estado == 'Programado':
                message = 'Este código aún no está vigente'
            elif cart_total < bono.valor_minimo_compra:
                message = f'Compra mínima requerida: ${bono.valor_minimo_compra:,.0f}'
            else:
                message = 'Código no válido para esta compra'
            
            return JsonResponse({
                'valid': False,
                'message': message,
                'discount_amount': 0,
                'bono_info': {
                    'codigo': bono.codigo,
                    'estado': estado,
                    'valor_minimo': float(bono.valor_minimo_compra)
                }
            })
        
        # Calcular descuento
        discount_amount = float(bono.calcular_descuento(cart_total))
        
        return JsonResponse({
            'valid': True,
            'message': f'¡Código aplicado! Descuento: ${discount_amount:,.0f}',
            'discount_amount': discount_amount,
            'bono_info': {
                'codigo': bono.codigo,
                'descripcion': bono.descripcion,
                'tipo': bono.tipo_descuento,
                'valor': float(bono.valor_descuento),
                'valor_minimo': float(bono.valor_minimo_compra),
                'usos_realizados': bono.usos_realizados,
                'usos_maximos': bono.usos_maximos
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'valid': False,
            'message': 'Datos inválidos',
            'discount_amount': 0
        })
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'message': f'Error del servidor: {str(e)}',
            'discount_amount': 0
        })


# ========== VIEWS PARA DASHBOARD DE USUARIO ==========

import random
import string
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.utils import timezone


@csrf_exempt
@require_http_methods(["POST"])
def send_verification_email(request):
    """Enviar código de verificación por email"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        # Generar código de 6 dígitos
        code = ''.join(random.choices(string.digits, k=6))
        
        # Crear token de verificación
        expires_at = timezone.now() + timedelta(minutes=10)  # Expira en 10 minutos
        
        # Obtener SimpleUser
        simple_user = SimpleUser.objects.get(email=request.user.email)
        
        # Eliminar tokens anteriores del mismo tipo
        simple_user.verification_tokens.filter(token_type=action, is_used=False).delete()
        
        # Crear nuevo token
        token = VerificationToken.objects.create(
            user=simple_user,
            token=code,
            token_type=action,
            pending_data=data.get('changes', {}),
            expires_at=expires_at
        )
        
        # Enviar email
        subject = 'Código de Verificación - CompuEasys'
        
        if action == 'profile_update':
            email_subject = 'Verificación para actualizar perfil'
        elif action == 'password_change':
            email_subject = 'Verificación para cambiar contraseña'
        else:
            email_subject = 'Código de verificación'
        
        message = f"""
        Hola {request.user.first_name},
        
        Tu código de verificación es: {code}
        
        Este código expirará en 10 minutos.
        Si no solicitaste este cambio, ignora este mensaje.
        
        Saludos,
        Equipo CompuEasys
        """
        
        send_mail(
            subject,
            message,
            'noreply@compueasys.com',
            [request.user.email],
            fail_silently=False,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Código de verificación enviado exitosamente'
        })
        
    except SimpleUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no encontrado'
        })
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al enviar código de verificación'
        })


@csrf_exempt
@require_http_methods(["POST"])
def verify_code(request):
    """Verificar código y aplicar cambios"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        code = data.get('code')
        changes = data.get('changes', {})
        
        # Obtener SimpleUser
        simple_user = SimpleUser.objects.get(email=request.user.email)
        
        # Buscar token válido
        token = simple_user.verification_tokens.filter(
            token=code,
            is_used=False
        ).first()
        
        if not token or not token.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Código de verificación inválido o expirado'
            })
        
        # Aplicar cambios según el tipo de token
        if token.token_type == 'profile_update':
            # Actualizar datos del usuario
            user = request.user
            if 'first_name' in changes:
                user.first_name = changes['first_name']
            if 'last_name' in changes:
                user.last_name = changes['last_name']
            user.save()
            
            # Actualizar datos del SimpleUser
            if 'phone' in changes:
                simple_user.telefono = changes['phone']
            if 'address' in changes:
                simple_user.address = changes['address']
            if 'city' in changes:
                simple_user.city = changes['city']
            simple_user.save()
            
        elif token.token_type == 'password_change':
            # Cambiar contraseña
            current_password = changes.get('current_password')
            new_password = changes.get('new_password')
            
            if not check_password(current_password, request.user.password):
                return JsonResponse({
                    'success': False,
                    'message': 'Contraseña actual incorrecta'
                })
            
            request.user.set_password(new_password)
            request.user.save()
            
            # Mantener la sesión activa
            update_session_auth_hash(request, request.user)
        
        # Marcar token como usado
        token.is_used = True
        token.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cambios aplicados exitosamente'
        })
        
    except SimpleUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no encontrado'
        })
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al verificar código'
        })


@csrf_exempt
@require_http_methods(["POST"])
def resend_verification_code(request):
    """Reenviar código de verificación"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        # Obtener SimpleUser
        simple_user = SimpleUser.objects.get(email=request.user.email)
        
        # Buscar el último token no usado
        last_token = simple_user.verification_tokens.filter(is_used=False).last()
        
        if not last_token:
            return JsonResponse({
                'success': False,
                'message': 'No hay tokens pendientes para reenviar'
            })
        
        # Generar nuevo código
        code = ''.join(random.choices(string.digits, k=6))
        
        # Actualizar token existente
        last_token.token = code
        last_token.expires_at = timezone.now() + timedelta(minutes=10)
        last_token.save()
        
        # Enviar nuevo email
        subject = 'Nuevo Código de Verificación - CompuEasys'
        message = f"""
        Hola {request.user.first_name},
        
        Tu nuevo código de verificación es: {code}
        
        Este código expirará en 10 minutos.
        
        Saludos,
        Equipo CompuEasys
        """
        
        send_mail(
            subject,
            message,
            'noreply@compueasys.com',
            [request.user.email],
            fail_silently=False,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Nuevo código enviado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error resending code: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al reenviar código'
        })


@require_http_methods(["GET"])
def order_details(request, order_id):
    """Obtener detalles completos de un pedido"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        simple_user = SimpleUser.objects.get(email=request.user.email)
        pedido = Pedido.objects.get(id=order_id, user=simple_user)
        
        # Generar HTML de detalles
        html = f"""
        <div class="order-full-details">
            <div class="row mb-4">
                <div class="col-md-6">
                    <h6>Información del Pedido</h6>
                    <p><strong>ID:</strong> #{pedido.id}</p>
                    <p><strong>Fecha:</strong> {pedido.fecha.strftime('%d/%m/%Y %H:%M')}</p>
                    <p><strong>Estado:</strong> 
                        <span class="status-badge status-{pedido.estado or 'pending'}">
                            {pedido.get_estado_display() or 'Pendiente'}
                        </span>
                    </p>
                    <p><strong>Total:</strong> ${pedido.total:,.0f}</p>
                </div>
                <div class="col-md-6">
                    <h6>Información de Entrega</h6>
                    <p><strong>Cliente:</strong> {request.user.first_name} {request.user.last_name}</p>
                    <p><strong>Email:</strong> {request.user.email}</p>
                    <p><strong>Teléfono:</strong> {simple_user.telefono or 'No especificado'}</p>
                    <p><strong>Dirección:</strong> {simple_user.address or 'No especificada'}</p>
                </div>
            </div>
            
            <div class="mb-4">
                <h6>Detalles de Productos</h6>
                <div class="bg-light p-3 rounded">
                    <pre>{pedido.detalles}</pre>
                </div>
            </div>
            
            {f'<div class="mb-4"><h6>Notas del Pedido</h6><div class="alert alert-info">{pedido.nota}</div></div>' if pedido.nota else ''}
            
            {f'<div class="mb-4"><h6>Novedades del Pedido</h6><div class="alert alert-warning">{pedido.admin_notes}</div></div>' if hasattr(pedido, 'admin_notes') and pedido.admin_notes else ''}
        </div>
        """
        
        return JsonResponse({
            'success': True,
            'html': html
        })
        
    except (SimpleUser.DoesNotExist, Pedido.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Pedido no encontrado'
        })


@csrf_exempt
@require_http_methods(["POST"])
def cancel_order(request):
    """Cancelar un pedido"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        simple_user = SimpleUser.objects.get(email=request.user.email)
        pedido = Pedido.objects.get(id=order_id, user=simple_user)
        
        # Verificar que el pedido se puede cancelar
        if hasattr(pedido, 'estado') and pedido.estado not in ['pending', None]:
            return JsonResponse({
                'success': False,
                'message': 'Este pedido no se puede cancelar porque ya está en proceso'
            })
        
        # Actualizar estado del pedido
        pedido.estado = 'cancelled'
        pedido.nota = 'Pedido cancelado por el cliente'
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Pedido cancelado exitosamente'
        })
        
    except (SimpleUser.DoesNotExist, Pedido.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Pedido no encontrado'
        })
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al cancelar pedido'
        })


@csrf_exempt
@require_http_methods(["POST"])
def start_conversation(request):
    """Iniciar nueva conversación con soporte"""
    # Verificar autenticación mediante sesión
    if not request.session.get('simple_user_id'):
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        message = data.get('message')
        
        if not subject or not message:
            return JsonResponse({
                'success': False,
                'message': 'Asunto y mensaje son requeridos'
            })
        
        # Obtener usuario desde sesión
        user_id = request.session.get('simple_user_id')
        try:
            simple_user = SimpleUser.objects.get(id=user_id)
        except SimpleUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            })
        
        # Crear conversación
        conversation = Conversation.objects.create(
            user=simple_user,
            subject=f"{subject}: {data.get('order_id', 'Consulta general')}"
        )
        
        # Crear primer mensaje
        ConversationMessage.objects.create(
            conversation=conversation,
            user=simple_user,
            message=message,
            is_admin=False
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Consulta enviada exitosamente',
            'conversation_id': conversation.id
        })
        
    except Exception as e:
        print(f"Error en start_conversation: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error al crear conversación: {str(e)}'
        })
        return JsonResponse({
            'success': False,
            'message': 'Usuario no encontrado'
        })
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al crear conversación'
        })


@require_http_methods(["GET"])
def get_conversations(request):
    """Obtener lista de conversaciones del usuario"""
    if not request.session.get('simple_user_id'):
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        user_id = request.session.get('simple_user_id')
        simple_user = SimpleUser.objects.get(id=user_id)
        conversations = Conversation.objects.filter(user=simple_user)
        
        data = []
        for conv in conversations:
            data.append({
                'id': conv.id,
                'subject': conv.subject,
                'last_message': conv.last_message,
                'unread_count': conv.unread_count,
                'updated_at': conv.updated_at.strftime('%d/%m/%Y %H:%M'),
                'status': conv.status
            })
        
        return JsonResponse({
            'success': True,
            'conversations': data
        })
        
    except SimpleUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no encontrado'
        })


@require_http_methods(["GET"])
def get_conversation(request, conversation_id):
    """Obtener mensajes de una conversación específica"""
    if not request.session.get('simple_user_id'):
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        user_id = request.session.get('simple_user_id')
        simple_user = SimpleUser.objects.get(id=user_id)
        conversation = Conversation.objects.get(id=conversation_id, user=simple_user)
        
        # Marcar mensajes como leídos
        conversation.messages.filter(is_admin=True, is_read=False).update(is_read=True)
        
        messages = []
        for msg in conversation.messages.all():
            messages.append({
                'message': msg.message,
                'is_admin': msg.is_admin,
                'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'subject': conversation.subject,
                'status': conversation.status,
                'created_at': conversation.created_at.strftime('%d/%m/%Y'),
                'messages': messages
            }
        })
        
    except (SimpleUser.DoesNotExist, Conversation.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Conversación no encontrada'
        })


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Enviar mensaje en una conversación"""
    if not request.session.get('simple_user_id'):
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        message = data.get('message')
        
        if not conversation_id or not message:
            return JsonResponse({
                'success': False,
                'message': 'ID de conversación y mensaje son requeridos'
            })
        
        user_id = request.session.get('simple_user_id')
        simple_user = SimpleUser.objects.get(id=user_id)
        conversation = Conversation.objects.get(id=conversation_id, user=simple_user)
        
        # Crear mensaje
        ConversationMessage.objects.create(
            conversation=conversation,
            user=simple_user,
            message=message,
            is_admin=False
        )
        
        # Actualizar timestamp de la conversación
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Mensaje enviado exitosamente'
        })
        
    except (SimpleUser.DoesNotExist, Conversation.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Conversación no encontrada'
        })
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al enviar mensaje'
        })

# ========================================
# STOCK NOTIFICATION SYSTEM
# ========================================

@csrf_exempt
@require_http_methods(["POST"])
def register_stock_notification(request):
    """
    Registrar notificación de stock para un producto
    """
    try:
        data = json.loads(request.body)
        
        # Validar datos requeridos
        product_id = data.get('product_id')
        email = data.get('email')
        notification_type = data.get('notification_type', 'stock_available')
        
        if not product_id or not email:
            return JsonResponse({
                'success': False,
                'message': 'Product ID y email son requeridos'
            })
        
        # Validar email
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return JsonResponse({
                'success': False,
                'message': 'Por favor ingresa un email válido'
            })
        
        # Verificar que el producto existe
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Producto no encontrado'
            })
        
        # Verificar que el producto esté sin stock
        if product.stock > 0 and notification_type == 'stock_available':
            return JsonResponse({
                'success': False,
                'message': 'El producto ya está disponible. ¡Agrégalo al carrito!'
            })
        
        # Buscar si ya existe una notificación activa (pendiente)
        existing_notification = StockNotification.objects.filter(
            product=product,
            email=email,
            notification_type=notification_type,
            status='pending'  # Cambiado de is_active=True a status='pending'
        ).first()
        
        if existing_notification:
            return JsonResponse({
                'success': True,
                'message': '¡Ya tienes una notificación activa para este producto!'
            })
        
        # Crear nueva notificación
        notification_data = {
            'product': product,
            'email': email,
            'notification_type': notification_type,
            'status': 'pending'  # Cambiado de is_active=True a status='pending'
        }
        
        # Agregar configuraciones adicionales
        if data.get('notify_price_drop'):
            notification_data['notify_price_drop'] = True
            if data.get('target_price'):
                try:
                    notification_data['target_price'] = Decimal(str(data['target_price']))
                except Exception as e:
                    pass  # Si no se puede convertir, simplemente ignorar
        
        if data.get('notify_low_stock'):
            notification_data['notify_low_stock'] = True
        
        notification = StockNotification.objects.create(**notification_data)
        
        # Respuesta de éxito
        message = f'¡Perfecto! Te notificaremos a {email} cuando "{product.name}" esté disponible.'
        
        if notification_data.get('notify_price_drop'):
            message += ' También te avisaremos si baja de precio.'
        
        if notification_data.get('notify_low_stock'):
            message += ' Y cuando quede poco stock.'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Error in register_stock_notification: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        })

def send_stock_notifications():
    """
    Función para enviar notificaciones de stock
    Se puede llamar desde un cron job o tarea programada
    """
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    import datetime
    
    try:
        # Buscar productos que ahora tienen stock y tienen notificaciones pendientes
        notifications_to_send = StockNotification.objects.filter(
            status='pending',
            notification_type='stock_available',
            product__stock__gt=0
        )
        
        sent_count = 0
        
        for notification in notifications_to_send:
            try:
                # Renderizar email HTML
                context = {
                    'product': notification.product,
                    'email': notification.email,
                    'site_name': 'CompuEasys',
                    'year': datetime.datetime.now().year
                }
                
                html_content = render_to_string('emails/stock_available.html', context)
                
                # Crear email
                subject = f'¡{notification.product.name} ya está disponible!'
                
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=f'El producto {notification.product.name} ya está disponible en CompuEasys.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[notification.email]
                )
                msg.attach_alternative(html_content, "text/html")
                
                # Enviar email
                msg.send()
                
                # Marcar notificación como enviada
                notification.status = 'sent'
                notification.sent_at = datetime.datetime.now()
                notification.save()
                
                # Registrar en log
                NotificationLog.objects.create(
                    stock_notification=notification,
                    success=True,
                    email_subject=subject
                )
                
                sent_count += 1
                
            except Exception as e:
                # Registrar error en log
                NotificationLog.objects.create(
                    stock_notification=notification,
                    success=False,
                    error_message=str(e),
                    email_subject=f'Error: {notification.product.name}'
                )
                
                logger.error(f"Error sending notification for {notification.product.name}: {e}")
        
        logger.info(f"Stock notifications sent: {sent_count}")
        return sent_count
        
    except Exception as e:
        logger.error(f"Error in send_stock_notifications: {e}")
        return 0

def check_price_drops():
    """
    Verificar y notificar bajadas de precio
    """
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    import datetime
    
    try:
        # Buscar notificaciones de precio activas
        price_notifications = StockNotification.objects.filter(
            status='pending',
            notify_price_drop=True,
            product__stock__gt=0
        ).exclude(target_price__isnull=True)
        
        sent_count = 0
        
        for notification in price_notifications:
            # Verificar si el precio actual es menor al objetivo
            if notification.product.price <= notification.target_price:
                try:
                    # Renderizar email HTML
                    context = {
                        'product': notification.product,
                        'target_price': notification.target_price,
                        'current_price': notification.product.price,
                        'email': notification.email,
                        'site_name': 'CompuEasys',
                        'year': datetime.datetime.now().year
                    }
                    
                    html_content = render_to_string('emails/price_drop.html', context)
                    
                    # Crear email
                    subject = f'¡{notification.product.name} bajó de precio!'
                    
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=f'{notification.product.name} ahora cuesta ${notification.product.price:,.0f}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[notification.email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    
                    # Enviar email
                    msg.send()
                    
                    # Marcar notificación como enviada (solo para precio)
                    notification.notify_price_drop = False
                    notification.target_price = None
                    notification.save()
                    
                    # Registrar en log
                    NotificationLog.objects.create(
                        stock_notification=notification,
                        success=True,
                        email_subject=subject
                    )
                    
                    sent_count += 1
                    
                except Exception as e:
                    # Registrar error en log
                    NotificationLog.objects.create(
                        stock_notification=notification,
                        success=False,
                        error_message=str(e),
                        email_subject=f'Error precio: {notification.product.name}'
                    )
                    
                    logger.error(f"Error sending price notification for {notification.product.name}: {e}")
        
        logger.info(f"Price drop notifications sent: {sent_count}")
        return sent_count
        
    except Exception as e:
        logger.error(f"Error in check_price_drops: {e}")
        return 0


# ============================================
# VISTAS PÚBLICAS DE PROYECTOS
# ============================================

def projects(request):
    """Vista pública para mostrar todos los proyectos"""
    from .models import Project
    
    # Obtener proyectos activos
    projects_list = Project.objects.filter(is_active=True).order_by('-order', '-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    if status_filter:
        projects_list = projects_list.filter(status=status_filter)
    
    # Proyectos destacados
    featured_projects = projects_list.filter(is_featured=True)[:3]
    
    # Contar carrito
    cart_count = 0
    if 'cart' in request.session:
        cart_count = sum(item['quantity'] for item in request.session['cart'].values())
    
    context = {
        'projects': projects_list,
        'featured_projects': featured_projects,
        'status_filter': status_filter,
        'status_choices': Project.STATUS_CHOICES,
        'cart_count': cart_count,
    }
    
    return render(request, 'projects.html', context)


def politicas_compras(request):
    """Vista pública para las políticas de compras"""
    return render(request, 'politicas_compras.html')


def project_detail(request, slug):
    """Vista pública para el detalle de un proyecto"""
    from .models import Project
    from django.shortcuts import get_object_or_404
    
    project = get_object_or_404(Project, slug=slug, is_active=True)
    
    # Proyectos relacionados (misma tecnología backend o frontend)
    related_projects = Project.objects.filter(
        Q(backend_tech__icontains=project.backend_tech.split(',')[0]) |
        Q(frontend_tech__icontains=project.frontend_tech.split(',')[0])
    ).exclude(id=project.id).filter(is_active=True)[:3]
    
    # Contar carrito
    cart_count = 0
    if 'cart' in request.session:
        cart_count = sum(item['quantity'] for item in request.session['cart'].values())
    
    context = {
        'project': project,
        'related_projects': related_projects,
        'cart_count': cart_count,
    }
    
    return render(request, 'project_detail.html', context)