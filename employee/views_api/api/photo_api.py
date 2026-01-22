# employee/views_api/api/photo_api.py
"""
API pour la gestion des photos de profil employé.
"""
import os
import time
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from employee.models import ZY00
from employee.utils import get_active_tab_for_ajax

logger = logging.getLogger(__name__)

# Extensions autorisées pour les photos
VALID_PHOTO_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
# Taille maximale: 5 MB
MAX_PHOTO_SIZE = 5 * 1024 * 1024


@require_POST
@login_required
def modifier_photo_ajax(request):
    """Vue AJAX pour modifier la photo de profil d'un employé."""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        photo = request.FILES.get('photo')

        if not employe_uuid or not photo:
            return JsonResponse({
                'success': False,
                'error': 'UUID de l\'employé ou photo manquant'
            })

        # Récupérer l'employé
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        # Vérifier la taille du fichier
        if photo.size > MAX_PHOTO_SIZE:
            return JsonResponse({
                'success': False,
                'error': 'La taille de la photo ne doit pas dépasser 5 MB'
            })

        # Vérifier l'extension du fichier
        ext = os.path.splitext(photo.name)[1].lower()
        if ext not in VALID_PHOTO_EXTENSIONS:
            return JsonResponse({
                'success': False,
                'error': f'Format non autorisé. Formats acceptés: {", ".join(VALID_PHOTO_EXTENSIONS)}'
            })

        # Supprimer l'ancienne photo si elle existe
        if employe.photo:
            try:
                if os.path.isfile(employe.photo.path):
                    os.remove(employe.photo.path)
            except Exception:
                pass  # Ignorer les erreurs de suppression

        # Enregistrer la nouvelle photo
        employe.photo = photo
        employe.save()

        # Ajouter timestamp à l'URL pour forcer le refresh du cache navigateur
        timestamp = int(time.time())
        photo_url_with_timestamp = f"{employe.photo.url}?t={timestamp}"

        logger.info(f"Photo modifiée pour {employe.matricule}")

        return JsonResponse({
            'success': True,
            'photo_url': photo_url_with_timestamp,
            **get_active_tab_for_ajax(request)
        })

    except Exception as e:
        logger.error(f"Erreur modification photo: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_POST
@login_required
def supprimer_photo_ajax(request, uuid):
    """Vue AJAX pour supprimer la photo de profil d'un employé."""
    try:
        employe = get_object_or_404(ZY00, uuid=uuid)

        # Supprimer le fichier photo
        if employe.photo:
            try:
                if os.path.isfile(employe.photo.path):
                    os.remove(employe.photo.path)
            except Exception:
                pass

        # Supprimer la référence dans la base de données
        employe.photo = None
        employe.save()

        logger.info(f"Photo supprimée pour {employe.matricule}")

        return JsonResponse({
            'success': True,
            'photo_url': employe.get_photo_url(),
            **get_active_tab_for_ajax(request)
        })

    except Exception as e:
        logger.error(f"Erreur suppression photo: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
