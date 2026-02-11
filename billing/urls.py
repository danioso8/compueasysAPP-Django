# URLs para el módulo de facturación
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Configuración Matias API
    path('matias/config/', views.matias_config, name='matias_config'),
    path('matias/test-connection/', views.matias_test_connection, name='matias_test_connection'),
    
    # Facturas - Lista y creación
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:invoice_id>/delete/', views.invoice_delete, name='invoice_delete'),
    
    # Facturación Electrónica - Matias API
    path('invoices/<int:invoice_id>/send-matias/', views.send_invoice_matias, name='send_invoice_matias'),
    path('invoices/<int:invoice_id>/check-status/', views.matias_check_status, name='matias_check_status'),
    path('invoices/<int:invoice_id>/download-pdf/', views.matias_download_pdf, name='matias_download_pdf'),
    path('invoices/<int:invoice_id>/download-xml/', views.matias_download_xml, name='matias_download_xml'),
    
    # AJAX - Búsqueda de productos
    path('products/search/', views.search_products_ajax, name='search_products_ajax'),
    
    # PDF de factura normal
    path('invoices/<int:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
