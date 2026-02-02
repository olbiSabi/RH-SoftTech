"""
Vues pour le dashboard du module GAC.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from gestion_achats.models import (
    GACDemandeAchat,
    GACBonCommande,
    GACBudget,
    GACReception,
    GACBonRetour,
    GACFournisseur,
)
from gestion_achats.services import DemandeService, BudgetService


@login_required
def dashboard(request):
    """Dashboard principal du module GAC avec statistiques complètes."""

    # Date pour les statistiques des 30 derniers jours
    date_30_jours = timezone.now() - timedelta(days=30)
    date_7_jours = timezone.now() - timedelta(days=7)

    # ==== STATISTIQUES PERSONNELLES ====
    mes_demandes = GACDemandeAchat.objects.filter(demandeur=request.user.employe)
    mes_demandes_count = mes_demandes.count()
    mes_demandes_en_cours = mes_demandes.exclude(
        statut__in=['VALIDEE_N2', 'CONVERTIE_BC', 'REFUSEE', 'ANNULEE']
    ).count()

    # Dernières demandes de l'utilisateur
    mes_dernieres_demandes = mes_demandes.order_by('-date_creation')[:5]

    # ==== DEMANDES À VALIDER ====
    demandes_n1 = DemandeService.get_demandes_a_valider_n1(request.user.employe).count()
    demandes_n2 = DemandeService.get_demandes_a_valider_n2(request.user.employe).count()

    # ==== STATISTIQUES BUDGÉTAIRES ====
    budgets_info = {}
    if request.user.employe.has_role('GESTIONNAIRE_BUDGET') or request.user.employe.has_role('ADMIN_GAC'):
        budgets_en_alerte = BudgetService.get_budgets_en_alerte()
        exercice_en_cours = timezone.now().year

        budgets_exercice = GACBudget.objects.filter(exercice=exercice_en_cours)
        total_budget_initial = budgets_exercice.aggregate(Sum('montant_initial'))['montant_initial__sum'] or 0
        total_budget_engage = budgets_exercice.aggregate(Sum('montant_engage'))['montant_engage__sum'] or 0
        total_budget_consomme = budgets_exercice.aggregate(Sum('montant_consomme'))['montant_consomme__sum'] or 0

        budgets_info = {
            'en_alerte': budgets_en_alerte,
            'nb_en_alerte': len(budgets_en_alerte),
            'exercice': exercice_en_cours,
            'total_initial': total_budget_initial,
            'total_engage': total_budget_engage,
            'total_consomme': total_budget_consomme,
            'total_disponible': total_budget_initial - total_budget_engage - total_budget_consomme,
            'taux_consommation': round((total_budget_consomme / total_budget_initial * 100), 1) if total_budget_initial > 0 else 0,
        }

    # ==== STATISTIQUES GLOBALES (Acheteur/Admin) ====
    stats_globales = None
    stats_tendances = None
    top_fournisseurs = []
    stats_receptions = {}
    stats_retours = {}

    if request.user.employe.has_role('ACHETEUR') or request.user.employe.has_role('ADMIN_GAC'):
        # Demandes
        total_demandes = GACDemandeAchat.objects.count()
        demandes_30j = GACDemandeAchat.objects.filter(date_creation__gte=date_30_jours).count()
        demandes_par_statut = GACDemandeAchat.objects.values('statut').annotate(
            count=Count('id')
        )

        # Bons de commande
        total_bcs = GACBonCommande.objects.count()
        bcs_30j = GACBonCommande.objects.filter(date_creation__gte=date_30_jours).count()
        montant_total_bcs = GACBonCommande.objects.aggregate(
            Sum('montant_total_ttc')
        )['montant_total_ttc__sum'] or 0

        bcs_par_statut = GACBonCommande.objects.values('statut').annotate(
            count=Count('id')
        )

        # Réceptions
        total_receptions = GACReception.objects.count()
        receptions_en_attente = GACReception.objects.filter(statut='BROUILLON').count()
        receptions_30j = GACReception.objects.filter(date_creation__gte=date_30_jours).count()

        receptions_conformes = GACReception.objects.filter(
            statut='VALIDEE',
            conforme=True
        ).count()
        receptions_non_conformes = GACReception.objects.filter(
            statut='VALIDEE',
            conforme=False
        ).count()

        total_receptions_validees = receptions_conformes + receptions_non_conformes
        taux_conformite = round(
            (receptions_conformes / total_receptions_validees * 100), 1
        ) if total_receptions_validees > 0 else 0

        stats_receptions = {
            'total': total_receptions,
            'en_attente': receptions_en_attente,
            'receptions_30j': receptions_30j,
            'conformes': receptions_conformes,
            'non_conformes': receptions_non_conformes,
            'taux_conformite': taux_conformite,
        }

        # Bons de retour
        total_retours = GACBonRetour.objects.count()
        retours_30j = GACBonRetour.objects.filter(date_creation__gte=date_30_jours).count()
        retours_en_cours = GACBonRetour.objects.filter(
            statut__in=['BROUILLON', 'EMIS', 'ENVOYE', 'RECU_FOURNISSEUR']
        ).count()

        montant_retours = GACBonRetour.objects.aggregate(
            Sum('montant_total_ttc')
        )['montant_total_ttc__sum'] or 0

        stats_retours = {
            'total': total_retours,
            'retours_30j': retours_30j,
            'en_cours': retours_en_cours,
            'montant_total': montant_retours,
        }

        # Top 5 fournisseurs (par montant de commandes)
        top_fournisseurs = GACBonCommande.objects.values(
            'fournisseur__raison_sociale',
            'fournisseur__uuid'
        ).annotate(
            nb_commandes=Count('id'),
            montant_total=Sum('montant_total_ttc')
        ).order_by('-montant_total')[:5]

        # Tendances des 30 derniers jours
        demandes_7j = GACDemandeAchat.objects.filter(date_creation__gte=date_7_jours).count()
        bcs_7j = GACBonCommande.objects.filter(date_creation__gte=date_7_jours).count()

        stats_tendances = {
            'demandes_7j': demandes_7j,
            'demandes_30j': demandes_30j,
            'bcs_7j': bcs_7j,
            'bcs_30j': bcs_30j,
        }

        stats_globales = {
            'total_demandes': total_demandes,
            'demandes_30j': demandes_30j,
            'total_bcs': total_bcs,
            'bcs_30j': bcs_30j,
            'montant_total_bcs': montant_total_bcs,
            'demandes_par_statut': {d['statut']: d['count'] for d in demandes_par_statut},
            'bcs_par_statut': {b['statut']: b['count'] for b in bcs_par_statut},
        }

    context = {
        # Statistiques personnelles
        'mes_demandes_count': mes_demandes_count,
        'mes_demandes_en_cours': mes_demandes_en_cours,
        'mes_dernieres_demandes': mes_dernieres_demandes,

        # Validations en attente
        'demandes_n1': demandes_n1,
        'demandes_n2': demandes_n2,

        # Budgets
        'budgets_info': budgets_info,

        # Statistiques globales
        'stats_globales': stats_globales,
        'stats_tendances': stats_tendances,
        'stats_receptions': stats_receptions,
        'stats_retours': stats_retours,
        'top_fournisseurs': top_fournisseurs,

        # Rôles
        'is_acheteur': request.user.employe.has_role('ACHETEUR') or request.user.employe.has_role('ADMIN_GAC'),
        'is_gestionnaire_budget': request.user.employe.has_role('GESTIONNAIRE_BUDGET') or request.user.employe.has_role('ADMIN_GAC'),
    }

    return render(request, 'gestion_achats/dashboard.html', context)
