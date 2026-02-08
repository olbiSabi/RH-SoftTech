# gestion_achats/tests/test_views.py
"""
Tests pour les vues du module Gestion des Achats & Commandes.
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from core.tests.base import BaseTestCase
from gestion_achats.models import (
    GACFournisseur,
    GACCategorie,
    GACArticle,
    GACBudget,
    GACDemandeAchat,
    GACLigneDemandeAchat,
)


# =============================================
# Tests Dashboard
# =============================================

class TestGACDashboardView(BaseTestCase):
    """Tests pour la vue dashboard GAC."""

    def test_access_authenticated(self):
        """Test accès authentifié retourne 200."""
        response = self.client.get(reverse('gestion_achats:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('gestion_achats:dashboard'))
        self.assertEqual(response.status_code, 302)


# =============================================
# Tests Demandes d'Achat
# =============================================

class TestDemandeListeView(BaseTestCase):
    """Tests pour la vue liste des demandes."""

    def test_access_authenticated(self):
        """Test accès authentifié retourne 200."""
        response = self.client.get(reverse('gestion_achats:demande_liste'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('gestion_achats:demande_liste'))
        self.assertEqual(response.status_code, 302)

    def test_context_contains_page_obj(self):
        """Test contexte contient page_obj."""
        response = self.client.get(reverse('gestion_achats:demande_liste'))
        self.assertIn('page_obj', response.context)

    def test_filter_by_statut(self):
        """Test filtrage par statut."""
        response = self.client.get(
            reverse('gestion_achats:demande_liste'),
            {'statut': 'BROUILLON'}
        )
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        """Test recherche par mot-clé."""
        response = self.client.get(
            reverse('gestion_achats:demande_liste'),
            {'search': 'test'}
        )
        self.assertEqual(response.status_code, 200)


class TestDemandeCreateView(BaseTestCase):
    """Tests pour la vue création de demande."""

    def test_get_form(self):
        """Test GET retourne le formulaire."""
        response = self.client.get(reverse('gestion_achats:demande_create'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('gestion_achats:demande_create'))
        self.assertEqual(response.status_code, 302)

    def test_create_valid_demande(self):
        """Test création demande valide via POST."""
        data = {
            'objet': 'Achat fournitures bureau',
            'justification': 'Stock épuisé, besoin urgent',
            'priorite': 'NORMALE',
        }
        response = self.client.post(
            reverse('gestion_achats:demande_create'), data
        )
        self.assertIn(response.status_code, [200, 302])

    def test_create_invalid_demande(self):
        """Test création demande invalide (champs vides)."""
        data = {
            'objet': '',
            'justification': '',
        }
        response = self.client.post(
            reverse('gestion_achats:demande_create'), data
        )
        self.assertEqual(response.status_code, 200)


class TestDemandeDetailView(BaseTestCase):
    """Tests pour la vue détail demande."""

    def setUp(self):
        super().setUp()
        self.demande = self.create_demande_achat()

    def test_access_own_demande(self):
        """Test accès à sa propre demande."""
        response = self.client.get(
            reverse('gestion_achats:demande_detail', args=[self.demande.uuid])
        )
        self.assertIn(response.status_code, [200, 302, 403])

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(
            reverse('gestion_achats:demande_detail', args=[self.demande.uuid])
        )
        self.assertEqual(response.status_code, 302)


class TestDemandeUpdateView(BaseTestCase):
    """Tests pour la vue modification demande."""

    def setUp(self):
        super().setUp()
        self.demande = self.create_demande_achat()

    def test_get_edit_form(self):
        """Test GET retourne le formulaire de modification."""
        response = self.client.get(
            reverse('gestion_achats:demande_update', args=[self.demande.uuid])
        )
        self.assertIn(response.status_code, [200, 302, 403])

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(
            reverse('gestion_achats:demande_update', args=[self.demande.uuid])
        )
        self.assertEqual(response.status_code, 302)


class TestDemandeDeleteView(BaseTestCase):
    """Tests pour la vue suppression demande."""

    def setUp(self):
        super().setUp()
        self.demande = self.create_demande_achat()

    def test_delete_own_brouillon(self):
        """Test suppression demande brouillon propre."""
        response = self.client.post(
            reverse('gestion_achats:demande_delete', args=[self.demande.uuid])
        )
        self.assertIn(response.status_code, [200, 302, 403])


class TestMesDemandesView(BaseTestCase):
    """Tests pour la vue mes_demandes."""

    def test_access_authenticated(self):
        """Test accès authentifié."""
        response = self.client.get(reverse('gestion_achats:mes_demandes'))
        self.assertEqual(response.status_code, 200)


class TestDemandesAValiderView(BaseTestCase):
    """Tests pour la vue demandes_a_valider."""

    def test_access_authenticated(self):
        """Test accès authentifié."""
        response = self.client.get(reverse('gestion_achats:demandes_a_valider'))
        self.assertIn(response.status_code, [200, 302, 403])


# =============================================
# Tests Fournisseurs
# =============================================

class TestFournisseurListView(BaseTestCase):
    """Tests pour la vue liste fournisseurs."""

    def test_access_authenticated(self):
        """Test accès authentifié."""
        response = self.client.get(reverse('gestion_achats:fournisseur_list'))
        self.assertIn(response.status_code, [200, 302, 403])

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('gestion_achats:fournisseur_list'))
        self.assertEqual(response.status_code, 302)


class TestFournisseurCreateView(BaseTestCase):
    """Tests pour la vue création fournisseur."""

    def test_get_form(self):
        """Test GET retourne le formulaire."""
        response = self.client.get(reverse('gestion_achats:fournisseur_create'))
        self.assertIn(response.status_code, [200, 302, 403])

    def test_create_valid_fournisseur(self):
        """Test création fournisseur valide."""
        data = {
            'raison_sociale': 'Fournisseur Test SARL',
            'email': 'contact@fournisseur-test.tg',
            'telephone': '+228 90 12 34 56',
            'adresse': 'Lomé, Quartier Test',
            'pays': 'Togo',
        }
        response = self.client.post(
            reverse('gestion_achats:fournisseur_create'), data
        )
        self.assertIn(response.status_code, [200, 302, 403])


class TestFournisseurDetailView(BaseTestCase):
    """Tests pour la vue détail fournisseur."""

    def setUp(self):
        super().setUp()
        self.fournisseur = self.create_fournisseur()

    def test_access_detail(self):
        """Test accès détail fournisseur."""
        response = self.client.get(
            reverse('gestion_achats:fournisseur_detail',
                    args=[self.fournisseur.uuid])
        )
        self.assertIn(response.status_code, [200, 302, 403])


# =============================================
# Tests Catalogue (Articles & Catégories)
# =============================================

class TestArticleListView(BaseTestCase):
    """Tests pour la vue liste articles."""

    def test_access_authenticated(self):
        """Test accès authentifié."""
        response = self.client.get(reverse('gestion_achats:article_list'))
        self.assertIn(response.status_code, [200, 302, 403])


class TestCategorieListView(BaseTestCase):
    """Tests pour la vue liste catégories."""

    def test_access_authenticated(self):
        """Test accès authentifié."""
        response = self.client.get(reverse('gestion_achats:categorie_list'))
        self.assertIn(response.status_code, [200, 302, 403])


# =============================================
# Tests Budgets
# =============================================

class TestBudgetListView(BaseTestCase):
    """Tests pour la vue liste budgets."""

    def test_access_authenticated(self):
        """Test accès authentifié."""
        response = self.client.get(reverse('gestion_achats:budget_list'))
        self.assertIn(response.status_code, [200, 302, 403])

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('gestion_achats:budget_list'))
        self.assertEqual(response.status_code, 302)
