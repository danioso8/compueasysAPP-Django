
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from core.models import ProductStore, ProductVariant, Galeria  # importa todos los modelos que uses en señales


@receiver(post_delete, sender=ProductStore)
def delete_product_image(sender, instance, **kwargs):
    if instance.imagen:
        instance.imagen.delete(False)

@receiver(post_delete, sender=ProductVariant)
def delete_variant_image(sender, instance, **kwargs):
    if instance.imagen:
        instance.imagen.delete(False)

@receiver(post_delete, sender=Galeria)
def delete_galeria_image(sender, instance, **kwargs):
    if instance.galeria:
        instance.galeria.delete(False)