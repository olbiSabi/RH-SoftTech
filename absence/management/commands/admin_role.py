"""
Script d'installation rapide du système de rôles
À exécuter dans le shell Django après avoir ajouté les modèles

1. Créer uniquement les rôles (sans interaction) :
python manage.py setup_roles --auto

2. Attribuer un rôle spécifique :
python manage.py setup_roles --role DAF --email utilisateur@exemple.com

3. Mode interactif complet :
python manage.py setup_roles
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
        'DESCRIPTION': 'Accès complet au paramétrage de l\'application (absences, entreprise, types d\'absence, jours fériés, conventions, temps et activités)',
        'PERMISSIONS_CUSTOM': {
            # Absences
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
            # Gestion Temps et Activités - ACCÈS COMPLET
            'can_view_all_imputations': True,
            'can_validate_imputations': True,
            'can_manage_projets': True,
            'can_manage_clients': True,
            'can_manage_activites': True,
            'can_manage_taches': True,
            'can_view_all_projets': True,
            # Module Matériel - ACCÈS COMPLET
            'can_manage_materiel': True,
            'can_affecter_materiel': True,
            'can_manage_maintenances': True,
            'can_manage_categories_materiel': True,
            'can_manage_fournisseurs': True,
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
        'DESCRIPTION': 'Validation des absences de ses subordonnés (niveau 1)',
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
            # Gestion Temps et Activités - Employé standard
            'can_create_imputation': True,
            'can_view_own_imputations': True,
        }
    },
    {
        'CODE': 'DRH',
        'LIBELLE': 'Direction des Ressources Humaines',
        'DESCRIPTION': 'Accès complet à la gestion RH, validation finale des demandes d\'absence et accès total à la gestion des temps',
        'PERMISSIONS_CUSTOM': {
            # Absences
            'can_validate_rh': True,
            'can_validate_manager': True,
            'can_manage_employees': True,
            'can_view_all_absences': True,
            'can_manage_roles': True,
            'can_view_payroll': True,
            'absence.valider_absence_rh': True,
            # Gestion Temps et Activités - ACCÈS COMPLET
            'can_view_all_imputations': True,
            'can_validate_imputations': True,
            'can_manage_projets': True,
            'can_manage_clients': True,
            'can_manage_activites': True,
            'can_manage_taches': True,
            'can_view_all_projets': True,
            # Module Matériel - ACCÈS COMPLET
            'can_manage_materiel': True,
            'can_affecter_materiel': True,
            'can_manage_maintenances': True,
            'can_manage_categories_materiel': True,
            'can_manage_fournisseurs': True,
        }
    },
    {
        'CODE': 'MANAGER',
        'LIBELLE': 'Manager de département',
        'DESCRIPTION': 'Validation des demandes d\'absence de son équipe et validation des imputations de temps',
        'PERMISSIONS_CUSTOM': {
            # Absences
            'can_validate_manager': True,
            'can_view_team_absences': True,
            'can_manage_team': True,
            # Gestion Temps et Activités - Manager
            'can_validate_imputations': True,
            'can_view_team_imputations': True,
            'can_manage_projets': True,
            'can_view_all_projets': True,
        }
    },
    {
        'CODE': 'COMPTABLE',
        'LIBELLE': 'Comptable',
        'DESCRIPTION': 'Accès à la comptabilité, à la paie et aux imputations facturables',
        'PERMISSIONS_CUSTOM': {
            'can_view_payroll': True,
            'can_manage_contracts': True,
            'can_view_reports': True,
            # Gestion Temps et Activités - Comptable
            'can_view_all_imputations': True,
            'can_view_facturables': True,
        }
    },
    {
        'CODE': 'DIRECTEUR',
        'LIBELLE': 'Directeur / Président',
        'DESCRIPTION': 'Accès complet à toutes les fonctionnalités',
        'PERMISSIONS_CUSTOM': {
            # Absences
            'can_validate_rh': True,
            'can_validate_manager': True,
            'can_manage_employees': True,
            'can_view_all_absences': True,
            'can_manage_roles': True,
            'can_view_payroll': True,
            'can_view_dashboard': True,
            'can_manage_company': True,
            # Gestion Temps et Activités - ACCÈS COMPLET
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
        'DESCRIPTION': 'Accès en lecture à la gestion RH et aux imputations',
        'PERMISSIONS_CUSTOM': {
            'can_view_all_absences': True,
            'can_view_employees': True,
            # Gestion Temps et Activités - Lecture seule
            'can_view_all_imputations': True,
            # Module Matériel - Affectation uniquement
            'can_affecter_materiel': True,
            'can_view_materiel': True,
        }
    },
    {
        'CODE': 'RESP_ADMIN',
        'LIBELLE': 'Responsable Administratif',
        'DESCRIPTION': 'Responsable de la gestion administrative incluant le matériel et les fournitures',
        'PERMISSIONS_CUSTOM': {
            'can_view_employees': True,
            # Module Matériel - ACCÈS COMPLET
            'can_manage_materiel': True,
            'can_affecter_materiel': True,
            'can_manage_maintenances': True,
            'can_manage_categories_materiel': True,
            'can_manage_fournisseurs': True,
        }
    },
    {
        'CODE': 'DAF',
        'LIBELLE': 'Directeur Administratif et Financier',
        'DESCRIPTION': 'Accès complet à la gestion financière, comptable et administrative',
        'PERMISSIONS_CUSTOM': {
            # Absences - Accès financier
            'can_view_all_absences': True,
            'can_view_payroll': True,
            'can_view_reports': True,
            # Gestion Temps et Activités - Accès complet pour facturation
            'can_view_all_imputations': True,
            'can_view_facturables': True,
            'can_validate_imputations': True,
            'can_manage_projets': True,
            'can_manage_clients': True,
            'can_view_all_projets': True,
            # Permissions financières spécifiques
            'can_manage_contracts': True,
            'can_view_financial_reports': True,
            'can_validate_timesheets': True,
            # Module Notes de Frais - Accès complet DAF
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
        print(f"  ✅ Rôle créé: {role.CODE} - {role.LIBELLE}")
        roles_crees += 1
    else:
        # Mettre à jour les permissions si le rôle existe déjà
        role.PERMISSIONS_CUSTOM = role_data['PERMISSIONS_CUSTOM']
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
print("6. MANAGER - Manager de département")
print("7. DIRECTEUR - Directeur/Président")
print("8. DAF - Directeur Administratif et Financier")
print("9. RESP_ADMIN - Responsable Administratif (gestion matériel)")

choix_role = input("\nQuel rôle voulez-vous attribuer ? (1-9) : ")

role_map = {
    '1': 'GESTION_APP',
    '2': 'RH_VALIDATION_ABS',
    '3': 'MANAGER_ABS',
    '4': 'EMPLOYE_STD',
    '5': 'DRH',
    '6': 'MANAGER',
    '7': 'DIRECTEUR',
    '8': 'DAF',
    '9': 'RESP_ADMIN'
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
                for code in ['GESTION_APP', 'DRH', 'RH_VALIDATION_ABS', 'MANAGER_ABS', 'EMPLOYE_STD', 'MANAGER', 'DIRECTEUR', 'DAF', 'RESP_ADMIN']:
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
                for perm, value in role.PERMISSIONS_CUSTOM.items():
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
print("📚 PERMISSIONS GESTION TEMPS ET ACTIVITÉS")
print("=" * 80)

print("""
🎯 ACCÈS PAR RÔLE:

1. 👔 MANAGER (Manager de département)
   ✓ Validation des imputations de temps de son équipe
   ✓ Gestion des projets
   ✓ Consultation de tous les projets
   → Accès: /gestion-temps/imputations/validation/
   → Accès: /gestion-temps/projets/

2. 🛡️ DRH (Direction des Ressources Humaines)
   ✓ ACCÈS COMPLET à toutes les fonctionnalités
   ✓ Validation des imputations
   ✓ Gestion projets, clients, activités, tâches
   → Accès: Tous les menus

4. 🔧 GESTION_APP (Gestionnaire Application)
   ✓ ACCÈS COMPLET à toutes les fonctionnalités
   → Accès: Tous les menus

5. 🏢 DIRECTEUR (Président / Directeur)
   ✓ ACCÈS COMPLET à toutes les fonctionnalités
   → Accès: Tous les menus

6. 💼 DAF (Directeur Administratif et Financier)
   ✓ Accès complet à la gestion financière et comptable
   ✓ Validation des imputations pour facturation
   ✓ Gestion des projets et clients
   ✓ Accès aux rapports financiers
   ✓ Validation des notes de frais et approbation des avances
   → Accès: Menus financiers, projets, imputations, notes de frais

7. 👤 EMPLOYE_STD (Employé Standard)
   ✓ Création de ses imputations de temps
   ✓ Consultation de ses propres imputations
   → Accès: /gestion-temps/imputations/mes-temps/

8. 💰 COMPTABLE
   ✓ Consultation de toutes les imputations (facturation)
   ✓ Consultation des imputations facturables
   → Accès: /gestion-temps/imputations/ (lecture)

9. 📋 ASSISTANT_RH
   ✓ Consultation de toutes les imputations (lecture seule)
   ✓ Affectation de matériel aux employés
   → Accès: /gestion-temps/imputations/ (lecture)
   → Accès: /materiel/ (affectation uniquement)

10. 🏢 RESP_ADMIN (Responsable Administratif)
   ✓ Gestion complète du parc matériel
   ✓ Affectation de matériel
   ✓ Gestion des maintenances
   ✓ Gestion des catégories et fournisseurs
   → Accès: /materiel/ (complet)
""")

print("=" * 80)
print("📦 PERMISSIONS MODULE MATÉRIEL")
print("=" * 80)

print("""
🎯 ACCÈS PAR RÔLE AU MODULE MATÉRIEL:

1. 🔧 GESTION_APP / 🛡️ DRH / 🏢 RESP_ADMIN
   ✓ Gestion complète du parc matériel (création, modification, réforme)
   ✓ Affectation de matériel aux employés
   ✓ Gestion des maintenances (planification, suivi, coûts)
   ✓ Gestion des catégories de matériel
   ✓ Gestion des fournisseurs
   → Accès: /materiel/ (complet)

2. 📋 ASSISTANT_RH
   ✓ Affectation de matériel aux employés
   ✓ Consultation du parc matériel
   → Accès: /materiel/ (affectation uniquement)

3. 👤 TOUS LES EMPLOYÉS
   ✓ Consultation de son propre matériel affecté
   → Accès: /materiel/mon-materiel/
""")

print("=" * 80)
print("✅ INSTALLATION TERMINÉE AVEC SUCCÈS")
print("=" * 80)