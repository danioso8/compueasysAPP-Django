"""
Management command para crear estructura de directorios de media en Render
Ejecutar en Render Shell: python manage.py fix_media_structure
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Crea la estructura de directorios de media en el disco persistente'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        
        # Directorios necesarios
        directories = [
            os.path.join(media_root, 'images'),
            os.path.join(media_root, 'variant_images'),
            os.path.join(media_root, 'galeria'),
            os.path.join(media_root, 'videos'),
            os.path.join(media_root, 'upload'),
        ]
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"🔧 Configurando estructura de media")
        self.stdout.write(f"📁 MEDIA_ROOT: {media_root}")
        self.stdout.write(f"{'='*60}\n")
        
        for directory in directories:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Creado: {directory}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Ya existe: {directory}")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creando {directory}: {str(e)}")
                )
        
        # Verificar permisos
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("🔒 Verificando permisos...")
        self.stdout.write(f"{'='*60}\n")
        
        for directory in directories:
            if os.path.exists(directory):
                stat_info = os.stat(directory)
                self.stdout.write(f"📂 {directory}")
                self.stdout.write(f"   Permisos: {oct(stat_info.st_mode)[-3:]}")
                
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("✅ Estructura de media lista"))
        self.stdout.write(f"{'='*60}\n")
        
        # Mostrar siguiente paso
        self.stdout.write("\n📋 SIGUIENTE PASO:")
        self.stdout.write("   Sube las imágenes desde el Dashboard de Django:")
        self.stdout.write(f"   https://compueasys.onrender.com/dashboard/\n")
