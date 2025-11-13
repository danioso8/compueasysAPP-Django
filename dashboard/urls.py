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
    eliminar_categoria,  # Nueva función de eliminación  
    api_get_product,  
    create_proveedor,
    edit_proveedor,
    delete_proveedor,
    crear_tipo,
    edit_tipo,
    delete_tipo,
    pedido_detalle,  # Nueva función para detalles de pedido
    update_pedido_estado,  # Nueva función para actualizar estado
    update_pedido_notes,  # Nueva función para actualizar notas
    # Nuevas funciones para gestión de usuarios
    edit_user,
    delete_user,
    get_user_details,
    # Nuevas funciones para gestión de conversaciones
    conversation_detail,
    conversation_reply,
    conversation_update_status,
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
    path('categoria/<int:categoria_id>/editar/', editar_categoria, name='editar_categoria'),
    path('categoria/<int:category_id>/eliminar/', delete_category, name='delete_category'),    
   
    # Nuevas rutas AJAX para categorías
    path('categorias/crear/', crear_categoria, name='ajax_crear_categoria'),
    path('categorias/editar/<int:categoria_id>/', editar_categoria, name='ajax_editar_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', eliminar_categoria, name='ajax_eliminar_categoria'),    
   
   


    path('crear/proveedor/', create_proveedor, name='create_proveedor'),
    path('proveedor/<int:proveedor_id>/editar/', edit_proveedor, name='edit_proveedor'),
    path('proveedor/<int:proveedor_id>/eliminar/', delete_proveedor, name='delete_proveedor'),

    path('crear/tipo/', crear_tipo, name='crear_tipo'),
    path('tipo/<int:tipo_id>/editar/', edit_tipo, name='edit_tipo'),
    path('tipo/<int:tipo_id>/eliminar/', delete_tipo, name='delete_tipo'),

    # URLs para gestión de pedidos
    path('pedido/<int:pedido_id>/detalle/', pedido_detalle, name='pedido_detalle'),
    path('pedido/update-estado/', update_pedido_estado, name='update_pedido_estado'),
    path('pedido/update-notes/', update_pedido_notes, name='update_pedido_notes'),

    # Nuevas URLs para gestión de usuarios
    path('usuario/editar/', edit_user, name='edit_user'),
    path('usuario/eliminar/', delete_user, name='delete_user'),
    path('usuario/<int:user_id>/<str:model_type>/detalles/', get_user_details, name='get_user_details'),

    # URLs para gestión de conversaciones (dashboard admin)
    path('admin/conversation/<int:conversation_id>/', conversation_detail, name='admin_conversation_detail'),
    path('admin/conversation/reply/', conversation_reply, name='admin_conversation_reply'),
    path('admin/conversation/update-status/', conversation_update_status, name='admin_conversation_update_status'),

]

# Solo servir archivos media localmente si no estamos usando Cloudinary
if settings.DEBUG and not getattr(settings, 'USE_CLOUDINARY', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)