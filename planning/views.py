"""Views pour le module Planning."""
import json

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.db.models import Count

_CACHE_TTL = getattr(settings, 'CACHE_TTL_PLANNING', 300)

from .models import Planning, SiteTravail, PosteTravail, Affectation, Evenement
from .forms import SiteTravailForm, PosteTravailForm, PlanningForm
from .permissions import get_planning_role, get_visible_employees, get_visible_plannings, can_edit_planning


@login_required
def planning_calendar(request):
    """Vue calendrier principale avec FullCalendar (données de select mises en cache 5 min)."""
    role = get_planning_role(request.user)
    if not role:
        messages.error(request, "Vous n'avez pas acces au module Planning.")
        return redirect('home')

    can_edit = can_edit_planning(request.user)
    visible_employees = get_visible_employees(request.user)

    postes_data = []
    employes_data = []
    plannings_data = []
    sites_data = []

    if can_edit:
        # Données de référence (postes, sites) : cache global
        ref_cache_key = 'planning_calendar_ref_data'
        ref_data = cache.get(ref_cache_key)
        if ref_data is None:
            ref_data = {
                'postes_data': list(
                    PosteTravail.objects.filter(is_active=True)
                    .select_related('site')
                    .values('id', 'nom', 'site__id', 'site__nom', 'heure_debut', 'heure_fin', 'type_poste')
                ),
                'sites_data': list(
                    SiteTravail.objects.filter(is_active=True).values('id', 'nom')
                ),
            }
            cache.set(ref_cache_key, ref_data, _CACHE_TTL)
        postes_data = ref_data['postes_data']
        sites_data = ref_data['sites_data']

        # Employés visibles et plannings : cache par utilisateur (périmètre variable)
        user_cache_key = f'planning_calendar_user_{request.user.pk}'
        user_data = cache.get(user_cache_key)
        if user_data is None:
            user_data = {
                'employes_data': list(visible_employees.values('matricule', 'nom', 'prenoms')),
                'plannings_data': list(
                    get_visible_plannings(request.user)
                    .filter(statut__in=['BROUILLON', 'PUBLIE'])
                    .values('id', 'titre', 'REFERENCE')
                ),
            }
            cache.set(user_cache_key, user_data, _CACHE_TTL)
        employes_data = user_data['employes_data']
        plannings_data = user_data['plannings_data']

    context = {
        'role': role,
        'can_edit': can_edit,
        'postes_json': json.dumps(postes_data, default=str),
        'employes_json': json.dumps(employes_data, default=str),
        'plannings_json': json.dumps(plannings_data, default=str),
        'sites_json': json.dumps(sites_data, default=str),
        'types_evenement': Evenement.TYPE_CHOICES,
        'statuts_affectation': Affectation.STATUT_CHOICES,
    }
    return render(request, 'planning/planning_simple.html', context)


@login_required
def mon_planning(request):
    """Vue 'Mon planning' - employe voit uniquement son planning."""
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Profil employe introuvable.")
        return redirect('home')

    context = {
        'role': 'employee',
        'can_edit': False,
        'employe': employe,
    }
    return render(request, 'planning/mon_planning.html', context)


# ===== GESTION DES SITES DE TRAVAIL =====

@login_required
def liste_sites(request):
    """Liste des sites de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    sites = SiteTravail.objects.annotate(
        nb_postes=Count('postetravail')
    ).order_by('nom')
    return render(request, 'planning/sites_list.html', {'sites': sites})


@login_required
def creer_site(request):
    """Creer un site de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    if request.method == 'POST':
        form = SiteTravailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Site '{form.instance.nom}' cree avec succes.")
            return redirect('planning:liste_sites')
    else:
        form = SiteTravailForm()

    return render(request, 'planning/site_form.html', {
        'form': form,
        'titre': 'Nouveau site de travail',
    })


@login_required
def modifier_site(request, pk):
    """Modifier un site de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    site = get_object_or_404(SiteTravail, pk=pk)

    if request.method == 'POST':
        form = SiteTravailForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, f"Site '{site.nom}' modifie avec succes.")
            return redirect('planning:liste_sites')
    else:
        form = SiteTravailForm(instance=site)

    return render(request, 'planning/site_form.html', {
        'form': form,
        'site': site,
        'titre': f'Modifier "{site.nom}"',
    })


@login_required
@require_POST
def supprimer_site(request, pk):
    """Supprimer un site de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    site = get_object_or_404(SiteTravail, pk=pk)

    # Verifier qu'aucun poste n'est rattache
    nb_postes = PosteTravail.objects.filter(site=site).count()
    if nb_postes > 0:
        messages.error(
            request,
            f"Impossible de supprimer le site '{site.nom}' : "
            f"{nb_postes} poste(s) de travail y sont rattache(s). "
            f"Supprimez d'abord les postes."
        )
        return redirect('planning:liste_sites')

    nom = site.nom
    site.delete()
    messages.success(request, f"Site '{nom}' supprime avec succes.")
    return redirect('planning:liste_sites')


# ===== GESTION DES POSTES DE TRAVAIL =====

@login_required
def liste_postes(request):
    """Liste des postes de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    postes = PosteTravail.objects.select_related('site').all().order_by('site__nom', 'nom')

    # Filtre par site
    site_id = request.GET.get('site')
    if site_id:
        postes = postes.filter(site_id=site_id)

    sites = SiteTravail.objects.filter(is_active=True).order_by('nom')

    return render(request, 'planning/postes_list.html', {
        'postes': postes,
        'sites': sites,
        'site_filtre': site_id,
    })


@login_required
def creer_poste(request):
    """Creer un poste de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    if request.method == 'POST':
        form = PosteTravailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Poste '{form.instance.nom}' cree avec succes.")
            return redirect('planning:liste_postes')
    else:
        form = PosteTravailForm()

    return render(request, 'planning/poste_form.html', {
        'form': form,
        'titre': 'Nouveau poste de travail',
    })


@login_required
def modifier_poste(request, pk):
    """Modifier un poste de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    poste = get_object_or_404(PosteTravail, pk=pk)

    if request.method == 'POST':
        form = PosteTravailForm(request.POST, instance=poste)
        if form.is_valid():
            form.save()
            messages.success(request, f"Poste '{poste.nom}' modifie avec succes.")
            return redirect('planning:liste_postes')
    else:
        form = PosteTravailForm(instance=poste)

    return render(request, 'planning/poste_form.html', {
        'form': form,
        'poste': poste,
        'titre': f'Modifier "{poste.nom}"',
    })


@login_required
@require_POST
def supprimer_poste(request, pk):
    """Supprimer un poste de travail."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    poste = get_object_or_404(PosteTravail, pk=pk)

    # Verifier qu'aucune affectation n'est rattachee
    nb_affectations = Affectation.objects.filter(poste=poste).count()
    if nb_affectations > 0:
        messages.error(
            request,
            f"Impossible de supprimer le poste '{poste.nom}' : "
            f"{nb_affectations} affectation(s) y sont rattachee(s)."
        )
        return redirect('planning:liste_postes')

    nom = poste.nom
    poste.delete()
    messages.success(request, f"Poste '{nom}' supprime avec succes.")
    return redirect('planning:liste_postes')


# ===== GESTION DES PLANNINGS =====

@login_required
def liste_plannings(request):
    """Liste des plannings."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    plannings = get_visible_plannings(request.user).select_related(
        'departement'
    ).annotate(
        nb_affectations=Count('affectations')
    ).order_by('-date_debut')
    return render(request, 'planning/plannings_list.html', {'plannings': plannings})


@login_required
def creer_planning(request):
    """Creer un planning."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    role = get_planning_role(request.user)

    if request.method == 'POST':
        form = PlanningForm(request.POST, user_role=role)
        if form.is_valid():
            planning = form.save(commit=False)
            planning.created_by = request.user
            # Auto-set departement pour les managers
            if role == 'manager':
                from employee.services.hierarchy_service import HierarchyService
                dept_ids = HierarchyService.get_managed_departments(request.user.employe)
                if dept_ids:
                    planning.departement_id = dept_ids[0]
            planning.save()
            messages.success(request, f"Planning '{planning.REFERENCE}' cree avec succes.")
            return redirect('planning:liste_plannings')
    else:
        form = PlanningForm(user_role=role)

    return render(request, 'planning/planning_form.html', {
        'form': form,
        'titre': 'Nouveau planning',
        'user_role': role,
    })


@login_required
def modifier_planning(request, pk):
    """Modifier un planning."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    planning = get_object_or_404(Planning, pk=pk)

    # Verifier que le planning est visible par l'utilisateur
    if not get_visible_plannings(request.user).filter(pk=pk).exists():
        return HttpResponseForbidden("Acces non autorise")

    role = get_planning_role(request.user)

    if request.method == 'POST':
        form = PlanningForm(request.POST, instance=planning, user_role=role)
        if form.is_valid():
            form.save()
            messages.success(request, f"Planning '{planning.REFERENCE}' modifie avec succes.")
            return redirect('planning:liste_plannings')
    else:
        form = PlanningForm(instance=planning, user_role=role)

    return render(request, 'planning/planning_form.html', {
        'form': form,
        'planning': planning,
        'titre': f'Modifier "{planning.REFERENCE} - {planning.titre}"',
        'user_role': role,
    })


@login_required
@require_POST
def supprimer_planning(request, pk):
    """Supprimer un planning."""
    if not can_edit_planning(request.user):
        return HttpResponseForbidden("Acces non autorise")

    planning = get_object_or_404(Planning, pk=pk)

    # Verifier que le planning est visible par l'utilisateur
    if not get_visible_plannings(request.user).filter(pk=pk).exists():
        return HttpResponseForbidden("Acces non autorise")

    # Verifier qu'aucune affectation n'est rattachee
    nb_affectations = Affectation.objects.filter(planning=planning).count()
    if nb_affectations > 0:
        messages.error(
            request,
            f"Impossible de supprimer le planning '{planning.REFERENCE}' : "
            f"{nb_affectations} affectation(s) y sont rattachee(s)."
        )
        return redirect('planning:liste_plannings')

    ref = planning.REFERENCE
    planning.delete()
    messages.success(request, f"Planning '{ref}' supprime avec succes.")
    return redirect('planning:liste_plannings')
