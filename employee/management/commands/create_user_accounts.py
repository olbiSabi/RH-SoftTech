from django.core.management.base import BaseCommand
from employee.models import ZY00
from employee.services.embauche_service import EmbaucheService


class Command(BaseCommand):
    help = 'Créer des comptes utilisateurs pour les employés existants'

    def handle(self, *args, **kwargs):
        employes_sans_compte = ZY00.objects.filter(user__isnull=True, etat='actif')

        compteur_creation = 0

        for employe in employes_sans_compte:
            try:
                username, password = EmbaucheService.create_user_account(employe)

                compteur_creation += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Compte créé pour {employe.nom} {employe.prenoms} '
                        f'(Username: {username})'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour {employe.matricule}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n{compteur_creation} compte(s) utilisateur(s) créé(s) avec succès!')
        )
