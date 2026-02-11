# Signals para el módulo de facturación
from django.db.models.signals import post_save
from django.dispatch import receiver

# Aquí se pueden agregar signals para:
# - Envío automático de facturas por email
# - Notificaciones cuando se aprueba una factura electrónica
# - Descuento automático de stock después de facturar
