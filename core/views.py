from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Category, Type, Galeria, SimpleUser, Pedido, ProductStore as Product
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail  
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

# Create your views here.
def home(request):
    return render(request, 'home.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('mis_pedidos')
        else:
            return render(request, 'login.html', {'error': 'Credenciales incorrectas'})
    return render(request, 'login_user.html')

def store(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    categories = Category.objects.all()
    products = Product.objects.all()
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())   
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
        cart_count = sum(cart.values())
        context = {
            'product': product, 
            'Galeria_images': Galeria_images,
            'cart_count': cart_count
            }       
        return render(request, 'product_detail.html', context)
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)

def checkout(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    for prod_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=prod_id)
            subtotal = product.price * quantity
            cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
            cart_total += subtotal
        except Product.DoesNotExist:
            continue
    context = {'cart_items': cart_items, 'cart_total': cart_total, 'cart_count': sum(cart.values())}
    return render(request, 'checkout.html', context)


def pago_exitoso(request):
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
        for prod_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=prod_id)
                subtotal = product.price * quantity
                cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
                cart_total += subtotal
                detalles += f"{product.name} x{quantity} - ${subtotal}\n"
            except Product.DoesNotExist:
                continue

        # Guardar pedido
        pedido = Pedido.objects.create(
            user=user,  # Usa SimpleUser, porque tu modelo Pedido espera SimpleUser
            nombre=nombre,
            direccion=direccion,
            ciudad=ciudad,
            departamento=departamento,
            codigo_postal=codigo_postal,
            total=cart_total,
            detalles=detalles
        )

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

        # Generar link de WhatsApp
        import urllib.parse
        mensaje = f"Hola, soy {nombre}. Mi pedido:\n{detalles}\nTotal: ${cart_total}\nDirección: {direccion}, {ciudad}, {departamento}, CP: {codigo_postal}\nTeléfono: {telefono}"
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


def register(request):
    return render(request, 'register.html')


def index(request):
    return render(request, "index.html")

def cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    for prod_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=prod_id)
            subtotal = product.price * quantity
            cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
            cart_total += subtotal
        except Product.DoesNotExist:
            continue
    context = {'cart_items': cart_items, 'cart_total': cart_total, 'cart_count': sum(cart.values())}
    return render(request, 'cart.html', context)
    
def update_cart(request, product_id):   
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        # Logic to update the cart item quantity goes here
        return redirect('cart', product_id=product_id)
    return HttpResponse("Invalid request", status=400)

def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = request.session.get('cart', {})
   
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
    else:
        quantity = 1
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    request.session['cart'] = cart

    # Si la petición es AJAX, responde con el contenido del carrito
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_items = []
        cart_total = 0
        for prod_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=prod_id)
                cart_items.append({'product_name': product.name, 'quantity': quantity, 'price': product.price, 'subtotal': product.price * quantity})
                cart_precio = product.price*quantity
                cart_total += cart_precio
                
            except Product.DoesNotExist:
                continue
        return JsonResponse({'cart_items': cart_items, 'cart_total': cart_total,  'cart_count': sum(cart.values())})
    return redirect('store')

def add_to_cart_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
    else:
        quantity = 1
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    request.session['cart'] = cart

    # Si la petición es AJAX, responde con el contenido del carrito
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_items = []
        cart_total = 0
        for prod_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=prod_id)
                cart_items.append({'product_name': product.name, 'quantity': quantity, 'price': product.price, 'subtotal': product.price * quantity})
                cart_precio = product.price*quantity
                cart_total += cart_precio
                
            except Product.DoesNotExist:
                continue
        return JsonResponse({'cart_items': cart_items, 'cart_total': cart_total,  'cart_count': sum(cart.values())})
    return redirect('cart')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')

def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
    return redirect('cart')

def mis_pedidos(request):
    # Busca el usuario por email (puedes adaptar a tu sistema de login)
    if request.user.is_authenticated:
        email = request.user.email
        try:
            simple_user = SimpleUser.objects.get(email=email)
        except SimpleUser.DoesNotExist:
            return HttpResponse("No tienes pedidos registrados.", status=404)
        pedidos = Pedido.objects.filter(user=simple_user).order_by('-fecha')
    else:
        return redirect('login')  # O muestra un mensaje de error

    return render(request, 'mis_pedidos.html', {'pedidos': pedidos})    