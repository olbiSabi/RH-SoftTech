# absence/views_modules/validation_views.py
"""
Vues pour la validation des absences:
- Validation manager
- Validation RH
- Consultation (lecture seule)
"""
import logging

from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from absence.decorators import drh_or_admin_required, role_required
from absence.models import Absence, TypeAbsence

logger = logging.getLogger(__name__)


@login_required
def validation_manager(request):
    """
    Liste des absences à valider pour le manager connecté
    Basé sur ZYMA (managers de départements) et ZYAF (affectations)
    """
    user_employe = request.user.employe

    if not user_employe.est_manager_departement():
        messages.error(request, "Vous n'avez pas les droits de manager")
        return redirect('absence:liste_absences')

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

    employes_ids = ZYAF.objects.filter(
        poste__DEPARTEMENT__in=dept_ids,
        date_fin__isnull=True,
        employe__etat='actif'
    ).values_list('employe', flat=True).distinct()

    absences = Absence.objects.filter(
        employe__in=employes_ids,
        statut='EN_ATTENTE_MANAGER'
    ).select_related(
        'employe',
        'type_absence'
    ).order_by('date_debut')

    for absence in absences:
        affectation = ZYAF.objects.filter(
            employe=absence.employe,
            date_fin__isnull=True
        ).select_related('poste__DEPARTEMENT').first()

        absence.employe_departement = affectation.poste.DEPARTEMENT.LIBELLE if affectation else "Non affecté"

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

    stats = {
        'total': absences.count(),
        'employes_count': absences.values('employe').distinct().count(),
        'jours_total': absences.aggregate(Sum('jours_ouvrables'))['jours_ouvrables__sum'] or 0,
    }

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

    if not user_employe.peut_valider_absence_rh():
        messages.error(request, "Vous n'avez pas les droits de validation RH")
        return redirect('absence:liste_absences')

    absences = Absence.objects.filter(
        statut='EN_ATTENTE_RH'
    ).select_related(
        'employe',
        'type_absence',
        'manager_validateur'
    ).order_by('date_debut')

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

    stats = {
        'total': absences.count(),
        'employes_count': absences.values('employe').distinct().count(),
        'jours_total': absences.aggregate(Sum('jours_ouvrables'))['jours_ouvrables__sum'] or 0,
    }

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


@role_required('ASSISTANT_RH', 'RH_VALIDATION_ABS', 'GESTION_APP', 'DRH')
def consultation_absences(request):
    """
    Vue de consultation des absences pour Assistant RH
    Lecture seule - pas de validation
    """
    user_employe = request.user.employe

    absences = Absence.objects.all().select_related(
        'employe',
        'type_absence',
        'manager_validateur',
        'rh_validateur'
    ).order_by('-date_debut')

    types_absence = TypeAbsence.objects.filter(actif=True)

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

    stats = absences.aggregate(
        total=Count('id'),
        en_attente=Count('id', filter=Q(statut__in=['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH'])),
        validees=Count('id', filter=Q(statut='VALIDE')),
        rejetees=Count('id', filter=Q(statut='REJETE')),
        total_jours=Sum('jours_ouvrables', filter=Q(statut='VALIDE'))
    )

    from django.core.paginator import Paginator
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
