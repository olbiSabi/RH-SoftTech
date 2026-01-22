# absence/views_api/jour_ferie_api.py
"""
API pour la gestion des jours fériés.
"""
import json
import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from absence.decorators import drh_or_admin_required, gestion_app_required
from absence.models import JourFerie
from absence.forms import JourFerieForm

logger = logging.getLogger(__name__)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_http_methods(["GET"])
def api_jour_ferie_detail(request, id):
    """Retourne les détails d'un jour férié en JSON"""
    try:
        jour_ferie = get_object_or_404(JourFerie, pk=id)

        data = {
            'id': jour_ferie.id,
            'nom': jour_ferie.nom,
            'date': jour_ferie.date.strftime('%Y-%m-%d'),
            'type_ferie': jour_ferie.type_ferie,
            'recurrent': jour_ferie.recurrent,
            'description': jour_ferie.description or '',
            'actif': jour_ferie.actif,
            'annee': jour_ferie.annee,
            'mois_nom': jour_ferie.mois_nom,
            'jour_semaine': jour_ferie.jour_semaine,
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        logger.exception("Erreur lors de la récupération du jour férié:")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_jour_ferie_create(request):
    """Crée un nouveau jour férié via AJAX"""
    try:
        form = JourFerieForm(request.POST)

        if form.is_valid():
            jour_ferie = form.save(commit=False)

            try:
                jour_ferie.created_by = request.user.zy00
            except Exception:
                pass

            jour_ferie.save()

            messages.success(request, f"Jour férié '{jour_ferie.nom}' créé avec succès")

            return JsonResponse({
                'success': True,
                'message': f"Jour férié '{jour_ferie.nom}' créé avec succès",
                'id': jour_ferie.id
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
        logger.exception("Erreur lors de la création du jour férié:")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_jour_ferie_update(request, id):
    """Met à jour un jour férié existant via AJAX"""
    try:
        jour_ferie = get_object_or_404(JourFerie, pk=id)
        form = JourFerieForm(request.POST, instance=jour_ferie)

        if form.is_valid():
            jour_ferie = form.save()

            messages.success(request, f"Jour férié '{jour_ferie.nom}' modifié avec succès")

            return JsonResponse({
                'success': True,
                'message': f"Jour férié '{jour_ferie.nom}' modifié avec succès"
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
def api_jour_ferie_delete(request, id):
    """Supprime un jour férié via AJAX"""
    try:
        jour_ferie = get_object_or_404(JourFerie, pk=id)
        nom = jour_ferie.nom

        jour_ferie.delete()

        messages.success(request, f"Jour férié '{nom}' supprimé avec succès")

        return JsonResponse({
            'success': True,
            'message': f"Jour férié '{nom}' supprimé avec succès"
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
def api_jour_ferie_toggle(request, id):
    """Active/Désactive un jour férié via AJAX"""
    try:
        jour_ferie = get_object_or_404(JourFerie, pk=id)
        jour_ferie.actif = not jour_ferie.actif
        jour_ferie.save()

        statut = "activé" if jour_ferie.actif else "désactivé"
        messages.success(request, f"Jour férié '{jour_ferie.nom}' {statut} avec succès")

        return JsonResponse({
            'success': True,
            'message': f"Jour férié '{jour_ferie.nom}' {statut} avec succès",
            'actif': jour_ferie.actif
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
def api_dupliquer_jours_feries(request):
    """Duplique les jours fériés d'une année vers une autre"""
    try:
        data = json.loads(request.body)
        annee_source = int(data.get('annee_source'))
        annee_cible = int(data.get('annee_cible'))

        if not annee_source or not annee_cible:
            return JsonResponse({
                'success': False,
                'error': 'Années source et cible requises'
            }, status=400)

        if annee_source == annee_cible:
            return JsonResponse({
                'success': False,
                'error': 'Les années source et cible doivent être différentes'
            }, status=400)

        jours_source = JourFerie.objects.filter(
            date__year=annee_source,
            recurrent=True
        )

        if not jours_source.exists():
            return JsonResponse({
                'success': False,
                'error': f'Aucun jour férié récurrent trouvé pour l\'année {annee_source}'
            }, status=400)

        created_count = 0
        for jour in jours_source:
            nouvelle_date = jour.date.replace(year=annee_cible)

            existe = JourFerie.objects.filter(
                nom=jour.nom,
                date=nouvelle_date
            ).exists()

            if not existe:
                JourFerie.objects.create(
                    nom=jour.nom,
                    date=nouvelle_date,
                    type_ferie=jour.type_ferie,
                    recurrent=jour.recurrent,
                    description=jour.description,
                    actif=True,
                    created_by=request.user.zy00 if hasattr(request.user, 'zy00') else None
                )
                created_count += 1

        messages.success(
            request,
            f"{created_count} jour(s) férié(s) dupliqué(s) de {annee_source} vers {annee_cible}"
        )

        return JsonResponse({
            'success': True,
            'message': f"{created_count} jour(s) férié(s) dupliqué(s) avec succès",
            'count': created_count
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def api_jours_feries(request):
    """Récupérer les jours fériés pour le calendrier"""
    try:
        start = request.GET.get('start')
        end = request.GET.get('end')

        if not start or not end:
            return JsonResponse({'success': False, 'error': 'Paramètres manquants'}, status=400)

        start_date = timezone.datetime.strptime(start, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(end, '%Y-%m-%d').date()

        jours_feries = JourFerie.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            actif=True
        ).order_by('date')

        data = []
        for jf in jours_feries:
            data.append({
                'id': jf.id,
                'nom': jf.nom,
                'date': jf.date.strftime('%Y-%m-%d'),
                'type_ferie': jf.type_ferie,
                'recurrent': jf.recurrent,
                'description': jf.description or '',
                'actif': jf.actif,
                'annee': jf.annee,
                'mois_nom': jf.mois_nom,
                'jour_semaine': jf.jour_semaine,
            })

        return JsonResponse({
            'success': True,
            'jours_feries': data
        })

    except Exception as e:
        logger.exception("Erreur API Jours Fériés:")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
