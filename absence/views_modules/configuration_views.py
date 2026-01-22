# absence/views_modules/configuration_views.py
"""
Vues pour la configuration des absences:
- Conventions collectives
- Jours fériés
- Types d'absence
- Paramètres de calcul des congés
"""
import logging
from datetime import datetime

from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from absence.decorators import drh_or_admin_required, gestion_app_required
from absence.models import (
    ConfigurationConventionnelle,
    JourFerie,
    TypeAbsence,
    ParametreCalculConges
)

logger = logging.getLogger(__name__)


# ===============================
# VUES POUR CONFIGURATIONCONVENTIONNELLE
# ===============================

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_conventions(request):
    """Liste des conventions collectives avec filtres"""
    filtre_actif = request.GET.get('actif', '')
    filtre_annee = request.GET.get('annee', '')
    type_filter = request.GET.get('type', '')
    search = request.GET.get('search', '')

    conventions = ConfigurationConventionnelle.objects.all()

    if filtre_actif == 'oui':
        conventions = conventions.filter(actif=True)
    elif filtre_actif == 'non':
        conventions = conventions.filter(actif=False)

    if filtre_annee:
        conventions = conventions.filter(annee_reference=filtre_annee)

    if type_filter:
        conventions = conventions.filter(type_convention=type_filter)

    if search:
        conventions = conventions.filter(
            Q(nom__icontains=search) |
            Q(code__icontains=search)
        )

    conventions = conventions.order_by(
        '-annee_reference',
        '-created_at' if hasattr(ConfigurationConventionnelle, 'created_at') else 'nom'
    )

    stats = {
        'total': ConfigurationConventionnelle.objects.count(),
        'actives': ConfigurationConventionnelle.objects.filter(actif=True).count(),
        'inactives': ConfigurationConventionnelle.objects.filter(actif=False).count(),
    }

    entreprise_count = ConfigurationConventionnelle.objects.filter(type_convention='ENTREPRISE').count()
    personnalisee_count = ConfigurationConventionnelle.objects.filter(type_convention='PERSONNALISEE').count()

    annees = ConfigurationConventionnelle.objects.values_list(
        'annee_reference', flat=True
    ).distinct().order_by('-annee_reference')

    context = {
        'conventions': conventions,
        'stats': stats,
        'entreprise_count': entreprise_count,
        'personnalisee_count': personnalisee_count,
        'annees': annees,
        'filtre_actif': filtre_actif,
        'filtre_annee': filtre_annee,
        'type_filter': type_filter,
        'search': search,
    }

    return render(request, 'absence/conventions_list.html', context)


# ===============================
# VUES POUR JOURS FÉRIÉS
# ===============================

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_jours_feries(request):
    """Affiche la liste des jours fériés avec filtres"""
    annee_filter = request.GET.get('annee', '')
    type_filter = request.GET.get('type', '')
    actif_filter = request.GET.get('actif', '')
    search = request.GET.get('search', '').strip()

    jours_feries = JourFerie.objects.all()

    if annee_filter:
        jours_feries = jours_feries.filter(date__year=annee_filter)

    if type_filter:
        jours_feries = jours_feries.filter(type_ferie=type_filter)

    if actif_filter == 'oui':
        jours_feries = jours_feries.filter(actif=True)
    elif actif_filter == 'non':
        jours_feries = jours_feries.filter(actif=False)

    if search:
        jours_feries = jours_feries.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search)
        )

    jours_feries = jours_feries.order_by('-date')

    total = jours_feries.count()
    actifs = jours_feries.filter(actif=True).count()
    inactifs = jours_feries.filter(actif=False).count()
    legaux = jours_feries.filter(type_ferie='LEGAL').count()
    entreprise = jours_feries.filter(type_ferie='ENTREPRISE').count()

    annees = JourFerie.objects.dates('date', 'year', order='DESC')
    annees_list = [date.year for date in annees]

    annee_courante = datetime.now().year

    context = {
        'jours_feries': jours_feries,
        'total': total,
        'actifs': actifs,
        'inactifs': inactifs,
        'legaux': legaux,
        'entreprise': entreprise,
        'annees': annees_list,
        'annee_courante': annee_courante,
        'annee_filter': annee_filter,
        'type_filter': type_filter,
        'actif_filter': actif_filter,
        'search': search,
    }

    return render(request, 'absence/jours_feries_list.html', context)


# ===============================
# VUES POUR TYPES D'ABSENCE
# ===============================

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_types_absence(request):
    """Affiche la liste des types d'absence avec filtres"""
    categorie_filter = request.GET.get('categorie', '')
    actif_filter = request.GET.get('actif', '')
    paye_filter = request.GET.get('paye', '')
    search = request.GET.get('search', '').strip()

    types_absence = TypeAbsence.objects.all()

    if categorie_filter:
        types_absence = types_absence.filter(categorie=categorie_filter)

    if actif_filter == 'oui':
        types_absence = types_absence.filter(actif=True)
    elif actif_filter == 'non':
        types_absence = types_absence.filter(actif=False)

    if paye_filter == 'oui':
        types_absence = types_absence.filter(paye=True)
    elif paye_filter == 'non':
        types_absence = types_absence.filter(paye=False)

    if search:
        types_absence = types_absence.filter(
            Q(code__icontains=search) |
            Q(libelle__icontains=search)
        )

    types_absence = types_absence.order_by('ordre', 'libelle')

    total = types_absence.count()
    actifs = types_absence.filter(actif=True).count()
    inactifs = types_absence.filter(actif=False).count()
    payes = types_absence.filter(paye=True).count()
    non_payes = types_absence.filter(paye=False).count()
    avec_decompte = types_absence.filter(decompte_solde=True).count()

    categories = TypeAbsence.CATEGORIE_CHOICES

    context = {
        'types_absence': types_absence,
        'total': total,
        'actifs': actifs,
        'inactifs': inactifs,
        'payes': payes,
        'non_payes': non_payes,
        'avec_decompte': avec_decompte,
        'categories': categories,
        'categorie_filter': categorie_filter,
        'actif_filter': actif_filter,
        'paye_filter': paye_filter,
        'search': search,
    }

    return render(request, 'absence/types_absence_list.html', context)


# ===============================
# VUES POUR PARAMÈTRES DE CALCUL
# ===============================

@login_required
@drh_or_admin_required
@gestion_app_required
def liste_parametres_calcul(request):
    """Liste des paramètres de calcul des congés avec filtres"""
    search = request.GET.get('search', '')
    convention_filter = request.GET.get('convention', '')

    parametres = ParametreCalculConges.objects.select_related('configuration').all()

    if search:
        parametres = parametres.filter(
            Q(configuration__nom__icontains=search) |
            Q(configuration__code__icontains=search)
        )

    if convention_filter:
        parametres = parametres.filter(configuration_id=convention_filter)

    parametres = parametres.order_by('-configuration__annee_reference')

    total = ParametreCalculConges.objects.count()
    avec_report = ParametreCalculConges.objects.filter(report_autorise=True).count()
    sans_report = ParametreCalculConges.objects.filter(report_autorise=False).count()
    avec_anciennete = ParametreCalculConges.objects.exclude(jours_supp_anciennete={}).count()

    conventions = ConfigurationConventionnelle.objects.filter(actif=True).order_by('nom')

    context = {
        'parametres': parametres,
        'total': total,
        'avec_report': avec_report,
        'sans_report': sans_report,
        'avec_anciennete': avec_anciennete,
        'conventions': conventions,
        'search': search,
        'convention_filter': convention_filter,
    }

    return render(request, 'absence/parametres_calcul_list.html', context)
