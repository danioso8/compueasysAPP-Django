from os import name
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib import admin

from core.views import login_user, add_to_cart, add_to_cart_detail, clear_cart, pago_exitoso, mis_pedidos, remove_from_cart, store, auctions, services, contactUs, aboutUs, cart, register, login, product_detail, checkout, update_cart

from django.conf import settings

urlpatterns = [  
    
    path('store/', store, name='store'),  # Added this line to map the /store URL to the store view    
    path('services/', services, name='services'),  # Added this line to map the /services URL to the Services view
    path('contactUs/', contactUs, name='contactUs'),  # Added this line to map the /contactUs URL to the contactUs view
    path('aboutUs/', aboutUs, name='aboutUs'),  # Added this line to map the /aboutUs URL to the aboutUs view    
    path('register/', register, name='register'),  # Added this line to map the /register URL to the register view
    path('login/', login, name='login'),  # Added this line to map the /login URL to the login view
    path('admin/', admin.site.urls),  # URL pattern for the admin site
    path('checkout/', checkout, name='checkout'),  # URL pattern for checkout view
    path('product_detail/<int:product_id>/', product_detail, name='product_detail'),  # URL pattern for product detail view
    path('update_cart/<int:product_id>/', update_cart, name='update_cart'),  # URL pattern for update cart view
    path('logout/', include('django.contrib.auth.urls')),  # URL pattern for authentication views
    path('add_to_cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart, name='cart'),
    path('clear_cart/', clear_cart, name='clear_cart'),
    path('remove_from_cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('add_to_cart_detail/<int:product_id>/', add_to_cart_detail, name='add_to_cart_detail'),  # URL pattern for adding to cart from product detail view
    path('pago_exitoso/', pago_exitoso, name='pago_exitoso'),  # URL pattern for processing payment
    path('mis-pedidos/', mis_pedidos, name='mis_pedidos'),  # URL pattern for viewing user orders
    path('login_user/', login_user, name='login_user'),  # URL pattern for user login
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
