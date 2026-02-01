# materiel/tests.py
"""
Tests pour le module Suivi du Matériel & Parc.
python manage.py test materiel
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import MTCA, MTFO, MTMT, MTAF, MTMV, MTMA


User = get_user_model()


class MTCAModelTests(TestCase):
    """Tests pour le modèle MTCA (Catégorie de matériel)."""

    def test_create_categorie(self):
        """Test de création d'une catégorie."""
        categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique',
            DESCRIPTION='Matériel informatique',
            DUREE_AMORTISSEMENT=36
        )
        self.assertEqual(categorie.CODE, 'INFO')
        self.assertEqual(categorie.LIBELLE, 'Informatique')
        self.assertEqual(categorie.DUREE_AMORTISSEMENT, 36)
        self.assertTrue(categorie.STATUT)

    def test_code_uppercase(self):
        """Test que le code est converti en majuscules."""
        categorie = MTCA.objects.create(
            CODE='info',
            LIBELLE='Informatique'
        )
        self.assertEqual(categorie.CODE, 'INFO')

    def test_str_representation(self):
        """Test de la représentation string."""
        categorie = MTCA.objects.create(
            CODE='MOBIL',
            LIBELLE='Mobilier'
        )
        self.assertEqual(str(categorie), 'MOBIL - Mobilier')

    def test_default_values(self):
        """Test des valeurs par défaut."""
        categorie = MTCA.objects.create(
            CODE='TEST',
            LIBELLE='Test'
        )
        self.assertTrue(categorie.STATUT)
        self.assertEqual(categorie.ORDRE, 0)
        self.assertEqual(categorie.DUREE_AMORTISSEMENT, 36)


class MTFOModelTests(TestCase):
    """Tests pour le modèle MTFO (Fournisseur)."""

    def test_create_fournisseur(self):
        """Test de création d'un fournisseur."""
        fournisseur = MTFO.objects.create(
            RAISON_SOCIALE='Tech Solutions',
            CONTACT='Jean Dupont',
            TELEPHONE='+225 07 00 00 00',
            EMAIL='contact@techsolutions.ci'
        )
        self.assertIsNotNone(fournisseur.CODE)
        self.assertEqual(fournisseur.RAISON_SOCIALE, 'Tech Solutions')
        self.assertTrue(fournisseur.STATUT)

    def test_code_auto_generation(self):
        """Test de génération automatique du code."""
        fournisseur1 = MTFO.objects.create(RAISON_SOCIALE='Fournisseur 1')
        fournisseur2 = MTFO.objects.create(RAISON_SOCIALE='Fournisseur 2')

        self.assertTrue(fournisseur1.CODE.startswith('FOUR-'))
        self.assertTrue(fournisseur2.CODE.startswith('FOUR-'))
        self.assertNotEqual(fournisseur1.CODE, fournisseur2.CODE)

    def test_str_representation(self):
        """Test de la représentation string."""
        fournisseur = MTFO.objects.create(
            RAISON_SOCIALE='Dell Technologies'
        )
        self.assertIn('Dell Technologies', str(fournisseur))


class MTMTModelTests(TestCase):
    """Tests pour le modèle MTMT (Matériel)."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique',
            DUREE_AMORTISSEMENT=36
        )
        self.fournisseur = MTFO.objects.create(
            RAISON_SOCIALE='Dell Technologies'
        )

    def test_create_materiel(self):
        """Test de création d'un matériel."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='Ordinateur portable Dell',
            MARQUE='Dell',
            MODELE='Latitude 5520',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('750000'),
            FOURNISSEUR=self.fournisseur
        )
        self.assertIsNotNone(materiel.CODE_INTERNE)
        self.assertEqual(materiel.STATUT, 'DISPONIBLE')
        self.assertEqual(materiel.ETAT, 'NEUF')

    def test_code_auto_generation(self):
        """Test de génération automatique du code."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000')
        )
        expected_prefix = f"INFO-{timezone.now().year}"
        self.assertTrue(materiel.CODE_INTERNE.startswith(expected_prefix))

    def test_est_sous_garantie_true(self):
        """Test de garantie active."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000'),
            DATE_FIN_GARANTIE=date.today() + timedelta(days=365)
        )
        self.assertTrue(materiel.est_sous_garantie)

    def test_est_sous_garantie_false(self):
        """Test de garantie expirée."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today() - timedelta(days=400),
            PRIX_ACQUISITION=Decimal('500000'),
            DATE_FIN_GARANTIE=date.today() - timedelta(days=35)
        )
        self.assertFalse(materiel.est_sous_garantie)

    def test_valeur_residuelle_neuf(self):
        """Test de calcul de valeur résiduelle pour matériel neuf."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('600000')
        )
        # Matériel neuf, valeur résiduelle proche du prix d'acquisition
        self.assertGreater(materiel.valeur_residuelle, Decimal('0'))

    def test_valeur_residuelle_amorti(self):
        """Test de calcul de valeur résiduelle pour matériel amorti."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today() - timedelta(days=1500),  # ~50 mois
            PRIX_ACQUISITION=Decimal('600000')
        )
        # Matériel amorti (>36 mois), valeur résiduelle = 0
        self.assertEqual(materiel.valeur_residuelle, Decimal('0'))

    def test_age_mois(self):
        """Test de calcul de l'âge en mois."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today() - timedelta(days=90),  # ~3 mois
            PRIX_ACQUISITION=Decimal('500000')
        )
        self.assertGreaterEqual(materiel.age_mois, 2)
        self.assertLessEqual(materiel.age_mois, 4)

    def test_str_representation(self):
        """Test de la représentation string."""
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='Imprimante HP',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('150000')
        )
        self.assertIn('Imprimante HP', str(materiel))


class MTAFModelTests(TestCase):
    """Tests pour le modèle MTAF (Affectation)."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique'
        )
        self.materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000')
        )
        # Note: Dans un vrai test, il faudrait créer un employé ZY00
        # Pour ce test, on vérifie juste la structure du modèle

    def test_est_en_cours(self):
        """Test de vérification d'affectation en cours."""
        # Ce test nécessite un employé ZY00 réel
        # On vérifie juste que la propriété existe
        self.assertTrue(hasattr(MTAF, 'est_en_cours'))

    def test_est_en_retard(self):
        """Test de vérification de retard."""
        self.assertTrue(hasattr(MTAF, 'est_en_retard'))


class MTMVModelTests(TestCase):
    """Tests pour le modèle MTMV (Mouvement)."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique'
        )
        self.materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000')
        )

    def test_create_mouvement(self):
        """Test de création d'un mouvement."""
        mouvement = MTMV.objects.create(
            MATERIEL=self.materiel,
            TYPE_MOUVEMENT='ENTREE',
            DATE_MOUVEMENT=date.today(),
            MOTIF='Acquisition initiale'
        )
        self.assertIsNotNone(mouvement.REFERENCE)
        self.assertTrue(mouvement.REFERENCE.startswith('MV'))

    def test_reference_auto_generation(self):
        """Test de génération automatique de référence."""
        mouvement1 = MTMV.objects.create(
            MATERIEL=self.materiel,
            TYPE_MOUVEMENT='ENTREE',
            DATE_MOUVEMENT=date.today(),
            MOTIF='Mouvement 1'
        )
        mouvement2 = MTMV.objects.create(
            MATERIEL=self.materiel,
            TYPE_MOUVEMENT='TRANSFERT',
            DATE_MOUVEMENT=date.today(),
            MOTIF='Mouvement 2'
        )
        self.assertNotEqual(mouvement1.REFERENCE, mouvement2.REFERENCE)


class MTMAModelTests(TestCase):
    """Tests pour le modèle MTMA (Maintenance)."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique'
        )
        self.materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000')
        )

    def test_create_maintenance(self):
        """Test de création d'une maintenance."""
        maintenance = MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Nettoyage et mise à jour',
            DATE_PLANIFIEE=date.today() + timedelta(days=7)
        )
        self.assertIsNotNone(maintenance.REFERENCE)
        self.assertEqual(maintenance.STATUT, 'PLANIFIE')

    def test_cout_total(self):
        """Test du calcul du coût total."""
        maintenance = MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='CORRECTIVE',
            DESCRIPTION='Remplacement écran',
            DATE_PLANIFIEE=date.today(),
            COUT_PIECES=Decimal('50000'),
            COUT_MAIN_OEUVRE=Decimal('25000')
        )
        self.assertEqual(maintenance.cout_total, Decimal('75000'))

    def test_reference_auto_generation(self):
        """Test de génération automatique de référence."""
        maintenance = MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='REVISION',
            DESCRIPTION='Révision annuelle',
            DATE_PLANIFIEE=date.today()
        )
        self.assertTrue(maintenance.REFERENCE.startswith('MA'))


class MaterielViewsTests(TestCase):
    """Tests pour les vues du module matériel."""

    def setUp(self):
        """Configuration des tests."""
        self.client = Client()
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Créer les données de test
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique'
        )
        self.materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Test',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000')
        )

    def test_dashboard_requires_login(self):
        """Test que le dashboard nécessite une connexion."""
        response = self.client.get(reverse('materiel:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_liste_materiels_requires_login(self):
        """Test que la liste des matériels nécessite une connexion."""
        response = self.client.get(reverse('materiel:liste_materiels'))
        self.assertEqual(response.status_code, 302)

    def test_api_search_employes_requires_login(self):
        """Test que l'API de recherche nécessite une connexion."""
        response = self.client.get(
            reverse('materiel:api_search_employes'),
            {'q': 'test'}
        )
        self.assertEqual(response.status_code, 302)


class MaterielFormsTests(TestCase):
    """Tests pour les formulaires du module matériel."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique'
        )

    def test_mtca_form_valid(self):
        """Test de validation du formulaire catégorie."""
        from .forms import MTCAForm
        form_data = {
            'CODE': 'MOBIL',
            'LIBELLE': 'Mobilier',
            'DESCRIPTION': 'Meubles de bureau',
            'DUREE_AMORTISSEMENT': 60,
            'STATUT': True,
            'ORDRE': 1
        }
        form = MTCAForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_mtfo_form_valid(self):
        """Test de validation du formulaire fournisseur."""
        from .forms import MTFOForm
        form_data = {
            'RAISON_SOCIALE': 'Nouveau Fournisseur',
            'CONTACT': 'Jean Test',
            'TELEPHONE': '+225 07 00 00 00',
            'EMAIL': 'test@example.com',
            'STATUT': True
        }
        form = MTFOForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_mtmt_form_valid(self):
        """Test de validation du formulaire matériel."""
        from .forms import MTMTForm
        form_data = {
            'CATEGORIE': self.categorie.pk,
            'DESIGNATION': 'Nouveau PC',
            'DATE_ACQUISITION': date.today().isoformat(),
            'PRIX_ACQUISITION': '500000',
            'ETAT': 'NEUF'
        }
        form = MTMTForm(data=form_data)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())

    def test_affectation_form_requires_employe(self):
        """Test que le formulaire d'affectation requiert un employé."""
        from .forms import AffectationForm
        form_data = {
            'type_affectation': 'AFFECTATION',
            'motif': 'Test affectation'
        }
        form = AffectationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('employe_id', form.errors)

    def test_affectation_form_pret_requires_date_retour(self):
        """Test que le prêt requiert une date de retour."""
        from .forms import AffectationForm
        form_data = {
            'employe_id': 'EMP001',
            'type_affectation': 'PRET',
            'motif': 'Prêt temporaire'
        }
        form = AffectationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_retour_prevue', form.errors)

    def test_affectation_form_pret_with_valid_date(self):
        """Test du formulaire d'affectation prêt avec date valide."""
        from .forms import AffectationForm
        form_data = {
            'employe_id': 'EMP001',
            'type_affectation': 'PRET',
            'date_retour_prevue': (date.today() + timedelta(days=30)).isoformat(),
            'motif': 'Prêt temporaire'
        }
        form = AffectationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_reforme_form_valid(self):
        """Test de validation du formulaire de réforme."""
        from .forms import ReformeForm
        form_data = {
            'motif': 'Matériel obsolète',
            'valeur_residuelle': '10000'
        }
        form = ReformeForm(data=form_data)
        self.assertTrue(form.is_valid())


class MaterielIntegrationTests(TestCase):
    """Tests d'intégration pour le module matériel."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique',
            DUREE_AMORTISSEMENT=36
        )
        self.fournisseur = MTFO.objects.create(
            RAISON_SOCIALE='Dell Technologies'
        )

    def test_full_materiel_lifecycle(self):
        """Test du cycle de vie complet d'un matériel."""
        # 1. Création du matériel
        materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable Dell Latitude',
            MARQUE='Dell',
            MODELE='Latitude 5520',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('750000'),
            FOURNISSEUR=self.fournisseur,
            ETAT='NEUF',
            STATUT='DISPONIBLE'
        )
        self.assertEqual(materiel.STATUT, 'DISPONIBLE')
        self.assertIsNotNone(materiel.CODE_INTERNE)

        # 2. Création d'un mouvement d'entrée
        mouvement = MTMV.objects.create(
            MATERIEL=materiel,
            TYPE_MOUVEMENT='ENTREE',
            DATE_MOUVEMENT=date.today(),
            MOTIF='Acquisition initiale'
        )
        self.assertEqual(mouvement.TYPE_MOUVEMENT, 'ENTREE')

        # 3. Planification d'une maintenance
        maintenance = MTMA.objects.create(
            MATERIEL=materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Installation et configuration',
            DATE_PLANIFIEE=date.today() + timedelta(days=1)
        )
        self.assertEqual(maintenance.STATUT, 'PLANIFIE')

        # 4. Passage en maintenance
        materiel.STATUT = 'EN_MAINTENANCE'
        materiel.save()
        maintenance.STATUT = 'EN_COURS'
        maintenance.DATE_DEBUT = date.today()
        maintenance.save()

        self.assertEqual(materiel.STATUT, 'EN_MAINTENANCE')

        # 5. Fin de maintenance
        maintenance.STATUT = 'TERMINE'
        maintenance.DATE_FIN = date.today()
        maintenance.ETAT_APRES = 'BON'
        maintenance.save()

        materiel.STATUT = 'DISPONIBLE'
        materiel.ETAT = 'BON'
        materiel.save()

        self.assertEqual(materiel.STATUT, 'DISPONIBLE')
        self.assertEqual(materiel.ETAT, 'BON')

    def test_multiple_categories(self):
        """Test de création de plusieurs catégories."""
        categories_data = [
            ('MOBIL', 'Mobilier', 60),
            ('VEHIC', 'Véhicule', 48),
            ('TELEP', 'Téléphonie', 24),
        ]
        for code, libelle, duree in categories_data:
            cat = MTCA.objects.create(
                CODE=code,
                LIBELLE=libelle,
                DUREE_AMORTISSEMENT=duree
            )
            self.assertEqual(cat.CODE, code)

        self.assertEqual(MTCA.objects.count(), 4)  # 3 + 1 from setUp

    def test_materiel_by_category(self):
        """Test de récupération de matériels par catégorie."""
        # Créer plusieurs matériels
        for i in range(5):
            MTMT.objects.create(
                CATEGORIE=self.categorie,
                DESIGNATION=f'PC Test {i}',
                DATE_ACQUISITION=date.today(),
                PRIX_ACQUISITION=Decimal('400000')
            )

        materiels = MTMT.objects.filter(CATEGORIE=self.categorie)
        self.assertEqual(materiels.count(), 5)

    def test_fournisseur_with_materiels(self):
        """Test de relation fournisseur-matériels."""
        # Créer plusieurs matériels du même fournisseur
        for i in range(3):
            MTMT.objects.create(
                CATEGORIE=self.categorie,
                DESIGNATION=f'Équipement Dell {i}',
                DATE_ACQUISITION=date.today(),
                PRIX_ACQUISITION=Decimal('300000'),
                FOURNISSEUR=self.fournisseur
            )

        self.assertEqual(self.fournisseur.materiels_fournis.count(), 3)


# =============================================================================
# TESTS DES SERVICES
# =============================================================================

class MaterielServiceTests(TestCase):
    """Tests pour MaterielService."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique',
            DUREE_AMORTISSEMENT=36
        )
        self.fournisseur = MTFO.objects.create(
            RAISON_SOCIALE='Dell Technologies'
        )
        self.materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Portable Test',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000'),
            FOURNISSEUR=self.fournisseur
        )

    def test_service_existe(self):
        """Test que le service existe."""
        from materiel.services.materiel_service import MaterielService
        self.assertIsNotNone(MaterielService)

    def test_modifier_materiel(self):
        """Test de modification d'un matériel."""
        from materiel.services.materiel_service import MaterielService

        MaterielService.modifier_materiel(
            self.materiel,
            DESIGNATION='PC Portable Dell Latitude',
            MARQUE='Dell',
            MODELE='Latitude 5520'
        )

        self.materiel.refresh_from_db()
        self.assertEqual(self.materiel.DESIGNATION, 'PC Portable Dell Latitude')
        self.assertEqual(self.materiel.MARQUE, 'Dell')
        self.assertEqual(self.materiel.MODELE, 'Latitude 5520')

    def test_modifier_materiel_champs_non_modifiables(self):
        """Test que les champs non modifiables sont ignorés."""
        from materiel.services.materiel_service import MaterielService

        code_original = self.materiel.CODE_INTERNE
        MaterielService.modifier_materiel(
            self.materiel,
            CODE_INTERNE='NOUVEAU_CODE',  # Ne devrait pas être modifié
            DESIGNATION='Nouvelle désignation'
        )

        self.materiel.refresh_from_db()
        self.assertEqual(self.materiel.CODE_INTERNE, code_original)
        self.assertEqual(self.materiel.DESIGNATION, 'Nouvelle désignation')

    def test_get_materiels_sans_filtre(self):
        """Test de récupération de tous les matériels."""
        from materiel.services.materiel_service import MaterielService

        materiels = MaterielService.get_materiels()
        self.assertEqual(materiels.count(), 1)

    def test_get_materiels_par_categorie(self):
        """Test de récupération par catégorie."""
        from materiel.services.materiel_service import MaterielService

        autre_cat = MTCA.objects.create(CODE='MOBIL', LIBELLE='Mobilier')
        MTMT.objects.create(
            CATEGORIE=autre_cat,
            DESIGNATION='Bureau',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('200000')
        )

        materiels = MaterielService.get_materiels(categorie=self.categorie)
        self.assertEqual(materiels.count(), 1)
        self.assertEqual(materiels.first().DESIGNATION, 'PC Portable Test')

    def test_get_materiels_par_statut(self):
        """Test de récupération par statut."""
        from materiel.services.materiel_service import MaterielService

        materiels = MaterielService.get_materiels(statut='DISPONIBLE')
        self.assertEqual(materiels.count(), 1)

        materiels_affectes = MaterielService.get_materiels(statut='AFFECTE')
        self.assertEqual(materiels_affectes.count(), 0)

    def test_get_materiels_disponibles(self):
        """Test de récupération des matériels disponibles."""
        from materiel.services.materiel_service import MaterielService

        # Créer un matériel affecté
        MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Affecté',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('600000'),
            STATUT='AFFECTE'
        )

        disponibles = MaterielService.get_materiels_disponibles()
        self.assertEqual(disponibles.count(), 1)
        self.assertEqual(disponibles.first().DESIGNATION, 'PC Portable Test')

    def test_get_materiels_disponibles_par_categorie(self):
        """Test de récupération des disponibles par catégorie."""
        from materiel.services.materiel_service import MaterielService

        autre_cat = MTCA.objects.create(CODE='VEHIC', LIBELLE='Véhicule')
        MTMT.objects.create(
            CATEGORIE=autre_cat,
            DESIGNATION='Voiture',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('15000000'),
            STATUT='DISPONIBLE'
        )

        disponibles = MaterielService.get_materiels_disponibles(categorie=self.categorie)
        self.assertEqual(disponibles.count(), 1)

    def test_rechercher_materiel_par_designation(self):
        """Test de recherche par désignation."""
        from materiel.services.materiel_service import MaterielService

        resultats = MaterielService.rechercher_materiel('Portable')
        self.assertEqual(resultats.count(), 1)

    def test_rechercher_materiel_par_marque(self):
        """Test de recherche par marque."""
        from materiel.services.materiel_service import MaterielService

        self.materiel.MARQUE = 'Dell'
        self.materiel.save()

        resultats = MaterielService.rechercher_materiel('Dell')
        self.assertEqual(resultats.count(), 1)

    def test_rechercher_materiel_sans_resultat(self):
        """Test de recherche sans résultat."""
        from materiel.services.materiel_service import MaterielService

        resultats = MaterielService.rechercher_materiel('xyz123')
        self.assertEqual(resultats.count(), 0)

    def test_get_historique_materiel(self):
        """Test de récupération de l'historique."""
        from materiel.services.materiel_service import MaterielService

        historique = MaterielService.get_historique_materiel(self.materiel)
        self.assertIn('affectations', historique)
        self.assertIn('mouvements', historique)
        self.assertIn('maintenances', historique)

    def test_get_maintenances_planifiees(self):
        """Test de récupération des maintenances planifiées."""
        from materiel.services.materiel_service import MaterielService

        # Créer une maintenance planifiée
        MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Nettoyage',
            DATE_PLANIFIEE=date.today() + timedelta(days=7),
            STATUT='PLANIFIE'
        )

        maintenances = MaterielService.get_maintenances_planifiees(jours_a_venir=30)
        self.assertEqual(maintenances.count(), 1)

    def test_get_maintenances_planifiees_hors_delai(self):
        """Test de maintenances planifiées hors délai."""
        from materiel.services.materiel_service import MaterielService

        # Créer une maintenance planifiée dans 60 jours
        MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Révision',
            DATE_PLANIFIEE=date.today() + timedelta(days=60),
            STATUT='PLANIFIE'
        )

        maintenances = MaterielService.get_maintenances_planifiees(jours_a_venir=30)
        self.assertEqual(maintenances.count(), 0)


class MaterielServiceMaintenanceTests(TestCase):
    """Tests pour les opérations de maintenance du MaterielService."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique'
        )
        self.materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Test',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000')
        )

    def test_planifier_maintenance(self):
        """Test de planification d'une maintenance."""
        from materiel.services.materiel_service import MaterielService

        maintenance = MaterielService.planifier_maintenance(
            materiel=self.materiel,
            type_maintenance='PREVENTIVE',
            description='Nettoyage annuel',
            date_planifiee=date.today() + timedelta(days=7),
            demande_par=None
        )

        self.assertIsNotNone(maintenance)
        self.assertEqual(maintenance.STATUT, 'PLANIFIE')
        self.assertEqual(maintenance.TYPE_MAINTENANCE, 'PREVENTIVE')

    def test_demarrer_maintenance(self):
        """Test de démarrage d'une maintenance."""
        from materiel.services.materiel_service import MaterielService
        from django.core.exceptions import ValidationError

        maintenance = MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='CORRECTIVE',
            DESCRIPTION='Réparation écran',
            DATE_PLANIFIEE=date.today(),
            STATUT='PLANIFIE'
        )

        maintenance = MaterielService.demarrer_maintenance(maintenance)
        self.assertEqual(maintenance.STATUT, 'EN_COURS')
        self.assertIsNotNone(maintenance.DATE_DEBUT)

    def test_demarrer_maintenance_deja_en_cours(self):
        """Test de démarrage d'une maintenance déjà en cours."""
        from materiel.services.materiel_service import MaterielService
        from django.core.exceptions import ValidationError

        maintenance = MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='CORRECTIVE',
            DESCRIPTION='Réparation',
            DATE_PLANIFIEE=date.today(),
            STATUT='EN_COURS'
        )

        with self.assertRaises(ValidationError):
            MaterielService.demarrer_maintenance(maintenance)

    def test_terminer_maintenance(self):
        """Test de terminaison d'une maintenance."""
        from materiel.services.materiel_service import MaterielService

        maintenance = MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Révision',
            DATE_PLANIFIEE=date.today(),
            STATUT='EN_COURS',
            DATE_DEBUT=date.today()
        )

        maintenance = MaterielService.terminer_maintenance(
            maintenance=maintenance,
            date_fin=date.today(),
            resultat='Révision effectuée avec succès',
            etat_apres='BON',
            cout_pieces=Decimal('10000'),
            cout_main_oeuvre=Decimal('15000')
        )

        self.assertEqual(maintenance.STATUT, 'TERMINE')
        self.assertEqual(maintenance.ETAT_APRES, 'BON')
        self.assertEqual(maintenance.COUT_PIECES, Decimal('10000'))
        self.assertEqual(maintenance.COUT_MAIN_OEUVRE, Decimal('15000'))

        # Vérifier que le matériel est mis à jour
        self.materiel.refresh_from_db()
        self.assertEqual(self.materiel.ETAT, 'BON')
        self.assertEqual(self.materiel.STATUT, 'DISPONIBLE')

    def test_terminer_maintenance_deja_terminee(self):
        """Test de terminaison d'une maintenance déjà terminée."""
        from materiel.services.materiel_service import MaterielService
        from django.core.exceptions import ValidationError

        maintenance = MTMA.objects.create(
            MATERIEL=self.materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Révision',
            DATE_PLANIFIEE=date.today(),
            STATUT='TERMINE'
        )

        with self.assertRaises(ValidationError):
            MaterielService.terminer_maintenance(
                maintenance=maintenance,
                date_fin=date.today(),
                resultat='Test',
                etat_apres='BON'
            )


class MaterielServiceMouvementTests(TestCase):
    """Tests pour les opérations de mouvement du MaterielService."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique'
        )
        self.materiel = MTMT.objects.create(
            CATEGORIE=self.categorie,
            DESIGNATION='PC Test',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('500000')
        )

    def test_creer_mouvement_entree(self):
        """Test de création d'un mouvement d'entrée."""
        from materiel.services.materiel_service import MaterielService

        mouvement = MaterielService.creer_mouvement(
            materiel=self.materiel,
            type_mouvement='ENTREE',
            date_mouvement=date.today(),
            motif='Achat neuf',
            effectue_par=None
        )

        self.assertIsNotNone(mouvement)
        self.assertEqual(mouvement.TYPE_MOUVEMENT, 'ENTREE')
        self.assertTrue(mouvement.REFERENCE.startswith('MV'))

    def test_creer_mouvement_reforme_change_statut(self):
        """Test que la réforme change le statut du matériel."""
        from materiel.services.materiel_service import MaterielService

        MaterielService.creer_mouvement(
            materiel=self.materiel,
            type_mouvement='REFORME',
            date_mouvement=date.today(),
            motif='Obsolescence',
            effectue_par=None
        )

        self.materiel.refresh_from_db()
        self.assertEqual(self.materiel.STATUT, 'REFORME')
        self.assertEqual(self.materiel.ETAT, 'REFORME')

    def test_creer_mouvement_perte_change_statut(self):
        """Test que la perte change le statut du matériel."""
        from materiel.services.materiel_service import MaterielService

        MaterielService.creer_mouvement(
            materiel=self.materiel,
            type_mouvement='PERTE',
            date_mouvement=date.today(),
            motif='Vol',
            effectue_par=None
        )

        self.materiel.refresh_from_db()
        self.assertEqual(self.materiel.STATUT, 'PERDU')

    def test_reformer_materiel(self):
        """Test de réforme complète d'un matériel."""
        from materiel.services.materiel_service import MaterielService

        mouvement = MaterielService.reformer_materiel(
            materiel=self.materiel,
            date_reforme=date.today(),
            motif='Matériel obsolète - fin de vie',
            effectue_par=None,
            valeur_sortie=Decimal('50000')
        )

        self.assertIsNotNone(mouvement)
        self.assertEqual(mouvement.TYPE_MOUVEMENT, 'REFORME')
        self.assertEqual(mouvement.VALEUR_SORTIE, Decimal('50000'))

        self.materiel.refresh_from_db()
        self.assertEqual(self.materiel.STATUT, 'REFORME')


class StatistiquesMaterielServiceTests(TestCase):
    """Tests pour StatistiquesMaterielService."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = MTCA.objects.create(
            CODE='INFO',
            LIBELLE='Informatique',
            DUREE_AMORTISSEMENT=36
        )
        # Créer plusieurs matériels
        for i in range(5):
            MTMT.objects.create(
                CATEGORIE=self.categorie,
                DESIGNATION=f'PC Test {i}',
                DATE_ACQUISITION=date.today(),
                PRIX_ACQUISITION=Decimal('500000')
            )

    def test_service_existe(self):
        """Test que le service existe."""
        from materiel.services.statistiques_service import StatistiquesMaterielService
        self.assertIsNotNone(StatistiquesMaterielService)

    def test_get_stats_globales(self):
        """Test des statistiques globales."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        stats = StatistiquesMaterielService.get_stats_globales()

        self.assertEqual(stats['total_materiels'], 5)
        self.assertEqual(stats['valeur_totale'], Decimal('2500000'))
        self.assertEqual(stats['disponibles'], 5)
        self.assertEqual(stats['affectes'], 0)
        self.assertIn('par_statut', stats)
        self.assertIn('par_etat', stats)

    def test_get_stats_globales_avec_statuts_varies(self):
        """Test des statistiques avec différents statuts."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        # Modifier les statuts de certains matériels
        materiels = MTMT.objects.all()
        materiels[0].STATUT = 'AFFECTE'
        materiels[0].save()
        materiels[1].STATUT = 'EN_MAINTENANCE'
        materiels[1].save()

        stats = StatistiquesMaterielService.get_stats_globales()

        self.assertEqual(stats['disponibles'], 3)
        self.assertEqual(stats['affectes'], 1)
        self.assertEqual(stats['en_maintenance'], 1)

    def test_get_stats_par_categorie(self):
        """Test des statistiques par catégorie."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        # Ajouter une autre catégorie
        autre_cat = MTCA.objects.create(CODE='MOBIL', LIBELLE='Mobilier')
        MTMT.objects.create(
            CATEGORIE=autre_cat,
            DESIGNATION='Bureau',
            DATE_ACQUISITION=date.today(),
            PRIX_ACQUISITION=Decimal('200000')
        )

        stats = StatistiquesMaterielService.get_stats_par_categorie()

        self.assertEqual(len(stats), 2)
        # Vérifier la catégorie INFO
        info_stats = next(s for s in stats if s['categorie'].CODE == 'INFO')
        self.assertEqual(info_stats['total'], 5)
        self.assertEqual(info_stats['valeur_totale'], Decimal('2500000'))

    def test_get_couts_maintenance(self):
        """Test des coûts de maintenance."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        materiel = MTMT.objects.first()

        # Créer des maintenances terminées
        MTMA.objects.create(
            MATERIEL=materiel,
            TYPE_MAINTENANCE='CORRECTIVE',
            DESCRIPTION='Réparation',
            DATE_PLANIFIEE=date.today(),
            DATE_FIN=date.today(),
            STATUT='TERMINE',
            COUT_PIECES=Decimal('20000'),
            COUT_MAIN_OEUVRE=Decimal('15000')
        )
        MTMA.objects.create(
            MATERIEL=materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Révision',
            DATE_PLANIFIEE=date.today(),
            DATE_FIN=date.today(),
            STATUT='TERMINE',
            COUT_PIECES=Decimal('5000'),
            COUT_MAIN_OEUVRE=Decimal('10000')
        )

        stats = StatistiquesMaterielService.get_couts_maintenance()

        self.assertEqual(stats['nb_maintenances'], 2)
        self.assertEqual(stats['cout_pieces'], Decimal('25000'))
        self.assertEqual(stats['cout_main_oeuvre'], Decimal('25000'))
        self.assertEqual(stats['cout_total'], Decimal('50000'))
        self.assertIn('par_type', stats)

    def test_get_valeur_parc(self):
        """Test du calcul de valeur du parc."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        stats = StatistiquesMaterielService.get_valeur_parc()

        self.assertEqual(stats['valeur_acquisition'], Decimal('2500000'))
        self.assertIn('valeur_residuelle', stats)
        self.assertIn('amortissement_cumule', stats)
        self.assertIn('taux_amortissement', stats)

    def test_get_alertes_sans_alertes(self):
        """Test des alertes quand il n'y en a pas."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        alertes = StatistiquesMaterielService.get_alertes()

        self.assertEqual(len(alertes['garanties_expirant']), 0)
        self.assertEqual(len(alertes['prets_retard']), 0)
        self.assertEqual(len(alertes['maintenances_retard']), 0)
        self.assertEqual(alertes['nb_alertes'], 0)

    def test_get_alertes_garantie_expirant(self):
        """Test des alertes pour garantie expirant."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        materiel = MTMT.objects.first()
        materiel.DATE_FIN_GARANTIE = date.today() + timedelta(days=15)
        materiel.save()

        alertes = StatistiquesMaterielService.get_alertes()

        self.assertEqual(len(alertes['garanties_expirant']), 1)
        self.assertGreater(alertes['nb_alertes'], 0)

    def test_get_alertes_maintenance_retard(self):
        """Test des alertes pour maintenance en retard."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        materiel = MTMT.objects.first()
        MTMA.objects.create(
            MATERIEL=materiel,
            TYPE_MAINTENANCE='PREVENTIVE',
            DESCRIPTION='Révision en retard',
            DATE_PLANIFIEE=date.today() - timedelta(days=10),
            STATUT='PLANIFIE'
        )

        alertes = StatistiquesMaterielService.get_alertes()

        self.assertEqual(len(alertes['maintenances_retard']), 1)

    def test_get_top_fournisseurs(self):
        """Test de récupération des top fournisseurs."""
        from materiel.services.statistiques_service import StatistiquesMaterielService

        fournisseur = MTFO.objects.create(RAISON_SOCIALE='Dell')
        for mat in MTMT.objects.all()[:3]:
            mat.FOURNISSEUR = fournisseur
            mat.save()

        top = StatistiquesMaterielService.get_top_fournisseurs(limit=5)

        self.assertEqual(len(top), 1)
        self.assertEqual(top[0].nb_materiels, 3)
        self.assertEqual(top[0].valeur_totale, Decimal('1500000'))
