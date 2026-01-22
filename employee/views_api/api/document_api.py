# employee/views_api/api/document_api.py
"""
API modale pour la gestion des documents (ZYDO).
Gère l'upload de fichiers avec validation.
"""
from typing import Dict, Any
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.decorators import login_required

from employee.models import ZY00, ZYDO
from employee.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


@login_required
def api_document_create_modal(request):
    """
    Créer un document via modal (avec upload de fichier).

    Cette vue ne peut pas utiliser GenericModalCRUDView car elle gère
    l'upload de fichiers via request.FILES.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        # Validation des champs requis
        errors = {}
        if not request.POST.get('type_document'):
            errors['type_document'] = ['Ce champ est requis']
        if not request.FILES.get('fichier'):
            errors['fichier'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        fichier = request.FILES.get('fichier')

        # Validation du fichier
        is_valid, file_errors = ValidationService.validate_file_upload(
            fichier,
            max_size_mb=10.0,
            allowed_extensions=['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'],
            field_name='fichier'
        )

        if not is_valid:
            return JsonResponse({'errors': file_errors}, status=400)

        with transaction.atomic():
            document = ZYDO.objects.create(
                employe=employe,
                type_document=request.POST.get('type_document'),
                fichier=fichier,
                description=request.POST.get('description', ''),
            )

        logger.info(f"Document créé: ID={document.id} pour employé {employe.matricule}")

        return JsonResponse({
            'success': True,
            'message': 'Document ajouté avec succès',
            'id': document.id
        })

    except Exception as e:
        logger.error(f"Erreur création document: {e}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_document_delete_modal(request, id):
    """
    Supprimer un document via modal.
    Supprime également le fichier physique.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        document = get_object_or_404(ZYDO, id=id)

        with transaction.atomic():
            # Supprimer le fichier physique
            if document.fichier:
                document.fichier.delete(save=False)
            document.delete()

        logger.info(f"Document supprimé: ID={id}")

        return JsonResponse({
            'success': True,
            'message': 'Document supprimé avec succès'
        })

    except Exception as e:
        logger.error(f"Erreur suppression document: {e}")
        return JsonResponse({'error': str(e)}, status=400)
