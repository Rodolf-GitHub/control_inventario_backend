from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from usuario.models import Usuario
import getpass


class Command(BaseCommand):
    help = 'Crear un superadmin Usuario desde la consola'

    def handle(self, *args, **options):
        username = input('Username: ').strip()
        if not username:
            self.stdout.write(self.style.ERROR('El nombre de usuario no puede estar vacío'))
            return

        if Usuario.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR('Ya existe un usuario con ese username'))
            return

        passwd = getpass.getpass('Password: ')
        passwd2 = getpass.getpass('Password (again): ')
        if passwd != passwd2:
            self.stdout.write(self.style.ERROR('Las contraseñas no coinciden'))
            return

        user = Usuario(username=username, password=make_password(passwd), es_superusuario=True)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Superadmin "{username}" creado con éxito'))
