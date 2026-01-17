#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.contrib.auth.models import User

# Crear superusuario
username = 'admin'
email = 'admin@compueasys.com'
password = 'CompuEasys2026!'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'✅ Superusuario creado exitosamente')
    print(f'   Usuario: {username}')
    print(f'   Contraseña: {password}')
else:
    print(f'⚠️  El usuario {username} ya existe')
