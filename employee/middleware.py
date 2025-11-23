from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class LoginRequiredMiddleware:
    """
    Middleware pour forcer l'authentification sur toutes les pages
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # URLs exemptées - ÉTENDUES
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('password_reset'),  # ← AJOUT
            reverse('password_reset_confirm'),  # ← AJOUT
            '/hronian/',
            '/static/',
            '/media/',
            '/admin/',  # ← AJOUT si vous utilisez l'admin Django
        ]

        # ✅ CORRECTION CRITIQUE : Autoriser les POST vers le login
        is_login_post = path == reverse('login') and request.method == 'POST'
        is_exempt = any(path.startswith(exempt_url) for exempt_url in exempt_urls)

        # ✅ AUTORISER les requêtes POST vers le login et autres URLs exemptées
        if not request.user.is_authenticated and not is_exempt and not is_login_post:
            # Message personnalisé selon le type de page
            if '/dossier/' in path:
                messages.warning(request, '🔒 Vous devez vous connecter pour accéder aux dossiers des employés.')
            elif '/embauche/' in path:
                messages.warning(request, '🔒 Vous devez vous connecter pour effectuer une embauche.')
            else:
                messages.warning(request, '🔒 Accès non autorisé. Veuillez vous connecter.')

            return redirect(f"{reverse('login')}?next={path}")

        response = self.get_response(request)
        return response