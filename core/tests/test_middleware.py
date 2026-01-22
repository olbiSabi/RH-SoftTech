# core/tests/test_middleware.py
"""
Tests pour les middlewares de l'application core.
"""
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

from core.middleware import CurrentRequestMiddleware, PermissionDeniedMiddleware
from core.signals import get_current_request


class TestCurrentRequestMiddleware(TestCase):
    """Tests pour CurrentRequestMiddleware."""

    def setUp(self):
        """Setup pour les tests."""
        self.factory = RequestFactory()

    def test_middleware_sets_request(self):
        """Test que le middleware définit la requête courante."""
        request = self.factory.get('/test/')

        def get_response(req):
            # Pendant le traitement, la requête doit être disponible
            current = get_current_request()
            self.assertEqual(current, req)
            return JsonResponse({'status': 'ok'})

        middleware = CurrentRequestMiddleware(get_response)
        middleware(request)

    def test_middleware_clears_request_after(self):
        """Test que le middleware nettoie la requête après."""
        request = self.factory.get('/test/')

        def get_response(req):
            return JsonResponse({'status': 'ok'})

        middleware = CurrentRequestMiddleware(get_response)
        middleware(request)

        # Après le traitement, la requête doit être None
        self.assertIsNone(get_current_request())


class TestPermissionDeniedMiddleware(TestCase):
    """Tests pour PermissionDeniedMiddleware."""

    def setUp(self):
        """Setup pour les tests."""
        self.factory = RequestFactory()

    def test_middleware_handles_permission_denied_ajax(self):
        """Test gestion PermissionDenied pour requête AJAX."""
        request = self.factory.get('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        def get_response(req):
            return JsonResponse({'status': 'ok'})

        middleware = PermissionDeniedMiddleware(get_response)

        # Simuler une exception PermissionDenied
        exception = PermissionDenied("Accès refusé")
        response = middleware.process_exception(request, exception)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
        self.assertIsInstance(response, JsonResponse)

    def test_middleware_returns_none_for_other_exceptions(self):
        """Test que le middleware ignore les autres exceptions."""
        request = self.factory.get('/test/')

        def get_response(req):
            return JsonResponse({'status': 'ok'})

        middleware = PermissionDeniedMiddleware(get_response)

        # Une autre exception
        exception = ValueError("Some error")
        response = middleware.process_exception(request, exception)

        self.assertIsNone(response)

    def test_middleware_call_passes_through(self):
        """Test que __call__ passe la requête normalement."""
        request = self.factory.get('/test/')

        def get_response(req):
            return JsonResponse({'status': 'ok'})

        middleware = PermissionDeniedMiddleware(get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
