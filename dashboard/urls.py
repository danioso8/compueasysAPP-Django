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
    delete_product,
    delete_category,
    crear_categoria,
    editar_categoria,    
)

urlpatterns = [
    path('dashboard_home/', dashboard_home, name='dashboard_home'),
    path('producto/crear/', dashboard_home, name='crear_producto'),
    path('producto/<int:product_id>/editar/', edit_product, name='edit_product'),
    path('producto/<int:product_id>/eliminar/', delete_product, name='delete_product'),
   
    path('usuario/<int:user_id>/dar_permiso_staff/', dar_permiso_staff, name='dar_permiso_staff'),        
    path('usuario/<int:user_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),
    path('usuario/<int:user_id>/editar/', editar_usuario, name='editar_usuario'), 
   
   
    path('categoria/crear/', crear_categoria, name='crear_categoria'),
    path('categoria/<int:category_id>/editar/', editar_categoria, name='editar_categoria'),
    path('categoria/<int:category_id>/eliminar/', delete_category, name='delete_category'),
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)