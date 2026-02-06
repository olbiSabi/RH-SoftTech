"""
Vues pour la gestion des bons de commande.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from django.core.paginator import Paginator
from django.db.models import Q

from gestion_achats.models import GACBonCommande, GACDemandeAchat
from gestion_achats.forms import (
    BonCommandeForm,
    LigneBonCommandeForm,
    BonCommandeEnvoiForm,
    BonCommandeConfirmationForm,
)
from gestion_achats.services import BonCommandeService, DemandeService
from gestion_achats.permissions import GACPermissions, require_permission
from gestion_achats.decorators import require_bon_commande_access, require_role


@login_required
def bon_commande_liste(request):
    """Liste des bons de commande."""
    if GACPermissions.can_view_all_bons_commande(request.user):
        bcs = GACBonCommande.objects.all()
    else:
        # Voir les BCs liés aux demandes de l'utilisateur
        bcs = GACBonCommande.objects.filter(
            demande_achat__demandeur=request.user.employe
        )

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        bcs = bcs.filter(statut=statut)

    search = request.GET.get('search')
    if search:
        bcs = bcs.filter(
            Q(numero__icontains=search) |
            Q(fournisseur__raison_sociale__icontains=search)
        )

    bcs = bcs.order_by('-date_creation')

    paginator = Paginator(bcs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'gestion_achats/bon_commande/bc_liste.html', {
        'page_obj': page_obj,
        'statut_filter': statut,
        'search': search,
    })


@login_required
@require_bon_commande_access
def bon_commande_detail(request, pk, bon_commande):
    """Détail d'un bon de commande."""
    return render(request, 'gestion_achats/bon_commande/bc_detail.html', {
        'bc': bon_commande,
        'lignes': bon_commande.lignes.all().order_by('ordre'),
        'can_modify': GACPermissions.can_modify_bon_commande(request.user, bon_commande),
        'can_emit': GACPermissions.can_emit_bon_commande(request.user, bon_commande),
        'can_send': GACPermissions.can_send_bon_commande(request.user, bon_commande),
        'can_confirm': GACPermissions.can_confirm_bon_commande(request.user, bon_commande),
        'can_cancel': GACPermissions.can_cancel_bon_commande(request.user, bon_commande),
    })


@login_required
@require_role('ACHETEUR')
def bon_commande_create_from_demande(request, demande_pk):
    """Créer un BC depuis une demande validée."""
    demande = get_object_or_404(GACDemandeAchat, uuid=demande_pk)
    require_permission(GACPermissions.can_convert_to_bc, request.user, demande)

    if request.method == 'POST':
        form = BonCommandeForm(request.POST)
        if form.is_valid():
            try:
                bc = BonCommandeService.creer_bon_commande(
                    demande_achat=demande,
                    acheteur=request.user.employe,
                    fournisseur=form.cleaned_data['fournisseur'],
                    date_livraison_souhaitee=form.cleaned_data.get('date_livraison_souhaitee')
                )

                messages.success(request, f'Bon de commande {bc.numero} créé.')
                return redirect('gestion_achats:bon_commande_detail', pk=bc.uuid)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = BonCommandeForm()

    return render(request, 'gestion_achats/bon_commande/bc_create_from_demande.html', {
        'form': form,
        'demande': demande,
    })


@login_required
@require_bon_commande_access
def bon_commande_emit(request, pk, bon_commande):
    """Émettre un bon de commande."""
    require_permission(GACPermissions.can_emit_bon_commande, request.user, bon_commande)

    if request.method == 'POST':
        try:
            BonCommandeService.emettre_bon_commande(bon_commande, request.user.employe)
            messages.success(request, f'BC {bon_commande.numero} émis.')
            return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
            return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

    # Si ce n'est pas une requête POST, rediriger vers la page de détail
    # (la confirmation se fait maintenant via le modal dans bc_detail.html)
    return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)


@login_required
@require_bon_commande_access
def bon_commande_send(request, pk, bon_commande):
    """Envoyer un BC au fournisseur."""
    require_permission(GACPermissions.can_send_bon_commande, request.user, bon_commande)

    if request.method == 'POST':
        form = BonCommandeEnvoiForm(request.POST)
        if form.is_valid():
            try:
                BonCommandeService.envoyer_au_fournisseur(
                    bon_commande,
                    request.user.employe,
                    email_destinataire=form.cleaned_data.get('email_destinataire')
                )
                messages.success(request, f'BC {bon_commande.numero} envoyé.')
                return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)
            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        # Pré-remplir avec l'email du fournisseur
        initial = {'email_destinataire': bon_commande.fournisseur.email}
        form = BonCommandeEnvoiForm(initial=initial)

    return render(request, 'gestion_achats/bon_commande/bc_envoi.html', {
        'form': form,
        'bc': bon_commande,
    })


@login_required
@require_bon_commande_access
def bon_commande_pdf(request, pk, bon_commande):
    """Télécharger le PDF d'un BC."""
    require_permission(GACPermissions.can_download_pdf, request.user, bon_commande)

    if bon_commande.fichier_pdf:
        return FileResponse(
            bon_commande.fichier_pdf.open('rb'),
            content_type='application/pdf',
            filename=f'BC_{bon_commande.numero}.pdf'
        )
    else:
        messages.error(request, 'Aucun PDF généré pour ce BC.')
        return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)


# ========== GESTION DES LIGNES DE BON DE COMMANDE ==========

@login_required
@require_bon_commande_access
def ligne_bc_create(request, pk, bon_commande):
    """Ajouter une ligne à un bon de commande en brouillon."""
    require_permission(GACPermissions.can_modify_bon_commande, request.user, bon_commande)

    # Vérifier que le BC est en brouillon
    if bon_commande.statut != 'BROUILLON':
        messages.error(request, 'Impossible d\'ajouter des lignes à un BC qui n\'est plus en brouillon.')
        return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

    if request.method == 'POST':
        form = LigneBonCommandeForm(request.POST)
        if form.is_valid():
            try:
                ligne = form.save(commit=False)
                ligne.bon_commande = bon_commande

                # Déterminer l'ordre (dernière ligne + 1)
                from gestion_achats.models import GACLigneBonCommande
                derniere_ligne = bon_commande.lignes.order_by('-ordre').first()
                ligne.ordre = (derniere_ligne.ordre + 1) if derniere_ligne else 1

                ligne.save()

                # Recalculer les totaux du BC
                bon_commande.calculer_totaux()

                messages.success(
                    request,
                    f'Ligne ajoutée : {ligne.article.designation} × {ligne.quantite_commandee}'
                )
                return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de l\'ajout de la ligne : {str(e)}')
    else:
        form = LigneBonCommandeForm()

    return render(request, 'gestion_achats/bon_commande/ligne_bc_form.html', {
        'form': form,
        'bc': bon_commande,
        'action': 'Ajouter',
    })


@login_required
@require_bon_commande_access
def ligne_bc_update(request, pk, bon_commande, ligne_pk):
    """Modifier une ligne d'un bon de commande en brouillon."""
    require_permission(GACPermissions.can_modify_bon_commande, request.user, bon_commande)

    # Vérifier que le BC est en brouillon
    if bon_commande.statut != 'BROUILLON':
        messages.error(request, 'Impossible de modifier des lignes d\'un BC qui n\'est plus en brouillon.')
        return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

    from gestion_achats.models import GACLigneBonCommande
    ligne = get_object_or_404(GACLigneBonCommande, pk=ligne_pk, bon_commande=bon_commande)

    if request.method == 'POST':
        form = LigneBonCommandeForm(request.POST, instance=ligne)
        if form.is_valid():
            try:
                form.save()

                # Recalculer les totaux du BC
                bon_commande.calculer_totaux()

                messages.success(request, 'Ligne modifiée avec succès.')
                return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de la modification : {str(e)}')
    else:
        form = LigneBonCommandeForm(instance=ligne)

    return render(request, 'gestion_achats/bon_commande/ligne_bc_form.html', {
        'form': form,
        'bc': bon_commande,
        'ligne': ligne,
        'action': 'Modifier',
    })


@login_required
@require_bon_commande_access
def ligne_bc_delete(request, pk, bon_commande, ligne_pk):
    """Supprimer une ligne d'un bon de commande en brouillon."""
    require_permission(GACPermissions.can_modify_bon_commande, request.user, bon_commande)

    # Vérifier que le BC est en brouillon
    if bon_commande.statut != 'BROUILLON':
        messages.error(request, 'Impossible de supprimer des lignes d\'un BC qui n\'est plus en brouillon.')
        return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

    from gestion_achats.models import GACLigneBonCommande
    ligne = get_object_or_404(GACLigneBonCommande, pk=ligne_pk, bon_commande=bon_commande)

    if request.method == 'POST':
        try:
            article_designation = ligne.article.designation
            quantite = ligne.quantite_commandee

            ligne.delete()

            # Recalculer les totaux du BC
            bon_commande.calculer_totaux()

            messages.success(
                request,
                f'Ligne supprimée : {article_designation} × {quantite}'
            )
            return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression : {str(e)}')

    return render(request, 'gestion_achats/bon_commande/ligne_bc_confirm_delete.html', {
        'bc': bon_commande,
        'ligne': ligne,
    })
