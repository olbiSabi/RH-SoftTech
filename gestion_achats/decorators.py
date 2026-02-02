"""
Décorateurs de permissions pour le module GAC.

Ce module fournit des décorateurs pour sécuriser les vues basées sur les rôles
et les permissions du module GAC.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required


def require_role(role_code):
    """
    Décorateur pour vérifier qu'un utilisateur a un rôle spécifique.

    Args:
        role_code: Code du rôle requis (ex: 'ACHETEUR')

    Usage:
        @require_role('ACHETEUR')
        def ma_vue(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_role(role_code):
                raise PermissionDenied(f"Rôle requis: {role_code}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_any_role(*role_codes):
    """
    Décorateur pour vérifier qu'un utilisateur a au moins un des rôles spécifiés.

    Args:
        *role_codes: Codes des rôles acceptés

    Usage:
        @require_any_role('ACHETEUR', 'RECEPTIONNAIRE')
        def ma_vue(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not any(request.user.has_role(role) for role in role_codes):
                roles_str = ', '.join(role_codes)
                raise PermissionDenied(f"Un de ces rôles est requis: {roles_str}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_demande_access(view_func):
    """
    Décorateur pour vérifier l'accès à une demande d'achat.

    La vue doit avoir un paramètre 'pk' qui identifie la demande.
    La demande est chargée et passée à la vue via kwargs['demande'].

    Usage:
        @require_demande_access
        def demande_detail(request, pk, demande):
            # La demande est déjà chargée et accessible
            ...
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, pk, *args, **kwargs):
        from gestion_achats.models import GACDemandeAchat
        from gestion_achats.permissions import GACPermissions

        demande = get_object_or_404(GACDemandeAchat, pk=pk)

        if not GACPermissions.can_view_demande(request.user, demande):
            raise PermissionDenied("Vous n'avez pas accès à cette demande")

        # Passer la demande à la vue pour éviter une double requête
        kwargs['demande'] = demande

        return view_func(request, pk, *args, **kwargs)
    return _wrapped_view


def require_bon_commande_access(view_func):
    """
    Décorateur pour vérifier l'accès à un bon de commande.

    La vue doit avoir un paramètre 'pk' qui identifie le BC.
    Le BC est chargé et passé à la vue via kwargs['bon_commande'].

    Usage:
        @require_bon_commande_access
        def bc_detail(request, pk, bon_commande):
            # Le BC est déjà chargé et accessible
            ...
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, pk, *args, **kwargs):
        from gestion_achats.models import GACBonCommande
        from gestion_achats.permissions import GACPermissions

        bc = get_object_or_404(GACBonCommande, pk=pk)

        if not GACPermissions.can_view_bon_commande(request.user, bc):
            raise PermissionDenied("Vous n'avez pas accès à ce bon de commande")

        # Passer le BC à la vue
        kwargs['bon_commande'] = bc

        return view_func(request, pk, *args, **kwargs)
    return _wrapped_view


def require_reception_access(view_func):
    """
    Décorateur pour vérifier l'accès à une réception.

    La vue doit avoir un paramètre 'pk' qui identifie la réception.
    La réception est chargée et passée à la vue via kwargs['reception'].

    Usage:
        @require_reception_access
        def reception_detail(request, pk, reception):
            # La réception est déjà chargée et accessible
            ...
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, pk, *args, **kwargs):
        from gestion_achats.models import GACReception
        from gestion_achats.permissions import GACPermissions

        reception = get_object_or_404(GACReception, pk=pk)

        if not GACPermissions.can_view_reception(request.user, reception):
            raise PermissionDenied("Vous n'avez pas accès à cette réception")

        # Passer la réception à la vue
        kwargs['reception'] = reception

        return view_func(request, pk, *args, **kwargs)
    return _wrapped_view


def require_budget_access(view_func):
    """
    Décorateur pour vérifier l'accès à un budget.

    La vue doit avoir un paramètre 'pk' qui identifie le budget.
    Le budget est chargé et passé à la vue via kwargs['budget'].

    Usage:
        @require_budget_access
        def budget_detail(request, pk, budget):
            # Le budget est déjà chargé et accessible
            ...
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, pk, *args, **kwargs):
        from gestion_achats.models import GACBudget
        from gestion_achats.permissions import GACPermissions

        budget = get_object_or_404(GACBudget, pk=pk)

        if not GACPermissions.can_view_budget(request.user, budget):
            raise PermissionDenied("Vous n'avez pas accès à ce budget")

        # Passer le budget à la vue
        kwargs['budget'] = budget

        return view_func(request, pk, *args, **kwargs)
    return _wrapped_view
