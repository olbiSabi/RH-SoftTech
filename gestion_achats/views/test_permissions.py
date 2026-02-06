"""
Vue de test pour déboguer les permissions.
À SUPPRIMER EN PRODUCTION.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from gestion_achats.models import GACDemandeAchat
from gestion_achats.permissions import GACPermissions


@login_required
def test_submit_permission(request, pk):
    """Teste les permissions de soumission pour une demande."""

    demande = get_object_or_404(GACDemandeAchat, uuid=pk)
    user = request.user

    debug_info = {
        'user': {
            'username': user.username,
            'is_authenticated': user.is_authenticated,
            'has_employe_attr': hasattr(user, 'employe'),
        },
        'employe': None,
        'demande': {
            'uuid': str(demande.uuid),
            'numero': demande.numero,
            'statut': demande.statut,
        },
        'permission_checks': {}
    }

    # Vérifier l'employe
    if hasattr(user, 'employe'):
        try:
            employe = user.employe
            debug_info['employe'] = {
                'matricule': employe.matricule,
                'nom': employe.nom,
                'prenoms': employe.prenoms,
            }

            # Vérifier les rôles
            try:
                debug_info['employe']['has_role_method'] = hasattr(employe, 'has_role')
                debug_info['employe']['has_ADMIN_GAC'] = employe.has_role('ADMIN_GAC') if hasattr(employe, 'has_role') else 'N/A'
                debug_info['employe']['get_roles'] = [r.role.CODE for r in employe.get_roles()] if hasattr(employe, 'get_roles') else 'N/A'
            except Exception as e:
                debug_info['employe']['role_error'] = str(e)
        except Exception as e:
            debug_info['employe'] = {'error': str(e)}

    # Tester les permissions
    try:
        debug_info['permission_checks']['can_view_demande'] = GACPermissions.can_view_demande(user, demande)
    except Exception as e:
        debug_info['permission_checks']['can_view_demande'] = f'ERROR: {e}'

    try:
        debug_info['permission_checks']['can_submit_demande'] = GACPermissions.can_submit_demande(user, demande)
    except Exception as e:
        debug_info['permission_checks']['can_submit_demande'] = f'ERROR: {e}'

    try:
        debug_info['permission_checks']['can_modify_demande'] = GACPermissions.can_modify_demande(user, demande)
    except Exception as e:
        debug_info['permission_checks']['can_modify_demande'] = f'ERROR: {e}'

    return JsonResponse(debug_info, json_dumps_params={'indent': 2})
