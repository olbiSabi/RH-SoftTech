"""
Vues pour la gestion des réceptions de marchandises.
"""

from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from gestion_achats.models import (
    GACReception,
    GACLigneReception,
    GACBonCommande,
    GACLigneBonCommande,
)
from gestion_achats.forms import (
    ReceptionForm,
    LigneReceptionForm,
    ReceptionValidationForm,
    ReceptionAnnulationForm,
)
from gestion_achats.services.reception_service import ReceptionService
from gestion_achats.permissions import GACPermissions, require_permission

import logging
logger = logging.getLogger(__name__)


@login_required
def reception_list(request):
    """Liste des réceptions."""
    require_permission(GACPermissions.can_view_all_receptions, request.user)

    # Récupérer toutes les réceptions
    receptions = GACReception.objects.select_related(
        'bon_commande',
        'bon_commande__fournisseur',
        'receptionnaire'
    ).all()

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        receptions = receptions.filter(statut=statut)

    # Filtre par bon de commande
    bc_numero = request.GET.get('bc_numero')
    if bc_numero:
        receptions = receptions.filter(bon_commande__numero__icontains=bc_numero)

    # Recherche
    search = request.GET.get('search')
    if search:
        receptions = receptions.filter(
            Q(numero__icontains=search) |
            Q(bon_commande__numero__icontains=search) |
            Q(bon_commande__fournisseur__raison_sociale__icontains=search)
        )

    # Tri
    receptions = receptions.order_by('-date_creation')

    # Pagination
    paginator = Paginator(receptions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculer les statistiques (sur toutes les réceptions, pas juste la page filtrée)
    from django.utils import timezone
    from django.db.models import Count

    all_receptions = GACReception.objects.all()

    stats = {
        'total': all_receptions.count(),
        'brouillon': all_receptions.filter(statut='BROUILLON').count(),
        'validees': all_receptions.filter(statut='VALIDEE').count(),
        'ce_mois': all_receptions.filter(
            date_creation__year=timezone.now().year,
            date_creation__month=timezone.now().month
        ).count(),
    }

    context = {
        'page_obj': page_obj,
        'statut_filter': statut,
        'bc_numero': bc_numero,
        'search': search,
        'stats': stats,
    }

    return render(request, 'gestion_achats/reception/reception_list.html', context)


@login_required
def reception_create(request, bc_pk):
    """Créer une nouvelle réception pour un bon de commande."""
    require_permission(GACPermissions.can_create_reception, request.user)

    bon_commande = get_object_or_404(GACBonCommande, uuid=bc_pk)

    # Vérifier que le BC est dans un état valide pour réception
    if bon_commande.statut not in ['ENVOYE', 'CONFIRME', 'RECU_PARTIEL']:
        messages.error(
            request,
            'Ce bon de commande ne peut pas faire l\'objet d\'une réception.'
        )
        return redirect('gestion_achats:bon_commande_detail', pk=bon_commande.uuid)

    if request.method == 'POST':
        form = ReceptionForm(request.POST, bon_commande=bon_commande)
        if form.is_valid():
            try:
                receptionnaire = request.user.employe if hasattr(request.user, 'employe') else None

                reception = ReceptionService.creer_reception(
                    bon_commande=bon_commande,
                    receptionnaire=receptionnaire,
                    date_reception=form.cleaned_data['date_reception'],
                )

                # Traiter les lignes de réception
                # Note: Les champs sont soumis avec le format ligne_{id}_qte_recue depuis le template
                for ligne_bc in bon_commande.lignes.all():
                    quantite_recue = Decimal(request.POST.get(f'ligne_{ligne_bc.id}_qte_recue', 0) or 0)
                    quantite_acceptee = Decimal(request.POST.get(f'ligne_{ligne_bc.id}_qte_acceptee', 0) or 0)
                    quantite_refusee = Decimal(request.POST.get(f'ligne_{ligne_bc.id}_qte_refusee', 0) or 0)
                    motif_refus = request.POST.get(f'ligne_{ligne_bc.id}_motif_refus', '').strip()

                    if quantite_recue > 0:
                        ligne_reception = GACLigneReception.objects.create(
                            reception=reception,
                            ligne_bon_commande=ligne_bc,
                            quantite_recue=quantite_recue,
                            quantite_acceptee=quantite_acceptee,
                            quantite_refusee=quantite_refusee,
                            motif_refus=motif_refus,
                        )

                messages.success(
                    request,
                    f'Réception {reception.numero} créée avec succès.'
                )
                return redirect('gestion_achats:reception_detail', pk=reception.uuid)

            except Exception as e:
                logger.error(f"Erreur création réception pour BC {bon_commande.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la création de la réception.")
    else:
        form = ReceptionForm(bon_commande=bon_commande)

    context = {
        'form': form,
        'bon_commande': bon_commande,
        'lignes_bc': bon_commande.lignes.all(),
    }

    return render(request, 'gestion_achats/reception/reception_form.html', context)


@login_required
def reception_detail(request, pk):
    """Détail d'une réception."""
    reception = get_object_or_404(
        GACReception.objects.select_related(
            'bon_commande',
            'bon_commande__fournisseur',
            'receptionnaire',
            'validateur'
        ),
        uuid=pk
    )

    require_permission(GACPermissions.can_view_reception, request.user, reception)

    # Récupérer les lignes de réception
    lignes = reception.lignes.select_related(
        'ligne_bon_commande',
        'ligne_bon_commande__article'
    ).all()

    context = {
        'reception': reception,
        'lignes': lignes,
        'bon_commande': reception.bon_commande,
        'can_validate': GACPermissions.can_validate_reception(request.user, reception),
        'can_cancel': GACPermissions.can_cancel_reception(request.user),
    }

    return render(request, 'gestion_achats/reception/reception_detail.html', context)


@login_required
def reception_update(request, pk):
    """Modifier une réception (uniquement si BROUILLON)."""
    require_permission(GACPermissions.can_create_reception, request.user)

    reception = get_object_or_404(GACReception, uuid=pk)

    # Seules les réceptions en brouillon peuvent être modifiées
    if reception.statut != 'BROUILLON':
        messages.error(request, 'Seules les réceptions en brouillon peuvent être modifiées.')
        return redirect('gestion_achats:reception_detail', pk=reception.uuid)

    if request.method == 'POST':
        form = ReceptionForm(request.POST, instance=reception, bon_commande=reception.bon_commande)
        if form.is_valid():
            try:
                # Mettre à jour la réception
                reception.date_reception = form.cleaned_data['date_reception']
                reception.commentaire = form.cleaned_data.get('commentaire', '')
                reception.save()

                # Mettre à jour les lignes
                for ligne in reception.lignes.all():
                    quantite_recue = form.cleaned_data.get(f'quantite_recue_{ligne.ligne_bon_commande.uuid}', ligne.quantite_recue)
                    quantite_acceptee = form.cleaned_data.get(f'quantite_acceptee_{ligne.ligne_bon_commande.uuid}', ligne.quantite_acceptee)
                    quantite_refusee = form.cleaned_data.get(f'quantite_refusee_{ligne.ligne_bon_commande.uuid}', ligne.quantite_refusee)
                    motif_refus = form.cleaned_data.get(f'motif_refus_{ligne.ligne_bon_commande.uuid}', ligne.motif_refus)

                    ligne.quantite_recue = quantite_recue
                    ligne.quantite_acceptee = quantite_acceptee
                    ligne.quantite_refusee = quantite_refusee
                    ligne.motif_refus = motif_refus
                    ligne.save()

                messages.success(request, 'Réception modifiée avec succès.')
                return redirect('gestion_achats:reception_detail', pk=reception.uuid)

            except Exception as e:
                logger.error(f"Erreur modification réception {reception.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la modification de la réception.")
    else:
        form = ReceptionForm(instance=reception, bon_commande=reception.bon_commande)

    context = {
        'form': form,
        'reception': reception,
        'bon_commande': reception.bon_commande,
        'lignes_bc': reception.bon_commande.lignes.all(),
    }

    return render(request, 'gestion_achats/reception/reception_form.html', context)


@login_required
@require_http_methods(["POST"])
def valider_reception(request, pk):
    """Valider une réception."""
    reception = get_object_or_404(GACReception, uuid=pk)

    require_permission(GACPermissions.can_validate_reception, request.user, reception)

    # Vérifier le statut
    if reception.statut != 'BROUILLON':
        messages.error(request, 'Seules les réceptions en brouillon peuvent être validées.')
        return redirect('gestion_achats:reception_detail', pk=reception.uuid)

    try:
        utilisateur = request.user.employe if hasattr(request.user, 'employe') else None

        ReceptionService.valider_reception(
            reception=reception,
            utilisateur=utilisateur
        )

        messages.success(request, f'Réception {reception.numero} validée avec succès.')

    except Exception as e:
        logger.error(f"Erreur validation réception {reception.numero}: {e}", exc_info=True)
        messages.error(request, "Erreur lors de la validation de la réception.")

    return redirect('gestion_achats:reception_detail', pk=reception.uuid)


@login_required
@require_http_methods(["POST"])
def annuler_reception(request, pk):
    """Annuler une réception."""
    require_permission(GACPermissions.can_cancel_reception, request.user)

    reception = get_object_or_404(GACReception, uuid=pk)

    # Vérifier le statut
    if reception.statut == 'ANNULEE':
        messages.error(request, 'Cette réception est déjà annulée.')
        return redirect('gestion_achats:reception_detail', pk=reception.uuid)

    motif = request.POST.get('motif', 'Annulation manuelle')

    try:
        utilisateur = request.user.employe if hasattr(request.user, 'employe') else None

        ReceptionService.annuler_reception(
            reception=reception,
            utilisateur=utilisateur,
            motif=motif
        )

        messages.success(request, f'Réception {reception.numero} annulée.')

    except Exception as e:
        logger.error(f"Erreur annulation réception {reception.numero}: {e}", exc_info=True)
        messages.error(request, "Erreur lors de l'annulation de la réception.")

    return redirect('gestion_achats:reception_detail', pk=reception.uuid)


@login_required
def receptions_en_attente(request):
    """Liste des réceptions en attente de validation."""
    require_permission(GACPermissions.can_view_all_receptions, request.user)

    receptions = ReceptionService.get_receptions_en_attente()

    context = {
        'receptions': receptions,
    }

    return render(request, 'gestion_achats/reception/receptions_en_attente.html', context)
