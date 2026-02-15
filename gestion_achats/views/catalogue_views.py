"""
Vues pour la gestion du catalogue (articles et catégories).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from gestion_achats.models import GACArticle, GACCategorie
from gestion_achats.forms import (
    ArticleForm,
    CategorieForm,
    ArticleFournisseurForm,
)
from gestion_achats.services.catalogue_service import CatalogueService
from gestion_achats.permissions import GACPermissions, require_permission

import logging
logger = logging.getLogger(__name__)


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
        except (GACCategorie.DoesNotExist, ValueError, ValidationError):
            # Gère à la fois les UUID non trouvés et les UUID invalides
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

    # Calculer les statistiques
    stats = {
        'total': GACArticle.objects.count(),
        'actifs': GACArticle.objects.filter(statut='ACTIF').count(),
        'inactifs': GACArticle.objects.filter(statut='INACTIF').count(),
        'nb_categories': GACCategorie.objects.count(),
    }

    context = {
        'page_obj': page_obj,
        'statut_filter': statut,
        'categorie_filter': categorie_uuid,
        'search': search,
        'categories': categories,
        'stats': stats,
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
                logger.error(f"Erreur création article: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la création de l'article.")
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

    # Calculer les statistiques de commandes
    from gestion_achats.models import GACLigneBonCommande
    lignes_commandes = GACLigneBonCommande.objects.filter(
        article=article
    ).select_related('bon_commande', 'bon_commande__fournisseur')
    
    # Statistiques
    stats = {
        'nb_commandes': lignes_commandes.count(),
        'qte_totale': lignes_commandes.aggregate(
            total=Sum('quantite_commandee')
        )['total'] or 0,
        'montant_total': lignes_commandes.aggregate(
            total=Sum('montant_ttc')
        )['total'] or 0,
    }

    # Commandes récentes (limitées à 10)
    commandes_recentes = lignes_commandes.order_by(
        '-bon_commande__date_emission'
    )[:10]

    context = {
        'article': article,
        'article_fournisseurs': article_fournisseurs,
        'lignes_demandes': lignes_demandes,
        'commandes_recentes': commandes_recentes,
        'stats': stats,
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
                logger.error(f"Erreur modification article {article.reference}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la modification de l'article.")
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
        logger.error(f"Erreur désactivation article {article.reference}: {e}", exc_info=True)
        messages.error(request, "Erreur lors de la désactivation de l'article.")

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
        logger.error(f"Erreur réactivation article {article.reference}: {e}", exc_info=True)
        messages.error(request, "Erreur lors de la réactivation de l'article.")

    return redirect('gestion_achats:article_detail', pk=article.uuid)


@login_required
@require_http_methods(["POST"])
def article_delete(request, pk):
    """Supprimer un article."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)

    article = get_object_or_404(GACArticle, uuid=pk)

    # Vérifications avant suppression
    if article.lignes_demande.exists():
        messages.error(request, 'Impossible de supprimer un article utilisé dans des demandes d\'achat.')
        return redirect('gestion_achats:article_detail', pk=article.uuid)
    
    if article.lignes_bc.exists():
        messages.error(request, 'Impossible de supprimer un article utilisé dans des bons de commande.')
        return redirect('gestion_achats:article_detail', pk=article.uuid)
    
    # Vérifier si les lignes de BC de cet article ont des réceptions
    from gestion_achats.models import GACLigneReception
    lignes_bc_article = article.lignes_bc.all()
    if GACLigneReception.objects.filter(ligne_bon_commande__in=lignes_bc_article).exists():
        messages.error(request, 'Impossible de supprimer un article utilisé dans des réceptions.')
        return redirect('gestion_achats:article_detail', pk=article.uuid)

    try:
        reference = article.reference
        designation = article.designation
        
        # Supprimer l'article
        article.delete()
        
        messages.success(request, f'Article {reference} - {designation} supprimé avec succès.')
        return redirect('gestion_achats:article_list')
        
    except Exception as e:
        logger.error(f"Erreur suppression article {article.reference}: {e}", exc_info=True)
        messages.error(request, "Erreur lors de la suppression de l'article.")
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

    # Récupérer les catégories principales (sans parent)
    from gestion_achats.models import GACCategorie
    categories_principales = GACCategorie.objects.filter(parent=None).order_by('nom')

    # Récupérer toutes les catégories
    toutes_categories = GACCategorie.objects.all().order_by('nom')

    context = {
        'arborescence': arborescence,
        'stats': stats,
        'categories_principales': categories_principales,
        'toutes_categories': toutes_categories,
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
                logger.error(f"Erreur création catégorie: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la création de la catégorie.")
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
                logger.error(f"Erreur modification catégorie {categorie.nom}: {e}", exc_info=True)
                messages.error(request, "Erreur lors de la modification de la catégorie.")
    else:
        form = CategorieForm(instance=categorie)

    context = {
        'form': form,
        'categorie': categorie,
        'action': 'Modifier',
    }

    return render(request, 'gestion_achats/catalogue/categorie_form.html', context)


@login_required
def categorie_delete(request, pk):
    """Supprimer une catégorie."""
    require_permission(GACPermissions.can_manage_catalogue, request.user)
    
    categorie = get_object_or_404(GACCategorie, uuid=pk)
    
    # Vérifier que la catégorie peut être supprimée
    if categorie.articles.exists():
        messages.error(request, 'Impossible de supprimer une catégorie contenant des articles.')
        return redirect('gestion_achats:categorie_list')
    
    if categorie.sous_categories.exists():
        messages.error(request, 'Impossible de supprimer une catégorie contenant des sous-catégories.')
        return redirect('gestion_achats:categorie_list')
    
    if request.method == 'POST':
        try:
            nom_categorie = categorie.nom
            categorie.delete()
            messages.success(request, f'Catégorie "{nom_categorie}" supprimée avec succès.')
            return redirect('gestion_achats:categorie_list')
            
        except Exception as e:
            logger.error(f"Erreur suppression catégorie {categorie.nom}: {e}", exc_info=True)
            messages.error(request, "Erreur lors de la suppression de la catégorie.")

    return redirect('gestion_achats:categorie_list')


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
        logger.error(f"Erreur recherche articles: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': "Erreur lors de la recherche."}, status=400)
