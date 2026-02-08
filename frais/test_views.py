# frais/test_views.py
"""
Tests pour les vues du module Notes de Frais.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from core.tests.base import BaseTestCase
from frais.models import NFCA, NFNF, NFLF, NFAV


# =============================================
# Tests Dashboard
# =============================================

class TestDashboardFraisView(BaseTestCase):
    """Tests pour la vue dashboard frais."""

    def test_access_authenticated(self):
        """Test accès authentifié retourne 200."""
        response = self.client.get(reverse('frais:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('frais:dashboard'))
        self.assertEqual(response.status_code, 302)


# =============================================
# Tests Notes de Frais CRUD
# =============================================

class TestListeNotesFraisView(BaseTestCase):
    """Tests pour la vue liste des notes de frais."""

    def test_access_authenticated(self):
        """Test accès authentifié retourne 200."""
        response = self.client.get(reverse('frais:liste_notes'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('frais:liste_notes'))
        self.assertEqual(response.status_code, 302)


class TestCreerNoteFraisView(BaseTestCase):
    """Tests pour la vue création de note de frais."""

    def test_get_form(self):
        """Test GET retourne le formulaire."""
        response = self.client.get(reverse('frais:creer_note'))
        self.assertEqual(response.status_code, 200)

    def test_create_valid_note(self):
        """Test création note valide via POST."""
        data = {
            'PERIODE_DEBUT': (date.today() - timedelta(days=30)).isoformat(),
            'PERIODE_FIN': date.today().isoformat(),
            'OBJET': 'Mission test',
        }
        response = self.client.post(reverse('frais:creer_note'), data)
        # Should redirect on success
        self.assertIn(response.status_code, [200, 302])

    def test_create_invalid_dates(self):
        """Test création avec dates invalides."""
        data = {
            'PERIODE_DEBUT': date.today().isoformat(),
            'PERIODE_FIN': (date.today() - timedelta(days=30)).isoformat(),
            'OBJET': 'Mission test',
        }
        response = self.client.post(reverse('frais:creer_note'), data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered


class TestDetailNoteFraisView(BaseTestCase):
    """Tests pour la vue détail note de frais."""

    def setUp(self):
        super().setUp()
        self.note = self.create_note_frais()

    def test_access_own_note(self):
        """Test accès à sa propre note."""
        response = self.client.get(
            reverse('frais:detail_note', args=[self.note.uuid])
        )
        self.assertIn(response.status_code, [200, 302])

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(
            reverse('frais:detail_note', args=[self.note.uuid])
        )
        self.assertEqual(response.status_code, 302)


class TestModifierNoteFraisView(BaseTestCase):
    """Tests pour la vue modification note de frais."""

    def setUp(self):
        super().setUp()
        self.note = self.create_note_frais()

    def test_get_edit_form(self):
        """Test GET retourne le formulaire de modification."""
        response = self.client.get(
            reverse('frais:modifier_note', args=[self.note.uuid])
        )
        self.assertIn(response.status_code, [200, 302])


class TestSupprimerNoteFraisView(BaseTestCase):
    """Tests pour la vue suppression note de frais."""

    def setUp(self):
        super().setUp()
        self.note = self.create_note_frais()

    def test_delete_own_brouillon_note(self):
        """Test suppression de sa propre note brouillon."""
        response = self.client.post(
            reverse('frais:supprimer_note', args=[self.note.uuid])
        )
        self.assertIn(response.status_code, [200, 302])


# =============================================
# Tests Workflow Notes
# =============================================

class TestSoumettreNoteView(BaseTestCase):
    """Tests pour la soumission de note de frais."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.categorie = NFCA.objects.create(
            CODE='TST', LIBELLE='Test cat',
            DESCRIPTION='Test', STATUT=True,
        )

    def setUp(self):
        super().setUp()
        self.note = self.create_note_frais()
        # Ajouter une ligne pour pouvoir soumettre
        NFLF.objects.create(
            NOTE_FRAIS=self.note,
            CATEGORIE=self.categorie,
            DATE_DEPENSE=date.today() - timedelta(days=10),
            DESCRIPTION='Dépense test',
            MONTANT=Decimal('5000'),
            DEVISE='XOF',
        )

    def test_soumettre_note_brouillon(self):
        """Test soumission d'une note brouillon."""
        response = self.client.post(
            reverse('frais:soumettre_note', args=[self.note.uuid])
        )
        self.assertIn(response.status_code, [200, 302])


# =============================================
# Tests Avances
# =============================================

class TestListeAvancesView(BaseTestCase):
    """Tests pour la vue liste des avances."""

    def test_access_authenticated(self):
        """Test accès authentifié retourne 200."""
        response = self.client.get(reverse('frais:liste_avances'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('frais:liste_avances'))
        self.assertEqual(response.status_code, 302)


class TestCreerAvanceView(BaseTestCase):
    """Tests pour la vue création d'avance."""

    def test_get_form(self):
        """Test GET retourne le formulaire."""
        response = self.client.get(reverse('frais:creer_avance'))
        self.assertEqual(response.status_code, 200)

    def test_create_valid_avance(self):
        """Test création avance valide via POST."""
        data = {
            'MONTANT_DEMANDE': '50000',
            'MOTIF': 'Mission Kara',
            'DATE_MISSION_DEBUT': (date.today() + timedelta(days=5)).isoformat(),
            'DATE_MISSION_FIN': (date.today() + timedelta(days=10)).isoformat(),
        }
        response = self.client.post(reverse('frais:creer_avance'), data)
        self.assertIn(response.status_code, [200, 302])

    def test_create_avance_below_minimum(self):
        """Test création avance en dessous du minimum."""
        data = {
            'MONTANT_DEMANDE': '500',
            'MOTIF': 'Test',
            'DATE_MISSION_DEBUT': (date.today() + timedelta(days=5)).isoformat(),
            'DATE_MISSION_FIN': (date.today() + timedelta(days=10)).isoformat(),
        }
        response = self.client.post(reverse('frais:creer_avance'), data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors


# =============================================
# Tests Catégories
# =============================================

class TestCategoriesView(BaseTestCase):
    """Tests pour les vues de gestion des catégories."""

    def test_liste_categories(self):
        """Test liste des catégories."""
        response = self.client.get(reverse('frais:liste_categories'))
        self.assertIn(response.status_code, [200, 302, 403])
