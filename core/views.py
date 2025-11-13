from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail  
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import urllib.parse
from django.http import JsonResponse, HttpResponseRedirect
from dashboard.models import register_superuser
from .models import Category, Type, Galeria, SimpleUser, Pedido, ProductVariant, ProductStore as Product, PedidoDetalle, BonoDescuento
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
    return render(request, 'home.html')

def wompi_test(request):
    """Vista de test para verificar configuración de Wompi"""
    context = {
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY,
        'wompi_environment': settings.WOMPI_ENVIRONMENT,
    }
    return render(request, 'wompi_test.html', context)

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']        
        password = request.POST['password']       
        superuser_qs = register_superuser.objects.filter(username=username)
        if superuser_qs.exists():           
            superuser = superuser_qs.first()
            if superuser.password == password:
                request.session['superuser_id'] = superuser.id
                request.session['superuser_username'] = superuser.username
                return redirect('/dashboard/dashboard_home')  
            else:
                return render(request, 'login_user.html', {'error': 'Contraseña incorrecta'})
        return render(request, 'login_user.html', {'error': 'El usuario no está registrado'})
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('/dashboard/dashboard_home')
            else:
                return redirect('/mis-pedidos')
        else:
            return render(request, 'login_user.html', {'error': 'Credenciales incorrectas'})
    return render(request, 'login_user.html')

def store(request):
    """
    Vista principal de la tienda con filtros modernos y AJAX
    """
    # Obtener parámetros de filtro
    query = request.GET.get('q', '')
    print(query)
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
    try:
        product = Product.objects.get(id=product_id)        
        Galeria_images = product.galeria.all()
        cart = request.session.get('cart', {})
        cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
        context = {
            'product': product, 
            'Galeria_images': Galeria_images,
            'cart_count': cart_count
            }       
        return render(request, 'product_detail.html', context)
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)

def checkout(request, note=None):
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

    

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'nota': nota,
        'departament_selected': departament_selected,
        'departamentos': DEPARTAMENTOS_CIUDADES,
        'ciudades': ciudades,
        'cart_count': sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()]),
        'saved': saved,
        'wompi_public_key': settings.WOMPI_PUBLIC_KEY
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

        # Crear o actualizar SimpleUser
        user, created = SimpleUser.objects.get_or_create(email=email, defaults={'telefono': telefono})
        if not created:
            user.telefono = telefono
            user.save()

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

        # Calcular envío según método de pago
        if metodo_pago == 'recoger_tienda':
            shipping_cost = Decimal(0)  # Siempre gratis para recoger en tienda
        else:
            shipping_cost = Decimal(15000) if cart_subtotal < Decimal(100000) else Decimal(0)
        
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
        if metodo_pago == 'recoger_tienda':
            detalles += f"🏪 Método: Recoger en tienda - Envío GRATIS\n"
        elif shipping_cost > 0:
            detalles += f"📦 Costo de envío: ${shipping_cost:,.0f}\n"
        else:
            detalles += f"📦 Envío: GRATIS\n"

        # Determinar estado inicial del pago
        estado_pago_inicial = 'pendiente'
        if metodo_pago in ['tarjeta', 'wompi'] and transaction_id:
            estado_pago_inicial = 'completado'

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
            nota=nota,  # Usar nota original sin modificar
            estado='pendiente',  # Estado inicial
            metodo_pago=metodo_pago,  # Método de pago correcto
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
        user = User.objects.create_user(username=username, email=email, password=password)
       
        user.save()
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
        return redirect('login_user')
    return render(request, 'register_user.html')

def index(request):
    return render(request, "index.html")

# ...existing code...
def cart(request):
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

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count
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
            if action == 'set':
                # Solo permite hasta el stock disponible
                if variant_id:
                    stock = ProductVariant.objects.get(id=variant_id).stock
                    price = ProductVariant.objects.get(id=variant_id).precio
                else:
                    stock = Product.objects.get(id=product_id).stock
                    price = Product.objects.get(id=product_id).price
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
                    q = v
                    try:
                        p = Product.objects.get(id=k).price
                    except:
                        p = 0
                cart_total += p * q
                cart_count += q

            return JsonResponse({
                'success': True,
                'subtotal': subtotal,      # sin formato
                'quantity': quantity,      # 🔄 Agregar cantidad actualizada
                'cart_total': cart_total,  # sin formato
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
    return redirect('cart')

def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
    return redirect('cart')

# ...existing code...
def mis_pedidos(request):
    # Busca el usuario por email (puedes adaptar a tu sistema de login)
    if request.user.is_authenticated:
        email = request.user.email
        try:
            simple_user = SimpleUser.objects.get(email=email)
            pedidos = Pedido.objects.filter(user=simple_user).order_by('-fecha')
            message = "" if pedidos.exists() else "Aún no tienes pedidos para visualizar."
        except SimpleUser.DoesNotExist:
            pedidos = []
            message = "Aún no tienes pedidos para visualizar."
    else:
        return redirect('login')  # O muestra un mensaje de error

    return render(request, 'mis_pedidos.html', {'pedidos': pedidos, 'message': message})
# ...existing code...

def logout_view(request):
    logout(request)
    return redirect('store')  # Redirect to your homepage or login page



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
        
        # Filtro de stock
        if in_stock and not out_of_stock:
            products = products.filter(stock__gt=0)
        elif out_of_stock and not in_stock:
            products = products.filter(stock=0)
        elif not in_stock and not out_of_stock:
            products = products.none()  # No mostrar nada si ambos están desactivados
        
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
        data = json.loads(request.body)
        amount = int(data.get('amount', 0))
        customer_email = data.get('customer_email', '')
        discount_code = data.get('discount_code', '')
        discount_amount = float(data.get('discount_amount', 0))
        
        # Validar datos
        if amount <= 0:
            return JsonResponse({
                'error': 'Monto inválido'
            }, status=400)
            
        if not customer_email:
            return JsonResponse({
                'error': 'Email requerido'
            }, status=400)
        
        # Crear cliente Wompi
        wompi_client = WompiClient()
        
        # Obtener token de aceptación
        acceptance_token = wompi_client.get_acceptance_token()
        
        # Convertir a centavos para Wompi
        amount_in_cents = int(amount * 100)
        reference = f"compueasys-{int(time.time())}"
        
        return JsonResponse({
            'success': True,
            'amount_in_cents': amount_in_cents,
            'reference': reference,
            'customer_email': customer_email,
            'acceptance_token': acceptance_token,
            'public_key': settings.WOMPI_PUBLIC_KEY,
            'currency': 'COP',
            'discount_code': discount_code,
            'discount_amount': discount_amount
        })
        
    except Exception as e:
        logger.error(f"Error creating Wompi transaction: {str(e)}")
        return JsonResponse({
            'error': 'Error interno del servidor'
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
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
    except Exception as e:
        logger.error(f"Error en webhook de Wompi: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


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