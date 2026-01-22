# gestion_temps_activite/views/tache_views.py
"""Vues pour la gestion des tâches (ZDTA)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator

from absence.decorators import role_required
from employee.models import ZY00
from gestion_temps_activite.models import ZDPJ, ZDTA
from gestion_temps_activite.forms import ZDTAForm, ZDCMForm
from gestion_temps_activite.services import StatistiqueService, CommentaireService
from gestion_temps_activite.views.notification_views import (
    notifier_nouvelle_tache,
    notifier_reassignation_tache,
    notifier_modification_tache,
    notifier_changement_statut_tache,
)


@login_required
def tache_liste(request):
    """Liste des tâches."""
    taches = ZDTA.objects.select_related('projet', 'assignee').all().order_by('-date_creation')

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        taches = taches.filter(
            Q(code_tache__icontains=search_query) |
            Q(titre__icontains=search_query) |
            Q(projet__nom_projet__icontains=search_query)
        )

    # Filtrage
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        taches = taches.filter(statut=statut_filter)

    projet_filter = request.GET.get('projet', '')
    if projet_filter:
        taches = taches.filter(projet_id=projet_filter)

    assignee_filter = request.GET.get('assignee', '')
    if assignee_filter:
        taches = taches.filter(assignee_id=assignee_filter)

    # Annotations
    taches = StatistiqueService.annotate_taches_stats(taches)

    # Pagination
    paginator = Paginator(taches, 20)
    page_number = request.GET.get('page')
    taches_page = paginator.get_page(page_number)

    # Listes pour les filtres
    projets = ZDPJ.objects.filter(actif=True).order_by('nom_projet')
    employes = ZY00.objects.filter(etat='actif').order_by('nom', 'prenoms')

    context = {
        'taches': taches_page,
        'projets': projets,
        'employes': employes,
        'search_query': search_query,
        'statut_filter': statut_filter,
        'projet_filter': projet_filter,
        'assignee_filter': assignee_filter
    }

    return render(request, 'gestion_temps_activite/tache_liste.html', context)


@login_required
def tache_detail(request, pk):
    """Détails d'une tâche avec système de commentaires."""
    tache = get_object_or_404(
        ZDTA.objects.select_related('projet', 'assignee', 'tache_parente'),
        pk=pk
    )

    # Imputations, documents, sous-tâches
    imputations = tache.imputations.select_related('employe', 'activite').order_by('-date')
    documents = tache.documents.filter(actif=True).select_related('uploade_par')
    sous_taches = tache.sous_taches.all()

    # Statistiques
    stats = StatistiqueService.get_stats_tache(tache)

    # Système de commentaires
    commentaires = []
    form_commentaire = None
    peut_ajouter_commentaire = False
    peut_voir_commentaires_prives = False
    details_visibilite = []

    if hasattr(request.user, 'employe'):
        employe_connecte = request.user.employe

        peut_voir_commentaires_prives = CommentaireService.peut_voir_commentaires_prives(
            employe_connecte, tache
        )
        peut_ajouter_commentaire = CommentaireService.peut_ajouter_commentaire(
            employe_connecte, tache
        )
        details_visibilite = CommentaireService.get_details_visibilite(
            employe_connecte, tache
        )

        # Récupérer les commentaires filtrés
        commentaires = CommentaireService.get_commentaires_tache(tache, employe_connecte)

        if peut_ajouter_commentaire:
            form_commentaire = ZDCMForm(tache=tache, employe=employe_connecte)

    context = {
        'tache': tache,
        'imputations': imputations,
        'documents': documents,
        'sous_taches': sous_taches,
        'commentaires': commentaires,
        'form_commentaire': form_commentaire,
        'heures_totales': stats['heures_totales'],
        'ecart_estimation': stats['ecart_estimation'],
        'peut_ajouter_commentaire': peut_ajouter_commentaire,
        'peut_voir_commentaires_prives': peut_voir_commentaires_prives,
        'details_visibilite': details_visibilite,
    }

    return render(request, 'gestion_temps_activite/tache_detail.html', context)


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def tache_create(request):
    """Créer une nouvelle tâche avec notification."""
    if request.method == 'POST':
        form = ZDTAForm(request.POST)
        if form.is_valid():
            tache = form.save(commit=False)
            if hasattr(request.user, 'employe'):
                tache.cree_par = request.user.employe
            tache.save()

            # Notification nouvelle tâche
            notifier_nouvelle_tache(tache, request.user.employe)

            messages.success(request, "✅ Tâche créée avec succès")
            return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)
        else:
            messages.error(request, 'Erreur lors de la création de la tâche.')
    else:
        projet_id = request.GET.get('projet')
        initial_data = {}
        if projet_id:
            initial_data['projet'] = projet_id
        form = ZDTAForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'Nouvelle Tâche',
        'action': 'Créer'
    }

    return render(request, 'gestion_temps_activite/tache_form.html', context)


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def tache_update(request, pk):
    """Modifier une tâche avec notifications."""
    tache = get_object_or_404(ZDTA, pk=pk)

    # Sauvegarder les anciennes valeurs
    ancien_assignee = tache.assignee
    ancien_statut = tache.statut

    if request.method == 'POST':
        form = ZDTAForm(request.POST, instance=tache)
        if form.is_valid():
            tache = form.save()

            nouvel_assignee = tache.assignee
            nouveau_statut = tache.statut

            # Notification réassignation
            if ancien_assignee != nouvel_assignee:
                notifier_reassignation_tache(tache, ancien_assignee, nouvel_assignee)

            # Notification modification
            changements = detecter_changements(form, tache, ['titre', 'description', 'priorite', 'date_fin_prevue'])
            if changements:
                notifier_modification_tache(tache, request.user.employe, changements)

            # Notification changement de statut
            if ancien_statut != nouveau_statut:
                notifier_changement_statut_tache(tache, ancien_statut, nouveau_statut)

            messages.success(request, "✅ Tâche modifiée avec succès")
            return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)
        else:
            messages.error(request, 'Erreur lors de la modification.')
    else:
        form = ZDTAForm(instance=tache)

    context = {
        'form': form,
        'tache': tache,
        'title': 'Modifier Tâche',
        'action': 'Modifier'
    }

    return render(request, 'gestion_temps_activite/tache_form.html', context)


def detecter_changements(form, tache, champs_a_surveiller):
    """Détecter les changements dans un formulaire."""
    changements = []
    for champ in champs_a_surveiller:
        if champ in form.changed_data:
            changements.append(form.fields[champ].label or champ)
    return changements


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def tache_delete(request, pk):
    """Supprimer une tâche."""
    tache = get_object_or_404(ZDTA, pk=pk)

    if request.method == 'POST':
        projet_pk = tache.projet.pk
        try:
            tache.delete()
            return redirect('gestion_temps_activite:projet_detail', pk=projet_pk)
        except Exception as e:
            messages.error(request, f'Impossible de supprimer : {str(e)}')
            return redirect('gestion_temps_activite:tache_detail', pk=pk)

    context = {
        'tache': tache,
        'imputations_count': tache.imputations.count(),
        'documents_count': tache.documents.count()
    }

    return render(request, 'gestion_temps_activite/tache_confirm_delete.html', context)
