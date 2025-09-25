from django.contrib import admin

# Register your models here.
from .models import ProductStore, Galeria, Category, Type


admin.site.register(Galeria)   
admin.site.register(Category)
admin.site.register(Type)


class GaleriaInline(admin.TabularInline):
    model = Galeria
    extra = 1
    fields = ['galeria', 'preview']
    readonly_fields = ['preview']

    def preview(self, obj):
        if obj.galeria:
            return f'<img src="{obj.galeria.url}" style="max-height:60px;"/>'
        return ""
    preview.allow_tags = True
    preview.short_description = "Vista previa"

@admin.register(ProductStore)
class ProductStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'descuento', 'stock', 'category', 'image_tag')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [GaleriaInline]
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'price', 'descuento', 'stock')
        }),
        ('Descripción', {
            'fields': ('description',)
        }),
         ('Categoría', {
            'fields': ('category',)
        }),
          ('Tipo', {
            'fields': ('type',)
        }),
        ('Imagen principal', {
            'fields': ('imagen', 'image_tag',)
        }),
    )
    readonly_fields = ['image_tag']

    def image_tag(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" style="max-height:80px;"/>'
        return ""
    image_tag.allow_tags = True
    image_tag.short_description = "Vista previa"


