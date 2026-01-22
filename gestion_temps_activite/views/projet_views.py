# gestion_temps_activite/views/projet_views.py
"""Vues pour la gestion des projets (ZDPJ)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from absence.decorators import role_required
from gestion_temps_activite.models import ZDCL, ZDPJ
from gestion_temps_activite.forms import ZDPJForm
from gestion_temps_activite.services import StatistiqueService


@login_required
def projet_liste(request):
    """Liste des projets."""
    projets = ZDPJ.objects.select_related('client', 'chef_projet').all().order_by('-date_creation')

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        projets = projets.filter(
            Q(code_projet__icontains=search_query) |
            Q(nom_projet__icontains=search_query) |
            Q(client__raison_sociale__icontains=search_query)
        )

    # Filtrage
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        projets = projets.filter(statut=statut_filter)

    client_filter = request.GET.get('client', '')
    if client_filter:
        projets = projets.filter(client_id=client_filter)

    actif_filter = request.GET.get('actif', '')
    if actif_filter:
        projets = projets.filter(actif=(actif_filter == 'True'))

    # Annotations
    projets = StatistiqueService.annotate_projets_stats(projets)

    # Pagination
    paginator = Paginator(projets, 15)
    page_number = request.GET.get('page')
    projets_page = paginator.get_page(page_number)

    # Liste des clients pour le filtre
    clients = ZDCL.objects.filter(actif=True).order_by('raison_sociale')

    context = {
        'projets': projets_page,
        'clients': clients,
        'search_query': search_query,
        'statut_filter': statut_filter,
        'client_filter': client_filter,
        'actif_filter': actif_filter,
        'total_projets': projets.count()
    }

    return render(request, 'gestion_temps_activite/projet_liste.html', context)


@login_required
def projet_detail(request, pk):
    """Détails d'un projet."""
    projet = get_object_or_404(
        ZDPJ.objects.select_related('client', 'chef_projet'),
        pk=pk
    )

    # Récupérer les tâches avec annotations
    taches = StatistiqueService.annotate_taches_stats(
        projet.taches.select_related('assignee')
    )

    # Documents du projet
    documents = projet.documents.filter(actif=True).select_related('uploade_par')

    # Statistiques
    stats = StatistiqueService.get_stats_projet(projet)

    context = {
        'projet': projet,
        'taches': taches,
        'documents': documents,
        'total_taches': stats['total_taches'],
        'taches_terminees': stats['taches_terminees'],
        'heures_totales': stats['heures_totales'],
        'budget_restant': stats['budget_restant'],
        'pourcentage_budget': stats['pourcentage_budget'],
        'avancement': stats['avancement']
    }

    return render(request, 'gestion_temps_activite/projet_detail.html', context)


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def projet_create(request):
    """Créer un nouveau projet."""
    if request.method == 'POST':
        form = ZDPJForm(request.POST)
        if form.is_valid():
            projet = form.save(commit=False)
            if hasattr(request.user, 'employe'):
                projet.cree_par = request.user.employe
            projet.save()

            return redirect('gestion_temps_activite:projet_detail', pk=projet.pk)
        else:
            messages.error(request, 'Erreur lors de la création du projet.')
    else:
        form = ZDPJForm()

    context = {
        'form': form,
        'title': 'Nouveau Projet',
        'action': 'Créer'
    }

    return render(request, 'gestion_temps_activite/projet_form.html', context)


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def projet_update(request, pk):
    """Modifier un projet."""
    projet = get_object_or_404(ZDPJ, pk=pk)

    if request.method == 'POST':
        form = ZDPJForm(request.POST, instance=projet)
        if form.is_valid():
            form.save()
            return redirect('gestion_temps_activite:projet_detail', pk=projet.pk)
        else:
            messages.error(request, 'Erreur lors de la modification.')
    else:
        form = ZDPJForm(instance=projet)

    context = {
        'form': form,
        'projet': projet,
        'title': 'Modifier Projet',
        'action': 'Modifier'
    }

    return render(request, 'gestion_temps_activite/projet_form.html', context)


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def projet_delete(request, pk):
    """Supprimer un projet."""
    projet = get_object_or_404(ZDPJ, pk=pk)

    if request.method == 'POST':
        try:
            projet.delete()
            return redirect('gestion_temps_activite:projet_liste')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer : {str(e)}')
            return redirect('gestion_temps_activite:projet_detail', pk=pk)

    context = {
        'projet': projet,
        'taches_count': projet.taches.count(),
        'documents_count': projet.documents.count()
    }

    return render(request, 'gestion_temps_activite/projet_confirm_delete.html', context)
