# employee/views_api/api/identite_bancaire_api.py
"""
API pour la gestion de l'identité bancaire (ZYIB).
"""
from datetime import datetime
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError

from employee.models import ZY00, ZYIB

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@login_required
def api_identite_bancaire_detail(request, employe_uuid):
    """Récupérer les détails de l'identité bancaire d'un employé."""
    try:
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        try:
            ib = employe.identite_bancaire
            data = {
                'id': ib.id,
                'titulaire_compte': ib.titulaire_compte,
                'nom_banque': ib.nom_banque,
                'code_banque': ib.code_banque,
                'code_guichet': ib.code_guichet,
                'numero_compte': ib.numero_compte,
                'cle_rib': ib.cle_rib,
                'iban': ib.iban or '',
                'bic': ib.bic or '',
                'type_compte': ib.type_compte,
                'domiciliation': ib.domiciliation or '',
                'date_ouverture': ib.date_ouverture.strftime('%Y-%m-%d') if ib.date_ouverture else '',
                'remarques': ib.remarques or '',
                'actif': ib.actif,
                'rib_complet': ib.get_rib(),
                'iban_formate': ib.get_iban_formate(),
            }
            return JsonResponse(data)
        except ZYIB.DoesNotExist:
            return JsonResponse({'error': 'Aucune identité bancaire enregistrée'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_identite_bancaire_create_or_update(request, employe_uuid):
    """Créer ou mettre à jour l'identité bancaire d'un employé."""
    try:
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        # Validation de base
        errors = {}
        required_fields = ['titulaire_compte', 'nom_banque', 'code_banque', 'code_guichet',
                           'numero_compte', 'cle_rib']

        for field in required_fields:
            value = request.POST.get(field)
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Récupération des données
        data = {
            'titulaire_compte': request.POST.get('titulaire_compte'),
            'nom_banque': request.POST.get('nom_banque'),
            'code_banque': request.POST.get('code_banque'),
            'code_guichet': request.POST.get('code_guichet'),
            'numero_compte': request.POST.get('numero_compte'),
            'cle_rib': request.POST.get('cle_rib'),
            'iban': request.POST.get('iban', ''),
            'bic': request.POST.get('bic', ''),
            'type_compte': request.POST.get('type_compte', 'COURANT'),
            'domiciliation': request.POST.get('domiciliation', ''),
            'remarques': request.POST.get('remarques', ''),
            'actif': request.POST.get('actif') == 'on',
        }

        # Date d'ouverture
        date_ouverture = request.POST.get('date_ouverture')
        if date_ouverture:
            try:
                data['date_ouverture'] = datetime.strptime(date_ouverture, '%Y-%m-%d').date()
            except ValueError:
                errors['date_ouverture'] = ['Format de date invalide']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Créer ou mettre à jour
        with transaction.atomic():
            ib, created = ZYIB.objects.update_or_create(
                employe=employe,
                defaults=data
            )

            # Valider le modèle
            try:
                ib.full_clean()
            except ValidationError as e:
                return JsonResponse({'errors': e.message_dict}, status=400)

            ib.save()
            logger.info(f"Identité bancaire {'créée' if created else 'modifiée'}: {ib.id}")

        return JsonResponse({
            'success': True,
            'message': f'Identité bancaire {"créée" if created else "modifiée"} avec succès',
            'id': ib.id
        })

    except Exception as e:
        logger.error(f"Erreur identité bancaire: {e}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_identite_bancaire_delete(request, employe_uuid):
    """Supprimer l'identité bancaire d'un employé."""
    try:
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        try:
            ib = employe.identite_bancaire
            with transaction.atomic():
                ib.delete()

            logger.info(f"Identité bancaire supprimée pour {employe.matricule}")
            return JsonResponse({
                'success': True,
                'message': 'Identité bancaire supprimée avec succès'
            })
        except ZYIB.DoesNotExist:
            return JsonResponse({'error': 'Aucune identité bancaire à supprimer'}, status=404)

    except Exception as e:
        logger.error(f"Erreur suppression identité bancaire: {e}")
        return JsonResponse({'error': str(e)}, status=400)
