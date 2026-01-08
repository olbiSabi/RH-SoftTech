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
import json
from employee.models import ZY00

from .models import ZDCL, ZDAC, ZDPJ, ZDTA, ZDDO, ZDIT, ZDCM
from .forms import (
    ZDCLForm, ZDACForm, ZDPJForm, ZDTAForm, ZDDOForm,
    ZDITForm, ZDITValidationForm, TimerForm, RechercheImputationForm, ZDCMForm
)
from absence.decorators import drh_or_admin_required, gestion_app_required
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
# ==================== VUES CLIENTS (ZDCL) ====================

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
            messages.success(request, f'Client "{client.raison_sociale}" créé avec succès.')
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


@login_required
def client_update(request, pk):
    """Modifier un client"""
    client = get_object_or_404(ZDCL, pk=pk)

    if request.method == 'POST':
        form = ZDCLForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client "{client.raison_sociale}" modifié avec succès.')
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


@login_required
def client_delete(request, pk):
    """Supprimer un client"""
    client = get_object_or_404(ZDCL, pk=pk)

    if request.method == 'POST':
        raison_sociale = client.raison_sociale
        try:
            client.delete()
            messages.success(request, f'Client "{raison_sociale}" supprimé avec succès.')
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


@login_required
def activite_create(request):
    """Créer un nouveau type d'activité"""
    if request.method == 'POST':
        form = ZDACForm(request.POST)
        if form.is_valid():
            activite = form.save()
            messages.success(request, f'Type d\'activité "{activite.libelle}" créé avec succès.')
            return redirect('gestion_temps_activite:activite_liste')
        else:
            messages.error(request, 'Erreur lors de la création du type d\'activité.')
    else:
        # Date de début par défaut = aujourd'hui
        initial_data = {'date_debut': timezone.now().date()}
        form = ZDACForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'Nouveau Type d\'Activité',
        'action': 'Créer'
    }

    return render(request, 'gestion_temps_activite/activite_form.html', context)


@login_required
def activite_update(request, pk):
    """Modifier un type d'activité"""
    activite = get_object_or_404(ZDAC, pk=pk)

    if request.method == 'POST':
        form = ZDACForm(request.POST, instance=activite)
        if form.is_valid():
            form.save()
            messages.success(request, f'Type d\'activité "{activite.libelle}" modifié avec succès.')
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


@login_required
def activite_delete(request, pk):
    """Supprimer un type d'activité"""
    activite = get_object_or_404(ZDAC, pk=pk)

    if request.method == 'POST':
        libelle = activite.libelle
        try:
            activite.delete()
            messages.success(request, f'Type d\'activité "{libelle}" supprimé avec succès.')
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
            messages.success(request,
                f'Projet "{projet.nom_projet}" créé avec succès. '
                f'Code projet: {projet.code_projet}'
            )
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


@login_required
def projet_update(request, pk):
    """Modifier un projet"""
    projet = get_object_or_404(ZDPJ, pk=pk)

    if request.method == 'POST':
        form = ZDPJForm(request.POST, instance=projet)
        if form.is_valid():
            form.save()
            messages.success(request, f'Projet "{projet.nom_projet}" modifié avec succès.')
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


@login_required
def projet_delete(request, pk):
    """Supprimer un projet"""
    projet = get_object_or_404(ZDPJ, pk=pk)

    if request.method == 'POST':
        nom_projet = projet.nom_projet
        try:
            projet.delete()
            messages.success(request, f'Projet "{nom_projet}" supprimé avec succès.')
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

        # ========================================
        # 1. PERMISSIONS
        # ========================================

        # A. Peut voir les commentaires privés ?
        peut_voir_commentaires_prives = any([
            tache.assignee == employe_connecte,
            tache.projet.chef_projet == employe_connecte,
            employe_connecte.has_role('DRH'),
            employe_connecte.has_role('GESTION_APP'),
            employe_connecte.est_manager_departement(),
        ])

        # B. Peut ajouter des commentaires ? ✅ CORRIGÉ
        peut_ajouter_commentaire = any([
            tache.assignee == employe_connecte,
            tache.projet.chef_projet == employe_connecte,
            employe_connecte.has_role('DRH'),
            employe_connecte.has_role('GESTION_APP'),
            # ✅ AJOUT : Vérifier si même équipe que l'assigné
            (tache.assignee and
             employe_connecte.get_departement_actuel() == tache.assignee.get_departement_actuel()),
            # ✅ AJOUT : Vérifier si manager du département de l'assigné
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

        # ========================================
        # 2. RÉCUPÉRER ET FILTRER LES COMMENTAIRES
        # ========================================

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

        # ✅ FILTRAGE CRITIQUE
        commentaires_visibles = []

        print(f"\n[DEBUG tache_detail] Employé connecté: {employe_connecte.nom}")
        print(f"[DEBUG tache_detail] Département: {employe_connecte.get_departement_actuel()}")
        print(f"[DEBUG tache_detail] Peut ajouter commentaire: {peut_ajouter_commentaire}")
        print(f"[DEBUG tache_detail] Nombre total de commentaires: {commentaires_query.count()}")

        for commentaire in commentaires_query:
            # ✅ Vérifier la visibilité avec logs
            peut_voir = commentaire.peut_voir(employe_connecte)
            print(f"[DEBUG tache_detail] Commentaire #{commentaire.id} - Peut voir: {peut_voir}")

            if peut_voir:
                # Filtrer les réponses
                reponses_visibles = [
                    reponse for reponse in commentaire.reponses.all()
                    if reponse.peut_voir(employe_connecte)
                ]

                commentaire.reponses_visibles = reponses_visibles
                commentaire.peut_modifier_par = commentaire.peut_modifier(employe_connecte)
                commentaire.peut_supprimer_par = commentaire.peut_supprimer(employe_connecte)

                commentaires_visibles.append(commentaire)

        commentaires = commentaires_visibles

        print(f"[DEBUG tache_detail] Commentaires visibles: {len(commentaires)}")

        # ========================================
        # 3. FORMULAIRE
        # ========================================

        if peut_ajouter_commentaire:
            form_commentaire = ZDCMForm(tache=tache, employe=employe_connecte)
        else:
            print(f"[DEBUG tache_detail] Formulaire non affiché - pas de permission")

    # ========================================
    # CONTEXTE
    # ========================================

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


@login_required
def tache_create(request):
    """Créer une nouvelle tâche"""
    if request.method == 'POST':
        form = ZDTAForm(request.POST)
        if form.is_valid():
            tache = form.save(commit=False)
            if hasattr(request.user, 'employe'):
                tache.cree_par = request.user.employe
            tache.save()
            messages.success(request, f'Tâche "{tache.titre}" créée avec succès.')
            return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)
        else:
            messages.error(request, 'Erreur lors de la création de la tâche.')
    else:
        # Si un projet est spécifié dans l'URL
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


@login_required
def tache_update(request, pk):
    """Modifier une tâche"""
    tache = get_object_or_404(ZDTA, pk=pk)

    if request.method == 'POST':
        form = ZDTAForm(request.POST, instance=tache)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tâche "{tache.titre}" modifiée avec succès.')
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


@login_required
def tache_delete(request, pk):
    """Supprimer une tâche"""
    tache = get_object_or_404(ZDTA, pk=pk)

    if request.method == 'POST':
        titre = tache.titre
        projet_pk = tache.projet.pk
        try:
            tache.delete()
            messages.success(request, f'Tâche "{titre}" supprimée avec succès.')
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

            messages.success(request, f'Document "{document.nom_document}" uploadé avec succès.')

            # Rediriger selon le type de rattachement
            if document.type_rattachement == 'PROJET':
                return redirect('gestion_temps_activite:projet_detail', pk=document.projet.pk)
            else:
                return redirect('gestion_temps_activite:tache_detail', pk=document.tache.pk)
        else:
            messages.error(request, 'Erreur lors de l\'upload du document.')
    else:
        # Pré-remplir selon les paramètres GET
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
            # Supprimer le fichier physique
            if document.fichier:
                document.fichier.delete()
            document.delete()

            messages.success(request, f'Document "{nom}" supprimé avec succès.')

            # Rediriger
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

@login_required
def imputation_liste(request):
    """Liste des imputations avec recherche et filtrage"""
    imputations = ZDIT.objects.select_related(
        'employe', 'tache__projet', 'activite'
    ).all().order_by('-date', '-date_creation')

    # Formulaire de recherche
    form = RechercheImputationForm(request.GET or None)

    if form.is_valid():
        # Appliquer les filtres
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

    context = {
        'imputations': imputations_page,
        'form': form,
        'total_heures': total_heures,
        'heures_validees': heures_validees,
        'heures_facturables': heures_facturables,
        'total_imputations': imputations.count()
    }

    return render(request, 'gestion_temps_activite/imputation_liste.html', context)


@login_required
def imputation_mes_temps(request):
    """Mes imputations de temps (employé connecté)"""
    if not hasattr(request.user, 'employe'):
        messages.error(request, 'Vous devez être associé à un employé.')
        return redirect('gestion_temps_activite:dashboard')

    employe = request.user.employe

    # Période sélectionnée (par défaut: ce mois)
    periode = request.GET.get('periode', 'mois')
    date_actuelle = timezone.now().date()

    if periode == 'semaine':
        date_debut = date_actuelle - timedelta(days=date_actuelle.weekday())
        date_fin = date_debut + timedelta(days=6)
    elif periode == 'mois':
        date_debut = date_actuelle.replace(day=1)
        # Dernier jour du mois
        if date_actuelle.month == 12:
            date_fin = date_actuelle.replace(day=31)
        else:
            date_fin = (date_actuelle.replace(month=date_actuelle.month + 1, day=1) - timedelta(days=1))
    else:  # année
        date_debut = date_actuelle.replace(month=1, day=1)
        date_fin = date_actuelle.replace(month=12, day=31)

    # Imputations de la période
    imputations = ZDIT.objects.filter(
        employe=employe,
        date__gte=date_debut,
        date__lte=date_fin
    ).select_related('tache__projet', 'activite').order_by('-date')

    # Statistiques
    total_heures = imputations.aggregate(total=Sum('duree'))['total'] or 0
    heures_validees = imputations.filter(valide=True).aggregate(total=Sum('duree'))['total'] or 0
    heures_en_attente = imputations.filter(valide=False).aggregate(total=Sum('duree'))['total'] or 0

    # Répartition par projet
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
        'heures_en_attente': heures_en_attente,
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
            messages.success(request, 'Imputation de temps enregistrée avec succès.')
            return redirect('gestion_temps_activite:imputation_mes_temps')
        else:
            messages.error(request, 'Erreur lors de l\'enregistrement.')
    else:
        form = ZDITForm(user=request.user)

    context = {
        'form': form,
        'title': 'Nouvelle Imputation',
        'action': 'Créer'
    }

    return render(request, 'gestion_temps_activite/imputation_form.html', context)


@login_required
def imputation_update(request, pk):
    """Modifier une imputation"""
    imputation = get_object_or_404(ZDIT, pk=pk)

    # Vérifier que l'utilisateur peut modifier (soit son imputation, soit il est manager/RH)
    if hasattr(request.user, 'employe'):
        if imputation.employe != request.user.employe and not request.user.is_staff:
            messages.error(request, 'Vous ne pouvez pas modifier cette imputation.')
            return redirect('gestion_temps_activite:imputation_mes_temps')

    # Empêcher la modification si déjà validé ou facturé
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
            messages.success(request, 'Imputation modifiée avec succès.')
            return redirect('gestion_temps_activite:imputation_mes_temps')
        else:
            messages.error(request, 'Erreur lors de la modification.')
    else:
        form = ZDITForm(instance=imputation, user=request.user)

    context = {
        'form': form,
        'imputation': imputation,
        'title': 'Modifier Imputation',
        'action': 'Modifier'
    }

    return render(request, 'gestion_temps_activite/imputation_form.html', context)


@login_required
def imputation_delete(request, pk):
    """Supprimer une imputation"""
    imputation = get_object_or_404(ZDIT, pk=pk)

    # Vérifier les permissions
    if hasattr(request.user, 'employe'):
        if imputation.employe != request.user.employe and not request.user.is_staff:
            messages.error(request, 'Vous ne pouvez pas supprimer cette imputation.')
            return redirect('gestion_temps_activite:imputation_mes_temps')

    # Empêcher la suppression si validé ou facturé
    if imputation.valide or imputation.facture:
        messages.error(request, 'Cette imputation ne peut pas être supprimée (validée ou facturée).')
        return redirect('gestion_temps_activite:imputation_mes_temps')

    if request.method == 'POST':
        try:
            imputation.delete()
            messages.success(request, 'Imputation supprimée avec succès.')
            return redirect('gestion_temps_activite:imputation_mes_temps')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer : {str(e)}')

    context = {
        'imputation': imputation
    }

    return render(request, 'gestion_temps_activite/imputation_confirm_delete.html', context)

@drh_or_admin_required
@login_required
def imputation_validation(request):
    """Validation des imputations (pour managers et RH)"""

    # Imputations à valider (non validées)
    imputations = ZDIT.objects.filter(
        valide=False
    ).select_related('employe', 'tache__projet', 'activite').order_by('-date')

    # Filtrage par employé
    employe_filter = request.GET.get('employe')
    if employe_filter:
        imputations = imputations.filter(employe_id=employe_filter)

    # Pagination
    paginator = Paginator(imputations, 30)
    page_number = request.GET.get('page')
    imputations_page = paginator.get_page(page_number)

    # Liste des employés pour le filtre
    employes = ZY00.objects.filter(etat='actif').order_by('nom', 'prenoms')

    context = {
        'imputations': imputations_page,
        'employes': employes,
        'employe_filter': employe_filter,
        'total_a_valider': imputations.count()
    }

    return render(request, 'gestion_temps_activite/imputation_validation.html', context)


@login_required
def imputation_valider(request, pk):
    """Valider une imputation"""
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé.')
        return redirect('gestion_temps_activite:dashboard')

    imputation = get_object_or_404(ZDIT, pk=pk)

    if request.method == 'POST':
        if not imputation.valide:
            imputation.valide = True
            if hasattr(request.user, 'employe'):
                imputation.valide_par = request.user.employe
            imputation.date_validation = timezone.now()
            imputation.save()
            messages.success(request, 'Imputation validée avec succès.')
        else:
            messages.info(request, 'Cette imputation est déjà validée.')

        return redirect('gestion_temps_activite:imputation_validation')

    context = {
        'imputation': imputation
    }

    return render(request, 'gestion_temps_activite/imputation_valider.html', context)


@login_required
def imputation_rejeter(request, pk):
    """Rejeter une imputation (la marquer comme non validée avec commentaire)"""
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
            messages.success(request, 'Imputation rejetée avec succès.')
        else:
            messages.error(request, 'Veuillez indiquer un motif de rejet.')

        return redirect('gestion_temps_activite:imputation_validation')

    context = {
        'imputation': imputation
    }

    return render(request, 'gestion_temps_activite/imputation_rejeter.html', context)


@login_required
def imputation_export_excel(request):
    """Export des imputations en format Excel avec pandas"""

    # Récupérer les mêmes filtres que la page liste
    imputations = ZDIT.objects.select_related(
        'employe', 'tache__projet', 'activite', 'valide_par'
    ).all().order_by('-date', '-date_creation')

    # Appliquer les mêmes filtres que le formulaire
    form = RechercheImputationForm(request.GET or None)

    if form.is_valid():
        # ... (garder les mêmes filtres) ...
        pass

    # Préparer les données pour le DataFrame
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
            'Taux Horaire (FCFA)': float(imputation.taux_horaire_applique) if imputation.taux_horaire_applique else 0,
            'Montant (FCFA)': montant,
            'Commentaire': imputation.commentaire or '',
            'Validé': 'Oui' if imputation.valide else 'Non',
            'Validé par': f"{imputation.valide_par.nom} {imputation.valide_par.prenoms}" if imputation.valide_par else '',
            'Date Validation': imputation.date_validation,
            'Facturable': 'Oui' if imputation.facturable else 'Non',
            'Facturé': 'Oui' if imputation.facture else 'Non',
            'Date Création': imputation.date_creation,
        })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # CONVERTIR TOUTES LES COLONNES DATETIME EN STRING (pour éviter l'erreur timezone)
    datetime_columns = df.select_dtypes(include=['datetime64[ns, UTC]', 'datetime64']).columns
    for col in datetime_columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Convertir les dates simples en string
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    # Créer la réponse Excel
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Imputations', index=False)

        # Ajuster la largeur des colonnes
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

@login_required
def dashboard(request):
    """Tableau de bord principal"""

    # Statistiques globales
    total_clients = ZDCL.objects.filter(actif=True).count()
    total_projets = ZDPJ.objects.filter(actif=True).count()
    projets_en_cours = ZDPJ.objects.filter(statut='EN_COURS').count()
    total_taches = ZDTA.objects.exclude(statut='TERMINE').count()

    # Projets récents
    projets_recents = ZDPJ.objects.select_related('client').filter(
        actif=True
    ).order_by('-date_creation')[:5]

    # Tâches urgentes (priorité haute ou critique, non terminées)
    taches_urgentes = ZDTA.objects.select_related('projet', 'assignee').filter(
        priorite__in=['HAUTE', 'CRITIQUE']
    ).exclude(statut='TERMINE').order_by('date_fin_prevue')[:10]

    # Si l'utilisateur est un employé, afficher ses statistiques personnelles
    if hasattr(request.user, 'employe'):
        employe = request.user.employe

        # Mes tâches
        mes_taches = ZDTA.objects.filter(
            assignee=employe
        ).exclude(statut='TERMINE').count()

        # Mes heures ce mois
        date_actuelle = timezone.now().date()
        debut_mois = date_actuelle.replace(day=1)
        mes_heures_mois = ZDIT.objects.filter(
            employe=employe,
            date__gte=debut_mois
        ).aggregate(total=Sum('duree'))['total'] or 0

        # Mes imputations non validées
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
    """Ajouter un commentaire"""
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
                form.save_m2m()

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
    """Répondre à un commentaire"""
    commentaire_parent = get_object_or_404(ZDCM, pk=commentaire_pk)
    tache = commentaire_parent.tache

    if request.method == 'POST':
        form = ZDCMForm(request.POST, tache=tache, employe=request.user.employe, parent=commentaire_parent)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.tache = tache
            reponse.employe = request.user.employe
            reponse.reponse_a = commentaire_parent
            reponse.save()
            form.save_m2m()

            messages.success(request, 'Réponse ajoutée avec succès.')
            return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)
    else:
        form = ZDCMForm(tache=tache, employe=request.user.employe, parent=commentaire_parent)

    context = {
        'form': form,
        'tache': tache,
        'commentaire_parent': commentaire_parent,
        'title': 'Répondre au commentaire'
    }

    return render(request, 'gestion_temps_activite/commentaire_form.html', context)


@login_required
def commentaire_modifier(request, pk):
    """Modifier un commentaire - Version AJAX"""
    commentaire = get_object_or_404(ZDCM, pk=pk)

    # Vérifier les permissions
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
        # Requête AJAX
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

        # Requête normale (fallback)
        else:
            form = ZDCMForm(request.POST, instance=commentaire, tache=commentaire.tache, employe=employe)

            if form.is_valid():
                try:
                    commentaire = form.save(commit=False)
                    commentaire.edite = True
                    commentaire.date_edition = timezone.now()
                    commentaire.save()
                    form.save_m2m()

                    messages.success(request, '✅ Commentaire modifié avec succès.')
                    return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)

                except Exception as e:
                    messages.error(request, f'❌ Erreur : {str(e)}')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')

    # Si GET, rediriger vers la tâche
    return redirect('gestion_temps_activite:tache_detail', pk=commentaire.tache.pk)


@login_required
def commentaire_supprimer(request, pk):
    """Supprimer un commentaire - Version AJAX"""
    commentaire = get_object_or_404(ZDCM, pk=pk)

    # Vérifier les permissions
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
        # Requête AJAX
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

        # Requête normale (fallback)
        else:
            try:
                commentaire.delete()
                messages.success(request, '✅ Commentaire supprimé avec succès.')
            except Exception as e:
                messages.error(request, f'❌ Erreur lors de la suppression : {str(e)}')

            return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)

    # Si GET, rediriger vers la tâche
    return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)


@login_required
def commentaire_mentions(request):
    """Récupérer les mentions (pour autocomplete)"""
    if not hasattr(request.user, 'employe'):
        return JsonResponse([], safe=False)

    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    # Chercher les employés actifs
    employes = ZY00.objects.filter(
        Q(nom__icontains=query) | Q(prenoms__icontains=query),
        etat='actif'
    ).exclude(pk=request.user.employe.pk)[:10]

    result = [
        {
            'id': emp.pk,
            'text': f"{emp.nom} {emp.prenoms}",
            'matricule': emp.matricule
        }
        for emp in employes
    ]

    return JsonResponse(result, safe=False)