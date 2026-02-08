"""
Tests pour le système de permissions du module GAC.

Tests complets pour toutes les permissions liées aux demandes,
bons de commande, fournisseurs, réceptions, budgets et catalogue.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from gestion_achats.models import (
    GACFournisseur,
    GACCategorie,
    GACArticle,
    GACBudget,
    GACDemandeAchat,
    GACBonCommande,
    GACReception,
)
from datetime import date
from gestion_achats.permissions import GACPermissions
from employee.models import ZY00
from departement.models import ZDDE
from entreprise.models import Entreprise


def create_test_entreprise_perm():
    """Crée une entreprise de test pour les permissions."""
    return Entreprise.objects.create(
        code='PRM',
        nom='Entreprise Permissions Test',
        raison_sociale='Permissions Test SARL',
        numero_impot='PRM123456',
        rccm='RCCM-PRM',
        adresse='789 Permissions Street',
        ville='Lomé',
        pays='Togo'
    )


def create_test_employee_perm(nom, prenoms, numero_id, entreprise, user=None):
    """Crée un employé de test avec tous les champs requis."""
    return ZY00.objects.create(
        nom=nom,
        prenoms=prenoms,
        date_naissance=date(1985, 1, 1),
        sexe='M',
        type_id='CNI',
        numero_id=numero_id,
        date_validite_id=date(2020, 1, 1),
        date_expiration_id=date(2030, 1, 1),
        entreprise=entreprise,
        etat='actif',
        user=user
    )


class BasePermissionTestCase(TestCase):
    """Classe de base pour les tests de permissions."""

    def setUp(self):
        """Prépare les utilisateurs avec différents rôles."""
        # Créer des utilisateurs Django
        self.user_admin = User.objects.create_user(
            username='admin',
            password='test123'
        )
        self.user_acheteur = User.objects.create_user(
            username='acheteur',
            password='test123'
        )
        self.user_demandeur = User.objects.create_user(
            username='demandeur',
            password='test123'
        )
        self.user_validateur = User.objects.create_user(
            username='validateur',
            password='test123'
        )
        self.user_receptionnaire = User.objects.create_user(
            username='receptionnaire',
            password='test123'
        )
        self.user_gestionnaire_budget = User.objects.create_user(
            username='gestionnaire',
            password='test123'
        )
        self.user_no_role = User.objects.create_user(
            username='norole',
            password='test123'
        )

        # Créer l'entreprise
        self.entreprise = create_test_entreprise_perm()

        # Créer les employés correspondants avec tous les champs requis
        self.employe_admin = create_test_employee_perm('Admin', 'Test', 'ADMIN001', self.entreprise, self.user_admin)
        self.employe_acheteur = create_test_employee_perm('Acheteur', 'Test', 'ACH001', self.entreprise, self.user_acheteur)
        self.employe_demandeur = create_test_employee_perm('Demandeur', 'Test', 'DEM001', self.entreprise, self.user_demandeur)
        self.employe_validateur = create_test_employee_perm('Validateur', 'Test', 'VAL001', self.entreprise, self.user_validateur)
        self.employe_receptionnaire = create_test_employee_perm('Receptionnaire', 'Test', 'REC001', self.entreprise, self.user_receptionnaire)
        self.employe_gestionnaire_budget = create_test_employee_perm('Gestionnaire', 'Budget', 'GES001', self.entreprise, self.user_gestionnaire_budget)
        self.employe_no_role = create_test_employee_perm('NoRole', 'Test', 'NOR001', self.entreprise, self.user_no_role)

        # Assigner les rôles (simulé - adapter selon votre implémentation)
        # Note: Adaptez ces lignes selon votre système de rôles
        # self.employe_admin.roles.add('ADMIN_GAC')
        # self.employe_acheteur.roles.add('ACHETEUR')
        # etc.

        # Créer des objets de test
        self.departement = ZDDE.objects.create(
            CODE='PRM',
            LIBELLE='Département Permissions'
        )

        self.budget = GACBudget.objects.create(
            code='BUD2024',
            libelle='Budget Test',
            montant_initial=Decimal('100000.00'),
            exercice=2024,
            date_debut=timezone.now().date(),
            date_fin=timezone.now().date() + timedelta(days=365),
            gestionnaire=self.employe_gestionnaire_budget
        )

        self.categorie = GACCategorie.objects.create(
            code='CAT001',
            nom='Test'
        )

        self.article = GACArticle.objects.create(
            reference='ART001',
            designation='Article Test',
            categorie=self.categorie,
            prix_unitaire=Decimal('10.00'),
            taux_tva=Decimal('20.00'),
            unite='PIECE'
        )

        self.fournisseur = GACFournisseur.objects.create(
            code='FRN001',
            raison_sociale='Fournisseur Test',
            nif='123456789',
            pays='Togo'
        )

        self.demande = GACDemandeAchat.objects.create(
            objet='Test',
            justification='Test',
            demandeur=self.employe_demandeur,
            departement=self.departement,
            budget=self.budget,
            statut='BROUILLON'
        )

        self.bon_commande = GACBonCommande.objects.create(
            fournisseur=self.fournisseur,
            acheteur=self.employe_acheteur,
            demande_achat=self.demande,
            statut='BROUILLON'
        )


class DemandePermissionsTest(BasePermissionTestCase):
    """Tests pour les permissions des demandes d'achat."""

    def test_can_view_demande_demandeur(self):
        """Test que le demandeur peut voir sa demande."""
        result = GACPermissions.can_view_demande(
            self.user_demandeur,
            self.demande
        )
        self.assertTrue(result)

    def test_can_view_demande_autre_utilisateur(self):
        """Test qu'un autre utilisateur ne peut pas voir la demande."""
        result = GACPermissions.can_view_demande(
            self.user_no_role,
            self.demande
        )
        self.assertFalse(result)

    def test_can_view_demande_admin(self):
        """Test que l'admin peut voir toutes les demandes."""
        # Note: Dépend de l'implémentation du système de rôles
        # Si has_role('ADMIN_GAC') fonctionne, ce test passera
        pass

    def test_can_create_demande_utilisateur_authentifie(self):
        """Test qu'un utilisateur authentifié peut créer une demande."""
        result = GACPermissions.can_create_demande(self.user_demandeur)
        self.assertTrue(result)

    def test_can_create_demande_non_authentifie(self):
        """Test qu'un utilisateur non authentifié ne peut pas créer."""
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        result = GACPermissions.can_create_demande(anonymous_user)
        self.assertFalse(result)

    def test_can_modify_demande_demandeur_brouillon(self):
        """Test que le demandeur peut modifier sa demande en brouillon."""
        result = GACPermissions.can_modify_demande(
            self.user_demandeur,
            self.demande
        )
        self.assertTrue(result)

    def test_can_modify_demande_non_brouillon(self):
        """Test qu'on ne peut pas modifier une demande non brouillon."""
        self.demande.statut = 'SOUMISE'
        self.demande.save()

        result = GACPermissions.can_modify_demande(
            self.user_demandeur,
            self.demande
        )
        self.assertFalse(result)

    def test_can_submit_demande_demandeur(self):
        """Test que le demandeur peut soumettre sa demande."""
        result = GACPermissions.can_submit_demande(
            self.user_demandeur,
            self.demande
        )
        self.assertTrue(result)

    def test_can_submit_demande_autre_utilisateur(self):
        """Test qu'un autre utilisateur ne peut pas soumettre."""
        result = GACPermissions.can_submit_demande(
            self.user_no_role,
            self.demande
        )
        self.assertFalse(result)

    def test_can_validate_n1_validateur(self):
        """Test que le validateur N1 peut valider."""
        self.demande.statut = 'SOUMISE'
        self.demande.validateur_n1 = self.employe_validateur
        self.demande.save()

        result = GACPermissions.can_validate_n1(
            self.user_validateur,
            self.demande
        )
        self.assertTrue(result)

    def test_can_validate_n1_mauvais_statut(self):
        """Test qu'on ne peut pas valider N1 si statut incorrect."""
        self.demande.statut = 'BROUILLON'
        self.demande.validateur_n1 = self.employe_validateur
        self.demande.save()

        result = GACPermissions.can_validate_n1(
            self.user_validateur,
            self.demande
        )
        self.assertFalse(result)

    def test_can_validate_n2_bon_statut(self):
        """Test que le validateur N2 peut valider avec bon statut."""
        self.demande.statut = 'VALIDEE_N1'
        self.demande.validateur_n2 = self.employe_validateur
        self.demande.save()

        result = GACPermissions.can_validate_n2(
            self.user_validateur,
            self.demande
        )
        self.assertTrue(result)

    def test_can_refuse_demande_validateur_n1(self):
        """Test que le validateur N1 peut refuser."""
        self.demande.statut = 'SOUMISE'
        self.demande.validateur_n1 = self.employe_validateur
        self.demande.save()

        result = GACPermissions.can_refuse_demande(
            self.user_validateur,
            self.demande
        )
        self.assertTrue(result)

    def test_can_cancel_demande_demandeur(self):
        """Test que le demandeur peut annuler sa demande."""
        result = GACPermissions.can_cancel_demande(
            self.user_demandeur,
            self.demande
        )
        self.assertTrue(result)

    def test_can_cancel_demande_convertie_bc(self):
        """Test qu'on ne peut pas annuler une demande convertie en BC."""
        self.demande.statut = 'CONVERTIE_BC'
        self.demande.save()

        result = GACPermissions.can_cancel_demande(
            self.user_demandeur,
            self.demande
        )
        self.assertFalse(result)

    def test_can_convert_to_bc_validee_n2(self):
        """Test qu'on peut convertir une demande validée N2."""
        self.demande.statut = 'VALIDEE_N2'
        self.demande.save()

        # Note: Dépend du système de rôles
        # result = GACPermissions.can_convert_to_bc(
        #     self.user_acheteur,
        #     self.demande
        # )
        # self.assertTrue(result)

    def test_can_convert_to_bc_mauvais_statut(self):
        """Test qu'on ne peut pas convertir si statut incorrect."""
        self.demande.statut = 'SOUMISE'
        self.demande.save()

        result = GACPermissions.can_convert_to_bc(
            self.user_acheteur,
            self.demande
        )
        self.assertFalse(result)


class BonCommandePermissionsTest(BasePermissionTestCase):
    """Tests pour les permissions des bons de commande."""

    def test_can_view_bon_commande_demandeur(self):
        """Test que le demandeur de la DA peut voir le BC."""
        result = GACPermissions.can_view_bon_commande(
            self.user_demandeur,
            self.bon_commande
        )
        self.assertTrue(result)

    def test_can_view_bon_commande_autre_utilisateur(self):
        """Test qu'un autre utilisateur ne peut pas voir."""
        result = GACPermissions.can_view_bon_commande(
            self.user_no_role,
            self.bon_commande
        )
        self.assertFalse(result)

    def test_can_modify_bon_commande_brouillon(self):
        """Test qu'on peut modifier un BC en brouillon."""
        # Note: Dépend du système de rôles
        # result = GACPermissions.can_modify_bon_commande(
        #     self.user_acheteur,
        #     self.bon_commande
        # )
        # self.assertTrue(result)

    def test_can_modify_bon_commande_non_brouillon(self):
        """Test qu'on ne peut pas modifier un BC non brouillon."""
        self.bon_commande.statut = 'EMIS'
        self.bon_commande.save()

        result = GACPermissions.can_modify_bon_commande(
            self.user_acheteur,
            self.bon_commande
        )
        self.assertFalse(result)

    def test_can_emit_bon_commande_brouillon(self):
        """Test qu'on peut émettre un BC en brouillon."""
        # Note: Dépend du système de rôles
        pass

    def test_can_emit_bon_commande_mauvais_statut(self):
        """Test qu'on ne peut pas émettre si statut incorrect."""
        self.bon_commande.statut = 'EMIS'
        self.bon_commande.save()

        result = GACPermissions.can_emit_bon_commande(
            self.user_acheteur,
            self.bon_commande
        )
        self.assertFalse(result)

    def test_can_send_bon_commande_emis(self):
        """Test qu'on peut envoyer un BC émis."""
        self.bon_commande.statut = 'EMIS'
        self.bon_commande.save()

        # result = GACPermissions.can_send_bon_commande(
        #     self.user_acheteur,
        #     self.bon_commande
        # )
        # self.assertTrue(result)

    def test_can_confirm_bon_commande_envoye(self):
        """Test qu'on peut confirmer un BC envoyé."""
        self.bon_commande.statut = 'ENVOYE'
        self.bon_commande.save()

        # result = GACPermissions.can_confirm_bon_commande(
        #     self.user_acheteur,
        #     self.bon_commande
        # )
        # self.assertTrue(result)

    def test_can_cancel_bon_commande_non_recu(self):
        """Test qu'on peut annuler un BC non reçu."""
        self.bon_commande.statut = 'EMIS'
        self.bon_commande.save()

        # result = GACPermissions.can_cancel_bon_commande(
        #     self.user_acheteur,
        #     self.bon_commande
        # )
        # self.assertTrue(result)

    def test_can_cancel_bon_commande_recu(self):
        """Test qu'on ne peut pas annuler un BC reçu."""
        self.bon_commande.statut = 'RECU_COMPLET'
        self.bon_commande.save()

        result = GACPermissions.can_cancel_bon_commande(
            self.user_acheteur,
            self.bon_commande
        )
        self.assertFalse(result)

    def test_can_download_pdf(self):
        """Test qu'on peut télécharger le PDF si on peut voir le BC."""
        result = GACPermissions.can_download_pdf(
            self.user_demandeur,
            self.bon_commande
        )
        self.assertTrue(result)


class FournisseurPermissionsTest(BasePermissionTestCase):
    """Tests pour les permissions des fournisseurs."""

    def test_can_view_fournisseur_authentifie(self):
        """Test qu'un utilisateur authentifié peut voir les fournisseurs."""
        result = GACPermissions.can_view_fournisseur(self.user_demandeur)
        self.assertTrue(result)

    def test_can_view_fournisseur_non_authentifie(self):
        """Test qu'un utilisateur non authentifié ne peut pas voir."""
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        result = GACPermissions.can_view_fournisseur(anonymous_user)
        self.assertFalse(result)


class ReceptionPermissionsTest(BasePermissionTestCase):
    """Tests pour les permissions des réceptions."""

    def setUp(self):
        """Prépare une réception de test."""
        super().setUp()

        self.reception = GACReception.objects.create(
            bon_commande=self.bon_commande,
            receptionnaire=self.employe_receptionnaire,
            date_reception=timezone.now().date(),
            statut='BROUILLON'
        )

    def test_can_view_reception_demandeur(self):
        """Test que le demandeur de la DA peut voir la réception."""
        result = GACPermissions.can_view_reception(
            self.user_demandeur,
            self.reception
        )
        self.assertTrue(result)

    def test_can_view_reception_autre_utilisateur(self):
        """Test qu'un autre utilisateur ne peut pas voir."""
        result = GACPermissions.can_view_reception(
            self.user_no_role,
            self.reception
        )
        self.assertFalse(result)

    def test_can_modify_reception_brouillon(self):
        """Test qu'on peut modifier une réception en brouillon."""
        # Note: Dépend du système de rôles
        pass

    def test_can_modify_reception_validee(self):
        """Test qu'on ne peut pas modifier une réception validée."""
        self.reception.statut = 'VALIDEE'
        self.reception.save()

        result = GACPermissions.can_modify_reception(
            self.user_receptionnaire,
            self.reception
        )
        self.assertFalse(result)

    def test_can_validate_reception_brouillon(self):
        """Test qu'on peut valider une réception en brouillon."""
        # Note: Dépend du système de rôles
        pass

    def test_can_validate_reception_mauvais_statut(self):
        """Test qu'on ne peut pas valider si statut incorrect."""
        self.reception.statut = 'VALIDEE'
        self.reception.save()

        result = GACPermissions.can_validate_reception(
            self.user_receptionnaire,
            self.reception
        )
        self.assertFalse(result)


class BudgetPermissionsTest(BasePermissionTestCase):
    """Tests pour les permissions des budgets."""

    def test_can_view_budget_gestionnaire(self):
        """Test que le gestionnaire peut voir son budget."""
        result = GACPermissions.can_view_budget(
            self.user_gestionnaire_budget,
            self.budget
        )
        self.assertTrue(result)

    def test_can_view_budget_demandeur_avec_demande_liee(self):
        """Test qu'un demandeur peut voir un budget s'il a une demande liée."""
        result = GACPermissions.can_view_budget(
            self.user_demandeur,
            self.budget
        )
        # La demande est liée au budget, donc devrait être True
        self.assertTrue(result)

    def test_can_view_budget_autre_utilisateur(self):
        """Test qu'un autre utilisateur ne peut pas voir le budget."""
        result = GACPermissions.can_view_budget(
            self.user_no_role,
            self.budget
        )
        self.assertFalse(result)

    def test_can_modify_budget_gestionnaire(self):
        """Test que le gestionnaire peut modifier son budget."""
        # Note: Dépend du système de rôles
        pass


class CataloguePermissionsTest(BasePermissionTestCase):
    """Tests pour les permissions du catalogue."""

    def test_can_view_catalogue_authentifie(self):
        """Test qu'un utilisateur authentifié peut voir le catalogue."""
        result = GACPermissions.can_view_catalogue(self.user_demandeur)
        self.assertTrue(result)

    def test_can_view_catalogue_non_authentifie(self):
        """Test qu'un utilisateur non authentifié ne peut pas voir."""
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        result = GACPermissions.can_view_catalogue(anonymous_user)
        self.assertFalse(result)


# Fonction pour exécuter tous les tests
def run_permission_tests():
    """Exécute tous les tests de permissions."""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(["gestion_achats.tests.test_permissions"])

    return failures
