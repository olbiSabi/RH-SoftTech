# employee/management/commands/unlock_account.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from employee.models import UserSecurity


class Command(BaseCommand):
    help = 'Débloquer un compte utilisateur spécifique'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help="Nom d'utilisateur à débloquer")

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
            security, created = UserSecurity.objects.get_or_create(user=user)

            if security.is_locked:
                security.reset_attempts()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Compte {username} débloqué avec succès')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'ℹ️ Le compte {username} n\'était pas bloqué')
                )

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Utilisateur {username} non trouvé')
            )