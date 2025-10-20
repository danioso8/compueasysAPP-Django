from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail  
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import urllib.parse
from django.http import JsonResponse, HttpResponseRedirect
from dashboard.models import register_superuser
from .models import Category, Type, Galeria, SimpleUser, Pedido, ProductVariant, ProductStore as Product, PedidoDetalle

from django.conf import settings
import json

# Create your views here.
def home(request):
    return render(request, 'home.html')

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
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    categories = Category.objects.all()
    products = Product.objects.all()
    cart = request.session.get('cart', {})
    cart_count = sum([item['quantity'] if isinstance(item, dict) else item for item in cart.values()])
    # Filtrar productos por nombre o categoría si se proporciona una consulta de búsqueda o categoría
    if query:
        products = products.filter(name__icontains=query)
    if category_id:
        products = products.filter(category_id=category_id)
    context = {
        'products': products, 
        'categories': categories,
        'cart_count': cart_count
        }
   
    return render(request, 'store.html', context)
   
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
    cart_total = 0
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
        'saved': saved
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
        cart_total = 0
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
            cart_total += subtotal

        # Organiza el detalle de productos para WhatsApp
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

        # Guardar pedido
        pedido = Pedido.objects.create(
            user=user,
            nombre=nombre,
            direccion=direccion,
            ciudad=ciudad,
            departamento=departamento,
            codigo_postal=codigo_postal,
            total=cart_total,
            detalles=detalles,
            nota=nota
        )

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

        # Enviar correo al usuario
        subject = "Confirmación de tu compra en CompuEasys"
        message = (
            f"¡Hola {nombre}!\n\n"
            f"Gracias por tu compra en CompuEasys.\n\n"
            f"Resumen de tu pedido:\n{detalles}\n"
            f"Total: ${cart_total}\n"
            f"Dirección: {direccion}, {ciudad}, {departamento}, CP: {codigo_postal}\n\n"
            f"Se ha creado una cuenta para ti con el email: {email}\n"
            f"Tu contraseña temporal es tu número de celular: {telefono}\n"
            f"Puedes cambiarla cuando quieras desde la tienda.\n\n"
            f"¡Gracias por confiar en nosotros!"
        )
        send_mail(subject, message, None, [email])

        # Generar link de WhatsApp ORDENADO
        mensaje = (
            f"🛒 *Nuevo pedido de {nombre}*\n\n"
            f"*Productos:*\n"
            f"{detalles}\n"
            f"*Total:* ${cart_total}\n\n"
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
            'whatsapp_url': whatsapp_url
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
    cart_total = 0
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

            subtotal = price * quantity

            # Calcula total del carrito y cantidad total
            cart_total = 0
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

    if key in cart and isinstance(cart[key], int):
        cart[key] = {
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': cart[key],
        }
    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': quantity,
        }
    request.session['cart'] = cart

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
     # --- Unifica formato antiguo a nuevo ---
    if key in cart and isinstance(cart[key], int):
        cart[key] = {
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': cart[key],
        }    
    # Si ya existe ese producto+variante, suma la cantidad
    if key in cart:
        cart[key]['quantity'] += quantity
    else:
     # Usa una clave única para producto+variante
     key = f"{product_id}-{variant_id}" if variant_id else str(product_id)
     cart[key] = {
        'product_id': product_id,
        'variant_id': variant_id,
        'quantity': quantity,
    }
    request.session['cart'] = cart
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