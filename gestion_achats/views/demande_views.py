"""
Vues pour la gestion des demandes d'achat.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from gestion_achats.models import GACDemandeAchat, GACLigneDemandeAchat
from gestion_achats.forms import (
    DemandeAchatForm,
    LigneDemandeAchatForm,
    DemandeValidationForm,
    DemandeRefusForm,
    DemandeAnnulationForm,
)
from gestion_achats.services import DemandeService
from gestion_achats.decorators import require_demande_access, ajax_login_required
from gestion_achats.permissions import GACPermissions, require_permission

import logging
logger = logging.getLogger(__name__)


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
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

            except Exception as e:
                logger.error(f"Erreur création demande: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la création de la demande. Veuillez vérifier les données saisies.")
    else:
        form = DemandeAchatForm(user=request.user)

    return render(request, 'gestion_achats/demande/demande_form.html', {
        'form': form,
        'action': 'Créer',
    })


@ajax_login_required
@require_demande_access
def demande_detail(request, pk, **kwargs):
    """Détail d'une demande d'achat."""
    demande = kwargs.get('demande')
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


@ajax_login_required
@require_demande_access
def demande_update(request, pk, **kwargs):
    """Modifier une demande d'achat."""
    demande = kwargs.get('demande')
    require_permission(GACPermissions.can_modify_demande, request.user, demande)

    if request.method == 'POST':
        form = DemandeAchatForm(request.POST, instance=demande, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Demande modifiée avec succès.')
            return redirect('gestion_achats:demande_detail', pk=demande.uuid)
    else:
        form = DemandeAchatForm(instance=demande, user=request.user)

    return render(request, 'gestion_achats/demande/demande_form.html', {
        'form': form,
        'demande': demande,
        'action': 'Modifier',
    })


@ajax_login_required
@require_demande_access
def demande_delete(request, pk, **kwargs):
    """Supprimer une demande d'achat (seulement si elle est en brouillon)."""
    demande = kwargs.get('demande')
    require_permission(GACPermissions.can_modify_demande, request.user, demande)

    # Vérifier que la demande est en brouillon
    if demande.statut != 'BROUILLON':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Seules les demandes en brouillon peuvent être supprimées.'
            }, status=400)
        messages.error(request, 'Seules les demandes en brouillon peuvent être supprimées.')
        return redirect('gestion_achats:demande_detail', pk=demande.uuid)

    if request.method == 'POST':
        # Gérer les requêtes AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                numero = demande.numero
                demande.delete()

                return JsonResponse({
                    'success': True,
                    'message': f'Demande {numero} supprimée avec succès.',
                    'redirect_url': reverse('gestion_achats:mes_demandes')
                })

            except Exception as e:
                logger.error(f"Erreur suppression demande (AJAX): {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': "Erreur lors de la suppression de la demande."
                }, status=400)

        # Gérer les requêtes normales (formulaire)
        try:
            numero = demande.numero
            demande.delete()

            messages.success(request, f'Demande {numero} supprimée avec succès.')
            return redirect('gestion_achats:mes_demandes')

        except Exception as e:
            logger.error(f"Erreur suppression demande {demande.numero}: {e}", exc_info=True)
            messages.error(request, "Erreur lors de la suppression de la demande.")
            return redirect('gestion_achats:demande_detail', pk=demande.uuid)

    return render(request, 'gestion_achats/demande/demande_confirm_delete.html', {
        'demande': demande,
    })


@ajax_login_required
@require_demande_access
def demande_ligne_create(request, pk, **kwargs):
    """Ajouter une ligne à une demande."""
    demande = kwargs.get('demande')
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
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

            except Exception as e:
                logger.error(f"Erreur ajout ligne demande {demande.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de l'ajout de la ligne. Veuillez vérifier les données.")
    else:
        form = LigneDemandeAchatForm()

    return render(request, 'gestion_achats/demande/ligne_form.html', {
        'form': form,
        'demande': demande,
    })


@ajax_login_required
@require_demande_access
def demande_ligne_update(request, pk, ligne_pk, **kwargs):
    """Modifier une ligne de demande."""
    demande = kwargs.get('demande')
    require_permission(GACPermissions.can_modify_demande, request.user, demande)

    ligne = get_object_or_404(GACLigneDemandeAchat, pk=ligne_pk, demande_achat=demande)

    if request.method == 'POST':
        form = LigneDemandeAchatForm(request.POST, instance=ligne)
        if form.is_valid():
            try:
                ligne.article = form.cleaned_data['article']
                ligne.quantite = form.cleaned_data['quantite']
                ligne.prix_unitaire = form.cleaned_data['prix_unitaire']
                ligne.taux_tva = form.cleaned_data.get('taux_tva')
                ligne.commentaire = form.cleaned_data.get('commentaire', '')
                ligne.save()

                # Recalculer les montants de la demande
                demande.save()

                messages.success(request, 'Ligne modifiée avec succès.')
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

            except Exception as e:
                logger.error(f"Erreur modification ligne demande {demande.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la modification de la ligne.")
    else:
        form = LigneDemandeAchatForm(instance=ligne)

    return render(request, 'gestion_achats/demande/ligne_form.html', {
        'form': form,
        'demande': demande,
        'ligne': ligne,
        'action': 'Modifier',
    })


@ajax_login_required
@require_demande_access
def demande_ligne_delete(request, pk, ligne_pk, **kwargs):
    """Supprimer une ligne de demande."""
    demande = kwargs.get('demande')
    require_permission(GACPermissions.can_modify_demande, request.user, demande)

    ligne = get_object_or_404(GACLigneDemandeAchat, pk=ligne_pk, demande_achat=demande)

    if request.method == 'POST':
        # Gérer les requêtes AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                ligne.delete()
                # Recalculer les montants de la demande
                demande.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Ligne supprimée avec succès.',
                    'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
                })

            except Exception as e:
                logger.error(f"Erreur suppression ligne demande (AJAX): {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': "Erreur lors de la suppression de la ligne."
                }, status=400)

        # Gérer les requêtes normales (formulaire)
        try:
            ligne.delete()
            # Recalculer les montants de la demande
            demande.save()

            messages.success(request, 'Ligne supprimée avec succès.')
            return redirect('gestion_achats:demande_detail', pk=demande.uuid)

        except Exception as e:
            logger.error(f"Erreur suppression ligne demande {demande.numero}: {e}", exc_info=True)
            messages.error(request, "Erreur lors de la suppression de la ligne.")
            return redirect('gestion_achats:demande_detail', pk=demande.uuid)

    return render(request, 'gestion_achats/demande/ligne_confirm_delete.html', {
        'ligne': ligne,
        'demande': demande,
    })


@ajax_login_required
def demande_submit(request, pk):
    """Soumettre une demande pour validation."""
    # Charger la demande manuellement (on ne utilise plus le décorateur qui causait des problèmes)
    demande = get_object_or_404(GACDemandeAchat, uuid=pk)

    if request.method == 'POST':
        try:
            # Vérifier les permissions (dans le try/except pour capturer les erreurs)
            if not GACPermissions.can_submit_demande(request.user, demande):
                raise PermissionDenied("Vous n'avez pas la permission de soumettre cette demande.")

            # Vérifier que l'utilisateur a un employe
            if not hasattr(request.user, 'employe') or not request.user.employe:
                raise ValueError("Votre compte n'est pas associé à un employé.")

            DemandeService.soumettre_demande(demande, request.user.employe)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Requête AJAX - retourner JSON
                return JsonResponse({
                    'success': True,
                    'message': f'Demande {demande.numero} soumise pour validation.',
                    'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
                })
            else:
                # Requête normale - retourner message et redirect
                try:
                    messages.success(
                        request,
                        f'Demande {demande.numero} soumise pour validation.'
                    )
                except Exception:
                    # Si le middleware messages n'est pas disponible, continuer sans message
                    pass
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

        except PermissionDenied as e:
            # Gérer spécifiquement les erreurs de permission
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': "Vous n'avez pas la permission de soumettre cette demande."
                }, status=403)
            else:
                messages.error(request, "Vous n'avez pas la permission de soumettre cette demande.")
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

        except Exception as e:
            logger.error(f"Erreur soumission demande {demande.numero}: {e}", exc_info=True)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': "Erreur lors de la soumission. Veuillez réessayer."
                }, status=400)
            else:
                try:
                    messages.error(request, "Erreur lors de la soumission. Veuillez réessayer.")
                except Exception:
                    pass
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

    # Pour les requêtes GET normales, rediriger vers le détail (la modale gérera la confirmation)
    return redirect('gestion_achats:demande_detail', pk=demande.uuid)


@login_required
def demande_validate_n1(request, pk, **kwargs):
    """Valider une demande au niveau N1."""
    # Charger la demande manuellement
    demande = get_object_or_404(GACDemandeAchat, uuid=pk)

    # Vérifier les permissions
    if not GACPermissions.can_view_demande(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas accès à cette demande"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas accès à cette demande")

    if not GACPermissions.can_validate_n1(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas la permission de valider cette demande au niveau N1"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas la permission de valider cette demande au niveau N1")

    if request.method == 'POST':
        # Gérer les requêtes AJAX (JSON)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                import json
                data = json.loads(request.body)
                commentaire = data.get('commentaire', '')

                DemandeService.valider_n1(
                    demande,
                    request.user.employe,
                    commentaire=commentaire
                )

                return JsonResponse({
                    'success': True,
                    'message': f'Demande {demande.numero} validée (N1).',
                    'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
                })

            except Exception as e:
                logger.error(f"Erreur validation N1 demande {demande.numero} (AJAX): {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': "Erreur lors de la validation. Veuillez réessayer."
                }, status=400)

        # Gérer les requêtes normales (formulaire)
        form = DemandeValidationForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.valider_n1(
                    demande,
                    request.user.employe,
                    commentaire=form.cleaned_data.get('commentaire', '')
                )

                messages.success(request, f'Demande {demande.numero} validée (N1).')
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

            except Exception as e:
                logger.error(f"Erreur validation N1 demande {demande.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la validation. Veuillez réessayer.")
    else:
        form = DemandeValidationForm()

    return render(request, 'gestion_achats/demande/demande_validation.html', {
        'form': form,
        'demande': demande,
        'niveau': 'N1',
    })


@login_required
def demande_validate_n2(request, pk, **kwargs):
    """Valider une demande au niveau N2."""
    # Charger la demande manuellement
    demande = get_object_or_404(GACDemandeAchat, uuid=pk)

    # Vérifier les permissions
    if not GACPermissions.can_view_demande(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas accès à cette demande"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas accès à cette demande")

    if not GACPermissions.can_validate_n2(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas la permission de valider cette demande au niveau N2"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas la permission de valider cette demande au niveau N2")

    if request.method == 'POST':
        # Gérer les requêtes AJAX (JSON)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                import json
                data = json.loads(request.body)
                commentaire = data.get('commentaire', '')

                DemandeService.valider_n2(
                    demande,
                    request.user.employe,
                    commentaire=commentaire
                )

                return JsonResponse({
                    'success': True,
                    'message': f'Demande {demande.numero} validée (N2).',
                    'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
                })

            except Exception as e:
                logger.error(f"Erreur validation N2 demande {demande.numero} (AJAX): {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': "Erreur lors de la validation. Veuillez réessayer."
                }, status=400)

        # Gérer les requêtes normales (formulaire)
        form = DemandeValidationForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.valider_n2(
                    demande,
                    request.user.employe,
                    commentaire=form.cleaned_data.get('commentaire', '')
                )

                messages.success(request, f'Demande {demande.numero} validée (N2).')
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

            except Exception as e:
                logger.error(f"Erreur validation N2 demande {demande.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la validation. Veuillez réessayer.")
    else:
        form = DemandeValidationForm()

    return render(request, 'gestion_achats/demande/demande_validation.html', {
        'form': form,
        'demande': demande,
        'niveau': 'N2',
    })


@login_required
def demande_refuse(request, pk, **kwargs):
    """Refuser une demande."""
    # Charger la demande manuellement
    demande = get_object_or_404(GACDemandeAchat, uuid=pk)

    # Vérifier les permissions
    if not GACPermissions.can_view_demande(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas accès à cette demande"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas accès à cette demande")

    if not GACPermissions.can_refuse_demande(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas la permission de refuser cette demande"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas la permission de refuser cette demande")

    if request.method == 'POST':
        # Gérer les requêtes AJAX (JSON)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                import json
                data = json.loads(request.body)
                motif = data.get('motif', '')

                if not motif:
                    return JsonResponse({
                        'success': False,
                        'message': 'Le motif de refus est obligatoire'
                    }, status=400)

                DemandeService.refuser_demande(
                    demande,
                    request.user.employe,
                    motif=motif
                )

                return JsonResponse({
                    'success': True,
                    'message': f'Demande {demande.numero} refusée.',
                    'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
                })

            except Exception as e:
                logger.error(f"Erreur refus demande {demande.numero} (AJAX): {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': "Erreur lors du refus. Veuillez réessayer."
                }, status=400)

        # Gérer les requêtes normales (formulaire)
        form = DemandeRefusForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.refuser_demande(
                    demande,
                    request.user.employe,
                    motif=form.cleaned_data['motif_refus']
                )

                messages.warning(request, f'Demande {demande.numero} refusée.')
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

            except Exception as e:
                logger.error(f"Erreur refus demande {demande.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors du refus de la demande.")
    else:
        form = DemandeRefusForm()

    return render(request, 'gestion_achats/demande/demande_refus.html', {
        'form': form,
        'demande': demande,
    })


@login_required
def demande_cancel(request, pk, **kwargs):
    """Annuler une demande."""
    # Charger la demande manuellement
    demande = get_object_or_404(GACDemandeAchat, uuid=pk)

    # Vérifier les permissions
    if not GACPermissions.can_view_demande(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas accès à cette demande"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas accès à cette demande")

    if not GACPermissions.can_cancel_demande(request.user, demande):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Vous n'avez pas la permission d'annuler cette demande"
            }, status=403)
        raise PermissionDenied("Vous n'avez pas la permission d'annuler cette demande")

    if request.method == 'POST':
        # Gérer les requêtes AJAX (JSON)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                import json
                data = json.loads(request.body)
                motif = data.get('motif', '')

                if not motif:
                    return JsonResponse({
                        'success': False,
                        'message': 'Le motif d\'annulation est obligatoire'
                    }, status=400)

                DemandeService.annuler_demande(
                    demande,
                    request.user.employe,
                    motif=motif
                )

                return JsonResponse({
                    'success': True,
                    'message': f'Demande {demande.numero} annulée.',
                    'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
                })

            except Exception as e:
                logger.error(f"Erreur annulation demande {demande.numero} (AJAX): {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': "Erreur lors de l'annulation. Veuillez réessayer."
                }, status=400)

        # Gérer les requêtes normales (formulaire)
        form = DemandeAnnulationForm(request.POST)
        if form.is_valid():
            try:
                DemandeService.annuler_demande(
                    demande,
                    request.user.employe,
                    motif=form.cleaned_data['motif_annulation']
                )

                messages.warning(request, f'Demande {demande.numero} annulée.')
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

            except Exception as e:
                logger.error(f"Erreur annulation demande {demande.numero}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de l'annulation de la demande.")
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
