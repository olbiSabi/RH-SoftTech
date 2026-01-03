# employee/decorators.py

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


def custom_permission_required(permission_name):
    """
    Décorateur pour vérifier les permissions JSON custom
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Vérifier authentification
            if not request.user.is_authenticated:
                raise PermissionDenied("Vous devez être connecté pour accéder à cette page.")

            # Les superusers ont tous les droits
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Vérifier que l'utilisateur a un employé associé
            if not hasattr(request.user, 'employe') or request.user.employe is None:
                raise PermissionDenied(
                    "Votre compte n'est pas associé à un profil employé. "
                    "Contactez l'administrateur système."
                )

            # Vérifier la permission custom
            if not request.user.employe.has_permission(permission_name):
                # Récupérer les rôles de l'employé pour un message plus informatif
                roles = [r.role.LIBELLE for r in request.user.employe.get_roles()]
                roles_text = ", ".join(roles) if roles else "Aucun rôle"

                raise PermissionDenied(
                    f"Accès refusé : Vous n'avez pas les permissions nécessaires pour cette action. "
                )

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


# ========================================
# DÉCORATEURS POUR VUES FONCTIONS
# ========================================

def drh_or_admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux DRH et administrateurs
    À utiliser sur les vues fonctions
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "⛔ Vous devez être connecté.")
            return redirect('login')

        # Vérifier si admin
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # Vérifier si DRH ou GESTION_APP
        if hasattr(request.user, 'employe'):
            employe = request.user.employe
            if employe.has_role('DRH') or employe.has_role('GESTION_APP'):
                return view_func(request, *args, **kwargs)

        # Accès refusé
        messages.error(
            request,
            "⛔ Accès refusé : Vous devez être DRH ou administrateur."
        )
        return redirect('dashboard')

    return wrapper


def gestion_app_required(view_func):
    """
    Décorateur pour restreindre l'accès au rôle GESTION_APP uniquement
    À utiliser sur les vues fonctions
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "⛔ Vous devez être connecté.")
            return redirect('login')

        # Vérifier si admin
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # Vérifier si GESTION_APP
        if hasattr(request.user, 'employe'):
            employe = request.user.employe
            if employe.has_role('GESTION_APP'):
                return view_func(request, *args, **kwargs)

        # Accès refusé
        messages.error(
            request,
            "⛔ Accès refusé : Vous devez avoir le rôle Gestionnaire Application."
        )
        return redirect('dashboard')

    return wrapper


def assistant_rh_required(view_func):
    """
    Décorateur pour restreindre l'accès aux Assistants RH et rôles RH supérieurs
    À utiliser sur les vues fonctions
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "⛔ Vous devez être connecté.")
            return redirect('login')

        # Vérifier si admin
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # Vérifier si rôle RH
        if hasattr(request.user, 'employe'):
            employe = request.user.employe
            if (employe.has_role('ASSISTANT_RH') or
                employe.has_role('RH_VALIDATION_ABS') or
                employe.has_role('DRH') or
                employe.has_role('GESTION_APP')):
                return view_func(request, *args, **kwargs)

        # Accès refusé
        messages.error(
            request,
            "⛔ Accès refusé : Vous devez être Assistant RH ou avoir un rôle RH."
        )
        return redirect('dashboard')

    return wrapper


def manager_required(view_func):
    """
    Décorateur pour restreindre l'accès aux Managers
    À utiliser sur les vues fonctions
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "⛔ Vous devez être connecté.")
            return redirect('login')

        # Vérifier si admin
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # Vérifier si manager
        if hasattr(request.user, 'employe'):
            employe = request.user.employe
            if (employe.est_manager_departement() or
                employe.has_role('MANAGER_ABS') or
                employe.has_role('DRH') or
                employe.has_role('GESTION_APP')):
                return view_func(request, *args, **kwargs)

        # Accès refusé
        messages.error(
            request,
            "⛔ Accès refusé : Vous devez être Manager."
        )
        return redirect('dashboard')

    return wrapper


# ========================================
# MIXINS POUR VUES CLASSES (CBV)
# ========================================

class DRHOrAdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès aux DRH et administrateurs
    À utiliser sur les vues classes (CBV)
    """

    def test_func(self):
        """Teste si l'utilisateur a les permissions requises"""
        if not self.request.user.is_authenticated:
            return False

        # Vérifier si l'utilisateur est admin
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Vérifier si l'utilisateur a le rôle DRH
        if hasattr(self.request.user, 'employe'):
            employe = self.request.user.employe
            if employe.has_role('DRH') or employe.has_role('GESTION_APP'):
                return True

        return False

    def handle_no_permission(self):
        """Gère le cas où l'utilisateur n'a pas la permission"""
        messages.error(
            self.request,
            "⛔ Accès refusé : Vous devez être DRH ou administrateur pour accéder à cette page."
        )
        return redirect('dashboard')


class AssistantRHRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès aux Assistants RH (lecture seule)
    À utiliser sur les vues classes (CBV)
    """

    def test_func(self):
        """Teste si l'utilisateur a les permissions requises"""
        if not self.request.user.is_authenticated:
            return False

        # Vérifier si l'utilisateur est admin
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Vérifier si l'utilisateur a le rôle ASSISTANT_RH
        if hasattr(self.request.user, 'employe'):
            employe = self.request.user.employe
            if (employe.has_role('ASSISTANT_RH') or
                    employe.has_role('RH_VALIDATION_ABS') or
                    employe.has_role('DRH') or
                    employe.has_role('GESTION_APP')):
                return True

        return False

    def handle_no_permission(self):
        """Gère le cas où l'utilisateur n'a pas la permission"""
        messages.error(
            self.request,
            "⛔ Accès refusé : Vous devez être Assistant RH ou avoir un rôle RH pour accéder à cette page."
        )
        return redirect('dashboard')


class DRHOrAssistantRHRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès aux DRH ET Assistants RH
    À utiliser sur les vues classes (CBV)
    """

    def test_func(self):
        """Teste si l'utilisateur a les permissions requises"""
        if not self.request.user.is_authenticated:
            return False

        # Vérifier si l'utilisateur est admin
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Vérifier si l'utilisateur a un rôle RH
        if hasattr(self.request.user, 'employe'):
            employe = self.request.user.employe
            if (employe.has_role('ASSISTANT_RH') or
                    employe.has_role('RH_VALIDATION_ABS') or
                    employe.has_role('DRH') or
                    employe.has_role('GESTION_APP')):
                return True

        return False

    def handle_no_permission(self):
        """Gère le cas où l'utilisateur n'a pas la permission"""
        messages.error(
            self.request,
            "⛔ Accès refusé : Vous devez avoir un rôle RH pour accéder à cette page."
        )
        return redirect('dashboard')


class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès aux Managers
    À utiliser sur les vues classes (CBV)
    """

    def test_func(self):
        """Teste si l'utilisateur a les permissions requises"""
        if not self.request.user.is_authenticated:
            return False

        # Vérifier si l'utilisateur est admin
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Vérifier si l'utilisateur est manager
        if hasattr(self.request.user, 'employe'):
            employe = self.request.user.employe
            if (employe.est_manager_departement() or
                    employe.has_role('MANAGER_ABS') or
                    employe.has_role('DRH') or
                    employe.has_role('GESTION_APP')):
                return True

        return False

    def handle_no_permission(self):
        """Gère le cas où l'utilisateur n'a pas la permission"""
        messages.error(
            self.request,
            "⛔ Accès refusé : Vous devez être Manager pour accéder à cette page."
        )
        return redirect('dashboard')


class GestionAppRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès au rôle GESTION_APP uniquement
    À utiliser sur les vues classes (CBV)
    """

    def test_func(self):
        """Teste si l'utilisateur a les permissions requises"""
        if not self.request.user.is_authenticated:
            return False

        # Vérifier si l'utilisateur est admin
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Vérifier si l'utilisateur a le rôle GESTION_APP
        if hasattr(self.request.user, 'employe'):
            employe = self.request.user.employe
            if employe.has_role('GESTION_APP'):
                return True

        return False

    def handle_no_permission(self):
        """Gère le cas où l'utilisateur n'a pas la permission"""
        messages.error(
            self.request,
            "⛔ Accès refusé : Vous devez avoir le rôle Gestionnaire Application."
        )
        return redirect('dashboard')