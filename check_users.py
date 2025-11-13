#!/usr/bin/env python
"""
Script para verificar usuarios en la base de datos
"""
import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import SimpleUser
from dashboard.models import register_superuser

print("=== USUARIOS SIMPLES ===")
simple_users = SimpleUser.objects.all()
if simple_users.exists():
    for user in simple_users:
        print(f"ID: {user.id}, Nombre: {user.name}, Email: {user.email}, Password: {user.password}")
else:
    print("No hay usuarios simples registrados")

print("\n=== USUARIOS ADMINISTRADORES ===")
admin_users = register_superuser.objects.all()
if admin_users.exists():
    for user in admin_users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Password: {user.password}")
else:
    print("No hay usuarios administradores registrados")

print("\n=== CREAR USUARIO DE PRUEBA ===")
# Crear un usuario simple de prueba si no existe
test_email = "test@test.com"
if not SimpleUser.objects.filter(email=test_email).exists():
    test_user = SimpleUser.objects.create(
        name="Usuario de Prueba",
        email=test_email,
        telefono="1234567890",
        username="testuser",
        password="123456",  # En producción usar hash
        address="Dirección de prueba",
        city="Ciudad de prueba"
    )
    print(f"Usuario de prueba creado: {test_user.email} / contraseña: 123456")
else:
    print(f"Usuario de prueba ya existe: {test_email}")