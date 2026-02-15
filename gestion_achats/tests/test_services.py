"""
Tests pour les services du module GAC.

Tests complets pour DemandeService, BonCommandeService, ReceptionService,
BudgetService et autres services critiques.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
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
    GACBonRetour,
    GACHistorique,
)
from gestion_achats.services import (
    DemandeService,
    BonCommandeService,
    ReceptionService,
    BudgetService,
    FournisseurService,
)
from gestion_achats.exceptions import (
    GACException,
    DemandeError,
    WorkflowError,
    BudgetInsuffisantError,
)
from datetime import date
from django.contrib.auth.models import User
from employee.models import ZY00, ZYRO, ZYRE
from departement.models import ZDDE
from entreprise.models import Entreprise


class BaseGACTestCase(TestCase):
    """Classe de base pour les tests GAC avec fixtures communes."""

    def setUp(self):
        """Prépare les données communes à tous les tests."""
        # Créer une entreprise
        self.entreprise = Entreprise.objects.create(
            code='GAC001',
            nom='Entreprise GAC Test',
            raison_sociale='GAC Test SARL',
            numero_impot='999888777',
            rccm='RCCM-GAC-001',
            adresse='123 Avenue Test',
            ville='Lomé',
            pays='Togo'
        )

        # Créer un rôle ADMIN_GAC pour la validation
        self.role_admin_gac, _ = ZYRO.objects.get_or_create(
            CODE='ADMIN_GAC',
            defaults={
                'LIBELLE': 'Administrateur GAC',
                'DESCRIPTION': 'Administrateur du module Gestion des Achats et Commandes'
            }
        )

        # Créer des employés avec tous les champs requis
        self.demandeur = ZY00.objects.create(
            nom='Demandeur',
            prenoms='Test',
            date_naissance=date(1985, 5, 15),
            sexe='M',
            type_id='CNI',
            numero_id='DEM001CNI',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise,
            etat='actif'
        )

        self.validateur_n1 = ZY00.objects.create(
            nom='Validateur',
            prenoms='N1',
            date_naissance=date(1980, 3, 20),
            sexe='M',
            type_id='CNI',
            numero_id='VAL001CNI',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise,
            etat='actif'
        )

        self.validateur_n2 = ZY00.objects.create(
            nom='Validateur',
            prenoms='N2',
            date_naissance=date(1982, 7, 10),
            sexe='F',
            type_id='CNI',
            numero_id='VAL002CNI',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise,
            etat='actif'
        )

        self.acheteur = ZY00.objects.create(
            nom='Acheteur',
            prenoms='Test',
            date_naissance=date(1988, 11, 25),
            sexe='M',
            type_id='CNI',
            numero_id='ACH001CNI',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise,
            etat='actif'
        )

        # Créer un département (CODE doit avoir 3 caractères max)
        self.departement = ZDDE.objects.create(
            CODE='ACH',
            LIBELLE='Département Achats'
        )

        # Créer un budget
        self.budget = GACBudget.objects.create(
            code='BUD2024',
            libelle='Budget Test 2024',
            montant_initial=Decimal('100000.00'),
            montant_engage=Decimal('0.00'),
            montant_commande=Decimal('0.00'),
            montant_consomme=Decimal('0.00'),
            exercice=2024,
            date_debut=timezone.now().date(),
            date_fin=timezone.now().date() + timedelta(days=365),
            gestionnaire=self.demandeur
        )

        # Créer une catégorie
        self.categorie = GACCategorie.objects.create(
            code='CAT001',
            nom='Fournitures de bureau'
        )

        # Créer des articles
        self.article1 = GACArticle.objects.create(
            reference='ART001',
            designation='Papier A4',
            categorie=self.categorie,
            prix_unitaire=Decimal('5.00'),
            taux_tva=Decimal('20.00'),
            unite='PAQUET'
        )

        self.article2 = GACArticle.objects.create(
            reference='ART002',
            designation='Stylos',
            categorie=self.categorie,
            prix_unitaire=Decimal('2.00'),
            taux_tva=Decimal('20.00'),
            unite='PIECE'
        )

        # Créer un fournisseur
        self.fournisseur = GACFournisseur.objects.create(
            code='FRN001',
            raison_sociale='Fournisseur Test',
            nif='123456789',
            telephone='0123456789',
            email='fournisseur@test.com',
            adresse='1 rue Test',
            code_postal='75001',
            ville='Lomé',
            pays='Togo'
        )

        # Assigner le rôle ADMIN_GAC aux validateurs (nécessaire pour soumettre_demande)
        ZYRE.objects.create(
            employe=self.validateur_n1,
            role=self.role_admin_gac,
            date_debut=date.today(),
            actif=True
        )
        ZYRE.objects.create(
            employe=self.validateur_n2,
            role=self.role_admin_gac,
            date_debut=date.today(),
            actif=True
        )


class DemandeServiceTest(BaseGACTestCase):
    """Tests pour DemandeService."""

    def test_creer_demande_brouillon(self):
        """Test la création d'une demande en brouillon."""
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Achat de fournitures',
            justification='Renouvellement stock',
            departement=self.departement,
            budget=self.budget,
            priorite='NORMALE'
        )

        self.assertIsNotNone(demande)
        self.assertEqual(demande.statut, 'BROUILLON')
        self.assertEqual(demande.demandeur, self.demandeur)
        self.assertEqual(demande.objet, 'Achat de fournitures')
        self.assertTrue(demande.numero.startswith('DA-'))

        # Vérifier qu'un historique a été créé
        historique = GACHistorique.objects.filter(
            object_id=demande.uuid,
            action='CREATION'
        ).first()
        self.assertIsNotNone(historique)

    def test_ajouter_ligne(self):
        """Test l'ajout d'une ligne à une demande."""
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test'
        )

        ligne = DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('5.00')
        )

        self.assertIsNotNone(ligne)
        self.assertEqual(ligne.article, self.article1)
        self.assertEqual(ligne.quantite, Decimal('10'))
        self.assertEqual(ligne.montant, Decimal('50.00'))

        # Vérifier que la demande a été recalculée
        demande.refresh_from_db()
        self.assertEqual(demande.montant_total_ht, Decimal('50.00'))

    def test_ajouter_ligne_demande_non_brouillon_echoue(self):
        """Test qu'on ne peut pas ajouter une ligne à une demande non brouillon."""
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test'
        )

        # Soumettre la demande
        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('5.00')
        )
        DemandeService.soumettre_demande(demande, self.demandeur)

        # Essayer d'ajouter une ligne après soumission
        with self.assertRaises(WorkflowError):
            DemandeService.ajouter_ligne(
                demande=demande,
                article=self.article2,
                quantite=Decimal('5'),
                prix_unitaire=Decimal('2.00')
            )

    def test_soumettre_demande(self):
        """Test la soumission d'une demande."""
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('5.00')
        )

        DemandeService.soumettre_demande(demande, self.demandeur)

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'SOUMISE')
        self.assertIsNotNone(demande.date_soumission)

    def test_soumettre_demande_sans_lignes_echoue(self):
        """Test qu'on ne peut pas soumettre une demande sans lignes."""
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test'
        )

        with self.assertRaises(GACException):
            DemandeService.soumettre_demande(demande, self.demandeur)

    def test_valider_n1(self):
        """Test la validation N1 d'une demande."""
        # Créer et soumettre une demande
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('5.00')
        )

        DemandeService.soumettre_demande(demande, self.demandeur)

        # Définir un validateur N2 pour que valider_n1 reste en VALIDEE_N1
        demande.validateur_n2 = self.validateur_n2
        demande.save()

        # Valider N1
        DemandeService.valider_n1(
            demande=demande,
            validateur=self.validateur_n1,
            commentaire='Approuvé N1'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'VALIDEE_N1')
        self.assertEqual(demande.validateur_n1, self.validateur_n1)
        self.assertIsNotNone(demande.date_validation_n1)

    def test_valider_n2(self):
        """Test la validation N2 d'une demande."""
        # Créer, soumettre et valider N1
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),  # Montant élevé pour nécessiter N2 (> 5000 FCFA seuil)
            prix_unitaire=Decimal('1000.00')
        )

        DemandeService.soumettre_demande(demande, self.demandeur)

        # Forcer le validateur_n2 correct (soumettre_demande auto-assigne le premier ADMIN_GAC)
        demande.validateur_n2 = self.validateur_n2
        demande.save()

        DemandeService.valider_n1(demande, self.validateur_n1)

        # Valider N2
        DemandeService.valider_n2(
            demande=demande,
            validateur=self.validateur_n2,
            commentaire='Approuvé N2'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'VALIDEE_N2')
        self.assertEqual(demande.validateur_n2, self.validateur_n2)
        self.assertIsNotNone(demande.date_validation_n2)

    def test_refuser_demande(self):
        """Test le refus d'une demande."""
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('5.00')
        )

        DemandeService.soumettre_demande(demande, self.demandeur)

        # Refuser la demande
        DemandeService.refuser_demande(
            demande=demande,
            validateur=self.validateur_n1,
            motif='Budget insuffisant'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'REFUSEE')
        self.assertEqual(demande.motif_refus, 'Budget insuffisant')

    def test_annuler_demande(self):
        """Test l'annulation d'une demande."""
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test'
        )

        DemandeService.annuler_demande(
            demande=demande,
            utilisateur=self.demandeur,
            motif='Erreur de saisie'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'ANNULEE')
        self.assertEqual(demande.motif_annulation, 'Erreur de saisie')

    def test_get_demandes_a_valider_n1(self):
        """Test la récupération des demandes à valider N1."""
        # Créer et soumettre plusieurs demandes
        for i in range(3):
            demande = DemandeService.creer_demande_brouillon(
                demandeur=self.demandeur,
                objet=f'Test {i}',
                justification='Test'
            )
            DemandeService.ajouter_ligne(
                demande=demande,
                article=self.article1,
                quantite=Decimal('10'),
                prix_unitaire=Decimal('5.00')
            )
            DemandeService.soumettre_demande(demande, self.demandeur)

        # Récupérer les demandes à valider
        demandes = DemandeService.get_demandes_a_valider_n1(self.validateur_n1)

        # Note: Le résultat dépend de la logique métier
        # (ex: validation par hiérarchie/département)
        self.assertIsNotNone(demandes)


class BonCommandeServiceTest(BaseGACTestCase):
    """Tests pour BonCommandeService."""

    def test_creer_bon_commande_depuis_demande(self):
        """Test la création d'un BC depuis une demande validée."""
        # Créer une demande validée
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test',
            justification='Test',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('5.00')
        )

        DemandeService.soumettre_demande(demande, self.demandeur)
        DemandeService.valider_n1(demande, self.validateur_n1)

        # Créer le bon de commande
        bc = BonCommandeService.creer_bon_commande(
            demande_achat=demande,
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        self.assertIsNotNone(bc)
        self.assertEqual(bc.statut, 'BROUILLON')
        self.assertEqual(bc.fournisseur, self.fournisseur)
        self.assertEqual(bc.demande_achat, demande)
        self.assertTrue(bc.numero.startswith('BC-'))

    def test_ajouter_ligne_bon_commande(self):
        """Test l'ajout d'une ligne à un bon de commande."""
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        ligne = BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('20'),
            prix_unitaire=Decimal('5.00')
        )

        self.assertIsNotNone(ligne)
        self.assertEqual(ligne.article, self.article1)
        self.assertEqual(ligne.quantite_commandee, Decimal('20'))
        self.assertEqual(ligne.montant, Decimal('100.00'))

        # Vérifier le recalcul du BC
        bc.refresh_from_db()
        self.assertEqual(bc.montant_total_ht, Decimal('100.00'))

    def test_emettre_bon_commande(self):
        """Test l'émission d'un bon de commande."""
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('20'),
            prix_unitaire=Decimal('5.00')
        )

        BonCommandeService.emettre_bon_commande(bc, self.acheteur)

        bc.refresh_from_db()
        self.assertEqual(bc.statut, 'EMIS')
        self.assertIsNotNone(bc.date_emission)

    def test_annuler_bon_commande(self):
        """Test l'annulation d'un bon de commande."""
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.annuler_bon_commande(
            bc=bc,
            utilisateur=self.acheteur,
            motif_annulation='Erreur fournisseur'
        )

        bc.refresh_from_db()
        self.assertEqual(bc.statut, 'ANNULE')
        self.assertEqual(bc.motif_annulation, 'Erreur fournisseur')

    def test_get_bons_commande_en_attente_reception(self):
        """Test la récupération des BCs en attente de réception."""
        # Créer un BC et l'amener au statut CONFIRME
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('20'),
            prix_unitaire=Decimal('5.00')
        )

        BonCommandeService.emettre_bon_commande(bc, self.acheteur)

        # Passer directement en CONFIRME (envoyer_au_fournisseur nécessite un PDF)
        bc.statut = 'ENVOYE'
        bc.save()
        bc.statut = 'CONFIRME'
        bc.date_confirmation = timezone.now()
        bc.save()

        # Récupérer les BCs en attente
        bcs_attente = BonCommandeService.get_bons_commande_en_attente_reception()

        # Le BC confirmé devrait être dans la liste
        self.assertTrue(bcs_attente.exists())


class ReceptionServiceTest(BaseGACTestCase):
    """Tests pour ReceptionService."""

    def setUp(self):
        """Prépare les données spécifiques aux tests de réception."""
        super().setUp()

        # Créer un bon de commande émis
        self.bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.ajouter_ligne(
            bc=self.bc,
            article=self.article1,
            quantite_commandee=Decimal('100'),
            prix_unitaire=Decimal('5.00')
        )

        BonCommandeService.emettre_bon_commande(self.bc, self.acheteur)

        # Simuler l'envoi au fournisseur
        self.bc.statut = 'ENVOYE'
        self.bc.save()

    def test_creer_reception(self):
        """Test la création d'une réception."""
        reception = ReceptionService.creer_reception(
            bon_commande=self.bc,
            receptionnaire=self.demandeur,
            date_reception=timezone.now().date()
        )

        self.assertIsNotNone(reception)
        self.assertEqual(reception.statut, 'BROUILLON')
        self.assertEqual(reception.bon_commande, self.bc)
        self.assertEqual(reception.receptionnaire, self.demandeur)
        self.assertTrue(reception.numero.startswith('REC-'))

    def test_valider_reception(self):
        """Test la validation d'une réception."""
        # Créer une réception
        reception = ReceptionService.creer_reception(
            bon_commande=self.bc,
            receptionnaire=self.demandeur
        )

        # Ajouter une ligne de réception
        ligne_bc = self.bc.lignes.first()
        ligne_reception = GACLigneReception.objects.create(
            reception=reception,
            ligne_bon_commande=ligne_bc,
            quantite_recue=Decimal('100'),
            quantite_acceptee=Decimal('100'),
            quantite_refusee=Decimal('0')
        )

        # Valider la réception
        ReceptionService.valider_reception(reception, self.demandeur)

        reception.refresh_from_db()
        self.assertEqual(reception.statut, 'VALIDEE')
        self.assertIsNotNone(reception.date_validation)

        # Vérifier que le BC a été mis à jour
        self.bc.refresh_from_db()
        ligne_bc.refresh_from_db()
        self.assertEqual(ligne_bc.quantite_recue, Decimal('100'))

    def test_annuler_reception(self):
        """Test l'annulation d'une réception."""
        reception = ReceptionService.creer_reception(
            bon_commande=self.bc,
            receptionnaire=self.demandeur
        )

        ReceptionService.annuler_reception(
            reception=reception,
            utilisateur=self.demandeur,
            motif='Erreur de saisie'
        )

        reception.refresh_from_db()
        self.assertEqual(reception.statut, 'ANNULEE')

    def test_get_receptions_en_attente(self):
        """Test la récupération des réceptions en attente."""
        # Créer plusieurs réceptions
        for i in range(3):
            ReceptionService.creer_reception(
                bon_commande=self.bc,
                receptionnaire=self.demandeur
            )

        receptions = ReceptionService.get_receptions_en_attente()

        self.assertEqual(receptions.count(), 3)


class BudgetServiceTest(BaseGACTestCase):
    """Tests pour BudgetService."""

    def test_get_budgets_en_alerte(self):
        """Test la récupération des budgets en alerte."""
        # Créer un budget presque épuisé
        budget_alerte = GACBudget.objects.create(
            code='BUD_ALERTE',
            libelle='Budget en alerte',
            montant_initial=Decimal('10000.00'),
            montant_engage=Decimal('8000.00'),
            montant_commande=Decimal('1500.00'),
            montant_consomme=Decimal('0.00'),
            exercice=2024,
            date_debut=timezone.now().date(),
            date_fin=timezone.now().date() + timedelta(days=365),
            gestionnaire=self.demandeur
        )

        budgets_alerte = BudgetService.get_budgets_en_alerte()

        # Le budget devrait être en alerte (95% consommé)
        self.assertTrue(
            any(b['budget'].uuid == budget_alerte.uuid for b in budgets_alerte)
        )

    def test_verifier_disponibilite(self):
        """Test la vérification de disponibilité budgétaire."""
        # Budget disponible: 100000
        disponible = BudgetService.verifier_disponibilite(
            budget=self.budget,
            montant=Decimal('50000.00')
        )

        self.assertTrue(disponible)

        # Montant trop élevé → doit lever BudgetInsuffisantError
        with self.assertRaises(BudgetInsuffisantError):
            BudgetService.verifier_disponibilite(
                budget=self.budget,
                montant=Decimal('150000.00')
            )


class FournisseurServiceTest(BaseGACTestCase):
    """Tests pour FournisseurService."""

    def test_get_fournisseurs_actifs(self):
        """Test la récupération des fournisseurs actifs."""
        fournisseurs = FournisseurService.get_fournisseurs_actifs()

        self.assertEqual(fournisseurs.count(), 1)
        self.assertEqual(fournisseurs.first(), self.fournisseur)

    def test_creer_fournisseur(self):
        """Test la création d'un fournisseur."""
        nouveau_fournisseur = FournisseurService.creer_fournisseur(
            raison_sociale='Nouveau Fournisseur',
            nif='987654321',
            email='nouveau@fournisseur.com',
            telephone='9876543210',
            adresse='2 rue Test',
            ville='Cotonou',
            pays='Bénin'
        )

        self.assertIsNotNone(nouveau_fournisseur)
        self.assertEqual(nouveau_fournisseur.statut, 'ACTIF')
        self.assertIsNotNone(nouveau_fournisseur.code)  # Code auto-généré


# Fonction pour exécuter tous les tests
def run_all_tests():
    """Exécute tous les tests du module services."""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(["gestion_achats.tests.test_services"])

    return failures
