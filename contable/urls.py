

from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from contable.views import  product, product_create, product_edit, product_delete


urlpatterns = [
   path('product/', product, name='product'), 
   path('product/create/', product_create, name='product_create'), 
   path('product/edit/<int:product_id>/', product_edit, name='product_edit'),
   path('product/delete/<int:product_id>/', product_delete, name='product_delete'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
