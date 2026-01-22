# absence/views_modules/acquisition_views.py
"""
Vues pour la gestion des acquisitions de congés.
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Count, Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from absence.decorators import drh_or_admin_required, gestion_app_required
from absence.models import AcquisitionConges, ConfigurationConventionnelle
from absence.forms import CalculAcquisitionForm
from employee.models import ZY00

logger = logging.getLogger(__name__)


@login_required
@drh_or_admin_required
@gestion_app_required
def liste_acquisitions(request):
    """Liste des acquisitions de congés avec filtres"""
    search = request.GET.get('search', '')
    annee_filter = request.GET.get('annee', timezone.now().year)
    employe_filter = request.GET.get('employe', '')

    employes_actifs = ZY00.objects.filter(
        etat='actif',
        entreprise__isnull=False
    )

    if search:
        employes_actifs = employes_actifs.filter(
            Q(nom__icontains=search) |
            Q(prenoms__icontains=search) |
            Q(matricule__icontains=search)
        )

    if employe_filter:
        employes_actifs = employes_actifs.filter(matricule=employe_filter)

    employes_actifs = employes_actifs.order_by('nom', 'prenoms')

    acquisitions_existantes = AcquisitionConges.objects.filter(
        annee_reference=annee_filter,
        employe__in=employes_actifs
    ).select_related('employe', 'employe__entreprise')

    acquisitions_dict = {acq.employe.uuid: acq for acq in acquisitions_existantes}

    stats = acquisitions_existantes.aggregate(
        total_employes=Count('employe', distinct=True),
        total_jours_acquis=Sum('jours_acquis'),
        total_jours_pris=Sum('jours_pris'),
        total_jours_restants=Sum('jours_restants')
    )

    annees = AcquisitionConges.objects.values_list(
        'annee_reference', flat=True
    ).distinct().order_by('-annee_reference')

    employes = ZY00.objects.filter(
        etat='actif',
        entreprise__isnull=False
    ).order_by('nom', 'prenoms')

    calcul_form = CalculAcquisitionForm(initial={'annee_reference': annee_filter})

    date_actuelle = timezone.now().date()
    annee_verrouille = False
    date_limite_recalcul = None
    message_verrouillage = ""
    dans_delai_grace = False
    fin_periode = None

    try:
        convention_entreprise = ConfigurationConventionnelle.objects.filter(
            type_convention='ENTREPRISE',
            actif=True
        ).first()

        if convention_entreprise and annee_filter:
            _, fin_periode = convention_entreprise.get_periode_acquisition(int(annee_filter))
            date_limite_recalcul = fin_periode + timedelta(days=2)

            if date_actuelle > date_limite_recalcul:
                annee_verrouille = True
                message_verrouillage = f"Le délai de recalcul a expiré le {date_limite_recalcul.strftime('%d/%m/%Y')}"
            elif date_actuelle > fin_periode and date_actuelle <= date_limite_recalcul:
                dans_delai_grace = True

    except Exception as e:
        logger.error("Erreur lors du calcul de verrouillage: %s", e)

    acquisitions_enrichies = []
    for emp in employes_actifs:
        acq = acquisitions_dict.get(emp.uuid)

        if acq:
            try:
                conv = emp.convention_applicable
                if conv:
                    _, fin_periode_acq = conv.get_periode_acquisition(int(annee_filter))
                    date_limite_acq = fin_periode_acq + timedelta(days=2)

                    acq.est_verrouille_cache = date_actuelle > date_limite_acq
                    acq.date_limite_modification_cache = date_limite_acq
                    acq.est_dans_delai_grace_cache = (
                        date_actuelle > fin_periode_acq and date_actuelle <= date_limite_acq
                    )
                else:
                    acq.est_verrouille_cache = True
                    acq.date_limite_modification_cache = None
                    acq.est_dans_delai_grace_cache = False
            except Exception:
                acq.est_verrouille_cache = True
                acq.date_limite_modification_cache = None
                acq.est_dans_delai_grace_cache = False

            acquisitions_enrichies.append(acq)
        else:
            acq_vide = type('AcquisitionVide', (), {
                'employe': emp,
                'annee_reference': annee_filter,
                'jours_acquis': Decimal('0.00'),
                'jours_pris': Decimal('0.00'),
                'jours_restants': Decimal('0.00'),
                'jours_report_anterieur': Decimal('0.00'),
                'jours_report_nouveau': Decimal('0.00'),
                'date_maj': None,
                'id': None,
                'est_verrouille_cache': False,
                'date_limite_modification_cache': None,
                'est_dans_delai_grace_cache': False,
                'a_calculer': True
            })()

            acquisitions_enrichies.append(acq_vide)

    context = {
        'acquisitions': acquisitions_enrichies,
        'stats': stats,
        'annees': annees,
        'employes': employes,
        'search': search,
        'annee_filter': annee_filter,
        'employe_filter': employe_filter,
        'calcul_form': calcul_form,
        'annee_verrouille': annee_verrouille,
        'date_limite_recalcul': date_limite_recalcul,
        'message_verrouillage': message_verrouillage,
        'dans_delai_grace': dans_delai_grace,
        'fin_periode': fin_periode,
        'today': timezone.now().date(),
    }

    return render(request, 'absence/acquisitions_list.html', context)
