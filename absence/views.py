# absence/views.py
import logging
from django.core.exceptions import ValidationError
from datetime import datetime
from django.contrib import messages
from django.views.decorators.cache import never_cache
import json
from .forms import TypeAbsenceForm
from django.urls import reverse
from .forms import JourFerieForm
from .decorators import drh_or_admin_required
from .decorators import manager_required
from .decorators import rh_required
from .decorators import gestion_app_required
from .decorators import manager_or_rh_required
from .decorators import role_required
from .forms import ParametreCalculCongesForm
import calendar
from .models import (
    ConfigurationConventionnelle,
    ParametreCalculConges,
    JourFerie,
    Absence,
    TypeAbsence,
    AcquisitionConges,
    ValidationAbsence, NotificationAbsence
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
from datetime import date, timedelta
from .forms import (
    AbsenceForm,
    AbsenceRechercheForm,
    ValidationAbsenceForm,
    CalculAcquisitionForm
)
from employee.models import ZY00

# Configuration du logger
logger = logging.getLogger(__name__)

# ===============================
# VUES POUR CONFIGURATIONCONVENTIONNELLE
# ===============================

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_conventions(request):
    """
    Liste des conventions collectives avec filtres
    """
    # Récupération des filtres
    filtre_actif = request.GET.get('actif', '')  # '', 'oui', 'non'
    filtre_annee = request.GET.get('annee', '')
    type_filter = request.GET.get('type', '')  # Filtre par type
    search = request.GET.get('search', '')

    # Base queryset
    conventions = ConfigurationConventionnelle.objects.all()

    # Appliquer les filtres
    if filtre_actif == 'oui':
        conventions = conventions.filter(actif=True)
    elif filtre_actif == 'non':
        conventions = conventions.filter(actif=False)

    if filtre_annee:
        conventions = conventions.filter(annee_reference=filtre_annee)

    # Filtre par type
    if type_filter:
        conventions = conventions.filter(type_convention=type_filter)

    if search:
        conventions = conventions.filter(
            Q(nom__icontains=search) |
            Q(code__icontains=search)
        )

    conventions = conventions.order_by('-annee_reference',
                                       '-created_at' if hasattr(ConfigurationConventionnelle, 'created_at') else 'nom')

    # Statistiques
    stats = {
        'total': ConfigurationConventionnelle.objects.count(),
        'actives': ConfigurationConventionnelle.objects.filter(actif=True).count(),
        'inactives': ConfigurationConventionnelle.objects.filter(actif=False).count(),
    }

    # ✅ NOUVELLES STATISTIQUES : Par type
    entreprise_count = ConfigurationConventionnelle.objects.filter(type_convention='ENTREPRISE').count()
    personnalisee_count = ConfigurationConventionnelle.objects.filter(type_convention='PERSONNALISEE').count()

    # Liste des années pour le filtre
    annees = ConfigurationConventionnelle.objects.values_list(
        'annee_reference', flat=True
    ).distinct().order_by('-annee_reference')

    context = {
        'conventions': conventions,
        'stats': stats,
        'entreprise_count': entreprise_count,
        'personnalisee_count': personnalisee_count,
        'annees': annees,
        'filtre_actif': filtre_actif,
        'filtre_annee': filtre_annee,
        'type_filter': type_filter,
        'search': search,
    }

    return render(request, 'absence/conventions_list.html', context)


# ===== API POUR LES MODALES =====

@require_http_methods(["GET"])
@login_required
@drh_or_admin_required
@gestion_app_required
def api_convention_detail(request, id):
    """Récupérer les détails d'une convention (pour édition)"""
    try:
        convention = get_object_or_404(ConfigurationConventionnelle, id=id)

        # Extraire les composants de date avec N/N+1
        # Pour la date de début
        annee_debut_relative = 'N+1' if convention.periode_prise_debut.year > convention.annee_reference else 'N'

        # Pour la date de fin
        if hasattr(convention, 'periode_prise_fin_annee_suivante'):
            annee_fin_relative = 'N+1' if convention.periode_prise_fin_annee_suivante else 'N'
        else:
            # Fallback pour les anciennes conventions
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

            # Dates de période décomposées
            'periode_prise_debut_jour': convention.periode_prise_debut.day,
            'periode_prise_debut_mois': f"{convention.periode_prise_debut.month:02d}",
            'periode_prise_debut_annee': annee_debut_relative,

            'periode_prise_fin_jour': convention.periode_prise_fin.day,
            'periode_prise_fin_mois': f"{convention.periode_prise_fin.month:02d}",
            'periode_prise_fin_annee': annee_fin_relative,

            'methode_calcul': convention.methode_calcul,
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
        # Validation de base
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

        # Vérifier l'unicité du code
        code = request.POST.get('code').upper().strip()
        if ConfigurationConventionnelle.objects.filter(code=code).exists():
            return JsonResponse({
                'errors': {'code': [f'Le code "{code}" est déjà utilisé']}
            }, status=400)

        # Récupérer l'année de référence
        annee_reference = int(request.POST.get('annee_reference'))

        # Conversion des dates d'effet
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

        # Conversion des dates de période (avec N/N+1)
        try:
            # Récupérer les composants de la date de début
            jour_debut = int(request.POST.get('periode_prise_debut_jour'))
            mois_debut = int(request.POST.get('periode_prise_debut_mois'))
            annee_debut_relative = request.POST.get('periode_prise_debut_annee')  # 'N' ou 'N+1'

            # Récupérer les composants de la date de fin
            jour_fin = int(request.POST.get('periode_prise_fin_jour'))
            mois_fin = int(request.POST.get('periode_prise_fin_mois'))
            annee_fin_relative = request.POST.get('periode_prise_fin_annee')  # 'N' ou 'N+1'

            # Calculer les années réelles pour le stockage
            if annee_debut_relative == 'N':
                annee_debut_reelle = annee_reference
            else:  # 'N+1'
                annee_debut_reelle = annee_reference + 1

            if annee_fin_relative == 'N':
                annee_fin_reelle = annee_reference
            else:  # 'N+1'
                annee_fin_reelle = annee_reference + 1

            # Créer les dates
            periode_prise_debut = date(annee_debut_reelle, mois_debut, jour_debut)
            periode_prise_fin = date(annee_fin_reelle, mois_fin, jour_fin)

            # ✅ Déterminer si la fin est en N+1
            periode_prise_fin_annee_suivante = (annee_fin_relative == 'N+1')

        except (ValueError, TypeError) as e:
            return JsonResponse({
                'errors': {'periode_prise': ['Erreur dans la construction des dates de période: ' + str(e)]}
            }, status=400)

        # ✅ Validation supplémentaire : la fin doit être après le début
        if periode_prise_fin <= periode_prise_debut:
            return JsonResponse({
                'errors': {
                    'periode_prise_fin': ['La date de fin de période doit être postérieure à la date de début']
                }
            }, status=400)

        # Créer la convention
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
            )

            # Validation Django (inclut toutes les règles de gestion)
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

        # Validation de base
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

        # Vérifier l'unicité du code (sauf pour l'instance courante)
        code = request.POST.get('code').upper().strip()
        if ConfigurationConventionnelle.objects.filter(code=code).exclude(id=id).exists():
            return JsonResponse({
                'errors': {'code': [f'Le code "{code}" est déjà utilisé']}
            }, status=400)

        # Récupérer l'année de référence
        annee_reference = int(request.POST.get('annee_reference'))

        # Conversion des dates d'effet
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

        # Conversion des dates de période (avec N/N+1)
        try:
            # Récupérer les composants de la date de début
            jour_debut = int(request.POST.get('periode_prise_debut_jour'))
            mois_debut = int(request.POST.get('periode_prise_debut_mois'))
            annee_debut_relative = request.POST.get('periode_prise_debut_annee')

            # Récupérer les composants de la date de fin
            jour_fin = int(request.POST.get('periode_prise_fin_jour'))
            mois_fin = int(request.POST.get('periode_prise_fin_mois'))
            annee_fin_relative = request.POST.get('periode_prise_fin_annee')

            # Calculer les années réelles pour le stockage
            if annee_debut_relative == 'N':
                annee_debut_reelle = annee_reference
            else:  # 'N+1'
                annee_debut_reelle = annee_reference + 1

            if annee_fin_relative == 'N':
                annee_fin_reelle = annee_reference
            else:  # 'N+1'
                annee_fin_reelle = annee_reference + 1

            # Créer les dates
            periode_prise_debut = date(annee_debut_reelle, mois_debut, jour_debut)
            periode_prise_fin = date(annee_fin_reelle, mois_fin, jour_fin)

            # ✅ Déterminer si la fin est en N+1
            periode_prise_fin_annee_suivante = (annee_fin_relative == 'N+1')

        except (ValueError, TypeError) as e:
            return JsonResponse({
                'errors': {'periode_prise': ['Erreur dans la construction des dates de période: ' + str(e)]}
            }, status=400)

        # Validation supplémentaire
        if periode_prise_fin <= periode_prise_debut:
            return JsonResponse({
                'errors': {
                    'periode_prise_fin': ['La date de fin de période doit être postérieure à la date de début']
                }
            }, status=400)

        # Mettre à jour
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

            # Validation Django
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

        # AMÉLIORÉ : Vérifier si la convention est utilisée
        # Vérifier si utilisée par l'entreprise
        from entreprise.models import Entreprise
        if Entreprise.objects.filter(configuration_conventionnelle=convention).exists():
            return JsonResponse({
                'error': 'Cette convention est utilisée par l\'entreprise et ne peut être supprimée'
            }, status=400)

        # TODO: Ajouter vérification pour les employés avec convention personnalisée
        # if convention.employes_personnalises.exists():
        #     return JsonResponse({
        #         'error': 'Cette convention est utilisée par des employés et ne peut être supprimée'
        #     }, status=400)

        nom = convention.nom
        with transaction.atomic():
            convention.delete()

        return JsonResponse({
            'success': True,
            'message': f'✅ Convention "{nom}" supprimée avec succès'
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

            # AMÉLIORÉ : Validation lors du changement de statut
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
            'message': f'✅ Convention "{convention.nom}" {statut}',
            'actif': convention.actif
        })

    except Exception as e:
        logger.exception("Erreur lors du changement de statut de la convention:")
        return JsonResponse({'error': str(e)}, status=400)

# ============================================
# JOURS FÉRIÉS - LISTE
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_jours_feries(request):
    """
    Affiche la liste des jours fériés avec filtres
    """
    # Récupération des paramètres de filtrage
    annee_filter = request.GET.get('annee', '')
    type_filter = request.GET.get('type', '')
    actif_filter = request.GET.get('actif', '')
    search = request.GET.get('search', '').strip()

    # Queryset de base
    jours_feries = JourFerie.objects.all()

    # Filtres
    if annee_filter:
        jours_feries = jours_feries.filter(date__year=annee_filter)

    if type_filter:
        jours_feries = jours_feries.filter(type_ferie=type_filter)

    if actif_filter == 'oui':
        jours_feries = jours_feries.filter(actif=True)
    elif actif_filter == 'non':
        jours_feries = jours_feries.filter(actif=False)

    if search:
        jours_feries = jours_feries.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search)
        )

    # Tri par date
    jours_feries = jours_feries.order_by('-date')

    # Statistiques
    total = jours_feries.count()
    actifs = jours_feries.filter(actif=True).count()
    inactifs = jours_feries.filter(actif=False).count()
    legaux = jours_feries.filter(type_ferie='LEGAL').count()
    entreprise = jours_feries.filter(type_ferie='ENTREPRISE').count()

    # Liste des années disponibles
    annees = JourFerie.objects.dates('date', 'year', order='DESC')
    annees_list = [date.year for date in annees]

    # Année courante par défaut
    annee_courante = datetime.now().year

    context = {
        'jours_feries': jours_feries,
        'total': total,
        'actifs': actifs,
        'inactifs': inactifs,
        'legaux': legaux,
        'entreprise': entreprise,
        'annees': annees_list,
        'annee_courante': annee_courante,
        'annee_filter': annee_filter,
        'type_filter': type_filter,
        'actif_filter': actif_filter,
        'search': search,
    }

    return render(request, 'absence/jours_feries_list.html', context)


# ============================================
# JOURS FÉRIÉS - API DÉTAIL
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_http_methods(["GET"])
def api_jour_ferie_detail(request, id):
    """
    Retourne les détails d'un jour férié en JSON
    """
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


# ============================================
# JOURS FÉRIÉS - API CRÉATION
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_jour_ferie_create(request):
    """
    Crée un nouveau jour férié via AJAX
    """
    try:
        form = JourFerieForm(request.POST)

        if form.is_valid():
            jour_ferie = form.save(commit=False)

            # Associer l'utilisateur créateur
            try:
                jour_ferie.created_by = request.user.zy00
            except:
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


# ============================================
# JOURS FÉRIÉS - API MODIFICATION
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_jour_ferie_update(request, id):
    """
    Met à jour un jour férié existant via AJAX
    """
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


# ============================================
# JOURS FÉRIÉS - API SUPPRESSION
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_jour_ferie_delete(request, id):
    """
    Supprime un jour férié via AJAX
    """
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


# ============================================
# JOURS FÉRIÉS - API TOGGLE ACTIF
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_jour_ferie_toggle(request, id):
    """
    Active/Désactive un jour férié via AJAX
    """
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


# ============================================
# JOURS FÉRIÉS - API DUPLIQUER ANNÉE
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_dupliquer_jours_feries(request):
    """
    Duplique les jours fériés d'une année vers une autre
    """
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

        # Récupérer les jours fériés de l'année source
        jours_source = JourFerie.objects.filter(
            date__year=annee_source,
            recurrent=True
        )

        if not jours_source.exists():
            return JsonResponse({
                'success': False,
                'error': f'Aucun jour férié récurrent trouvé pour l\'année {annee_source}'
            }, status=400)

        # Dupliquer vers l'année cible
        created_count = 0
        for jour in jours_source:
            # Calculer la nouvelle date
            nouvelle_date = jour.date.replace(year=annee_cible)

            # Vérifier si existe déjà
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


# ============================================
# TYPES D'ABSENCE - LISTE
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_types_absence(request):
    """
    Affiche la liste des types d'absence avec filtres
    """
    # Récupération des paramètres de filtrage
    categorie_filter = request.GET.get('categorie', '')
    actif_filter = request.GET.get('actif', '')
    paye_filter = request.GET.get('paye', '')
    search = request.GET.get('search', '').strip()

    # Queryset de base
    types_absence = TypeAbsence.objects.all()

    # Filtres
    if categorie_filter:
        types_absence = types_absence.filter(categorie=categorie_filter)

    if actif_filter == 'oui':
        types_absence = types_absence.filter(actif=True)
    elif actif_filter == 'non':
        types_absence = types_absence.filter(actif=False)

    if paye_filter == 'oui':
        types_absence = types_absence.filter(paye=True)
    elif paye_filter == 'non':
        types_absence = types_absence.filter(paye=False)

    if search:
        types_absence = types_absence.filter(
            Q(code__icontains=search) |
            Q(libelle__icontains=search)
        )

    # Tri par ordre puis libellé
    types_absence = types_absence.order_by('ordre', 'libelle')

    # Statistiques
    total = types_absence.count()
    actifs = types_absence.filter(actif=True).count()
    inactifs = types_absence.filter(actif=False).count()
    payes = types_absence.filter(paye=True).count()
    non_payes = types_absence.filter(paye=False).count()
    avec_decompte = types_absence.filter(decompte_solde=True).count()

    # Liste des catégories pour le filtre
    categories = TypeAbsence.CATEGORIE_CHOICES

    context = {
        'types_absence': types_absence,
        'total': total,
        'actifs': actifs,
        'inactifs': inactifs,
        'payes': payes,
        'non_payes': non_payes,
        'avec_decompte': avec_decompte,
        'categories': categories,
        'categorie_filter': categorie_filter,
        'actif_filter': actif_filter,
        'paye_filter': paye_filter,
        'search': search,
    }

    return render(request, 'absence/types_absence_list.html', context)


# ============================================
# TYPES D'ABSENCE - API DÉTAIL
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_http_methods(["GET"])
def api_type_absence_detail(request, id):
    """
    Retourne les détails d'un type d'absence en JSON
    """
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


# ============================================
# TYPES D'ABSENCE - API CRÉATION
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_create(request):
    """
    Crée un nouveau type d'absence via AJAX
    """
    try:
        # DEBUG : Afficher les données reçues
        logger.debug("=" * 50)
        logger.debug("DONNÉES REÇUES:")
        logger.debug("POST: %s", request.POST)
        logger.debug("=" * 50)

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
            # Afficher les erreurs du formulaire
            logger.error("ERREURS DU FORMULAIRE:")
            logger.error("Erreurs: %s", form.errors)
            logger.error("=" * 50)

            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]

            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

    except Exception as e:
        # Afficher l'exception
        logger.exception("EXCEPTION lors de la création du type d'absence:")
        logger.error("=" * 50)

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================
# TYPES D'ABSENCE - API MODIFICATION
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_update(request, id):
    """
    Met à jour un type d'absence existant via AJAX
    """
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


# ============================================
# TYPES D'ABSENCE - API SUPPRESSION
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_delete(request, id):
    """
    Supprime un type d'absence via AJAX
    """
    try:
        type_absence = get_object_or_404(TypeAbsence, pk=id)
        code = type_absence.code
        libelle = type_absence.libelle

        # Vérifier si le type d'absence est utilisé
        # TODO: Ajouter la vérification des demandes d'absence liées
        # if type_absence.demandes_absence.exists():
        #     return JsonResponse({
        #         'success': False,
        #         'error': 'Ce type d\'absence est utilisé et ne peut pas être supprimé'
        #     }, status=400)

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


# ============================================
# TYPES D'ABSENCE - API TOGGLE ACTIF
# ============================================

@login_required
@drh_or_admin_required
@gestion_app_required
@require_POST
def api_type_absence_toggle(request, id):
    """
    Active/Désactive un type d'absence via AJAX
    """
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


# ===== VUES PARAMÈTRES CALCUL CONGÉS =====
@login_required
@drh_or_admin_required
@gestion_app_required
def liste_parametres_calcul(request):
    """
    Liste des paramètres de calcul des congés avec filtres
    """
    # Récupération des filtres
    search = request.GET.get('search', '')
    convention_filter = request.GET.get('convention', '')

    # Base queryset
    parametres = ParametreCalculConges.objects.select_related('configuration').all()

    # Appliquer les filtres
    if search:
        parametres = parametres.filter(
            Q(configuration__nom__icontains=search) |
            Q(configuration__code__icontains=search)
        )

    if convention_filter:
        parametres = parametres.filter(configuration_id=convention_filter)

    parametres = parametres.order_by('-configuration__annee_reference')

    # Statistiques
    total = ParametreCalculConges.objects.count()
    avec_report = ParametreCalculConges.objects.filter(report_autorise=True).count()
    sans_report = ParametreCalculConges.objects.filter(report_autorise=False).count()
    avec_anciennete = ParametreCalculConges.objects.exclude(jours_supp_anciennete={}).count()

    # Conventions disponibles pour le filtre
    conventions = ConfigurationConventionnelle.objects.filter(actif=True).order_by('nom')

    context = {
        'parametres': parametres,
        'total': total,
        'avec_report': avec_report,
        'sans_report': sans_report,
        'avec_anciennete': avec_anciennete,
        'conventions': conventions,
        'search': search,
        'convention_filter': convention_filter,
    }

    return render(request, 'absence/parametres_calcul_list.html', context)


# ============================================
# PARAMÈTRES CALCUL CONGÉS - API CALCUL DETAIL
# ============================================
@require_http_methods(["GET"])
@login_required
@drh_or_admin_required
@gestion_app_required
def api_parametre_calcul_detail(request, id):
    """Récupérer les détails d'un paramètre (pour édition)"""
    try:
        parametre = get_object_or_404(ParametreCalculConges, id=id)

        # Extraire les valeurs d'ancienneté
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


# ============================================
# PARAMÈTRES CALCUL CONGÉS - API CREATE
# ============================================
@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_parametre_calcul_create(request):
    """Créer un paramètre via modal"""
    try:
        # Vérifier qu'il n'existe pas déjà un paramètre pour cette configuration
        configuration_id = request.POST.get('configuration')
        if ParametreCalculConges.objects.filter(configuration_id=configuration_id).exists():
            return JsonResponse({
                'success': False,
                'errors': {'configuration': ['Un paramètre existe déjà pour cette convention']}
            }, status=400)

        # Préparer les données pour le formulaire
        data = request.POST.copy()

        # Construire le JSON d'ancienneté
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


# ============================================
# PARAMÈTRES CALCUL CONGÉS - API UPDATE
# ============================================
@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_parametre_calcul_update(request, id):
    """Mettre à jour un paramètre via modal"""
    try:
        parametre = get_object_or_404(ParametreCalculConges, id=id)

        # Préparer les données
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


# ============================================
# PARAMÈTRES CALCUL CONGÉS - API DELETE
# ============================================
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


# ===== VUES ACQUISITION CONGÉS =====

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_acquisitions(request):
    """Liste des acquisitions de congés avec filtres"""
    from django.utils import timezone
    from datetime import timedelta

    # Récupération des filtres
    search = request.GET.get('search', '')
    annee_filter = request.GET.get('annee', timezone.now().year)
    employe_filter = request.GET.get('employe', '')

    # Base queryset
    acquisitions = AcquisitionConges.objects.select_related(
        'employe',
        'employe__entreprise'
    ).all()

    # Appliquer les filtres
    if search:
        acquisitions = acquisitions.filter(
            Q(employe__nom__icontains=search) |
            Q(employe__prenoms__icontains=search) |
            Q(employe__matricule__icontains=search)
        )

    if annee_filter:
        acquisitions = acquisitions.filter(annee_reference=annee_filter)

    if employe_filter:
        acquisitions = acquisitions.filter(employe_id=employe_filter)

    acquisitions = acquisitions.order_by('employe__nom', 'employe__prenoms')

    # Statistiques
    stats = acquisitions.aggregate(
        total_employes=Count('employe', distinct=True),
        total_jours_acquis=Sum('jours_acquis'),
        total_jours_pris=Sum('jours_pris'),
        total_jours_restants=Sum('jours_restants')
    )

    # Années disponibles
    annees = AcquisitionConges.objects.values_list(
        'annee_reference', flat=True
    ).distinct().order_by('-annee_reference')

    # Employés pour le filtre
    employes = ZY00.objects.filter(
        etat='actif',
        entreprise__isnull=False
    ).order_by('nom', 'prenoms')

    # Formulaire de calcul
    calcul_form = CalculAcquisitionForm(initial={'annee_reference': annee_filter})

    # Calculer le statut de verrouillage pour l'année filtrée
    date_actuelle = timezone.now().date()
    annee_verrouille = False
    date_limite_recalcul = None
    message_verrouillage = ""
    dans_delai_grace = False
    fin_periode = None

    try:
        from absence.models import ConfigurationConventionnelle

        convention_entreprise = ConfigurationConventionnelle.objects.filter(
            type_convention='ENTREPRISE',
            actif=True
        ).first()

        if convention_entreprise and annee_filter:
            # Calculer la date de fin de période pour l'année filtrée
            _, fin_periode = convention_entreprise.get_periode_acquisition(int(annee_filter))

            # Date limite = fin de période + 2 jours
            date_limite_recalcul = fin_periode + timedelta(days=2)

            # Vérifier si l'année est verrouillée
            if date_actuelle > date_limite_recalcul:
                annee_verrouille = True
                message_verrouillage = f"Le délai de recalcul a expiré le {date_limite_recalcul.strftime('%d/%m/%Y')}"

            # Vérifier si on est dans le délai de grâce
            elif date_actuelle > fin_periode and date_actuelle <= date_limite_recalcul:
                dans_delai_grace = True

    except Exception as e:
        logger.error("Erreur lors du calcul de verrouillage: %s", e)

    # Enrichir chaque acquisition avec son statut de verrouillage
    acquisitions_enrichies = []
    for acq in acquisitions:
        try:
            conv = acq.employe.convention_applicable
            if conv:
                _, fin_periode_acq = conv.get_periode_acquisition(acq.annee_reference)
                date_limite_acq = fin_periode_acq + timedelta(days=2)

                acq.est_verrouille_cache = date_actuelle > date_limite_acq
                acq.date_limite_modification_cache = date_limite_acq
                acq.est_dans_delai_grace_cache = (date_actuelle > fin_periode_acq and date_actuelle <= date_limite_acq)
            else:
                acq.est_verrouille_cache = True
                acq.date_limite_modification_cache = None
                acq.est_dans_delai_grace_cache = False
        except:
            acq.est_verrouille_cache = True
            acq.date_limite_modification_cache = None
            acq.est_dans_delai_grace_cache = False

        acquisitions_enrichies.append(acq)

    context = {
        'acquisitions': acquisitions_enrichies,
        'stats': stats,
        'annees': annees,
        'employes': employes,
        'search': search,
        'annee_filter': annee_filter,
        'employe_filter': employe_filter,
        'calcul_form': calcul_form,
        'annee_verrouille': annee_verrouille,
        'date_limite_recalcul': date_limite_recalcul,
        'message_verrouillage': message_verrouillage,
        'dans_delai_grace': dans_delai_grace,
        'fin_periode': fin_periode,
    }

    return render(request, 'absence/acquisitions_list.html', context)


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
    """
    Mettre à jour une acquisition (principalement le report antérieur)
    """
    try:
        acquisition = get_object_or_404(AcquisitionConges, id=id)

        # Seul le report antérieur peut être modifié manuellement
        jours_report_anterieur = request.POST.get('jours_report_anterieur')

        if jours_report_anterieur is not None:
            with transaction.atomic():
                acquisition.jours_report_anterieur = Decimal(jours_report_anterieur)
                acquisition.save()  # Recalcule automatiquement jours_restants

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
    """
    Calcule automatiquement les acquisitions pour une année donnée
    BLOCAGE : Impossible de recalculer les années passées après
    la fin de la période de référence + 2 jours
    Exemple :
    - Période convention: 01/05/N → 30/04/N+1
    - Blocage à partir de: 02/05/N+1
    """
    from django.utils import timezone
    from datetime import timedelta

    try:
        logger.debug("📥 POST data: %s", request.POST)

        form = CalculAcquisitionForm(request.POST)

        if not form.is_valid():
            logger.error("❌ Formulaire invalide: %s", form.errors)
            return JsonResponse({
                'success': False,
                'errors': {field: errors[0] for field, errors in form.errors.items()}
            }, status=400)

        annee = form.cleaned_data['annee_reference']
        recalculer = form.cleaned_data['recalculer_existantes']
        employes_selection = form.cleaned_data.get('employes')

        # Vérification basée sur la période de convention
        date_actuelle = timezone.now().date()

        # Récupérer la convention d'entreprise active
        try:
            from absence.models import ConfigurationConventionnelle
            convention_entreprise = ConfigurationConventionnelle.objects.filter(
                type_convention='ENTREPRISE',
                actif=True
            ).first()

            if not convention_entreprise:
                return JsonResponse({
                    'success': False,
                    'error': 'Aucune convention d\'entreprise active trouvée. '
                             'Veuillez configurer une convention avant de calculer les acquisitions.'
                }, status=400)

            # Calculer la date de fin de période pour l'année de référence
            _, fin_periode = convention_entreprise.get_periode_acquisition(annee)

            # Date limite de recalcul = fin de période + 2 jours
            date_limite_recalcul = fin_periode + timedelta(days=2)

            # Si on est après la date limite, bloquer le recalcul
            if date_actuelle > date_limite_recalcul:
                return JsonResponse({
                    'success': False,
                    'error': f'Impossible de recalculer l\'année {annee}.\n'
                             f'Période de référence: {convention_entreprise.periode_prise_debut.strftime("%d/%m")} → '
                             f'{convention_entreprise.periode_prise_fin.strftime("%d/%m")}\n'
                             f'Fin de période pour {annee}: {fin_periode.strftime("%d/%m/%Y")}\n'
                             f'Le délai de recalcul a expiré le {date_limite_recalcul.strftime("%d/%m/%Y")}.\n'
                             f'Contactez votre administrateur système pour toute modification.'
                }, status=403)

            # Afficher un avertissement si on est dans les 2 derniers jours
            if date_actuelle > fin_periode and date_actuelle <= date_limite_recalcul:
                logger.warning("⚠️  AVERTISSEMENT: Vous êtes dans les 2 derniers jours de recalcul pour l'année %s", annee)
                logger.warning("   Date limite: %s", date_limite_recalcul.strftime('%d/%m/%Y'))

        except Exception as e:
            logger.error("❌ Erreur lors de la vérification de la convention: %s", e)
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la vérification de la période de référence: {str(e)}'
            }, status=500)

        logger.info("✅ Formulaire valide - Année: %s, Recalculer: %s", annee, recalculer)
        logger.info("📅 Période de référence: %s", fin_periode.strftime('%d/%m/%Y'))
        logger.info("🔓 Date limite de recalcul: %s", date_limite_recalcul.strftime('%d/%m/%Y'))

        # Déterminer les employés à traiter
        if employes_selection is not None and employes_selection.exists():
            employes = employes_selection
            logger.info("📋 Employés sélectionnés: %s", employes.count())
        else:
            employes = ZY00.objects.filter(
                etat='actif',
                entreprise__isnull=False
            )
            logger.info("📋 Tous les employés actifs: %s", employes.count())

        if not employes.exists():
            return JsonResponse({
                'success': False,
                'error': 'Aucun employé à traiter'
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
            logger.info("🔄 Traitement: %s (ID: %s)", employe, employe.matricule)

            try:
                if not employe.convention_applicable:
                    logger.warning("Pas de convention pour %s", employe)
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

                logger.info("  %s", '✨ Créée' if created else '📝 Existante')

                if created or recalculer:
                    logger.debug("  🧮 Calcul des jours...")
                    jours = calculer_jours_acquis(employe, annee)
                    logger.info("  ✅ Jours calculés: %s", jours)

                    acquisition.jours_acquis = jours
                    acquisition.save()

                    if created:
                        resultats['crees'] += 1
                    else:
                        resultats['mis_a_jour'] += 1
                else:
                    logger.info("  ⏭️  Ignorée (déjà existe)")
                    resultats['ignores'] += 1

            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                logger.error("  ❌ ERREUR: %s", error_msg)

                resultats['erreurs'] += 1
                resultats['details_erreurs'].append({
                    'employe': str(employe),
                    'erreur': str(e)
                })

        logger.info("📊 RÉSULTATS FINAUX: %s", resultats)

        return JsonResponse({
            'success': True,
            'message': f'{resultats["crees"]} acquisitions créées, '
                       f'{resultats["mis_a_jour"]} mises à jour, '
                       f'{resultats["ignores"]} ignorées, '
                       f'{resultats["erreurs"]} erreurs',
            'resultats': resultats
        })

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        logger.exception("❌ ERREUR GLOBALE: %s", error_msg)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required
@drh_or_admin_required
@gestion_app_required
def api_recalculer_acquisition(request, id):
    """
    Recalcule une acquisition spécifique
    """
    try:
        acquisition = get_object_or_404(AcquisitionConges, id=id)

        # Recalculer les jours acquis
        jours = calculer_jours_acquis(acquisition.employe, acquisition.annee_reference)

        with transaction.atomic():
            acquisition.jours_acquis = jours
            acquisition.save()

        return JsonResponse({
            'success': True,
            'message': 'Acquisition recalculée avec succès',
            'jours_acquis': str(acquisition.jours_acquis),
            'jours_restants': str(acquisition.jours_restants)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== FONCTIONS UTILITAIRES =====

def calculer_jours_acquis(employe, annee_reference):
    """
    Calcule le nombre de jours de congés acquis pour un employé sur une année

    Args:
        employe (ZY00): L'employé
        annee_reference (int): L'année de référence

    Returns:
        Decimal: Nombre de jours acquis
    """
    # 1. Récupérer la convention applicable
    convention = employe.convention_applicable
    if not convention:
        raise ValueError(f"Aucune convention applicable pour {employe}")

    # 2. Récupérer les paramètres de calcul
    try:
        parametres = convention.parametres_calcul
    except ParametreCalculConges.DoesNotExist:
        # Créer des paramètres par défaut
        parametres = ParametreCalculConges.objects.create(
            configuration=convention
        )

    # 3. Calculer les mois travaillés dans l'année
    mois_travailles = calculer_mois_travailles(employe, annee_reference)

    if mois_travailles < parametres.mois_acquisition_min:
        return Decimal('0.00')

    # 4. Calcul de base : jours_acquis_par_mois × mois_travailles
    jours_base = convention.jours_acquis_par_mois * Decimal(str(mois_travailles))

    # 5. Appliquer le plafond
    if jours_base > parametres.plafond_jours_an:
        jours_base = Decimal(str(parametres.plafond_jours_an))

    # 6. Ajouter les jours supplémentaires d'ancienneté
    jours_anciennete = calculer_jours_anciennete(employe, parametres)
    jours_total = jours_base + jours_anciennete

    # 7. Appliquer le coefficient temps partiel
    if parametres.prise_compte_temps_partiel:
        jours_total = jours_total * employe.coefficient_temps_travail

    return jours_total.quantize(Decimal('0.01'))


def calculer_mois_travailles(employe, annee_reference):
    """
    Calcule le nombre de mois travaillés par l'employé dans l'année de référence
    """
    from django.utils import timezone

    if not employe.date_entree_entreprise:
        return Decimal('0.00')

    # Récupérer la convention
    convention = employe.convention_applicable
    if not convention:
        return Decimal('0.00')

    # ✅ Utiliser la méthode helper pour obtenir la période
    debut_annee, fin_annee = convention.get_periode_acquisition(annee_reference)

    # Déterminer la date limite
    date_actuelle = timezone.now().date()

    if debut_annee > date_actuelle:
        return Decimal('0.00')

    if date_actuelle >= debut_annee and date_actuelle <= fin_annee:
        date_limite_calcul = date_actuelle
    elif date_actuelle > fin_annee:
        date_limite_calcul = fin_annee
    else:
        return Decimal('0.00')

    # Calculer la période de travail
    date_debut = max(employe.date_entree_entreprise, debut_annee)
    date_fin = min(date_limite_calcul, fin_annee)

    if date_debut > date_fin:
        return Decimal('0.00')

    # Calculer mois par mois
    mois_total = Decimal('0.00')
    current_date = date(date_debut.year, date_debut.month, 1)

    while current_date <= date_fin:
        mois = current_date.month
        annee = current_date.year

        premier_jour = date(annee, mois, 1)
        dernier_jour = date(annee, mois, calendar.monthrange(annee, mois)[1])

        debut_effectif = max(date_debut, premier_jour)
        fin_effective = min(date_fin, dernier_jour)

        if debut_effectif <= fin_effective:
            jours_calendaires = (fin_effective - debut_effectif).days + 1

            if jours_calendaires >= 25:
                mois_total += Decimal('1.00')
            elif jours_calendaires >= 15:
                mois_total += Decimal('0.50')

        if mois == 12:
            current_date = date(annee + 1, 1, 1)
        else:
            current_date = date(annee, mois + 1, 1)

    return mois_total


def calculer_jours_anciennete(employe, parametres):
    """
    Calcule les jours supplémentaires selon l'ancienneté

    Returns:
        Decimal: Nombre de jours supplémentaires
    """
    if not parametres.jours_supp_anciennete:
        return Decimal('0.00')

    anciennete = employe.anciennete_annees
    jours_supp = Decimal('0.00')

    # Parcourir les paliers d'ancienneté (trié décroissant)
    paliers = sorted(
        [(int(k), v) for k, v in parametres.jours_supp_anciennete.items()],
        reverse=True
    )

    for annees, jours in paliers:
        if anciennete >= annees:
            jours_supp = Decimal(str(jours))
            break

    return jours_supp


# ===== VUES PRINCIPALES =====

@login_required
def liste_absences(request):
    user_employe = request.user.employe

    # TOUT LE MONDE voit uniquement SES PROPRES absences
    absences = Absence.objects.filter(employe=user_employe)
    view_type = 'employe'

    # Filtres
    form = AbsenceRechercheForm(request.GET)

    if form.is_valid():
        search = form.cleaned_data.get('search')
        type_absence = form.cleaned_data.get('type_absence')
        statut = form.cleaned_data.get('statut')
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')

        if type_absence:
            absences = absences.filter(type_absence=type_absence)

        if statut:
            absences = absences.filter(statut=statut)

        if date_debut:
            absences = absences.filter(date_fin__gte=date_debut)

        if date_fin:
            absences = absences.filter(date_debut__lte=date_fin)

    # Tri
    absences = absences.select_related(
        'employe',
        'type_absence',
        'manager_validateur',
        'rh_validateur',
        'created_by'
    ).order_by('-date_debut', '-created_at')

    # Pagination
    paginator = Paginator(absences, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques (UNIQUEMENT pour l'employé connecté)
    stats = absences.aggregate(
        total=Count('id'),
        en_attente=Count('id', filter=Q(statut__in=['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH'])),
        validees=Count('id', filter=Q(statut='VALIDE')),
        rejetees=Count('id', filter=Q(statut='REJETE')),
        total_jours=Sum('jours_ouvrables', filter=Q(statut='VALIDE'))
    )

    # Solde de congés de l'utilisateur
    annee_courante = timezone.now().year
    solde_disponible = None
    try:
        acquisition = AcquisitionConges.objects.get(
            employe=user_employe,
            annee_reference=annee_courante - 1  # Système N+1
        )
        solde_disponible = {
            'annee_acquisition': annee_courante - 1,
            'jours_acquis': acquisition.jours_acquis,
            'jours_pris': acquisition.jours_pris,
            'jours_restants': acquisition.jours_restants,
        }
    except AcquisitionConges.DoesNotExist:
        pass

    context = {
        'page_obj': page_obj,
        'form': form,
        'stats': stats,
        'view_type': view_type,
        'solde_disponible': solde_disponible,
        'annee_courante': annee_courante,
    }

    return render(request, 'absence/absences_list.html', context)


@login_required
def validation_manager(request):
    """
    Liste des absences à valider pour le manager connecté
    Basé sur ZYMA (managers de départements) et ZYAF (affectations)
    """
    user_employe = request.user.employe

    # Vérifier que l'utilisateur est bien manager
    if not user_employe.est_manager_departement():
        messages.error(request, "Vous n'avez pas les droits de manager")
        return redirect('absence:liste_absences')

    # Récupérer les départements gérés
    from departement.models import ZYMA, ZDDE
    from employee.models import ZYAF

    departements_geres = ZYMA.objects.filter(
        employe=user_employe,
        actif=True,
        date_fin__isnull=True
    ).select_related('departement')

    if not departements_geres.exists():
        messages.warning(request, "Aucun département sous votre responsabilité")
        return redirect('absence:liste_absences')

    dept_ids = [d.departement.id for d in departements_geres]
    departements = ZDDE.objects.filter(id__in=dept_ids)

    # Récupérer les employés des départements gérés (via ZYAF)
    employes_ids = ZYAF.objects.filter(
        poste__DEPARTEMENT__in=dept_ids,
        date_fin__isnull=True,  # Affectation active
        employe__etat='actif'
    ).values_list('employe', flat=True).distinct()

    # Récupérer les absences en attente de validation manager
    absences = Absence.objects.filter(
        employe__in=employes_ids,
        statut='EN_ATTENTE_MANAGER'
    ).select_related(
        'employe',
        'type_absence'
    ).order_by('date_debut')

    # ✅ Ajouter le département de chaque employé
    for absence in absences:
        affectation = ZYAF.objects.filter(
            employe=absence.employe,
            date_fin__isnull=True
        ).select_related('poste__DEPARTEMENT').first()

        absence.employe_departement = affectation.poste.DEPARTEMENT.LIBELLE if affectation else "Non affecté"

    # Filtres
    departement_filter = request.GET.get('departement', '')
    type_filter = request.GET.get('type_absence', '')
    search = request.GET.get('search', '').strip()

    if departement_filter:
        employes_dept = ZYAF.objects.filter(
            poste__DEPARTEMENT_id=departement_filter,
            date_fin__isnull=True
        ).values_list('employe', flat=True)
        absences = absences.filter(employe__in=employes_dept)

    if type_filter:
        absences = absences.filter(type_absence_id=type_filter)

    if search:
        absences = absences.filter(
            Q(employe__nom__icontains=search) |
            Q(employe__prenoms__icontains=search) |
            Q(employe__matricule__icontains=search)
        )

    # Statistiques
    stats = {
        'total': absences.count(),
        'employes_count': absences.values('employe').distinct().count(),
        'jours_total': absences.aggregate(Sum('jours_ouvrables'))['jours_ouvrables__sum'] or 0,
    }

    # Types d'absence pour le filtre
    types_absence = TypeAbsence.objects.filter(actif=True).order_by('libelle')

    context = {
        'user_employe': user_employe,
        'absences_a_valider': absences,
        'departements_geres': departements,
        'stats': stats,
        'types_absence': types_absence,
        'departement_filter': departement_filter,
        'type_filter': type_filter,
        'search': search,
    }

    return render(request, 'absence/validation_manager.html', context)


@login_required
@drh_or_admin_required
def validation_rh(request):
    """
    Liste des absences à valider pour les RH
    Basé sur le système de rôles ZYRO/ZYRE
    """
    user_employe = request.user.employe

    # Vérifier que l'utilisateur a le rôle RH
    if not user_employe.peut_valider_absence_rh():
        messages.error(request, "Vous n'avez pas les droits de validation RH")
        return redirect('absence:liste_absences')

    # Récupérer toutes les absences en attente de validation RH
    absences = Absence.objects.filter(
        statut='EN_ATTENTE_RH'
    ).select_related(
        'employe',
        'type_absence',
        'manager_validateur'
    ).order_by('date_debut')

    # Filtres
    type_filter = request.GET.get('type_absence', '')
    search = request.GET.get('search', '').strip()

    if type_filter:
        absences = absences.filter(type_absence_id=type_filter)

    if search:
        absences = absences.filter(
            Q(employe__nom__icontains=search) |
            Q(employe__prenoms__icontains=search) |
            Q(employe__matricule__icontains=search)
        )

    # Statistiques
    stats = {
        'total': absences.count(),
        'employes_count': absences.values('employe').distinct().count(),
        'jours_total': absences.aggregate(Sum('jours_ouvrables'))['jours_ouvrables__sum'] or 0,
    }

    # Types d'absence pour le filtre
    types_absence = TypeAbsence.objects.filter(actif=True).order_by('libelle')

    context = {
        'user_employe': user_employe,
        'absences_a_valider': absences,
        'stats': stats,
        'types_absence': types_absence,
        'type_filter': type_filter,
        'search': search,
    }

    return render(request, 'absence/validation_rh.html', context)


@never_cache
@login_required
def creer_absence(request):
    """Créer une nouvelle demande d'absence"""
    user_employe = request.user.employe

    if request.method == 'POST':
        # Détecter si c'est une requête AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        form = AbsenceForm(request.POST, request.FILES, user=user_employe)

        if form.is_valid():
            absence = form.save(commit=False)
            absence.employe = user_employe
            absence.created_by = user_employe
            absence.statut = 'EN_ATTENTE_MANAGER'
            absence.save()

            # Réponse JSON pour AJAX
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Demande d\'absence créée avec succès',
                    'redirect_url': reverse('absence:liste_absences')
                })

            # Réponse HTML classique (fallback)
            messages.success(request, 'Demande d\'absence créée avec succès')
            return redirect('absence:liste_absences')

        else:
            # ✅ Erreurs de validation pour AJAX
            if is_ajax:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(e) for e in error_list]

                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Veuillez corriger les erreurs dans le formulaire'
                }, status=400)

    else:
        form = AbsenceForm(user=user_employe)

    context = {
        'form': form,
        'title': 'Nouvelle demande d\'absence',
        'employe': user_employe
    }

    return render(request, 'absence/absence_form.html', context)


@login_required
def modifier_absence(request, id):
    """Modifier une absence existante"""
    user_employe = request.user.employe
    absence = get_object_or_404(Absence, id=id)

    if absence.employe != user_employe:
        messages.error(request, 'Vous ne pouvez modifier que vos propres absences')
        return redirect('absence:liste_absences')

    if not absence.peut_modifier:
        messages.error(request, f'Impossible de modifier une absence avec le statut "{absence.get_statut_display()}"')
        return redirect('absence:liste_absences')

    if request.method == 'POST':
        # Détecter si c'est une requête AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        form = AbsenceForm(request.POST, request.FILES, instance=absence, user=user_employe)

        if form.is_valid():
            with transaction.atomic():
                absence = form.save(commit=False)
                absence.employe = user_employe
                absence.save()

            # ✅ Réponse JSON pour AJAX
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Absence modifiée avec succès',
                    'redirect_url': reverse('absence:liste_absences')
                })

            messages.success(request, '✅ Absence modifiée avec succès')
            return redirect('absence:liste_absences')

        else:
            # ✅ Erreurs de validation pour AJAX
            if is_ajax:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(e) for e in error_list]

                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Veuillez corriger les erreurs dans le formulaire'
                }, status=400)

    else:
        form = AbsenceForm(instance=absence, user=user_employe)

    context = {
        'form': form,
        'absence': absence,
        'title': 'Modifier l\'absence',
        'employe': user_employe
    }

    return render(request, 'absence/absence_form.html', context)


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

        # Sauvegarder le type pour le message
        type_absence = absence.type_absence.libelle

        with transaction.atomic():
            absence.delete()

        logger.info("✅ Absence supprimée: %s", type_absence)

        return JsonResponse({
            'success': True,
            'message': f'Absence "{type_absence}" supprimée avec succès'
        })

    except Exception as e:
        logger.exception("❌ ERREUR lors de la suppression:")
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

        # Vérification propriétaire
        if absence.employe != user_employe:
            logger.warning("❌ Employé différent: %s tenté d'annuler l'absence de %s", user_employe, absence.employe)
            return JsonResponse({
                'success': False,
                'error': 'Vous ne pouvez annuler que vos propres absences'
            }, status=403)

        # Vérifier si l'absence peut être annulée
        if not absence.peut_annuler:
            logger.warning("❌ L'absence ne peut pas être annulée (statut: %s)", absence.statut)
            return JsonResponse({
                'success': False,
                'error': f'Impossible d\'annuler une absence avec le statut "{absence.get_statut_display()}"'
            }, status=400)

        # Annuler l'absence
        with transaction.atomic():
            absence.annuler(user_employe)

        logger.info("✅ Absence annulée avec succès par %s", user_employe)

        return JsonResponse({
            'success': True,
            'message': f'Absence "{absence.type_absence.libelle}" annulée avec succès'
        })

    except ValidationError as e:
        logger.error("❌ ValidationError: %s", e)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.exception("❌ ERREUR lors de l'annulation:")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def api_mes_absences_calendrier(request):
    """Récupérer les absences de l'employé connecté pour le calendrier"""
    try:
        user_employe = request.user.employe
        start = request.GET.get('start')
        end = request.GET.get('end')

        logger.debug("📅 API Calendrier appelée - Employé: %s", user_employe)
        logger.debug("📅 Start: %s, End: %s", start, end)

        # Convertir les dates
        if start:
            start_date = timezone.datetime.fromisoformat(start.replace('Z', '+00:00')).date()
        else:
            start_date = timezone.now().date()

        if end:
            end_date = timezone.datetime.fromisoformat(end.replace('Z', '+00:00')).date()
        else:
            end_date = start_date + timedelta(days=30)

        logger.debug("📅 Dates traitées: %s -> %s", start_date, end_date)

        # Récupérer les absences
        absences = Absence.objects.filter(
            employe=user_employe,
            date_debut__lte=end_date,
            date_fin__gte=start_date
        ).select_related('type_absence')

        logger.debug("📅 Nombre d'absences trouvées: %s", absences.count())

        data = []
        for abs in absences:
            data.append({
                'id': abs.id,
                'type_absence': abs.type_absence.libelle,  # Important: utiliser 'libelle' pas 'nom'
                'date_debut': abs.date_debut.strftime('%Y-%m-%d'),
                'date_fin': abs.date_fin.strftime('%Y-%m-%d'),
                'jours_ouvrables': str(abs.jours_ouvrables),
                'statut': abs.statut,
                'couleur': getattr(abs.type_absence, 'couleur', '#1c5d5f'),
                'employe': str(abs.employe)
            })

        logger.debug("📅 Données retournées: %s éléments", len(data))

        return JsonResponse({
            'success': True,
            'absences': data
        })

    except Exception as e:
        logger.exception("❌ ERREUR API Calendrier:")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== API ENDPOINTS (suite) =====

@require_http_methods(["GET"])
@login_required
@drh_or_admin_required
@gestion_app_required
def api_acquisition_employe_annee(request, employe_id, annee):
    """
    Récupérer l'acquisition de congés d'un employé pour une année
    ✅ Seul l'employé connecté peut voir son propre solde
    """
    try:
        user_employe = request.user.employe

        # ✅ VÉRIFICATION : Seul son propre solde
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


@require_http_methods(["GET"])
@login_required
def api_absence_detail(request, id):
    """Récupérer les détails d'une absence"""
    try:
        absence = get_object_or_404(Absence, id=id)
        user_employe = request.user.employe

        # Vérifier les permissions (AJOUT DE ASSISTANT_RH)
        if not (absence.employe == user_employe or
                user_employe.has_role('DRH') or
                user_employe.has_role('RH_VALIDATION_ABS') or
                user_employe.has_role('ASSISTANT_RH') or  # ✅ AJOUTÉ
                user_employe.has_role('GESTION_APP') or  # ✅ AJOUTÉ
                user_employe.est_manager_departement()):
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # ... le reste de votre code reste identique
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
            'motif': absence.motif or '',  # ✅ Ajout de valeur par défaut
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

        # Historique de validation
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
def api_valider_absence(request, id):
    """
    Valider ou rejeter une absence (manager ou RH)
    """
    try:
        absence = get_object_or_404(Absence, id=id)
        user_employe = request.user.employe

        # Récupérer la décision depuis le formulaire
        decision = request.POST.get('decision')
        commentaire = request.POST.get('commentaire', '').strip()

        logger.info("📋 Validation demandée par %s", user_employe)
        logger.info("   - Absence ID: %s", id)
        logger.info("   - Décision: %s", decision)
        logger.info("   - Commentaire: %s", commentaire)

        # Déterminer si c'est une validation manager ou RH
        if absence.statut == 'EN_ATTENTE_MANAGER':
            # Validation manager
            absence.valider_par_manager(user_employe, decision, commentaire)
            message = f'Absence {decision.lower()}e par le manager'

        elif absence.statut == 'EN_ATTENTE_RH':
            # Validation RH
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
        logger.error("❌ Erreur de validation: %s", e)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception as e:
        logger.exception("❌ Erreur serveur:")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def api_verifier_solde(request):
    """
    Vérifier le solde de congés disponible pour une période donnée
    """
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

        # Calculer les jours ouvrables demandés
        jours_demandes = 0
        current = date_debut
        while current <= date_fin:
            if current.weekday() < 5:  # Lundi à Vendredi
                jours_demandes += 1
            current += timedelta(days=1)

        # Récupérer le solde disponible (système N+1)
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
def api_historique_validation(request, id):
    """
    Récupérer l'historique de validation d'une absence
    """
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
def api_type_detail(request, id):
    """Récupérer les détails d'un type d'absence"""
    try:
        type_absence = get_object_or_404(TypeAbsence, id=id)

        data = {
            'id': type_absence.id,
            'code': type_absence.code,
            'libelle': type_absence.libelle,  # ✅ Utiliser 'libelle' pas 'nom'
            'description': type_absence.description if hasattr(type_absence, 'description') else '',
            'decompte_solde': type_absence.decompte_solde,
            'justificatif_obligatoire': type_absence.justificatif_obligatoire,
            'couleur': type_absence.couleur if hasattr(type_absence, 'couleur') else '#1c5d5f',
        }

        return JsonResponse({
            'success': True,
            'data': data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
@login_required
def api_jours_feries(request):
    """
    Récupérer les jours fériés pour le calendrier
    """
    try:
        start = request.GET.get('start')
        end = request.GET.get('end')

        if not start or not end:
            return JsonResponse({'success': False, 'error': 'Paramètres manquants'}, status=400)

        # Convertir les dates
        start_date = timezone.datetime.strptime(start, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(end, '%Y-%m-%d').date()

        # ✅ CORRECTION IMPORTANTE : Filtrer par actif=True
        jours_feries = JourFerie.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            actif=True  # ✅ SEULEMENT les jours fériés actifs
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
        logger.exception("❌ ERREUR API Jours Fériés:")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def notification_detail(request, id):
    """
    Marquer une notification comme lue et rediriger selon le CONTEXTE
    """
    notification = get_object_or_404(
        NotificationAbsence,
        id=id,
        destinataire=request.user.employe
    )

    # Marquer comme lue
    notification.marquer_comme_lue()
    contexte = notification.contexte

    # ========================================
    # REDIRECTION BASÉE SUR LE CONTEXTE
    # ========================================

    if contexte == 'MANAGER':
        # Notification reçue en tant que MANAGER
        # → Rediriger vers validation_manager
        return redirect('absence:validation_manager')

    elif contexte == 'RH':
        # Notification reçue en tant que RH
        # → Rediriger vers validation_rh
        return redirect('absence:validation_rh')

    else:  # contexte == 'EMPLOYE' ou par défaut
        # Notification reçue en tant qu'EMPLOYÉ
        # → Rediriger vers liste_absences
        return redirect('absence:liste_absences')


@login_required
def marquer_toutes_lues(request):
    """Marquer toutes les notifications comme lues"""
    NotificationAbsence.objects.filter(
        destinataire=request.user.employe,
        lue=False
    ).update(lue=True, date_lecture=timezone.now())

    # Pas de message - redirection silencieuse
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


@login_required
def toutes_notifications(request):
    """Page listant toutes les notifications avec filtres"""
    notifications = NotificationAbsence.objects.filter(
        destinataire=request.user.employe
    ).select_related('absence', 'absence__employe', 'absence__type_absence').order_by('-date_creation')

    # Filtres
    statut_filter = request.GET.get('statut', '')
    type_filter = request.GET.get('type', '')

    if statut_filter == 'non_lues':
        notifications = notifications.filter(lue=False)
    elif statut_filter == 'lues':
        notifications = notifications.filter(lue=True)

    if type_filter:
        notifications = notifications.filter(type_notification=type_filter)

    # Compter les non lues
    notifications_count = NotificationAbsence.objects.filter(
        destinataire=request.user.employe,
        lue=False
    ).count()

    # Pagination
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'notifications_count': notifications_count,
        'title': 'Toutes les notifications'
    }

    return render(request, 'absence/toutes_notifications.html', context)


@role_required('ASSISTANT_RH', 'RH_VALIDATION_ABS', 'GESTION_APP', 'DRH')
def consultation_absences(request):
    """
    Vue de consultation des absences pour Assistant RH
    Lecture seule - pas de validation
    """
    user_employe = request.user.employe

    # Toutes les absences
    absences = Absence.objects.all().select_related(
        'employe',
        'type_absence',
        'manager_validateur',
        'rh_validateur'
    ).order_by('-date_debut')

    # Types d'absence pour le filtre
    types_absence = TypeAbsence.objects.filter(actif=True)

    # Filtres
    search = request.GET.get('search', '')
    type_absence = request.GET.get('type_absence', '')
    statut = request.GET.get('statut', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    if search:
        absences = absences.filter(
            Q(employe__nom__icontains=search) |
            Q(employe__prenoms__icontains=search) |
            Q(employe__matricule__icontains=search)
        )

    if type_absence:
        absences = absences.filter(type_absence_id=type_absence)

    if statut:
        absences = absences.filter(statut=statut)

    if date_debut:
        absences = absences.filter(date_fin__gte=date_debut)

    if date_fin:
        absences = absences.filter(date_debut__lte=date_fin)

    # Statistiques
    stats = absences.aggregate(
        total=Count('id'),
        en_attente=Count('id', filter=Q(statut__in=['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH'])),
        validees=Count('id', filter=Q(statut='VALIDE')),
        rejetees=Count('id', filter=Q(statut='REJETE')),
        total_jours=Sum('jours_ouvrables', filter=Q(statut='VALIDE'))
    )

    # Pagination
    paginator = Paginator(absences, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'types_absence': types_absence,
        'stats': stats,
        'view_type': 'consultation',
        'can_validate': False,
    }

    return render(request, 'absence/consultation_absences.html', context)