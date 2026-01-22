# absence/views_api/parametre_calcul_api.py
"""
API pour la gestion des paramètres de calcul des congés.
"""
import logging

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST

from absence.decorators import drh_or_admin_required, gestion_app_required
from absence.models import ParametreCalculConges
from absence.forms import ParametreCalculCongesForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@login_required
@drh_or_admin_required
@gestion_app_required
def api_parametre_calcul_detail(request, id):
    """Récupérer les détails d'un paramètre (pour édition)"""
    try:
        parametre = get_object_or_404(ParametreCalculConges, id=id)

        jours_supp = parametre.jours_supp_anciennete or {}

        data = {
            'id': parametre.id,
            'configuration': parametre.configuration_id,
            'mois_acquisition_min': parametre.mois_acquisition_min,
            'plafond_jours_an': parametre.plafond_jours_an,
            'report_autorise': parametre.report_autorise,
            'jours_report_max': parametre.jours_report_max,
            'delai_prise_report': parametre.delai_prise_report,
            'prise_compte_temps_partiel': parametre.prise_compte_temps_partiel,
            'anciennete_5_ans': jours_supp.get('5', 0),
            'anciennete_10_ans': jours_supp.get('10', 0),
            'anciennete_15_ans': jours_supp.get('15', 0),
            'anciennete_20_ans': jours_supp.get('20', 0),
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_parametre_calcul_create(request):
    """Créer un paramètre via modal"""
    try:
        configuration_id = request.POST.get('configuration')
        if ParametreCalculConges.objects.filter(configuration_id=configuration_id).exists():
            return JsonResponse({
                'success': False,
                'errors': {'configuration': ['Un paramètre existe déjà pour cette convention']}
            }, status=400)

        data = request.POST.copy()

        jours_supp_anciennete = {}
        for annees in ['5', '10', '15', '20']:
            valeur = request.POST.get(f'anciennete_{annees}_ans', 0)
            if valeur and int(valeur) > 0:
                jours_supp_anciennete[annees] = int(valeur)

        form = ParametreCalculCongesForm(data)

        if form.is_valid():
            with transaction.atomic():
                parametre = form.save()

            return JsonResponse({
                'success': True,
                'message': 'Paramètre créé avec succès',
                'id': parametre.id
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = str(error_list[0])

            return JsonResponse({'success': False, 'errors': errors}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_parametre_calcul_update(request, id):
    """Mettre à jour un paramètre via modal"""
    try:
        parametre = get_object_or_404(ParametreCalculConges, id=id)

        data = request.POST.copy()

        form = ParametreCalculCongesForm(data, instance=parametre)

        if form.is_valid():
            with transaction.atomic():
                parametre = form.save()

            return JsonResponse({
                'success': True,
                'message': 'Paramètre modifié avec succès'
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = str(error_list[0])

            return JsonResponse({'success': False, 'errors': errors}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_parametre_calcul_delete(request, id):
    """Supprimer un paramètre"""
    try:
        parametre = get_object_or_404(ParametreCalculConges, id=id)

        convention_nom = parametre.configuration.nom
        with transaction.atomic():
            parametre.delete()

        return JsonResponse({
            'success': True,
            'message': f'Paramètres de "{convention_nom}" supprimés avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
