"""
Vues pour la gestion du catalogue (articles et catégories).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from gestion_achats.models import GACArticle, GACCategorie
from gestion_achats.forms import (
    ArticleForm,
    CategorieForm,
    ArticleFournisseurForm,
)
from gestion_achats.services.catalogue_service import CatalogueService
from gestion_achats.permissions import GACPermissions, require_permission


# ========================================
# VUES ARTICLES
# ========================================

@login_required
def article_list(request):
    """Liste des articles du catalogue."""
    require_permission(GACPermissions.can_view_catalogue, request.user)

    # Récupérer tous les articles
    articles = GACArticle.objects.select_related('categorie').all()

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        articles = articles.filter(statut=statut)

    # Filtre par catégorie
    categorie_uuid = request.GET.get('categorie')
    if categorie_uuid:
        try:
            categorie = GACCategorie.objects.get(uuid=categorie_uuid)
            # Récupérer aussi les sous-catégories
            categories_ids = [categorie.id]
            sous_categories = CatalogueService._get_categories_et_sous_categories(categorie)
            categories_ids.extend([c.id for c in sous_categories])
            articles = articles.filter(categorie_id__in=categories_ids)
        except GACCategorie.DoesNotExist:
            pass

    # Recherche
    search = request.GET.get('search')
    if search:
        articles = articles.filter(
            Q(reference__icontains=search) |
            Q(designation__icontains=search) |
            Q(description__icontains=search)
        )

    # Tri
    articles = articles.order_by('reference')

    # Pagination
    paginator = Paginator(articles, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Récupérer les catégories pour le filtre
    categories = CatalogueService.get_categories_racines()

    context = {
        'page_obj': page_obj,
        'statut_filter': statut,
        'categorie_filter': categorie_uuid,
        'search': search,
        'categories': categories,
    }

    return render(request, 'gestion_achats/catalogue/article_list.html', context)


@login_required
def article_create(request):
    """Créer un nouvel article."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                utilisateur = request.user.employe if hasattr(request.user, 'employe') else None

                article = CatalogueService.creer_article(
                    reference=form.cleaned_data['reference'],
                    designation=form.cleaned_data['designation'],
                    categorie=form.cleaned_data['categorie'],
                    prix_unitaire=form.cleaned_data['prix_unitaire'],
                    unite=form.cleaned_data['unite'],
                    taux_tva=form.cleaned_data.get('taux_tva'),
                    description=form.cleaned_data.get('description', ''),
                    cree_par=utilisateur,
                )

                messages.success(
                    request,
                    f'Article {article.reference} - {article.designation} créé avec succès.'
                )
                return redirect('gestion_achats:article_detail', pk=article.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
    else:
        form = ArticleForm()

    context = {
        'form': form,
        'action': 'Créer',
    }

    return render(request, 'gestion_achats/catalogue/article_form.html', context)


@login_required
def article_detail(request, pk):
    """Détail d'un article."""
    require_permission(GACPermissions.can_view_catalogue, request.user)

    article = get_object_or_404(
        GACArticle.objects.select_related('categorie', 'cree_par'),
        uuid=pk
    )

    # Récupérer les fournisseurs associés
    from gestion_achats.models import GACArticleFournisseur
    article_fournisseurs = GACArticleFournisseur.objects.filter(
        article=article
    ).select_related('fournisseur').order_by('-fournisseur_principal', 'prix_fournisseur')

    # Récupérer les demandes d'achat contenant cet article
    lignes_demandes = article.lignes_demande.select_related(
        'demande_achat'
    ).order_by('-demande_achat__date_creation')[:10]

    context = {
        'article': article,
        'article_fournisseurs': article_fournisseurs,
        'lignes_demandes': lignes_demandes,
        'can_modify': GACPermissions.can_manage_catalogue(request.user),
    }

    return render(request, 'gestion_achats/catalogue/article_detail.html', context)


@login_required
def article_update(request, pk):
    """Modifier un article."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)

    article = get_object_or_404(GACArticle, uuid=pk)

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
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
                    CatalogueService.modifier_article(
                        article=article,
                        utilisateur=utilisateur,
                        **kwargs
                    )

                messages.success(request, 'Article modifié avec succès.')
                return redirect('gestion_achats:article_detail', pk=article.uuid)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = ArticleForm(instance=article)

    context = {
        'form': form,
        'article': article,
        'action': 'Modifier',
    }

    return render(request, 'gestion_achats/catalogue/article_form.html', context)


@login_required
@require_http_methods(["POST"])
def article_desactiver(request, pk):
    """Désactiver un article."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)

    article = get_object_or_404(GACArticle, uuid=pk)
    motif = request.POST.get('motif', 'Désactivation manuelle')

    try:
        utilisateur = request.user.employe if hasattr(request.user, 'employe') else None
        CatalogueService.desactiver_article(
            article=article,
            utilisateur=utilisateur,
            motif=motif
        )
        messages.success(request, f'Article {article.reference} désactivé.')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')

    return redirect('gestion_achats:article_detail', pk=article.uuid)


@login_required
@require_http_methods(["POST"])
def article_reactiver(request, pk):
    """Réactiver un article."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)

    article = get_object_or_404(GACArticle, uuid=pk)

    try:
        utilisateur = request.user.employe if hasattr(request.user, 'employe') else None
        CatalogueService.reactiver_article(
            article=article,
            utilisateur=utilisateur
        )
        messages.success(request, f'Article {article.reference} réactivé.')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')

    return redirect('gestion_achats:article_detail', pk=article.uuid)


# ========================================
# VUES CATÉGORIES
# ========================================

@login_required
def categorie_list(request):
    """Liste des catégories (arborescence)."""
    require_permission(GACPermissions.can_view_catalogue, request.user)

    # Récupérer l'arborescence complète
    arborescence = CatalogueService.get_arborescence_categories()

    # Récupérer les statistiques
    stats = CatalogueService.get_statistiques_catalogue()

    context = {
        'arborescence': arborescence,
        'stats': stats,
        'can_modify': GACPermissions.can_manage_catalogue(request.user),
    }

    return render(request, 'gestion_achats/catalogue/categorie_list.html', context)


@login_required
def categorie_create(request):
    """Créer une nouvelle catégorie."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)

    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            try:
                utilisateur = request.user.employe if hasattr(request.user, 'employe') else None

                categorie = CatalogueService.creer_categorie(
                    nom=form.cleaned_data['nom'],
                    parent=form.cleaned_data.get('parent'),
                    description=form.cleaned_data.get('description', ''),
                    cree_par=utilisateur,
                )

                messages.success(
                    request,
                    f'Catégorie "{categorie.nom}" créée avec succès.'
                )
                return redirect('gestion_achats:categorie_list')

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = CategorieForm()

    context = {
        'form': form,
        'action': 'Créer',
    }

    return render(request, 'gestion_achats/catalogue/categorie_form.html', context)


@login_required
def categorie_update(request, pk):
    """Modifier une catégorie."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)

    categorie = get_object_or_404(GACCategorie, uuid=pk)

    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Catégorie modifiée avec succès.')
                return redirect('gestion_achats:categorie_list')

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = CategorieForm(instance=categorie)

    context = {
        'form': form,
        'categorie': categorie,
        'action': 'Modifier',
    }

    return render(request, 'gestion_achats/catalogue/categorie_form.html', context)


# ========================================
# VUES API AJAX
# ========================================

@login_required
def recherche_articles_ajax(request):
    """API AJAX pour la recherche d'articles."""
    query = request.GET.get('q', '')
    categorie_uuid = request.GET.get('categorie')
    limit = int(request.GET.get('limit', 20))

    try:
        categorie = None
        if categorie_uuid:
            categorie = GACCategorie.objects.get(uuid=categorie_uuid)

        articles = CatalogueService.rechercher_articles(
            query=query,
            categorie=categorie,
            actif_uniquement=True
        )[:limit]

        data = [
            {
                'uuid': str(article.uuid),
                'reference': article.reference,
                'designation': article.designation,
                'categorie': article.categorie.nom,
                'prix_unitaire': float(article.prix_unitaire),
                'unite': article.unite,
                'taux_tva': float(article.taux_tva),
            }
            for article in articles
        ]

        return JsonResponse({'success': True, 'articles': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
