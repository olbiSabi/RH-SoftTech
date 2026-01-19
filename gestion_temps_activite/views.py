# gestion_temps_activite/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from employee.models import ZY00
from .models import ZDCL, ZDAC, ZDPJ, ZDTA, ZDDO, ZDIT, ZDCM
from .forms import (
    ZDCLForm, ZDACForm, ZDPJForm, ZDTAForm, ZDDOForm,
    ZDITForm, ZDITValidationForm, TimerForm, RechercheImputationForm, ZDCMForm
)
from absence.decorators import drh_or_admin_required, gestion_app_required, manager_or_rh_required, manager_required, \
    role_required
import pandas as pd
from io import BytesIO
from absence.models import NotificationAbsence

# ==================== VUES CLIENTS (ZDCL) ====================
@role_required('DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def client_liste(request):
    """Liste des clients avec recherche et filtrage"""
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

    # Annotations pour statistiques
    clients = clients.annotate(
        nombre_projets=Count('projets'),
        projets_actifs=Count('projets', filter=Q(projets__actif=True))
    )

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
    """Détails d'un client"""
    client = get_object_or_404(ZDCL, pk=pk)

    # Récupérer les projets du client
    projets = client.projets.all().annotate(
        nombre_taches=Count('taches'),
        taches_terminees=Count('taches', filter=Q(taches__statut='TERMINE'))
    )

    # Statistiques
    total_projets = projets.count()
    projets_actifs = projets.filter(actif=True).count()
    projets_termines = projets.filter(statut='TERMINE').count()

    context = {
        'client': client,
        'projets': projets,
        'total_projets': total_projets,
        'projets_actifs': projets_actifs,
        'projets_termines': projets_termines
    }

    return render(request, 'gestion_temps_activite/client_detail.html', context)

@role_required('DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def client_create(request):
    """Créer un nouveau client"""
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
    """Modifier un client"""
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
    """Supprimer un client"""
    client = get_object_or_404(ZDCL, pk=pk)

    if request.method == 'POST':
        raison_sociale = client.raison_sociale
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


# ==================== VUES ACTIVITÉS (ZDAC) ====================
@role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def activite_liste(request):
    """Liste des types d'activités"""
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
    """Créer un nouveau type d'activité"""
    if request.method == 'POST':
        form = ZDACForm(request.POST)
        if form.is_valid():
            activite = form.save()

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
    """Modifier un type d'activité"""
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
    """Supprimer un type d'activité"""
    activite = get_object_or_404(ZDAC, pk=pk)

    if request.method == 'POST':
        libelle = activite.libelle
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


# ==================== VUES PROJETS (ZDPJ) ====================
@login_required
def projet_liste(request):
    """Liste des projets"""
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
    projets = projets.annotate(
        nombre_taches=Count('taches'),
        taches_terminees=Count('taches', filter=Q(taches__statut='TERMINE')),
        heures_consommees=Coalesce(
            Sum('taches__imputations__duree'),
            0,
            output_field=DecimalField()
        )
    )

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
    """Détails d'un projet"""
    projet = get_object_or_404(
        ZDPJ.objects.select_related('client', 'chef_projet'),
        pk=pk
    )

    # Récupérer les tâches
    taches = projet.taches.select_related('assignee').annotate(
        heures_realisees=Coalesce(
            Sum('imputations__duree'),
            0,
            output_field=DecimalField()
        )
    )

    # Documents du projet
    documents = projet.documents.filter(actif=True).select_related('uploade_par')

    # Statistiques
    total_taches = taches.count()
    taches_terminees = taches.filter(statut='TERMINE').count()
    heures_totales = taches.aggregate(total=Sum('imputations__duree'))['total'] or 0

    # Calcul du budget restant
    budget_restant = None
    pourcentage_budget = None
    if projet.budget_heures:
        budget_restant = float(projet.budget_heures) - float(heures_totales)
        pourcentage_budget = (float(heures_totales) / float(projet.budget_heures)) * 100

    context = {
        'projet': projet,
        'taches': taches,
        'documents': documents,
        'total_taches': total_taches,
        'taches_terminees': taches_terminees,
        'heures_totales': heures_totales,
        'budget_restant': budget_restant,
        'pourcentage_budget': pourcentage_budget,
        'avancement': projet.get_avancement_pourcentage()
    }

    return render(request, 'gestion_temps_activite/projet_detail.html', context)

@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def projet_create(request):
    """Créer un nouveau projet"""
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
    """Modifier un projet"""
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
    """Supprimer un projet"""
    projet = get_object_or_404(ZDPJ, pk=pk)

    if request.method == 'POST':
        nom_projet = projet.nom_projet
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


# ==================== VUES TÂCHES (ZDTA) ====================

@login_required
def tache_liste(request):
    """Liste des tâches"""
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
    taches = taches.annotate(
        heures_realisees=Coalesce(
            Sum('imputations__duree'),
            0,
            output_field=DecimalField()
        )
    )

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
    """Détails d'une tâche - Version avec visibilité par équipe"""
    tache = get_object_or_404(
        ZDTA.objects.select_related('projet', 'assignee', 'tache_parente'),
        pk=pk
    )

    # Imputations, documents, sous-tâches
    imputations = tache.imputations.select_related('employe', 'activite').order_by('-date')
    documents = tache.documents.filter(actif=True).select_related('uploade_par')
    sous_taches = tache.sous_taches.all()

    # Statistiques
    heures_totales = imputations.aggregate(total=Sum('duree'))['total'] or 0
    ecart_estimation = tache.get_ecart_estimation()

    # ============================================
    # SYSTÈME DE COMMENTAIRES - VERSION ÉQUIPE
    # ============================================

    commentaires = []
    form_commentaire = None
    peut_ajouter_commentaire = False
    peut_voir_commentaires_prives = False
    details_visibilite = []

    if hasattr(request.user, 'employe'):
        employe_connecte = request.user.employe

        # A. Peut voir les commentaires privés ?
        peut_voir_commentaires_prives = any([
            tache.assignee == employe_connecte,
            tache.projet.chef_projet == employe_connecte,
            employe_connecte.has_role('DRH'),
            employe_connecte.has_role('GESTION_APP'),
            employe_connecte.est_manager_departement(),
        ])

        # B. Peut ajouter des commentaires ?
        peut_ajouter_commentaire = any([
            tache.assignee == employe_connecte,
            tache.projet.chef_projet == employe_connecte,
            employe_connecte.has_role('DRH'),
            employe_connecte.has_role('GESTION_APP'),
            (tache.assignee and
             employe_connecte.get_departement_actuel() == tache.assignee.get_departement_actuel()),
            (tache.assignee and
             employe_connecte.est_manager_de(tache.assignee)),
        ])

        # C. Détails de visibilité
        details_visibilite = []
        if tache.assignee == employe_connecte:
            details_visibilite.append("Vous êtes assigné à cette tâche")
        if tache.projet.chef_projet == employe_connecte:
            details_visibilite.append("Vous êtes chef de projet")
        if employe_connecte.est_manager_departement():
            details_visibilite.append("Vous êtes manager de département")
        if employe_connecte.has_role('DRH') or employe_connecte.has_role('GESTION_APP'):
            details_visibilite.append("Vous avez un rôle RH/Admin")
        if tache.assignee and employe_connecte.get_departement_actuel() == tache.assignee.get_departement_actuel():
            details_visibilite.append(
                f"Vous êtes dans la même équipe ({employe_connecte.get_departement_actuel().LIBELLE})")

        # RÉCUPÉRER ET FILTRER LES COMMENTAIRES
        commentaires_query = tache.commentaires.filter(
            reponse_a__isnull=True
        ).select_related(
            'employe',
            'tache__assignee',
            'tache__projet__chef_projet'
        ).prefetch_related(
            'reponses__employe',
            'mentions'
        ).order_by('-date_creation')

        commentaires_visibles = []

        for commentaire in commentaires_query:
            peut_voir = commentaire.peut_voir(employe_connecte)

            if peut_voir:
                # ✅ CORRECTION : Boucle for au lieu de list comprehension
                reponses_visibles = []
                for reponse in commentaire.reponses.all():
                    if reponse.peut_voir(employe_connecte):
                        # Calculer les permissions pour chaque réponse
                        reponse.peut_modifier_par = reponse.peut_modifier(employe_connecte)
                        reponse.peut_supprimer_par = reponse.peut_supprimer(employe_connecte)
                        reponses_visibles.append(reponse)

                commentaire.reponses_visibles = reponses_visibles
                commentaire.peut_modifier_par = commentaire.peut_modifier(employe_connecte)
                commentaire.peut_supprimer_par = commentaire.peut_supprimer(employe_connecte)

                commentaires_visibles.append(commentaire)

        commentaires = commentaires_visibles

        if peut_ajouter_commentaire:
            form_commentaire = ZDCMForm(tache=tache, employe=employe_connecte)

    context = {
        'tache': tache,
        'imputations': imputations,
        'documents': documents,
        'sous_taches': sous_taches,
        'commentaires': commentaires,
        'form_commentaire': form_commentaire,
        'heures_totales': heures_totales,
        'ecart_estimation': ecart_estimation,
        'peut_ajouter_commentaire': peut_ajouter_commentaire,
        'peut_voir_commentaires_prives': peut_voir_commentaires_prives,
        'details_visibilite': details_visibilite,
    }

    return render(request, 'gestion_temps_activite/tache_detail.html', context)


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def tache_create(request):
    """Créer une nouvelle tâche avec notification"""
    if request.method == 'POST':
        form = ZDTAForm(request.POST)
        if form.is_valid():
            tache = form.save(commit=False)
            if hasattr(request.user, 'employe'):
                tache.cree_par = request.user.employe
            tache.save()

            # ✅ NOTIFICATION NOUVELLE TÂCHE
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
    """Modifier une tâche avec notifications"""
    tache = get_object_or_404(ZDTA, pk=pk)

    # ✅ SAUVEGARDER les anciennes valeurs AVANT modification
    ancien_assignee = tache.assignee
    ancien_statut = tache.statut

    if request.method == 'POST':
        form = ZDTAForm(request.POST, instance=tache)
        if form.is_valid():
            tache = form.save()

            nouvel_assignee = tache.assignee
            nouveau_statut = tache.statut

            # ✅ NOTIFICATION RÉASSIGNATION
            if ancien_assignee != nouvel_assignee:
                notifier_reassignation_tache(tache, ancien_assignee, nouvel_assignee)

            # ✅ NOTIFICATION MODIFICATION
            changements = detecter_changements(form, tache, ['titre', 'description', 'priorite', 'date_fin_prevue'])
            if changements:
                notifier_modification_tache(tache, request.user.employe, changements)

            # ✅ NOTIFICATION CHANGEMENT DE STATUT
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
    """Détecter les changements dans un formulaire"""
    changements = []
    for champ in champs_a_surveiller:
        if champ in form.changed_data:
            changements.append(form.fields[champ].label or champ)
    return changements


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def tache_delete(request, pk):
    """Supprimer une tâche"""
    tache = get_object_or_404(ZDTA, pk=pk)

    if request.method == 'POST':
        titre = tache.titre
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


# ==================== VUES DOCUMENTS (ZDDO) ====================

@login_required
def document_upload(request):
    """Upload de document"""
    if request.method == 'POST':
        form = ZDDOForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            if hasattr(request.user, 'employe'):
                document.uploade_par = request.user.employe
            document.save()

            if document.type_rattachement == 'PROJET':
                return redirect('gestion_temps_activite:projet_detail', pk=document.projet.pk)
            else:
                return redirect('gestion_temps_activite:tache_detail', pk=document.tache.pk)
        else:
            messages.error(request, 'Erreur lors de l\'upload du document.')
    else:
        type_rattachement = request.GET.get('type', 'PROJET')
        projet_id = request.GET.get('projet')
        tache_id = request.GET.get('tache')

        initial_data = {'type_rattachement': type_rattachement}
        if projet_id:
            initial_data['projet'] = projet_id
        if tache_id:
            initial_data['tache'] = tache_id
            initial_data['type_rattachement'] = 'TACHE'

        form = ZDDOForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'Upload Document'
    }

    return render(request, 'gestion_temps_activite/document_form.html', context)


@login_required
def document_delete(request, pk):
    """Supprimer un document"""
    document = get_object_or_404(ZDDO, pk=pk)

    if request.method == 'POST':
        nom = document.nom_document
        type_rattachement = document.type_rattachement
        objet_pk = document.projet.pk if type_rattachement == 'PROJET' else document.tache.pk

        try:
            if document.fichier:
                document.fichier.delete()
            document.delete()

            if type_rattachement == 'PROJET':
                return redirect('gestion_temps_activite:projet_detail', pk=objet_pk)
            else:
                return redirect('gestion_temps_activite:tache_detail', pk=objet_pk)
        except Exception as e:
            messages.error(request, f'Impossible de supprimer : {str(e)}')

    context = {
        'document': document
    }

    return render(request, 'gestion_temps_activite/document_confirm_delete.html', context)


# ==================== VUES IMPUTATIONS TEMPS (ZDIT) ====================
@role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def imputation_liste(request):
    """Liste des imputations avec recherche et filtrage"""
    imputations = ZDIT.objects.select_related(
        'employe', 'tache__projet', 'activite'
    ).all().order_by('-date', '-date_creation')

    form = RechercheImputationForm(request.GET or None)

    if form.is_valid():
        if form.cleaned_data.get('employe'):
            imputations = imputations.filter(employe=form.cleaned_data['employe'])

        if form.cleaned_data.get('projet'):
            imputations = imputations.filter(tache__projet=form.cleaned_data['projet'])

        if form.cleaned_data.get('tache'):
            imputations = imputations.filter(tache=form.cleaned_data['tache'])

        if form.cleaned_data.get('activite'):
            imputations = imputations.filter(activite=form.cleaned_data['activite'])

        if form.cleaned_data.get('date_debut'):
            imputations = imputations.filter(date__gte=form.cleaned_data['date_debut'])

        if form.cleaned_data.get('date_fin'):
            imputations = imputations.filter(date__lte=form.cleaned_data['date_fin'])

        if form.cleaned_data.get('valide'):
            imputations = imputations.filter(valide=(form.cleaned_data['valide'] == 'True'))

        if form.cleaned_data.get('facture'):
            imputations = imputations.filter(facture=(form.cleaned_data['facture'] == 'True'))

    # Statistiques
    total_heures = imputations.aggregate(total=Sum('duree'))['total'] or 0
    heures_validees = imputations.filter(valide=True).aggregate(total=Sum('duree'))['total'] or 0
    heures_facturables = imputations.filter(facturable=True, valide=True).aggregate(total=Sum('duree'))['total'] or 0

    # Pagination
    paginator = Paginator(imputations, 25)
    page_number = request.GET.get('page')
    imputations_page = paginator.get_page(page_number)

    employes = ZY00.objects.filter(etat='actif').order_by('nom', 'prenoms')
    projets = ZDPJ.objects.filter(actif=True).order_by('nom_projet')
    taches = ZDTA.objects.filter(statut__in=['A_FAIRE', 'EN_COURS', 'EN_ATTENTE']).select_related('projet').order_by('code_tache')
    activites = ZDAC.objects.filter(actif=True).order_by('libelle')

    context = {
        'imputations': imputations_page,
        'form': form,
        'total_heures': total_heures,
        'heures_validees': heures_validees,
        'heures_facturables': heures_facturables,
        'total_imputations': imputations.count(),
        'employes': employes,
        'projets': projets,
        'taches': taches,
        'activites': activites,
    }

    return render(request, 'gestion_temps_activite/imputation_liste.html', context)


@login_required
def imputation_mes_temps(request):
    """Mes imputations de temps (employé connecté)"""
    if not hasattr(request.user, 'employe'):
        messages.error(request, 'Vous devez être associé à un employé.')
        return redirect('gestion_temps_activite:dashboard')

    employe = request.user.employe

    periode = request.GET.get('periode', 'mois')
    date_actuelle = timezone.now().date()

    # Gestion période personnalisée
    if periode == 'personnalisee':
        date_debut_str = request.GET.get('date_debut')
        date_fin_str = request.GET.get('date_fin')
        if date_debut_str and date_fin_str:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
        else:
            # Par défaut, utiliser le mois en cours
            date_debut = date_actuelle.replace(day=1)
            if date_actuelle.month == 12:
                date_fin = date_actuelle.replace(day=31)
            else:
                date_fin = (date_actuelle.replace(month=date_actuelle.month + 1, day=1) - timedelta(days=1))
    elif periode == 'semaine':
        date_debut = date_actuelle - timedelta(days=date_actuelle.weekday())
        date_fin = date_debut + timedelta(days=6)
    elif periode == 'mois':
        date_debut = date_actuelle.replace(day=1)
        if date_actuelle.month == 12:
            date_fin = date_actuelle.replace(day=31)
        else:
            date_fin = (date_actuelle.replace(month=date_actuelle.month + 1, day=1) - timedelta(days=1))
    elif periode == 'annee':
        date_debut = date_actuelle.replace(month=1, day=1)
        date_fin = date_actuelle.replace(month=12, day=31)
    else:
        # Par défaut : mois
        date_debut = date_actuelle.replace(day=1)
        if date_actuelle.month == 12:
            date_fin = date_actuelle.replace(day=31)
        else:
            date_fin = (date_actuelle.replace(month=date_actuelle.month + 1, day=1) - timedelta(days=1))

    imputations = ZDIT.objects.filter(
        employe=employe,
        date__gte=date_debut,
        date__lte=date_fin
    ).select_related('tache__projet', 'activite').order_by('-date')

    # ✅ STATISTIQUES CORRIGÉES
    total_heures = imputations.aggregate(total=Sum('duree'))['total'] or 0
    heures_validees = imputations.filter(valide=True).aggregate(total=Sum('duree'))['total'] or 0
    heures_attente = total_heures - heures_validees

    # ✅ AJOUT : Calcul de la moyenne par jour
    jours_travailles = imputations.values('date').distinct().count()
    moyenne_jour = (total_heures / jours_travailles) if jours_travailles > 0 else 0

    par_projet = imputations.values(
        'tache__projet__nom_projet'
    ).annotate(
        total_heures=Sum('duree')
    ).order_by('-total_heures')

    context = {
        'imputations': imputations,
        'periode': periode,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'total_heures': total_heures,
        'heures_validees': heures_validees,
        'heures_attente': heures_attente,
        'moyenne_jour': moyenne_jour,
        'par_projet': par_projet
    }

    return render(request, 'gestion_temps_activite/imputation_mes_temps.html', context)


@login_required
def imputation_create(request):
    """Créer une nouvelle imputation"""
    if not hasattr(request.user, 'employe'):
        messages.error(request, 'Vous devez être associé à un employé.')
        return redirect('gestion_temps_activite:dashboard')

    if request.method == 'POST':
        form = ZDITForm(request.POST, user=request.user)
        if form.is_valid():
            imputation = form.save()
            # Messages supprimés comme demandé
            return redirect('gestion_temps_activite:imputation_mes_temps')
        else:
            messages.error(request, 'Erreur lors de l\'enregistrement.')
    else:
        form = ZDITForm(user=request.user)

    # ✅ AJOUTER : Récupérer tous les projets actifs
    projets = ZDPJ.objects.filter(actif=True).order_by('nom_projet')

    context = {
        'form': form,
        'title': 'Nouvelle Imputation',
        'action': 'Créer',
        'projets': projets,  # ✅ AJOUTER cette ligne
    }

    return render(request, 'gestion_temps_activite/imputation_form.html', context)


@login_required
def imputation_update(request, pk):
    """Modifier une imputation"""
    imputation = get_object_or_404(ZDIT, pk=pk)

    # Vérifier les permissions
    if hasattr(request.user, 'employe'):
        if imputation.employe != request.user.employe and not request.user.is_staff:
            messages.error(request, 'Vous ne pouvez pas modifier cette imputation.')
            return redirect('gestion_temps_activite:imputation_mes_temps')

    # Empêcher la modification si validé ou facturé
    if imputation.valide:
        messages.warning(request, 'Cette imputation est déjà validée et ne peut plus être modifiée.')
        return redirect('gestion_temps_activite:imputation_mes_temps')

    if imputation.facture:
        messages.error(request, 'Cette imputation est déjà facturée et ne peut plus être modifiée.')
        return redirect('gestion_temps_activite:imputation_mes_temps')

    if request.method == 'POST':
        form = ZDITForm(request.POST, instance=imputation, user=request.user)
        if form.is_valid():
            form.save()
            # Messages supprimés
            return redirect('gestion_temps_activite:imputation_mes_temps')
        else:
            messages.error(request, 'Erreur lors de la modification.')
    else:
        form = ZDITForm(instance=imputation, user=request.user)

    # ✅ AJOUTER : Récupérer tous les projets actifs
    projets = ZDPJ.objects.filter(actif=True).order_by('nom_projet')

    context = {
        'form': form,
        'imputation': imputation,
        'title': 'Modifier Imputation',
        'action': 'Modifier',
        'projets': projets,  # ✅ AJOUTER cette ligne
    }

    return render(request, 'gestion_temps_activite/imputation_form.html', context)


@login_required
def imputation_delete(request, pk):
    """Supprimer une imputation"""
    imputation = get_object_or_404(ZDIT, pk=pk)

    if hasattr(request.user, 'employe'):
        if imputation.employe != request.user.employe and not request.user.is_staff:
            messages.error(request, 'Vous ne pouvez pas supprimer cette imputation.')
            return redirect('gestion_temps_activite:imputation_mes_temps')

    if imputation.valide or imputation.facture:
        messages.error(request, 'Cette imputation ne peut pas être supprimée (validée ou facturée).')
        return redirect('gestion_temps_activite:imputation_mes_temps')

    if request.method == 'POST':
        try:
            imputation.delete()

            return redirect('gestion_temps_activite:imputation_mes_temps')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer : {str(e)}')

    context = {
        'imputation': imputation
    }

    return render(request, 'gestion_temps_activite/imputation_confirm_delete.html', context)


@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def imputation_validation(request):
    """Validation des imputations (pour managers et RH)"""
    imputations = ZDIT.objects.filter(
        valide=False
    ).select_related('employe', 'tache__projet', 'activite').order_by('-date')

    employe_filter = request.GET.get('employe')
    if employe_filter:
        imputations = imputations.filter(employe_id=employe_filter)

    paginator = Paginator(imputations, 30)
    page_number = request.GET.get('page')
    imputations_page = paginator.get_page(page_number)

    employes = ZY00.objects.filter(etat='actif').order_by('nom', 'prenoms')

    context = {
        'imputations': imputations_page,
        'employes': employes,
        'employe_filter': employe_filter,
        'total_a_valider': imputations.count()
    }

    return render(request, 'gestion_temps_activite/imputation_validation.html', context)

@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def imputation_valider(request, pk):
    imputation = get_object_or_404(ZDIT, pk=pk)

    if request.method == 'POST':
        if not imputation.valide:
            imputation.valide = True
            if hasattr(request.user, 'employe'):
                imputation.valide_par = request.user.employe
            imputation.date_validation = timezone.now()
            imputation.save()

        else:
            messages.info(request, 'Cette imputation est déjà validée.')

        return redirect('gestion_temps_activite:imputation_validation')

    context = {
        'imputation': imputation
    }

    return render(request, 'gestion_temps_activite/imputation_valider.html', context)


@login_required
def imputation_rejeter(request, pk):
    """Rejeter une imputation"""
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé.')
        return redirect('gestion_temps_activite:dashboard')

    imputation = get_object_or_404(ZDIT, pk=pk)

    if request.method == 'POST':
        commentaire = request.POST.get('commentaire_rejet', '')
        if commentaire:
            imputation.valide = False
            imputation.commentaire = f"[REJETÉ] {commentaire}\n{imputation.commentaire or ''}"
            imputation.save()

        else:
            messages.error(request, 'Veuillez indiquer un motif de rejet.')

        return redirect('gestion_temps_activite:imputation_validation')

    context = {
        'imputation': imputation
    }

    return render(request, 'gestion_temps_activite/imputation_rejeter.html', context)

@role_required('MANAGER', 'DRH', 'GESTION_APP', 'DIRECTEUR')
@login_required
def imputation_export_excel(request):
    """Export des imputations en format Excel avec pandas"""
    imputations = ZDIT.objects.select_related(
        'employe', 'tache__projet', 'activite', 'valide_par'
    ).all().order_by('-date', '-date_creation')

    form = RechercheImputationForm(request.GET or None)

    if form.is_valid():
        pass

    data = []
    for imputation in imputations:
        montant = 0
        if imputation.duree and imputation.taux_horaire_applique and imputation.facturable:
            montant = float(imputation.duree) * float(imputation.taux_horaire_applique)

        data.append({
            'Date': imputation.date,
            'Employé': f"{imputation.employe.nom} {imputation.employe.prenoms}",
            'Matricule': imputation.employe.matricule or '',
            'Projet': imputation.tache.projet.nom_projet if imputation.tache.projet else '',
            'Code Projet': imputation.tache.projet.code_projet if imputation.tache.projet else '',
            'Tâche': imputation.tache.titre,
            'Code Tâche': imputation.tache.code_tache,
            'Activité': imputation.activite.libelle if imputation.activite else '',
            'Durée (h)': float(imputation.duree) if imputation.duree else 0,
            'Taux Horaire (FCFA)': float(
                imputation.taux_horaire_applique) if imputation.taux_horaire_applique else 0,
            'Montant (FCFA)': montant,
            'Commentaire': imputation.commentaire or '',
            'Validé': 'Oui' if imputation.valide else 'Non',
            'Validé par': f"{imputation.valide_par.nom} {imputation.valide_par.prenoms}" if imputation.valide_par else '',
            'Date Validation': imputation.date_validation,
            'Facturable': 'Oui' if imputation.facturable else 'Non',
            'Facturé': 'Oui' if imputation.facture else 'Non',
            'Date Création': imputation.date_creation,
        })

    df = pd.DataFrame(data)

    datetime_columns = df.select_dtypes(include=['datetime64[ns, UTC]', 'datetime64']).columns
    for col in datetime_columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Imputations', index=False)

        worksheet = writer.sheets['Imputations']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response[
        'Content-Disposition'] = f'attachment; filename="imputations_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

    return response


# ==================== VUE DASHBOARD ====================
@role_required('MANAGER', 'GESTION_APP', 'DIRECTEUR')
@login_required
def dashboard(request):
    """Tableau de bord principal"""
    total_clients = ZDCL.objects.filter(actif=True).count()
    total_projets = ZDPJ.objects.filter(actif=True).count()
    projets_en_cours = ZDPJ.objects.filter(statut='EN_COURS').count()
    total_taches = ZDTA.objects.exclude(statut='TERMINE').count()

    projets_recents = ZDPJ.objects.select_related('client').filter(
        actif=True
    ).order_by('-date_creation')[:5]

    taches_urgentes = ZDTA.objects.select_related('projet', 'assignee').filter(
        priorite__in=['HAUTE', 'CRITIQUE']
    ).exclude(statut='TERMINE').order_by('date_fin_prevue')[:10]

    if hasattr(request.user, 'employe'):
        employe = request.user.employe

        mes_taches = ZDTA.objects.filter(
            assignee=employe
        ).exclude(statut='TERMINE').count()

        date_actuelle = timezone.now().date()
        debut_mois = date_actuelle.replace(day=1)
        mes_heures_mois = ZDIT.objects.filter(
            employe=employe,
            date__gte=debut_mois
        ).aggregate(total=Sum('duree'))['total'] or 0

        mes_imputations_attente = ZDIT.objects.filter(
            employe=employe,
            valide=False
        ).count()
    else:
        mes_taches = 0
        mes_heures_mois = 0
        mes_imputations_attente = 0

    context = {
        'total_clients': total_clients,
        'total_projets': total_projets,
        'projets_en_cours': projets_en_cours,
        'total_taches': total_taches,
        'projets_recents': projets_recents,
        'taches_urgentes': taches_urgentes,
        'mes_taches': mes_taches,
        'mes_heures_mois': mes_heures_mois,
        'mes_imputations_attente': mes_imputations_attente
    }

    return render(request, 'gestion_temps_activite/dashboard.html', context)


# ==================== VUES API/AJAX ====================

@login_required
def api_taches_par_projet(request, projet_id):
    """API: Récupérer les tâches d'un projet (pour AJAX)"""
    taches = ZDTA.objects.filter(projet_id=projet_id).values('id', 'code_tache', 'titre')
    return JsonResponse(list(taches), safe=False)


@login_required
def api_activites_en_vigueur(request):
    """API: Récupérer les activités en vigueur (pour AJAX)"""
    date_actuelle = timezone.now().date()
    activites = ZDAC.objects.filter(
        actif=True,
        date_debut__lte=date_actuelle
    ).filter(
        Q(date_fin__isnull=True) | Q(date_fin__gte=date_actuelle)
    ).values('id', 'code_activite', 'libelle', 'taux_horaire_defaut')

    return JsonResponse(list(activites), safe=False)


@login_required
def commentaire_ajouter(request, tache_pk):
    """Ajouter un commentaire avec notifications optimisées"""
    tache = get_object_or_404(ZDTA, pk=tache_pk)

    if not hasattr(request.user, 'employe'):
        messages.error(request, 'Vous devez être un employé pour commenter.')
        return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)

    if request.method == 'POST':
        form = ZDCMForm(request.POST, tache=tache, employe=request.user.employe)

        if form.is_valid():
            try:
                commentaire = form.save(commit=False)
                commentaire.tache = tache
                commentaire.employe = request.user.employe
                commentaire.prive = False
                commentaire.save()
                form.save_m2m()  # Pour sauvegarder les mentions

                # ✅ NOTIFICATIONS OPTIMISÉES
                destinataires = commentaire.get_destinataires_notification()

                print(f"\n[DEBUG commentaire_ajouter] 📧 Envoi notifications")
                print(f"[DEBUG] Auteur: {request.user.employe}")
                print(f"[DEBUG] Destinataires ({len(destinataires)}): {[str(d) for d in destinataires]}")

                for destinataire in destinataires:
                    # Déterminer le message personnalisé
                    if destinataire == tache.assignee:
                        message = f"💬 Nouveau commentaire sur votre tâche '{tache.titre}'"
                    elif destinataire in commentaire.mentions.all():
                        message = f"💬 Vous avez été mentionné dans un commentaire sur la tâche '{tache.titre}'"
                    elif destinataire == tache.projet.chef_projet:
                        message = f"💬 Nouveau commentaire sur la tâche '{tache.titre}' de votre projet"
                    else:
                        # Manager ou membre d'équipe
                        message = f"💬 Nouveau commentaire sur la tâche '{tache.titre}'"

                    NotificationAbsence.creer_notification(
                        destinataire=destinataire,
                        type_notif='COMMENTAIRE_TACHE',
                        message=message,
                        contexte='GTA',
                        tache=tache
                    )
                    print(f"[DEBUG] ✅ Notification envoyée à {destinataire}")

                messages.success(request, '✅ Commentaire ajouté avec succès')
                return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)

            except Exception as e:
                messages.error(request, f'❌ Erreur : {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)


@login_required
def commentaire_repondre(request, commentaire_pk):
    """Répondre à un commentaire avec notifications optimisées"""
    commentaire_parent = get_object_or_404(ZDCM, pk=commentaire_pk)
    tache = commentaire_parent.tache

    if not hasattr(request.user, 'employe'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
        messages.error(request, 'Vous devez être un employé.')
        return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)

    if request.method == 'POST':
        # Requête AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                contenu = request.POST.get('contenu', '').strip()

                if not contenu or len(contenu) < 2:
                    return JsonResponse({
                        'success': False,
                        'error': 'La réponse doit contenir au moins 2 caractères.'
                    })

                if len(contenu) > 1000:
                    return JsonResponse({
                        'success': False,
                        'error': 'La réponse ne peut pas dépasser 1000 caractères.'
                    })

                reponse = ZDCM.objects.create(
                    tache=tache,
                    employe=request.user.employe,
                    contenu=contenu,
                    reponse_a=commentaire_parent,
                    prive=commentaire_parent.prive  # Hérite de la visibilité
                )

                # ✅ NOTIFICATIONS OPTIMISÉES POUR RÉPONSES
                destinataires = set()

                # 1. L'auteur du commentaire parent (prioritaire)
                if commentaire_parent.employe and commentaire_parent.employe != request.user.employe:
                    destinataires.add(commentaire_parent.employe)

                # 2. L'assigné de la tâche
                if tache.assignee and tache.assignee != request.user.employe:
                    destinataires.add(tache.assignee)

                # 3. Le chef de projet
                if tache.projet.chef_projet and tache.projet.chef_projet != request.user.employe:
                    destinataires.add(tache.projet.chef_projet)

                # 4. Extraire les mentions de la réponse
                import re
                mentions_trouvees = re.findall(r'@([A-Za-zÀ-ÖØ-öø-ÿ\s]+)', contenu)
                if mentions_trouvees:
                    for mention in mentions_trouvees:
                        employes = ZY00.objects.filter(
                            Q(nom__icontains=mention) | Q(prenoms__icontains=mention),
                            etat='actif'
                        ).exclude(pk=request.user.employe.pk)

                        for employe in employes:
                            destinataires.add(employe)

                # 5. Le manager du département de l'assigné
                if tache.assignee:
                    try:
                        from departement.models import ZYMA
                        manager_dept = ZYMA.objects.filter(
                            departement=tache.assignee.get_departement_actuel(),
                            actif=True,
                            date_fin__isnull=True
                        ).first()

                        if manager_dept and manager_dept.employe != request.user.employe:
                            destinataires.add(manager_dept.employe)
                    except:
                        pass

                # 6. Les membres de l'équipe (avec vérification visibilité)
                if tache.assignee:
                    try:
                        from employee.models import ZYAF
                        dept_assignee = tache.assignee.get_departement_actuel()

                        if dept_assignee:
                            membres_equipe = ZYAF.objects.filter(
                                poste__DEPARTEMENT=dept_assignee,
                                date_fin__isnull=True,
                                employe__etat='actif'
                            ).values_list('employe', flat=True).distinct()

                            for employe_id in membres_equipe:
                                employe = ZY00.objects.filter(pk=employe_id).first()
                                if employe and employe != request.user.employe:
                                    if reponse.peut_voir(employe):
                                        destinataires.add(employe)
                    except:
                        pass

                # Envoyer les notifications
                print(f"\n[DEBUG commentaire_repondre] 📧 Envoi notifications")
                print(f"[DEBUG] Auteur: {request.user.employe}")
                print(f"[DEBUG] Destinataires ({len(destinataires)}): {[str(d) for d in destinataires]}")

                for destinataire in destinataires:
                    # Message personnalisé
                    if destinataire == commentaire_parent.employe:
                        message = f"💬 Quelqu'un a répondu à votre commentaire sur la tâche '{tache.titre}'"
                    elif destinataire in [emp for mention in mentions_trouvees
                                          for emp in ZY00.objects.filter(
                            Q(nom__icontains=mention) | Q(prenoms__icontains=mention),
                            etat='actif')]:
                        message = f"💬 Vous avez été mentionné dans une réponse sur la tâche '{tache.titre}'"
                    else:
                        message = f"💬 Nouvelle réponse sur la tâche '{tache.titre}'"

                    NotificationAbsence.creer_notification(
                        destinataire=destinataire,
                        type_notif='COMMENTAIRE_TACHE',
                        message=message,
                        contexte='GTA',
                        tache=tache
                    )
                    print(f"[DEBUG] ✅ Notification envoyée à {destinataire}")

                return JsonResponse({
                    'success': True,
                    'message': 'Réponse ajoutée avec succès.',
                    'reponse_id': str(reponse.id)
                })

            except Exception as e:
                print(f"[DEBUG] ❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })

    return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)


@login_required
def commentaire_modifier(request, pk):
    """Modifier un commentaire - Version AJAX"""
    commentaire = get_object_or_404(ZDCM, pk=pk)

    if not hasattr(request.user, 'employe'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
        messages.error(request, 'Vous devez être un employé.')
        return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)

    employe = request.user.employe

    if not commentaire.peut_modifier(employe):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
        messages.error(request, '❌ Vous n\'avez pas la permission de modifier ce commentaire.')
        return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)

    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                contenu = request.POST.get('contenu', '').strip()

                if not contenu or len(contenu) < 2:
                    return JsonResponse({
                        'success': False,
                        'error': 'Le commentaire doit contenir au moins 2 caractères.'
                    })

                if len(contenu) > 1000:
                    return JsonResponse({
                        'success': False,
                        'error': 'Le commentaire ne peut pas dépasser 1000 caractères.'
                    })

                commentaire.contenu = contenu
                commentaire.edite = True
                commentaire.date_edition = timezone.now()
                commentaire.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Commentaire modifié avec succès.'
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })

        else:
            form = ZDCMForm(request.POST, instance=commentaire, tache=commentaire.tache, employe=employe)

            if form.is_valid():
                try:
                    commentaire = form.save(commit=False)
                    commentaire.edite = True
                    commentaire.date_edition = timezone.now()
                    commentaire.save()
                    form.save_m2m()

                    return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)

                except Exception as e:
                    messages.error(request, f'❌ Erreur : {str(e)}')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')

    return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)


@login_required
def commentaire_supprimer(request, pk):
    """Supprimer un commentaire - Version AJAX"""
    commentaire = get_object_or_404(ZDCM, pk=pk)

    if not hasattr(request.user, 'employe'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
        messages.error(request, 'Vous devez être un employé.')
        return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)

    employe = request.user.employe

    if not commentaire.peut_supprimer(employe):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
        messages.error(request, '❌ Vous n\'avez pas la permission de supprimer ce commentaire.')
        return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)

    tache_pk = commentaire.tache.pk

    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                commentaire.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Commentaire supprimé avec succès.'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })

        else:
            try:
                commentaire.delete()
            except Exception as e:
                messages.error(request, f'❌ Erreur lors de la suppression : {str(e)}')

            return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)

    return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)


@login_required
def commentaire_mentions(request):
    """Récupérer les mentions (pour autocomplete)"""
    if not hasattr(request.user, 'employe'):
        return JsonResponse([], safe=False)

    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    employes = ZY00.objects.filter(
        Q(nom__icontains=query) | Q(prenoms__icontains=query),
        etat='actif'
    ).exclude(pk=request.user.employe.pk)[:10]

    result = [
        {
            'id': emp.pk,
            'text': f"{emp.nom} {emp.prenoms}",
            #'matricule': emp.matricule
        }
        for emp in employes
    ]

    return JsonResponse(result, safe=False)


# ==================== VUES NOTIFICATIONS GTA ====================
def notifier_changement_statut(tache, ancien_statut, nouveau_statut, request):
    """Notifier l'assigné du changement de statut"""
    if not tache.assignee:
        return

    # Ne notifier que pour certains changements importants
    notifications_importantes = {
        ('A_FAIRE', 'EN_COURS'): "🚀 Votre tâche '{titre}' est maintenant en cours",
        ('EN_COURS', 'TERMINE'): "✅ La tâche '{titre}' a été marquée comme terminée",
        ('EN_COURS', 'EN_ATTENTE'): "⏸️ La tâche '{titre}' est en attente",
        ('EN_ATTENTE', 'EN_COURS'): "▶️ La tâche '{titre}' a repris",
    }

    cle = (ancien_statut, nouveau_statut)
    if cle in notifications_importantes:
        message = notifications_importantes[cle].format(titre=tache.titre)

        NotificationAbsence.creer_notification(
            destinataire=tache.assignee,
            type_notif='STATUT_TACHE_CHANGE',
            message=message,
            contexte='GTA',
            tache=tache
        )


@login_required
def notification_tache_detail(request, notification_id):
    """Détail d'une notification de tâche GTA"""
    notification = get_object_or_404(
        NotificationAbsence.objects.select_related('tache', 'tache__projet'),
        pk=notification_id,
        destinataire=request.user.employe if hasattr(request.user, 'employe') else None
    )

    # Marquer comme lue
    if not notification.lue:
        notification.marquer_comme_lue()

    # Rediriger vers la tâche concernée
    if notification.tache:
        return redirect('gestion_temps_activite:tache_detail', pk=notification.tache.pk)

    # Fallback vers le dashboard
    messages.info(request, "Notification traitée")
    return redirect('gestion_temps_activite:dashboard')


@login_required
def toutes_notifications_gta(request):
    """Toutes les notifications GTA de l'utilisateur"""
    if not hasattr(request.user, 'employe'):
        messages.error(request, 'Vous devez être associé à un employé.')
        return redirect('gestion_temps_activite:dashboard')

    employe = request.user.employe

    notifications_gta = NotificationAbsence.objects.filter(
        destinataire=employe,
        tache__isnull=False
    ).select_related(
        'tache', 'tache__projet', 'tache__assignee'
    ).order_by('-date_creation')

    context = {
        'notifications': notifications_gta,
        'page_title': 'Toutes mes notifications GTA'
    }

    return render(request, 'gestion_temps_activite/notifications_liste.html', context)


@login_required
def marquer_notification_gta_lue(request, notification_id):
    """Marquer une notification GTA comme lue (AJAX)"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Requête invalide'}, status=400)

    try:
        notification = NotificationAbsence.objects.get(
            pk=notification_id,
            destinataire=request.user.employe if hasattr(request.user, 'employe') else None,
            tache__isnull=False  # Uniquement les notifications GTA
        )

        if not notification.lue:
            notification.marquer_comme_lue()

        return JsonResponse({'success': True})

    except NotificationAbsence.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification non trouvée'}, status=404)


@login_required
def marquer_toutes_notifications_gta_lues(request):
    """Marquer toutes les notifications GTA comme lues"""
    if not hasattr(request.user, 'employe'):
        messages.error(request, 'Vous devez être associé à un employé.')
        return redirect('gestion_temps_activite:dashboard')

    count = NotificationAbsence.objects.filter(
        destinataire=request.user.employe,
        tache__isnull=False,
        lue=False
    ).update(lue=True, date_lecture=timezone.now())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'count': count})

    messages.success(request, f'{count} notification(s) GTA marquée(s) comme lue(s).')
    return redirect(request.META.get('HTTP_REFERER', 'gestion_temps_activite:dashboard'))


def notifier_nouvelle_tache(tache, createur):
    """Notifier l'assigné d'une nouvelle tâche"""
    if not tache.assignee:
        return None

    return NotificationAbsence.creer_notification(
        destinataire=tache.assignee,
        type_notif='TACHE_ASSIGNEE',
        message=f"📋 Nouvelle tâche assignée : {tache.titre}",
        contexte='GTA',
        tache=tache
    )


def notifier_reassignation_tache(tache, ancien_assignee, nouvel_assignee):
    """Notifier l'ancien et le nouvel assigné lors d'une réassignation"""
    notifications = []

    if nouvel_assignee:
        notifications.append(
            NotificationAbsence.creer_notification(
                destinataire=nouvel_assignee,
                type_notif='TACHE_REASSIGNEE',
                message=f"📋 Tâche réassignée : {tache.titre}",
                contexte='GTA',
                tache=tache
            )
        )

    if ancien_assignee and ancien_assignee != nouvel_assignee:
        notifications.append(
            NotificationAbsence.creer_notification(
                destinataire=ancien_assignee,
                type_notif='TACHE_REASSIGNEE',
                message=f"ℹ️ La tâche '{tache.titre}' a été réassignée à {nouvel_assignee.nom if nouvel_assignee else 'un autre employé'}",
                contexte='GTA',
                tache=tache
            )
        )

    return notifications


def notifier_modification_tache(tache, employe_modifiant, changements):
    """Notifier l'assigné d'une modification de tâche"""
    if not tache.assignee or tache.assignee == employe_modifiant:
        return None

    message = f"✏️ Votre tâche '{tache.titre}' a été modifiée"
    if changements:
        message += f" : {', '.join(changements)}"

    return NotificationAbsence.creer_notification(
        destinataire=tache.assignee,
        type_notif='TACHE_MODIFIEE',
        message=message,
        contexte='GTA',
        tache=tache
    )


def notifier_changement_statut_tache(tache, ancien_statut, nouveau_statut):
    """Notifier le changement de statut d'une tâche"""
    if not tache.assignee:
        return None

    messages_statut = {
        ('A_FAIRE', 'EN_COURS'): "🚀 Votre tâche '{titre}' est maintenant en cours",
        ('EN_COURS', 'TERMINE'): "✅ La tâche '{titre}' a été marquée comme terminée",
        ('EN_COURS', 'EN_ATTENTE'): "⏸️ La tâche '{titre}' est en attente",
        ('EN_ATTENTE', 'EN_COURS'): "▶️ La tâche '{titre}' a repris",
        ('EN_COURS', 'A_FAIRE'): "↩️ La tâche '{titre}' est revenue à 'À faire'",
    }

    cle = (ancien_statut, nouveau_statut)
    if cle in messages_statut:
        message = messages_statut[cle].format(titre=tache.titre)

        return NotificationAbsence.creer_notification(
            destinataire=tache.assignee,
            type_notif='STATUT_TACHE_CHANGE',
            message=message,
            contexte='GTA',
            tache=tache
        )

    return None


def notifier_nouveau_commentaire(commentaire):
    """Notifier les personnes mentionnées dans un commentaire"""
    if not commentaire.tache.assignee:
        return []

    notifications = []

    # Notifier l'assigné de la tâche (si différent de l'auteur)
    if commentaire.tache.assignee != commentaire.employe:
        notifications.append(
            NotificationAbsence.creer_notification(
                destinataire=commentaire.tache.assignee,
                type_notif='COMMENTAIRE_TACHE',
                message=f"💬 Nouveau commentaire sur votre tâche '{commentaire.tache.titre}'",
                contexte='GTA',
                tache=commentaire.tache
            )
        )

    # Notifier les personnes mentionnées
    for mentionne in commentaire.mentions.all():
        if mentionne != commentaire.employe:
            notifications.append(
                NotificationAbsence.creer_notification(
                    destinataire=mentionne,
                    type_notif='COMMENTAIRE_TACHE',
                    message=f"💬 Vous avez été mentionné dans un commentaire sur la tâche '{commentaire.tache.titre}'",
                    contexte='GTA',
                    tache=commentaire.tache
                )
            )

    return notifications


def notifier_echeance_tache_proche(tache):
    """Notifier que l'échéance d'une tâche approche"""
    if not tache.assignee or not tache.date_fin_prevue:
        return None

    aujourdhui = timezone.now().date()
    jours_restants = (tache.date_fin_prevue - aujourdhui).days

    if 0 <= jours_restants <= 2:  # Dans les 2 prochains jours
        message = f"⏳ Échéance proche ({jours_restants} jour(s)) : {tache.titre}"

        return NotificationAbsence.creer_notification(
            destinataire=tache.assignee,
            type_notif='ECHEANCE_TACHE_PROCHE',
            message=message,
            contexte='GTA',
            tache=tache
        )

    return None