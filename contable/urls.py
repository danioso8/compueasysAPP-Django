from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from contable.views import product, product_create, product_edit, product_delete
from contable import auth_views
from contable import admin_views

app_name = 'contable'

urlpatterns = [
    # Vistas antiguas de productos (mantener compatibilidad)
    path('product/', product, name='product'), 
    path('product/create/', product_create, name='product_create'), 
    path('product/edit/<int:product_id>/', product_edit, name='product_edit'),
    path('product/delete/<int:product_id>/', product_delete, name='product_delete'),
    
    # Nuevas vistas de autenticación del sistema contable
    path('register/', auth_views.register_view, name='register'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('verify/<str:token>/', auth_views.verify_email, name='verify_email'),
    path('forgot-password/', auth_views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', auth_views.reset_password, name='reset_password'),
    
    # Dashboard principal
    path('dashboard/', auth_views.dashboard_view, name='dashboard'),
    
    # Administración de usuarios (solo superusuarios)
    path('admin/users/', admin_views.admin_users_view, name='admin_users'),
    path('admin/users/<uuid:user_id>/toggle/', admin_views.toggle_user_status, name='toggle_user_status'),
    path('admin/users/<uuid:user_id>/verify/', admin_views.verify_user_email, name='verify_user_email'),
    path('admin/users/<uuid:user_id>/delete/', admin_views.delete_user, name='delete_user'),
    path('admin/users/<uuid:user_id>/edit/', admin_views.edit_user_view, name='edit_user'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
