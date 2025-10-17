from django.contrib.auth.decorators import login_required, permission_required
from core.models import ProductStore, Pedido, SimpleUser, Category, Type, proveedor, Galeria, ProductVariant
from django.contrib.auth.models import User
from dashboard.models import register_superuser
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from functools import wraps
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('superuser_id'):
            return view_func(request, *args, **kwargs)
        return redirect('/login_user/?next=' + request.path)
    return _wrapped_view

@superuser_required
def dashboard_home(request):
    productos = ProductStore.objects.all()
    categorias = Category.objects.all()
    tipos = Type.objects.all()
    proveedores = proveedor.objects.all()
    userSimples = register_superuser.objects.all()
    show_create_product_form = request.GET.get('view') == 'productos' and request.GET.get('crear') == '1'

    if request.method == 'POST' and show_create_product_form:
        name = request.POST.get('name')
        description = request.POST.get('description')
        price_buy = float(request.POST.get('price_buy', 0))
        price = float(request.POST.get('price', 0))
        stock = int(request.POST.get('stock', 0))
        descuento = float(request.POST.get('descuento', 0))
        iva = float(request.POST.get('iva', 0))
        imagen = request.FILES.get('images')
        galeria_files = request.FILES.getlist('galeria')

        # Proveedor (opcional)
        proveedor_id = request.POST.get('proveedor')
        proveedor_obj = None
        if proveedor_id:
            try:
                proveedor_obj = proveedor.objects.get(id=proveedor_id)
            except proveedor.DoesNotExist:
                proveedor_obj = None

        # Categoría (opcional)
        categoria_id = request.POST.get('categoria')
        category_obj = None
        if categoria_id:
            try:
                category_obj = Category.objects.get(id=categoria_id)
            except Category.DoesNotExist:
                category_obj = None

        # Tipo de producto (opcional)
        type_id = request.POST.get('type')
        type_obj = None
        if type_id:
            try:
                type_obj = Type.objects.get(id=type_id)
            except Type.DoesNotExist:
                type_obj = None

        # Crear producto
        product = ProductStore.objects.create(
            name=name,
            description=description,
            price_buy=price_buy,
            price=price,
            stock=stock,
            proveedor=proveedor_obj,
            category=category_obj,
            iva=iva,
            descuento=descuento,
            type=type_obj,
            imagen=imagen
        )

        

        # Galería (ManyToMany)
        for img in galeria_files:
            galeria_obj = Galeria.objects.create(galeria=img, product=product)  # Usa el nombre real del campo de imagen
            product.galeria.add(galeria_obj)

        # Variantes (si tienes modelo Variante)
        variante_nombres = request.POST.getlist('variante_nombre[]')
        variante_precio = request.POST.getlist('variante_precio[]')
        variante_imagenes = request.FILES.getlist('variante_imagen[]')
        variante_stock = request.POST.getlist('variante_stock[]')
        variante_color = request.POST.getlist('variante_color[]')
        variante_talla = request.POST.getlist('variante_talla[]')
        for nombre, precio, stock, color, talla, img in zip(variante_nombres, variante_precio, variante_stock, variante_color, variante_talla, variante_imagenes):
            if nombre and precio:
                ProductVariant.objects.create(
                    product=product,
                    nombre=nombre,
                    precio=precio,
                    stock=stock,
                    color=color,
                    talla=talla,
                    imagen=img
                    )

        return redirect('dashboard_home')

    return render(request, 'dashboard/dashboard_home.html', {
        'productos': productos,
        'categorias': categorias,
        'tipos': tipos,
        'proveedores': proveedores,
        'usuarios': userSimples,
        'show_create_product_form': show_create_product_form,
    })

@superuser_required
def dar_permiso_staff(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    usuario.is_staff = True
    usuario.save()
    return redirect('dashboard_home')

@superuser_required
def eliminar_usuario(request, user_id):
    success = False
    if request.method == 'POST':
        try:
            usuario = register_superuser.objects.get(id=user_id)
            usuario.delete()
            success = True
        except register_superuser.DoesNotExist:
            success = False
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': success})
    return redirect('dashboard_home')

@superuser_required
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')
        usuario.save()
        return redirect('dashboard_home')
    return render(request, 'dashboard/editar_usuario.html', {'usuario': usuario})






@superuser_required
def edit_product(request, product_id):
    product = get_object_or_404(ProductStore, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = float(request.POST.get('price', product.price))
        product.stock = int(request.POST.get('stock', product.stock))
        product.categoria = request.POST.get('categoria', product.categoria)
        product.iva = float(request.POST.get('iva', product.iva))
        product.descuento = float(request.POST.get('descuento', product.descuento))

        if 'images' in request.FILES:
            product.imagen = request.FILES['images']

        if 'galeria' in request.FILES:
            galeria_files = request.FILES.getlist('galeria')
            for img in galeria_files:
                galeria_obj = Galeria.objects.create(image=img)
                product.galeria.add(galeria_obj)

        product.save()
        return redirect('dashboard_home')

    return render(request, 'dashboard/editar_producto.html', {'product': product})
@superuser_required
def delete_product(request, product_id):
    product = get_object_or_404(ProductStore, id=product_id)
    product.delete()
    return redirect('dashboard_home')           



@superuser_required
def crear_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            Category.objects.create(nombre=nombre)
    return redirect('dashboard_home')  # O la vista que corresponda

@superuser_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return redirect('dashboard_home')

@superuser_required
def editar_categoria(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            category.nombre = nombre
            category.save()
            return redirect('dashboard_home')
    return render(request, 'dashboard/editar_categoria.html', {'category': category})        



# ...existing code...


def api_get_product(request, product_id):
    try:
        producto = Product.objects.get(id=product_id)  # ajusta el modelo si se llama distinto
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    # main image
    try:
        imagen_url = producto.imagen.url if producto.imagen else ''
    except Exception:
        imagen_url = ''

    # gallery: intenta varios patrones según tu modelo
    gallery_urls = []
    # si tienes relación product.galeria_set o product.galeria
    if hasattr(producto, 'galeria'):
        try:
            for f in producto.galeria.all():
                if hasattr(f, 'imagen'):
                    gallery_urls.append(f.imagen.url)
                elif hasattr(f, 'url'):
                    gallery_urls.append(f.url)
        except Exception:
            pass
    # fallback: si tienes campo galeria como texto separado por comas
    if not gallery_urls:
        gal_text = getattr(producto, 'galeria', '') or ''
        if isinstance(gal_text, str) and gal_text:
            for p in gal_text.split(','):
                p = p.strip()
                if p:
                    gallery_urls.append(p)

    data = {
        'id': producto.id,
        'name': producto.name,
        'description': producto.description,
        'price_buy': getattr(producto, 'price_buy', ''),
        'price': getattr(producto, 'price', ''),
        'stock': getattr(producto, 'stock', ''),
        'descuento': getattr(producto, 'descuento', ''),
        'iva': getattr(producto, 'iva', ''),
        'proveedor_id': getattr(producto.proveedor, 'id', '') if getattr(producto, 'proveedor', None) else '',
        'categoria_id': getattr(producto.categoria, 'id', '') if getattr(producto, 'categoria', None) else '',
        'type_id': getattr(producto.type, 'id', '') if getattr(producto, 'type', None) else '',
        'imagen': imagen_url,
        'gallery': gallery_urls,
        'update_url': reverse('edit_product', args=[producto.id]) if 'edit_product' in [u.name for u in []] else '',  # placeholder
    }
    return JsonResponse(data)
# ...existing code...   