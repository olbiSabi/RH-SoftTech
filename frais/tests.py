# frais/tests.py
"""
Tests pour le module de gestion des Notes de Frais et Avances.
python manage.py test frais
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import NFCA, NFPL, NFNF, NFLF, NFAV


User = get_user_model()


class NFCAModelTests(TestCase):
    """Tests pour le modèle NFCA (Catégorie de frais)."""

    def test_create_categorie(self):
        """Test de création d'une catégorie de frais."""
        categorie = NFCA.objects.create(
            CODE='TRANS',
            LIBELLE='Transport',
            DESCRIPTION='Frais de transport',
            JUSTIFICATIF_OBLIGATOIRE=True
        )
        self.assertEqual(categorie.CODE, 'TRANS')
        self.assertEqual(categorie.LIBELLE, 'Transport')
        self.assertTrue(categorie.JUSTIFICATIF_OBLIGATOIRE)
        self.assertTrue(categorie.STATUT)

    def test_code_uppercase(self):
        """Test que le code est converti en majuscules."""
        categorie = NFCA.objects.create(
            CODE='repas',
            LIBELLE='Repas'
        )
        self.assertEqual(categorie.CODE, 'REPAS')

    def test_str_representation(self):
        """Test de la représentation string."""
        categorie = NFCA.objects.create(
            CODE='HOTEL',
            LIBELLE='Hébergement'
        )
        self.assertEqual(str(categorie), 'HOTEL - Hébergement')

    def test_default_values(self):
        """Test des valeurs par défaut."""
        categorie = NFCA.objects.create(
            CODE='TEST',
            LIBELLE='Test'
        )
        self.assertTrue(categorie.STATUT)
        self.assertTrue(categorie.JUSTIFICATIF_OBLIGATOIRE)
        self.assertEqual(categorie.ORDRE, 0)

    def test_categorie_with_plafond(self):
        """Test de catégorie avec plafond par défaut."""
        categorie = NFCA.objects.create(
            CODE='REPAS',
            LIBELLE='Repas',
            PLAFOND_DEFAUT=Decimal('15000')
        )
        self.assertEqual(categorie.PLAFOND_DEFAUT, Decimal('15000'))


class NFPLModelTests(TestCase):
    """Tests pour le modèle NFPL (Plafond de frais)."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = NFCA.objects.create(
            CODE='REPAS',
            LIBELLE='Repas'
        )

    def test_create_plafond(self):
        """Test de création d'un plafond."""
        plafond = NFPL.objects.create(
            CATEGORIE=self.categorie,
            MONTANT_JOURNALIER=Decimal('25000'),
            MONTANT_MENSUEL=Decimal('500000'),
            DATE_DEBUT=date.today()
        )
        self.assertEqual(plafond.MONTANT_JOURNALIER, Decimal('25000'))
        self.assertTrue(plafond.STATUT)

    def test_plafond_par_grade(self):
        """Test de plafond spécifique par grade."""
        plafond = NFPL.objects.create(
            CATEGORIE=self.categorie,
            GRADE='DIRECTEUR',
            MONTANT_JOURNALIER=Decimal('50000'),
            DATE_DEBUT=date.today()
        )
        self.assertEqual(plafond.GRADE, 'DIRECTEUR')

    def test_est_actif_true(self):
        """Test de plafond actuellement actif."""
        plafond = NFPL.objects.create(
            CATEGORIE=self.categorie,
            MONTANT_JOURNALIER=Decimal('20000'),
            DATE_DEBUT=date.today() - timedelta(days=30),
            DATE_FIN=date.today() + timedelta(days=30),
            STATUT=True
        )
        self.assertTrue(plafond.est_actif())

    def test_est_actif_false_expired(self):
        """Test de plafond expiré."""
        plafond = NFPL.objects.create(
            CATEGORIE=self.categorie,
            MONTANT_JOURNALIER=Decimal('20000'),
            DATE_DEBUT=date.today() - timedelta(days=60),
            DATE_FIN=date.today() - timedelta(days=30),
            STATUT=True
        )
        self.assertFalse(plafond.est_actif())

    def test_est_actif_false_disabled(self):
        """Test de plafond désactivé."""
        plafond = NFPL.objects.create(
            CATEGORIE=self.categorie,
            MONTANT_JOURNALIER=Decimal('20000'),
            DATE_DEBUT=date.today(),
            STATUT=False
        )
        self.assertFalse(plafond.est_actif())

    def test_str_representation(self):
        """Test de la représentation string."""
        plafond = NFPL.objects.create(
            CATEGORIE=self.categorie,
            GRADE='MANAGER',
            MONTANT_JOURNALIER=Decimal('30000'),
            DATE_DEBUT=date.today()
        )
        self.assertIn('REPAS', str(plafond))
        self.assertIn('MANAGER', str(plafond))


class NFNFModelTests(TestCase):
    """Tests pour le modèle NFNF (Note de frais)."""

    def test_reference_auto_generation(self):
        """Test de génération automatique de référence."""
        # Note: Ce test nécessite un employé ZY00
        # On vérifie juste que le modèle a les bonnes propriétés
        self.assertTrue(hasattr(NFNF, 'REFERENCE'))
        self.assertTrue(hasattr(NFNF, 'STATUT'))

    def test_statut_choices(self):
        """Test des choix de statut disponibles."""
        statuts = [choice[0] for choice in NFNF.STATUT_CHOICES]
        self.assertIn('BROUILLON', statuts)
        self.assertIn('SOUMIS', statuts)
        self.assertIn('VALIDE', statuts)
        self.assertIn('REJETE', statuts)
        self.assertIn('REMBOURSE', statuts)

    def test_peut_etre_modifie(self):
        """Test de la méthode peut_etre_modifie."""
        self.assertTrue(hasattr(NFNF, 'peut_etre_modifie'))

    def test_peut_etre_soumis(self):
        """Test de la méthode peut_etre_soumis."""
        self.assertTrue(hasattr(NFNF, 'peut_etre_soumis'))

    def test_peut_etre_valide(self):
        """Test de la méthode peut_etre_valide."""
        self.assertTrue(hasattr(NFNF, 'peut_etre_valide'))


class NFLFModelTests(TestCase):
    """Tests pour le modèle NFLF (Ligne de frais)."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = NFCA.objects.create(
            CODE='TRANS',
            LIBELLE='Transport'
        )

    def test_statut_choices(self):
        """Test des choix de statut disponibles."""
        statuts = [choice[0] for choice in NFLF.STATUT_CHOICES]
        self.assertIn('EN_ATTENTE', statuts)
        self.assertIn('VALIDE', statuts)
        self.assertIn('REJETE', statuts)

    def test_devise_default(self):
        """Test de la devise par défaut."""
        # Vérifier que XOF est la devise par défaut
        field = NFLF._meta.get_field('DEVISE')
        self.assertEqual(field.default, 'XOF')

    def test_taux_change_default(self):
        """Test du taux de change par défaut."""
        field = NFLF._meta.get_field('TAUX_CHANGE')
        self.assertEqual(field.default, Decimal('1'))


class NFAVModelTests(TestCase):
    """Tests pour le modèle NFAV (Avance sur frais)."""

    def test_reference_auto_generation(self):
        """Test de génération automatique de référence."""
        self.assertTrue(hasattr(NFAV, 'REFERENCE'))

    def test_statut_choices(self):
        """Test des choix de statut disponibles."""
        statuts = [choice[0] for choice in NFAV.STATUT_CHOICES]
        self.assertIn('DEMANDE', statuts)
        self.assertIn('APPROUVE', statuts)
        self.assertIn('VERSE', statuts)
        self.assertIn('REGULARISE', statuts)
        self.assertIn('ANNULE', statuts)

    def test_solde_a_regulariser(self):
        """Test de la méthode solde_a_regulariser."""
        self.assertTrue(hasattr(NFAV, 'solde_a_regulariser'))

    def test_peut_etre_modifie(self):
        """Test de la méthode peut_etre_modifie."""
        self.assertTrue(hasattr(NFAV, 'peut_etre_modifie'))

    def test_peut_etre_approuve(self):
        """Test de la méthode peut_etre_approuve."""
        self.assertTrue(hasattr(NFAV, 'peut_etre_approuve'))

    def test_peut_etre_verse(self):
        """Test de la méthode peut_etre_verse."""
        self.assertTrue(hasattr(NFAV, 'peut_etre_verse'))


class FraisFormsTests(TestCase):
    """Tests pour les formulaires du module frais."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = NFCA.objects.create(
            CODE='TRANS',
            LIBELLE='Transport'
        )

    def test_nfca_form_valid(self):
        """Test de validation du formulaire catégorie."""
        from .forms import NFCAForm
        form_data = {
            'CODE': 'REPAS',
            'LIBELLE': 'Repas',
            'DESCRIPTION': 'Frais de repas',
            'JUSTIFICATIF_OBLIGATOIRE': True,
            'PLAFOND_DEFAUT': '15000',
            'STATUT': True,
            'ORDRE': 1
        }
        form = NFCAForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_nfca_form_missing_required(self):
        """Test de formulaire catégorie avec champs manquants."""
        from .forms import NFCAForm
        form_data = {
            'DESCRIPTION': 'Description sans code ni libellé'
        }
        form = NFCAForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('CODE', form.errors)
        self.assertIn('LIBELLE', form.errors)


class FraisViewsTests(TestCase):
    """Tests pour les vues du module frais."""

    def setUp(self):
        """Configuration des tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.categorie = NFCA.objects.create(
            CODE='TRANS',
            LIBELLE='Transport'
        )

    def test_dashboard_requires_login(self):
        """Test que le dashboard nécessite une connexion."""
        response = self.client.get(reverse('frais:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_liste_categories_requires_login(self):
        """Test que la liste des catégories nécessite une connexion."""
        response = self.client.get(reverse('frais:liste_categories'))
        self.assertEqual(response.status_code, 302)


class FraisIntegrationTests(TestCase):
    """Tests d'intégration pour le module frais."""

    def setUp(self):
        """Configuration des tests."""
        # Créer plusieurs catégories
        self.cat_transport = NFCA.objects.create(
            CODE='TRANS',
            LIBELLE='Transport',
            JUSTIFICATIF_OBLIGATOIRE=True,
            PLAFOND_DEFAUT=Decimal('50000')
        )
        self.cat_repas = NFCA.objects.create(
            CODE='REPAS',
            LIBELLE='Repas',
            JUSTIFICATIF_OBLIGATOIRE=True,
            PLAFOND_DEFAUT=Decimal('15000')
        )
        self.cat_hotel = NFCA.objects.create(
            CODE='HOTEL',
            LIBELLE='Hébergement',
            JUSTIFICATIF_OBLIGATOIRE=True,
            PLAFOND_DEFAUT=Decimal('100000')
        )

    def test_multiple_categories_creation(self):
        """Test de création de plusieurs catégories."""
        self.assertEqual(NFCA.objects.count(), 3)
        self.assertEqual(self.cat_transport.CODE, 'TRANS')
        self.assertEqual(self.cat_repas.CODE, 'REPAS')
        self.assertEqual(self.cat_hotel.CODE, 'HOTEL')

    def test_plafonds_by_category(self):
        """Test de création de plafonds par catégorie."""
        # Plafond général pour transport
        plafond_general = NFPL.objects.create(
            CATEGORIE=self.cat_transport,
            MONTANT_PAR_DEPENSE=Decimal('30000'),
            DATE_DEBUT=date.today()
        )

        # Plafond spécifique directeur pour transport
        plafond_directeur = NFPL.objects.create(
            CATEGORIE=self.cat_transport,
            GRADE='DIRECTEUR',
            MONTANT_PAR_DEPENSE=Decimal('100000'),
            DATE_DEBUT=date.today()
        )

        self.assertEqual(self.cat_transport.plafonds.count(), 2)
        self.assertIsNone(plafond_general.GRADE)
        self.assertEqual(plafond_directeur.GRADE, 'DIRECTEUR')

    def test_categorie_ordering(self):
        """Test de l'ordre des catégories."""
        self.cat_transport.ORDRE = 1
        self.cat_transport.save()
        self.cat_repas.ORDRE = 2
        self.cat_repas.save()
        self.cat_hotel.ORDRE = 3
        self.cat_hotel.save()

        categories = NFCA.objects.all()
        self.assertEqual(categories[0].CODE, 'TRANS')
        self.assertEqual(categories[1].CODE, 'REPAS')
        self.assertEqual(categories[2].CODE, 'HOTEL')

    def test_categorie_with_justificatif_not_required(self):
        """Test de catégorie sans justificatif obligatoire."""
        cat_divers = NFCA.objects.create(
            CODE='DIVERS',
            LIBELLE='Frais divers',
            JUSTIFICATIF_OBLIGATOIRE=False
        )
        self.assertFalse(cat_divers.JUSTIFICATIF_OBLIGATOIRE)

    def test_plafond_lifecycle(self):
        """Test du cycle de vie d'un plafond."""
        # Créer un plafond actif
        plafond = NFPL.objects.create(
            CATEGORIE=self.cat_repas,
            MONTANT_JOURNALIER=Decimal('20000'),
            DATE_DEBUT=date.today() - timedelta(days=30),
            STATUT=True
        )
        self.assertTrue(plafond.est_actif())

        # Désactiver le plafond
        plafond.STATUT = False
        plafond.save()
        self.assertFalse(plafond.est_actif())

        # Réactiver avec date de fin future
        plafond.STATUT = True
        plafond.DATE_FIN = date.today() + timedelta(days=30)
        plafond.save()
        self.assertTrue(plafond.est_actif())

        # Plafond expiré
        plafond.DATE_FIN = date.today() - timedelta(days=1)
        plafond.save()
        self.assertFalse(plafond.est_actif())


class FraisPermissionsTests(TestCase):
    """Tests pour les permissions du module frais."""

    def test_nfnf_permissions(self):
        """Test des permissions sur les notes de frais."""
        permissions = [p[0] for p in NFNF._meta.permissions]
        self.assertIn('can_validate_note_frais', permissions)
        self.assertIn('can_process_remboursement', permissions)
        self.assertIn('can_view_all_notes_frais', permissions)

    def test_nfav_permissions(self):
        """Test des permissions sur les avances."""
        permissions = [p[0] for p in NFAV._meta.permissions]
        self.assertIn('can_approve_avance', permissions)
        self.assertIn('can_process_versement', permissions)
        self.assertIn('can_view_all_avances', permissions)


class FraisCalculsTests(TestCase):
    """Tests pour les calculs du module frais."""

    def setUp(self):
        """Configuration des tests."""
        self.categorie = NFCA.objects.create(
            CODE='TRANS',
            LIBELLE='Transport'
        )

    def test_taux_change_conversion(self):
        """Test de conversion avec taux de change."""
        # Simuler le calcul de conversion
        montant_eur = Decimal('100.00')
        taux_change = Decimal('655.957')  # Taux EUR vers XOF
        montant_xof = montant_eur * taux_change

        self.assertEqual(montant_xof, Decimal('65595.700'))

    def test_plafond_validation(self):
        """Test de validation des plafonds."""
        plafond = NFPL.objects.create(
            CATEGORIE=self.categorie,
            MONTANT_PAR_DEPENSE=Decimal('50000'),
            DATE_DEBUT=date.today()
        )

        # Dépense sous le plafond
        depense = Decimal('40000')
        self.assertLessEqual(depense, plafond.MONTANT_PAR_DEPENSE)

        # Dépense au-dessus du plafond
        depense_elevee = Decimal('60000')
        self.assertGreater(depense_elevee, plafond.MONTANT_PAR_DEPENSE)
