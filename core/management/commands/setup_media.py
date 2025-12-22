from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Crea la estructura de directorios para media files en Render'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        
        # Crear directorios necesarios
        directories = [
            media_root,
            os.path.join(media_root, 'images'),
            os.path.join(media_root, 'galeria'),
            os.path.join(media_root, 'variant_images'),
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    self.stdout.write(self.style.SUCCESS(f'✅ Creado: {directory}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error creando {directory}: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Ya existe: {directory}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Estructura de directorios lista'))
        self.stdout.write(f'📁 MEDIA_ROOT: {media_root}')
        self.stdout.write(f'🌐 MEDIA_URL: {settings.MEDIA_URL}')
