# python manage.py shell
#python manage.py shell < scripts/init_permissions.py
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from employee.models import ZYRO, ZYRE, ZY00, ZYNP, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA, ZYPP, ZYIB
from departement.models import ZDDE, ZDPO, ZYMA

print("=" * 80)
print("🚀 INITIALISATION DU SYSTÈME HYBRIDE DE PERMISSIONS")
print("=" * 80)

# ========================================
# 1. CRÉER LES GROUPES DJANGO
# ========================================
print("\n📦 Étape 1 : Création des groupes Django...")

# Groupe DRH
group_drh, created = Group.objects.get_or_create(name='ROLE_DRH')
if created:
    print("✅ Groupe ROLE_DRH créé")
else:
    print("ℹ️ Groupe ROLE_DRH existe déjà")

# Groupe MANAGER
group_manager, created = Group.objects.get_or_create(name='ROLE_MANAGER')
if created:
    print("✅ Groupe ROLE_MANAGER créé")
else:
    print("ℹ️ Groupe ROLE_MANAGER existe déjà")

# Groupe COMPTABLE
group_comptable, created = Group.objects.get_or_create(name='ROLE_COMPTABLE')
if created:
    print("✅ Groupe ROLE_COMPTABLE créé")
else:
    print("ℹ️ Groupe ROLE_COMPTABLE existe déjà")

# Groupe EMPLOYE
group_employe, created = Group.objects.get_or_create(name='ROLE_EMPLOYE')
if created:
    print("✅ Groupe ROLE_EMPLOYE créé")
else:
    print("ℹ️ Groupe ROLE_EMPLOYE existe déjà")

# ========================================
# 2. ASSIGNER LES PERMISSIONS DJANGO AUX GROUPES
# ========================================
print("\n🔑 Étape 2 : Attribution des permissions Django aux groupes...")

# ========== PERMISSIONS DRH ==========
print("\n📋 Configuration du groupe DRH...")

permissions_drh = []

# Employés (ZY00) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zy00',
    codename__in=['add_zy00', 'change_zy00', 'delete_zy00', 'view_zy00']
))

# Départements (ZDDE) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='departement',
    content_type__model='zdde',
    codename__in=['add_zdde', 'change_zdde', 'delete_zdde', 'view_zdde']
))

# Postes (ZDPO) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='departement',
    content_type__model='zdpo',
    codename__in=['add_zdpo', 'change_zdpo', 'delete_zdpo', 'view_zdpo']
))

# Managers (ZYMA) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='departement',
    content_type__model='zyma',
    codename__in=['add_zyma', 'change_zyma', 'delete_zyma', 'view_zyma']
))

# Types absence (ZDAB) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='parametres',
    content_type__model='zdab',
    codename__in=['add_zdab', 'change_zdab', 'delete_zdab', 'view_zdab']
))

# Contrats (ZYCO) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyco',
    codename__in=['add_zyco', 'change_zyco', 'delete_zyco', 'view_zyco']
))

# Téléphones (ZYTE) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyte',
    codename__in=['add_zyte', 'change_zyte', 'delete_zyte', 'view_zyte']
))

# Emails (ZYME) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyme',
    codename__in=['add_zyme', 'change_zyme', 'delete_zyme', 'view_zyme']
))

# Affectations (ZYAF) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyaf',
    codename__in=['add_zyaf', 'change_zyaf', 'delete_zyaf', 'view_zyaf']
))

# Adresses (ZYAD) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyad',
    codename__in=['add_zyad', 'change_zyad', 'delete_zyad', 'view_zyad']
))

# Documents (ZYDO) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zydo',
    codename__in=['add_zydo', 'change_zydo', 'delete_zydo', 'view_zydo']
))

# Famille (ZYFA) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyfa',
    codename__in=['add_zyfa', 'change_zyfa', 'delete_zyfa', 'view_zyfa']
))

# Personnes à prévenir (ZYPP) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zypp',
    codename__in=['add_zypp', 'change_zypp', 'delete_zypp', 'view_zypp']
))

# Identités bancaires (ZYIB) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyib',
    codename__in=['add_zyib', 'change_zyib', 'delete_zyib', 'view_zyib']
))

# Historique noms/prénoms (ZYNP) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zynp',
    codename__in=['add_zynp', 'change_zynp', 'delete_zynp', 'view_zynp']
))

# Rôles (ZYRO, ZYRE) - CRUD complet
permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyro',
    codename__in=['add_zyro', 'change_zyro', 'delete_zyro', 'view_zyro', 'manage_roles', 'assign_roles', 'view_all_roles']
))

permissions_drh.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyre',
    codename__in=['add_zyre', 'change_zyre', 'delete_zyre', 'view_zyre']
))

group_drh.permissions.set(permissions_drh)
print(f"✅ {len(permissions_drh)} permissions assignées au groupe DRH")

# ========== PERMISSIONS MANAGER ==========
print("\n📋 Configuration du groupe MANAGER...")

permissions_manager = []


# Employés - Lecture uniquement
permissions_manager.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zy00',
    codename='view_zy00'
))

# Départements - Lecture uniquement
permissions_manager.extend(Permission.objects.filter(
    content_type__app_label='departement',
    content_type__model='zdde',
    codename='view_zdde'
))

# Postes - Lecture uniquement
permissions_manager.extend(Permission.objects.filter(
    content_type__app_label='departement',
    content_type__model='zdpo',
    codename='view_zdpo'
))

group_manager.permissions.set(permissions_manager)
print(f"✅ {len(permissions_manager)} permissions assignées au groupe MANAGER")

# ========== PERMISSIONS COMPTABLE ==========
print("\n📋 Configuration du groupe COMPTABLE...")

permissions_comptable = []

# Employés - Lecture uniquement
permissions_comptable.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zy00',
    codename='view_zy00'
))

# Identités bancaires - Lecture uniquement
permissions_comptable.extend(Permission.objects.filter(
    content_type__app_label='employee',
    content_type__model='zyib',
    codename='view_zyib'
))

group_comptable.permissions.set(permissions_comptable)
print(f"✅ {len(permissions_comptable)} permissions assignées au groupe COMPTABLE")

# ========== PERMISSIONS EMPLOYE ==========
print("\n📋 Configuration du groupe EMPLOYE...")

permissions_employe = []

group_employe.permissions.set(permissions_employe)
print(f"✅ {len(permissions_employe)} permissions assignées au groupe EMPLOYE")

# ========================================
# 3. CRÉER/METTRE À JOUR LES RÔLES ZYRO
# ========================================
print("\n🎭 Étape 3 : Création/mise à jour des rôles ZYRO...")

# ========== RÔLE DRH ==========
role_drh, created = ZYRO.objects.update_or_create(
    CODE='DRH',
    defaults={
        'LIBELLE': 'Directeur des Ressources Humaines',
        'DESCRIPTION': 'Accès complet à la gestion RH et toutes les fonctionnalités',
        'django_group': group_drh,
        'PERMISSIONS_CUSTOM': {
            # Permissions métier spécifiques
            'can_validate_rh': True,
            'can_override_manager_decision': True,
            'can_access_confidential_reports': True,
            'can_adjust_balances': True,
            'can_manage_company_policies': True,
            'can_export_all_data': True,
            'can_access_salary_data': True,
        },
        'actif': True,
    }
)
print(f"{'✅ Rôle DRH créé' if created else 'ℹ️ Rôle DRH mis à jour'}")

# ========== RÔLE MANAGER ==========
role_manager, created = ZYRO.objects.update_or_create(
    CODE='MANAGER',
    defaults={
        'LIBELLE': 'Manager',
        'DESCRIPTION': 'Responsable d\'équipe avec validation des absences',
        'django_group': group_manager,
        'PERMISSIONS_CUSTOM': {
            # Permissions métier spécifiques
            'can_validate_manager': True,
            'can_view_team_absences': True,
            'can_view_team_performance': True,
            'can_submit_team_reports': True,
        },
        'actif': True,
    }
)
print(f"{'✅ Rôle MANAGER créé' if created else 'ℹ️ Rôle MANAGER mis à jour'}")

# ========== RÔLE COMPTABLE ==========
role_comptable, created = ZYRO.objects.update_or_create(
    CODE='COMPTABLE',
    defaults={
        'LIBELLE': 'Comptable',
        'DESCRIPTION': 'Accès lecture et export des données financières',
        'django_group': group_comptable,
        'PERMISSIONS_CUSTOM': {
            # Permissions métier spécifiques
            'can_export_financial_data': True,
            'can_generate_reports': True,
            'can_view_bank_details': True,
        },
        'actif': True,
    }
)
print(f"{'✅ Rôle COMPTABLE créé' if created else 'ℹ️ Rôle COMPTABLE mis à jour'}")

# ========== RÔLE EMPLOYE ==========
role_employe, created = ZYRO.objects.update_or_create(
    CODE='EMPLOYE',
    defaults={
        'LIBELLE': 'Employé',
        'DESCRIPTION': 'Employé standard avec accès de base',
        'django_group': group_employe,
        'PERMISSIONS_CUSTOM': {
            # Permissions métier spécifiques
            'can_request_absence': True,
            'can_view_own_data': True,
            'can_update_own_profile': True,
        },
        'actif': True,
    }
)
print(f"{'✅ Rôle EMPLOYE créé' if created else 'ℹ️ Rôle EMPLOYE mis à jour'}")

# ========================================
# 4. SYNCHRONISER LES UTILISATEURS EXISTANTS
# ========================================
print("\n👥 Étape 4 : Synchronisation des utilisateurs avec les groupes Django...")

attributions_actives = ZYRE.objects.filter(
    actif=True,
    date_fin__isnull=True
).select_related('employe__user', 'role__django_group')

count_synced = 0
count_no_user = 0

for attribution in attributions_actives:
    if attribution.employe.user and attribution.role.django_group:
        attribution.employe.user.groups.add(attribution.role.django_group)
        count_synced += 1
        print(f"   ✓ {attribution.employe.nom} {attribution.employe.prenoms} → {attribution.role.django_group.name}")
    elif not attribution.employe.user:
        count_no_user += 1
        print(f"   ⚠️ {attribution.employe.nom} {attribution.employe.prenoms} n'a pas de compte utilisateur")

print(f"\n✅ {count_synced} utilisateur(s) synchronisé(s)")
if count_no_user > 0:
    print(f"⚠️ {count_no_user} employé(s) sans compte utilisateur")

# ========================================
# 5. RÉSUMÉ
# ========================================
print("\n" + "=" * 80)
print("🎉 INITIALISATION TERMINÉE")
print("=" * 80)

print("\n📊 RÉSUMÉ :")
print(f"  - Groupes Django créés/mis à jour : 4 (DRH, MANAGER, COMPTABLE, EMPLOYE)")
print(f"  - Rôles ZYRO créés/mis à jour : 4")
print(f"  - Permissions DRH : {len(permissions_drh)}")
print(f"  - Permissions MANAGER : {len(permissions_manager)}")
print(f"  - Permissions COMPTABLE : {len(permissions_comptable)}")
print(f"  - Permissions EMPLOYE : {len(permissions_employe)}")
print(f"  - Utilisateurs synchronisés : {count_synced}")

print("\n✅ Système de permissions hybride opérationnel !")
print("\n💡 Prochaines étapes :")
print("  1. Créer les migrations : python manage.py makemigrations")
print("  2. Appliquer les migrations : python manage.py migrate")
print("  3. Tester les permissions dans vos vues")