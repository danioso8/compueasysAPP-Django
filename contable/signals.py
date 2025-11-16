from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear UserProfile automáticamente cuando se crea un User"""
    if created:
        from contable.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar UserProfile cuando se guarda el User"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
