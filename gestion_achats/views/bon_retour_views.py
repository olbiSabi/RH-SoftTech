"""
Vues pour la gestion des bons de retour fournisseur.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from decimal import Decimal

from gestion_achats.models import GACBonRetour, GACReception, GACLigneReception
from gestion_achats.services.reception_service import ReceptionService
from gestion_achats.permissions import GACPermissions, require_permission


@login_required
def bon_retour_list(request):
    """Liste des bons de retour."""
    # Filtrer selon les permissions
    if GACPermissions.can_view_all_bons_commande(request.user):
        bons_retour = GACBonRetour.objects.all()
    else:
        # Voir les bons de retour liés aux demandes de l'utilisateur
        bons_retour = GACBonRetour.objects.filter(
            bon_commande__demande_achat__demandeur=request.user.employe
        )

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        bons_retour = bons_retour.filter(statut=statut)

    fournisseur = request.GET.get('fournisseur')
    if fournisseur:
        bons_retour = bons_retour.filter(fournisseur_id=fournisseur)

    search = request.GET.get('search')
    if search:
        bons_retour = bons_retour.filter(
            Q(numero__icontains=search) |
            Q(fournisseur__raison_sociale__icontains=search) |
            Q(motif_retour__icontains=search)
        )

    bons_retour = bons_retour.select_related(
        'fournisseur',
        'reception',
        'bon_commande',
        'cree_par'
    ).order_by('-date_creation')

    # Pagination
    paginator = Paginator(bons_retour, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'gestion_achats/bon_retour/bon_retour_list.html', {
        'page_obj': page_obj,
        'statut_filter': statut,
        'fournisseur_filter': fournisseur,
        'search': search,
    })


@login_required
def bon_retour_detail(request, pk):
    """Détail d'un bon de retour."""
    bon_retour = get_object_or_404(
        GACBonRetour.objects.select_related(
            'fournisseur',
            'reception',
            'bon_commande',
            'cree_par',
            'emis_par'
        ),
        uuid=pk
    )

    # Vérifier les permissions
    require_permission(GACPermissions.can_view_bon_commande, request.user, bon_retour.bon_commande)

    lignes = bon_retour.lignes.select_related(
        'article',
        'ligne_reception__ligne_bon_commande'
    ).order_by('ordre')

    return render(request, 'gestion_achats/bon_retour/bon_retour_detail.html', {
        'bon_retour': bon_retour,
        'lignes': lignes,
        'can_modify': bon_retour.statut == 'BROUILLON' and GACPermissions.can_create_reception(request.user),
    })


@login_required
def bon_retour_create_from_reception(request, reception_pk):
    """Créer un bon de retour depuis une réception."""
    reception = get_object_or_404(
        GACReception.objects.select_related('bon_commande__fournisseur'),
        uuid=reception_pk
    )

    require_permission(GACPermissions.can_create_reception, request.user)

    # Vérifier que la réception est validée
    if reception.statut != 'VALIDEE':
        messages.error(request, 'Seules les réceptions validées peuvent générer des bons de retour.')
        return redirect('gestion_achats:reception_detail', pk=reception.uuid)

    # Récupérer les lignes avec quantité refusée
    lignes_non_conformes = reception.lignes.filter(
        quantite_refusee__gt=0
    ).select_related('ligne_bon_commande__article')

    if not lignes_non_conformes.exists():
        messages.warning(request, 'Cette réception ne contient aucun article refusé.')
        return redirect('gestion_achats:reception_detail', pk=reception.uuid)

    if request.method == 'POST':
        motif_retour = request.POST.get('motif_retour', '')
        if not motif_retour:
            messages.error(request, 'Le motif de retour est obligatoire.')
        else:
            try:
                # Construire la liste des lignes à retourner
                lignes_a_retourner = []
                for ligne in lignes_non_conformes:
                    quantite_key = f'quantite_retour_{ligne.pk}'
                    quantite_str = request.POST.get(quantite_key, '0')

                    try:
                        quantite = Decimal(quantite_str)
                        if quantite > 0:
                            lignes_a_retourner.append((ligne, quantite))
                    except (ValueError, TypeError):
                        pass

                if not lignes_a_retourner:
                    messages.error(request, 'Aucune ligne à retourner n\'a été spécifiée.')
                else:
                    # Créer le bon de retour
                    bon_retour = ReceptionService.creer_bon_retour(
                        reception=reception,
                        lignes_non_conformes=lignes_a_retourner,
                        motif_retour=motif_retour,
                        utilisateur=request.user.employe
                    )

                    messages.success(
                        request,
                        f'Bon de retour {bon_retour.numero} créé avec succès.'
                    )
                    return redirect('gestion_achats:bon_retour_detail', pk=bon_retour.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de la création : {str(e)}')

    return render(request, 'gestion_achats/bon_retour/bon_retour_create.html', {
        'reception': reception,
        'lignes_non_conformes': lignes_non_conformes,
    })


@login_required
def bon_retour_emit(request, pk):
    """Émettre un bon de retour."""
    bon_retour = get_object_or_404(GACBonRetour, uuid=pk)

    require_permission(GACPermissions.can_create_reception, request.user)

    if bon_retour.statut != 'BROUILLON':
        messages.error(request, 'Seuls les bons de retour en brouillon peuvent être émis.')
        return redirect('gestion_achats:bon_retour_detail', pk=bon_retour.uuid)

    if request.method == 'POST':
        try:
            from django.utils import timezone
            from gestion_achats.models import GACHistorique

            bon_retour.statut = 'EMIS'
            bon_retour.date_emission = timezone.now()
            bon_retour.emis_par = request.user.employe
            bon_retour.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=bon_retour,
                action='EMISSION',
                utilisateur=request.user.employe,
                details=f"Bon de retour {bon_retour.numero} émis"
            )

            messages.success(request, f'Bon de retour {bon_retour.numero} émis.')
            return redirect('gestion_achats:bon_retour_detail', pk=bon_retour.uuid)

        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    return render(request, 'gestion_achats/bon_retour/bon_retour_confirm.html', {
        'bon_retour': bon_retour,
        'action': 'émettre',
    })


@login_required
def bon_retour_send(request, pk):
    """Marquer un bon de retour comme envoyé au fournisseur."""
    bon_retour = get_object_or_404(GACBonRetour, uuid=pk)

    require_permission(GACPermissions.can_create_reception, request.user)

    if bon_retour.statut != 'EMIS':
        messages.error(request, 'Seuls les bons de retour émis peuvent être envoyés.')
        return redirect('gestion_achats:bon_retour_detail', pk=bon_retour.uuid)

    if request.method == 'POST':
        try:
            from django.utils import timezone
            from gestion_achats.models import GACHistorique

            bon_retour.statut = 'ENVOYE'
            bon_retour.date_envoi = timezone.now()
            bon_retour.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=bon_retour,
                action='ENVOI',
                utilisateur=request.user.employe,
                details=f"Bon de retour {bon_retour.numero} envoyé au fournisseur"
            )

            messages.success(request, f'Bon de retour {bon_retour.numero} marqué comme envoyé.')
            return redirect('gestion_achats:bon_retour_detail', pk=bon_retour.uuid)

        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    return render(request, 'gestion_achats/bon_retour/bon_retour_confirm.html', {
        'bon_retour': bon_retour,
        'action': 'marquer comme envoyé',
    })


@login_required
def bon_retour_receive(request, pk):
    """Marquer un bon de retour comme reçu par le fournisseur."""
    bon_retour = get_object_or_404(GACBonRetour, uuid=pk)

    require_permission(GACPermissions.can_create_reception, request.user)

    if bon_retour.statut != 'ENVOYE':
        messages.error(request, 'Seuls les bons de retour envoyés peuvent être marqués comme reçus.')
        return redirect('gestion_achats:bon_retour_detail', pk=bon_retour.uuid)

    if request.method == 'POST':
        try:
            from django.utils import timezone
            from gestion_achats.models import GACHistorique

            bon_retour.statut = 'RECU_FOURNISSEUR'
            bon_retour.date_reception_fournisseur = timezone.now()
            bon_retour.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=bon_retour,
                action='RECEPTION',
                utilisateur=request.user.employe,
                details=f"Bon de retour {bon_retour.numero} reçu par le fournisseur"
            )

            messages.success(request, f'Bon de retour {bon_retour.numero} marqué comme reçu.')
            return redirect('gestion_achats:bon_retour_detail', pk=bon_retour.uuid)

        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    return render(request, 'gestion_achats/bon_retour/bon_retour_confirm.html', {
        'bon_retour': bon_retour,
        'action': 'marquer comme reçu par le fournisseur',
    })
