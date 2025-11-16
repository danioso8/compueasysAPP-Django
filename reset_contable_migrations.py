import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.db import connection

# Eliminar la migración de contable del registro
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'contable'")
    connection.commit()
    print("✓ Registro de migraciones de contable eliminado")

print("\nAhora ejecuta: python manage.py migrate contable")
