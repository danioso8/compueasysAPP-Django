#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.contrib.auth.models import User

# Crear superusuario danioso8
username = 'danioso8'
email = 'danioso8@hotmail.com'
password = 'Miesposa0526@'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'✅ Superusuario creado exitosamente')
    print(f'   Usuario: {username}')
    print(f'   Email: {email}')
    print(f'   Contraseña: {password}')
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.email = email
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f'✅ Usuario {username} actualizado')
    print(f'   Email: {email}')
    print(f'   Contraseña: {password}')
