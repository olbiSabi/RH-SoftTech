# absence/views_api/acquisition_api.py
"""
API pour la gestion des acquisitions de congés.
"""
import logging
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from absence.decorators import drh_or_admin_required, gestion_app_required
from absence.models import AcquisitionConges, ConfigurationConventionnelle
from absence.forms import CalculAcquisitionForm
from absence.utils import calculer_jours_acquis_au
from employee.models import ZY00

logger = logging.getLogger(__name__)


def calculer_jours_acquis_au_mensuel(employe, annee, date_reference):
    """Calcul mensuel progressif pour la fonction api_calculer_acquis_a_date"""
    return calculer_jours_acquis_au(employe, annee, date_reference)


@require_http_methods(["GET"])
@login_required
@drh_or_admin_required
@gestion_app_required
def api_acquisition_detail(request, id):
    """Récupérer les détails d'une acquisition (pour édition)"""
    try:
        acquisition = get_object_or_404(AcquisitionConges, id=id)

        data = {
            'id': acquisition.id,
            'employe': acquisition.employe_id,
            'employe_nom': str(acquisition.employe),
            'annee_reference': acquisition.annee_reference,
            'jours_acquis': str(acquisition.jours_acquis),
            'jours_pris': str(acquisition.jours_pris),
            'jours_restants': str(acquisition.jours_restants),
            'jours_report_anterieur': str(acquisition.jours_report_anterieur),
            'jours_report_nouveau': str(acquisition.jours_report_nouveau),
            'date_calcul': acquisition.date_calcul.strftime('%Y-%m-%d %H:%M'),
            'date_maj': acquisition.date_maj.strftime('%Y-%m-%d %H:%M'),
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_acquisition_update(request, id):
    """Mettre à jour une acquisition (principalement le report antérieur)"""
    try:
        acquisition = get_object_or_404(AcquisitionConges, id=id)

        jours_report_anterieur = request.POST.get('jours_report_anterieur')

        if jours_report_anterieur is not None:
            with transaction.atomic():
                acquisition.jours_report_anterieur = Decimal(jours_report_anterieur)
                acquisition.save()

            return JsonResponse({
                'success': True,
                'message': 'Acquisition mise à jour avec succès',
                'jours_restants': str(acquisition.jours_restants)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Aucune donnée à mettre à jour'
            }, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_acquisition_delete(request, id):
    """Supprimer une acquisition"""
    try:
        acquisition = get_object_or_404(AcquisitionConges, id=id)

        employe_nom = str(acquisition.employe)
        annee = acquisition.annee_reference

        with transaction.atomic():
            acquisition.delete()

        return JsonResponse({
            'success': True,
            'message': f'Acquisition de {employe_nom} pour {annee} supprimée'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_calculer_acquisitions(request):
    """Calcule automatiquement les acquisitions pour une année donnée"""
    from datetime import timedelta

    try:
        logger.debug("POST data: %s", request.POST)

        form = CalculAcquisitionForm(request.POST)

        if not form.is_valid():
            logger.error("Formulaire invalide: %s", form.errors)
            return JsonResponse({
                'success': False,
                'errors': {field: errors[0] for field, errors in form.errors.items()}
            }, status=400)

        annee = form.cleaned_data['annee_reference']
        recalculer = form.cleaned_data['recalculer_existantes']
        employes_selection = form.cleaned_data.get('employes')

        date_reference_str = request.POST.get('date_reference')
        if date_reference_str:
            date_reference = datetime.strptime(date_reference_str, '%Y-%m-%d').date()
        else:
            date_reference = timezone.now().date()

        date_actuelle = timezone.now().date()

        try:
            convention_entreprise = ConfigurationConventionnelle.objects.filter(
                type_convention='ENTREPRISE',
                actif=True
            ).first()

            if not convention_entreprise:
                return JsonResponse({
                    'success': False,
                    'error': 'Aucune convention d\'entreprise active trouvée.'
                }, status=400)

            _, fin_periode = convention_entreprise.get_periode_acquisition(annee)
            date_limite_recalcul = fin_periode + timedelta(days=2)

            if date_actuelle > date_limite_recalcul:
                return JsonResponse({
                    'success': False,
                    'error': f'Impossible de recalculer l\'année {annee}.\n'
                             f'Le délai a expiré le {date_limite_recalcul.strftime("%d/%m/%Y")}.'
                }, status=403)

        except Exception as e:
            logger.error("Erreur vérification convention: %s", e)
            return JsonResponse({
                'success': False,
                'error': f'Erreur vérification: {str(e)}'
            }, status=500)

        inactifs_exclus = 0

        if employes_selection is not None and employes_selection.exists():
            inactifs_exclus = employes_selection.exclude(etat='actif').count()
            employes = employes_selection.filter(
                etat='actif',
                entreprise__isnull=False
            )
        else:
            employes = ZY00.objects.filter(
                etat='actif',
                entreprise__isnull=False
            )

        if not employes.exists():
            return JsonResponse({
                'success': False,
                'error': 'Aucun employé actif à traiter'
            }, status=400)

        resultats = {
            'total': 0,
            'crees': 0,
            'mis_a_jour': 0,
            'ignores': 0,
            'erreurs': 0,
            'details_erreurs': []
        }

        for employe in employes:
            resultats['total'] += 1

            try:
                if not employe.convention_applicable:
                    resultats['erreurs'] += 1
                    resultats['details_erreurs'].append({
                        'employe': str(employe),
                        'erreur': 'Aucune convention applicable'
                    })
                    continue

                acquisition, created = AcquisitionConges.objects.get_or_create(
                    employe=employe,
                    annee_reference=annee,
                    defaults={
                        'jours_acquis': Decimal('0.00'),
                        'jours_pris': Decimal('0.00'),
                        'jours_restants': Decimal('0.00'),
                        'jours_report_anterieur': Decimal('0.00'),
                        'jours_report_nouveau': Decimal('0.00'),
                    }
                )

                if created or recalculer:
                    resultat = calculer_jours_acquis_au(
                        employe,
                        annee,
                        date_reference
                    )

                    acquisition.jours_acquis = resultat['jours_acquis']
                    acquisition.save()

                    if created:
                        resultats['crees'] += 1
                    else:
                        resultats['mis_a_jour'] += 1
                else:
                    resultats['ignores'] += 1

            except Exception as e:
                import traceback
                logger.error("Erreur %s: %s", employe, traceback.format_exc())
                resultats['erreurs'] += 1
                resultats['details_erreurs'].append({
                    'employe': str(employe),
                    'erreur': str(e)
                })

        message_parts = [
            f'{resultats["crees"]} créées',
            f'{resultats["mis_a_jour"]} mises à jour',
            f'{resultats["ignores"]} ignorées'
        ]

        if resultats['erreurs'] > 0:
            message_parts.append(f'{resultats["erreurs"]} erreurs')

        if inactifs_exclus > 0:
            message_parts.append(f'{inactifs_exclus} inactif(s) exclu(s)')

        return JsonResponse({
            'success': True,
            'message': ', '.join(message_parts),
            'resultats': resultats
        })

    except Exception as e:
        import traceback
        logger.exception("ERREUR GLOBALE: %s", traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_recalculer_acquisition(request, id):
    """Recalcule une acquisition spécifique"""
    try:
        acquisition = get_object_or_404(AcquisitionConges, id=id)

        logger.info("RECALCUL - Acquisition ID: %s, Employé: %s, Année: %s",
                    id, acquisition.employe, acquisition.annee_reference)

        date_reference = timezone.now().date()

        resultat = calculer_jours_acquis_au(
            acquisition.employe,
            acquisition.annee_reference,
            date_reference
        )

        with transaction.atomic():
            acquisition.jours_acquis = resultat['jours_acquis']
            acquisition.save()

        return JsonResponse({
            'success': True,
            'message': 'Acquisition recalculée avec succès',
            'jours_acquis': str(acquisition.jours_acquis),
            'jours_restants': str(acquisition.jours_restants),
            'mois_travailles': str(resultat['mois_travailles'])
        })

    except Exception as e:
        import traceback
        logger.error("ERREUR recalcul: %s", traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
@login_required
@gestion_app_required
def api_calculer_acquis_a_date(request):
    """Calcule les jours acquis à une date donnée"""
    try:
        employe_id = request.GET.get('employe_id')
        annee = request.GET.get('annee')
        date_str = request.GET.get('date')

        if not employe_id or not annee:
            return JsonResponse({
                'success': False,
                'error': 'Paramètres manquants'
            }, status=400)

        try:
            employe = ZY00.objects.get(uuid=employe_id)
        except ZY00.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Employé non trouvé'
            }, status=404)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Format d\'UUID invalide'
            }, status=400)

        annee = int(annee)

        if date_str:
            date_reference = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date_reference = timezone.now().date()

        if date_reference.year != annee:
            return JsonResponse({
                'success': False,
                'error': f'La date de référence doit être dans l\'année {annee}'
            }, status=400)

        if not employe.convention_applicable:
            return JsonResponse({
                'success': False,
                'error': f'Aucune convention applicable pour {employe}'
            }, status=400)

        resultat = calculer_jours_acquis_au_mensuel(employe, annee, date_reference)

        return JsonResponse({
            'success': True,
            'data': {
                'employe': str(employe),
                'matricule': employe.matricule,
                'annee_reference': annee,
                'date_reference': date_reference.strftime('%d/%m/%Y'),
                'jours_acquis': str(resultat['jours_acquis']),
                'mois_travailles': resultat['mois_travailles'],
                'detail': resultat['detail'],
                'convention': str(employe.convention_applicable),
                'jours_par_mois': float(employe.convention_applicable.jours_acquis_par_mois)
            }
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception as e:
        logger.error("Erreur api_calculer_acquis_a_date: %s", str(e))
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du calcul: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@login_required
@drh_or_admin_required
@gestion_app_required
def api_acquisition_employe_annee(request, employe_id, annee):
    """Récupérer l'acquisition de congés d'un employé pour une année"""
    try:
        user_employe = request.user.employe

        if user_employe.matricule != employe_id:
            return JsonResponse({
                'success': False,
                'error': 'Vous ne pouvez consulter que votre propre solde'
            }, status=403)

        acquisition = get_object_or_404(
            AcquisitionConges,
            employe=user_employe,
            annee_reference=annee
        )

        data = {
            'jours_acquis': str(acquisition.jours_acquis),
            'jours_pris': str(acquisition.jours_pris),
            'jours_restants': str(acquisition.jours_restants),
            'jours_report_anterieur': str(acquisition.jours_report_anterieur),
            'jours_report_nouveau': str(acquisition.jours_report_nouveau),
        }

        return JsonResponse({
            'success': True,
            'data': data
        })

    except AcquisitionConges.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Aucune acquisition trouvée pour cette année'
        }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
