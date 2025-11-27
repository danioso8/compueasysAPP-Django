from functools import wraps
from django.shortcuts import redirect, render
from django.contrib import messages
from django.db.models import Q

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('superuser_id'):
            return view_func(request, *args, **kwargs)
        return redirect('/login_user/?next=' + request.path)
    return _wrapped_view

from .models import WompiConfig

# Vista para configuración global de Wompi
@superuser_required
def wompi_config_view(request):
    config = WompiConfig.objects.first()
    if not config:
        config = WompiConfig.objects.create(
            public_key='', private_key='', environment='production', base_url='https://production.wompi.co/v1')

    if request.method == 'POST':
        config.public_key = request.POST.get('public_key', config.public_key)
        config.private_key = request.POST.get('private_key', config.private_key)
        config.environment = request.POST.get('environment', config.environment)
        config.base_url = request.POST.get('base_url', config.base_url)
        config.save()
        messages.success(request, 'Configuración Wompi actualizada correctamente.')
        return redirect('wompi_config')

    return render(request, 'dashboard/wompi_config.html', {'config': config})
from django.contrib.auth.decorators import login_required, permission_required
from core.models import ProductStore, Pedido, SimpleUser, Category, Type, proveedor, Galeria, ProductVariant, PedidoDetalle, BonoDescuento, Conversation, ConversationMessage
from django.contrib.auth.models import User
from dashboard.models import register_superuser
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from functools import wraps
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('superuser_id'):
            return view_func(request, *args, **kwargs)
        return redirect('/login_user/?next=' + request.path)
    return _wrapped_view



@superuser_required
def dashboard_home(request):
    from core.models import StoreVisit
    Pedidos = [];
    categorias = [];
    crear_producto_url = f"{reverse('dashboard_home')}?view=productos"
    
    # Obtener información del usuario autenticado
    superuser_id = request.session.get('superuser_id')
    current_user = None
    is_superuser = False
    is_staff = False
    
    if superuser_id:
        try:
            current_user = register_superuser.objects.get(id=superuser_id)
            is_superuser = current_user.is_superuser
            is_staff = current_user.is_staff
        except register_superuser.DoesNotExist:
            pass

    # Filtros y paginación para productos
    view_param = request.GET.get('view', 'ventas')  # 'ventas' por defecto

    # Si el usuario selecciona 'Configurar Wompi', preparar config para el contexto
    config = None
    if view_param == 'wompi_config':
        from .models import WompiConfig
        config = WompiConfig.objects.first()
        if not config:
            config = WompiConfig.objects.create(
                public_key='', private_key='', environment='production', base_url='https://production.wompi.co/v1')
        if request.method == 'POST':
            config.public_key = request.POST.get('public_key', config.public_key)
            config.private_key = request.POST.get('private_key', config.private_key)
            config.environment = request.POST.get('environment', config.environment)
            config.base_url = request.POST.get('base_url', config.base_url)
            config.save()
            messages.success(request, 'Configuración Wompi actualizada correctamente.')

    # Si el usuario selecciona 'Datos de mi tienda', puedes preparar datos aquí si lo necesitas

    # Obtener filtros para productos
    categoria_filter = request.GET.get('categoria_filter', '')
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    # Base queryset para productos
    productos_queryset = ProductStore.objects.select_related('category', 'proveedor', 'type').all().order_by('-id')

    # Aplicar filtros
    if categoria_filter:
        try:
            categoria_filter_id = int(categoria_filter)
            productos_queryset = productos_queryset.filter(category_id=categoria_filter_id)
        except (ValueError, TypeError):
            pass

    if search_query:
        productos_queryset = productos_queryset.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Paginación para productos
    productos_paginator = Paginator(productos_queryset, 10)  # 10 productos por página
    try:
        productos_page = productos_paginator.page(page_number)
    except PageNotAnInteger:
        productos_page = productos_paginator.page(1)
    except EmptyPage:
        productos_page = productos_paginator.page(productos_paginator.num_pages)

    # Para compatibilidad con el código existente
    productos = productos_page.object_list

    categorias = Category.objects.all()
    tipos = Type.objects.all()
    proveedores = proveedor.objects.all()

    # Obtener todos los usuarios: SimpleUser y register_superuser combinados
    simple_users = SimpleUser.objects.all()
    admin_users = register_superuser.objects.all()

    # Crear una lista combinada de usuarios con información de tipo
    all_users = []

    # Agregar usuarios simples
    for user in simple_users:
        all_users.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': getattr(user, 'telefono', ''),  # Corregido: telefono en lugar de phone
            'address': getattr(user, 'address', ''),
            'city': getattr(user, 'city', ''),
            'date_joined': getattr(user, 'created_at', 'N/A'),
            'username': getattr(user, 'username', ''),
            'is_admin': False,
            'user_type': 'simple',
            'model_type': 'SimpleUser'
        })

    # Agregar usuarios administradores
    for user in admin_users:
        all_users.append({
            'id': user.id,
            'name': getattr(user, 'username', ''),  # register_superuser usa username como name
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'address': getattr(user, 'address', ''),
            'city': getattr(user, 'city', ''),
            'date_joined': getattr(user, 'created_at', user.created_at),
            'username': user.username,
            'is_admin': True,
            'user_type': 'admin',
            'model_type': 'register_superuser'
        })

    userSimples = all_users  # Mantenemos el nombre para compatibilidad
    bonos = BonoDescuento.objects.all().order_by('-fecha_creacion')

    # Obtener pedidos con filtros
    pedidos_queryset = Pedido.objects.select_related('user').all().order_by('-fecha')

    # VISITAS RECIENTES Y RESUMEN
    visitas_recientes = StoreVisit.objects.select_related('user').order_by('-timestamp')[:20]

    # Filtros de visitas
    visitas_filter = request.GET.get('visitas_filter', 'all')
    visitas_user_filter = request.GET.get('visitas_user', 'all')
    visitas_type_filter = request.GET.get('visitas_type', 'all')
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    visitas_qs = StoreVisit.objects.all()
    if visitas_filter == 'today':
        visitas_qs = visitas_qs.filter(timestamp__gte=today_start)
    elif visitas_filter == 'week':
        visitas_qs = visitas_qs.filter(timestamp__gte=week_start)
    elif visitas_filter == 'month':
        visitas_qs = visitas_qs.filter(timestamp__gte=month_start)

    if visitas_user_filter == 'auth':
        visitas_qs = visitas_qs.exclude(user=None)
    elif visitas_user_filter == 'anon':
        visitas_qs = visitas_qs.filter(user=None)
    
    if visitas_type_filter == 'store':
        visitas_qs = visitas_qs.filter(visit_type='store')
    elif visitas_type_filter == 'product_detail':
        visitas_qs = visitas_qs.filter(visit_type='product_detail')

    visitas_count = visitas_qs.count()
    visitas_count_today = StoreVisit.objects.filter(timestamp__gte=today_start).count()
    visitas_count_week = StoreVisit.objects.filter(timestamp__gte=week_start).count()
    visitas_count_month = StoreVisit.objects.filter(timestamp__gte=month_start).count()
    visitas_count_auth = StoreVisit.objects.exclude(user=None).count()
    visitas_count_anon = StoreVisit.objects.filter(user=None).count()
    visitas_count_total = StoreVisit.objects.count()
    visitas_count_store = StoreVisit.objects.filter(visit_type='store').count()
    visitas_count_product = StoreVisit.objects.filter(visit_type='product_detail').count()
    
    # ESTADÍSTICAS DE PRODUCTOS MÁS VISITADOS
    from django.db.models import Count
    productos_mas_visitados = []
    if view_param == 'visitas':
        periodo_productos = request.GET.get('periodo_productos', 'all')
        visitas_productos_qs = StoreVisit.objects.filter(
            visit_type='product_detail',
            product_id__isnull=False
        )
        
        if periodo_productos == 'today':
            visitas_productos_qs = visitas_productos_qs.filter(timestamp__gte=today_start)
        elif periodo_productos == 'week':
            visitas_productos_qs = visitas_productos_qs.filter(timestamp__gte=week_start)
        elif periodo_productos == 'month':
            visitas_productos_qs = visitas_productos_qs.filter(timestamp__gte=month_start)
        
        productos_stats = visitas_productos_qs.values('product_id').annotate(
            total_visitas=Count('id')
        ).order_by('-total_visitas')[:10]
        
        for item in productos_stats:
            try:
                product = ProductStore.objects.get(id=item['product_id'])
                productos_mas_visitados.append({
                    'product': product,
                    'total_visitas': item['total_visitas']
                })
            except ProductStore.DoesNotExist:
                pass
    
    # Aplicar filtros para pedidos
    if view_param == 'pedidos':
        estado_filter = request.GET.get('estado_filter', '')
        metodo_filter = request.GET.get('metodo_filter', '')
        search_pedidos = request.GET.get('search', '')
        
        if estado_filter:
            pedidos_queryset = pedidos_queryset.filter(estado=estado_filter)
        if metodo_filter:
            pedidos_queryset = pedidos_queryset.filter(metodo_pago=metodo_filter)
        if search_pedidos:
            pedidos_queryset = pedidos_queryset.filter(
                Q(nombre__icontains=search_pedidos) |
                Q(user__email__icontains=search_pedidos) |
                Q(id__icontains=search_pedidos) |
                Q(transaction_id__icontains=search_pedidos)
            )
    
    Pedidos = pedidos_queryset
    
    # Estadísticas de pedidos
    pedidos_pendientes_count = Pedidos.filter(estado='pendiente').count() if view_param == 'pedidos' else 0
    pedidos_enviados_count = Pedidos.filter(estado__in=['enviado', 'llegando']).count() if view_param == 'pedidos' else 0
    pedidos_entregados_count = Pedidos.filter(estado='entregado').count() if view_param == 'pedidos' else 0
    show_create_product_form = request.GET.get('view') == 'productos' and request.GET.get('crear') == '1'
    editar_id = request.GET.get('editar')
    show_edit_product_form = request.GET.get('view') == 'productos' and bool(editar_id)
    producto_to_edit = None
    
    # Variables para análisis de ventas
    ventas_por_categoria = []
    total_ventas_general = 0
    estadisticas_ventas = {
        'pedidos_totales': 0,
        'productos_vendidos': 0,
        'promedio_por_pedido': 0,
        'categoria_mas_vendida': None,
        'categoria_mayor_ingresos': None,
    }
    
   
    if editar_id:
        # Obtener producto con todas sus relaciones (galería y variantes)
        producto_to_edit = ProductStore.objects.prefetch_related(
            'galeria',
            'variants'
        ).filter(id=editar_id).first()

        inventario_all = []
        inventario_by_category = []
        resumen_inventario = {
         'valor_invertido': 0,
         'valor_productos': 0,
         'margen_ganancia': 0,
         'cantidad_productos_stock': 0,
     }
      # Inicializar variables usadas en el contexto para evitar UnboundLocalError
   
    message = ''
    inventario_all = []
    inventario_by_category = []
    resumen_inventario = {
        'valor_invertido': 0,
        'valor_productos': 0,
        'margen_ganancia': 0,
        'cantidad_productos_stock': 0,
    }

    def _calcular_inventario(queryset):
        items = []
        by_cat = {}
        total_invertido = 0.0
        total_productos = 0.0
        total_cantidad = 0
        for p in queryset:
            stock = int(getattr(p, 'stock', 0) or 0)
            price_buy = float(getattr(p, 'price_buy', 0) or 0)
            price_sell = float(getattr(p, 'price', 0) or 0)
            subtotal_buy = price_buy * stock
            subtotal_sell = price_sell * stock
            cat = getattr(p, 'category', None) or getattr(p, 'categoria', None)
            if cat:
                cat_id = getattr(cat, 'id', 'sin-categoria')
                cat_name = getattr(cat, 'nombre', None) or getattr(cat, 'name', None) or str(cat)
            else:
                cat_id = 'sin-categoria'
                cat_name = 'Sin categoría'
            item = {
                'product_id': p.id,
                'product_name': getattr(p, 'name', None) or getattr(p, 'nombre', ''),
                'stock': stock,
                'price_buy': price_buy,
                'price': price_sell,
                'subtotal_buy': subtotal_buy,
                'subtotal_sell': subtotal_sell,
                'category_id': cat_id,
                'category_name': cat_name,
            }
            items.append(item)
            grp = by_cat.setdefault(cat_id, {
                'category_id': cat_id,
                'category_name': cat_name,
                'items': [],
                'valor_invertido': 0.0,
                'valor_productos': 0.0,
                'cantidad_stock': 0
            })
            grp['items'].append(item)
            grp['valor_invertido'] += subtotal_buy
            grp['valor_productos'] += subtotal_sell
            grp['cantidad_stock'] += stock
            total_invertido += subtotal_buy
            total_productos += subtotal_sell
            total_cantidad += stock
        resumen = {
            'valor_invertido': total_invertido,
            'valor_productos': total_productos,
            'margen_ganancia': total_productos - total_invertido,
            'cantidad_productos_stock': total_cantidad,
        }
        inventario_by_category_list = sorted(by_cat.values(), key=lambda x: x['category_name'])
        return resumen, items, inventario_by_category_list

    # si hay filtro GET (inventory_category) o si el view es 'inventario' calculamos para GET
    selected_category = request.GET.get('inventory_category')
    try:
        selected_category = int(selected_category) if selected_category not in (None, '', 'None') else None
    except Exception:
        selected_category = None
     
    if request.method != 'POST':
        qs = ProductStore.objects.all()
        if selected_category:
            qs = ProductStore.objects.filter(category_id=selected_category) if ProductStore.objects.filter(category_id=selected_category).exists() else ProductStore.objects.filter(categoria_id=selected_category)
        try:
            resumen_inventario, inventario_items, inventario_by_category = _calcular_inventario(qs)
            inventario_all = [resumen_inventario] + inventario_items
        except Exception:
            inventario_all = []
            inventario_by_category = []
            resumen_inventario = resumen_inventario  # mantiene valores iniciales


    # POST: crear o actualizar según product_id
    if request.method == 'POST' and (show_create_product_form or show_edit_product_form):
        # recoger campos
        name = request.POST.get('name')
        description = request.POST.get('description')
        price_buy = float(request.POST.get('price_buy', 0) or 0)
        price = float(request.POST.get('price', 0) or 0)
        stock = int(request.POST.get('stock', 0) or 0)
        descuento = float(request.POST.get('descuento', 0) or 0)
        iva = float(request.POST.get('iva', 0) or 0)
        imagen = request.FILES.get('images')
        galeria_files = request.FILES.getlist('galeria')


        
        productos_all = ProductStore.objects.all()
        total_productos_stock = sum(p.stock for p in productos_all)
        productos_comprados = sum(p.price_buy * p.stock for p in productos_all)
        valor_productos = sum(p.price * p.stock for p in productos_all)
        margen_ganancia = valor_productos - productos_comprados
        inventario_all = []
        inventario_by_category = []
        inventario_all.append({
            'nombre': 'Todos los productos',
            'valor_invertido': productos_comprados,
            'valor_productos': valor_productos,
            'margen_ganancia': margen_ganancia,
            'cantidad_productos_stock': total_productos_stock,
        })      
        

        # Proveedor / Categoria / Tipo (opcional)
        proveedor_id = request.POST.get('proveedor')
        proveedor_obj = None
        if proveedor_id:
            try:
                proveedor_obj = proveedor.objects.get(id=proveedor_id)
            except proveedor.DoesNotExist:
                proveedor_obj = None        
       

        categoria_id = request.POST.get('categoria')
        category_obj = None
        if categoria_id:
            try:
                category_obj = Category.objects.get(id=categoria_id)
            except Category.DoesNotExist:
                category_obj = None

        type_id = request.POST.get('type')
        type_obj = None
        if type_id:
            try:
                type_obj = Type.objects.get(id=type_id)
            except Type.DoesNotExist:
                type_obj = None
        
    
        # identificar si es actualización o creación
        product_id = request.POST.get('product_id') or None
        if product_id:
            # actualizar existente
            product = get_object_or_404(ProductStore, id=product_id)
            product.name = name
            product.description = description
            product.price_buy = price_buy
            product.price = price
            product.stock = stock
            product.proveedor = proveedor_obj
            product.category = category_obj
            product.iva = iva
            product.descuento = descuento
            product.type = type_obj
            if imagen:
                # eliminar anterior si deseas (opcional)
                try:
                    if getattr(product, 'imagen', None):
                        product.imagen.delete(save=False)
                except Exception:
                    pass
                product.imagen = imagen
            product.save()

            # Manejar eliminación de imágenes de galería marcadas
            galeria_delete_ids = request.POST.getlist('galeria_delete[]')
            if galeria_delete_ids:
                for gal_id in galeria_delete_ids:
                    try:
                        gal_obj = Galeria.objects.get(id=gal_id, product=product)
                        # Eliminar el archivo físico
                        if hasattr(gal_obj, 'galeria') and gal_obj.galeria:
                            gal_obj.galeria.delete(save=False)
                        elif hasattr(gal_obj, 'imagen') and gal_obj.imagen:
                            gal_obj.imagen.delete(save=False)
                        gal_obj.delete()
                    except Galeria.DoesNotExist:
                        pass
            
            # Agregar nuevas imágenes de galería si se enviaron
            if galeria_files:
                for img in galeria_files:
                    galeria_obj = Galeria.objects.create(galeria=img, product=product)
                    product.galeria.add(galeria_obj)

            # Manejar variantes: eliminar las marcadas y actualizar/crear las demás
            variante_ids = request.POST.getlist('variante_id[]')  # IDs de variantes existentes
            variante_nombres = request.POST.getlist('variante_nombre[]')
            variante_precios = request.POST.getlist('variante_precio[]')
            variante_imagenes = request.FILES.getlist('variante_imagen[]')
            variante_stocks = request.POST.getlist('variante_stock[]')
            variante_colores = request.POST.getlist('variante_color[]')
            variante_tallas = request.POST.getlist('variante_talla[]')
            variante_delete_ids = request.POST.getlist('variante_delete[]')
            
            # Eliminar variantes marcadas
            if variante_delete_ids:
                for var_id in variante_delete_ids:
                    try:
                        var_obj = ProductVariant.objects.get(id=var_id, product=product)
                        # Eliminar imagen si existe
                        if var_obj.imagen:
                            var_obj.imagen.delete(save=False)
                        var_obj.delete()
                    except ProductVariant.DoesNotExist:
                        pass
            
            # Actualizar o crear variantes
            if hasattr(product, 'variants'):
                max_len = max(len(variante_nombres), len(variante_precios), len(variante_stocks),
                              len(variante_colores), len(variante_tallas), len(variante_ids))
                
                for i in range(max_len):
                    nombre = variante_nombres[i] if i < len(variante_nombres) else ''
                    precio_v = variante_precios[i] if i < len(variante_precios) else None
                    stock_v = variante_stocks[i] if i < len(variante_stocks) else None
                    color = variante_colores[i] if i < len(variante_colores) else ''
                    talla = variante_tallas[i] if i < len(variante_tallas) else ''
                    img_v = variante_imagenes[i] if i < len(variante_imagenes) else None
                    var_id = variante_ids[i] if i < len(variante_ids) else None
                    
                    # Saltar si no hay nombre ni precio
                    if not nombre and not precio_v:
                        continue
                    
                    # Si tiene ID, actualizar variante existente
                    if var_id:
                        try:
                            variant = ProductVariant.objects.get(id=var_id, product=product)
                            variant.nombre = nombre
                            variant.precio = float(precio_v) if precio_v else 0
                            variant.stock = int(stock_v) if stock_v else 0
                            variant.color = color
                            variant.talla = talla
                            if img_v:  # Solo actualizar imagen si se sube una nueva
                                # Eliminar imagen anterior
                                if variant.imagen:
                                    variant.imagen.delete(save=False)
                                variant.imagen = img_v
                            variant.save()
                        except ProductVariant.DoesNotExist:
                            pass
                    else:
                        # Crear nueva variante
                        ProductVariant.objects.create(
                            product=product,
                            nombre=nombre,
                            precio=float(precio_v) if precio_v else 0,
                            stock=int(stock_v) if stock_v else 0,
                            color=color,
                            talla=talla,
                            imagen=img_v
                        )

            # redirigir a la lista o a la edición del producto actualizado
            return redirect(crear_producto_url)

        else:
            # crear nuevo producto
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

            # guardar galería
            for img in galeria_files:
                galeria_obj = Galeria.objects.create(galeria=img, product=product)
                product.galeria.add(galeria_obj)

            # crear variantes
            variante_nombres = request.POST.getlist('variante_nombre[]')
            variante_precios = request.POST.getlist('variante_precio[]')
            variante_imagenes = request.FILES.getlist('variante_imagen[]')
            variante_stocks = request.POST.getlist('variante_stock[]')
            variante_colores = request.POST.getlist('variante_color[]')
            variante_tallas = request.POST.getlist('variante_talla[]')

            max_len = max(len(variante_nombres), len(variante_precios), len(variante_stocks),
                          len(variante_colores), len(variante_tallas), len(variante_imagenes))
            for i in range(max_len):
                nombre = variante_nombres[i] if i < len(variante_nombres) else ''
                precio_v = variante_precios[i] if i < len(variante_precios) else None
                stock_v = variante_stocks[i] if i < len(variante_stocks) else None
                color = variante_colores[i] if i < len(variante_colores) else ''
                talla = variante_tallas[i] if i < len(variante_tallas) else ''
                img_v = variante_imagenes[i] if i < len(variante_imagenes) else None
                if nombre or precio_v:
                    ProductVariant.objects.create(
                        product=product,
                        nombre=nombre,
                        precio=(float(precio_v) if precio_v else 0),
                        stock=(int(stock_v) if stock_v else 0),
                        color=color,
                        talla=talla,
                        imagen=img_v
                    )

            # tras crear, redirigir a la lista sin abrir el form crear
            return redirect(f"{reverse('dashboard_home')}?view=productos")

    # MANEJO DE BONOS DE DESCUENTO
    if request.method == 'POST' and view_param == 'bonos':
        action = request.POST.get('action')
        
        if action == 'crear_bono':
            try:
                from django.utils import timezone
                
                codigo = request.POST.get('codigo', '').strip().upper()
                descripcion = request.POST.get('descripcion', '').strip()
                tipo_descuento = request.POST.get('tipo_descuento')
                valor_descuento = float(request.POST.get('valor_descuento', 0))
                valor_minimo_compra = float(request.POST.get('valor_minimo_compra', 0))
                fecha_inicio_str = request.POST.get('fecha_inicio')
                fecha_fin_str = request.POST.get('fecha_fin')
                usos_maximos = int(request.POST.get('usos_maximos', 1))
                activo = request.POST.get('activo') == 'on'
                
                # Validaciones
                if not codigo:
                    messages.error(request, 'El código del bono es requerido')
                    return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
                # Verificar que el código no exista
                if BonoDescuento.objects.filter(codigo=codigo).exists():
                    messages.error(request, f'Ya existe un bono con el código "{codigo}"')
                    return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
                # Parsear fechas
                try:
                    fecha_inicio = timezone.make_aware(datetime.strptime(fecha_inicio_str, '%Y-%m-%dT%H:%M'))
                    fecha_fin = timezone.make_aware(datetime.strptime(fecha_fin_str, '%Y-%m-%dT%H:%M'))
                except ValueError:
                    messages.error(request, 'Formato de fecha inválido')
                    return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
                # Validación flexible de fecha de inicio (permitir hasta 5 minutos en el pasado)
                now = timezone.now()
                time_diff = (fecha_inicio - now).total_seconds()
                
                if time_diff < -300:  # -300 segundos = -5 minutos
                    messages.error(request, 'La fecha de inicio no puede ser más de 5 minutos en el pasado')
                    return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
                if fecha_fin <= fecha_inicio:
                    messages.error(request, 'La fecha de fin debe ser posterior a la fecha de inicio')
                    return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
                # Crear bono
                bono = BonoDescuento.objects.create(
                    codigo=codigo,
                    descripcion=descripcion,
                    tipo_descuento=tipo_descuento,
                    valor_descuento=valor_descuento,
                    valor_minimo_compra=valor_minimo_compra,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    usos_maximos=usos_maximos,
                    activo=activo
                )
                
                messages.success(request, f'Bono "{codigo}" creado exitosamente')
                return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
            except Exception as e:
                messages.error(request, f'Error al crear bono: {str(e)}')
                return redirect(f"{reverse('dashboard_home')}?view=bonos")
        
        elif action == 'editar_bono':
            try:
                bono_id = request.POST.get('bono_id')
                bono = get_object_or_404(BonoDescuento, id=bono_id)
                
                from django.utils import timezone
                
                codigo = request.POST.get('codigo', '').strip().upper()
                descripcion = request.POST.get('descripcion', '').strip()
                tipo_descuento = request.POST.get('tipo_descuento')
                valor_descuento = float(request.POST.get('valor_descuento', 0))
                valor_minimo_compra = float(request.POST.get('valor_minimo_compra', 0))
                fecha_inicio_str = request.POST.get('fecha_inicio')
                fecha_fin_str = request.POST.get('fecha_fin')
                usos_maximos = int(request.POST.get('usos_maximos', 1))
                activo = request.POST.get('activo') == 'on'
                
                # Verificar código único (excluyendo el actual)
                if BonoDescuento.objects.filter(codigo=codigo).exclude(id=bono_id).exists():
                    messages.error(request, f'Ya existe otro bono con el código "{codigo}"')
                    return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
                # Parsear fechas
                fecha_inicio = timezone.make_aware(datetime.strptime(fecha_inicio_str, '%Y-%m-%dT%H:%M'))
                fecha_fin = timezone.make_aware(datetime.strptime(fecha_fin_str, '%Y-%m-%dT%H:%M'))
                
                if fecha_fin <= fecha_inicio:
                    messages.error(request, 'La fecha de fin debe ser posterior a la fecha de inicio')
                    return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
                # Actualizar bono
                bono.codigo = codigo
                bono.descripcion = descripcion
                bono.tipo_descuento = tipo_descuento
                bono.valor_descuento = valor_descuento
                bono.valor_minimo_compra = valor_minimo_compra
                bono.fecha_inicio = fecha_inicio
                bono.fecha_fin = fecha_fin
                bono.usos_maximos = usos_maximos
                bono.activo = activo
                bono.save()
                
                messages.success(request, f'Bono "{codigo}" actualizado exitosamente')
                return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
            except Exception as e:
                messages.error(request, f'Error al editar bono: {str(e)}')
                return redirect(f"{reverse('dashboard_home')}?view=bonos")
        
        elif action == 'eliminar_bono':
            try:
                bono_id = request.POST.get('bono_id')
                bono = get_object_or_404(BonoDescuento, id=bono_id)
                codigo = bono.codigo
                bono.delete()
                messages.success(request, f'Bono "{codigo}" eliminado exitosamente')
                return redirect(f"{reverse('dashboard_home')}?view=bonos")
                
            except Exception as e:
                messages.error(request, f'Error al eliminar bono: {str(e)}')
                return redirect(f"{reverse('dashboard_home')}?view=bonos")

    # Calcular estadísticas de ventas por categorías (siempre, para usar en home)
    view_param = request.GET.get('view', 'ventas')  # 'ventas' por defecto
    
    # Obtener todas las ventas (pedidos confirmados) - EXCLUIR CANCELADOS
    ventas_detalles = PedidoDetalle.objects.select_related(
        'producto', 'producto__category', 'pedido'
    ).exclude(
        pedido__estado='cancelado'
    ).all()
    
    # Calcular ventas por categoría
    ventas_por_categoria_dict = {}
    total_ventas_general = 0
    total_productos_vendidos = 0
    
    for detalle in ventas_detalles:
        categoria = detalle.producto.category
        categoria_nombre = categoria.nombre if categoria else 'Sin Categoría'
        precio_total = float(detalle.precio) * int(detalle.cantidad)
        
        if categoria_nombre not in ventas_por_categoria_dict:
            ventas_por_categoria_dict[categoria_nombre] = {
                'nombre': categoria_nombre,
                'total_ingresos': 0,
                'cantidad_productos': 0,
                'cantidad_pedidos': 0,
                'productos_vendidos': [],
                'pedidos_ids': set(),
            }
        
        ventas_por_categoria_dict[categoria_nombre]['total_ingresos'] += precio_total
        ventas_por_categoria_dict[categoria_nombre]['cantidad_productos'] += int(detalle.cantidad)
        ventas_por_categoria_dict[categoria_nombre]['pedidos_ids'].add(detalle.pedido.id)
        
        # Agregar producto vendido si no está ya en la lista
        producto_info = {
            'nombre': detalle.producto.name,
            'cantidad': int(detalle.cantidad),
            'precio_unitario': float(detalle.precio),
            'total': precio_total
        }
        ventas_por_categoria_dict[categoria_nombre]['productos_vendidos'].append(producto_info)
        
        total_ventas_general += precio_total
        total_productos_vendidos += int(detalle.cantidad)
    
    # Convertir a lista y agregar cantidad de pedidos
    ventas_por_categoria = []
    for categoria_data in ventas_por_categoria_dict.values():
        categoria_data['cantidad_pedidos'] = len(categoria_data['pedidos_ids'])
        del categoria_data['pedidos_ids']  # Remover el set que no es serializable
        ventas_por_categoria.append(categoria_data)
    
    # Ordenar por total de ingresos descendente
    ventas_por_categoria.sort(key=lambda x: x['total_ingresos'], reverse=True)
    
    # Calcular estadísticas generales - EXCLUIR PEDIDOS CANCELADOS
    pedidos_totales = Pedido.objects.exclude(estado='cancelado').count()
    promedio_por_pedido = total_ventas_general / pedidos_totales if pedidos_totales > 0 else 0
    
    categoria_mas_vendida = None
    categoria_mayor_ingresos = None
    
    if ventas_por_categoria:
        # Categoría con más productos vendidos
        categoria_mas_vendida = max(ventas_por_categoria, key=lambda x: x['cantidad_productos'])
        # Categoría con mayores ingresos
        categoria_mayor_ingresos = ventas_por_categoria[0]  # Ya está ordenada por ingresos
    
    # Calcular estadísticas diarias

    from django.utils import timezone
    
    hoy = timezone.now().date()
    inicio_dia = datetime.combine(hoy, datetime.min.time())
    if timezone.is_aware(timezone.now()):
        inicio_dia = timezone.make_aware(inicio_dia)
    
    pedidos_hoy = Pedido.objects.filter(fecha__gte=inicio_dia).exclude(estado='cancelado')
    pedidos_diarios = pedidos_hoy.count()
    
    ventas_diarias = pedidos_hoy.filter(
        Q(estado_pago='completado') | Q(estado='entregado')
    ).aggregate(total=Sum('total'))['total'] or 0
    
    productos_vendidos_hoy = PedidoDetalle.objects.filter(
        pedido__fecha__gte=inicio_dia,
        pedido__estado__in=['pendiente', 'confirmado', 'enviado', 'llegando', 'entregado']
    ).aggregate(total=Sum('cantidad'))['total'] or 0
    
    estadisticas_ventas = {
        'pedidos_totales': pedidos_totales,
        'productos_vendidos': total_productos_vendidos,
        'promedio_por_pedido': round(promedio_por_pedido, 2),
        'categoria_mas_vendida': categoria_mas_vendida,
        'categoria_mayor_ingresos': categoria_mayor_ingresos,
    }
    
    estadisticas_diarias = {
        'pedidos_hoy': pedidos_diarios,
        'ventas_hoy': float(ventas_diarias),
        'productos_vendidos_hoy': productos_vendidos_hoy,
    }
    


    # Datos para la sección de mensajes
    conversations = []
    conversations_stats = {
        'total_conversations': 0,
        'pending_conversations': 0,
        'today_messages': 0,
        'active_conversations': 0,
    }
    
    if view_param == 'mensajes':
        # Obtener conversaciones con paginación
        conversations_queryset = Conversation.objects.select_related('user').prefetch_related(
            'messages__user',
            'messages__admin_user'
        ).order_by('-created_at')
        
        # Paginación de conversaciones
        conversations_paginator = Paginator(conversations_queryset, 10)  # 10 conversaciones por página
        conversations_page_number = request.GET.get('page', 1)
        
        try:
            conversations = conversations_paginator.page(conversations_page_number)
        except PageNotAnInteger:
            conversations = conversations_paginator.page(1)
        except EmptyPage:
            conversations = conversations_paginator.page(conversations_paginator.num_pages)
        
        # Calcular estadísticas
        total_conversations = Conversation.objects.count()
        pending_conversations = Conversation.objects.filter(status='open').count()
        active_conversations = Conversation.objects.filter(status='in_progress').count()
        
        # Mensajes de hoy
        today = datetime.now().date()
        today_messages = ConversationMessage.objects.filter(
            created_at__date=today
        ).count()
        
        conversations_stats = {
            'total_conversations': total_conversations,
            'pending_conversations': pending_conversations,
            'today_messages': today_messages,
            'active_conversations': active_conversations,
        }

# ...existing code...
    return render(request, 'dashboard/dashboard_home.html', {
        'productos': productos,
        'productos_page': productos_page,
        'categorias': categorias,
        'tipos': tipos,
        'proveedores': proveedores,
        'usuarios': userSimples,
        'bonos': bonos,
        'show_create_product_form': show_create_product_form,
        'show_edit_product_form': show_edit_product_form,
        'producto_to_edit': producto_to_edit,       
        'inventario_all': inventario_all,
        'inventario_by_category': inventario_by_category,
        'resumen_inventario': resumen_inventario,
        'pedidos': Pedidos,
        'pedidos_pendientes_count': pedidos_pendientes_count,
        'pedidos_enviados_count': pedidos_enviados_count,
        'pedidos_entregados_count': pedidos_entregados_count,
        'ventas_por_categoria': ventas_por_categoria,
        'total_ventas_general': total_ventas_general,
        'estadisticas_ventas': estadisticas_ventas,
        'estadisticas_diarias': estadisticas_diarias,
        'categoria_filter': categoria_filter,
        'search_query': search_query,
        'conversations': conversations,
        'conversations_stats': conversations_stats,
        'visitas_recientes': visitas_qs.select_related('user').order_by('-timestamp')[:20],
        'visitas_count': visitas_count,
        'visitas_count_today': visitas_count_today,
        'visitas_count_week': visitas_count_week,
        'visitas_count_month': visitas_count_month,
        'visitas_count_auth': visitas_count_auth,
        'visitas_count_anon': visitas_count_anon,
        'visitas_count_store': visitas_count_store,
        'visitas_count_product': visitas_count_product,
        'productos_mas_visitados': productos_mas_visitados,
        'view': view_param,
        'current_user': current_user,
        'is_superuser': is_superuser,
        'is_staff': is_staff,
        'selected_category': selected_category,

    })
# ...existing code...


@superuser_required
def eliminar_producto(request, product_id):
    # Aceptar solo POST y devolver JSON (no redirect) para uso por AJAX
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

    # Permisos: aceptar sesión superuser personalizada o usuario Django staff/superuser
    is_super_session = bool(request.session.get('superuser_id'))
    is_django_staff = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    if not (is_super_session or is_django_staff):
        return JsonResponse({'success': False, 'error': 'Permiso denegado.'}, status=403)

    # Usar el modelo correcto (ProductStore) — antes estaba Product (no importado)
    product = get_object_or_404(ProductStore, id=product_id)
    try:
        # eliminar imagen principal si existe
        try:
            if getattr(product, 'imagen', None):
                product.imagen.delete(save=False)
        except Exception:
            pass

        # eliminar imágenes de galería asociadas (soporta varios nombres de campo)
        try:
            if hasattr(product, 'galeria'):
                for g in product.galeria.all():
                    try:
                        if getattr(g, 'imagen', None):
                            g.imagen.delete(save=False)
                        elif getattr(g, 'image', None):
                            g.image.delete(save=False)
                        elif getattr(g, 'galeria', None):
                            g.galeria.delete(save=False)
                    except Exception:
                        pass
        except Exception:
            pass

        # eliminar imágenes de variantes si existen
        try:
            if hasattr(product, 'variants'):
                for v in product.variants.all():
                    try:
                        if getattr(v, 'imagen', None):
                            v.imagen.delete(save=False)
                    except Exception:
                        pass
        except Exception:
            pass

        product.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
# ...existing code...

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


# ---------- Category Management Views ----------

@superuser_required
def crear_categoria(request):
    """Crear nueva categoría vía AJAX"""
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            slug = request.POST.get('slug', '').strip()
            
            if not nombre:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la categoría es requerido'
                })
            
            if not slug:
                return JsonResponse({
                    'success': False,
                    'message': 'El slug es requerido'
                })
            
            # Verificar que el slug sea único
            if Category.objects.filter(slug=slug).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una categoría con ese slug'
                })
            
            # Crear la categoría
            categoria = Category.objects.create(
                nombre=nombre,
                slug=slug
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Categoría creada exitosamente',
                'categoria': {
                    'id': categoria.id,
                    'nombre': categoria.nombre,
                    'slug': categoria.slug,
                    'products_count': categoria.products.count()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear la categoría: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@superuser_required
def editar_categoria(request, categoria_id):
    """Editar categoría existente vía AJAX"""
    if request.method == 'POST':
        try:
            categoria = get_object_or_404(Category, id=categoria_id)
            
            nombre = request.POST.get('nombre', '').strip()
            slug = request.POST.get('slug', '').strip()
            
            if not nombre:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la categoría es requerido'
                })
            
            if not slug:
                return JsonResponse({
                    'success': False,
                    'message': 'El slug es requerido'
                })
            
            # Verificar que el slug sea único (excluyendo la categoría actual)
            if Category.objects.filter(slug=slug).exclude(id=categoria_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe otra categoría con ese slug'
                })
            
            # Actualizar la categoría
            categoria.nombre = nombre
            categoria.slug = slug
            categoria.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Categoría actualizada exitosamente',
                'categoria': {
                    'id': categoria.id,
                    'nombre': categoria.nombre,
                    'slug': categoria.slug,
                    'products_count': categoria.products.count()
                }
            })
            
        except Category.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'La categoría no existe'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar la categoría: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@superuser_required
def eliminar_categoria(request, categoria_id):
    """Eliminar categoría vía AJAX"""
    if request.method == 'POST':
        try:
            categoria = get_object_or_404(Category, id=categoria_id)
            
            # Verificar si la categoría tiene productos asociados
            productos_count = categoria.products.count()
            if productos_count > 0:
                return JsonResponse({
                    'success': False,
                    'message': f'No se puede eliminar la categoría porque tiene {productos_count} producto(s) asociado(s). Primero debe reasignar o eliminar esos productos.'
                })
            
            categoria_nombre = categoria.nombre
            categoria.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Categoría "{categoria_nombre}" eliminada exitosamente'
            })
            
        except Category.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'La categoría no existe'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar la categoría: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@superuser_required
def pedido_detalle(request, pedido_id):
    """Obtener detalles completos de un pedido"""
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Obtener detalles de productos - manejo más robusto
        items = []
        try:
            # Intentar obtener desde PedidoDetalle usando pedidodetalle_set
            print(f"🔍 Buscando detalles para pedido {pedido_id}")
            detalles = pedido.pedidodetalle_set.all()
            print(f"📦 Encontrados {detalles.count()} detalles")
            
            for detalle in detalles:
                variante_info = ''
                if detalle.variante:
                    variante_info = f"{detalle.variante.color or ''} {detalle.variante.size or ''}".strip()
                
                item = {
                    'nombre': detalle.producto.name,
                    'cantidad': detalle.cantidad,
                    'precio': float(detalle.precio),
                    'variante': variante_info if variante_info else None
                }
                items.append(item)
                print(f"  ✅ Item: {item['nombre']} x{item['cantidad']}")
            
            # Si no hay detalles específicos, usar el campo detalles del pedido
            if not items and pedido.detalles:
                try:
                    import json
                    detalles_json = json.loads(pedido.detalles)
                    if isinstance(detalles_json, list):
                        items = detalles_json
                    else:
                        items = [{
                            'nombre': 'Productos varios',
                            'cantidad': 1,
                            'precio': float(pedido.total),
                            'descripcion': str(pedido.detalles)
                        }]
                except:
                    # Si no es JSON válido, mostrar como texto
                    items = [{
                        'nombre': 'Detalles del pedido',
                        'cantidad': 1,
                        'precio': float(pedido.total),
                        'descripcion': str(pedido.detalles)
                    }]
        except Exception as e:
            print(f"Error procesando items del pedido: {e}")
            # Fallback básico
            items = [{
                'nombre': 'Pedido',
                'cantidad': 1,
                'precio': float(pedido.total),
                'descripcion': 'Ver detalles en el campo "detalles" del pedido'
            }]
        
        # Datos del pedido
        pedido_data = {
            'id': pedido.id,
            'nombre': pedido.nombre,
            'email': pedido.email or pedido.user.email,
            'telefono': pedido.telefono,
            'direccion': pedido.direccion,
            'ciudad': pedido.ciudad,
            'departamento': pedido.departamento,
            'codigo_postal': getattr(pedido, 'codigo_postal', ''),
            'nota': pedido.nota or '',
            'nota_admin': getattr(pedido, 'nota_admin', ''),
            'detalles': pedido.detalles,
            'fecha': pedido.fecha.isoformat(),
            'total': float(pedido.total),
            'subtotal': float(getattr(pedido, 'subtotal', 0)),
            'envio': float(getattr(pedido, 'envio', 0)),
            'descuento': float(getattr(pedido, 'descuento', 0)),
            'estado': pedido.estado,
            'estado_display': pedido.get_estado_display(),
            'metodo_pago': pedido.metodo_pago,
            'metodo_pago_display': pedido.get_metodo_pago_display(),
            'estado_pago': pedido.estado_pago,
            'estado_pago_display': pedido.get_estado_pago_display(),
            'transaction_id': getattr(pedido, 'transaction_id', ''),
            'payment_reference': getattr(pedido, 'payment_reference', ''),
            'codigo_descuento': getattr(pedido, 'codigo_descuento', ''),
            'items': items
        }
        
        return JsonResponse({
            'success': True,
            'pedido': pedido_data
        })
        
    except Exception as e:
        print(f"Error en pedido_detalle: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener detalles: {str(e)}'
        })


@superuser_required  
@csrf_exempt
def update_pedido_estado(request):
    """Actualizar el estado de un pedido"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        import json
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        nuevo_estado = data.get('nuevo_estado')
        
        if not pedido_id or not nuevo_estado:
            return JsonResponse({
                'success': False, 
                'error': 'Faltan datos requeridos'
            })
        
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Validar estado
        estados_validos = ['pendiente', 'confirmado', 'enviado', 'llegando', 'entregado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'error': 'Estado no válido'
            })
        
        # Obtener estado anterior
        old_estado = getattr(pedido, 'estado', 'pendiente')
        
        # MANEJAR CANCELACIÓN DE PEDIDO - DEVOLVER STOCK
        if nuevo_estado == 'cancelado' and old_estado != 'cancelado':
            # Importar modelos necesarios
            from core.models import PedidoDetalle, ProductStore, ProductVariant
            
            # Obtener todos los detalles del pedido
            detalles = PedidoDetalle.objects.filter(pedido=pedido)
            
            # Devolver stock para cada producto
            for detalle in detalles:
                try:
                    if detalle.variante:
                        # Si es una variante, devolver stock a la variante
                        variante = detalle.variante
                        variante.stock += detalle.cantidad
                        variante.save()
                        print(f"✅ Stock devuelto - Variante {variante.id}: +{detalle.cantidad} unidades")
                    else:
                        # Si es producto principal, devolver stock al producto
                        producto = detalle.producto
                        producto.stock += detalle.cantidad
                        producto.save()
                        print(f"✅ Stock devuelto - Producto {producto.name}: +{detalle.cantidad} unidades")
                        
                except Exception as e:
                    print(f"❌ Error devolviendo stock para detalle {detalle.id}: {str(e)}")
                    # Continuar con los demás productos aunque uno falle
                    
            print(f"🔄 Pedido #{pedido.id} cancelado - Stock devuelto al inventario")
        
        # Actualizar estado
        # Si el campo estado no existe, crearlo dinámicamente
        if hasattr(pedido, 'estado'):
            pedido.estado = nuevo_estado
        else:
            # Para compatibilidad con modelos antiguos
            setattr(pedido, 'estado', nuevo_estado)
        
        # Actualizar fechas especiales
        from django.utils import timezone
        if nuevo_estado == 'enviado' and not getattr(pedido, 'fecha_enviado', None):
            if hasattr(pedido, 'fecha_enviado'):
                pedido.fecha_enviado = timezone.now()
            else:
                setattr(pedido, 'fecha_enviado', timezone.now())
                
        elif nuevo_estado == 'entregado' and not getattr(pedido, 'fecha_entregado', None):
            if hasattr(pedido, 'fecha_entregado'):
                pedido.fecha_entregado = timezone.now()
            else:
                setattr(pedido, 'fecha_entregado', timezone.now())
        
        # Actualizar estado de pago si es necesario
        if nuevo_estado == 'entregado' and getattr(pedido, 'metodo_pago', 'contraentrega') == 'contraentrega':
            if hasattr(pedido, 'estado_pago'):
                pedido.estado_pago = 'completado'
            else:
                setattr(pedido, 'estado_pago', 'completado')
        
        pedido.save()
        
        # Mensaje personalizado según el estado
        if nuevo_estado == 'cancelado':
            message = f'Pedido cancelado - Stock devuelto al inventario'
        else:
            message = f'Estado cambiado de "{old_estado}" a "{nuevo_estado}"'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'nuevo_estado': nuevo_estado
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar estado: {str(e)}'
        })


@superuser_required  
@csrf_exempt
def update_pedido_notes(request):
    """Actualizar las notas administrativas de un pedido"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        import json
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        notas_admin = data.get('notas_admin', '')
        
        if not pedido_id:
            return JsonResponse({
                'success': False, 
                'error': 'ID de pedido requerido'
            })
        
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Actualizar notas administrativas
        if hasattr(pedido, 'nota_admin'):
            pedido.nota_admin = notas_admin
        else:
            setattr(pedido, 'nota_admin', notas_admin)
        
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notas administrativas actualizadas correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar notas: {str(e)}'
        })


@superuser_required  
@csrf_exempt
def confirmar_pago_pedido(request):
    """Confirmar el pago de un pedido"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        import json
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        
        if not pedido_id:
            return JsonResponse({
                'success': False, 
                'error': 'ID de pedido requerido'
            })
        
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Obtener estado anterior
        old_estado_pago = getattr(pedido, 'estado_pago', 'pendiente')
        
        # Actualizar estado de pago a completado
        if hasattr(pedido, 'estado_pago'):
            pedido.estado_pago = 'completado'
        else:
            setattr(pedido, 'estado_pago', 'completado')
        
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Pago confirmado - Estado cambiado de "{old_estado_pago}" a "completado"',
            'nuevo_estado_pago': 'completado'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al confirmar pago: {str(e)}'
        })


@superuser_required
@csrf_exempt
def edit_user(request):
    """Editar datos de usuario (SimpleUser o register_superuser)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        model_type = data.get('model_type')
        
        print(f"Debug - Editing user: {user_id}, type: {model_type}, data: {data}")
        
        # Determinar qué modelo usar
        if model_type == 'SimpleUser':
            User = SimpleUser
        elif model_type == 'register_superuser':
            User = register_superuser
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de usuario inválido'})
        
        # Obtener el usuario
        user = get_object_or_404(User, id=user_id)
        
        # Actualizar campos según el tipo de modelo
        if model_type == 'SimpleUser':
            # SimpleUser tiene 'name' y 'telefono'
            user.name = data.get('name', user.name)
            user.email = data.get('email', user.email)
            if hasattr(user, 'telefono'):
                user.telefono = data.get('phone', getattr(user, 'telefono', ''))
            
            # Actualizar estado activo para usuarios simples
            if 'is_active' in data:
                user.is_active = data.get('is_active', True)
                
        elif model_type == 'register_superuser':
            # register_superuser tiene 'username' y 'phone'
            user.username = data.get('name', user.username)  # Usamos name del formulario para username
            user.email = data.get('email', user.email)
            if hasattr(user, 'phone'):
                user.phone = data.get('phone', getattr(user, 'phone', ''))
            
            # Actualizar permisos para administradores
            if 'is_active' in data:
                user.is_active = data.get('is_active', True)
            if 'is_staff' in data:
                user.is_staff = data.get('is_staff', False)
            if 'is_superuser' in data:
                user.is_superuser = data.get('is_superuser', False)
        
        # Campos comunes
        if hasattr(user, 'address'):
            user.address = data.get('address', getattr(user, 'address', ''))
        if hasattr(user, 'city'):
            user.city = data.get('city', getattr(user, 'city', ''))
        if hasattr(user, 'username') and model_type == 'SimpleUser':
            user.username = data.get('username', getattr(user, 'username', ''))
        
        # Actualizar contraseña si se proporcionó
        new_password = data.get('password')
        if new_password and new_password.strip():
            if len(new_password) < 6:
                return JsonResponse({'success': False, 'error': 'La contraseña debe tener al menos 6 caracteres'})
            
            # En producción, aquí deberías usar hash
            user.password = new_password
            print(f"Debug - Password updated for user {user_id}")
            
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {getattr(user, "name", getattr(user, "username", ""))} actualizado correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except Exception as e:
        print(f"Error editing user: {e}")
        return JsonResponse({'success': False, 'error': f'Error al editar usuario: {str(e)}'})


@superuser_required
@csrf_exempt
def delete_user(request):
    """Eliminar usuario (SimpleUser o register_superuser)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        model_type = data.get('model_type')
        
        # No permitir eliminar administradores por seguridad
        if model_type == 'register_superuser':
            return JsonResponse({
                'success': False, 
                'error': 'No se pueden eliminar usuarios administradores por seguridad'
            })
        
        # Determinar qué modelo usar
        if model_type == 'SimpleUser':
            User = SimpleUser
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de usuario inválido'})
        
        # Obtener y eliminar el usuario
        user = get_object_or_404(User, id=user_id)
        user_name = user.name
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {user_name} eliminado correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al eliminar usuario: {str(e)}'})


@superuser_required
def get_user_details(request, user_id, model_type):
    """Obtener detalles de un usuario específico"""
    try:
        # Determinar qué modelo usar
        if model_type == 'SimpleUser':
            User = SimpleUser
        elif model_type == 'register_superuser':
            User = register_superuser
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de usuario inválido'})
        
        user = get_object_or_404(User, id=user_id)
        
        # Obtener campos según el modelo
        phone_field = 'telefono' if model_type == 'SimpleUser' else 'phone'
        name_field = 'name' if model_type == 'SimpleUser' else 'username'
        
        user_data = {
            'id': user.id,
            'name': getattr(user, name_field, ''),
            'email': user.email,
            'phone': getattr(user, phone_field, ''),
            'address': getattr(user, 'address', ''),
            'city': getattr(user, 'city', ''),
            'username': getattr(user, 'username', ''),
            'date_joined': str(getattr(user, 'date_joined', getattr(user, 'created_at', ''))),
            'is_admin': model_type == 'register_superuser',
            'user_type': 'admin' if model_type == 'register_superuser' else 'simple',
            'model_type': model_type,
            # Permisos - incluir para ambos tipos de usuario
            'is_active': getattr(user, 'is_active', True),
            'is_staff': getattr(user, 'is_staff', False),
            'is_superuser': getattr(user, 'is_superuser', False),
            'can_edit_permissions': model_type == 'register_superuser',  # Solo admins pueden editar permisos
        }
        
        return JsonResponse({'success': True, 'user': user_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al obtener usuario: {str(e)}'})


import json


# ===== VISTAS PARA GESTIÓN DE CONVERSACIONES =====

@superuser_required
def conversation_detail(request, conversation_id):
    """Obtener detalles completos de una conversación"""
    print(f"🔍 conversation_detail called for ID: {conversation_id}")
    try:
        conversation = get_object_or_404(
            Conversation.objects.select_related('user'),
            id=conversation_id
        )
        print(f"✅ Conversación encontrada: {conversation.id} - {conversation.subject}")
        
        # Obtener mensajes de la conversación
        messages = ConversationMessage.objects.filter(
            conversation=conversation
        ).order_by('created_at')
        print(f"📨 Mensajes encontrados: {messages.count()}")
        
        # Serializar datos
        conversation_data = {
            'id': conversation.id,
            'subject': conversation.subject,
            'status': conversation.status,
            'created_at': conversation.created_at.isoformat(),
            'user': {
                'id': conversation.user.id,
                'username': conversation.user.username,
                'email': conversation.user.email,
            },
            'messages': []
        }
        
        # Agregar mensajes
        for message in messages:
            print(f"🔍 Procesando mensaje ID: {message.id}, is_admin: {message.is_admin}")
            # Determinar el nombre del remitente según si es admin o usuario
            if message.is_admin:
                sender_name = message.admin_user.username if message.admin_user else 'Admin'
            else:
                sender_name = message.user.username if message.user else 'Usuario'
                
            print(f"👤 Sender name determinado: {sender_name}")
                
            message_data = {
                'id': message.id,
                'message': message.message,
                'is_admin': message.is_admin,
                'sender_name': sender_name,
                'created_at': message.created_at.isoformat(),
            }
            conversation_data['messages'].append(message_data)
        
        print(f"✅ Datos de respuesta preparados: {len(conversation_data['messages'])} mensajes")
        return JsonResponse({
            'success': True,
            'conversation': conversation_data
        })
        
    except Exception as e:
        print(f"❌ Error in conversation_detail: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Error al cargar conversación: {str(e)}'
        })


@superuser_required
def conversation_reply(request):
    """Responder a una conversación como administrador"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        message_text = data.get('message', '').strip()
        mark_resolved = data.get('mark_resolved', False)
        
        if not conversation_id or not message_text:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        # Obtener la conversación
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Obtener el usuario administrador de la sesión
        superuser_id = request.session.get('superuser_id')
        if not superuser_id:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'})
        
        admin_user = get_object_or_404(register_superuser, id=superuser_id)
        
        # Crear el mensaje de respuesta
        ConversationMessage.objects.create(
            conversation=conversation,
            user=None,  # Mensaje de admin, no viene de SimpleUser
            admin_user=None,  # Por ahora None, podría mejorarse para usar el admin real
            message=message_text,
            is_admin=True
        )
        
        # Actualizar estado si se marca como resuelto
        if mark_resolved:
            conversation.status = 'resolved'
            conversation.save()
        else:
            # Si no se marca como resuelto pero estaba abierto, pasar a "en progreso"
            if conversation.status == 'open':
                conversation.status = 'in_progress'
                conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Respuesta enviada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except Exception as e:
        print(f"Error in conversation_reply: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error al enviar respuesta: {str(e)}'
        })


@superuser_required 
def conversation_update_status(request):
    """Actualizar estado de una conversación"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        new_status = data.get('new_status')
        
        valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
        
        if not conversation_id or new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Datos inválidos'})
        
        # Obtener y actualizar la conversación
        conversation = get_object_or_404(Conversation, id=conversation_id)
        conversation.status = new_status
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Estado actualizado a "{new_status}" correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except Exception as e:
        print(f"Error in conversation_update_status: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar estado: {str(e)}'
        })


@superuser_required
def pedidos_count(request):
    """API para obtener el conteo de pedidos con los filtros aplicados"""
    try:
        # Obtener todos los pedidos
        pedidos = Pedido.objects.all().order_by('-fecha')
        
        # Aplicar filtros si existen
        estado_filter = request.GET.get('estado_filter')
        metodo_filter = request.GET.get('metodo_filter')
        search = request.GET.get('search', '').strip()
        
        if estado_filter:
            pedidos = pedidos.filter(estado=estado_filter)
        
        if metodo_filter:
            pedidos = pedidos.filter(metodo_pago=metodo_filter)
        
        if search:
            pedidos = pedidos.filter(
                Q(id__icontains=search) |
                Q(nombre__icontains=search) |
                Q(email__icontains=search) |
                Q(telefono__icontains=search) |
                Q(transaction_id__icontains=search)
            )
        
        count = pedidos.count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        print(f"Error in pedidos_count: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@superuser_required
def pedidos_list(request):
    """API para obtener la lista HTML de pedidos actualizada"""
    try:
        from django.template.loader import render_to_string
        
        # Obtener todos los pedidos
        pedidos = Pedido.objects.all().select_related('user').order_by('-fecha')
        
        # Aplicar filtros si existen
        estado_filter = request.GET.get('estado_filter')
        metodo_filter = request.GET.get('metodo_filter')
        search = request.GET.get('search', '').strip()
        
        if estado_filter:
            pedidos = pedidos.filter(estado=estado_filter)
        
        if metodo_filter:
            pedidos = pedidos.filter(metodo_pago=metodo_filter)
        
        if search:
            pedidos = pedidos.filter(
                Q(id__icontains=search) |
                Q(nombre__icontains=search) |
                Q(email__icontains=search) |
                Q(telefono__icontains=search) |
                Q(transaction_id__icontains=search)
            )
        
        # Generar HTML para las filas de la tabla
        html_rows = []
        for pedido in pedidos:
            # Determinar clase de badge para estado
            estado_class = {
                'pendiente': 'warning',
                'confirmado': 'info',
                'enviado': 'primary',
                'llegando': 'info',
                'entregado': 'success',
                'cancelado': 'danger'
            }.get(pedido.estado, 'secondary')
            
            # Determinar clase de badge para método de pago
            metodo_class = {
                'contraentrega': 'warning',
                'recoger_tienda': 'info',
                'tarjeta': 'primary',
                'wompi': 'primary',
                'efectivo': 'warning'
            }.get(pedido.metodo_pago, 'secondary')
            
            # Determinar clase de badge para estado de pago
            pago_class = {
                'completado': 'success',
                'pendiente': 'warning',
                'procesando': 'info',
                'fallido': 'danger'
            }.get(pedido.estado_pago, 'secondary')
            
            # Iconos para estados
            estado_icons = {
                'pendiente': 'fa-clock',
                'confirmado': 'fa-check',
                'enviado': 'fa-shipping-fast',
                'llegando': 'fa-truck',
                'entregado': 'fa-check-circle'
            }
            
            pago_icons = {
                'completado': 'fa-check-circle',
                'pendiente': 'fa-clock',
                'procesando': 'fa-spinner',
                'fallido': 'fa-times-circle'
            }
            
            metodo_icons = {
                'contraentrega': 'fa-money-bill',
                'recoger_tienda': 'fa-store',
                'tarjeta': 'fa-credit-card',
                'wompi': 'fa-credit-card',
                'efectivo': 'fa-money-bill'
            }
            
            html_row = f'''
            <tr>
                <td>
                    <strong class="text-primary">#{pedido.id}</strong>
                    {'<br><small class="text-muted">' + pedido.transaction_id[:8] + '...</small>' if pedido.transaction_id else ''}
                </td>
                <td>
                    <div>
                        <strong>{pedido.nombre}</strong><br>
                        <small class="text-muted">{pedido.user.email if pedido.user else pedido.email}</small>
                    </div>
                </td>
                <td>
                    {'<small><i class="fas fa-phone"></i> ' + pedido.telefono + '</small><br>' if pedido.telefono else ''}
                    <small class="text-muted">
                        <i class="fas fa-map-marker-alt"></i> {pedido.ciudad}, {pedido.departamento}
                    </small>
                </td>
                <td>
                    <strong class="text-success">${pedido.total:,.0f}</strong>
                    {'<br><small class="text-muted">Sub: $' + f'{pedido.subtotal:,.0f}' + (f' + Envío: ${pedido.envio:,.0f}' if pedido.envio and pedido.envio > 0 else '') + '</small>' if hasattr(pedido, 'subtotal') and pedido.subtotal else ''}
                </td>
                <td>
                    <span class="badge bg-{metodo_class}">
                        <i class="fas {metodo_icons.get(pedido.metodo_pago, 'fa-question')}"></i> 
                        {pedido.get_metodo_pago_display()}
                    </span>
                </td>
                <td>
                    <span class="badge bg-{estado_class}">
                        <i class="fas {estado_icons.get(pedido.estado, 'fa-question')}"></i>
                        {pedido.get_estado_display()}
                    </span>
                </td>
                <td>
                    <span class="badge bg-{pago_class}">
                        <i class="fas {pago_icons.get(pedido.estado_pago, 'fa-question')}"></i>
                        {pedido.get_estado_pago_display()}
                    </span>
                </td>
                <td>
                    <small>{pedido.fecha.strftime('%d/%m/%Y %H:%M')}</small>
                    {'<br><small class="text-success">Entregado: ' + pedido.fecha_entregado.strftime('%d/%m') + '</small>' if hasattr(pedido, 'fecha_entregado') and pedido.fecha_entregado else ''}
                </td>
                <td class="text-center">
                    <div class="d-flex flex-column gap-1">
                        <button type="button" class="btn btn-outline-primary btn-sm" 
                                data-bs-toggle="modal" 
                                data-bs-target="#pedidoModal"
                                onclick="loadPedidoDetails({pedido.id})"
                                title="Ver detalles del pedido">
                            <i class="fas fa-eye me-1"></i> Ver
                        </button>
                        {'<button type="button" class="btn btn-outline-success btn-sm" onclick="confirmarPago(' + str(pedido.id) + ')" title="Confirmar pago del pedido"><i class="fas fa-dollar-sign me-1"></i> Confirmar Pago</button>' if pedido.estado_pago != 'completado' else ''}
                        <div class="dropdown">
                            <button class="btn btn-outline-secondary btn-sm dropdown-toggle w-100" 
                                    type="button" 
                                    id="dropdownEstado{pedido.id}"
                                    data-bs-toggle="dropdown"
                                    aria-expanded="false"
                                    title="Cambiar estado del pedido">
                                <i class="fas fa-edit me-1"></i> Estado
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="dropdownEstado{pedido.id}">
                                <li><a class="dropdown-item" href="javascript:void(0)" onclick="event.preventDefault(); updateEstado({pedido.id}, 'pendiente')">
                                    <i class="fas fa-clock me-2 text-warning"></i>Pendiente
                                </a></li>
                                <li><a class="dropdown-item" href="javascript:void(0)" onclick="event.preventDefault(); updateEstado({pedido.id}, 'confirmado')">
                                    <i class="fas fa-check me-2 text-info"></i>Confirmar
                                </a></li>
                                <li><a class="dropdown-item" href="javascript:void(0)" onclick="event.preventDefault(); updateEstado({pedido.id}, 'enviado')">
                                    <i class="fas fa-shipping-fast me-2 text-primary"></i>Enviar
                                </a></li>
                                <li><a class="dropdown-item" href="javascript:void(0)" onclick="event.preventDefault(); updateEstado({pedido.id}, 'llegando')">
                                    <i class="fas fa-truck me-2 text-info"></i>En camino
                                </a></li>
                                <li><a class="dropdown-item" href="javascript:void(0)" onclick="event.preventDefault(); updateEstado({pedido.id}, 'entregado')">
                                    <i class="fas fa-check-circle me-2 text-success"></i>Entregar
                                </a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item text-danger" href="javascript:void(0)" onclick="event.preventDefault(); updateEstado({pedido.id}, 'cancelado')">
                                    <i class="fas fa-times-circle me-2"></i>Cancelar
                                </a></li>
                            </ul>
                        </div>
                    </div>
                </td>
            </tr>
            '''
            html_rows.append(html_row)
        
        html = ''.join(html_rows)
        
        return JsonResponse({
            'success': True,
            'html': html,
            'count': pedidos.count()
        })
        
    except Exception as e:
        print(f"Error in pedidos_list: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@superuser_required
def dashboard_stats(request):
    """API para obtener estadísticas actualizadas del dashboard home"""
    try:
        from django.db.models import Sum, Count
        from decimal import Decimal

        from django.utils import timezone
        
        # Obtener fecha de hoy
        hoy = timezone.now().date()
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        if timezone.is_aware(timezone.now()):
            inicio_dia = timezone.make_aware(inicio_dia)
        
        # ===== ESTADÍSTICAS GENERALES =====
        total_pedidos = Pedido.objects.count()
        pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
        pedidos_completados = Pedido.objects.filter(estado='entregado').count()
        
        # Estadísticas financieras generales
        ingresos_totales = Pedido.objects.filter(
            estado_pago='completado'
        ).aggregate(total=Sum('total'))['total'] or Decimal(0)
        
        ingresos_pendientes = Pedido.objects.filter(
            Q(estado_pago='pendiente') | Q(estado_pago='procesando')
        ).aggregate(total=Sum('total'))['total'] or Decimal(0)
        
        # ===== ESTADÍSTICAS DIARIAS =====
        pedidos_hoy = Pedido.objects.filter(fecha__gte=inicio_dia)
        
        # Pedidos de hoy
        pedidos_diarios = pedidos_hoy.count()
        
        # Ventas de hoy (solo pedidos completados o con pago completado)
        ventas_diarias = pedidos_hoy.filter(
            Q(estado_pago='completado') | Q(estado='entregado')
        ).aggregate(total=Sum('total'))['total'] or Decimal(0)
        
        # Productos vendidos hoy
        from core.models import PedidoDetalle
        productos_vendidos_hoy = PedidoDetalle.objects.filter(
            pedido__fecha__gte=inicio_dia
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        # Ingresos pendientes de hoy
        ingresos_pendientes_hoy = pedidos_hoy.filter(
            Q(estado_pago='pendiente') | Q(estado_pago='procesando')
        ).aggregate(total=Sum('total'))['total'] or Decimal(0)
        
        # Nuevos clientes hoy
        nuevos_clientes_hoy = SimpleUser.objects.filter(
            created_at__gte=inicio_dia
        ).count() if hasattr(SimpleUser, 'created_at') else 0
        
        # ===== PRODUCTOS =====
        total_productos = ProductStore.objects.count()
        productos_sin_stock = ProductStore.objects.filter(stock=0).count()
        productos_bajo_stock = ProductStore.objects.filter(stock__lte=5, stock__gt=0).count()
        
        # ===== USUARIOS =====
        total_usuarios = SimpleUser.objects.count()
        
        # Pedidos recientes (últimos 5)
        pedidos_recientes = Pedido.objects.select_related('user').order_by('-fecha')[:5]
        pedidos_data = []
        for pedido in pedidos_recientes:
            pedidos_data.append({
                'id': pedido.id,
                'nombre': pedido.nombre,
                'total': float(pedido.total),
                'estado': pedido.estado,
                'estado_display': pedido.get_estado_display(),
                'fecha': pedido.fecha.strftime('%d/%m/%Y %H:%M')
            })
        
        # Productos más vendidos (top 5)
        from core.models import PedidoDetalle
        productos_vendidos = PedidoDetalle.objects.values(
            'producto__id', 'producto__name'
        ).annotate(
            total_vendido=Sum('cantidad')
        ).order_by('-total_vendido')[:5]
        
        productos_top = []
        for item in productos_vendidos:
            productos_top.append({
                'id': item['producto__id'],
                'nombre': item['producto__name'],
                'cantidad': item['total_vendido']
            })
        
        return JsonResponse({
            'success': True,
            'stats': {
                'pedidos': {
                    'total': total_pedidos,
                    'pendientes': pedidos_pendientes,
                    'completados': pedidos_completados
                },
                'finanzas': {
                    'ingresos_totales': float(ingresos_totales),
                    'ingresos_pendientes': float(ingresos_pendientes)
                },
                'diarias': {
                    'pedidos_hoy': pedidos_diarios,
                    'ventas_hoy': float(ventas_diarias),
                    'productos_vendidos_hoy': productos_vendidos_hoy,
                    'ingresos_pendientes_hoy': float(ingresos_pendientes_hoy),
                    'nuevos_clientes_hoy': nuevos_clientes_hoy
                },
                'productos': {
                    'total': total_productos,
                    'sin_stock': productos_sin_stock,
                    'bajo_stock': productos_bajo_stock
                },
                'usuarios': {
                    'total': total_usuarios
                },
                'pedidos_recientes': pedidos_data,
                'productos_top': productos_top,
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"Error in dashboard_stats: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================
# GESTIÓN DE PROYECTOS
# ============================================

@superuser_required
def projects_list(request):
    """Lista todos los proyectos en el dashboard"""
    from core.models import Project
    
    projects = Project.objects.all().order_by('-order', '-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(client__icontains=search_query)
        )
    
    context = {
        'projects': projects,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Project.STATUS_CHOICES,
    }
    
    return render(request, 'dashboard/projects_list.html', context)


@superuser_required
def project_create(request):
    """Crear un nuevo proyecto"""
    from core.models import Project
    from django.utils.text import slugify
    
    if request.method == 'POST':
        try:
            # Crear proyecto
            project = Project()
            project.name = request.POST.get('name', '')
            project.slug = slugify(project.name)
            project.description = request.POST.get('description', '')
            project.status = request.POST.get('status', 'planning')
            
            # Tecnologías
            project.frontend_tech = request.POST.get('frontend_tech', '')
            project.backend_tech = request.POST.get('backend_tech', '')
            project.database = request.POST.get('database', '')
            project.authentication = request.POST.get('authentication', '')
            project.main_components = request.POST.get('main_components', '')
            
            # Información adicional
            project.client = request.POST.get('client', '')
            project.project_url = request.POST.get('project_url', '')
            project.github_url = request.POST.get('github_url', '')
            
            # Fechas
            project.start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if end_date:
                project.end_date = end_date
            
            # Control
            project.is_featured = request.POST.get('is_featured') == 'on'
            project.is_active = request.POST.get('is_active') == 'on'
            project.order = int(request.POST.get('order', 0))
            
            # Imágenes
            if 'main_image' in request.FILES:
                project.main_image = request.FILES['main_image']
            if 'screenshot_1' in request.FILES:
                project.screenshot_1 = request.FILES['screenshot_1']
            if 'screenshot_2' in request.FILES:
                project.screenshot_2 = request.FILES['screenshot_2']
            if 'screenshot_3' in request.FILES:
                project.screenshot_3 = request.FILES['screenshot_3']
            
            project.save()
            
            messages.success(request, f'Proyecto "{project.name}" creado exitosamente')
            return redirect('dashboard_projects')
            
        except Exception as e:
            messages.error(request, f'Error al crear proyecto: {str(e)}')
            print(f"Error creating project: {e}")
    
    context = {
        'status_choices': Project.STATUS_CHOICES,
    }
    
    return render(request, 'dashboard/project_form.html', context)


@superuser_required
def project_edit(request, project_id):
    """Editar un proyecto existente"""
    from core.models import Project
    from django.utils.text import slugify
    
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            project.name = request.POST.get('name', project.name)
            project.slug = slugify(project.name)
            project.description = request.POST.get('description', project.description)
            project.status = request.POST.get('status', project.status)
            
            # Tecnologías
            project.frontend_tech = request.POST.get('frontend_tech', project.frontend_tech)
            project.backend_tech = request.POST.get('backend_tech', project.backend_tech)
            project.database = request.POST.get('database', project.database)
            project.authentication = request.POST.get('authentication', project.authentication)
            project.main_components = request.POST.get('main_components', project.main_components)
            
            # Información adicional
            project.client = request.POST.get('client', project.client)
            project.project_url = request.POST.get('project_url', project.project_url)
            project.github_url = request.POST.get('github_url', project.github_url)
            
            # Fechas
            project.start_date = request.POST.get('start_date', project.start_date)
            end_date = request.POST.get('end_date')
            if end_date:
                project.end_date = end_date
            
            # Control
            project.is_featured = request.POST.get('is_featured') == 'on'
            project.is_active = request.POST.get('is_active') == 'on'
            project.order = int(request.POST.get('order', project.order))
            
            # Actualizar imágenes solo si se suben nuevas
            if 'main_image' in request.FILES:
                project.main_image = request.FILES['main_image']
            if 'screenshot_1' in request.FILES:
                project.screenshot_1 = request.FILES['screenshot_1']
            if 'screenshot_2' in request.FILES:
                project.screenshot_2 = request.FILES['screenshot_2']
            if 'screenshot_3' in request.FILES:
                project.screenshot_3 = request.FILES['screenshot_3']
            
            project.save()
            
            messages.success(request, f'Proyecto "{project.name}" actualizado exitosamente')
            return redirect('dashboard_projects')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar proyecto: {str(e)}')
            print(f"Error updating project: {e}")
    
    context = {
        'project': project,
        'status_choices': Project.STATUS_CHOICES,
        'edit_mode': True,
    }
    
    return render(request, 'dashboard/project_form.html', context)


@superuser_required
def project_delete(request, project_id):
    """Eliminar un proyecto"""
    from core.models import Project
    
    if request.method == 'POST':
        try:
            project = get_object_or_404(Project, id=project_id)
            project_name = project.name
            project.delete()
            
            messages.success(request, f'Proyecto "{project_name}" eliminado exitosamente')
            return JsonResponse({'success': True, 'message': 'Proyecto eliminado'})
            
        except Exception as e:
            messages.error(request, f'Error al eliminar proyecto: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ============================================
# API ENDPOINTS PARA VISITAS EN TIEMPO REAL
# ============================================

@superuser_required
def visitas_live_data(request):
    """
    Endpoint API para obtener datos de visitas en tiempo real
    Retorna visitas recientes y estadísticas actualizadas
    """
    from core.models import StoreVisit, ProductStore
    from django.utils import timezone
    
    # Obtener filtros
    visitas_filter = request.GET.get('visitas_filter', 'all')
    visitas_user_filter = request.GET.get('visitas_user', 'all')
    visitas_type_filter = request.GET.get('visitas_type', 'all')
    limit = int(request.GET.get('limit', 20))
    
    # Calcular rangos de tiempo
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    # Base queryset
    visitas_qs = StoreVisit.objects.select_related('user').all()
    
    # Aplicar filtros de tiempo
    if visitas_filter == 'today':
        visitas_qs = visitas_qs.filter(timestamp__gte=today_start)
    elif visitas_filter == 'week':
        visitas_qs = visitas_qs.filter(timestamp__gte=week_start)
    elif visitas_filter == 'month':
        visitas_qs = visitas_qs.filter(timestamp__gte=month_start)
    
    # Aplicar filtros de usuario
    if visitas_user_filter == 'auth':
        visitas_qs = visitas_qs.exclude(user=None)
    elif visitas_user_filter == 'anon':
        visitas_qs = visitas_qs.filter(user=None)
    
    # Aplicar filtros de tipo
    if visitas_type_filter == 'store':
        visitas_qs = visitas_qs.filter(visit_type='store')
    elif visitas_type_filter == 'product_detail':
        visitas_qs = visitas_qs.filter(visit_type='product_detail')
    
    # Obtener visitas recientes
    visitas_recientes = visitas_qs.order_by('-timestamp')[:limit]
    
    # Serializar visitas
    visitas_data = []
    for visita in visitas_recientes:
        product_name = None
        if visita.product_id:
            try:
                product = ProductStore.objects.get(id=visita.product_id)
                product_name = product.name
            except ProductStore.DoesNotExist:
                pass
        
        visitas_data.append({
            'id': visita.id,
            'timestamp': visita.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            'visit_type': visita.visit_type,
            'product_id': visita.product_id,
            'product_name': product_name,
            'user_name': visita.user.name if visita.user else None,
            'user_email': visita.user.email if visita.user else None,
            'is_authenticated': visita.user is not None,
            'city': visita.city,
            'country': visita.country,
            'ip_address': visita.ip_address,
        })
    
    # Calcular estadísticas
    stats = {
        'total_filtrado': visitas_qs.count(),
        'total_hoy': StoreVisit.objects.filter(timestamp__gte=today_start).count(),
        'total_semana': StoreVisit.objects.filter(timestamp__gte=week_start).count(),
        'total_mes': StoreVisit.objects.filter(timestamp__gte=month_start).count(),
        'total_autenticados': StoreVisit.objects.exclude(user=None).count(),
        'total_anonimos': StoreVisit.objects.filter(user=None).count(),
        'total_tienda': StoreVisit.objects.filter(visit_type='store').count(),
        'total_productos': StoreVisit.objects.filter(visit_type='product_detail').count(),
        'total_general': StoreVisit.objects.count(),
    }
    
    return JsonResponse({
        'success': True,
        'visitas': visitas_data,
        'stats': stats,
        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
    })


@superuser_required
def productos_mas_visitados(request):
    """
    Endpoint API para obtener estadísticas de productos más visitados
    """
    from core.models import StoreVisit, ProductStore
    from django.db.models import Count
    from django.utils import timezone
    
    # Obtener parámetros
    periodo = request.GET.get('periodo', 'all')  # all, today, week, month
    limit = int(request.GET.get('limit', 10))
    
    # Calcular rangos de tiempo
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    # Base queryset - solo visitas a productos
    visitas_qs = StoreVisit.objects.filter(
        visit_type='product_detail',
        product_id__isnull=False
    )
    
    # Aplicar filtro de periodo
    if periodo == 'today':
        visitas_qs = visitas_qs.filter(timestamp__gte=today_start)
    elif periodo == 'week':
        visitas_qs = visitas_qs.filter(timestamp__gte=week_start)
    elif periodo == 'month':
        visitas_qs = visitas_qs.filter(timestamp__gte=month_start)
    
    # Agrupar por producto y contar visitas
    productos_visitados = visitas_qs.values('product_id').annotate(
        total_visitas=Count('id')
    ).order_by('-total_visitas')[:limit]
    
    # Enriquecer con datos del producto
    productos_data = []
    for item in productos_visitados:
        try:
            product = ProductStore.objects.select_related('category').get(id=item['product_id'])
            productos_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_price': float(product.price),
                'product_stock': product.stock,
                'product_category': product.category.nombre if product.category else 'Sin categoría',
                'product_image': product.imagen.url if product.imagen else None,
                'total_visitas': item['total_visitas'],
            })
        except ProductStore.DoesNotExist:
            # Producto eliminado pero con visitas
            productos_data.append({
                'product_id': item['product_id'],
                'product_name': f'Producto #{item["product_id"]} (eliminado)',
                'product_price': 0,
                'product_stock': 0,
                'product_category': 'N/A',
                'product_image': None,
                'total_visitas': item['total_visitas'],
            })
    
    return JsonResponse({
        'success': True,
        'productos': productos_data,
        'periodo': periodo,
        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
    })


@superuser_required
def ventas_por_periodo(request):
    """
    API endpoint para obtener estadísticas de ventas filtradas por período.
    Parámetros GET:
    - periodo: 'all', 'today', 'week', 'month'
    """
    from django.utils import timezone
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    periodo = request.GET.get('periodo', 'all')
    
    # Calcular rangos de tiempo
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    # Base queryset - excluir pedidos cancelados
    ventas_qs = PedidoDetalle.objects.select_related(
        'producto', 'producto__category', 'pedido'
    ).exclude(pedido__estado='cancelado')
    
    # Aplicar filtro de período
    if periodo == 'today':
        ventas_qs = ventas_qs.filter(pedido__fecha__gte=today_start)
    elif periodo == 'week':
        ventas_qs = ventas_qs.filter(pedido__fecha__gte=week_start)
    elif periodo == 'month':
        ventas_qs = ventas_qs.filter(pedido__fecha__gte=month_start)
    
    # Calcular ventas por categoría
    ventas_por_categoria_dict = {}
    total_ventas = 0
    total_productos = 0
    
    for detalle in ventas_qs:
        categoria = detalle.producto.category
        categoria_nombre = categoria.nombre if categoria else 'Sin Categoría'
        precio_total = float(detalle.precio) * int(detalle.cantidad)
        
        if categoria_nombre not in ventas_por_categoria_dict:
            ventas_por_categoria_dict[categoria_nombre] = {
                'nombre': categoria_nombre,
                'total_ingresos': 0,
                'cantidad_productos': 0,
                'cantidad_pedidos': 0,
                'pedidos_ids': set(),
            }
        
        ventas_por_categoria_dict[categoria_nombre]['total_ingresos'] += precio_total
        ventas_por_categoria_dict[categoria_nombre]['cantidad_productos'] += int(detalle.cantidad)
        ventas_por_categoria_dict[categoria_nombre]['pedidos_ids'].add(detalle.pedido.id)
        
        total_ventas += precio_total
        total_productos += int(detalle.cantidad)
    
    # Convertir a lista
    ventas_por_categoria = []
    for categoria_data in ventas_por_categoria_dict.values():
        categoria_data['cantidad_pedidos'] = len(categoria_data['pedidos_ids'])
        del categoria_data['pedidos_ids']
        ventas_por_categoria.append(categoria_data)
    
    # Ordenar por ingresos
    ventas_por_categoria.sort(key=lambda x: x['total_ingresos'], reverse=True)
    
    # Estadísticas generales
    pedidos_totales = Pedido.objects.exclude(estado='cancelado')
    if periodo == 'today':
        pedidos_totales = pedidos_totales.filter(fecha__gte=today_start)
    elif periodo == 'week':
        pedidos_totales = pedidos_totales.filter(fecha__gte=week_start)
    elif periodo == 'month':
        pedidos_totales = pedidos_totales.filter(fecha__gte=month_start)
    
    pedidos_count = pedidos_totales.count()
    promedio_pedido = total_ventas / pedidos_count if pedidos_count > 0 else 0
    
    return JsonResponse({
        'success': True,
        'periodo': periodo,
        'ventas_por_categoria': ventas_por_categoria,
        'estadisticas': {
            'total_ventas': total_ventas,
            'total_productos': total_productos,
            'pedidos_totales': pedidos_count,
            'promedio_por_pedido': promedio_pedido,
        },
        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
    })