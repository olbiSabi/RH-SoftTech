# project_management/mixins.py
"""
Mixins de permission pour le module Project Management.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from functools import wraps


class ClientPermissionMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier les permissions de gestion des clients.
    Rôles autorisés: RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
    """
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if hasattr(user, 'employe') and user.employe:
            return user.employe.peut_gerer_clients()
        return False

    def handle_no_permission(self):
        raise PermissionDenied("Vous n'avez pas la permission de gérer les clients.")


class ProjectPermissionMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier les permissions de gestion des projets.
    Rôles autorisés: MANAGER, RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
    """
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if hasattr(user, 'employe') and user.employe:
            return user.employe.peut_gerer_projets()
        return False

    def handle_no_permission(self):
        raise PermissionDenied("Vous n'avez pas la permission de gérer les projets.")


class TimeEntryValidationPermissionMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier les permissions de validation des imputations.
    Rôles autorisés: MANAGER, RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
    """
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if hasattr(user, 'employe') and user.employe:
            return user.employe.peut_voir_toutes_imputations()
        return False

    def handle_no_permission(self):
        raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette fonctionnalité.")


# Décorateurs pour les vues fonctionnelles

def client_permission_required(view_func):
    """
    Décorateur pour vérifier les permissions de gestion des clients.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentification requise.")
        if user.is_superuser or user.is_staff:
            return view_func(request, *args, **kwargs)
        if hasattr(user, 'employe') and user.employe and user.employe.peut_gerer_clients():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Vous n'avez pas la permission de gérer les clients.")
    return wrapper


def project_permission_required(view_func):
    """
    Décorateur pour vérifier les permissions de gestion des projets.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentification requise.")
        if user.is_superuser or user.is_staff:
            return view_func(request, *args, **kwargs)
        if hasattr(user, 'employe') and user.employe and user.employe.peut_gerer_projets():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Vous n'avez pas la permission de gérer les projets.")
    return wrapper


def time_validation_permission_required(view_func):
    """
    Décorateur pour vérifier les permissions de validation des imputations.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentification requise.")
        if user.is_superuser or user.is_staff:
            return view_func(request, *args, **kwargs)
        if hasattr(user, 'employe') and user.employe and user.employe.peut_voir_toutes_imputations():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette fonctionnalité.")
    return wrapper
