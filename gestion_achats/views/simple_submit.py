"""
Vue de soumission ultra-simplifiée qui fonctionne à coup sûr.
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from gestion_achats.models import GACDemandeAchat
from gestion_achats.services import DemandeService


@csrf_exempt  # TEMPORAIRE: Désactiver CSRF pour déboguer
@require_POST  # Seulement POST
def simple_demande_submit(request, pk):
    """
    Soumission ultra-simple sans décorateurs complexes.
    Fonctionne avec ou sans AJAX.
    """
    try:
        # 1. Charger la demande
        demande = get_object_or_404(GACDemandeAchat, uuid=pk)

        # 2. Vérifier que l'utilisateur est authentifié
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': "Vous devez être connecté pour soumettre une demande."
                }, status=401)
            messages.error(request, "Vous devez être connecté.")
            return redirect('login')

        # 3. Vérifier que l'utilisateur a un employe
        if not hasattr(request.user, 'employe') or not request.user.employe:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': "Votre compte n'est pas associé à un employé."
                }, status=400)
            messages.error(request, "Votre compte n'est pas associé à un employé.")
            return redirect('gestion_achats:dashboard')

        # 4. Soumettre la demande (le service fait les vérifications de permission)
        DemandeService.soumettre_demande(demande, request.user.employe)

        # 5. Retourner la réponse appropriée
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Demande {demande.numero} soumise pour validation.',
                'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
            })
        else:
            messages.success(request, f'Demande {demande.numero} soumise pour validation.')
            return redirect('gestion_achats:demande_detail', pk=demande.uuid)

    except Exception as e:
        # Gérer toutes les erreurs
        error_message = str(e)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {error_message}'
            }, status=400)
        else:
            messages.error(request, f'Erreur: {error_message}')
            return redirect('gestion_achats:demande_detail', pk=pk)
