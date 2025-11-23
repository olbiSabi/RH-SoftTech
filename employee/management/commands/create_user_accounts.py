from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from employee.models import ZY00


class Command(BaseCommand):
    help = 'Créer des comptes utilisateurs pour les employés existants'

    def handle(self, *args, **kwargs):
        employes_sans_compte = ZY00.objects.filter(user__isnull=True, etat='actif')

        compteur_creation = 0

        for employe in employes_sans_compte:
            # Générer un username unique
            username = f"{employe.nom.lower()}.{employe.prenoms.split()[0].lower()}"

            # Vérifier si le username existe déjà
            if User.objects.filter(username=username).exists():
                username = f"{username}{employe.matricule[-3:]}"

            try:
                # Créer l'utilisateur
                user = User.objects.create_user(
                    username=username,
                    password='Hronian2024!',  # Mot de passe temporaire
                    first_name=employe.prenomuser,
                    last_name=employe.username,
                    email=f"{username}@hronian.com"
                )

                # Lier à l'employé
                employe.user = user
                employe.save()

                compteur_creation += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Compte créé pour {employe.username} {employe.prenomuser} '
                        f'(Username: {username}, Password: Hronian2024!)'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur pour {employe.matricule}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 {compteur_creation} compte(s) utilisateur(s) créé(s) avec succès!')
        )