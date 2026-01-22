# absence/views_api/type_absence_api.py
"""
API pour la gestion des types d'absence.
"""
import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST

from absence.decorators import drh_or_admin_required, gestion_app_required
from absence.models import TypeAbsence
from absence.forms import TypeAbsenceForm

logger = logging.getLogger(__name__)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_http_methods(["GET"])
def api_type_absence_detail(request, id):
    """Retourne les détails d'un type d'absence en JSON"""
    try:
        type_absence = get_object_or_404(TypeAbsence, pk=id)

        data = {
            'id': type_absence.id,
            'code': type_absence.code,
            'libelle': type_absence.libelle,
            'categorie': type_absence.categorie,
            'paye': type_absence.paye,
            'decompte_solde': type_absence.decompte_solde,
            'justificatif_obligatoire': type_absence.justificatif_obligatoire,
            'couleur': type_absence.couleur,
            'ordre': type_absence.ordre,
            'actif': type_absence.actif,
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_create(request):
    """Crée un nouveau type d'absence via AJAX"""
    try:
        logger.debug("Données reçues: %s", request.POST)

        form = TypeAbsenceForm(request.POST)

        if form.is_valid():
            type_absence = form.save()

            messages.success(
                request,
                f"Type d'absence '{type_absence.code} - {type_absence.libelle}' créé avec succès"
            )

            return JsonResponse({
                'success': True,
                'message': f"Type d'absence '{type_absence.code}' créé avec succès",
                'id': type_absence.id
            })
        else:
            logger.error("Erreurs formulaire: %s", form.errors)

            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]

            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

    except Exception as e:
        logger.exception("Exception lors de la création du type d'absence:")

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_update(request, id):
    """Met à jour un type d'absence existant via AJAX"""
    try:
        type_absence = get_object_or_404(TypeAbsence, pk=id)
        form = TypeAbsenceForm(request.POST, instance=type_absence)

        if form.is_valid():
            type_absence = form.save()

            messages.success(
                request,
                f"Type d'absence '{type_absence.code} - {type_absence.libelle}' modifié avec succès"
            )

            return JsonResponse({
                'success': True,
                'message': f"Type d'absence '{type_absence.code}' modifié avec succès"
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]

            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_delete(request, id):
    """Supprime un type d'absence via AJAX"""
    try:
        type_absence = get_object_or_404(TypeAbsence, pk=id)
        code = type_absence.code
        libelle = type_absence.libelle

        type_absence.delete()

        messages.success(request, f"Type d'absence '{code} - {libelle}' supprimé avec succès")

        return JsonResponse({
            'success': True,
            'message': f"Type d'absence '{code}' supprimé avec succès"
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_toggle(request, id):
    """Active/Désactive un type d'absence via AJAX"""
    try:
        type_absence = get_object_or_404(TypeAbsence, pk=id)
        type_absence.actif = not type_absence.actif
        type_absence.save()

        statut = "activé" if type_absence.actif else "désactivé"
        messages.success(
            request,
            f"Type d'absence '{type_absence.code}' {statut} avec succès"
        )

        return JsonResponse({
            'success': True,
            'message': f"Type d'absence '{type_absence.code}' {statut} avec succès",
            'actif': type_absence.actif
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
