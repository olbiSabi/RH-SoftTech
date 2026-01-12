# absence/decorators.py
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def drh_or_admin_required(view_func):
    """
    Décorateur pour autoriser uniquement les DRH, PDG ou superusers
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Superuser = toujours autorisé
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Vérifier si l'utilisateur a un employé lié
        if not hasattr(user, 'employe'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Vous n\'avez pas les permissions nécessaires'
                }, status=403)
            messages.error(request, '❌ Vous n\'avez pas les permissions nécessaires')
            return redirect('dashboard')

        employe = user.employe

        # Vérifier si l'employé a le rôle DRH ou PDG
        if employe.has_role('DRH') or employe.has_role('PDG'):
            return view_func(request, *args, **kwargs)

        # Accès refusé
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Vous devez avoir le rôle DRH ou PDG pour accéder à cette fonctionnalité'
            }, status=403)

        messages.error(
            request,
            '❌ Vous devez avoir le rôle DRH ou PDG pour accéder à cette fonctionnalité'
        )
        return redirect('dashboard')

    return wrapper


def manager_required(view_func):
    """
    Décorateur pour autoriser uniquement les managers
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Superuser = toujours autorisé
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Vérifier si l'utilisateur a un employé lié
        if not hasattr(user, 'employe'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Vous n\'avez pas les permissions nécessaires'
                }, status=403)
            messages.error(request, '❌ Vous n\'avez pas les permissions nécessaires')
            return redirect('absence:liste_absences')

        employe = user.employe

        # Vérifier si l'employé est manager de département
        if employe.est_manager_departement():
            return view_func(request, *args, **kwargs)

        # Accès refusé
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Vous devez être manager pour accéder à cette fonctionnalité'
            }, status=403)

        messages.error(
            request,
            '❌ Vous devez être manager pour accéder à cette fonctionnalité'
        )
        return redirect('absence:liste_absences')

    return wrapper


def rh_required(view_func):
    """
    Décorateur pour autoriser uniquement les RH
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Superuser = toujours autorisé
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Vérifier si l'utilisateur a un employé lié
        if not hasattr(user, 'employe'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Vous n\'avez pas les permissions nécessaires'
                }, status=403)
            messages.error(request, '❌ Vous n\'avez pas les permissions nécessaires')
            return redirect('absence:liste_absences')

        employe = user.employe

        # Vérifier si l'employé a le rôle RH
        if employe.peut_valider_absence_rh():
            return view_func(request, *args, **kwargs)

        # Accès refusé
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Vous devez avoir le rôle RH pour accéder à cette fonctionnalité'
            }, status=403)

        messages.error(
            request,
            '❌ Vous devez avoir le rôle RH pour accéder à cette fonctionnalité'
        )
        return redirect('absence:liste_absences')

    return wrapper


def assistant_rh_required(view_func):
    """
    Décorateur pour autoriser les Assistants RH et rôles RH supérieurs
    (consultation uniquement)
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Superuser = toujours autorisé
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Vérifier si l'utilisateur a un employé lié
        if not hasattr(user, 'employe'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Vous n\'avez pas les permissions nécessaires'
                }, status=403)
            messages.error(request, '❌ Vous n\'avez pas les permissions nécessaires')
            return redirect('absence:liste_absences')

        employe = user.employe

        # Vérifier si l'employé a le rôle ASSISTANT_RH ou rôles supérieurs
        if (employe.has_role('ASSISTANT_RH') or
            employe.has_role('RH_VALIDATION_ABS') or
            employe.has_role('DRH') or
            employe.has_role('GESTION_APP')):
            return view_func(request, *args, **kwargs)

        # Accès refusé
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Vous devez avoir un rôle RH pour accéder à cette fonctionnalité'
            }, status=403)

        messages.error(
            request,
            '❌ Vous devez avoir un rôle RH pour accéder à cette fonctionnalité'
        )
        return redirect('absence:liste_absences')

    return wrapper


def gestion_app_required(view_func):
    """
    Décorateur pour autoriser uniquement les gestionnaires d'application
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Superuser = toujours autorisé
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Vérifier si l'utilisateur a un employé lié
        if not hasattr(user, 'employe'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Vous n\'avez pas les permissions nécessaires'
                }, status=403)
            messages.error(request, '❌ Vous n\'avez pas les permissions nécessaires')
            return redirect('dashboard')

        employe = user.employe

        # Vérifier si l'employé a le rôle GESTION_APP
        if employe.peut_gerer_parametrage_app():
            return view_func(request, *args, **kwargs)

        # Accès refusé
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Vous devez avoir le rôle Gestionnaire Application pour accéder à cette fonctionnalité'
            }, status=403)

        messages.error(
            request,
            '❌ Vous devez avoir le rôle Gestionnaire Application pour accéder à cette fonctionnalité'
        )
        return redirect('dashboard')

    return wrapper


def manager_or_rh_required(view_func):
    """
    Décorateur pour autoriser les managers OU les RH
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Superuser = toujours autorisé
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Vérifier si l'utilisateur a un employé lié
        if not hasattr(user, 'employe'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Vous n\'avez pas les permissions nécessaires'
                }, status=403)
            messages.error(request, '❌ Vous n\'avez pas les permissions nécessaires')
            return redirect('absence:liste_absences')

        employe = user.employe

        # Vérifier si manager OU RH
        if employe.est_manager_departement() or employe.peut_valider_absence_rh():
            return view_func(request, *args, **kwargs)

        # Accès refusé
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Vous devez être manager ou RH pour accéder à cette fonctionnalité'
            }, status=403)

        messages.error(
            request,
            '❌ Vous devez être manager ou RH pour accéder à cette fonctionnalité'
        )
        return redirect('absence:liste_absences')

    return wrapper


def role_required(*required_roles):
    """
    Décorateur générique pour vérifier plusieurs rôles

    Usage:
        @role_required('ASSISTANT_RH', 'RH_VALIDATION_ABS', 'DRH', 'GESTION_APP')
        def ma_vue(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Superuser = toujours autorisé
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Vérifier si l'utilisateur a un employé lié
            if not hasattr(user, 'employe'):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Vous n\'avez pas les permissions nécessaires'
                    }, status=403)
                messages.error(request, '❌ Vous n\'avez pas les permissions nécessaires')
                return redirect('dashboard')

            employe = user.employe

            # Vérifier si l'employé a au moins un des rôles requis
            for role in required_roles:
                if employe.has_role(role):
                    return view_func(request, *args, **kwargs)

            # Accès refusé
            roles_str = ', '.join(required_roles)
            error_message = f'Vous devez avoir l\'un de ces rôles : {roles_str}'

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_message
                }, status=403)

            messages.error(request, f'❌ {error_message}')
            return redirect('dashboard')

        return wrapper

    return decorator


def manager_or_admin_required(view_func):
    """
    Décorateur pour autoriser :
    - MANAGER (validation équipe)
    - DRH (accès complet RH)
    - GESTION_APP (accès complet paramétrage)
    - DIRECTEUR (accès complet direction)

    Usage : Gestion projets, validation imputations, gestion tâches
    """
    return role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')(view_func)


def admin_only_required(view_func):
    """
    Décorateur pour autoriser uniquement :
    - DRH (accès complet RH)
    - GESTION_APP (accès complet paramétrage)
    - DIRECTEUR (accès complet direction)

    Usage : Gestion clients, activités, paramètres sensibles
    """
    return role_required('DRH', 'GESTION_APP', 'DIRECTEUR')(view_func)


def can_view_all_data(view_func):
    """
    Décorateur pour autoriser la consultation (lecture seule) :
    - DRH, GESTION_APP, DIRECTEUR (accès complet)
    - COMPTABLE (pour facturation)
    - ASSISTANT_RH (pour consultation RH)

    Usage : Consultation de toutes les imputations, rapports
    """
    return role_required('DRH', 'GESTION_APP', 'DIRECTEUR', 'COMPTABLE', 'ASSISTANT_RH')(view_func)