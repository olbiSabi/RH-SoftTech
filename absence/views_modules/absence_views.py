# absence/views_modules/absence_views.py
"""
Vues pour la gestion des absences:
- Liste des absences
- Création d'absence
- Modification d'absence
"""
import logging

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from absence.models import Absence, AcquisitionConges
from absence.forms import AbsenceForm, AbsenceRechercheForm

logger = logging.getLogger(__name__)


@login_required
def liste_absences(request):
    """Liste des absences de l'employé connecté"""
    user_employe = request.user.employe

    absences = Absence.objects.filter(employe=user_employe)
    view_type = 'employe'

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

    absences = absences.select_related(
        'employe',
        'type_absence',
        'manager_validateur',
        'rh_validateur',
        'created_by'
    ).order_by('-date_debut', '-created_at')

    paginator = Paginator(absences, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    stats = absences.aggregate(
        total=Count('id'),
        en_attente=Count('id', filter=Q(statut__in=['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH'])),
        validees=Count('id', filter=Q(statut='VALIDE')),
        rejetees=Count('id', filter=Q(statut='REJETE')),
        total_jours=Sum('jours_ouvrables', filter=Q(statut='VALIDE'))
    )

    annee_courante = timezone.now().year
    solde_disponible = None
    try:
        acquisition = AcquisitionConges.objects.get(
            employe=user_employe,
            annee_reference=annee_courante - 1
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


@never_cache
@login_required
def creer_absence(request):
    """Créer une nouvelle demande d'absence"""
    user_employe = request.user.employe

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        form = AbsenceForm(request.POST, request.FILES, user=user_employe)

        if form.is_valid():
            absence = form.save(commit=False)
            absence.employe = user_employe
            absence.created_by = user_employe
            absence.statut = 'EN_ATTENTE_MANAGER'
            absence.save()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Demande d\'absence créée avec succès',
                    'redirect_url': reverse('absence:liste_absences')
                })

            messages.success(request, 'Demande d\'absence créée avec succès')
            return redirect('absence:liste_absences')

        else:
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
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        form = AbsenceForm(request.POST, request.FILES, instance=absence, user=user_employe)

        if form.is_valid():
            with transaction.atomic():
                absence = form.save(commit=False)
                absence.employe = user_employe
                absence.save()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Absence modifiée avec succès',
                    'redirect_url': reverse('absence:liste_absences')
                })

            messages.success(request, 'Absence modifiée avec succès')
            return redirect('absence:liste_absences')

        else:
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
