from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Category, Type, Galeria,  ProductStore as Product
from django.db.models import Q
from django.http import JsonResponse




# Create your views here.
def home(request):
    return render(request, 'home.html')


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
    return render(request, 'checkout.html')

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

def login(request):
    return render(request, 'login.html')

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