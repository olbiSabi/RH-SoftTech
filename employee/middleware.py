# employee/middleware.py
import logging
import re

from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class LoginRequiredMiddleware:
    """
    Middleware pour forcer l'authentification sur toutes les pages.

    Configuration via settings.py:
        LOGIN_URL = '/employe/login/'  # URL de connexion
        LOGIN_EXEMPT_URLS = ['/api/public/', '/webhook/']  # URLs supplémentaires à exempter
    """

    # URLs toujours exemptées (patterns regex)
    ALWAYS_EXEMPT_PATTERNS = [
        r'^/static/',
        r'^/media/',
        r'^/admin/',
        r'^/hronian/',
        r'^/login/',
        r'^/logout/',
        r'^/employe/login/',
        r'^/employe/logout/',
        r'^/employe/password-reset',
        r'^/password-reset',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        # Compiler les patterns une seule fois
        self.exempt_patterns = [
            re.compile(pattern) for pattern in self.ALWAYS_EXEMPT_PATTERNS
        ]
        # Ajouter les patterns personnalisés depuis settings
        custom_exempt = getattr(settings, 'LOGIN_EXEMPT_URLS', [])
        for pattern in custom_exempt:
            self.exempt_patterns.append(re.compile(pattern))

    def __call__(self, request):
        path = request.path_info

        # Vérifier si l'URL est exemptée
        if self._is_exempt(path):
            return self.get_response(request)

        # Si l'utilisateur n'est pas authentifié, rediriger vers login
        if not request.user.is_authenticated:
            login_url = getattr(settings, 'LOGIN_URL', '/employe/login/')

            # Ajouter un message contextuel uniquement pour les accès à des pages spécifiques
            # Ne pas afficher de message pour les accès génériques (/, /dashboard/, etc.)
            if '/dossier/' in path:
                messages.warning(request, 'Vous devez vous connecter pour accéder aux dossiers des employés.')
            elif '/embauche/' in path:
                messages.warning(request, 'Vous devez vous connecter pour effectuer une embauche.')
            elif '/absence/' in path:
                messages.warning(request, 'Vous devez vous connecter pour accéder aux absences.')
            elif '/projet/' in path or '/project/' in path:
                messages.warning(request, 'Vous devez vous connecter pour accéder aux projets.')
            # Ne plus afficher de message générique pour éviter la confusion
            # L'utilisateur comprend déjà qu'il doit se connecter en voyant la page de login

            # Rediriger vers login avec l'URL de retour
            return redirect(f"{login_url}?next={path}")

        return self.get_response(request)

    def _is_exempt(self, path):
        """Vérifie si le chemin est exempté d'authentification."""
        for pattern in self.exempt_patterns:
            if pattern.match(path):
                return True
        return False


class ContratExpirationMiddleware:
    """
    Middleware pour vérifier l'expiration des contrats
    et bloquer l'accès si le contrat est expiré.
    """

    # URLs exemptées de la vérification
    EXEMPT_URLS = [
        '/employe/login/',
        '/employe/logout/',
        '/admin/',
        '/static/',
        '/media/',
        '/employe/password-reset',
        '/hronian/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Import tardif pour éviter les imports circulaires
        from employee.models import ZY00, ZYCO

        # Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            # Vérifier si c'est un superuser (admin) - ne pas bloquer
            if request.user.is_superuser:
                return self.get_response(request)

            # Vérifier si l'URL est exemptée
            if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
                return self.get_response(request)

            try:
                employe = request.user.employe

                # Vérifier si l'employé est déjà inactif
                if employe.etat == 'inactif':
                    logout(request)
                    messages.error(
                        request,
                        "Votre compte a été désactivé. Veuillez contacter le service RH."
                    )
                    return redirect('login')

                # Vérifier si l'employé a un contrat actif
                date_actuelle = timezone.now().date()

                # Récupérer le contrat actif de l'employé
                contrat_actif = ZYCO.objects.filter(
                    employe=employe,
                    actif=True
                ).first()

                if contrat_actif:
                    # Vérifier si le contrat est expiré
                    if contrat_actif.date_fin and contrat_actif.date_fin < date_actuelle:
                        # Bloquer l'employé automatiquement
                        employe.etat = 'inactif'
                        employe.save(update_fields=['etat'])

                        # Désactiver le contrat
                        contrat_actif.actif = False
                        contrat_actif.save(update_fields=['actif'])

                        # Déconnecter l'utilisateur
                        logout(request)

                        messages.error(
                            request,
                            f"⛔ Votre contrat a expiré le {contrat_actif.date_fin.strftime('%d/%m/%Y')}. "
                            f"Veuillez contacter le service RH."
                        )

                        return redirect('login')

                    # Avertissement si le contrat expire dans moins de 30 jours
                    elif contrat_actif.date_fin:
                        jours_restants = (contrat_actif.date_fin - date_actuelle).days

                        if 0 < jours_restants <= 30:
                            # Stocker l'avertissement dans la session pour l'afficher une seule fois
                            session_key = f'contrat_warning_{employe.matricule}'
                            if not request.session.get(session_key):
                                messages.warning(
                                    request,
                                    f"⚠️ Attention : Votre contrat expire dans {jours_restants} jour(s) "
                                    f"({contrat_actif.date_fin.strftime('%d/%m/%Y')}). "
                                    f"Veuillez contacter le service RH."
                                )
                                request.session[session_key] = True

            except ZY00.DoesNotExist:
                # L'utilisateur n'a pas de profil employé
                pass
            except Exception as e:
                # En cas d'erreur, logger et continuer
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur dans ContratExpirationMiddleware: {str(e)}")

        response = self.get_response(request)
        return response