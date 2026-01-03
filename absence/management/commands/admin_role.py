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
        'CODE': 'GESTION_APP',
        'LIBELLE': 'Gestionnaire Application',
        'DESCRIPTION': 'Accès complet au paramétrage de l\'application (absences, entreprise, types d\'absence, jours fériés, conventions)',
        'PERMISSIONS': {
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
        }
    },
    {
        'CODE': 'RH_VALIDATION_ABS',
        'LIBELLE': 'RH - Validation absences',
        'DESCRIPTION': 'Validation finale des absences au niveau RH',
        'PERMISSIONS': {
            'can_validate_rh': True,
            'can_view_all_absences': True,
            'absence.valider_absence_rh': True,
        }
    },
    {
        'CODE': 'MANAGER_ABS',
        'LIBELLE': 'Manager - Validation absences',
        'DESCRIPTION': 'Validation des absences de ses subordonnés (niveau 1)',
        'PERMISSIONS': {
            'can_validate_manager': True,
            'can_view_team_absences': True,
        }
    },
    {
        'CODE': 'EMPLOYE_STD',
        'LIBELLE': 'Employé standard',
        'DESCRIPTION': 'Peut déclarer et voir ses propres absences',
        'PERMISSIONS': {
            'can_create_absence': True,
            'can_view_own_absences': True,
        }
    },
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
            'can_view_payroll': True,
            'absence.valider_absence_rh': True,
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
roles_mis_a_jour = 0

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
        # Mettre à jour les permissions si le rôle existe déjà
        role.PERMISSIONS = role_data['PERMISSIONS']
        role.DESCRIPTION = role_data['DESCRIPTION']
        role.save()
        print(f"  🔄 Rôle mis à jour: {role.CODE}")
        roles_mis_a_jour += 1

print(f"\n✅ {roles_crees} nouveau(x) rôle(s) créé(s)")
print(f"🔄 {roles_mis_a_jour} rôle(s) mis à jour")

# ============================================================================
# ÉTAPE 2 : ATTRIBUER UN RÔLE PRINCIPAL
# ============================================================================

print("\n" + "=" * 80)
print("2. Attribution d'un rôle principal")
print("=" * 80)

print("\nRôles disponibles pour attribution:")
print("1. GESTION_APP - Gestionnaire Application (paramétrage complet)")
print("2. RH_VALIDATION_ABS - RH Validation absences")
print("3. MANAGER_ABS - Manager Validation absences")
print("4. EMPLOYE_STD - Employé standard")
print("5. DRH - Direction des Ressources Humaines")

choix_role = input("\nQuel rôle voulez-vous attribuer ? (1-5) : ")

role_map = {
    '1': 'GESTION_APP',
    '2': 'RH_VALIDATION_ABS',
    '3': 'MANAGER_ABS',
    '4': 'EMPLOYE_STD',
    '5': 'DRH'
}

role_code = role_map.get(choix_role)

if not role_code:
    print("❌ Choix invalide")
else:
    print(f"\n✅ Rôle sélectionné: {role_code}")

    print("\nUtilisateurs disponibles:")
    users = User.objects.all()[:20]
    for i, u in enumerate(users, 1):
        try:
            if hasattr(u, 'employe') and u.employe:
                employe_info = f" - {u.employe.nom} {u.employe.prenoms}"
            else:
                employe_info = " (pas d'employé)"
        except:
            employe_info = " (pas d'employé)"

        # Vérifier les rôles existants
        try:
            if hasattr(u, 'employe') and u.employe:
                roles_actuels = []
                for code in ['GESTION_APP', 'DRH', 'RH_VALIDATION_ABS', 'MANAGER_ABS', 'EMPLOYE_STD']:
                    if u.employe.has_role(code):
                        roles_actuels.append(code)
                if roles_actuels:
                    employe_info += f" [✓ {', '.join(roles_actuels)}]"
        except:
            pass

        print(f"{i}. {u.email} ({u.username}){employe_info}")

    email = input(f"\nEmail de l'utilisateur à qui attribuer le rôle {role_code} : ")

    try:
        user = User.objects.get(email=email)
        print(f"✅ Utilisateur trouvé: {user.username}")

        if not hasattr(user, 'employe') or not user.employe:
            print("❌ Cet utilisateur n'a pas d'employé associé")
            print("Créez d'abord un employé et liez-le à cet utilisateur")
        else:
            employe = user.employe
            print(f"✅ Employé: {employe.nom} {employe.prenoms}")

            # Vérifier si a déjà le rôle
            if employe.has_role(role_code):
                print(f"⚠️  Cet employé a déjà le rôle {role_code}!")

                # Afficher les détails
                attribution = ZYRE.objects.filter(
                    employe=employe,
                    role__CODE=role_code,
                    actif=True,
                    date_fin__isnull=True
                ).first()

                if attribution:
                    print(f"   Date début: {attribution.date_debut}")
                    print(f"   Date fin: {attribution.date_fin if attribution.date_fin else 'Pas de date de fin'}")
            else:
                # Attribuer le rôle
                role = ZYRO.objects.get(CODE=role_code)

                ZYRE.objects.create(
                    employe=employe,
                    role=role,
                    date_debut=date.today(),
                    actif=True,
                    commentaire=f'Attribution initiale via script d\'installation'
                )

                print(f"✅ Rôle {role_code} attribué à {employe.nom} {employe.prenoms}")

                # Vérifier
                if employe.has_role(role_code):
                    print(f"✅ Vérification OK: L'employé a bien le rôle {role_code}")

                # Afficher les permissions
                print("\n📋 Permissions accordées:")
                for perm, value in role.PERMISSIONS.items():
                    if value:
                        print(f"  ✓ {perm}")

    except User.DoesNotExist:
        print(f"❌ Utilisateur '{email}' non trouvé")
    except ZYRO.DoesNotExist:
        print(f"❌ Rôle '{role_code}' non trouvé dans la base")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback

        traceback.print_exc()

# ============================================================================
# RÉCAPITULATIF
# ============================================================================

print("\n" + "=" * 80)
print("RÉCAPITULATIF")
print("=" * 80)

print("\n📊 Rôles disponibles:")
for role in ZYRO.objects.filter(actif=True).order_by('CODE'):
    nb_employes = ZYRE.objects.filter(
        role=role,
        actif=True,
        date_fin__isnull=True
    ).count()
    print(f"  • {role.CODE}: {role.LIBELLE} ({nb_employes} employé(s))")

print("\n👥 Attributions actives:")
attributions = ZYRE.objects.filter(
    actif=True,
    date_fin__isnull=True
).select_related('employe', 'role').order_by('role__CODE', 'employe__nom')[:20]

if attributions:
    for attr in attributions:
        print(f"  • {attr.employe.nom} {attr.employe.prenoms}: {attr.role.CODE} ({attr.role.LIBELLE})")
else:
    print("  Aucune attribution active")

print("\n" + "=" * 80)
print("PROCHAINES ÉTAPES")
print("=" * 80)

print("""
1. 🔍 Vérifier l'admin Django:
   → http://127.0.0.1:8000/admin/employee/zyro/
   → http://127.0.0.1:8000/admin/employee/zyre/

2. 🧪 Tester les accès selon le rôle attribué:

   GESTION_APP:
   → Se déconnecter/reconnecter
   → Accéder aux paramètres (types d'absence, jours fériés, etc.)
   → ✅ Tous les menus de paramétrage doivent être visibles

   RH_VALIDATION_ABS:
   → Se déconnecter/reconnecter
   → Aller sur /absence/validation-rh/
   → ✅ La page de validation RH doit s'afficher

   MANAGER_ABS:
   → Se déconnecter/reconnecter
   → Aller sur /absence/validation-manager/
   → ✅ La page de validation manager doit s'afficher

   EMPLOYE_STD:
   → Se déconnecter/reconnecter
   → Aller sur /absence/
   → ✅ Créer une demande d'absence

3. 🔔 Vérifier les notifications:
   → Le badge correspondant au rôle doit apparaître
   → Les notifications doivent rediriger correctement selon le contexte

4. ➕ Créer d'autres attributions si nécessaire:
   → Dans l'admin Django
   → Ou via le shell Python: 

     from employee.models import ZY00, ZYRO, ZYRE
     from datetime import date

     employe = ZY00.objects.get(matricule='MT000001')
     role = ZYRO.objects.get(CODE='GESTION_APP')

     ZYRE.objects.create(
         employe=employe,
         role=role,
         date_debut=date.today(),
         actif=True
     )

5. ⚙️ Personnaliser les permissions:
   → Modifier ZYRO.PERMISSIONS dans l'admin
   → Ajouter vos propres permissions personnalisées

6. 🔗 Tester le cumul de rôles:
   → Un employé peut avoir plusieurs rôles simultanément
   → Exemple: EMPLOYE_STD + MANAGER_ABS + RH_VALIDATION_ABS
   → Le système gérera automatiquement les redirections
   → Chaque rôle générera des notifications avec son propre contexte
""")

print("\n" + "=" * 80)
print("📚 RÔLES SPÉCIFIQUES AU MODULE ABSENCE")
print("=" * 80)

print("""
Le système de gestion des absences utilise 4 rôles principaux:

1. 🔧 GESTION_APP (Gestionnaire Application)
   ✓ Paramétrage complet de l'application
   ✓ Configuration des types d'absence
   ✓ Gestion des jours fériés
   ✓ Configuration des conventions de congés
   ✓ Paramètres de calcul
   ✓ Paramètres de l'entreprise
   → Accès: Menus Paramètres (types, jours fériés, conventions, etc.)

2. 🛡️ RH_VALIDATION_ABS (RH Validation)
   ✓ Validation finale des absences (niveau 2)
   ✓ Consultation de toutes les absences de l'entreprise
   ✓ Export des données d'absence
   ✓ Consultation des acquisitions de congés
   → Accès: /absence/validation-rh/

3. 👔 MANAGER_ABS (Manager Validation)
   ✓ Validation des absences de l'équipe (niveau 1)
   ✓ Consultation des absences du département
   ✓ Gestion de son équipe
   → Accès: /absence/validation-manager/

4. 👤 EMPLOYE_STD (Employé Standard)
   ✓ Création de demandes d'absence
   ✓ Consultation de ses propres absences
   ✓ Modification de ses absences (brouillon)
   ✓ Annulation de ses demandes
   → Accès: /absence/

📋 Workflow typique:

  Employé (EMPLOYE_STD)
    ↓ Crée demande
  Manager (MANAGER_ABS)
    ↓ Valide niveau 1
  RH (RH_VALIDATION_ABS)
    ↓ Valide niveau 2
  ✅ Confirmé

🔔 Système de notifications:
  • Chaque action génère des notifications contextuelles
  • Un employé avec plusieurs rôles reçoit plusieurs notifications
  • Chaque notification redirige vers la page appropriée

⚡ Pour créer tous ces rôles avec les permissions Django:
  → python manage.py create_absence_roles
""")

print("=" * 80)
print("✅ INSTALLATION TERMINÉE AVEC SUCCÈS")
print("=" * 80)