from django.urls import path
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from AppCompueasys import settings
from core.views import home, index

from .views import (
    Category,
    dashboard_home,
    dar_permiso_staff,   
    eliminar_usuario,
    editar_usuario,
    edit_product,
    eliminar_producto,
    delete_category,
    crear_categoria,
    editar_categoria,  
    api_get_product,  
    create_proveedor,
    edit_proveedor,
    delete_proveedor,
    crear_tipo,
    edit_tipo,
    delete_tipo,
   
)

urlpatterns = [
    path('dashboard_home/', dashboard_home, name='dashboard_home'),
    
    path('producto/crear/', dashboard_home, name='crear_producto'),
    path('producto/<int:product_id>/editar/', edit_product, name='edit_product'),
    path('producto/<int:product_id>/eliminar/', eliminar_producto, name='eliminar_producto'),
    path('api/producto/<int:product_id>/', api_get_product, name='api_get_product'),
   
    path('usuario/<int:user_id>/dar_permiso_staff/', dar_permiso_staff, name='dar_permiso_staff'),        
    path('usuario/<int:user_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),
    path('usuario/<int:user_id>/editar/', editar_usuario, name='editar_usuario'), 
      
    path('categoria/crear/', crear_categoria, name='crear_categoria'),
    path('categoria/<int:category_id>/editar/', editar_categoria, name='editar_categoria'),
    path('categoria/<int:category_id>/eliminar/', delete_category, name='delete_category'),    
   
   


    path('crear/proveedor/', create_proveedor, name='create_proveedor'),
    path('proveedor/<int:proveedor_id>/editar/', edit_proveedor, name='edit_proveedor'),
    path('proveedor/<int:proveedor_id>/eliminar/', delete_proveedor, name='delete_proveedor'),

    path('crear/tipo/', crear_tipo, name='crear_tipo'),
    path('tipo/<int:tipo_id>/editar/', edit_tipo, name='edit_tipo'),
    path('tipo/<int:tipo_id>/eliminar/', delete_tipo, name='delete_tipo'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)