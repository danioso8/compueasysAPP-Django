"""
Mixins reutilizables para modelos Django
"""
from django.db import models
from django.utils import timezone


class TimeStampedMixin(models.Model):
    """Mixin para añadir timestamps a cualquier modelo"""
    created_at = models.DateTimeField(
        'Fecha de creación',
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        'Última actualización',
        auto_now=True
    )

    class Meta:
        abstract = True


class OrganizationMixin(models.Model):
    """Mixin para multi-tenancy con organización"""
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        verbose_name='Organización',
        related_name='%(class)s_set'
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization']),
        ]


class SoftDeleteMixin(models.Model):
    """Mixin para eliminación suave (soft delete)"""
    is_deleted = models.BooleanField(
        'Eliminado',
        default=False,
        db_index=True
    )
    deleted_at = models.DateTimeField(
        'Fecha de eliminación',
        null=True,
        blank=True
    )
    deleted_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted_set',
        verbose_name='Eliminado por'
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Elimina suavemente el registro"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restaura un registro eliminado"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class ActiveMixin(models.Model):
    """Mixin para control de estado activo/inactivo"""
    is_active = models.BooleanField(
        'Activo',
        default=True,
        db_index=True,
        help_text='Indica si el registro está activo'
    )

    class Meta:
        abstract = True


class OrderMixin(models.Model):
    """Mixin para ordenamiento manual"""
    order = models.PositiveIntegerField(
        'Orden',
        default=0,
        db_index=True,
        help_text='Orden de visualización'
    )

    class Meta:
        abstract = True
        ordering = ['order']
