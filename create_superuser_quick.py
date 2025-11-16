import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from contable.models import ContableUser, UserProfile

# Datos del superusuario
email = 'admin@compueasys.com'
password = 'Admin123456'
first_name = 'Super'
last_name = 'Admin'
phone = '3000000000'

# Verificar si ya existe
if ContableUser.objects.filter(email=email).exists():
    print(f'❌ Ya existe un usuario con el email {email}')
    user = ContableUser.objects.get(email=email)
    print(f'\n📧 Email: {user.email}')
    print(f'👤 Nombre: {user.get_full_name()}')
    print(f'⭐ Es superusuario: {"Sí" if user.is_superuser else "No"}')
else:
    # Crear superusuario
    user = ContableUser.objects.create_superuser(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email_verified=True
    )

    # Crear perfil
    UserProfile.objects.create(
        user=user,
        role='superuser'
    )

    print('=' * 60)
    print('✅ SUPERUSUARIO CREADO EXITOSAMENTE')
    print('=' * 60)
    print(f'\n📧 Email: {email}')
    print(f'🔑 Contraseña: {password}')
    print(f'👤 Nombre: {user.get_full_name()}')
    print(f'📱 Teléfono: {phone}')
    print(f'⭐ Rol: Superusuario')
    print(f'✅ Email Verificado: Sí')
    print(f'\n🌐 Inicia sesión en: http://localhost:8000/contable/login/')
    print(f'⚙️  Panel de admin: http://localhost:8000/contable/admin/users/')
    print('=' * 60)
