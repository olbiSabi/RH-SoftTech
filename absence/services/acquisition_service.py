# absence/services/acquisition_service.py
"""
Service de gestion des acquisitions de congés.
"""
from decimal import Decimal
from datetime import date
import calendar
import logging

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class AcquisitionService:
    """Service pour gérer les acquisitions de congés."""

    @staticmethod
    def calculer_jours_acquis_au(employe, annee_reference, date_reference):
        """
        Calcule les jours acquis jusqu'à une date donnée.

        Args:
            employe: Instance de l'employé (ZY00)
            annee_reference: Année de référence
            date_reference: Date jusqu'à laquelle calculer

        Returns:
            dict: Résultat du calcul avec détails
        """
        from absence.models import ParametreCalculConges

        logger.info("Calcul acquisition pour %s - Année %s - Date %s",
                    employe, annee_reference, date_reference)

        # 1. Récupérer la convention
        convention = employe.convention_applicable
        if not convention:
            raise ValueError(f"Aucune convention applicable pour {employe}")

        # 2. Récupérer les paramètres
        try:
            parametres = convention.parametres_calcul
        except Exception:
            parametres = ParametreCalculConges.objects.create(
                configuration=convention
            )

        # 3. Calculer les mois travaillés
        mois_travailles = AcquisitionService.calculer_mois_travailles_jusquau(
            employe, annee_reference, date_reference
        )

        # 4. Vérifier le minimum requis
        if mois_travailles < parametres.mois_acquisition_min:
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
        plafond_applique = False

        # 6. Appliquer le plafond
        if jours_base > parametres.plafond_jours_an:
            jours_base = Decimal(str(parametres.plafond_jours_an))
            plafond_applique = True

        # 7. Ajouter l'ancienneté
        jours_anciennete = AcquisitionService.calculer_jours_anciennete(
            employe, parametres
        )

        jours_total = jours_base + jours_anciennete

        # 8. Temps partiel
        coefficient_tp = employe.coefficient_temps_travail
        if parametres.prise_compte_temps_partiel:
            jours_total = jours_total * coefficient_tp

        resultat_final = jours_total.quantize(Decimal('0.01'))

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

    @staticmethod
    def calculer_mois_travailles_jusquau(employe, annee_reference, date_limite):
        """
        Calcule le nombre de mois travaillés jusqu'à une date donnée.

        Args:
            employe: Instance de l'employé
            annee_reference: Année de référence
            date_limite: Date jusqu'à laquelle compter

        Returns:
            Decimal: Nombre de mois travaillés
        """
        if not employe.date_entree_entreprise:
            return Decimal('0.00')

        convention = employe.convention_applicable
        if not convention:
            return Decimal('0.00')

        debut_annee, fin_annee = convention.get_periode_acquisition(annee_reference)

        if date_limite < debut_annee:
            return Decimal('0.00')

        date_fin_effective = min(date_limite, fin_annee)
        date_debut = max(employe.date_entree_entreprise, debut_annee)
        date_fin = date_fin_effective

        if date_debut > date_fin:
            return Decimal('0.00')

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

            if mois == 12:
                current_date = date(annee + 1, 1, 1)
            else:
                current_date = date(annee, mois + 1, 1)

        return mois_total

    @staticmethod
    def calculer_jours_anciennete(employe, parametres):
        """
        Calcule les jours supplémentaires selon l'ancienneté.

        Args:
            employe: Instance de l'employé
            parametres: Paramètres de calcul

        Returns:
            Decimal: Nombre de jours supplémentaires
        """
        if not parametres.jours_supp_anciennete:
            return Decimal('0.00')

        anciennete = employe.anciennete_annees
        jours_supp = Decimal('0.00')

        paliers = sorted(
            [(int(k), v) for k, v in parametres.jours_supp_anciennete.items()],
            reverse=True
        )

        for annees, jours in paliers:
            if anciennete >= annees:
                jours_supp = Decimal(str(jours))
                break

        return jours_supp

    @staticmethod
    def calculer_acquisitions_employes(annee, employes=None):
        """
        Calcule les acquisitions pour plusieurs employés.

        Args:
            annee: Année de référence
            employes: Liste des employés (ou tous si None)

        Returns:
            dict: Résultats des calculs
        """
        from employee.models import ZY00
        from absence.models import AcquisitionConges

        if employes is None:
            employes = ZY00.objects.filter(statut='ACTIF')

        resultats = {
            'succes': [],
            'erreurs': [],
            'total': 0
        }

        for employe in employes:
            try:
                with transaction.atomic():
                    acquisition, created = AcquisitionConges.objects.get_or_create(
                        employe=employe,
                        annee_reference=annee,
                        defaults={
                            'jours_acquis': Decimal('0.00'),
                            'jours_pris': Decimal('0.00'),
                            'jours_solde': Decimal('0.00'),
                        }
                    )

                    # Recalculer
                    resultat = AcquisitionService.calculer_jours_acquis_au(
                        employe,
                        annee,
                        timezone.now().date()
                    )

                    acquisition.jours_acquis = resultat['jours_acquis']
                    acquisition.jours_solde = acquisition.jours_acquis - acquisition.jours_pris
                    acquisition.save()

                    resultats['succes'].append({
                        'employe': str(employe),
                        'jours_acquis': str(acquisition.jours_acquis),
                        'created': created
                    })

            except Exception as e:
                resultats['erreurs'].append({
                    'employe': str(employe),
                    'erreur': str(e)
                })

        resultats['total'] = len(resultats['succes'])
        return resultats

    @staticmethod
    def recalculer_acquisition(acquisition):
        """
        Recalcule une acquisition spécifique.

        Args:
            acquisition: Instance d'AcquisitionConges

        Returns:
            dict: Résultat du recalcul
        """
        resultat = AcquisitionService.calculer_jours_acquis_au(
            acquisition.employe,
            acquisition.annee_reference,
            timezone.now().date()
        )

        with transaction.atomic():
            acquisition.jours_acquis = resultat['jours_acquis']
            acquisition.jours_solde = acquisition.jours_acquis - acquisition.jours_pris
            acquisition.save()

        return {
            'jours_acquis': str(acquisition.jours_acquis),
            'jours_pris': str(acquisition.jours_pris),
            'jours_solde': str(acquisition.jours_solde),
            'detail': resultat['detail']
        }
