"""
Tests pour les mixins et décorateurs de permission du module Project Management.
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from unittest.mock import Mock, patch, MagicMock

from ..mixins import (
    ClientPermissionMixin,
    ProjectPermissionMixin,
    TimeEntryValidationPermissionMixin,
    client_permission_required,
    project_permission_required,
    time_validation_permission_required
)
from ..models import JRClient, JRProject

User = get_user_model()


class PermissionMixinTestCase(TestCase):
    """Tests de base pour les mixins de permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

        # Créer un utilisateur normal sans rôle
        self.user_normal = User.objects.create_user(
            username='normal_user',
            email='normal@test.com',
            password='testpass123'
        )

        # Créer un superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )

        # Créer un staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='staffpass123',
            is_staff=True
        )


class ClientPermissionMixinTest(PermissionMixinTestCase):
    """Tests pour ClientPermissionMixin."""

    def test_superuser_has_permission(self):
        """Test qu'un superuser a la permission de gérer les clients."""
        mixin = ClientPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = self.superuser

        self.assertTrue(mixin.test_func())

    def test_staff_has_permission(self):
        """Test qu'un staff a la permission de gérer les clients."""
        mixin = ClientPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = self.staff_user

        self.assertTrue(mixin.test_func())

    def test_unauthenticated_has_no_permission(self):
        """Test qu'un utilisateur non authentifié n'a pas la permission."""
        mixin = ClientPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = Mock()
        mixin.request.user.is_authenticated = False

        self.assertFalse(mixin.test_func())

    def test_normal_user_without_employe_has_no_permission(self):
        """Test qu'un utilisateur normal sans employé n'a pas la permission."""
        mixin = ClientPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = self.user_normal
        mixin.request.user.is_authenticated = True
        mixin.request.user.is_superuser = False
        mixin.request.user.is_staff = False

        # Simuler l'absence d'employe
        if hasattr(self.user_normal, 'employe'):
            delattr(self.user_normal, 'employe')

        self.assertFalse(mixin.test_func())

    def test_handle_no_permission_raises_denied(self):
        """Test que handle_no_permission lève PermissionDenied."""
        mixin = ClientPermissionMixin()
        with self.assertRaises(PermissionDenied):
            mixin.handle_no_permission()


class ProjectPermissionMixinTest(PermissionMixinTestCase):
    """Tests pour ProjectPermissionMixin."""

    def test_superuser_has_permission(self):
        """Test qu'un superuser a la permission de gérer les projets."""
        mixin = ProjectPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = self.superuser

        self.assertTrue(mixin.test_func())

    def test_staff_has_permission(self):
        """Test qu'un staff a la permission de gérer les projets."""
        mixin = ProjectPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = self.staff_user

        self.assertTrue(mixin.test_func())

    def test_unauthenticated_has_no_permission(self):
        """Test qu'un utilisateur non authentifié n'a pas la permission."""
        mixin = ProjectPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = Mock()
        mixin.request.user.is_authenticated = False

        self.assertFalse(mixin.test_func())

    def test_handle_no_permission_raises_denied(self):
        """Test que handle_no_permission lève PermissionDenied."""
        mixin = ProjectPermissionMixin()
        with self.assertRaises(PermissionDenied):
            mixin.handle_no_permission()


class TimeEntryValidationPermissionMixinTest(PermissionMixinTestCase):
    """Tests pour TimeEntryValidationPermissionMixin."""

    def test_superuser_has_permission(self):
        """Test qu'un superuser a la permission de valider les imputations."""
        mixin = TimeEntryValidationPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = self.superuser

        self.assertTrue(mixin.test_func())

    def test_staff_has_permission(self):
        """Test qu'un staff a la permission de valider les imputations."""
        mixin = TimeEntryValidationPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = self.staff_user

        self.assertTrue(mixin.test_func())

    def test_unauthenticated_has_no_permission(self):
        """Test qu'un utilisateur non authentifié n'a pas la permission."""
        mixin = TimeEntryValidationPermissionMixin()
        mixin.request = Mock()
        mixin.request.user = Mock()
        mixin.request.user.is_authenticated = False

        self.assertFalse(mixin.test_func())

    def test_handle_no_permission_raises_denied(self):
        """Test que handle_no_permission lève PermissionDenied."""
        mixin = TimeEntryValidationPermissionMixin()
        with self.assertRaises(PermissionDenied):
            mixin.handle_no_permission()


class ClientPermissionDecoratorTest(PermissionMixinTestCase):
    """Tests pour le décorateur client_permission_required."""

    def test_superuser_can_access(self):
        """Test qu'un superuser peut accéder à une vue protégée."""
        @client_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = self.superuser

        result = protected_view(request)
        self.assertEqual(result, "OK")

    def test_staff_can_access(self):
        """Test qu'un staff peut accéder à une vue protégée."""
        @client_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = self.staff_user

        result = protected_view(request)
        self.assertEqual(result, "OK")

    def test_unauthenticated_raises_denied(self):
        """Test qu'un utilisateur non authentifié lève PermissionDenied."""
        @client_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        with self.assertRaises(PermissionDenied):
            protected_view(request)

    def test_normal_user_without_role_raises_denied(self):
        """Test qu'un utilisateur normal sans rôle lève PermissionDenied."""
        @client_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = self.user_normal
        request.user.is_authenticated = True
        request.user.is_superuser = False
        request.user.is_staff = False

        # Supprimer l'attribut employe s'il existe
        if hasattr(request.user, 'employe'):
            delattr(request.user, 'employe')

        with self.assertRaises(PermissionDenied):
            protected_view(request)


class ProjectPermissionDecoratorTest(PermissionMixinTestCase):
    """Tests pour le décorateur project_permission_required."""

    def test_superuser_can_access(self):
        """Test qu'un superuser peut accéder à une vue protégée."""
        @project_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = self.superuser

        result = protected_view(request)
        self.assertEqual(result, "OK")

    def test_staff_can_access(self):
        """Test qu'un staff peut accéder à une vue protégée."""
        @project_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = self.staff_user

        result = protected_view(request)
        self.assertEqual(result, "OK")

    def test_unauthenticated_raises_denied(self):
        """Test qu'un utilisateur non authentifié lève PermissionDenied."""
        @project_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        with self.assertRaises(PermissionDenied):
            protected_view(request)


class TimeValidationPermissionDecoratorTest(PermissionMixinTestCase):
    """Tests pour le décorateur time_validation_permission_required."""

    def test_superuser_can_access(self):
        """Test qu'un superuser peut accéder à une vue protégée."""
        @time_validation_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = self.superuser

        result = protected_view(request)
        self.assertEqual(result, "OK")

    def test_staff_can_access(self):
        """Test qu'un staff peut accéder à une vue protégée."""
        @time_validation_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = self.staff_user

        result = protected_view(request)
        self.assertEqual(result, "OK")

    def test_unauthenticated_raises_denied(self):
        """Test qu'un utilisateur non authentifié lève PermissionDenied."""
        @time_validation_permission_required
        def protected_view(request):
            return "OK"

        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        with self.assertRaises(PermissionDenied):
            protected_view(request)


class ViewPermissionIntegrationTest(TestCase):
    """Tests d'intégration pour les permissions sur les vues."""

    def setUp(self):
        self.client = Client()

        # Utilisateurs
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='testpass123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )

        # Données de test
        self.test_client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        self.test_project = JRProject.objects.create(
            nom='Test Project',
            client=self.test_client,
            statut='ACTIF'
        )

    def test_client_list_requires_permission(self):
        """Test que la liste des clients nécessite une permission."""
        # Non authentifié - doit rediriger
        response = self.client.get(reverse('pm:client_list'))
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access_client_list(self):
        """Test qu'un superuser peut accéder à la liste des clients."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('pm:client_list'))
        self.assertEqual(response.status_code, 200)

    def test_projet_list_accessible_to_authenticated(self):
        """Test que la liste des projets est accessible aux utilisateurs connectés."""
        self.client.login(username='normal', password='testpass123')
        response = self.client.get(reverse('pm:projet_list'))
        self.assertEqual(response.status_code, 200)

    def test_projet_create_requires_permission(self):
        """Test que la création de projet nécessite une permission."""
        self.client.login(username='normal', password='testpass123')
        response = self.client.get(reverse('pm:projet_create'))
        # Devrait être 403 Forbidden ou rediriger
        self.assertIn(response.status_code, [302, 403])

    def test_superuser_can_create_projet(self):
        """Test qu'un superuser peut créer un projet."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('pm:projet_create'))
        self.assertEqual(response.status_code, 200)

    def test_validation_imputations_requires_permission(self):
        """Test que la validation des imputations nécessite une permission."""
        self.client.login(username='normal', password='testpass123')
        response = self.client.get(reverse('pm:validation_imputations'))
        # Devrait être 403 Forbidden
        self.assertIn(response.status_code, [302, 403])

    def test_superuser_can_access_validation(self):
        """Test qu'un superuser peut accéder à la validation."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('pm:validation_imputations'))
        self.assertEqual(response.status_code, 200)

    def test_rapports_temps_requires_permission(self):
        """Test que les rapports de temps nécessitent une permission."""
        self.client.login(username='normal', password='testpass123')
        response = self.client.get(reverse('pm:rapports_temps'))
        # Devrait être 403 Forbidden
        self.assertIn(response.status_code, [302, 403])

    def test_superuser_can_access_rapports(self):
        """Test qu'un superuser peut accéder aux rapports."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('pm:rapports_temps'))
        self.assertEqual(response.status_code, 200)
