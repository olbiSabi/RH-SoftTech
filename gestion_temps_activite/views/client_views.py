# gestion_temps_activite/views/client_views.py
"""Vues pour la gestion des clients (ZDCL)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator

from absence.decorators import role_required
from gestion_temps_activite.models import ZDCL
from gestion_temps_activite.forms import ZDCLForm
from gestion_temps_activite.services import StatistiqueService


@role_required('DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def client_liste(request):
    """Liste des clients avec recherche et filtrage."""
    clients = ZDCL.objects.all().order_by('-date_creation')

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        clients = clients.filter(
            Q(code_client__icontains=search_query) |
            Q(raison_sociale__icontains=search_query) |
            Q(ville__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Filtrage par type
    type_filter = request.GET.get('type_client', '')
    if type_filter:
        clients = clients.filter(type_client=type_filter)

    # Filtrage par statut actif
    actif_filter = request.GET.get('actif', '')
    if actif_filter:
        clients = clients.filter(actif=(actif_filter == 'True'))

    # Annotations
    clients = StatistiqueService.annotate_clients_stats(clients)

    # Pagination
    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    clients_page = paginator.get_page(page_number)

    context = {
        'clients': clients_page,
        'search_query': search_query,
        'type_filter': type_filter,
        'actif_filter': actif_filter,
        'total_clients': clients.count(),
        'clients_actifs': clients.filter(actif=True).count()
    }

    return render(request, 'gestion_temps_activite/client_liste.html', context)


@role_required('DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def client_detail(request, pk):
    """Détails d'un client."""
    client = get_object_or_404(ZDCL, pk=pk)

    # Récupérer les projets du client
    projets = client.projets.all().annotate(
        nombre_taches=Count('taches'),
        taches_terminees=Count('taches', filter=Q(taches__statut='TERMINE'))
    )

    # Statistiques
    stats = StatistiqueService.get_stats_client(client)

    context = {
        'client': client,
        'projets': projets,
        'total_projets': stats['total_projets'],
        'projets_actifs': stats['projets_actifs'],
        'projets_termines': stats['projets_termines']
    }

    return render(request, 'gestion_temps_activite/client_detail.html', context)


@role_required('DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def client_create(request):
    """Créer un nouveau client."""
    if request.method == 'POST':
        form = ZDCLForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            if hasattr(request.user, 'employe'):
                client.cree_par = request.user.employe
            client.save()

            return redirect('gestion_temps_activite:client_detail', pk=client.pk)
        else:
            messages.error(request, 'Erreur lors de la création du client. Veuillez vérifier les informations.')
    else:
        form = ZDCLForm()

    context = {
        'form': form,
        'title': 'Nouveau Client',
        'action': 'Créer'
    }

    return render(request, 'gestion_temps_activite/client_form.html', context)


@role_required('DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def client_update(request, pk):
    """Modifier un client."""
    client = get_object_or_404(ZDCL, pk=pk)

    if request.method == 'POST':
        form = ZDCLForm(request.POST, instance=client)
        if form.is_valid():
            form.save()

            return redirect('gestion_temps_activite:client_detail', pk=client.pk)
        else:
            messages.error(request, 'Erreur lors de la modification du client.')
    else:
        form = ZDCLForm(instance=client)

    context = {
        'form': form,
        'client': client,
        'title': 'Modifier Client',
        'action': 'Modifier'
    }

    return render(request, 'gestion_temps_activite/client_form.html', context)


@role_required('DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def client_delete(request, pk):
    """Supprimer un client."""
    client = get_object_or_404(ZDCL, pk=pk)

    if request.method == 'POST':
        try:
            client.delete()
            return redirect('gestion_temps_activite:client_liste')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer le client : {str(e)}')
            return redirect('gestion_temps_activite:client_detail', pk=pk)

    context = {
        'client': client,
        'projets_count': client.projets.count()
    }

    return render(request, 'gestion_temps_activite/client_confirm_delete.html', context)
