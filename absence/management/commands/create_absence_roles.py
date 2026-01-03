# employee/management/commands/create_absence_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from employee.models import ZYRO


class Command(BaseCommand):
    help = 'Crée les rôles par défaut pour la gestion des absences'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔄 Création des rôles d\'absence...'))

        # Récupérer les permissions pour les absences
        absence_permissions = Permission.objects.filter(
            content_type__app_label='absence'
        )

        # Récupérer les permissions pour l'entreprise
        entreprise_permissions = Permission.objects.filter(
            content_type__app_label='entreprise'
        )

        # ========================================
        # 1. Rôle "GESTION_APP" - Super Admin Paramétrage
        # ========================================
        self.stdout.write('📋 Création du rôle GESTION_APP...')

        # Permissions pour la gestion complète
        gestion_app_permissions = Permission.objects.filter(
            content_type__app_label__in=['absence', 'entreprise']
        ) | Permission.objects.filter(
            codename__in=[
                # Absence - Toutes les permissions
                'add_typeabsence',
                'change_typeabsence',
                'delete_typeabsence',
                'view_typeabsence',
                'add_jourferie',
                'change_jourferie',
                'delete_jourferie',
                'view_jourferie',
                'add_conventionconges',
                'change_conventionconges',
                'delete_conventionconges',
                'view_conventionconges',
                'add_parametrecalcul',
                'change_parametrecalcul',
                'delete_parametrecalcul',
                'view_parametrecalcul',
                'add_acquisitionconges',
                'change_acquisitionconges',
                'delete_acquisitionconges',
                'view_acquisitionconges',
                'valider_absence_rh',
                'valider_absence_manager',
                'voir_toutes_absences',
                'exporter_absences',
                'gerer_types_absence',

                # Entreprise - Toutes les permissions
                'add_entreprise',
                'change_entreprise',
                'delete_entreprise',
                'view_entreprise',
            ]
        )

        gestion_app_role, created = ZYRO.objects.get_or_create(
            CODE='GESTION_APP',
            defaults={
                'LIBELLE': 'Gestionnaire Application',
                'DESCRIPTION': 'Accès complet au paramétrage des absences et de l\'entreprise',
                'PERMISSIONS_CUSTOM': {
                    'can_manage_absence_settings': True,
                    'can_manage_entreprise_settings': True,
                    'can_manage_types_absence': True,
                    'can_manage_jours_feries': True,
                    'can_manage_conventions': True,
                    'can_manage_acquisitions': True,
                    'full_absence_access': True,
                    'full_entreprise_access': True,
                },
                'actif': True
            }
        )

        # Créer le groupe Django associé
        django_group_gestion_app, _ = Group.objects.get_or_create(name='GESTION_APP')

        # Ajouter TOUTES les permissions
        for perm in gestion_app_permissions:
            django_group_gestion_app.permissions.add(perm)

        if gestion_app_role.django_group != django_group_gestion_app:
            gestion_app_role.django_group = django_group_gestion_app
            gestion_app_role.save()

        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Rôle GESTION_APP créé'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Rôle GESTION_APP mis à jour'))

        # ========================================
        # 2. Rôle "RH Validation Absences"
        # ========================================
        self.stdout.write('📋 Création du rôle RH_VALIDATION_ABS...')

        rh_permissions = absence_permissions.filter(
            codename__in=[
                'valider_absence_rh',
                'voir_toutes_absences',
                'exporter_absences',
                'view_absence',
                'view_acquisitionconges',
            ]
        )

        rh_role, created = ZYRO.objects.get_or_create(
            CODE='RH_VALIDATION_ABS',
            defaults={
                'LIBELLE': 'RH - Validation absences',
                'DESCRIPTION': 'Peut valider les absences au niveau RH',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_rh': True,
                    'can_view_all_absences': True,
                    'absence.valider_absence_rh': True,
                },
                'actif': True
            }
        )

        # Synchroniser avec Django Group
        django_group_rh, _ = Group.objects.get_or_create(name='RH_VALIDATION_ABS')
        for perm in rh_permissions:
            django_group_rh.permissions.add(perm)

        if rh_role.django_group != django_group_rh:
            rh_role.django_group = django_group_rh
            rh_role.save()

        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Rôle RH_VALIDATION_ABS créé'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Rôle RH_VALIDATION_ABS mis à jour'))

        # ========================================
        # 3. Rôle "Manager Validation Absences"
        # ========================================
        self.stdout.write('📋 Création du rôle MANAGER_ABS...')

        manager_permissions = absence_permissions.filter(
            codename__in=[
                'valider_absence_manager',
                'voir_toutes_absences',
                'view_absence',
                'add_absence',
                'change_absence',
            ]
        )

        manager_role, created = ZYRO.objects.get_or_create(
            CODE='MANAGER_ABS',
            defaults={
                'LIBELLE': 'Manager - Validation absences',
                'DESCRIPTION': 'Peut valider les absences de ses subordonnés',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_manager': True,
                    'can_view_team_absences': True,
                },
                'actif': True
            }
        )

        django_group_manager, _ = Group.objects.get_or_create(name='MANAGER_ABS')
        for perm in manager_permissions:
            django_group_manager.permissions.add(perm)

        if manager_role.django_group != django_group_manager:
            manager_role.django_group = django_group_manager
            manager_role.save()

        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Rôle MANAGER_ABS créé'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Rôle MANAGER_ABS mis à jour'))

        # ========================================
        # 4. Rôle "Employé Standard"
        # ========================================
        self.stdout.write('📋 Création du rôle EMPLOYE_STD...')

        employe_permissions = absence_permissions.filter(
            codename__in=[
                'add_absence',
                'view_absence',
                'change_absence',
                'delete_absence',
            ]
        )

        employe_role, created = ZYRO.objects.get_or_create(
            CODE='EMPLOYE_STD',
            defaults={
                'LIBELLE': 'Employé standard',
                'DESCRIPTION': 'Peut déclarer et voir ses propres absences',
                'PERMISSIONS_CUSTOM': {
                    'can_create_absence': True,
                    'can_view_own_absences': True,
                },
                'actif': True
            }
        )

        django_group_employe, _ = Group.objects.get_or_create(name='EMPLOYE_STD')
        for perm in employe_permissions:
            django_group_employe.permissions.add(perm)

        if employe_role.django_group != django_group_employe:
            employe_role.django_group = django_group_employe
            employe_role.save()

        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Rôle EMPLOYE_STD créé'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Rôle EMPLOYE_STD mis à jour'))

        # ========================================
        # 5. Rôle "ASSISTANT_RH" - Consultation uniquement
        # ========================================
        self.stdout.write('📋 Création du rôle ASSISTANT_RH...')

        assistant_rh_permissions = absence_permissions.filter(
            codename__in=[
                'view_absence',
                'view_typeabsence',
                'view_acquisitionconges',
                'view_jourferie',
                'view_conventionconges',
            ]
        )

        assistant_rh_role, created = ZYRO.objects.get_or_create(
            CODE='ASSISTANT_RH',
            defaults={
                'LIBELLE': 'Assistant RH',
                'DESCRIPTION': 'Peut consulter toutes les absences sans pouvoir les valider',
                'PERMISSIONS_CUSTOM': {
                    'can_view_all_absences': True,
                    'can_view_employees': True,
                    'can_view_reports': True,
                },
                'actif': True
            }
        )

        django_group_assistant_rh, _ = Group.objects.get_or_create(name='ASSISTANT_RH')
        for perm in assistant_rh_permissions:
            django_group_assistant_rh.permissions.add(perm)

        if assistant_rh_role.django_group != django_group_assistant_rh:
            assistant_rh_role.django_group = django_group_assistant_rh
            assistant_rh_role.save()

        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Rôle ASSISTANT_RH créé'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Rôle ASSISTANT_RH mis à jour'))

        # ========================================
        # RÉSUMÉ
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n✅ === RÉSUMÉ DES RÔLES ==='))
        self.stdout.write(f'  • GESTION_APP: {gestion_app_permissions.count()} permissions')
        self.stdout.write(f'  • RH_VALIDATION_ABS: {rh_permissions.count()} permissions')
        self.stdout.write(f'  • MANAGER_ABS: {manager_permissions.count()} permissions')
        self.stdout.write(f'  • EMPLOYE_STD: {employe_permissions.count()} permissions')
        self.stdout.write(f'  • ASSISTANT_RH: {assistant_rh_permissions.count()} permissions')
        self.stdout.write(self.style.SUCCESS('\n🎉 Configuration des rôles terminée !'))