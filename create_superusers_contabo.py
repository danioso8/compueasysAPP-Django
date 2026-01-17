import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from dashboard.models import register_superuser

print("\n" + "="*60)
print("CREANDO SUPERUSUARIOS")
print("="*60 + "\n")

# Lista de superusuarios a crear
superusers_data = [
    {
        'username': 'admin',
        'password': 'CompuEasys2026!',
        'email': 'admin@compueasys.com',
        'phone': '3001234567'
    },
    {
        'username': 'danioso8',
        'password': 'Miesposa0526@',
        'email': 'danioso8@compueasys.com',
        'phone': '3001234568'
    }
]

for data in superusers_data:
    # Verificar si ya existe
    existing = register_superuser.objects.filter(username=data['username']).first()
    
    if existing:
        print(f"⚠️  El usuario '{data['username']}' ya existe. Actualizando contraseña...")
        existing.password = data['password']
        existing.email = data['email']
        existing.phone = data.get('phone', '')
        existing.save()
        print(f"✅ Usuario '{data['username']}' actualizado")
    else:
        # Crear nuevo superusuario
        user = register_superuser.objects.create(
            username=data['username'],
            password=data['password'],  # En texto plano según el patrón del proyecto
            email=data['email'],
            phone=data.get('phone', '')
        )
        print(f"✅ Superusuario '{data['username']}' creado exitosamente")
    
    print(f"   Username: {data['username']}")
    print(f"   Password: {data['password']}")
    print(f"   Email: {data['email']}")
    print("-" * 60)

print("\n✅ Proceso completado!\n")
print("Ahora puedes iniciar sesión con:")
print("  - admin / CompuEasys2026!")
print("  - danioso8 / Miesposa0526@\n")
