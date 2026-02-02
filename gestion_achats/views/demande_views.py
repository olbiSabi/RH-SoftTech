"""
Vues pour la gestion des demandes d'achat.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from gestion_achats.models import GACDemandeAchat, GACLigneDemandeAchat
from gestion_achats.forms import (
    DemandeAchatForm,
    LigneDemandeAchatForm,
    DemandeValidationForm,
    DemandeRefusForm,
    DemandeAnnulationForm,
)
from gestion_achats.services import DemandeService
from gestion_achats.permissions import GACPermissions, require_permission
from gestion_achats.decorators import require_demande_access


@login_required
def demande_liste(request):
    """Liste des demandes d'achat."""
    # Filtrer selon les permissions
    if GACPermissions.can_view_all_demandes(request.user):
        demandes = GACDemandeAchat.objects.all()
    else:
        # Voir uniquement ses demandes et celles à valider
        demandes = GACDemandeAchat.objects.filter(
            Q(demandeur=request.user.employe) |
            Q(validateur_n1=request.user.employe) |
            Q(validateur_n2=request.user.employe)
        )

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        demandes = demandes.filter(statut=statut)

    # Recherche
    search = request.GET.get('search')
    if search:
        demandes = demandes.filter(
            Q(numero__icontains=search) |
            Q(objet__icontains=search) |
            Q(demandeur__nom__icontains=search)
        )

    # Tri
    demandes = demandes.order_by('-date_creation')

    # Pagination
    paginator = Paginator(demandes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'statut_filter': statut,
        'search': search,
    }

    return render(request, 'gestion_achats/demande/demande_liste.html', context)


@login_required
def demande_create(request):
    """Créer une nouvelle demande d'achat."""
    require_permission(GACPermissions.can_create_demande, request.user)

    if request.method == 'POST':
        form = DemandeAchatForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                demande = DemandeService.creer_demande_brouillon(
                    demandeur=request.user.employe,
                    objet=form.cleaned_data['objet'],
                    justification=form.cleaned_data['justification'],
                    departement=form.cleaned_data.get('departement'),
                    projet=form.cleaned_data.get('projet'),
                    budget=form.cleaned_data.get('budget'),
                    priorite=form.cleaned_data.get('priorite', 'NORMALE'),
                )

                messages.success(
                    request,
                    f'Demande {demande.numero} créée avec succès.'
                )
                return redirect('gestion_achats:demande_detail', pk=demande.pk)

            except Exception as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
    else:
        form = DemandeAchatForm(user=request.user)

    return render(request, 'gestion_achats/demande/demande_form.html', {
        'form': form,
        'action': 'Créer',
    })


@login_required
@require_demande_access
def demande_detail(request, pk, demande):
    """Détail d'une demande d'achat."""
    context = {
        'demande': demande,
        'lignes': demande.lignes.all().order_by('ordre'),
        'can_modify': GACPermissions.can_modify_demande(request.user, demande),
        'can_submit': GACPermissions.can_submit_demande(request.user, demande),
        'can_validate_n1': GACPermissions.can_validate_n1(request.user, demande),
        'can_validate_n2': GACPermissions.can_validate_n2(request.user, demande),
        'can_refuse': GACPermissions.can_refuse_demande(request.user, demande),
        'can_cancel': GACPermissions.can_cancel_demande(request.user, demande),
        'can_convert': GACPermissions.can_convert_to_bc(request.user, demande),
    }

    return render(request, 'gestion_achats/demande/demande_detail.html', context)


@login_required
@require_demande_access
def demande_update(request, pk, demande):
    """Modifier une demande d'achat."""
    require_permission(GACPermissions.can_modify_demande, request.user, demande)

    if request.method == 'POST':
        form = DemandeAchatForm(request.POST, instance=demande, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Demande modifiée avec succès.')
            return redirect('gestion_achats:demande_detail', pk=demande.pk)
    else:
        form = DemandeAchatForm(instance=demande, user=request.user)

    return render(request, 'gestion_achats/demande/demande_form.html', {
        'form': form,
        'demande': demande,
        'action': 'Modifier',
    })


@login_required
@require_demande_access
def demande_ligne_create(request, pk, demande):
    """Ajouter une ligne à une demande."""
    require_permission(GACPermissions.can_modify_demande, request.user, demande)

    if request.method == 'POST':
        form = LigneDemandeAchatForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.ajouter_ligne(
                    demande=demande,
                    article=form.cleaned_data['article'],
                    quantite=form.cleaned_data['quantite'],
                    prix_unitaire=form.cleaned_data['prix_unitaire'],
                    taux_tva=form.cleaned_data.get('taux_tva'),
                    commentaire=form.cleaned_data.get('commentaire', ''),
                )

                messages.success(request, 'Ligne ajoutée avec succès.')
                return redirect('gestion_achats:demande_detail', pk=demande.pk)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = LigneDemandeAchatForm()

    return render(request, 'gestion_achats/demande/ligne_form.html', {
        'form': form,
        'demande': demande,
    })


@login_required
@require_demande_access
def demande_submit(request, pk, demande):
    """Soumettre une demande pour validation."""
    require_permission(GACPermissions.can_submit_demande, request.user, demande)

    if request.method == 'POST':
        try:
            DemandeService.soumettre_demande(demande, request.user.employe)
            messages.success(
                request,
                f'Demande {demande.numero} soumise pour validation.'
            )
            return redirect('gestion_achats:demande_detail', pk=demande.pk)

        except Exception as e:
            messages.error(request, f'Erreur lors de la soumission: {str(e)}')
            return redirect('gestion_achats:demande_detail', pk=demande.pk)

    return render(request, 'gestion_achats/demande/demande_confirm.html', {
        'demande': demande,
        'action': 'soumettre',
        'message': 'Voulez-vous vraiment soumettre cette demande pour validation ?',
    })


@login_required
@require_demande_access
def demande_validate_n1(request, pk, demande):
    """Valider une demande au niveau N1."""
    require_permission(GACPermissions.can_validate_n1, request.user, demande)

    if request.method == 'POST':
        form = DemandeValidationForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.valider_n1(
                    demande,
                    request.user.employe,
                    commentaire=form.cleaned_data.get('commentaire', '')
                )

                messages.success(request, f'Demande {demande.numero} validée (N1).')
                return redirect('gestion_achats:demande_detail', pk=demande.pk)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = DemandeValidationForm()

    return render(request, 'gestion_achats/demande/demande_validation.html', {
        'form': form,
        'demande': demande,
        'niveau': 'N1',
    })


@login_required
@require_demande_access
def demande_validate_n2(request, pk, demande):
    """Valider une demande au niveau N2."""
    require_permission(GACPermissions.can_validate_n2, request.user, demande)

    if request.method == 'POST':
        form = DemandeValidationForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.valider_n2(
                    demande,
                    request.user.employe,
                    commentaire=form.cleaned_data.get('commentaire', '')
                )

                messages.success(request, f'Demande {demande.numero} validée (N2).')
                return redirect('gestion_achats:demande_detail', pk=demande.pk)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = DemandeValidationForm()

    return render(request, 'gestion_achats/demande/demande_validation.html', {
        'form': form,
        'demande': demande,
        'niveau': 'N2',
    })


@login_required
@require_demande_access
def demande_refuse(request, pk, demande):
    """Refuser une demande."""
    require_permission(GACPermissions.can_refuse_demande, request.user, demande)

    if request.method == 'POST':
        form = DemandeRefusForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.refuser_demande(
                    demande,
                    request.user.employe,
                    motif=form.cleaned_data['motif_refus']
                )

                messages.warning(request, f'Demande {demande.numero} refusée.')
                return redirect('gestion_achats:demande_detail', pk=demande.pk)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = DemandeRefusForm()

    return render(request, 'gestion_achats/demande/demande_refus.html', {
        'form': form,
        'demande': demande,
    })


@login_required
@require_demande_access
def demande_cancel(request, pk, demande):
    """Annuler une demande."""
    require_permission(GACPermissions.can_cancel_demande, request.user, demande)

    if request.method == 'POST':
        form = DemandeAnnulationForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.annuler_demande(
                    demande,
                    request.user.employe,
                    motif=form.cleaned_data['motif_annulation']
                )

                messages.warning(request, f'Demande {demande.numero} annulée.')
                return redirect('gestion_achats:demande_detail', pk=demande.pk)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = DemandeAnnulationForm()

    return render(request, 'gestion_achats/demande/demande_annulation.html', {
        'form': form,
        'demande': demande,
    })


@login_required
def mes_demandes(request):
    """Liste des demandes de l'utilisateur connecté."""
    demandes = GACDemandeAchat.objects.filter(
        demandeur=request.user.employe
    ).order_by('-date_creation')

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        demandes = demandes.filter(statut=statut)

    # Pagination
    paginator = Paginator(demandes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'gestion_achats/demande/mes_demandes.html', {
        'page_obj': page_obj,
        'statut_filter': statut,
    })


@login_required
def demandes_a_valider(request):
    """Liste des demandes à valider par l'utilisateur."""
    # Demandes à valider N1
    demandes_n1 = DemandeService.get_demandes_a_valider_n1(request.user.employe)

    # Demandes à valider N2
    demandes_n2 = DemandeService.get_demandes_a_valider_n2(request.user.employe)

    return render(request, 'gestion_achats/demande/demandes_a_valider.html', {
        'demandes_n1': demandes_n1,
        'demandes_n2': demandes_n2,
    })
