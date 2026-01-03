# employee/middleware.py

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from employee.models import ZY00, ZYCO


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
            reverse('password_reset'),
            reverse('password_reset_confirm'),
            '/hronian/',
            '/static/',
            '/media/',
            '/admin/',
        ]

        # Autoriser les POST vers le login
        is_login_post = path == reverse('login') and request.method == 'POST'
        is_exempt = any(path.startswith(exempt_url) for exempt_url in exempt_urls)

        # Autoriser les requêtes POST vers le login et autres URLs exemptées
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


class ContratExpirationMiddleware:
    """
    Middleware pour vérifier l'expiration des contrats
    et bloquer l'accès si le contrat est expiré
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URLs exemptées de la vérification
        self.exempt_urls = [
            '/login/',
            '/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/password-reset/',
            '/hronian/',
        ]

    def __call__(self, request):
        # Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            # Vérifier si c'est un superuser (admin) - ne pas bloquer
            if request.user.is_superuser:
                return self.get_response(request)

            # Vérifier si l'URL est exemptée
            if any(request.path.startswith(url) for url in self.exempt_urls):
                return self.get_response(request)

            try:
                employe = request.user.employe

                # Vérifier si l'employé est déjà inactif
                if employe.etat == 'inactif':
                    logout(request)
                    messages.error(
                        request,
                        "⛔ Votre compte a été désactivé. Veuillez contacter le service RH."
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