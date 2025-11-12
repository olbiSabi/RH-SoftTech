# employee/utils.py
"""
Utilitaires pour la gestion des employés
"""

from django.urls import reverse


def get_redirect_url_with_tab(request, base_url):
    """
    Construit l'URL de redirection avec l'onglet actif

    Args:
        request: La requête Django (POST ou GET)
        base_url: L'URL de base (ex: /employe/dossier/xxx/)

    Returns:
        URL avec le fragment d'onglet (ex: /employe/dossier/xxx/#emp_coordonnee)

    Usage:
        base_url = reverse('dossier_detail', kwargs={'uuid': employe.uuid})
        redirect_url = get_redirect_url_with_tab(request, base_url)
        return redirect(redirect_url)
    """
    # Récupérer l'onglet actif depuis POST ou GET
    active_tab = request.POST.get('active_tab') or request.GET.get('active_tab')

    if active_tab:
        # S'assurer que le hash est présent
        if not active_tab.startswith('#'):
            active_tab = f'#{active_tab}'
        return f"{base_url}{active_tab}"

    return base_url


def get_active_tab_for_ajax(request):
    """
    Récupère l'onglet actif pour une réponse AJAX

    Returns:
        dict: Dictionnaire à ajouter à la réponse JSON

    Usage dans vos vues AJAX:
        response_data = {
            'success': True,
            'message': '✅ Téléphone ajouté',
            **get_active_tab_for_ajax(request)
        }
        return JsonResponse(response_data)
    """
    active_tab = request.POST.get('active_tab') or request.GET.get('active_tab')

    if active_tab:
        if not active_tab.startswith('#'):
            active_tab = f'#{active_tab}'
        return {'active_tab': active_tab}

    return {}