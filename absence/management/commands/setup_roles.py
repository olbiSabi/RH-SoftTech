from django.core.management.base import BaseCommand
from employee.models import ZYRO, ZYRE, ZY00
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Configure le système de rôles et permet d\'attribuer des rôles aux utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Crée uniquement les rôles sans interaction',
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Code du rôle à attribuer (ex: DAF, DRH, etc.)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email de l\'utilisateur à qui attribuer le rôle',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("INSTALLATION DU SYSTÈME DE RÔLES")
        self.stdout.write("=" * 80)

        # Créer les rôles
        self._create_roles()

        if options['auto']:
            self.stdout.write("✅ Rôles créés avec succès (mode auto)")
            return

        # Mode interactif pour attribution
        if options['role'] and options['email']:
            self._attribuer_role(options['role'], options['email'])
        else:
            self._mode_interactif()

    def _create_roles(self):
        """Crée tous les rôles de base"""
        roles_a_creer = [
            {
                'CODE': 'GESTION_APP',
                'LIBELLE': 'Gestionnaire Application',
                'DESCRIPTION': 'Accès complet au paramétrage de l\'application',
                'PERMISSIONS_CUSTOM': {
                    'can_manage_absence_settings': True,
                    'can_manage_entreprise_settings': True,
                    'can_manage_types_absence': True,
                    'can_manage_jours_feries': True,
                    'can_manage_conventions': True,
                    'can_manage_acquisitions': True,
                    'full_absence_access': True,
                    'full_entreprise_access': True,
                    'can_validate_rh': True,
                    'can_validate_manager': True,
                    'can_view_all_absences': True,
                    'can_manage_employees': True,
                    'can_view_all_imputations': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_manage_activites': True,
                    'can_manage_taches': True,
                    'can_view_all_projets': True,
                }
            },
            {
                'CODE': 'RH_VALIDATION_ABS',
                'LIBELLE': 'RH - Validation absences',
                'DESCRIPTION': 'Validation finale des absences au niveau RH',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_rh': True,
                    'can_view_all_absences': True,
                    'absence.valider_absence_rh': True,
                }
            },
            {
                'CODE': 'MANAGER_ABS',
                'LIBELLE': 'Manager - Validation absences',
                'DESCRIPTION': 'Validation des absences de ses subordonnés',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_manager': True,
                    'can_view_team_absences': True,
                }
            },
            {
                'CODE': 'EMPLOYE_STD',
                'LIBELLE': 'Employé standard',
                'DESCRIPTION': 'Peut déclarer et voir ses propres absences et imputations',
                'PERMISSIONS_CUSTOM': {
                    'can_create_absence': True,
                    'can_view_own_absences': True,
                    'can_create_imputation': True,
                    'can_view_own_imputations': True,
                }
            },
            {
                'CODE': 'DRH',
                'LIBELLE': 'Direction des Ressources Humaines',
                'DESCRIPTION': 'Accès complet à la gestion RH',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_rh': True,
                    'can_validate_manager': True,
                    'can_manage_employees': True,
                    'can_view_all_absences': True,
                    'can_manage_roles': True,
                    'can_view_payroll': True,
                    'absence.valider_absence_rh': True,
                    'can_view_all_imputations': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_manage_activites': True,
                    'can_manage_taches': True,
                    'can_view_all_projets': True,
                }
            },
            {
                'CODE': 'MANAGER',
                'LIBELLE': 'Manager de département',
                'DESCRIPTION': 'Validation des demandes de son équipe',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_manager': True,
                    'can_view_team_absences': True,
                    'can_manage_team': True,
                    'can_validate_imputations': True,
                    'can_view_team_imputations': True,
                    'can_manage_projets': True,
                    'can_view_all_projets': True,
                }
            },
            {
                'CODE': 'COMPTABLE',
                'LIBELLE': 'Comptable',
                'DESCRIPTION': 'Accès à la comptabilité et à la paie',
                'PERMISSIONS_CUSTOM': {
                    'can_view_payroll': True,
                    'can_manage_contracts': True,
                    'can_view_reports': True,
                    'can_view_all_imputations': True,
                    'can_view_facturables': True,
                }
            },
            {
                'CODE': 'DIRECTEUR',
                'LIBELLE': 'Directeur / Président',
                'DESCRIPTION': 'Accès complet à toutes les fonctionnalités',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_rh': True,
                    'can_validate_manager': True,
                    'can_manage_employees': True,
                    'can_view_all_absences': True,
                    'can_manage_roles': True,
                    'can_view_payroll': True,
                    'can_view_dashboard': True,
                    'can_manage_company': True,
                    'can_view_all_imputations': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_manage_activites': True,
                    'can_manage_taches': True,
                    'can_view_all_projets': True,
                }
            },
            {
                'CODE': 'ASSISTANT_RH',
                'LIBELLE': 'Assistant RH',
                'DESCRIPTION': 'Accès en lecture à la gestion RH',
                'PERMISSIONS_CUSTOM': {
                    'can_view_all_absences': True,
                    'can_view_employees': True,
                    'can_view_all_imputations': True,
                }
            },
            {
                'CODE': 'DAF',
                'LIBELLE': 'Directeur Administratif et Financier',
                'DESCRIPTION': 'Accès complet à la gestion financière, comptable et administrative',
                'PERMISSIONS_CUSTOM': {
                    'can_view_all_absences': True,
                    'can_view_payroll': True,
                    'can_view_reports': True,
                    'can_view_all_imputations': True,
                    'can_view_facturables': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_view_all_projets': True,
                    'can_manage_contracts': True,
                    'can_view_financial_reports': True,
                    'can_validate_timesheets': True,
                    'can_validate_frais': True,
                    'can_approve_avances': True,
                    'can_manage_frais_categories': True,
                    'can_view_frais_statistics': True,
                }
            }
        ]

        roles_crees = 0
        roles_mis_a_jour = 0

        for role_data in roles_a_creer:
            role, created = ZYRO.objects.get_or_create(
                CODE=role_data['CODE'],
                defaults={
                    'LIBELLE': role_data['LIBELLE'],
                    'DESCRIPTION': role_data['DESCRIPTION'],
                    'PERMISSIONS_CUSTOM': role_data['PERMISSIONS_CUSTOM'],
                    'actif': True
                }
            )
            if created:
                self.stdout.write(f"  ✅ Rôle créé: {role.CODE} - {role.LIBELLE}")
                roles_crees += 1
            else:
                role.PERMISSIONS_CUSTOM = role_data['PERMISSIONS_CUSTOM']
                role.DESCRIPTION = role_data['DESCRIPTION']
                role.save()
                self.stdout.write(f"  🔄 Rôle mis à jour: {role.CODE}")
                roles_mis_a_jour += 1

        self.stdout.write(f"\n✅ {roles_crees} nouveau(x) rôle(s) créé(s)")
        self.stdout.write(f"🔄 {roles_mis_a_jour} rôle(s) mis à jour")

    def _attribuer_role(self, role_code, email):
        """Attribue un rôle à un utilisateur"""
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"✅ Utilisateur trouvé: {user.username}")

            if not hasattr(user, 'employe') or not user.employe:
                self.stdout.write(self.style.ERROR("❌ Cet utilisateur n'a pas d'employé associé"))
                return

            employe = user.employe
            self.stdout.write(f"✅ Employé: {employe.nom} {employe.prenoms}")

            if employe.has_role(role_code):
                self.stdout.write(self.style.WARNING(f"⚠️  Cet employé a déjà le rôle {role_code}!"))
            else:
                role = ZYRO.objects.get(CODE=role_code)
                ZYRE.objects.create(
                    employe=employe,
                    role=role,
                    date_debut=date.today(),
                    actif=True,
                    commentaire=f'Attribution via commande setup_roles'
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Rôle {role_code} attribué à {employe.nom} {employe.prenoms}"))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Utilisateur '{email}' non trouvé"))
        except ZYRO.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Rôle '{role_code}' non trouvé"))

    def _mode_interactif(self):
        """Mode interactif pour attribution"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("2. Attribution d'un rôle principal")
        self.stdout.write("=" * 80)

        self.stdout.write("\nRôles disponibles pour attribution:")
        roles = ZYRO.objects.filter(actif=True).order_by('CODE')
        for i, role in enumerate(roles, 1):
            self.stdout.write(f"{i}. {role.CODE} - {role.LIBELLE}")

        try:
            # Simuler l'input avec les arguments ou utiliser une valeur par défaut
            choix = input("\nQuel rôle voulez-vous attribuer ? (numéro) : ")
            choix_idx = int(choix) - 1
            
            if 0 <= choix_idx < len(roles):
                role = roles[choix_idx]
                email = input(f"\nEmail de l'utilisateur pour le rôle {role.CODE}: ")
                self._attribuer_role(role.CODE, email)
            else:
                self.stdout.write(self.style.ERROR("❌ Choix invalide"))
        except (ValueError, KeyboardInterrupt):
            self.stdout.write(self.style.WARNING("⚠️  Opération annulée"))
