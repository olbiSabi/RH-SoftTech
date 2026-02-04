"""
Vues pour la gestion des fournisseurs.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from gestion_achats.models import GACFournisseur, GACArticle
from gestion_achats.forms import (
    FournisseurForm,
    FournisseurEvaluationForm,
)
from gestion_achats.services.fournisseur_service import FournisseurService
from gestion_achats.permissions import GACPermissions, require_permission


@login_required
def fournisseur_list(request):
    """Liste des fournisseurs."""
    require_permission(GACPermissions.can_view_fournisseur, request.user)

    # Récupérer tous les fournisseurs
    fournisseurs = GACFournisseur.objects.all()

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        fournisseurs = fournisseurs.filter(statut=statut)

    # Recherche
    search = request.GET.get('search')
    if search:
        fournisseurs = fournisseurs.filter(
            Q(code__icontains=search) |
            Q(raison_sociale__icontains=search) |
            Q(nif__icontains=search) |
            Q(email__icontains=search)
        )

    # Tri
    fournisseurs = fournisseurs.order_by('raison_sociale')

    # Pagination
    paginator = Paginator(fournisseurs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'statut_filter': statut,
        'search': search,
    }

    return render(request, 'gestion_achats/fournisseur/fournisseur_list.html', context)


@login_required
def fournisseur_create(request):
    """Créer un nouveau fournisseur."""
    require_permission(GACPermissions.can_modify_fournisseur, request.user)

    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            try:
                fournisseur = FournisseurService.creer_fournisseur(
                    raison_sociale=form.cleaned_data['raison_sociale'],
                    email=form.cleaned_data['email'],
                    telephone=form.cleaned_data['telephone'],
                    adresse=form.cleaned_data['adresse'],
                    nif=form.cleaned_data.get('nif'),
                    code_postal=form.cleaned_data.get('code_postal'),
                    ville=form.cleaned_data.get('ville'),
                    pays=form.cleaned_data.get('pays', 'Togo'),
                    conditions_paiement=form.cleaned_data.get('conditions_paiement'),
                    nom_contact=form.cleaned_data.get('nom_contact'),
                    email_contact=form.cleaned_data.get('email_contact'),
                    telephone_contact=form.cleaned_data.get('telephone_contact'),
                    iban=form.cleaned_data.get('iban'),
                    numero_tva=form.cleaned_data.get('numero_tva'),
                    fax=form.cleaned_data.get('fax'),
                    cree_par=request.user.employe if hasattr(request.user, 'employe') else None,
                )

                messages.success(
                    request,
                    f'Fournisseur {fournisseur.code} - {fournisseur.raison_sociale} créé avec succès.'
                )
                return redirect('gestion_achats:fournisseur_detail', pk=fournisseur.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
    else:
        form = FournisseurForm()

    return render(request, 'gestion_achats/fournisseur/fournisseur_form.html', {
        'form': form,
        'action': 'Créer',
    })


@login_required
def fournisseur_detail(request, pk):
    """Détail d'un fournisseur."""
    require_permission(GACPermissions.can_view_fournisseur, request.user)

    fournisseur = get_object_or_404(GACFournisseur, uuid=pk)

    # Récupérer les statistiques
    try:
        stats = FournisseurService.get_statistiques_fournisseur(fournisseur)
    except Exception:
        stats = {}

    # Récupérer les bons de commande récents
    bons_commande = fournisseur.bons_commande.order_by('-date_creation')[:10]

    # Récupérer les articles fournis
    articles = fournisseur.articles.filter(statut='ACTIF')[:20]

    context = {
        'fournisseur': fournisseur,
        'stats': stats,
        'bons_commande': bons_commande,
        'articles': articles,
        'can_modify': GACPermissions.can_modify_fournisseur(request.user),
        'can_evaluate': GACPermissions.can_evaluate_fournisseur(request.user),
    }

    return render(request, 'gestion_achats/fournisseur/fournisseur_detail.html', context)


@login_required
def fournisseur_update(request, pk):
    """Modifier un fournisseur."""
    require_permission(GACPermissions.can_modify_fournisseur, request.user)

    fournisseur = get_object_or_404(GACFournisseur, uuid=pk)

    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            try:
                utilisateur = request.user.employe if hasattr(request.user, 'employe') else None

                # Préparer les données à modifier
                kwargs = {
                    key: form.cleaned_data[key]
                    for key in form.cleaned_data
                    if key in form.changed_data
                }

                if kwargs:
                    FournisseurService.modifier_fournisseur(
                        fournisseur=fournisseur,
                        utilisateur=utilisateur,
                        **kwargs
                    )

                messages.success(request, 'Fournisseur modifié avec succès.')
                return redirect('gestion_achats:fournisseur_detail', pk=fournisseur.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de la modification: {str(e)}')
    else:
        form = FournisseurForm(instance=fournisseur)

    return render(request, 'gestion_achats/fournisseur/fournisseur_form.html', {
        'form': form,
        'fournisseur': fournisseur,
        'action': 'Modifier',
    })


@login_required
@require_http_methods(["POST"])
def fournisseur_suspend(request, pk):
    """Suspendre un fournisseur."""
    require_permission(GACPermissions.can_modify_fournisseur, request.user)

    fournisseur = get_object_or_404(GACFournisseur, uuid=pk)
    motif = request.POST.get('motif', 'Suspension manuelle')

    try:
        utilisateur = request.user.employe if hasattr(request.user, 'employe') else None
        FournisseurService.suspendre_fournisseur(
            fournisseur=fournisseur,
            utilisateur=utilisateur,
            motif=motif
        )
        messages.success(request, f'Fournisseur {fournisseur.raison_sociale} suspendu.')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')

    return redirect('gestion_achats:fournisseur_detail', pk=fournisseur.uuid)


@login_required
@require_http_methods(["POST"])
def fournisseur_reactivate(request, pk):
    """Réactiver un fournisseur."""
    require_permission(GACPermissions.can_modify_fournisseur, request.user)

    fournisseur = get_object_or_404(GACFournisseur, uuid=pk)

    try:
        utilisateur = request.user.employe if hasattr(request.user, 'employe') else None
        FournisseurService.reactiver_fournisseur(
            fournisseur=fournisseur,
            utilisateur=utilisateur
        )
        messages.success(request, f'Fournisseur {fournisseur.raison_sociale} réactivé.')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')

    return redirect('gestion_achats:fournisseur_detail', pk=fournisseur.uuid)


@login_required
def evaluer_fournisseur(request, pk):
    """Évaluer un fournisseur."""
    require_permission(GACPermissions.can_evaluate_fournisseur, request.user)

    fournisseur = get_object_or_404(GACFournisseur, uuid=pk)

    if request.method == 'POST':
        form = FournisseurEvaluationForm(request.POST)
        if form.is_valid():
            try:
                evaluateur = request.user.employe if hasattr(request.user, 'employe') else None

                FournisseurService.evaluer_fournisseur(
                    fournisseur=fournisseur,
                    evaluateur=evaluateur,
                    note_qualite=form.cleaned_data['note_qualite'],
                    note_delai=form.cleaned_data['note_delai'],
                    note_prix=form.cleaned_data['note_prix'],
                    commentaire=form.cleaned_data.get('commentaire', '')
                )

                messages.success(request, 'Évaluation enregistrée avec succès.')
                return redirect('gestion_achats:fournisseur_detail', pk=fournisseur.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de l\'évaluation: {str(e)}')
        else:
            # Afficher les erreurs de validation du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = FournisseurEvaluationForm()

    context = {
        'form': form,
        'fournisseur': fournisseur,
    }

    return render(request, 'gestion_achats/fournisseur/evaluer.html', context)


@login_required
def fournisseurs_pour_article_ajax(request, article_pk):
    """API AJAX pour récupérer les fournisseurs d'un article."""
    try:
        article = get_object_or_404(GACArticle, uuid=article_pk)
        fournisseurs = FournisseurService.get_fournisseurs_pour_article(article)

        data = [
            {
                'uuid': str(f['fournisseur__uuid']),
                'code': f['fournisseur__code'],
                'raison_sociale': f['fournisseur__raison_sociale'],
                'prix': float(f['prix_fournisseur']),
                'delai': f['delai_livraison'],
                'principal': f['fournisseur_principal'],
            }
            for f in fournisseurs
        ]

        return JsonResponse({'success': True, 'fournisseurs': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def fournisseur_delete(request, pk):
    """Supprimer un fournisseur."""
    require_permission(GACPermissions.can_delete_fournisseur, request.user)

    fournisseur = get_object_or_404(GACFournisseur, uuid=pk)

    try:
        raison_sociale = fournisseur.raison_sociale
        fournisseur.delete()
        messages.success(request, f'Le fournisseur "{raison_sociale}" a été supprimé avec succès.')
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression: {str(e)}')

    return redirect('gestion_achats:fournisseur_list')
