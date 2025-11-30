"""
Script d'installation rapide du système de rôles
À exécuter dans le shell Django après avoir ajouté les modèles
"""

from employee.models import ZYRO, ZYRE, ZY00
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

print("=" * 80)
print("INSTALLATION DU SYSTÈME DE RÔLES")
print("=" * 80)

# ============================================================================
# ÉTAPE 1 : CRÉER LES RÔLES DE BASE
# ============================================================================

print("\n1. Création des rôles de base...")

roles_a_creer = [
    {
        'CODE': 'DRH',
        'LIBELLE': 'Direction des Ressources Humaines',
        'DESCRIPTION': 'Accès complet à la gestion RH et validation finale des demandes d\'absence',
        'PERMISSIONS': {
            'can_validate_rh': True,
            'can_validate_manager': True,
            'can_manage_employees': True,
            'can_view_all_absences': True,
            'can_manage_roles': True,
            'can_view_payroll': True
        }
    },
    {
        'CODE': 'MANAGER',
        'LIBELLE': 'Manager de département',
        'DESCRIPTION': 'Validation des demandes d\'absence de son équipe',
        'PERMISSIONS': {
            'can_validate_manager': True,
            'can_view_team_absences': True,
            'can_manage_team': True
        }
    },
    {
        'CODE': 'COMPTABLE',
        'LIBELLE': 'Comptable',
        'DESCRIPTION': 'Accès à la comptabilité et à la paie',
        'PERMISSIONS': {
            'can_view_payroll': True,
            'can_manage_contracts': True,
            'can_view_reports': True
        }
    },
    {
        'CODE': 'DIRECTEUR',
        'LIBELLE': 'Directeur',
        'DESCRIPTION': 'Accès complet à toutes les fonctionnalités',
        'PERMISSIONS': {
            'can_validate_rh': True,
            'can_validate_manager': True,
            'can_manage_employees': True,
            'can_view_all_absences': True,
            'can_manage_roles': True,
            'can_view_payroll': True,
            'can_view_dashboard': True,
            'can_manage_company': True
        }
    },
    {
        'CODE': 'ASSISTANT_RH',
        'LIBELLE': 'Assistant RH',
        'DESCRIPTION': 'Accès en lecture à la gestion RH',
        'PERMISSIONS': {
            'can_view_all_absences': True,
            'can_view_employees': True
        }
    }
]

roles_crees = 0
for role_data in roles_a_creer:
    role, created = ZYRO.objects.get_or_create(
        CODE=role_data['CODE'],
        defaults={
            'LIBELLE': role_data['LIBELLE'],
            'DESCRIPTION': role_data['DESCRIPTION'],
            'PERMISSIONS': role_data['PERMISSIONS'],
            'actif': True
        }
    )
    if created:
        print(f"  ✅ Rôle créé: {role.CODE} - {role.LIBELLE}")
        roles_crees += 1
    else:
        print(f"  ℹ️  Rôle existe déjà: {role.CODE}")

print(f"\n✅ {roles_crees} nouveau(x) rôle(s) créé(s)")

# ============================================================================
# ÉTAPE 2 : ATTRIBUER LE RÔLE DRH
# ============================================================================

print("\n" + "=" * 80)
print("2. Attribution du rôle DRH")
print("=" * 80)

print("\nUtilisateurs disponibles:")
users = User.objects.all()[:20]
for i, u in enumerate(users, 1):
    try:
        employe_info = f" - {u.employe.nom} {u.employe.prenoms}" if hasattr(u, 'employe') and u.employe else ""
    except:
        employe_info = " (pas d'employé)"

    # Vérifier si a déjà le rôle DRH
    try:
        if u.employe and u.employe.has_role('DRH'):
            employe_info += " [✓ DRH]"
    except:
        pass

    print(f"{i}. {u.email} ({u.username}){employe_info}")

email = input("\nEmail de l'utilisateur à qui attribuer le rôle DRH : ")

try:
    user = User.objects.get(email=email)
    print(f"✅ Utilisateur trouvé: {user.username}")

    employe = user.employe
    print(f"✅ Employé: {employe.nom} {employe.prenoms}")

    # Vérifier si a déjà le rôle
    if employe.has_role('DRH'):
        print("⚠️  Cet employé a déjà le rôle DRH!")

        # Afficher les détails
        attribution = ZYRE.objects.filter(
            employe=employe,
            role__CODE='DRH',
            actif=True
        ).first()

        if attribution:
            print(f"   Date début: {attribution.date_debut}")
            print(f"   Date fin: {attribution.date_fin if attribution.date_fin else 'N/A'}")
    else:
        # Attribuer le rôle
        role_drh = ZYRO.objects.get(CODE='DRH')

        ZYRE.objects.create(
            employe=employe,
            role=role_drh,
            date_debut=date.today(),
            actif=True,
            commentaire='Attribution initiale via script d\'installation'
        )

        print(f"✅ Rôle DRH attribué à {employe.nom} {employe.prenoms}")

        # Vérifier
        if employe.has_role('DRH'):
            print("✅ Vérification OK: L'employé a bien le rôle DRH")

        # Afficher les permissions
        print("\nPermissions accordées:")
        role = ZYRO.objects.get(CODE='DRH')
        for perm, value in role.PERMISSIONS.items():
            if value:
                print(f"  ✓ {perm}")

except User.DoesNotExist:
    print(f"❌ Utilisateur '{email}' non trouvé")
except AttributeError:
    print("❌ Cet utilisateur n'a pas d'employé associé")
    print("Créez d'abord un employé et liez-le à cet utilisateur")
except Exception as e:
    print(f"❌ Erreur: {e}")

# ============================================================================
# RÉCAPITULATIF
# ============================================================================

print("\n" + "=" * 80)
print("RÉCAPITULATIF")
print("=" * 80)

print("\nRôles disponibles:")
for role in ZYRO.objects.filter(actif=True):
    nb_employes = ZYRE.objects.filter(
        role=role,
        actif=True,
        date_fin__isnull=True
    ).count()
    print(f"  - {role.CODE}: {role.LIBELLE} ({nb_employes} employé(s))")

print("\nAttributions actives:")
attributions = ZYRE.objects.filter(
    actif=True,
    date_fin__isnull=True
).select_related('employe', 'role')[:10]

if attributions:
    for attr in attributions:
        print(f"  - {attr.employe.nom} {attr.employe.prenoms}: {attr.role.CODE}")
else:
    print("  Aucune attribution active")

print("\n" + "=" * 80)
print("PROCHAINES ÉTAPES")
print("=" * 80)

print("""
1. Vérifier l'admin Django:
   → http://127.0.0.1:8000/admin/employee/zyro/
   → http://127.0.0.1:8000/admin/employee/zyre/

2. Tester l'accès RH:
   → Se déconnecter/reconnecter
   → Aller sur /absence/rh/validation/
   → ✅ La page doit s'afficher

3. Vérifier les notifications:
   → Le badge RH doit apparaître dans le header

4. Créer d'autres attributions si nécessaire:
   → Dans l'admin Django
   → Ou via le shell: employe.add_role('MANAGER')

5. Personnaliser les permissions:
   → Modifier ZYRO.PERMISSIONS dans l'admin
   → Ajouter vos propres permissions
""")

print("=" * 80)
print("✅ INSTALLATION TERMINÉE")
print("=" * 80)