import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.contrib.auth.models import User
from contable.models import UserProfile

print("=== VERIFICANDO USUARIOS ===\n")

# Mostrar todos los usuarios
users = User.objects.all()
print(f"Total usuarios: {users.count()}\n")

for user in users:
    print(f"ID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Nombre: {user.get_full_name()}")
    print(f"Activo: {user.is_active}")
    print(f"Superuser: {user.is_superuser}")
    
    # Verificar si tiene perfil
    try:
        profile = UserProfile.objects.get(user=user)
        print(f"Perfil: Sí (Verificado: {profile.email_verified})")
    except UserProfile.DoesNotExist:
        print(f"Perfil: No")
    except UserProfile.MultipleObjectsReturned:
        print(f"Perfil: MÚLTIPLES (ERROR)")
    
    print("-" * 50)

# Buscar emails duplicados
from django.db.models import Count
duplicates = User.objects.values('email').annotate(count=Count('email')).filter(count__gt=1)

if duplicates.exists():
    print("\n⚠️  EMAILS DUPLICADOS ENCONTRADOS:")
    for dup in duplicates:
        print(f"  Email: {dup['email']} ({dup['count']} veces)")
        users_with_email = User.objects.filter(email=dup['email'])
        for u in users_with_email:
            print(f"    - ID {u.id}: {u.username}")
else:
    print("\n✓ No hay emails duplicados")
