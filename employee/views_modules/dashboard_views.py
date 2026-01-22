# employee/views_modules/dashboard_views.py
"""
Vue du dashboard principal avec statistiques RH.
"""
from datetime import date, timedelta

from django.db.models import Q, Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from absence.models import AcquisitionConges, Absence
from departement.models import ZDDE
from employee.models import ZY00, ZYCO


@login_required
def dashboard(request):
    """
    Dashboard principal avec statistiques RH
    """
    # ========================================
    # STATISTIQUES EMPLOYÉS
    # ========================================

    # Total employés
    total_employes = ZY00.objects.count()

    # Employés actifs
    employes_actifs = ZY00.objects.filter(etat='actif').count()

    # Employés en attente (nouveau statut ou à valider)
    employes_attente = ZY00.objects.filter(
        Q(etat='en_attente') | Q(etat='nouveau')
    ).count()

    # Contrats actifs (contrats non expirés)
    date_actuelle = timezone.now().date()
    contrats_actifs = ZYCO.objects.filter(
        Q(date_fin__gte=date_actuelle) | Q(date_fin__isnull=True),
        actif=True
    ).count()

    # ========================================
    # NOUVEAUX EMPLOYÉS (30 derniers jours)
    # ========================================

    date_limite = date_actuelle - timedelta(days=30)

    # Employés en attente de validation
    embauches_attente = ZY00.objects.filter(
        etat='en_attente',
        date_entree_entreprise__gte=date_limite
    ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

    # Dernières embauches validées
    dernieres_embauches = ZY00.objects.filter(
        etat='actif',
        date_entree_entreprise__gte=date_limite
    ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

    # ========================================
    # STATISTIQUES ABSENCES
    # ========================================

    # Absences en attente de validation
    absences_attente_manager = Absence.objects.filter(
        statut='EN_ATTENTE_MANAGER'
    ).count()

    absences_attente_rh = Absence.objects.filter(
        statut='EN_ATTENTE_RH'
    ).count()

    absences_total_attente = absences_attente_manager + absences_attente_rh

    # Absences du mois en cours
    premier_jour_mois = date_actuelle.replace(day=1)
    absences_mois = Absence.objects.filter(
        date_debut__gte=premier_jour_mois,
        statut='VALIDE'
    ).count()

    # ========================================
    # DÉPARTEMENTS
    # ========================================

    # Total départements
    total_departements = ZDDE.objects.filter(actif=True).count()

    # Départements avec leur effectif
    departements_effectifs = ZDDE.objects.filter(actif=True).annotate(
        effectif=Count('postes__affectations', filter=Q(
            postes__affectations__date_fin__isnull=True,
            postes__affectations__employe__etat='actif'
        ))
    ).order_by('-effectif')[:5]

    # ========================================
    # ANNIVERSAIRES DE TRAVAIL (ce mois)
    # ========================================

    mois_actuel = date_actuelle.month
    anniversaires = ZY00.objects.filter(
        etat='actif',
        date_entree_entreprise__month=mois_actuel
    ).exclude(
        date_entree_entreprise__year=date_actuelle.year
    ).select_related('entreprise').order_by('date_entree_entreprise')[:10]

    # ========================================
    # CONTRATS ARRIVANT À ÉCHÉANCE (60 jours)
    # ========================================

    date_limite_contrat = date_actuelle + timedelta(days=60)
    contrats_echeance = ZYCO.objects.filter(
        date_fin__gte=date_actuelle,
        date_fin__lte=date_limite_contrat,
        actif=True
    ).select_related('employe', 'employe__entreprise').order_by('date_fin')[:5]

    # ========================================
    # SOLDES DE CONGÉS À SURVEILLER
    # ========================================

    annee_acquisition = date_actuelle.year - 1
    soldes_faibles = AcquisitionConges.objects.filter(
        annee_reference=annee_acquisition,
        jours_restants__lte=5,
        jours_restants__gt=0,
        employe__etat='actif'
    ).select_related('employe').order_by('jours_restants')[:5]

    # ========================================
    # CONTEXT
    # ========================================

    context = {
        # Statistiques principales
        'total_employes': total_employes,
        'employes_actifs': employes_actifs,
        'employes_attente': employes_attente,
        'contrats_actifs': contrats_actifs,

        # Embauches
        'embauches_attente': embauches_attente,
        'dernieres_embauches': dernieres_embauches,

        # Absences
        'absences_total_attente': absences_total_attente,
        'absences_attente_manager': absences_attente_manager,
        'absences_attente_rh': absences_attente_rh,
        'absences_mois': absences_mois,

        # Départements
        'total_departements': total_departements,
        'departements_effectifs': departements_effectifs,

        # Alertes
        'anniversaires': anniversaires,
        'contrats_echeance': contrats_echeance,
        'soldes_faibles': soldes_faibles,
    }

    return render(request, 'home.html', context)


def handler400(request, exception):
    """Vue personnalisée pour les erreurs 400"""
    return render(request, '400.html', status=400)
