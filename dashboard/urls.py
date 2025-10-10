from django.urls import path


from .views import dashboard_home, dar_permiso_staff, eliminar_usuario, editar_usuario

urlpatterns = [
    path('dashboard_home/', dashboard_home, name='dashboard_home'),
    path('usuario/<int:user_id>/dar_permiso_staff/', dar_permiso_staff, name='dar_permiso_staff'),
    path('usuario/<int:user_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),
    path('usuario/<int:user_id>/editar/', editar_usuario, name='editar_usuario'),
]