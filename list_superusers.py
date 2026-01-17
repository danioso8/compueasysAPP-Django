import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from dashboard.models import register_superuser

print("\n" + "="*60)
print("LISTA DE SUPERUSUARIOS EN LA BASE DE DATOS")
print("="*60 + "\n")

superusers = register_superuser.objects.all()

if superusers.exists():
    for i, user in enumerate(superusers, 1):
        print(f"Superusuario #{i}:")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Password: {user.password}")
        print(f"  Email: {user.email if hasattr(user, 'email') else 'N/A'}")
        print(f"  Activo: {user.is_active if hasattr(user, 'is_active') else 'N/A'}")
        print("-" * 60)
    
    print(f"\nTotal de superusuarios: {superusers.count()}\n")
else:
    print("❌ No hay superusuarios registrados en la base de datos\n")
