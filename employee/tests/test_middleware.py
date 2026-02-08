"""
Tests pour les middlewares du module employee.

Tests complets pour LoginRequiredMiddleware et ContratExpirationMiddleware.
"""

from datetime import date, timedelta
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.shortcuts import redirect

from employee.models import ZY00, ZYCO
from employee.middleware import LoginRequiredMiddleware, ContratExpirationMiddleware
from entreprise.models import Entreprise


class BaseMiddlewareTestCase(TestCase):
    """Classe de base pour les tests de middleware."""

    def setUp(self):
        """Prépare les données communes."""
        self.factory = RequestFactory()

        # Créer une entreprise
        self.entreprise = Entreprise.objects.create(
            code='ENT001',
            nom='Entreprise Test',
            raison_sociale='Entreprise Test SARL',
            numero_impot='123456789',
            rccm='RCCM123',
            adresse='123 Rue Test',
            ville='Lomé',
            pays='Togo'
        )

        # Créer un utilisateur et employé
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

        self.employe = ZY00.objects.create(
            nom='Dupont',
            prenoms='Jean',
            date_naissance=date(1990, 1, 1),
            sexe='M',
            type_id='CNI',
            numero_id='CNI001',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise,
            user=self.user,
            etat='actif'
        )

    def _get_response(self, request):
        """Fonction de réponse factice."""
        return HttpResponse("OK")

    def _add_session_to_request(self, request):
        """Ajoute le support de session à une requête."""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

    def _add_messages_to_request(self, request):
        """Ajoute le support de messages à une requête."""
        # S'assurer que la session existe
        if not hasattr(request, 'session'):
            setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)


class LoginRequiredMiddlewareTest(BaseMiddlewareTestCase):
    """Tests pour LoginRequiredMiddleware."""

    def test_authenticated_user_passes_through(self):
        """Test qu'un utilisateur authentifié passe sans problème."""
        request = self.factory.get('/dashboard/')
        request.user = self.user

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

    def test_unauthenticated_user_redirected_to_login(self):
        """Test qu'un utilisateur non authentifié est redirigé vers login."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/dashboard/')
        request.user = AnonymousUser()
        self._add_session_to_request(request)
        self._add_messages_to_request(request)

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        # Devrait rediriger
        self.assertEqual(response.status_code, 302)
        # Le LOGIN_URL peut être soit /employe/login/ soit /login/ selon settings
        self.assertTrue('/login' in response.url, f"Expected /login in {response.url}")

    def test_static_urls_are_exempt(self):
        """Test que les URLs statiques sont exemptées."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/static/css/style.css')
        request.user = AnonymousUser()

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        # Ne devrait pas rediriger
        self.assertEqual(response.status_code, 200)

    def test_media_urls_are_exempt(self):
        """Test que les URLs media sont exemptées."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/media/photos/test.jpg')
        request.user = AnonymousUser()

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_admin_urls_are_exempt(self):
        """Test que les URLs admin sont exemptées."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/admin/')
        request.user = AnonymousUser()

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_login_url_itself_is_exempt(self):
        """Test que l'URL de login est exemptée."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/employe/login/')
        request.user = AnonymousUser()

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_logout_url_is_exempt(self):
        """Test que l'URL de logout est exemptée."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/employe/logout/')
        request.user = AnonymousUser()

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    @override_settings(LOGIN_EXEMPT_URLS=[r'^/api/public/'])
    def test_custom_exempt_urls_from_settings(self):
        """Test que les URLs exemptées personnalisées fonctionnent."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/api/public/data/')
        request.user = AnonymousUser()

        middleware = LoginRequiredMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)


class ContratExpirationMiddlewareTest(BaseMiddlewareTestCase):
    """Tests pour ContratExpirationMiddleware."""

    def setUp(self):
        """Prépare les données spécifiques."""
        super().setUp()

        # Créer un contrat actif
        self.contrat_actif = ZYCO.objects.create(
            employe=self.employe,
            type_contrat='CDI',
            date_debut=date.today() - timedelta(days=100),
            actif=True
        )

    def test_employee_with_valid_contract_passes(self):
        """Test qu'un employé avec contrat valide passe."""
        request = self.factory.get('/dashboard/')
        request.user = self.user
        self._add_session_to_request(request)
        self._add_messages_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_employee_with_expired_contract_blocked(self):
        """Test qu'un employé avec contrat expiré est bloqué."""
        from django.contrib.sessions.backends.db import SessionStore

        # Mettre un contrat expiré
        self.contrat_actif.date_fin = date.today() - timedelta(days=1)
        self.contrat_actif.save()

        request = self.factory.get('/dashboard/')
        request.user = self.user

        # Utiliser une vraie session pour supporter logout()
        request.session = SessionStore()
        request.session.create()

        self._add_messages_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        # Devrait être redirigé vers login
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'employé est maintenant inactif
        self.employe.refresh_from_db()
        self.assertEqual(self.employe.etat, 'inactif')

        # Vérifier que le contrat est désactivé
        self.contrat_actif.refresh_from_db()
        self.assertFalse(self.contrat_actif.actif)

    def test_employee_with_expiring_contract_gets_warning(self):
        """Test qu'un employé avec contrat qui expire bientôt reçoit un avertissement."""
        # Contrat qui expire dans 15 jours
        self.contrat_actif.date_fin = date.today() + timedelta(days=15)
        self.contrat_actif.save()

        request = self.factory.get('/dashboard/')
        request.user = self.user
        self._add_session_to_request(request)
        self._add_messages_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        # Devrait passer mais avec un message
        self.assertEqual(response.status_code, 200)

        # Vérifier qu'un message a été ajouté à la session
        self.assertIn(f'contrat_warning_{self.employe.matricule}', request.session)

    def test_superuser_always_passes(self):
        """Test qu'un superuser passe toujours."""
        # Créer un superuser
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

        request = self.factory.get('/dashboard/')
        request.user = superuser
        self._add_session_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_inactive_employee_logged_out(self):
        """Test qu'un employé inactif est déconnecté."""
        from django.contrib.sessions.backends.db import SessionStore

        # Marquer l'employé comme inactif
        self.employe.etat = 'inactif'
        self.employe.save()

        request = self.factory.get('/dashboard/')
        request.user = self.user

        # Utiliser une vraie session pour supporter logout()
        request.session = SessionStore()
        request.session.create()

        self._add_messages_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        # Devrait rediriger
        self.assertEqual(response.status_code, 302)

    def test_exempt_urls_not_checked(self):
        """Test que les URLs exemptées ne sont pas vérifiées."""
        # Marquer l'employé comme inactif
        self.employe.etat = 'inactif'
        self.employe.save()

        # Accéder à une URL exemptée
        request = self.factory.get('/employe/login/')
        request.user = self.user
        self._add_session_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        # Devrait passer
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_passes(self):
        """Test qu'un utilisateur non authentifié passe (géré par LoginRequiredMiddleware)."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/dashboard/')
        request.user = AnonymousUser()
        self._add_session_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        # Devrait passer (sera géré par LoginRequiredMiddleware)
        self.assertEqual(response.status_code, 200)

    def test_user_without_employee_profile_passes(self):
        """Test qu'un user sans profil employé passe."""
        # Créer un user sans employe
        user_no_employe = User.objects.create_user(
            username='noemployee',
            email='noemployee@test.com',
            password='test123'
        )

        request = self.factory.get('/dashboard/')
        request.user = user_no_employe
        self._add_session_to_request(request)
        self._add_messages_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)
        response = middleware(request)

        # Devrait passer
        self.assertEqual(response.status_code, 200)

    def test_contract_expiration_warning_shown_once(self):
        """Test que l'avertissement d'expiration est affiché une seule fois."""
        # Contrat qui expire bientôt
        self.contrat_actif.date_fin = date.today() + timedelta(days=20)
        self.contrat_actif.save()

        request = self.factory.get('/dashboard/')
        request.user = self.user
        self._add_session_to_request(request)
        self._add_messages_to_request(request)

        middleware = ContratExpirationMiddleware(self._get_response)

        # Première requête - devrait afficher l'avertissement
        response1 = middleware(request)
        self.assertEqual(response1.status_code, 200)
        session_key = f'contrat_warning_{self.employe.matricule}'
        self.assertIn(session_key, request.session)

        # Deuxième requête avec la même session - ne devrait pas réafficher
        request2 = self.factory.get('/autre-page/')
        request2.user = self.user
        request2.session = request.session  # Réutiliser la session
        self._add_messages_to_request(request2)

        response2 = middleware(request2)
        self.assertEqual(response2.status_code, 200)


class MiddlewareIntegrationTest(BaseMiddlewareTestCase):
    """Tests d'intégration des middlewares ensemble."""

    def test_middlewares_chain_unauthenticated(self):
        """Test que LoginRequired est vérifié avant ContratExpiration."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/dashboard/')
        request.user = AnonymousUser()
        self._add_session_to_request(request)
        self._add_messages_to_request(request)

        # Créer la chaîne de middlewares
        def final_response(req):
            return HttpResponse("Final OK")

        contrat_middleware = ContratExpirationMiddleware(final_response)
        login_middleware = LoginRequiredMiddleware(contrat_middleware)

        response = login_middleware(request)

        # Devrait être bloqué par LoginRequired avant d'atteindre ContratExpiration
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


# Fonction pour exécuter tous les tests
def run_middleware_tests():
    """Exécute tous les tests de middleware."""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(["employee.tests.test_middleware"])

    return failures
