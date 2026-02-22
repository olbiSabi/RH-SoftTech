# employee/views_modules/dashboard_views.py
"""
Vue du dashboard principal avec statistiques RH.
"""
from datetime import date, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from absence.models import AcquisitionConges, Absence
from departement.models import ZDDE
from employee.models import ZY00, ZYCO

_CACHE_TTL = getattr(settings, 'CACHE_TTL_DASHBOARD', 300)


def _compute_dashboard_stats(date_actuelle):
    """Calcule les statistiques globales du dashboard (cacheable)."""
    date_limite = date_actuelle - timedelta(days=30)
    premier_jour_mois = date_actuelle.replace(day=1)
    mois_actuel = date_actuelle.month
    date_limite_contrat = date_actuelle + timedelta(days=60)
    annee_acquisition = date_actuelle.year - 1

    absences_attente_manager = Absence.objects.filter(statut='EN_ATTENTE_MANAGER').count()
    absences_attente_rh = Absence.objects.filter(statut='EN_ATTENTE_RH').count()

    return {
        # Compteurs employés
        'total_employes': ZY00.objects.count(),
        'employes_actifs': ZY00.objects.filter(etat='actif').count(),
        'employes_attente': ZY00.objects.filter(Q(etat='en_attente') | Q(etat='nouveau')).count(),
        'contrats_actifs': ZYCO.objects.filter(
            Q(date_fin__gte=date_actuelle) | Q(date_fin__isnull=True), actif=True
        ).count(),
        # Embauches récentes (listes converties pour sérialisation)
        'embauches_attente': list(
            ZY00.objects.filter(etat='en_attente', date_entree_entreprise__gte=date_limite)
            .select_related('entreprise').order_by('-date_entree_entreprise')[:5]
        ),
        'dernieres_embauches': list(
            ZY00.objects.filter(etat='actif', date_entree_entreprise__gte=date_limite)
            .select_related('entreprise').order_by('-date_entree_entreprise')[:5]
        ),
        # Absences
        'absences_attente_manager': absences_attente_manager,
        'absences_attente_rh': absences_attente_rh,
        'absences_total_attente': absences_attente_manager + absences_attente_rh,
        'absences_mois': Absence.objects.filter(
            date_debut__gte=premier_jour_mois, statut='VALIDE'
        ).count(),
        # Départements
        'total_departements': ZDDE.objects.filter(actif=True).count(),
        'departements_effectifs': list(
            ZDDE.objects.filter(actif=True).annotate(
                effectif=Count('postes__affectations', filter=Q(
                    postes__affectations__date_fin__isnull=True,
                    postes__affectations__employe__etat='actif'
                ))
            ).order_by('-effectif')[:5]
        ),
        # Alertes
        'anniversaires': list(
            ZY00.objects.filter(etat='actif', date_entree_entreprise__month=mois_actuel)
            .exclude(date_entree_entreprise__year=date_actuelle.year)
            .select_related('entreprise').order_by('date_entree_entreprise')[:10]
        ),
        'contrats_echeance': list(
            ZYCO.objects.filter(
                date_fin__gte=date_actuelle, date_fin__lte=date_limite_contrat, actif=True
            ).select_related('employe', 'employe__entreprise').order_by('date_fin')[:5]
        ),
        'soldes_faibles': list(
            AcquisitionConges.objects.filter(
                annee_reference=annee_acquisition, jours_restants__lte=5,
                jours_restants__gt=0, employe__etat='actif'
            ).select_related('employe').order_by('jours_restants')[:5]
        ),
    }


@login_required
def dashboard(request):
    """Dashboard principal avec statistiques RH (mise en cache Redis 5 min)."""
    date_actuelle = timezone.now().date()
    # Clé de cache incluant la date du jour (invalide naturellement à minuit)
    cache_key = f'dashboard_stats_{date_actuelle.isoformat()}'

    context = cache.get(cache_key)
    if context is None:
        context = _compute_dashboard_stats(date_actuelle)
        cache.set(cache_key, context, _CACHE_TTL)

    return render(request, 'home.html', context)


def handler400(request, exception):
    """Vue personnalisée pour les erreurs 400"""
    return render(request, '400.html', status=400)
