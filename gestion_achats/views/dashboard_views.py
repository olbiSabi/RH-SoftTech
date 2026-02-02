"""
Vues pour le dashboard du module GAC.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum

from gestion_achats.models import GACDemandeAchat, GACBonCommande, GACBudget
from gestion_achats.services import DemandeService, BudgetService


@login_required
def dashboard(request):
    """Dashboard principal du module GAC."""

    # Statistiques pour l'utilisateur
    mes_demandes = GACDemandeAchat.objects.filter(demandeur=request.user.employe)
    mes_demandes_count = mes_demandes.count()
    mes_demandes_en_cours = mes_demandes.exclude(
        statut__in=['VALIDEE_N2', 'CONVERTIE_BC', 'REFUSEE', 'ANNULEE']
    ).count()

    # Demandes à valider
    demandes_n1 = DemandeService.get_demandes_a_valider_n1(request.user.employe).count()
    demandes_n2 = DemandeService.get_demandes_a_valider_n2(request.user.employe).count()

    # Statistiques budgétaires (si gestionnaire)
    budgets_en_alerte = []
    if request.user.employe.has_role('GESTIONNAIRE_BUDGET') or request.user.employe.has_role('ADMIN_GAC'):
        budgets_en_alerte = BudgetService.get_budgets_en_alerte()

    # Statistiques globales (si acheteur ou admin)
    stats_globales = None
    if request.user.employe.has_role('ACHETEUR') or request.user.employe.has_role('ADMIN_GAC'):
        total_demandes = GACDemandeAchat.objects.count()
        total_bcs = GACBonCommande.objects.count()

        demandes_par_statut = GACDemandeAchat.objects.values('statut').annotate(
            count=Count('id')
        )

        stats_globales = {
            'total_demandes': total_demandes,
            'total_bcs': total_bcs,
            'demandes_par_statut': {d['statut']: d['count'] for d in demandes_par_statut},
        }

    context = {
        'mes_demandes_count': mes_demandes_count,
        'mes_demandes_en_cours': mes_demandes_en_cours,
        'demandes_n1': demandes_n1,
        'demandes_n2': demandes_n2,
        'budgets_en_alerte': budgets_en_alerte,
        'stats_globales': stats_globales,
    }

    return render(request, 'gestion_achats/dashboard.html', context)
