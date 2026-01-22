# absence/views_api/absence_api.py
"""
API pour la gestion des absences.
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from absence.models import Absence, AcquisitionConges, ValidationAbsence
from employee.models import ZY00

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@login_required
def api_absence_detail(request, id):
    """Récupérer les détails d'une absence"""
    try:
        absence = get_object_or_404(Absence, id=id)
        user_employe = request.user.employe

        if not (absence.employe == user_employe or
                user_employe.has_role('DRH') or
                user_employe.has_role('RH_VALIDATION_ABS') or
                user_employe.has_role('ASSISTANT_RH') or
                user_employe.has_role('GESTION_APP') or
                user_employe.est_manager_departement()):
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        data = {
            'id': absence.id,
            'employe': str(absence.employe),
            'employe_matricule': absence.employe.matricule,
            'type_absence': str(absence.type_absence),
            'date_debut': absence.date_debut.strftime('%Y-%m-%d'),
            'date_fin': absence.date_fin.strftime('%Y-%m-%d'),
            'periode': absence.get_periode_display(),
            'jours_ouvrables': str(absence.jours_ouvrables),
            'jours_calendaires': absence.jours_calendaires,
            'statut': absence.statut,
            'statut_display': absence.get_statut_display(),
            'motif': absence.motif or '',
            'commentaire_manager': absence.commentaire_manager or '',
            'commentaire_rh': absence.commentaire_rh or '',
            'justificatif_url': absence.justificatif.url if absence.justificatif else None,
            'manager_validateur': str(absence.manager_validateur) if absence.manager_validateur else None,
            'rh_validateur': str(absence.rh_validateur) if absence.rh_validateur else None,
            'date_validation_manager': absence.date_validation_manager.strftime('%Y-%m-%d %H:%M') if absence.date_validation_manager else None,
            'date_validation_rh': absence.date_validation_rh.strftime('%Y-%m-%d %H:%M') if absence.date_validation_rh else None,
            'created_at': absence.created_at.strftime('%Y-%m-%d %H:%M'),
            'peut_modifier': absence.peut_modifier,
            'peut_supprimer': absence.peut_supprimer,
            'peut_annuler': absence.peut_annuler,
            'annee_acquisition_utilisee': absence.annee_acquisition_utilisee,
            'solde_disponible': str(absence.get_solde_disponible()),
        }

        validations = ValidationAbsence.objects.filter(absence=absence).order_by('ordre')
        data['validations'] = [{
            'etape': v.get_etape_display(),
            'validateur': str(v.validateur),
            'decision': v.get_decision_display(),
            'commentaire': v.commentaire,
            'date': v.date_validation.strftime('%Y-%m-%d %H:%M') if v.date_validation else 'En attente'
        } for v in validations]

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def api_absence_delete(request, id):
    """Supprimer une absence"""
    try:
        absence = get_object_or_404(Absence, id=id)
        user_employe = request.user.employe

        if absence.employe != user_employe:
            return JsonResponse({
                'success': False,
                'error': 'Vous ne pouvez supprimer que vos propres absences'
            }, status=403)

        if not absence.peut_supprimer:
            return JsonResponse({
                'success': False,
                'error': f'Impossible de supprimer une absence avec le statut "{absence.get_statut_display()}"'
            }, status=400)

        type_absence = absence.type_absence.libelle

        with transaction.atomic():
            absence.delete()

        logger.info("Absence supprimée: %s", type_absence)

        return JsonResponse({
            'success': True,
            'message': f'Absence "{type_absence}" supprimée avec succès'
        })

    except Exception as e:
        logger.exception("ERREUR lors de la suppression:")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@login_required
def api_absence_annuler(request, id):
    """Annuler une absence"""
    try:
        absence = get_object_or_404(Absence, id=id)
        user_employe = request.user.employe

        if absence.employe != user_employe:
            logger.warning("Employé différent: %s tenté d'annuler l'absence de %s", user_employe, absence.employe)
            return JsonResponse({
                'success': False,
                'error': 'Vous ne pouvez annuler que vos propres absences'
            }, status=403)

        if not absence.peut_annuler:
            logger.warning("L'absence ne peut pas être annulée (statut: %s)", absence.statut)
            return JsonResponse({
                'success': False,
                'error': f'Impossible d\'annuler une absence avec le statut "{absence.get_statut_display()}"'
            }, status=400)

        with transaction.atomic():
            absence.annuler(user_employe)

        logger.info("Absence annulée avec succès par %s", user_employe)

        return JsonResponse({
            'success': True,
            'message': f'Absence "{absence.type_absence.libelle}" annulée avec succès'
        })

    except ValidationError as e:
        logger.error("ValidationError: %s", e)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.exception("ERREUR lors de l'annulation:")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@login_required
def api_valider_absence(request, id):
    """Valider ou rejeter une absence (manager ou RH)"""
    try:
        absence = get_object_or_404(Absence, id=id)
        user_employe = request.user.employe

        decision = request.POST.get('decision')
        commentaire = request.POST.get('commentaire', '').strip()

        logger.info("Validation demandée par %s - Absence ID: %s, Décision: %s",
                    user_employe, id, decision)

        if absence.statut == 'EN_ATTENTE_MANAGER':
            absence.valider_par_manager(user_employe, decision, commentaire)
            message = f'Absence {decision.lower()}e par le manager'

        elif absence.statut == 'EN_ATTENTE_RH':
            absence.valider_par_rh(user_employe, decision, commentaire)
            message = f'Absence {decision.lower()}e par les RH'

        else:
            return JsonResponse({
                'success': False,
                'error': 'Cette absence n\'est pas en attente de validation'
            }, status=400)

        return JsonResponse({
            'success': True,
            'message': message
        })

    except ValidationError as e:
        logger.error("Erreur de validation: %s", e)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception as e:
        logger.exception("Erreur serveur:")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def api_historique_validation(request, id):
    """Récupérer l'historique de validation d'une absence"""
    try:
        absence = get_object_or_404(Absence, id=id)

        validations = ValidationAbsence.objects.filter(
            absence=absence
        ).select_related('validateur').order_by('ordre')

        data = [{
            'etape': v.get_etape_display(),
            'ordre': v.ordre,
            'validateur': {
                'nom': v.validateur.nom,
                'prenoms': v.validateur.prenoms,
                'matricule': v.validateur.matricule
            },
            'decision': v.get_decision_display(),
            'commentaire': v.commentaire,
            'date_demande': v.date_demande.strftime('%Y-%m-%d %H:%M'),
            'date_validation': v.date_validation.strftime('%Y-%m-%d %H:%M') if v.date_validation else None
        } for v in validations]

        return JsonResponse({
            'success': True,
            'data': data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
@login_required
def api_verifier_solde(request):
    """Vérifier le solde de congés disponible pour une période donnée"""
    try:
        employe_id = request.GET.get('employe_id')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')

        if not all([employe_id, date_debut, date_fin]):
            return JsonResponse({
                'success': False,
                'error': 'Paramètres manquants'
            }, status=400)

        employe = get_object_or_404(ZY00, matricule=employe_id)
        date_debut = timezone.datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin = timezone.datetime.strptime(date_fin, '%Y-%m-%d').date()

        jours_demandes = 0
        current = date_debut
        while current <= date_fin:
            if current.weekday() < 5:
                jours_demandes += 1
            current += timedelta(days=1)

        annee_absence = date_debut.year
        annee_acquisition = annee_absence - 1

        try:
            acquisition = AcquisitionConges.objects.get(
                employe=employe,
                annee_reference=annee_acquisition
            )
            solde_disponible = acquisition.jours_restants
        except AcquisitionConges.DoesNotExist:
            solde_disponible = Decimal('0.00')

        return JsonResponse({
            'success': True,
            'data': {
                'jours_demandes': jours_demandes,
                'solde_disponible': str(solde_disponible),
                'annee_acquisition': annee_acquisition,
                'solde_suffisant': solde_disponible >= jours_demandes
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
@login_required
def api_mes_absences_calendrier(request):
    """Récupérer les absences de l'employé connecté pour le calendrier"""
    try:
        user_employe = request.user.employe
        start = request.GET.get('start')
        end = request.GET.get('end')

        logger.debug("API Calendrier appelée - Employé: %s, Start: %s, End: %s",
                     user_employe, start, end)

        if start:
            start_date = timezone.datetime.fromisoformat(start.replace('Z', '+00:00')).date()
        else:
            start_date = timezone.now().date()

        if end:
            end_date = timezone.datetime.fromisoformat(end.replace('Z', '+00:00')).date()
        else:
            end_date = start_date + timedelta(days=30)

        absences = Absence.objects.filter(
            employe=user_employe,
            date_debut__lte=end_date,
            date_fin__gte=start_date
        ).select_related('type_absence')

        data = []
        for abs in absences:
            data.append({
                'id': abs.id,
                'type_absence': abs.type_absence.libelle,
                'date_debut': abs.date_debut.strftime('%Y-%m-%d'),
                'date_fin': abs.date_fin.strftime('%Y-%m-%d'),
                'jours_ouvrables': str(abs.jours_ouvrables),
                'statut': abs.statut,
                'couleur': getattr(abs.type_absence, 'couleur', '#1c5d5f'),
                'employe': str(abs.employe)
            })

        return JsonResponse({
            'success': True,
            'absences': data
        })

    except Exception as e:
        logger.exception("ERREUR API Calendrier:")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
