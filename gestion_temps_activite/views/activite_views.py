# gestion_temps_activite/views/activite_views.py
"""Vues pour la gestion des types d'activités (ZDAC)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from absence.decorators import role_required
from gestion_temps_activite.models import ZDAC
from gestion_temps_activite.forms import ZDACForm


@role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def activite_liste(request):
    """Liste des types d'activités."""
    activites = ZDAC.objects.all().order_by('code_activite')

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        activites = activites.filter(
            Q(code_activite__icontains=search_query) |
            Q(libelle__icontains=search_query)
        )

    # Filtrage
    facturable_filter = request.GET.get('facturable', '')
    if facturable_filter:
        activites = activites.filter(facturable=(facturable_filter == 'True'))

    actif_filter = request.GET.get('actif', '')
    if actif_filter:
        activites = activites.filter(actif=(actif_filter == 'True'))

    # Annotations
    activites = activites.annotate(
        nombre_imputations=Count('imputations')
    )

    context = {
        'activites': activites,
        'search_query': search_query,
        'facturable_filter': facturable_filter,
        'actif_filter': actif_filter
    }

    return render(request, 'gestion_temps_activite/activite_liste.html', context)


@role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def activite_create(request):
    """Créer un nouveau type d'activité."""
    if request.method == 'POST':
        form = ZDACForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion_temps_activite:activite_liste')
        else:
            messages.error(request, 'Erreur lors de la création du type d\'activité.')
    else:
        initial_data = {'date_debut': timezone.now().date()}
        form = ZDACForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'Nouveau Type d\'Activité',
        'action': 'Créer'
    }

    return render(request, 'gestion_temps_activite/activite_form.html', context)


@role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def activite_update(request, pk):
    """Modifier un type d'activité."""
    activite = get_object_or_404(ZDAC, pk=pk)

    if request.method == 'POST':
        form = ZDACForm(request.POST, instance=activite)
        if form.is_valid():
            form.save()
            return redirect('gestion_temps_activite:activite_liste')
        else:
            messages.error(request, 'Erreur lors de la modification.')
    else:
        form = ZDACForm(instance=activite)

    context = {
        'form': form,
        'activite': activite,
        'title': 'Modifier Type d\'Activité',
        'action': 'Modifier'
    }

    return render(request, 'gestion_temps_activite/activite_form.html', context)


@role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def activite_delete(request, pk):
    """Supprimer un type d'activité."""
    activite = get_object_or_404(ZDAC, pk=pk)

    if request.method == 'POST':
        try:
            activite.delete()
            return redirect('gestion_temps_activite:activite_liste')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer : {str(e)}')
            return redirect('gestion_temps_activite:activite_liste')

    context = {
        'activite': activite,
        'imputations_count': activite.imputations.count()
    }

    return render(request, 'gestion_temps_activite/activite_confirm_delete.html', context)
