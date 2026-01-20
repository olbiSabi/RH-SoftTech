# absence/utils.py

from decimal import Decimal
from datetime import date
import calendar
from django.utils import timezone

# absence/utils.py

import logging

logger = logging.getLogger(__name__)


def calculer_jours_acquis_au(employe, annee_reference, date_reference):
    """
    Calcule les jours acquis jusqu'à une date donnée
    """
    logger.info("=" * 80)
    logger.info("🔍 DÉBUT CALCUL - %s", employe)
    logger.info("=" * 80)
    logger.info("📅 Année référence: %s", annee_reference)
    logger.info("📅 Date référence: %s", date_reference.strftime('%d/%m/%Y'))

    # 1. Récupérer la convention
    convention = employe.convention_applicable
    if not convention:
        logger.error("❌ Aucune convention pour %s", employe)
        raise ValueError(f"Aucune convention applicable pour {employe}")

    logger.info("✅ Convention: %s", convention.nom)
    logger.info("   - Code: %s", convention.code)
    logger.info("   - Jours/mois: %s", convention.jours_acquis_par_mois)

    # 2. Récupérer les paramètres
    try:
        parametres = convention.parametres_calcul
    except Exception as e:
        logger.warning("⚠️  Paramètres manquants, création par défaut")
        from absence.models import ParametreCalculConges
        parametres = ParametreCalculConges.objects.create(
            configuration=convention
        )

    logger.info("📋 Paramètres calcul:")
    logger.info("   - Mois minimum: %s", parametres.mois_acquisition_min)
    logger.info("   - Plafond annuel: %s jours", parametres.plafond_jours_an)
    logger.info("   - Temps partiel pris en compte: %s", parametres.prise_compte_temps_partiel)

    # 3. Calculer les mois travaillés jusqu'à date_reference
    logger.info("🧮 Calcul des mois travaillés...")
    mois_travailles = calculer_mois_travailles_jusquau(
        employe,
        annee_reference,
        date_reference
    )

    logger.info("📊 Mois travaillés: %s", mois_travailles)

    # 4. Vérifier le minimum requis
    if mois_travailles < parametres.mois_acquisition_min:
        logger.warning("⚠️  CONDITION NON REMPLIE: %s mois < %s mois minimum requis",
                       mois_travailles, parametres.mois_acquisition_min)
        return {
            'jours_acquis': Decimal('0.00'),
            'mois_travailles': mois_travailles,
            'date_reference': date_reference,
            'detail': {
                'jours_base': '0.00',
                'jours_anciennete': '0.00',
                'coefficient_tp': str(employe.coefficient_temps_travail),
                'plafond_applique': False,
                'raison': f'Moins de {parametres.mois_acquisition_min} mois travaillés'
            }
        }

    # 5. Calcul de base
    jours_base = convention.jours_acquis_par_mois * mois_travailles
    logger.info("💰 Jours base: %s × %s = %s",
                convention.jours_acquis_par_mois, mois_travailles, jours_base)

    plafond_applique = False

    # 6. Appliquer le plafond
    if jours_base > parametres.plafond_jours_an:
        logger.info("🔒 Plafond appliqué: %s → %s", jours_base, parametres.plafond_jours_an)
        jours_base = Decimal(str(parametres.plafond_jours_an))
        plafond_applique = True

    # 7. Ajouter l'ancienneté
    jours_anciennete = calculer_jours_anciennete(employe, parametres)
    logger.info("🎖️  Jours ancienneté: %s (ancienneté: %s ans)",
                jours_anciennete, employe.anciennete_annees)

    jours_total = jours_base + jours_anciennete
    logger.info("📈 Total avant temps partiel: %s", jours_total)

    # 8. Temps partiel
    coefficient_tp = employe.coefficient_temps_travail
    logger.info("⏰ Coefficient temps partiel: %s", coefficient_tp)

    if parametres.prise_compte_temps_partiel:
        jours_total = jours_total * coefficient_tp
        logger.info("✅ Après temps partiel: %s × %s = %s",
                    jours_base + jours_anciennete, coefficient_tp, jours_total)

    resultat_final = jours_total.quantize(Decimal('0.01'))

    logger.info("=" * 80)
    logger.info("✅ RÉSULTAT FINAL: %s jours", resultat_final)
    logger.info("=" * 80)

    return {
        'jours_acquis': resultat_final,
        'mois_travailles': mois_travailles,
        'date_reference': date_reference,
        'detail': {
            'jours_base': str(jours_base),
            'jours_anciennete': str(jours_anciennete),
            'coefficient_tp': str(coefficient_tp),
            'plafond_applique': plafond_applique
        }
    }


def calculer_mois_travailles_jusquau(employe, annee_reference, date_limite):
    """
    Calcule le nombre de mois travaillés jusqu'à une date donnée

    Args:
        employe (ZY00): Instance de l'employé
        annee_reference (int): Année de référence
        date_limite (date): Date jusqu'à laquelle compter

    Returns:
        Decimal: Nombre de mois travaillés
    """
    if not employe.date_entree_entreprise:
        return Decimal('0.00')

    # Récupérer la convention
    convention = employe.convention_applicable
    if not convention:
        return Decimal('0.00')

    # Période d'acquisition
    debut_annee, fin_annee = convention.get_periode_acquisition(annee_reference)

    # ✅ DIFFÉRENCE PRINCIPALE : Utiliser date_limite au lieu de date_actuelle

    # Si date_limite est avant le début de la période
    if date_limite < debut_annee:
        return Decimal('0.00')

    # Déterminer la date de fin effective
    date_fin_effective = min(date_limite, fin_annee)

    # Calculer la période de travail
    date_debut = max(employe.date_entree_entreprise, debut_annee)
    date_fin = date_fin_effective

    if date_debut > date_fin:
        return Decimal('0.00')

    # Calculer mois par mois
    mois_total = Decimal('0.00')
    current_date = date(date_debut.year, date_debut.month, 1)

    while current_date <= date_fin:
        mois = current_date.month
        annee = current_date.year

        premier_jour = date(annee, mois, 1)
        dernier_jour = date(annee, mois, calendar.monthrange(annee, mois)[1])

        debut_effectif = max(date_debut, premier_jour)
        fin_effective = min(date_fin, dernier_jour)

        if debut_effectif <= fin_effective:
            jours_calendaires = (fin_effective - debut_effectif).days + 1

            if jours_calendaires >= 25:
                mois_total += Decimal('1.00')
            elif jours_calendaires >= 15:
                mois_total += Decimal('0.50')

        # Passer au mois suivant
        if mois == 12:
            current_date = date(annee + 1, 1, 1)
        else:
            current_date = date(annee, mois + 1, 1)

    return mois_total


def calculer_jours_anciennete(employe, parametres):
    """
    Calcule les jours supplémentaires selon l'ancienneté

    Args:
        employe (ZY00): Instance de l'employé
        parametres (ParametreCalculConges): Paramètres de calcul

    Returns:
        Decimal: Nombre de jours supplémentaires
    """
    if not parametres.jours_supp_anciennete:
        return Decimal('0.00')

    anciennete = employe.anciennete_annees
    jours_supp = Decimal('0.00')

    # Parcourir les paliers d'ancienneté (trié décroissant)
    paliers = sorted(
        [(int(k), v) for k, v in parametres.jours_supp_anciennete.items()],
        reverse=True
    )

    for annees, jours in paliers:
        if anciennete >= annees:
            jours_supp = Decimal(str(jours))
            break

    return jours_supp