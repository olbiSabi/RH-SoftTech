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

        # 3. Calculer les mois travaillés et jours restants
        mois_travailles, jours_restants = AcquisitionService.calculer_mois_travailles_jusquau(
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

        # 5. Calcul de base : mois_complets × jours_par_mois
        jours_base = convention.jours_acquis_par_mois * mois_travailles

        # 6. Bonus fraction : reste >= 15 jours → +0.5 jours acquis
        if jours_restants >= 15:
            jours_base += Decimal('0.50')

        plafond_applique = False

        # 7. Appliquer le plafond
        if jours_base > parametres.plafond_jours_an:
            jours_base = Decimal(str(parametres.plafond_jours_an))
            plafond_applique = True

        # 8. Ajouter l'ancienneté
        jours_anciennete = AcquisitionService.calculer_jours_anciennete(
            employe, parametres
        )

        jours_total = jours_base + jours_anciennete

        # 9. Temps partiel
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
                'plafond_applique': plafond_applique,
                'jours_restants': jours_restants
            }
        }

    @staticmethod
    def calculer_mois_travailles_jusquau(employe, annee_reference, date_limite):
        """
        Calcule le nombre de mois travaillés jusqu'à une date donnée.

        Utilise la date_debut du contrat actif (ZYCO, actif=True).

        Args:
            employe: Instance de l'employé
            annee_reference: Année de référence
            date_limite: Date jusqu'à laquelle compter

        Returns:
            tuple: (mois_complets: Decimal, jours_restants: int)
        """
        from django.db.models import Q

        # Récupérer la date de début du contrat actif (ZYCO)
        contrat_actif = employe.contrats.filter(
            actif=True
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=date_limite)
        ).order_by('-date_debut').first()

        if not contrat_actif:
            return Decimal('0'), 0

        date_debut_contrat = contrat_actif.date_debut

        convention = employe.convention_applicable
        if not convention:
            return Decimal('0'), 0

        debut_annee, fin_annee = convention.get_periode_acquisition(annee_reference)

        if date_limite < debut_annee:
            return Decimal('0'), 0

        # Borner les dates dans la période d'acquisition
        date_fin = min(date_limite, fin_annee)
        date_debut = max(date_debut_contrat, debut_annee)

        if date_debut > date_fin:
            return Decimal('0'), 0

        # Nombre de jours = date_fin - date_debut (différence simple)
        jours_total = (date_fin - date_debut).days

        # Chaque tranche de 30 jours = 1 mois complet
        mois_complets = jours_total // 30
        jours_restants = jours_total % 30

        return Decimal(str(mois_complets)), jours_restants

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
