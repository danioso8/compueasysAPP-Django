from os import name
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib import admin

from core.views import (
    add_to_cart, login_user, add_to_cart_detail, clear_cart, pago_exitoso, 
    mis_pedidos, remove_from_cart, store, auctions, services, contactUs, 
    aboutUs, cart, register_user, login, product_detail, checkout, 
    update_cart, logout_view, search_suggestions, 
    filter_products_ajax, get_categories_ajax
)

from django.conf import settings

urlpatterns = [  
    
    path('store/', store, name='store'),  # Added this line to map the /store URL to the store view
    
    path('services/', services, name='services'),  # Added this line to map the /services URL to the Services view
    path('contactUs/', contactUs, name='contactUs'),  # Added this line to map the /contactUs URL to the contactUs view
    path('aboutUs/', aboutUs, name='aboutUs'),  # Added this line to map the /aboutUs URL to the aboutUs view
    path('register_user/', register_user, name='register_user'),  # Added this line to map the /register URL to the register view
    path('login/', login, name='login'),  # Added this line to map the /login URL to the login view
    path('admin/', admin.site.urls),  # URL pattern for the admin site
    path('checkout/', checkout, name='checkout'),  # URL pattern for checkout view
    path('product_detail/<int:product_id>/', product_detail, name='product_detail'),  # URL pattern for product detail view
    path('update_cart/<int:product_id>/', update_cart, name='update_cart'),  # URL pattern for update cart view
    path('logout/', include('django.contrib.auth.urls')),  # URL pattern for authentication views
   
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('add-to-cart-detail/<int:product_id>/', add_to_cart_detail, name='add_to_cart_detail'),  # URL pattern for adding to cart from product detail view

    path('cart/', cart, name='cart'),
    path('clear_cart/', clear_cart, name='clear_cart'),
    path('remove_from_cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
   
    path('pago_exitoso/', pago_exitoso, name='pago_exitoso'),  # URL pattern for processing payment
    path('mis-pedidos/', mis_pedidos, name='mis_pedidos'),  # URL pattern for viewing user orders
    path('login_user/', login_user, name='login_user'),  # URL pattern for user login
    path('logout_view/', logout_view, name='logout_view'),  # URL pattern for user logout
    
    # Endpoints AJAX para store moderno
    path('api/search-suggestions/', search_suggestions, name='search_suggestions'),
    path('api/filter-products/', filter_products_ajax, name='filter_products_ajax'),
    path('api/categories/', get_categories_ajax, name='get_categories_ajax'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
