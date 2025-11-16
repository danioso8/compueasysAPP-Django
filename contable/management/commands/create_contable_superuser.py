from django.core.management.base import BaseCommand
from contable.models import ContableUser, UserProfile
import getpass


class Command(BaseCommand):
    help = 'Crea un superusuario para el sistema contable'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email del superusuario')
        parser.add_argument('--password', type=str, help='Contraseña del superusuario')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== CREAR SUPERUSUARIO CONTABLE ===\n'))

        # Obtener email
        email = options.get('email')
        if not email:
            email = input('Email: ').strip().lower()

        # Verificar si ya existe
        if ContableUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'Ya existe un usuario con el email {email}'))
            return

        # Obtener nombre
        first_name = input('Nombre: ').strip()
        last_name = input('Apellido: ').strip()
        phone = input('Teléfono (opcional): ').strip()

        # Obtener contraseña
        password = options.get('password')
        if not password:
            while True:
                password = getpass.getpass('Contraseña: ')
                password_confirm = getpass.getpass('Confirmar contraseña: ')
                
                if password != password_confirm:
                    self.stdout.write(self.style.ERROR('Las contraseñas no coinciden. Intenta de nuevo.'))
                elif len(password) < 8:
                    self.stdout.write(self.style.ERROR('La contraseña debe tener al menos 8 caracteres.'))
                else:
                    break

        try:
            # Crear superusuario
            user = ContableUser.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email_verified=True  # Pre-verificado
            )

            # Crear perfil con rol de superusuario
            UserProfile.objects.create(
                user=user,
                role='superuser'
            )

            self.stdout.write(self.style.SUCCESS(f'\n✓ Superusuario creado exitosamente!'))
            self.stdout.write(self.style.SUCCESS(f'  Email: {user.email}'))
            self.stdout.write(self.style.SUCCESS(f'  Nombre: {user.get_full_name()}'))
            self.stdout.write(self.style.SUCCESS(f'  Rol: Superusuario\n'))
            self.stdout.write(self.style.WARNING(f'Puedes iniciar sesión en: /contable/login/\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear superusuario: {str(e)}'))
