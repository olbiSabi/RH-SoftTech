"""
Décorateurs basés sur les rôles
À remplacer dans absence/decorators.py
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*role_codes):
    """
    Décorateur pour vérifier qu'un utilisateur a au moins un des rôles spécifiés

    Usage:
        @role_required('DRH')
        def rh_validation(request):
            ...

        @role_required('DRH', 'DIRECTEUR')  # DRH OU DIRECTEUR
        def ma_vue(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Vérifier si l'utilisateur est connecté
            if not request.user.is_authenticated:
                #messages.warning(request, "Vous devez être connecté pour accéder à cette page.")
                return redirect('login')

            # Les staff et superusers ont accès à tout
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Vérifier si l'utilisateur a un employé
            try:
                employe = request.user.employe

                # Vérifier si l'employé a au moins un des rôles requis
                for role_code in role_codes:
                    if employe.has_role(role_code):
                        return view_func(request, *args, **kwargs)

                # Aucun rôle requis trouvé
                roles_str = " ou ".join(role_codes)
                #messages.error(request,f"Accès refusé. Cette page nécessite le rôle : {roles_str}")
                return redirect('dashboard')

            except AttributeError:
                #messages.error(request, "Accès refusé. Vous n'avez pas de profil employé associé.")
                return redirect('dashboard')

        return wrapper
    return decorator


def permission_required(permission_name):
    """
    Décorateur pour vérifier qu'un utilisateur a une permission spécifique

    Usage:
        @permission_required('can_validate_rh')
        def rh_validation(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                #messages.warning(request, "Vous devez être connecté pour accéder à cette page.")
                return redirect('login')

            # Staff et superusers ont toutes les permissions
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            try:
                employe = request.user.employe

                if employe.has_permission(permission_name):
                    return view_func(request, *args, **kwargs)

                #messages.error(request,f"Accès refusé. Permission requise : {permission_name}")
                return redirect('dashboard')

            except AttributeError:
                #messages.error(request, "Accès refusé. Vous n'avez pas de profil employé associé.")
                return redirect('dashboard')

        return wrapper
    return decorator


# Décorateurs spécifiques pour faciliter l'utilisation
def drh_required(view_func):
    """
    Décorateur spécifique pour le rôle DRH
    Équivalent à @role_required('DRH')
    """
    return role_required('DRH')(view_func)


def manager_required(view_func):
    """
    Décorateur spécifique pour le rôle MANAGER
    """
    return role_required('MANAGER')(view_func)


# Fonctions utilitaires
def user_has_role(user, role_code):
    """
    Vérifie si un utilisateur a un rôle spécifique

    Args:
        user: L'utilisateur Django
        role_code: Code du rôle (ex: 'DRH')

    Returns:
        bool: True si l'utilisateur a ce rôle
    """
    if user.is_staff or user.is_superuser:
        return True

    try:
        return user.employe.has_role(role_code)
    except AttributeError:
        return False


def user_has_permission(user, permission_name):
    """
    Vérifie si un utilisateur a une permission spécifique

    Args:
        user: L'utilisateur Django
        permission_name: Nom de la permission (ex: 'can_validate_rh')

    Returns:
        bool: True si l'utilisateur a cette permission
    """
    if user.is_staff or user.is_superuser:
        return True

    try:
        return user.employe.has_permission(permission_name)
    except AttributeError:
        return False