"""
Vues pour la gestion des budgets.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F
from django.http import JsonResponse
from django.utils import timezone

from gestion_achats.models import GACBudget, ZDDE
from gestion_achats.forms import BudgetForm
from gestion_achats.services.budget_service import BudgetService
from gestion_achats.permissions import GACPermissions, require_permission


@login_required
def budget_list(request):
    """Liste des budgets."""
    require_permission(GACPermissions.can_view_all_budgets, request.user)

    # Récupérer tous les budgets
    budgets = GACBudget.objects.select_related(
        'gestionnaire',
        'departement',
        'cree_par'
    ).all()

    # Filtre par exercice
    exercice = request.GET.get('exercice')
    if exercice:
        budgets = budgets.filter(exercice=exercice)
    else:
        # Par défaut, afficher l'exercice en cours
        exercice_en_cours = timezone.now().year
        budgets = budgets.filter(exercice=exercice_en_cours)

    # Filtre par département
    departement = request.GET.get('departement')
    if departement:
        budgets = budgets.filter(departement_id=departement)

    # Filtre par gestionnaire
    gestionnaire = request.GET.get('gestionnaire')
    if gestionnaire:
        budgets = budgets.filter(gestionnaire_id=gestionnaire)

    # Recherche
    search = request.GET.get('search')
    if search:
        budgets = budgets.filter(
            Q(code__icontains=search) |
            Q(libelle__icontains=search)
        )

    # Tri
    budgets = budgets.order_by('-exercice', 'code')

    # Calcul des consommations
    for budget in budgets:
        budget.montant_disponible_calc = budget.montant_disponible()
        budget.taux_consommation_calc = budget.taux_consommation()
    # Pagination
    paginator = Paginator(budgets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Récupérer les données pour les filtres
    from decimal import Decimal
    
    exercices = list(GACBudget.objects.values_list('exercice', flat=True).distinct().order_by('-exercice'))
    departements = ZDDE.objects.values('id', 'LIBELLE').order_by('LIBELLE')

    # Récupérer les budgets en alerte
    budgets_en_alerte = BudgetService.get_budgets_en_alerte() if not exercice else []

    # Calcul des statistiques
    stats_budgets = GACBudget.objects.all()
    if exercice:
        stats_budgets = stats_budgets.filter(exercice=exercice)
    
    # Statistiques globales
    stats = stats_budgets.aggregate(
        total=Count('id'),
        montant_total=Sum('montant_initial'),
        en_alerte=Count('id', filter=Q(montant_engage__gte=F('montant_initial')))
    )
    
    # Calcul du taux moyen de consommation
    taux_moyen = 0
    if stats['montant_total']:
        total_utilise_agg = stats_budgets.aggregate(
            total_engage=Sum('montant_engage'),
            total_commande=Sum('montant_commande'),
            total_consomme=Sum('montant_consomme')
        )
        total_utilise = (total_utilise_agg['total_engage'] or 0) + \
                       (total_utilise_agg['total_commande'] or 0) + \
                       (total_utilise_agg['total_consomme'] or 0)
        taux_moyen = (total_utilise / stats['montant_total'] * 100) if stats['montant_total'] > 0 else 0

    context = {
        'page_obj': page_obj,
        'exercice_filter': exercice or timezone.now().year,
        'departement_filter': departement,
        'gestionnaire_filter': gestionnaire,
        'search': search,
        'budgets_en_alerte': budgets_en_alerte,
        'exercices': exercices,
        'departements': departements,
        'stats': {
            'total': stats['total'] or 0,
            'montant_total': stats['montant_total'] or Decimal('0'),
            'en_alerte': stats['en_alerte'] or 0,
            'taux_moyen': taux_moyen,
        }
    }

    return render(request, 'gestion_achats/budget/budget_list.html', context)


@login_required
def budget_create(request):
    """Créer un nouveau budget."""
    require_permission(GACPermissions.can_create_budget, request.user)

    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                utilisateur = request.user.employe if hasattr(request.user, 'employe') else None

                budget = BudgetService.creer_budget(
                    libelle=form.cleaned_data['libelle'],
                    montant_initial=form.cleaned_data['montant_initial'],
                    exercice=form.cleaned_data['exercice'],
                    date_debut=form.cleaned_data['date_debut'],
                    date_fin=form.cleaned_data['date_fin'],
                    gestionnaire=form.cleaned_data['gestionnaire'],
                    departement=form.cleaned_data.get('departement'),
                    description=form.cleaned_data.get('description', ''),
                    seuil_alerte_1=form.cleaned_data.get('seuil_alerte_1'),
                    seuil_alerte_2=form.cleaned_data.get('seuil_alerte_2'),
                    cree_par=utilisateur,
                )

                messages.success(
                    request,
                    f'Budget {budget.code} - {budget.libelle} créé avec succès.'
                )
                return redirect('gestion_achats:budget_detail', pk=budget.uuid)

            except Exception as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
    else:
        form = BudgetForm(user=request.user)

    context = {
        'form': form,
        'action': 'Créer',
    }

    return render(request, 'gestion_achats/budget/budget_form.html', context)


@login_required
def budget_detail(request, pk):
    """Détail d'un budget."""
    budget = get_object_or_404(
        GACBudget.objects.select_related(
            'gestionnaire',
            'departement',
            'cree_par'
        ),
        uuid=pk
    )

    require_permission(GACPermissions.can_view_budget, request.user, budget)

    # Récupérer les statistiques
    try:
        stats = BudgetService.get_statistiques_budget(budget)
    except Exception:
        stats = {}

    # Calculs
    budget.montant_disponible_calc = budget.montant_disponible()
    budget.taux_consommation_calc = budget.taux_consommation()

    # Récupérer les demandes associées
    demandes = budget.demandes.order_by('-date_creation')[:10]

    # Vérifier les alertes
    alerte_niveau = None
    if budget.taux_consommation_calc >= budget.seuil_alerte_2:
        alerte_niveau = 2
    elif budget.taux_consommation_calc >= budget.seuil_alerte_1:
        alerte_niveau = 1

    context = {
        'budget': budget,
        'stats': stats,
        'demandes': demandes,
        'alerte_niveau': alerte_niveau,
        'can_modify': GACPermissions.can_modify_budget(request.user, budget),
    }

    return render(request, 'gestion_achats/budget/budget_detail.html', context)


@login_required
def budget_update(request, pk):
    """Modifier un budget."""
    budget = get_object_or_404(GACBudget, uuid=pk)

    require_permission(GACPermissions.can_modify_budget, request.user, budget)

    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Budget modifié avec succès.')
                return redirect('gestion_achats:budget_detail', pk=budget.uuid)

            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = BudgetForm(instance=budget, user=request.user)

    context = {
        'form': form,
        'budget': budget,
        'action': 'Modifier',
    }

    return render(request, 'gestion_achats/budget/budget_form.html', context)


@login_required
def budget_historique(request, pk):
    """Historique des mouvements d'un budget."""
    budget = get_object_or_404(GACBudget, uuid=pk)

    require_permission(GACPermissions.can_view_budget, request.user, budget)

    # Récupérer l'historique des mouvements
    historique = budget.historique.order_by('-date_action')

    # Pagination
    paginator = Paginator(historique, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'budget': budget,
        'page_obj': page_obj,
    }

    return render(request, 'gestion_achats/budget/budget_historique.html', context)


@login_required
def synthese_budgets(request):
    """Synthèse de tous les budgets par exercice."""
    require_permission(GACPermissions.can_view_all_budgets, request.user)

    # Récupérer l'exercice
    exercice = request.GET.get('exercice')
    if not exercice:
        exercice = timezone.now().year

    try:
        exercice = int(exercice)
        synthese = BudgetService.get_synthese_budgets(exercice)
        
        # Récupérer la liste des exercices disponibles
        from gestion_achats.models import GACBudget
        exercices_disponibles = GACBudget.objects.values_list('exercice', flat=True).distinct().order_by('-exercice')
        
        # Ajouter l'année courante si pas dans la liste
        annee_courante = timezone.now().year
        if annee_courante not in exercices_disponibles:
            exercices_disponibles = list(exercices_disponibles) + [annee_courante]
        
        # Trier par ordre décroissant
        exercices_disponibles = sorted(exercices_disponibles, reverse=True)
        
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')
        synthese = {}
        exercices_disponibles = [timezone.now().year]

    context = {
        'exercice': exercice,
        'exercices': exercices_disponibles,
        'synthese': synthese,
    }

    return render(request, 'gestion_achats/budget/synthese_budgets.html', context)


@login_required
def budgets_en_alerte_ajax(request):
    """API AJAX pour récupérer les budgets en alerte."""
    try:
        budgets = BudgetService.get_budgets_en_alerte()

        data = [
            {
                'uuid': str(budget.uuid),
                'code': budget.code,
                'libelle': budget.libelle,
                'taux_consommation': float(budget.taux_consommation()),
                'montant_disponible': float(budget.montant_disponible()),
                'exercice': budget.exercice,
            }
            for budget in budgets
        ]

        return JsonResponse({'success': True, 'budgets': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
