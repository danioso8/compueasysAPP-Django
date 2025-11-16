import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from contable.models import ContableUser, UserProfile

print("\n" + "=" * 70)
print("⭐ SUPERUSUARIOS DEL SISTEMA CONTABLE")
print("=" * 70 + "\n")

superusers = ContableUser.objects.filter(is_superuser=True).select_related('profile')

if superusers.exists():
    for user in superusers:
        print(f"📧 Email: {user.email}")
        print(f"👤 Nombre: {user.get_full_name()}")
        print(f"📱 Teléfono: {user.phone or 'N/A'}")
        print(f"🔑 ID: {user.id}")
        print(f"✅ Activo: {'Sí' if user.is_active else 'No'}")
        print(f"✅ Email verificado: {'Sí' if user.email_verified else 'No'}")
        print(f"⭐ is_superuser: {'Sí' if user.is_superuser else 'No'}")
        print(f"🛡️  is_staff: {'Sí' if user.is_staff else 'No'}")
        
        if hasattr(user, 'profile'):
            print(f"👔 Rol en perfil: {user.profile.get_role_display()}")
        else:
            print(f"👔 Rol en perfil: ❌ Sin perfil")
        
        print(f"📅 Fecha registro: {user.date_joined.strftime('%d/%m/%Y %H:%M')}")
        print(f"🕐 Último login: {user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Nunca'}")
        print("=" * 70 + "\n")
else:
    print("❌ No hay superusuarios registrados en el sistema")
    print("\n💡 Para crear uno, ejecuta:")
    print("   python make_superuser.py")
    print("=" * 70 + "\n")

# Mostrar total de usuarios
total = ContableUser.objects.count()
print(f"📊 Total de usuarios en el sistema: {total}")
print("=" * 70)
