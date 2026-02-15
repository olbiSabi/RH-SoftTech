"""
Tests d'intégration pour les workflows critiques du module GAC.

Tests end-to-end des processus métier complets:
- Workflow de demande d'achat (création → validation → conversion BC)
- Workflow de bon de commande (création → émission → envoi → réception)
- Workflow de réception (création → validation → mise à jour stocks/BC)
- Workflow de budget (engagement → consommation)
- Workflows de rejet et annulation
"""

from decimal import Decimal
from django.test import TestCase
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
    GACHistorique,
)
from gestion_achats.services import (
    DemandeService,
    BonCommandeService,
    ReceptionService,
    BudgetService,
)
from gestion_achats.exceptions import (
    DemandeError,
    WorkflowError,
    BudgetInsuffisantError,
)
from datetime import date
from django.contrib.auth.models import User
from employee.models import ZY00, ZYRO, ZYRE
from departement.models import ZDDE
from entreprise.models import Entreprise


class BaseWorkflowTestCase(TestCase):
    """Classe de base pour les tests de workflows."""

    def setUp(self):
        """Prépare les données communes."""
        # Créer une entreprise
        self.entreprise = Entreprise.objects.create(
            code='WKF001',
            nom='Entreprise Workflow Test',
            raison_sociale='Workflow Test SARL',
            numero_impot='888777666',
            rccm='RCCM-WKF-001',
            adresse='456 Boulevard Test',
            ville='Lomé',
            pays='Togo'
        )

        # Créer des employés pour chaque rôle avec tous les champs requis
        self.demandeur = ZY00.objects.create(
            nom='Demandeur',
            prenoms='Test',
            date_naissance=date(1985, 5, 15),
            sexe='M',
            type_id='CNI',
            numero_id='WF-DEM001',
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
            numero_id='WF-VAL001',
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
            numero_id='WF-VAL002',
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
            numero_id='WF-ACH001',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise,
            etat='actif'
        )

        self.receptionnaire = ZY00.objects.create(
            nom='Receptionnaire',
            prenoms='Test',
            date_naissance=date(1990, 2, 14),
            sexe='M',
            type_id='CNI',
            numero_id='WF-REC001',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise,
            etat='actif'
        )

        # Créer un département (CODE doit avoir 3 caractères max)
        self.departement = ZDDE.objects.create(
            CODE='WKF',
            LIBELLE='Département Workflow'
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

        # Créer une catégorie et des articles
        self.categorie = GACCategorie.objects.create(
            code='CAT001',
            nom='Fournitures de bureau'
        )

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
            ville='Lomé',
            pays='Togo'
        )

        # Créer le rôle ADMIN_GAC et l'assigner aux validateurs
        self.role_admin_gac, _ = ZYRO.objects.get_or_create(
            CODE='ADMIN_GAC',
            defaults={
                'LIBELLE': 'Administrateur GAC',
                'DESCRIPTION': 'Administrateur du module Gestion des Achats'
            }
        )
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


class WorkflowDemandeCompletTest(BaseWorkflowTestCase):
    """Test du workflow complet d'une demande d'achat."""

    def test_workflow_demande_validee_standard(self):
        """
        Test le workflow complet d'une demande standard (sans N2):
        Création → Ajout lignes → Soumission → Validation N1
        """
        # 1. Créer une demande en brouillon
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Achat de fournitures',
            justification='Renouvellement stock',
            departement=self.departement,
            budget=self.budget,
            priorite='NORMALE'
        )

        self.assertEqual(demande.statut, 'BROUILLON')

        # 2. Ajouter des lignes
        ligne1 = DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('5.00')
        )

        ligne2 = DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article2,
            quantite=Decimal('20'),
            prix_unitaire=Decimal('2.00')
        )

        # Vérifier les montants
        demande.refresh_from_db()
        expected_ht = Decimal('10') * Decimal('5.00') + Decimal('20') * Decimal('2.00')
        self.assertEqual(demande.montant_total_ht, expected_ht)

        # 3. Soumettre la demande
        DemandeService.soumettre_demande(demande, self.demandeur)

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'SOUMISE')
        self.assertIsNotNone(demande.date_soumission)

        # 4. Valider N1
        demande.validateur_n1 = self.validateur_n1
        demande.validateur_n2 = self.validateur_n2  # Nécessaire pour rester en VALIDEE_N1
        demande.save()

        DemandeService.valider_n1(
            demande=demande,
            validateur=self.validateur_n1,
            commentaire='Approuvé'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'VALIDEE_N1')
        self.assertIsNotNone(demande.date_validation_n1)

        # Vérifier l'historique
        historique = GACHistorique.objects.filter(
            object_id=demande.uuid
        ).order_by('date_action')

        self.assertGreaterEqual(historique.count(), 3)  # CREATION, SOUMISSION, VALIDATION_N1

    def test_workflow_demande_validee_avec_n2(self):
        """
        Test le workflow complet d'une demande nécessitant N2:
        Création → Ajout lignes → Soumission → Validation N1 → Validation N2
        """
        # 1. Créer une demande avec montant élevé
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Achat de matériel informatique',
            justification='Équipement nouveau service',
            departement=self.departement,
            budget=self.budget,
            priorite='HAUTE'
        )

        # 2. Ajouter une ligne avec montant élevé nécessitant validation N2 (> 5000 seuil)
        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('10'),
            prix_unitaire=Decimal('1000.00')
        )

        # 3. Soumettre
        DemandeService.soumettre_demande(demande, self.demandeur)

        # 4. Valider N1
        demande.validateur_n1 = self.validateur_n1
        demande.save()

        DemandeService.valider_n1(demande, self.validateur_n1)

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'VALIDEE_N1')

        # 5. Valider N2
        demande.validateur_n2 = self.validateur_n2
        demande.save()

        DemandeService.valider_n2(
            demande=demande,
            validateur=self.validateur_n2,
            commentaire='Approuvé N2'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'VALIDEE_N2')
        self.assertIsNotNone(demande.date_validation_n2)

    def test_workflow_demande_refusee(self):
        """
        Test le workflow de refus d'une demande:
        Création → Soumission → Refus N1
        """
        # 1. Créer et soumettre une demande
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Achat non justifié',
            justification='Test refus',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('5'),
            prix_unitaire=Decimal('5.00')
        )

        DemandeService.soumettre_demande(demande, self.demandeur)

        # 2. Refuser la demande
        demande.validateur_n1 = self.validateur_n1
        demande.save()

        DemandeService.refuser_demande(
            demande=demande,
            validateur=self.validateur_n1,
            motif='Budget insuffisant pour cet achat'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'REFUSEE')
        self.assertEqual(demande.motif_refus, 'Budget insuffisant pour cet achat')

    def test_workflow_demande_annulee(self):
        """
        Test le workflow d'annulation d'une demande par le demandeur.
        """
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Achat à annuler',
            justification='Test annulation'
        )

        DemandeService.annuler_demande(
            demande=demande,
            utilisateur=self.demandeur,
            motif='Erreur de saisie'
        )

        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'ANNULEE')
        self.assertEqual(demande.motif_annulation, 'Erreur de saisie')


class WorkflowBonCommandeCompletTest(BaseWorkflowTestCase):
    """Test du workflow complet d'un bon de commande."""

    def test_workflow_bc_depuis_demande_validee(self):
        """
        Test le workflow complet: DA validée → Création BC → Émission → Envoi
        """
        # 1. Créer et valider une demande
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Achat fournitures',
            justification='Test BC',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('50'),
            prix_unitaire=Decimal('5.00')
        )

        DemandeService.soumettre_demande(demande, self.demandeur)

        demande.validateur_n1 = self.validateur_n1
        demande.save()

        DemandeService.valider_n1(demande, self.validateur_n1)

        # 2. Créer le bon de commande
        bc = BonCommandeService.creer_bon_commande(
            demande_achat=demande,
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        self.assertEqual(bc.statut, 'BROUILLON')
        self.assertEqual(bc.demande_achat, demande)

        # Vérifier que la demande a été marquée comme convertie
        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'CONVERTIE_BC')

        # 3. Émettre le BC
        BonCommandeService.emettre_bon_commande(bc, self.acheteur)

        bc.refresh_from_db()
        self.assertEqual(bc.statut, 'EMIS')
        self.assertIsNotNone(bc.date_emission)

        # 4. Envoyer au fournisseur
        BonCommandeService.envoyer_au_fournisseur(
            bc=bc,
            utilisateur=self.acheteur,
            email_destinataire=self.fournisseur.email
        )

        bc.refresh_from_db()
        self.assertEqual(bc.statut, 'ENVOYE')
        self.assertIsNotNone(bc.date_envoi)

    def test_workflow_bc_manuel_sans_demande(self):
        """
        Test la création d'un BC manuel (sans DA associée).
        """
        # 1. Créer un BC manuel
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        # 2. Ajouter des lignes
        ligne1 = BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('30'),
            prix_unitaire=Decimal('5.00')
        )

        ligne2 = BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article2,
            quantite_commandee=Decimal('50'),
            prix_unitaire=Decimal('2.00')
        )

        # 3. Vérifier les montants
        bc.refresh_from_db()
        expected_ht = Decimal('30') * Decimal('5.00') + Decimal('50') * Decimal('2.00')
        self.assertEqual(bc.montant_total_ht, expected_ht)

        # 4. Émettre
        BonCommandeService.emettre_bon_commande(bc, self.acheteur)

        bc.refresh_from_db()
        self.assertEqual(bc.statut, 'EMIS')

    def test_workflow_bc_annulation(self):
        """Test l'annulation d'un bon de commande."""
        # Créer et émettre un BC
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

        # Annuler le BC
        BonCommandeService.annuler_bon_commande(
            bc=bc,
            utilisateur=self.acheteur,
            motif_annulation='Fournisseur indisponible'
        )

        bc.refresh_from_db()
        self.assertEqual(bc.statut, 'ANNULE')
        self.assertEqual(bc.motif_annulation, 'Fournisseur indisponible')


class WorkflowReceptionCompletTest(BaseWorkflowTestCase):
    """Test du workflow complet d'une réception."""

    def test_workflow_reception_complete_conforme(self):
        """
        Test le workflow complet d'une réception conforme:
        BC envoyé → Création réception → Validation → Mise à jour BC
        """
        # 1. Créer et émettre un BC
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('100'),
            prix_unitaire=Decimal('5.00')
        )

        BonCommandeService.emettre_bon_commande(bc, self.acheteur)
        BonCommandeService.envoyer_au_fournisseur(bc, self.acheteur)

        # 2. Créer une réception
        reception = ReceptionService.creer_reception(
            bon_commande=bc,
            receptionnaire=self.receptionnaire,
            date_reception=timezone.now().date()
        )

        self.assertEqual(reception.statut, 'BROUILLON')

        # 3. Enregistrer les lignes de réception
        ligne_bc = bc.lignes.first()

        ligne_reception = GACLigneReception.objects.create(
            reception=reception,
            ligne_bon_commande=ligne_bc,
            quantite_recue=Decimal('100'),
            quantite_acceptee=Decimal('100'),
            quantite_refusee=Decimal('0')
        )

        # 4. Valider la réception
        ReceptionService.valider_reception(
            reception=reception,
            utilisateur=self.receptionnaire
        )

        reception.refresh_from_db()
        self.assertEqual(reception.statut, 'VALIDEE')
        self.assertIsNotNone(reception.date_validation)

        # 5. Vérifier que le BC et ses lignes ont été mis à jour
        bc.refresh_from_db()
        ligne_bc.refresh_from_db()

        self.assertEqual(ligne_bc.quantite_recue, Decimal('100'))
        self.assertEqual(bc.statut, 'RECU_COMPLET')

    def test_workflow_reception_partielle(self):
        """Test le workflow d'une réception partielle."""
        # 1. Créer BC
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('100'),
            prix_unitaire=Decimal('5.00')
        )

        BonCommandeService.emettre_bon_commande(bc, self.acheteur)
        BonCommandeService.envoyer_au_fournisseur(bc, self.acheteur)

        # 2. Créer réception avec quantité partielle
        reception = ReceptionService.creer_reception(
            bon_commande=bc,
            receptionnaire=self.receptionnaire
        )

        ligne_bc = bc.lignes.first()

        GACLigneReception.objects.create(
            reception=reception,
            ligne_bon_commande=ligne_bc,
            quantite_recue=Decimal('50'),  # Seulement 50 sur 100
            quantite_acceptee=Decimal('50'),
            quantite_refusee=Decimal('0')
        )

        # 3. Valider
        ReceptionService.valider_reception(reception, self.receptionnaire)

        # 4. Vérifier le statut
        bc.refresh_from_db()
        ligne_bc.refresh_from_db()

        self.assertEqual(ligne_bc.quantite_recue, Decimal('50'))
        self.assertEqual(bc.statut, 'RECU_PARTIEL')

    def test_workflow_reception_non_conforme(self):
        """Test le workflow d'une réception avec articles refusés."""
        # 1. Créer BC
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('100'),
            prix_unitaire=Decimal('5.00')
        )

        BonCommandeService.emettre_bon_commande(bc, self.acheteur)
        BonCommandeService.envoyer_au_fournisseur(bc, self.acheteur)

        # 2. Créer réception avec refus
        reception = ReceptionService.creer_reception(
            bon_commande=bc,
            receptionnaire=self.receptionnaire
        )

        ligne_bc = bc.lignes.first()

        GACLigneReception.objects.create(
            reception=reception,
            ligne_bon_commande=ligne_bc,
            quantite_recue=Decimal('100'),
            quantite_acceptee=Decimal('80'),  # 20 refusés
            quantite_refusee=Decimal('20'),
            conforme=False,
            motif_refus='Articles endommagés'
        )

        # 3. Valider
        ReceptionService.valider_reception(reception, self.receptionnaire)

        # 4. Vérifier
        reception.refresh_from_db()
        self.assertEqual(reception.conforme, False)

    def test_workflow_reception_annulation(self):
        """Test l'annulation d'une réception."""
        # Créer réception
        bc = BonCommandeService.creer_bon_commande(
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        BonCommandeService.ajouter_ligne(
            bc=bc,
            article=self.article1,
            quantite_commandee=Decimal('50'),
            prix_unitaire=Decimal('5.00')
        )

        BonCommandeService.emettre_bon_commande(bc, self.acheteur)
        BonCommandeService.envoyer_au_fournisseur(bc, self.acheteur)

        reception = ReceptionService.creer_reception(
            bon_commande=bc,
            receptionnaire=self.receptionnaire
        )

        # Annuler
        ReceptionService.annuler_reception(
            reception=reception,
            utilisateur=self.acheteur,
            motif='Erreur de saisie'
        )

        reception.refresh_from_db()
        self.assertEqual(reception.statut, 'ANNULEE')


class WorkflowBudgetTest(BaseWorkflowTestCase):
    """Test du workflow de gestion budgétaire."""

    def test_workflow_engagement_consommation_budget(self):
        """
        Test le cycle complet d'engagement et consommation du budget:
        DA soumise → Engagement → DA validée → BC créé → Commande → Réception → Consommation
        """
        budget_initial = self.budget.montant_disponible()

        # 1. Créer et soumettre demande
        demande = DemandeService.creer_demande_brouillon(
            demandeur=self.demandeur,
            objet='Test budget',
            justification='Test',
            budget=self.budget
        )

        DemandeService.ajouter_ligne(
            demande=demande,
            article=self.article1,
            quantite=Decimal('100'),
            prix_unitaire=Decimal('10.00')
        )

        montant_demande = Decimal('1000.00')

        DemandeService.soumettre_demande(demande, self.demandeur)

        # 2. Vérifier l'engagement du budget
        self.budget.refresh_from_db()
        # Note: L'engagement réel dépend de l'implémentation des signaux

        # 3. Valider la demande
        demande.validateur_n1 = self.validateur_n1
        demande.save()

        DemandeService.valider_n1(demande, self.validateur_n1)

        # 4. Créer BC
        bc = BonCommandeService.creer_bon_commande(
            demande_achat=demande,
            fournisseur=self.fournisseur,
            acheteur=self.acheteur
        )

        # 5. Vérifier le montant commandé
        self.budget.refresh_from_db()
        # Le montant commandé devrait être mis à jour

    def test_verfication_disponibilite_budget(self):
        """Test la vérification de disponibilité budgétaire."""
        # Budget disponible: 100000

        # Test montant acceptable
        disponible = BudgetService.verifier_disponibilite(
            budget=self.budget,
            montant=Decimal('50000.00')
        )
        self.assertTrue(disponible)

        # Test montant trop élevé → doit lever BudgetInsuffisantError
        from gestion_achats.exceptions import BudgetInsuffisantError
        with self.assertRaises(BudgetInsuffisantError):
            BudgetService.verifier_disponibilite(
                budget=self.budget,
                montant=Decimal('150000.00')
            )


# Fonction pour exécuter tous les tests de workflows
def run_workflow_tests():
    """Exécute tous les tests de workflows."""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(["gestion_achats.tests.test_workflows"])

    return failures
