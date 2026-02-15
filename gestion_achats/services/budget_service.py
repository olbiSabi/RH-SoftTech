"""
Service métier pour la gestion des budgets.

Ce service encapsule toute la logique métier liée aux budgets,
incluant le contrôle de disponibilité, l'engagement, la commande et la consommation des montants,
ainsi que la gestion des alertes budgétaires.
"""

import logging
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count

from gestion_achats.models import (
    GACBudget,
    GACDemandeAchat,
    GACBonCommande,
    GACHistorique,
)
from gestion_achats.constants import (
    SEUIL_ALERTE_BUDGET_1,
    SEUIL_ALERTE_BUDGET_2,
)
from gestion_achats.exceptions import (
    BudgetError,
    BudgetInsuffisantError,
    ValidationError as GACValidationError,
)

logger = logging.getLogger(__name__)


class BudgetService:
    """Service pour la gestion des budgets."""

    @staticmethod
    def verifier_disponibilite(budget, montant):
        """
        Vérifie qu'un montant est disponible sur un budget.

        Args:
            budget: L'enveloppe budgétaire
            montant: Le montant à vérifier

        Returns:
            True si disponible

        Raises:
            BudgetInsuffisantError: Si le budget est insuffisant
        """
        disponible = budget.montant_disponible()

        if montant > disponible:
            raise BudgetInsuffisantError(
                f"Budget insuffisant. Disponible: {disponible} FCFA, Demandé: {montant} FCFA"
            )

        return True

    @staticmethod
    @transaction.atomic
    def engager_montant(budget, montant, reference):
        """
        Engage un montant sur un budget (validation demande).

        Args:
            budget: L'enveloppe budgétaire
            montant: Le montant à engager
            reference: Référence de l'engagement (ex: "DA DA-2026-0001")

        Returns:
            GACBudget: Le budget mis à jour

        Raises:
            BudgetInsuffisantError: Si le budget est insuffisant
        """
        try:
            # Vérifier la disponibilité
            BudgetService.verifier_disponibilite(budget, montant)

            # Engager
            budget.montant_engage += montant
            budget.save()

            # Vérifier les seuils d'alerte
            BudgetService._verifier_seuils_alerte(budget)

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=budget,
                action='ENGAGEMENT',
                utilisateur=None,
                details=f"Engagement de {montant} FCFA ({reference})"
            )

            logger.info(f"Montant {montant} FCFA engagé sur budget {budget.code} ({reference})")

            return budget

        except BudgetInsuffisantError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'engagement du montant: {str(e)}")
            raise BudgetError(f"Impossible d'engager le montant: {str(e)}")

    @staticmethod
    @transaction.atomic
    def commander_montant(budget, montant, reference):
        """
        Passe un montant de "engagé" à "commandé" (émission BC).

        Args:
            budget: L'enveloppe budgétaire
            montant: Le montant à commander
            reference: Référence de la commande (ex: "BC BC-2026-0001")

        Returns:
            GACBudget: Le budget mis à jour
        """
        try:
            # Vérifier que le montant engagé est suffisant
            if budget.montant_engage < montant:
                logger.warning(
                    f"Montant engagé ({budget.montant_engage}) inférieur au montant commandé ({montant}). "
                    f"Ajustement automatique."
                )
                # On ajuste en prenant la différence sur le disponible
                difference = montant - budget.montant_engage
                budget.montant_engage = Decimal('0')
                budget.montant_commande += montant
            else:
                # Décrémenter l'engagé et incrémenter le commandé
                budget.montant_engage -= montant
                budget.montant_commande += montant

            budget.save()

            # Vérifier les seuils d'alerte
            BudgetService._verifier_seuils_alerte(budget)

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=budget,
                action='COMMANDE',
                utilisateur=None,
                details=f"Commande de {montant} FCFA ({reference})"
            )

            logger.info(f"Montant {montant} FCFA commandé sur budget {budget.code} ({reference})")

            return budget

        except Exception as e:
            logger.error(f"Erreur lors de la commande du montant: {str(e)}")
            raise BudgetError(f"Impossible de commander le montant: {str(e)}")

    @staticmethod
    @transaction.atomic
    def consommer_montant(budget, montant, reference):
        """
        Passe un montant de "commandé" à "consommé" (réception).

        Args:
            budget: L'enveloppe budgétaire
            montant: Le montant à consommer
            reference: Référence de la consommation (ex: "Réception REC-2026-0001")

        Returns:
            GACBudget: Le budget mis à jour
        """
        try:
            # Vérifier que le montant commandé est suffisant
            if budget.montant_commande < montant:
                logger.warning(
                    f"Montant commandé ({budget.montant_commande}) inférieur au montant consommé ({montant}). "
                    f"Ajustement automatique."
                )
                # On ajuste
                difference = montant - budget.montant_commande
                budget.montant_commande = Decimal('0')
                budget.montant_consomme += montant
            else:
                # Décrémenter le commandé et incrémenter le consommé
                budget.montant_commande -= montant
                budget.montant_consomme += montant

            budget.save()

            # Vérifier les seuils d'alerte
            BudgetService._verifier_seuils_alerte(budget)

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=budget,
                action='CONSOMMATION',
                utilisateur=None,
                details=f"Consommation de {montant} FCFA ({reference})"
            )

            logger.info(f"Montant {montant} FCFA consommé sur budget {budget.code} ({reference})")

            return budget

        except Exception as e:
            logger.error(f"Erreur lors de la consommation du montant: {str(e)}")
            raise BudgetError(f"Impossible de consommer le montant: {str(e)}")

    @staticmethod
    @transaction.atomic
    def liberer_montant(budget, montant, reference):
        """
        Libère un montant engagé ou commandé (annulation).

        Args:
            budget: L'enveloppe budgétaire
            montant: Le montant à libérer
            reference: Référence de la libération

        Returns:
            GACBudget: Le budget mis à jour
        """
        try:
            # Libérer en priorité du montant commandé, puis engagé
            if budget.montant_commande >= montant:
                budget.montant_commande -= montant
            elif budget.montant_commande > 0:
                reste = montant - budget.montant_commande
                budget.montant_commande = Decimal('0')
                budget.montant_engage = max(Decimal('0'), budget.montant_engage - reste)
            else:
                budget.montant_engage = max(Decimal('0'), budget.montant_engage - montant)

            budget.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=budget,
                action='LIBERATION',
                utilisateur=None,
                details=f"Libération de {montant} FCFA ({reference})"
            )

            logger.info(f"Montant {montant} FCFA libéré sur budget {budget.code} ({reference})")

            return budget

        except Exception as e:
            logger.error(f"Erreur lors de la libération du montant: {str(e)}")
            raise BudgetError(f"Impossible de libérer le montant: {str(e)}")

    @staticmethod
    def _verifier_seuils_alerte(budget):
        """
        Vérifie si les seuils d'alerte budgétaire sont atteints.

        Args:
            budget: L'enveloppe budgétaire

        Returns:
            None (envoie des notifications si nécessaire)
        """
        taux = budget.taux_consommation()

        # Alerte critique (seuil 2)
        if taux >= budget.seuil_alerte_2 and not budget.alerte_2_envoyee:
            logger.warning(
                f"ALERTE CRITIQUE - Budget {budget.code}: {taux:.1f}% consommé "
                f"(seuil 2: {budget.seuil_alerte_2}%)"
            )

            budget.alerte_2_envoyee = True
            budget.save()

            from gestion_achats.services.notification_service import NotificationService
            NotificationService.notifier_alerte_budget(
                budget=budget,
                niveau='CRITIQUE',
                message=f"Budget {budget.code}: {taux:.1f}% consommé (seuil 2: {budget.seuil_alerte_2}%)"
            )

        # Alerte avertissement (seuil 1)
        elif taux >= budget.seuil_alerte_1 and not budget.alerte_1_envoyee:
            logger.warning(
                f"ALERTE AVERTISSEMENT - Budget {budget.code}: {taux:.1f}% consommé "
                f"(seuil 1: {budget.seuil_alerte_1}%)"
            )

            budget.alerte_1_envoyee = True
            budget.save()

            from gestion_achats.services.notification_service import NotificationService
            NotificationService.notifier_alerte_budget(
                budget=budget,
                niveau='AVERTISSEMENT',
                message=f"Budget {budget.code}: {taux:.1f}% consommé (seuil 1: {budget.seuil_alerte_1}%)"
            )

    @staticmethod
    @transaction.atomic
    def creer_budget(libelle, montant_initial, exercice, date_debut=None, date_fin=None,
                    departement=None, gestionnaire=None, description=None,
                    seuil_alerte_1=None, seuil_alerte_2=None, cree_par=None):
        """
        Crée une enveloppe budgétaire.

        Args:
            libelle: Libellé du budget
            montant_initial: Montant initial alloué
            exercice: Année de l'exercice
            date_debut: Date de début (optionnel)
            date_fin: Date de fin (optionnel)
            departement: Département concerné (optionnel)
            gestionnaire: Gestionnaire du budget (optionnel)
            description: Description du budget (optionnel)
            seuil_alerte_1: Premier seuil d'alerte en % (optionnel, défaut: constante)
            seuil_alerte_2: Deuxième seuil d'alerte en % (optionnel, défaut: constante)
            cree_par: Utilisateur créateur (optionnel)

        Returns:
            GACBudget: Le budget créé

        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Valider le montant
            if montant_initial <= 0:
                raise GACValidationError("Le montant initial doit être supérieur à 0")

            # Seuils d'alerte par défaut
            if seuil_alerte_1 is None:
                seuil_alerte_1 = SEUIL_ALERTE_BUDGET_1
            if seuil_alerte_2 is None:
                seuil_alerte_2 = SEUIL_ALERTE_BUDGET_2

            # Créer le budget (le code sera généré automatiquement par la méthode save())
            budget = GACBudget.objects.create(
                libelle=libelle,
                description=description or '',
                montant_initial=montant_initial,
                exercice=exercice,
                date_debut=date_debut,
                date_fin=date_fin,
                departement=departement,
                gestionnaire=gestionnaire,
                seuil_alerte_1=seuil_alerte_1,
                seuil_alerte_2=seuil_alerte_2,
                cree_par=cree_par
            )

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=budget,
                action='CREATION',
                utilisateur=cree_par,
                details=f"Création du budget {budget.code} - {libelle} ({montant_initial} FCFA)"
            )

            logger.info(f"Budget {budget.code} créé: {montant_initial} FCFA pour l'exercice {exercice}")

            return budget

        except GACValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création du budget: {str(e)}")
            raise BudgetError(f"Impossible de créer le budget: {str(e)}")

    @staticmethod
    def get_budgets_en_alerte():
        """
        Récupère les budgets ayant atteint un seuil d'alerte.

        Returns:
            list: Liste des budgets en alerte avec leurs taux
        """
        from django.utils import timezone
        today = timezone.now().date()
        budgets = GACBudget.objects.filter(date_fin__gte=today)
        budgets_en_alerte = []

        for budget in budgets:
            taux = budget.taux_consommation()
            if taux >= budget.seuil_alerte_1:
                niveau = 'CRITIQUE' if taux >= budget.seuil_alerte_2 else 'AVERTISSEMENT'
                budgets_en_alerte.append({
                    'budget': budget,
                    'code': budget.code,
                    'libelle': budget.libelle,
                    'taux': round(taux, 2),
                    'niveau': niveau,
                })

        return sorted(budgets_en_alerte, key=lambda x: x['taux'], reverse=True)

    @staticmethod
    def get_synthese_budgets(exercice=None):
        """
        Récupère la synthèse de tous les budgets.

        Args:
            exercice: Année de l'exercice (optionnel)

        Returns:
            dict: Synthèse budgétaire
        """
        from django.utils import timezone
        today = timezone.now().date()
        queryset = GACBudget.objects.filter(date_fin__gte=today)

        if exercice:
            queryset = queryset.filter(exercice=exercice)

        # Totaux
        totaux = queryset.aggregate(
            total_initial=Sum('montant_initial'),
            total_engage=Sum('montant_engage'),
            total_commande=Sum('montant_commande'),
            total_consomme=Sum('montant_consomme')
        )

        total_initial = totaux['total_initial'] or Decimal('0')
        total_engage = totaux['total_engage'] or Decimal('0')
        total_commande = totaux['total_commande'] or Decimal('0')
        total_consomme = totaux['total_consomme'] or Decimal('0')

        # Disponible
        total_disponible = total_initial - total_engage - total_commande - total_consomme

        # Taux de consommation global
        taux_consommation_global = (
            ((total_engage + total_commande + total_consomme) / total_initial * 100)
            if total_initial > 0 else 0
        )

        # Calcul des pourcentages individuels
        pct_engage = (total_engage / total_initial * 100) if total_initial > 0 else 0
        pct_commande = (total_commande / total_initial * 100) if total_initial > 0 else 0
        pct_consomme = (total_consomme / total_initial * 100) if total_initial > 0 else 0
        pct_disponible = (total_disponible / total_initial * 100) if total_initial > 0 else 0

        # Budgets en alerte
        budgets_en_alerte = BudgetService.get_budgets_en_alerte()

        # Agrégation par département
        par_departement = []
        from gestion_achats.models import ZDDE  # Import du modèle de département
        
        departements = ZDDE.objects.filter(
            id__in=queryset.values_list('departement_id', flat=True)
        ).distinct()
        
        for dept in departements:
            budgets_dept = queryset.filter(departement=dept)
            
            if budgets_dept.exists():
                totaux_dept = budgets_dept.aggregate(
                    montant_initial=Sum('montant_initial'),
                    montant_engage=Sum('montant_engage'),
                    montant_commande=Sum('montant_commande'),
                    montant_consomme=Sum('montant_consomme')
                )
                
                initial_dept = totaux_dept['montant_initial'] or Decimal('0')
                engage_dept = totaux_dept['montant_engage'] or Decimal('0')
                commande_dept = totaux_dept['montant_commande'] or Decimal('0')
                consomme_dept = totaux_dept['montant_consomme'] or Decimal('0')
                disponible_dept = initial_dept - engage_dept - commande_dept - consomme_dept
                
                total_utilise_dept = engage_dept + commande_dept + consomme_dept
                taux_dept = (total_utilise_dept / initial_dept * 100) if initial_dept > 0 else 0
                
                par_departement.append({
                    'nom': dept.LIBELLE or dept.CODE,
                    'nb_budgets': budgets_dept.count(),
                    'montant_initial': initial_dept,
                    'montant_engage': engage_dept,
                    'montant_commande': commande_dept,
                    'montant_consomme': consomme_dept,
                    'montant_disponible': disponible_dept,
                    'taux': round(taux_dept, 1)
                })

        return {
            'total_initial': total_initial,
            'total_engage': total_engage,
            'total_commande': total_commande,
            'total_consomme': total_consomme,
            'total_disponible': total_disponible,
            'taux_consommation_global': round(taux_consommation_global, 2),
            'pct_engage': round(pct_engage, 1),
            'pct_commande': round(pct_commande, 1),
            'pct_consomme': round(pct_consomme, 1),
            'pct_disponible': round(pct_disponible, 1),
            'nombre_budgets': queryset.count(),
            'budgets_en_alerte': budgets_en_alerte,
            'par_departement': par_departement,
        }

    @staticmethod
    def get_statistiques_budget(budget):
        """
        Récupère les statistiques détaillées d'un budget.

        Args:
            budget: L'enveloppe budgétaire

        Returns:
            dict: Statistiques du budget
        """
        # Demandes liées
        demandes = GACDemandeAchat.objects.filter(budget=budget)
        nombre_demandes = demandes.count()

        # Bons de commande liés
        bons_commande = GACBonCommande.objects.filter(
            demande_achat__budget=budget
        )
        nombre_bc = bons_commande.count()

        return {
            'code': budget.code,
            'libelle': budget.libelle,
            'exercice': budget.exercice,
            'montant_initial': budget.montant_initial,
            'montant_engage': budget.montant_engage,
            'montant_commande': budget.montant_commande,
            'montant_consomme': budget.montant_consomme,
            'montant_disponible': budget.montant_disponible(),
            'taux_consommation': budget.taux_consommation(),
            'nombre_demandes': nombre_demandes,
            'nombre_bons_commande': nombre_bc,
        }
