"""
Vue de débogage pour vérifier les permissions et l'association employe.
À SUPPRIMER EN PRODUCTION.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
def debug_user_info(request):
    """Affiche les informations de l'utilisateur pour le débogage."""

    user = request.user

    # Collecter les informations
    info = {
        'username': user.username,
        'email': user.email,
        'is_authenticated': user.is_authenticated,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'has_employe_attr': hasattr(user, 'employe'),
    }

    # Vérifier si l'utilisateur a un employe
    if hasattr(user, 'employe'):
        try:
            employe = user.employe
            info['employe'] = {
                'matricule': employe.matricule,
                'nom': employe.nom,
                'prenoms': employe.prenoms,  # Notez: "prenoms" avec un "s"
                'username': employe.username if hasattr(employe, 'username') else None,
                'email': employe.email_professionnel if hasattr(employe, 'email_professionnel') else None,
                'departement': str(employe.departement) if hasattr(employe, 'departement') and employe.departement else None,
            }

            # Récupérer les rôles
            info['roles'] = []
            if hasattr(employe, 'roles'):
                try:
                    info['roles'] = [role.nom for role in employe.roles.all()]
                except Exception as e:
                    info['roles_error'] = str(e)

        except Exception as e:
            info['employe'] = None
            info['employe_error'] = str(e)
    else:
        info['employe'] = None
        info['employe_message'] = "L'utilisateur n'a pas d'enregistrement employe associé"

    # Retourner JSON si c'est une requête AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(info)

    # Sinon retourner HTML
    return render(request, 'gestion_achats/debug/user_info.html', {'info': info})
