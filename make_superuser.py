import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from contable.models import ContableUser

# Actualizar tu usuario actual a superusuario
email = 'danioso8@hotmail.com'

try:
    user = ContableUser.objects.get(email=email)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    
    # Actualizar perfil
    if hasattr(user, 'profile'):
        user.profile.role = 'superuser'
        user.profile.save()
    
    print('=' * 60)
    print('✅ USUARIO ACTUALIZADO A SUPERUSUARIO')
    print('=' * 60)
    print(f'\n📧 Email: {user.email}')
    print(f'👤 Nombre: {user.get_full_name()}')
    print(f'⭐ Rol: Superusuario')
    print(f'✅ is_superuser: {user.is_superuser}')
    print(f'✅ is_staff: {user.is_staff}')
    print(f'\n🌐 Panel de admin: http://localhost:8000/contable/admin/users/')
    print('=' * 60)
    
except ContableUser.DoesNotExist:
    print(f'❌ No se encontró usuario con email {email}')
