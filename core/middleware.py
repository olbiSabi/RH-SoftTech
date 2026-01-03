from .signals import set_current_request
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

class CurrentRequestMiddleware:
    """Middleware unique pour tout le projet"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        set_current_request(None)
        return response


# core/middleware.py (ou employee/middleware.py)
class PermissionDeniedMiddleware:
    """
    Middleware qui intercepte les erreurs PermissionDenied
    et affiche un message au lieu de la page 403
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Intercepte les exceptions PermissionDenied"""
        if isinstance(exception, PermissionDenied):
            # Si c'est une requête AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'permission_denied',
                    'message': str(exception) or "Vous n'avez pas les permissions nécessaires."
                }, status=403)

            # Pour les requêtes normales
            messages.error(
                request,
                str(exception) or "Accès refusé : Vous n'avez pas les permissions nécessaires pour cette action."
            )

            # Rediriger vers la page précédente ou le dashboard
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('dashboard')

        return None