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
    crear_producto_url = f"{reverse('dashboard_home')}?view=productos&crear=1"
    productos = ProductStore.objects.all()
    categorias = Category.objects.all()
    tipos = Type.objects.all()
    proveedores = proveedor.objects.all()
    userSimples = register_superuser.objects.all()
    show_create_product_form = request.GET.get('view') == 'productos' and request.GET.get('crear') == '1'

    # ...existing code...
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

        # Crear producto (sin argumentos repetidos)
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
            galeria_obj = Galeria.objects.create(galeria=img, product=product)
            product.galeria.add(galeria_obj)

        # Variantes
        variante_nombres = request.POST.getlist('variante_nombre[]')
        variante_precio = request.POST.getlist('variante_precio[]')
        variante_imagenes = request.FILES.getlist('variante_imagen[]')
        variante_stock = request.POST.getlist('variante_stock[]')
        variante_color = request.POST.getlist('variante_color[]')
        variante_talla = request.POST.getlist('variante_talla[]')
        for nombre, precio, stock_v, color, talla, img in zip(variante_nombres, variante_precio, variante_stock, variante_color, variante_talla, variante_imagenes):
            if nombre and precio:
                ProductVariant.objects.create(
                    product=product,
                    nombre=nombre,
                    precio=precio,
                    stock=stock_v,
                    color=color,
                    talla=talla,
                    imagen=img
                )

        return redirect(crear_producto_url)
# ...existing code...
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

# ...existing code...
def create_proveedor(request):
    redirect_url = f"{reverse('dashboard_home')}?view=proveedores"

    if request.method == 'POST':
        data = {
            'nombre': request.POST.get('nombre'),
            'cedulaOnita': request.POST.get('cedulaOnita'),
            'email': request.POST.get('email'),
            'telefono': request.POST.get('telefono'),
            'direccion': request.POST.get('direccion'),
        }

        model = proveedor
        try:
            model_field_names = [f.name for f in model._meta.fields]
        except Exception as e:
            print('create_proveedor: objeto "proveedor" no es un modelo:', e)
            return redirect(redirect_url)

        create_kwargs = {k: v for k, v in data.items() if k in model_field_names and v not in (None, '')}

        try:
            if create_kwargs:
                model.objects.create(**create_kwargs)
        except TypeError as e:
            print('create_proveedor TypeError:', e)
            if data.get('nombre'):
                try:
                    model.objects.create(nombre=data.get('nombre'))
                except Exception as e2:
                    print('create_proveedor fallback error:', e2)
        except Exception as e:
            print('create_proveedor error:', e)

    return redirect(redirect_url)
# ...existing code...

@superuser_required
def edit_proveedor(request, proveedor_id):
    proveedor_obj = get_object_or_404(proveedor, id=proveedor_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            proveedor_obj.nombre = nombre
            proveedor_obj.save()
            return redirect('dashboard_home')
    return render(request, 'dashboard/editar_proveedor.html', {'proveedor': proveedor_obj})

@superuser_required 
def delete_proveedor(request, proveedor_id):
    redirect_url = f"{reverse('dashboard_home')}?view=proveedores"
    proveedor_obj = get_object_or_404(proveedor, id=proveedor_id)
    proveedor_obj.delete()
    return redirect(redirect_url)





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



@superuser_required
def crear_tipo(request):
    crear_tipo_url = f"{reverse('dashboard_home')}?view=tipos"
    if request.method == 'POST':
        # aceptar 'name' o 'nombre' desde el formulario
        nombre = request.POST.get('name') or request.POST.get('nombre')
        if nombre:
            # escoger campo correcto según el modelo Type
            field_names = [f.name for f in Type._meta.fields]
            field = 'nombre' if 'nombre' in field_names else 'name'
            Type.objects.create(**{field: nombre})
    return redirect(crear_tipo_url)

@superuser_required
def edit_tipo(request, tipo_id):
    redirect_url = f"{reverse('dashboard_home')}?view=tipos"
    tipo = get_object_or_404(Type, id=tipo_id)
    if request.method == 'POST':
        nombre = request.POST.get('name') or request.POST.get('nombre')
        if nombre:
            field_names = [f.name for f in Type._meta.fields]
            field = 'nombre' if 'nombre' in field_names else 'name'
            setattr(tipo, field, nombre)
            tipo.save()
            return redirect(redirect_url)
    return render(request, 'dashboard/editar_tipo.html', {'tipo': tipo})

@superuser_required
def delete_tipo(request, tipo_id):
    crear_tipo_url = f"{reverse('dashboard_home')}?view=tipos"
    tipo = get_object_or_404(Type, id=tipo_id)
    tipo.delete()
    return redirect(crear_tipo_url)


# ...existing code...
def api_get_product(request, product_id):
    try:
        producto = ProductStore.objects.get(id=product_id)
    except ProductStore.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    # imagen principal
    try:
        imagen_url = producto.imagen.url if getattr(producto, 'imagen', None) else ''
    except Exception:
        imagen_url = ''

    # galería
    gallery_urls = []
    if hasattr(producto, 'galeria'):
        try:
            for f in producto.galeria.all():
                if getattr(f, 'imagen', None):
                    gallery_urls.append(f.imagen.url)
                elif getattr(f, 'image', None):
                    gallery_urls.append(f.image.url)
        except Exception:
            pass

    data = {
        'id': producto.id,
        'name': getattr(producto, 'name', '') or getattr(producto, 'nombre', ''),
        'description': getattr(producto, 'description', '') or getattr(producto, 'descripcion', ''),
        'price_buy': getattr(producto, 'price_buy', ''),
        'price': getattr(producto, 'price', ''),
        'stock': getattr(producto, 'stock', ''),
        'descuento': getattr(producto, 'descuento', ''),
        'iva': getattr(producto, 'iva', ''),
        'proveedor_id': getattr(getattr(producto, 'proveedor', None), 'id', '') if getattr(producto, 'proveedor', None) else '',
        'categoria_id': getattr(getattr(producto, 'category', None), 'id', '') if getattr(producto, 'category', None) else '',
        'type_id': getattr(getattr(producto, 'type', None), 'id', '') if getattr(producto, 'type', None) else '',
        'imagen': imagen_url,
        'gallery': gallery_urls,
        'update_url': reverse('edit_product', args=[producto.id]) if 'edit_product' else '',
    }
    return JsonResponse(data)
# ...existing code...