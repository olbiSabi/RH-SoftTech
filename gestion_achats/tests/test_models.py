"""
Tests unitaires pour les modèles du module GAC.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from gestion_achats.models import (
    GACFournisseur,
    GACCategorie,
    GACArticle,
    GACBudget,
    GACDemandeAchat,
    GACLigneDemandeAchat,
    GACBonCommande,
    GACLigneBonCommande,
    GACReception,
    GACLigneReception,
)
from employee.models import ZY00
from departement.models import ZDDE


class GACFournisseurModelTest(TestCase):
    """Tests pour le modèle GACFournisseur."""

    def setUp(self):
        """Prépare les données de test."""
        self.fournisseur = GACFournisseur.objects.create(
            code='FRNTEST',
            raison_sociale='Fournisseur Test',
            siret='12345678901234',
            email='test@fournisseur.fr',
            telephone='0123456789',
            adresse='1 rue Test',
            code_postal='75001',
            ville='Paris'
        )

    def test_str_representation(self):
        """Teste la représentation en chaîne."""
        expected = "FRNTEST - Fournisseur Test"
        self.assertEqual(str(self.fournisseur), expected)

    def test_siret_validation(self):
        """Teste la validation du SIRET."""
        # SIRET valide
        self.assertEqual(len(self.fournisseur.siret), 14)

    def test_statut_default(self):
        """Teste le statut par défaut."""
        self.assertEqual(self.fournisseur.statut, 'ACTIF')

    def test_evaluation_moyenne_default(self):
        """Teste la valeur par défaut de l'évaluation."""
        self.assertEqual(self.fournisseur.evaluation_moyenne, Decimal('0.00'))


class GACCategorieModelTest(TestCase):
    """Tests pour le modèle GACCategorie."""

    def setUp(self):
        """Prépare les données de test."""
        self.categorie_parent = GACCategorie.objects.create(
            code='CAT_PARENT',
            nom='Catégorie Parent',
            description='Description parent'
        )

        self.sous_categorie = GACCategorie.objects.create(
            code='CAT_ENFANT',
            nom='Sous-catégorie',
            parent=self.categorie_parent
        )

    def test_str_representation_sans_parent(self):
        """Teste la représentation d'une catégorie sans parent."""
        self.assertEqual(str(self.categorie_parent), 'Catégorie Parent')

    def test_str_representation_avec_parent(self):
        """Teste la représentation d'une sous-catégorie."""
        expected = 'Catégorie Parent > Sous-catégorie'
        self.assertEqual(str(self.sous_categorie), expected)

    def test_get_chemin_complet(self):
        """Teste la récupération du chemin complet."""
        chemin = self.sous_categorie.get_chemin_complet()
        expected = 'Catégorie Parent > Sous-catégorie'
        self.assertEqual(chemin, expected)


class GACArticleModelTest(TestCase):
    """Tests pour le modèle GACArticle."""

    def setUp(self):
        """Prépare les données de test."""
        self.categorie = GACCategorie.objects.create(
            code='CAT_TEST',
            nom='Catégorie Test'
        )

        self.article = GACArticle.objects.create(
            reference='ART001',
            designation='Article Test',
            categorie=self.categorie,
            prix_unitaire=Decimal('100.00'),
            taux_tva=Decimal('20.00'),
            unite='PIECE'
        )

    def test_str_representation(self):
        """Teste la représentation en chaîne."""
        expected = "ART001 - Article Test"
        self.assertEqual(str(self.article), expected)

    def test_calculer_prix_ttc(self):
        """Teste le calcul du prix TTC."""
        prix_ttc = self.article.calculer_prix_ttc()
        expected = Decimal('120.00')
        self.assertEqual(prix_ttc, expected)

    def test_statut_default(self):
        """Teste le statut par défaut."""
        self.assertEqual(self.article.statut, 'ACTIF')


class GACBudgetModelTest(TestCase):
    """Tests pour le modèle GACBudget."""

    def setUp(self):
        """Prépare les données de test."""
        # Créer un employé de test
        self.employe = ZY00.objects.create(
            MATRICULE='TEST001',
            NOM='Test',
            PRENOM='User',
            EMAIL='test@example.com'
        )

        # Créer un budget
        today = timezone.now().date()
        self.budget = GACBudget.objects.create(
            code='BUD2024',
            libelle='Budget Test 2024',
            montant_initial=Decimal('10000.00'),
            montant_engage=Decimal('2000.00'),
            montant_commande=Decimal('3000.00'),
            montant_consomme=Decimal('1000.00'),
            exercice=2024,
            date_debut=today,
            date_fin=today + timedelta(days=365),
            gestionnaire=self.employe
        )

    def test_str_representation(self):
        """Teste la représentation en chaîne."""
        expected = "BUD2024 - Budget Test 2024 (2024)"
        self.assertEqual(str(self.budget), expected)

    def test_montant_disponible(self):
        """Teste le calcul du montant disponible."""
        disponible = self.budget.montant_disponible()
        # 10000 - (2000 + 3000 + 1000) = 4000
        expected = Decimal('4000.00')
        self.assertEqual(disponible, expected)

    def test_taux_consommation(self):
        """Teste le calcul du taux de consommation."""
        taux = self.budget.taux_consommation()
        # (2000 + 3000 + 1000) / 10000 * 100 = 60%
        expected = Decimal('60.00')
        self.assertEqual(taux, expected)

    def test_taux_consommation_budget_nul(self):
        """Teste le taux de consommation avec un budget initial nul."""
        budget = GACBudget.objects.create(
            code='BUD_NUL',
            libelle='Budget Nul',
            montant_initial=Decimal('0.00'),
            exercice=2024,
            date_debut=timezone.now().date(),
            date_fin=timezone.now().date() + timedelta(days=365),
            gestionnaire=self.employe
        )
        taux = budget.taux_consommation()
        self.assertEqual(taux, Decimal('0.00'))


class GACDemandeAchatModelTest(TestCase):
    """Tests pour le modèle GACDemandeAchat."""

    def setUp(self):
        """Prépare les données de test."""
        # Créer un employé
        self.employe = ZY00.objects.create(
            MATRICULE='TEST002',
            NOM='Demandeur',
            PRENOM='Test',
            EMAIL='demandeur@example.com'
        )

        # Créer une demande
        self.demande = GACDemandeAchat.objects.create(
            objet='Test Demande',
            justification='Justification test',
            demandeur=self.employe,
            priorite='NORMALE'
        )

    def test_generation_numero(self):
        """Teste la génération automatique du numéro."""
        self.assertIsNotNone(self.demande.numero)
        self.assertTrue(self.demande.numero.startswith('DA-'))

    def test_statut_default(self):
        """Teste le statut par défaut."""
        self.assertEqual(self.demande.statut, 'BROUILLON')

    def test_get_statut_badge_class(self):
        """Teste la récupération de la classe CSS du badge de statut."""
        self.assertEqual(self.demande.get_statut_badge_class(), 'secondary')

        self.demande.statut = 'VALIDEE_N2'
        self.assertEqual(self.demande.get_statut_badge_class(), 'success')

    def test_get_priorite_badge_class(self):
        """Teste la récupération de la classe CSS du badge de priorité."""
        self.assertEqual(self.demande.get_priorite_badge_class(), 'info')

        self.demande.priorite = 'URGENTE'
        self.assertEqual(self.demande.get_priorite_badge_class(), 'danger')


class GACLigneDemandeAchatModelTest(TestCase):
    """Tests pour le modèle GACLigneDemandeAchat."""

    def setUp(self):
        """Prépare les données de test."""
        # Créer employé, catégorie, article, demande
        self.employe = ZY00.objects.create(
            MATRICULE='TEST003',
            NOM='Test',
            PRENOM='User'
        )

        self.categorie = GACCategorie.objects.create(
            code='CAT_TEST',
            nom='Test'
        )

        self.article = GACArticle.objects.create(
            reference='ART_TEST',
            designation='Article Test',
            categorie=self.categorie,
            prix_unitaire=Decimal('50.00'),
            taux_tva=Decimal('20.00'),
            unite='PIECE'
        )

        self.demande = GACDemandeAchat.objects.create(
            objet='Test',
            justification='Test',
            demandeur=self.employe
        )

        self.ligne = GACLigneDemandeAchat.objects.create(
            demande_achat=self.demande,
            article=self.article,
            quantite=Decimal('10.00'),
            prix_unitaire=Decimal('50.00'),
            taux_tva=Decimal('20.00')
        )

    def test_calcul_montants(self):
        """Teste le calcul automatique des montants."""
        # Montant HT = 10 * 50 = 500
        self.assertEqual(self.ligne.montant, Decimal('500.00'))

        # TVA = 500 * 20% = 100
        self.assertEqual(self.ligne.montant_tva, Decimal('100.00'))

        # TTC = 500 + 100 = 600
        self.assertEqual(self.ligne.montant_ttc, Decimal('600.00'))

    def test_str_representation(self):
        """Teste la représentation en chaîne."""
        expected = "ART_TEST x 10.00"
        self.assertEqual(str(self.ligne), expected)


class GACBonCommandeModelTest(TestCase):
    """Tests pour le modèle GACBonCommande."""

    def setUp(self):
        """Prépare les données de test."""
        self.employe = ZY00.objects.create(
            MATRICULE='TEST004',
            NOM='Acheteur',
            PRENOM='Test'
        )

        self.fournisseur = GACFournisseur.objects.create(
            code='FRN_TEST',
            raison_sociale='Fournisseur Test',
            siret='12345678901234',
            email='test@frn.fr',
            telephone='0123456789',
            adresse='Test'
        )

        self.bon_commande = GACBonCommande.objects.create(
            fournisseur=self.fournisseur,
            acheteur=self.employe
        )

    def test_generation_numero(self):
        """Teste la génération automatique du numéro."""
        self.assertIsNotNone(self.bon_commande.numero)
        self.assertTrue(self.bon_commande.numero.startswith('BC-'))

    def test_statut_default(self):
        """Teste le statut par défaut."""
        self.assertEqual(self.bon_commande.statut, 'BROUILLON')

    def test_get_statut_badge_class(self):
        """Teste la classe CSS du badge de statut."""
        self.assertEqual(self.bon_commande.get_statut_badge_class(), 'secondary')

        self.bon_commande.statut = 'RECU_COMPLET'
        self.assertEqual(self.bon_commande.get_statut_badge_class(), 'success')


# Fonction pour exécuter les tests
def run_tests():
    """Exécute tous les tests du module GAC."""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["gestion_achats.tests"])

    return failures
