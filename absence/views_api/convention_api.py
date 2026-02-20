# absence/views_api/convention_api.py
"""
API pour la gestion des conventions collectives.
"""
import logging
from datetime import datetime, date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST

from absence.decorators import drh_or_admin_required, gestion_app_required
from absence.models import ConfigurationConventionnelle

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@login_required
@drh_or_admin_required
@gestion_app_required
def api_convention_detail(request, id):
    """Récupérer les détails d'une convention (pour édition)"""
    try:
        convention = get_object_or_404(ConfigurationConventionnelle, id=id)

        # Extraire les composants de date avec N/N+1
        annee_debut_relative = 'N+1' if convention.periode_prise_debut.year > convention.annee_reference else 'N'

        if hasattr(convention, 'periode_prise_fin_annee_suivante'):
            annee_fin_relative = 'N+1' if convention.periode_prise_fin_annee_suivante else 'N'
        else:
            annee_fin_relative = 'N+1' if convention.periode_prise_fin.year > convention.periode_prise_debut.year else 'N'

        data = {
            'id': convention.id,
            'nom': convention.nom,
            'code': convention.code,
            'type_convention': convention.type_convention,
            'annee_reference': convention.annee_reference,
            'date_debut': convention.date_debut.strftime('%Y-%m-%d'),
            'date_fin': convention.date_fin.strftime('%Y-%m-%d') if convention.date_fin else '',
            'actif': convention.actif,
            'jours_acquis_par_mois': str(convention.jours_acquis_par_mois),
            'duree_conges_principale': convention.duree_conges_principale,
            'periode_prise_debut_jour': convention.periode_prise_debut.day,
            'periode_prise_debut_mois': f"{convention.periode_prise_debut.month:02d}",
            'periode_prise_debut_annee': annee_debut_relative,
            'periode_prise_fin_jour': convention.periode_prise_fin.day,
            'periode_prise_fin_mois': f"{convention.periode_prise_fin.month:02d}",
            'periode_prise_fin_annee': annee_fin_relative,
            'methode_calcul': convention.methode_calcul,
            'mode_validation': convention.mode_validation,
        }
        return JsonResponse(data)
    except Exception as e:
        logger.exception("Erreur lors de la récupération des détails de la convention:")
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_convention_create(request):
    """Créer une convention via modal"""
    try:
        errors = {}
        required_fields = [
            'nom', 'code', 'type_convention', 'annee_reference', 'date_debut',
            'jours_acquis_par_mois', 'duree_conges_principale',
            'periode_prise_debut_jour', 'periode_prise_debut_mois', 'periode_prise_debut_annee',
            'periode_prise_fin_jour', 'periode_prise_fin_mois', 'periode_prise_fin_annee',
            'methode_calcul'
        ]

        for field in required_fields:
            value = request.POST.get(field)
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        code = request.POST.get('code').upper().strip()
        if ConfigurationConventionnelle.objects.filter(code=code).exists():
            return JsonResponse({
                'errors': {'code': [f'Le code "{code}" est déjà utilisé']}
            }, status=400)

        annee_reference = int(request.POST.get('annee_reference'))

        try:
            date_debut = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'errors': {'date_debut': ['Format de date invalide']}
            }, status=400)

        date_fin = None
        if request.POST.get('date_fin'):
            try:
                date_fin = datetime.strptime(request.POST.get('date_fin'), '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'errors': {'date_fin': ['Format de date invalide']}
                }, status=400)

        try:
            jour_debut = int(request.POST.get('periode_prise_debut_jour'))
            mois_debut = int(request.POST.get('periode_prise_debut_mois'))
            annee_debut_relative = request.POST.get('periode_prise_debut_annee')

            jour_fin = int(request.POST.get('periode_prise_fin_jour'))
            mois_fin = int(request.POST.get('periode_prise_fin_mois'))
            annee_fin_relative = request.POST.get('periode_prise_fin_annee')

            annee_debut_reelle = annee_reference if annee_debut_relative == 'N' else annee_reference + 1
            annee_fin_reelle = annee_reference if annee_fin_relative == 'N' else annee_reference + 1

            periode_prise_debut = date(annee_debut_reelle, mois_debut, jour_debut)
            periode_prise_fin = date(annee_fin_reelle, mois_fin, jour_fin)
            periode_prise_fin_annee_suivante = (annee_fin_relative == 'N+1')

        except (ValueError, TypeError) as e:
            return JsonResponse({
                'errors': {'periode_prise': ['Erreur dans la construction des dates de période: ' + str(e)]}
            }, status=400)

        if periode_prise_fin <= periode_prise_debut:
            return JsonResponse({
                'errors': {
                    'periode_prise_fin': ['La date de fin de période doit être postérieure à la date de début']
                }
            }, status=400)

        with transaction.atomic():
            convention = ConfigurationConventionnelle(
                nom=request.POST.get('nom'),
                code=code,
                type_convention=request.POST.get('type_convention'),
                annee_reference=annee_reference,
                date_debut=date_debut,
                date_fin=date_fin,
                actif=request.POST.get('actif') == 'on',
                jours_acquis_par_mois=request.POST.get('jours_acquis_par_mois'),
                duree_conges_principale=int(request.POST.get('duree_conges_principale')),
                periode_prise_debut=periode_prise_debut,
                periode_prise_fin=periode_prise_fin,
                periode_prise_fin_annee_suivante=periode_prise_fin_annee_suivante,
                methode_calcul=request.POST.get('methode_calcul'),
                mode_validation=request.POST.get('mode_validation', 'MANAGER_ET_RH'),
            )

            try:
                convention.full_clean()
            except ValidationError as e:
                return JsonResponse({'errors': e.message_dict}, status=400)

            convention.save()

        messages.success(request, f"Convention '{convention.nom}' créée avec succès")

        return JsonResponse({
            'success': True,
            'message': 'Convention créée avec succès',
            'id': convention.id
        })

    except Exception as e:
        logger.exception("Erreur lors de la création de la convention:")
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_convention_update(request, id):
    """Mettre à jour une convention via modal"""
    try:
        convention = get_object_or_404(ConfigurationConventionnelle, id=id)

        errors = {}
        required_fields = [
            'nom', 'code', 'type_convention', 'annee_reference', 'date_debut',
            'jours_acquis_par_mois', 'duree_conges_principale',
            'periode_prise_debut_jour', 'periode_prise_debut_mois', 'periode_prise_debut_annee',
            'periode_prise_fin_jour', 'periode_prise_fin_mois', 'periode_prise_fin_annee',
            'methode_calcul'
        ]

        for field in required_fields:
            if not request.POST.get(field):
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        code = request.POST.get('code').upper().strip()
        if ConfigurationConventionnelle.objects.filter(code=code).exclude(id=id).exists():
            return JsonResponse({
                'errors': {'code': [f'Le code "{code}" est déjà utilisé']}
            }, status=400)

        annee_reference = int(request.POST.get('annee_reference'))

        try:
            date_debut = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'errors': {'date_debut': ['Format de date invalide']}
            }, status=400)

        date_fin = None
        if request.POST.get('date_fin'):
            try:
                date_fin = datetime.strptime(request.POST.get('date_fin'), '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'errors': {'date_fin': ['Format de date invalide']}
                }, status=400)

        try:
            jour_debut = int(request.POST.get('periode_prise_debut_jour'))
            mois_debut = int(request.POST.get('periode_prise_debut_mois'))
            annee_debut_relative = request.POST.get('periode_prise_debut_annee')

            jour_fin = int(request.POST.get('periode_prise_fin_jour'))
            mois_fin = int(request.POST.get('periode_prise_fin_mois'))
            annee_fin_relative = request.POST.get('periode_prise_fin_annee')

            annee_debut_reelle = annee_reference if annee_debut_relative == 'N' else annee_reference + 1
            annee_fin_reelle = annee_reference if annee_fin_relative == 'N' else annee_reference + 1

            periode_prise_debut = date(annee_debut_reelle, mois_debut, jour_debut)
            periode_prise_fin = date(annee_fin_reelle, mois_fin, jour_fin)
            periode_prise_fin_annee_suivante = (annee_fin_relative == 'N+1')

        except (ValueError, TypeError) as e:
            return JsonResponse({
                'errors': {'periode_prise': ['Erreur dans la construction des dates de période: ' + str(e)]}
            }, status=400)

        if periode_prise_fin <= periode_prise_debut:
            return JsonResponse({
                'errors': {
                    'periode_prise_fin': ['La date de fin de période doit être postérieure à la date de début']
                }
            }, status=400)

        with transaction.atomic():
            convention.nom = request.POST.get('nom')
            convention.code = code
            convention.type_convention = request.POST.get('type_convention')
            convention.annee_reference = annee_reference
            convention.date_debut = date_debut
            convention.date_fin = date_fin
            convention.actif = request.POST.get('actif') == 'on'
            convention.jours_acquis_par_mois = request.POST.get('jours_acquis_par_mois')
            convention.duree_conges_principale = int(request.POST.get('duree_conges_principale'))
            convention.periode_prise_debut = periode_prise_debut
            convention.periode_prise_fin = periode_prise_fin
            convention.periode_prise_fin_annee_suivante = periode_prise_fin_annee_suivante
            convention.methode_calcul = request.POST.get('methode_calcul')
            convention.mode_validation = request.POST.get('mode_validation', 'MANAGER_ET_RH')

            try:
                convention.full_clean()
            except ValidationError as e:
                return JsonResponse({'errors': e.message_dict}, status=400)

            convention.save()

        messages.success(request, f"Convention '{convention.nom}' modifiée avec succès")

        return JsonResponse({
            'success': True,
            'message': 'Convention modifiée avec succès'
        })

    except Exception as e:
        logger.exception("Erreur lors de la modification de la convention:")
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_convention_delete(request, id):
    """Supprimer une convention"""
    try:
        convention = get_object_or_404(ConfigurationConventionnelle, id=id)

        from entreprise.models import Entreprise
        if Entreprise.objects.filter(configuration_conventionnelle=convention).exists():
            return JsonResponse({
                'error': 'Cette convention est utilisée par l\'entreprise et ne peut être supprimée'
            }, status=400)

        nom = convention.nom
        with transaction.atomic():
            convention.delete()

        return JsonResponse({
            'success': True,
            'message': f'Convention "{nom}" supprimée avec succès'
        })

    except Exception as e:
        logger.exception("Erreur lors de la suppression de la convention:")
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_convention_toggle_actif(request, id):
    """Activer/Désactiver une convention"""
    try:
        convention = get_object_or_404(ConfigurationConventionnelle, id=id)

        with transaction.atomic():
            convention.actif = not convention.actif

            try:
                convention.full_clean()
            except ValidationError as e:
                return JsonResponse({
                    'error': list(e.message_dict.values())[0][0] if e.message_dict else str(e)
                }, status=400)

            convention.save()

        statut = "activée" if convention.actif else "désactivée"
        return JsonResponse({
            'success': True,
            'message': f'Convention "{convention.nom}" {statut}',
            'actif': convention.actif
        })

    except Exception as e:
        logger.exception("Erreur lors du changement de statut de la convention:")
        return JsonResponse({'error': str(e)}, status=400)
