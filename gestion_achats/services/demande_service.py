"""
Service métier pour la gestion des demandes d'achat.

Ce service encapsule toute la logique métier liée aux demandes d'achat,
incluant la création, la validation, la conversion en BC, etc.
"""

import logging
from decimal import Decimal
from datetime import datetime
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError

from gestion_achats.models import (
    GACDemandeAchat,
    GACLigneDemandeAchat,
    GACBudget,
    GACHistorique,
)
from gestion_achats.constants import (
    STATUT_DEMANDE_BROUILLON,
    STATUT_DEMANDE_SOUMISE,
    STATUT_DEMANDE_VALIDEE_N1,
    STATUT_DEMANDE_VALIDEE_N2,
    STATUT_DEMANDE_REFUSEE,
    STATUT_DEMANDE_ANNULEE,
    STATUT_DEMANDE_CONVERTIE_BC,
    SEUIL_VALIDATION_N2,
)
from gestion_achats.exceptions import (
    DemandeError,
    WorkflowError,
    BudgetInsuffisantError,
    ValidationError as GACValidationError,
)
from gestion_achats.utils import determiner_validateur_n2

logger = logging.getLogger(__name__)


class DemandeService:
    """Service pour la gestion des demandes d'achat."""

    @staticmethod
    @transaction.atomic
    def creer_demande_brouillon(demandeur, objet, justification,
                                departement=None, projet=None, budget=None, priorite='NORMALE'):
        """
        Crée une demande d'achat en brouillon.

        Args:
            demandeur: L'employé qui crée la demande
            objet: L'objet de la demande
            justification: La justification métier
            departement: Le département concerné (optionnel)
            projet: Le projet lié (optionnel)
            budget: L'enveloppe budgétaire (optionnel)
            priorite: Priorité de la demande (par défaut NORMALE)

        Returns:
            GACDemandeAchat: La demande créée

        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Créer la demande (le numéro est généré automatiquement dans le modèle)
            demande = GACDemandeAchat.objects.create(
                demandeur=demandeur,
                objet=objet,
                justification=justification,
                departement=departement,
                projet=projet,
                budget=budget,
                priorite=priorite,
                statut=STATUT_DEMANDE_BROUILLON,
                cree_par=demandeur
            )

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=demande,
                action='CREATION',
                utilisateur=demandeur,
                details=f"Création de la demande {demande.numero} en brouillon"
            )

            logger.info(f"Demande {demande.numero} créée en brouillon par {demandeur}")

            return demande

        except Exception as e:
            logger.error(f"Erreur lors de la création de la demande: {str(e)}")
            raise DemandeError(f"Impossible de créer la demande: {str(e)}")

    @staticmethod
    @transaction.atomic
    def ajouter_ligne(demande, article, quantite, prix_unitaire, taux_tva=None, commentaire=''):
        """
        Ajoute une ligne à une demande d'achat.

        Args:
            demande: La demande d'achat
            article: L'article à ajouter
            quantite: La quantité
            prix_unitaire: Le prix unitaire HT
            taux_tva: Le taux de TVA (si None, utilise celui de l'article)
            commentaire: Commentaire sur la ligne (optionnel)

        Returns:
            GACLigneDemandeAchat: La ligne créée

        Raises:
            WorkflowError: Si la demande n'est pas en brouillon
            ValidationError: Si les données sont invalides
        """
        if demande.statut != STATUT_DEMANDE_BROUILLON:
            raise WorkflowError(
                "Impossible d'ajouter une ligne à une demande qui n'est pas en brouillon"
            )

        try:
            # Utiliser le taux TVA de l'article si non spécifié
            if taux_tva is None:
                taux_tva = article.taux_tva

            # Déterminer l'ordre
            dernier_ordre = demande.lignes.aggregate(
                max_ordre=models.Max('ordre')
            )['max_ordre'] or 0

            # Créer la ligne
            ligne = GACLigneDemandeAchat.objects.create(
                demande_achat=demande,
                article=article,
                quantite=quantite,
                prix_unitaire=prix_unitaire,
                taux_tva=taux_tva,
                commentaire=commentaire,
                ordre=dernier_ordre + 1
            )

            # Les montants sont calculés automatiquement dans le save() du modèle
            # Les totaux de la demande sont aussi recalculés automatiquement

            logger.info(
                f"Ligne ajoutée à la demande {demande.numero}: "
                f"{article.reference} x {quantite}"
            )

            return ligne

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de ligne: {str(e)}")
            raise DemandeError(f"Impossible d'ajouter la ligne: {str(e)}")

    @staticmethod
    @transaction.atomic
    def soumettre_demande(demande, utilisateur):
        """
        Soumet une demande pour validation.

        Args:
            demande: La demande à soumettre
            utilisateur: L'utilisateur qui soumet

        Returns:
            GACDemandeAchat: La demande mise à jour

        Raises:
            WorkflowError: Si la demande n'est pas en brouillon
            ValidationError: Si la demande est invalide (pas de lignes, etc.)
            BudgetInsuffisantError: Si le budget est insuffisant
        """
        if demande.statut != STATUT_DEMANDE_BROUILLON:
            raise WorkflowError("Seules les demandes en brouillon peuvent être soumises")

        if not demande.lignes.exists():
            raise GACValidationError("Impossible de soumettre une demande sans lignes")

        # Vérifier le budget si spécifié
        if demande.budget:
            DemandeService._verifier_budget(demande)

        # Déterminer le validateur N1 (manager du demandeur)
        try:
            manager = demande.demandeur.get_manager_departement()
            if manager:
                demande.validateur_n1 = manager
            else:
                # Si pas de manager département, essayer de trouver un manager ADMIN_GAC
                from employee.models import ZY00
                admin_gac_users = ZY00.objects.filter(
                    roles_attribues__role__CODE='ADMIN_GAC',
                    roles_attribues__actif=True
                ).exclude(uuid=demande.demandeur.uuid).first()
                
                if admin_gac_users:
                    demande.validateur_n1 = admin_gac_users
                else:
                    raise GACValidationError(
                        "Le demandeur n'a pas de manager assigné "
                        "et aucun administrateur GAC disponible pour la validation N1."
                    )
        except Exception as e:
            raise GACValidationError(
                f"Erreur lors de la détermination du validateur N1: {str(e)}"
            )

        # Si le montant dépasse le seuil, déterminer aussi le validateur N2
        from gestion_achats.models import GACParametres
        seuil = GACParametres.get_seuil_validation_n2()

        if demande.montant_total_ttc >= seuil:
            demande.validateur_n2 = determiner_validateur_n2(demande)
            if not demande.validateur_n2:
                raise GACValidationError(
                    f"Le montant de la demande ({demande.montant_total_ttc} FCFA) dépasse le seuil ({seuil} FCFA) "
                    "mais aucun validateur N2 n'a pu être trouvé. "
                    "Veuillez créer au moins un utilisateur avec le rôle ADMIN_GAC, ACHETEUR, "
                    "RESPONSABLE_ACHATS ou DIRECTEUR_GENERAL."
                )

        # Mettre à jour le statut
        ancien_statut = demande.statut
        demande.statut = STATUT_DEMANDE_SOUMISE
        demande.date_soumission = timezone.now()
        demande.save()

        # Créer l'historique
        GACHistorique.enregistrer_action(
            objet=demande,
            action='SOUMISSION',
            utilisateur=utilisateur,
            ancien_statut=ancien_statut,
            nouveau_statut=demande.statut,
            details=f"Demande soumise pour validation (Montant: {demande.montant_total_ttc} FCFA)"
        )

        # Les notifications sont gérées automatiquement par les signaux (signals.py)

        logger.info(
            f"Demande {demande.numero} soumise par {utilisateur} "
            f"pour validation N1 par {demande.validateur_n1}"
        )

        return demande

    @staticmethod
    @transaction.atomic
    def valider_n1(demande, validateur, commentaire=''):
        """
        Valide une demande au niveau N1 (manager).

        Args:
            demande: La demande à valider
            validateur: Le validateur N1
            commentaire: Commentaire de validation (optionnel)

        Returns:
            GACDemandeAchat: La demande mise à jour

        Raises:
            WorkflowError: Si la demande n'est pas au bon statut
            PermissionError: Si l'utilisateur n'est pas le validateur N1
        """
        if demande.statut != STATUT_DEMANDE_SOUMISE:
            raise WorkflowError(
                "Seules les demandes soumises peuvent être validées N1"
            )

        if demande.validateur_n1 != validateur:
            raise PermissionError(
                f"Seul {demande.validateur_n1} peut valider cette demande au niveau N1"
            )

        ancien_statut = demande.statut
        demande.statut = STATUT_DEMANDE_VALIDEE_N1
        demande.date_validation_n1 = timezone.now()
        demande.commentaire_validation_n1 = commentaire
        demande.save()

        # Si un validateur N2 est requis, passer en validation N2
        if demande.validateur_n2:
            nouveau_statut = STATUT_DEMANDE_VALIDEE_N1
            details = f"Validation N1 par {validateur}. En attente validation N2."
        else:
            # Sinon, la demande est complètement validée
            nouveau_statut = STATUT_DEMANDE_VALIDEE_N2
            demande.statut = nouveau_statut
            demande.date_validation_n2 = timezone.now()
            demande.save()
            details = f"Validation N1 par {validateur}. Demande validée (pas de N2 requis)."

        # Créer l'historique
        GACHistorique.enregistrer_action(
            objet=demande,
            action='VALIDATION_N1',
            utilisateur=validateur,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            details=details
        )

        # Les notifications sont gérées automatiquement par les signaux (signals.py)

        logger.info(f"Demande {demande.numero} validée N1 par {validateur}")

        return demande

    @staticmethod
    @transaction.atomic
    def valider_n2(demande, validateur, commentaire=''):
        """
        Valide une demande au niveau N2 (direction/acheteur).

        Args:
            demande: La demande à valider
            validateur: Le validateur N2
            commentaire: Commentaire de validation (optionnel)

        Returns:
            GACDemandeAchat: La demande mise à jour

        Raises:
            WorkflowError: Si la demande n'est pas au bon statut
            PermissionError: Si l'utilisateur n'est pas le validateur N2
        """
        # Si l'utilisateur a le rôle ADMIN_GAC et la demande est SOUMISE, valider N1 automatiquement
        if demande.statut == STATUT_DEMANDE_SOUMISE and validateur.has_role('ADMIN_GAC'):
            logger.info(
                f"ADMIN_GAC {validateur} valide automatiquement N1 pour la demande {demande.numero}"
            )
            # Valider N1 automatiquement
            demande.statut = STATUT_DEMANDE_VALIDEE_N1
            demande.date_validation_n1 = timezone.now()
            demande.commentaire_validation_n1 = f"Validation automatique N1 par ADMIN_GAC ({commentaire})" if commentaire else "Validation automatique N1 par ADMIN_GAC"
            demande.save()

            # Créer l'historique pour N1
            GACHistorique.enregistrer_action(
                objet=demande,
                action='VALIDATION_N1',
                utilisateur=validateur,
                ancien_statut=STATUT_DEMANDE_SOUMISE,
                nouveau_statut=STATUT_DEMANDE_VALIDEE_N1,
                details=f"Validation N1 automatique par ADMIN_GAC {validateur}"
            )

        if demande.statut != STATUT_DEMANDE_VALIDEE_N1:
            raise WorkflowError(
                "Seules les demandes validées N1 peuvent être validées N2"
            )

        # Pour ADMIN_GAC, pas besoin d'être le validateur N2 assigné
        if not validateur.has_role('ADMIN_GAC'):
            if demande.validateur_n2 != validateur:
                raise PermissionError(
                    f"Seul {demande.validateur_n2} peut valider cette demande au niveau N2"
                )

        ancien_statut = demande.statut
        demande.statut = STATUT_DEMANDE_VALIDEE_N2
        demande.date_validation_n2 = timezone.now()
        demande.commentaire_validation_n2 = commentaire
        demande.save()

        # Engager le budget si applicable
        if demande.budget:
            from gestion_achats.services.budget_service import BudgetService
            from gestion_achats.exceptions import BudgetInsuffisantError
            try:
                BudgetService.engager_montant(
                    budget=demande.budget,
                    montant=demande.montant_total_ttc,
                    reference=f"Demande {demande.numero}"
                )
                logger.info(
                    f"Budget {demande.budget.code} engagé pour {demande.montant_total_ttc} FCFA "
                    f"(demande {demande.numero})"
                )
            except BudgetInsuffisantError as e:
                logger.error(f"Erreur d'engagement budgétaire: {str(e)}")
                # Note: La demande reste validée mais l'engagement a échoué
                # On pourrait lever une exception ici pour annuler la validation
                # mais cela dépend de la politique de l'entreprise

        # Créer l'historique
        GACHistorique.enregistrer_action(
            objet=demande,
            action='VALIDATION_N2',
            utilisateur=validateur,
            ancien_statut=ancien_statut,
            nouveau_statut=demande.statut,
            details=f"Validation N2 par {validateur}. Demande complètement validée."
        )

        # Les notifications sont gérées automatiquement par les signaux (signals.py)

        logger.info(f"Demande {demande.numero} validée N2 par {validateur}")

        return demande

    @staticmethod
    @transaction.atomic
    def refuser_demande(demande, validateur, motif):
        """
        Refuse une demande.

        Args:
            demande: La demande à refuser
            validateur: L'utilisateur qui refuse
            motif: Le motif du refus

        Returns:
            GACDemandeAchat: La demande mise à jour

        Raises:
            WorkflowError: Si la demande ne peut pas être refusée
        """
        if demande.statut not in [STATUT_DEMANDE_SOUMISE, STATUT_DEMANDE_VALIDEE_N1]:
            raise WorkflowError(
                "Seules les demandes soumises ou validées N1 peuvent être refusées"
            )

        ancien_statut = demande.statut
        demande.statut = STATUT_DEMANDE_REFUSEE
        demande.motif_refus = motif
        demande.date_refus = timezone.now()
        demande.save()

        # Libérer le budget si la demande était validée N2 (donc engagée)
        if ancien_statut == STATUT_DEMANDE_VALIDEE_N2 and demande.budget:
            from gestion_achats.services.budget_service import BudgetService
            try:
                BudgetService.liberer_montant(
                    budget=demande.budget,
                    montant=demande.montant_total_ttc,
                    reference=f"Refus demande {demande.numero}"
                )
                logger.info(
                    f"Budget {demande.budget.code} libéré de {demande.montant_total_ttc} FCFA "
                    f"suite au refus de la demande {demande.numero}"
                )
            except Exception as e:
                logger.error(f"Erreur lors de la libération du budget: {str(e)}")

        # Créer l'historique
        GACHistorique.enregistrer_action(
            objet=demande,
            action='REFUS',
            utilisateur=validateur,
            ancien_statut=ancien_statut,
            nouveau_statut=demande.statut,
            details=f"Demande refusée par {validateur}. Motif: {motif}"
        )

        # Les notifications sont gérées automatiquement par les signaux (signals.py)
        # Le motif est récupéré depuis demande.motif_refus par le signal

        logger.info(f"Demande {demande.numero} refusée par {validateur}")

        return demande

    @staticmethod
    @transaction.atomic
    def annuler_demande(demande, utilisateur, motif):
        """
        Annule une demande.

        Args:
            demande: La demande à annuler
            utilisateur: L'utilisateur qui annule
            motif: Le motif d'annulation

        Returns:
            GACDemandeAchat: La demande mise à jour

        Raises:
            WorkflowError: Si la demande ne peut pas être annulée
        """
        if demande.statut == STATUT_DEMANDE_CONVERTIE_BC:
            raise WorkflowError(
                "Impossible d'annuler une demande déjà convertie en bon de commande"
            )

        if demande.statut == STATUT_DEMANDE_ANNULEE:
            raise WorkflowError("Cette demande est déjà annulée")

        ancien_statut = demande.statut
        demande.statut = STATUT_DEMANDE_ANNULEE
        demande.motif_annulation = motif
        demande.date_annulation = timezone.now()
        demande.save()

        # Libérer le budget si la demande était validée N2 (donc engagée)
        if ancien_statut == STATUT_DEMANDE_VALIDEE_N2 and demande.budget:
            from gestion_achats.services.budget_service import BudgetService
            try:
                BudgetService.liberer_montant(
                    budget=demande.budget,
                    montant=demande.montant_total_ttc,
                    reference=f"Annulation demande {demande.numero}"
                )
                logger.info(
                    f"Budget {demande.budget.code} libéré de {demande.montant_total_ttc} FCFA "
                    f"suite à l'annulation de la demande {demande.numero}"
                )
            except Exception as e:
                logger.error(f"Erreur lors de la libération du budget: {str(e)}")

        # Créer l'historique
        GACHistorique.enregistrer_action(
            objet=demande,
            action='ANNULATION',
            utilisateur=utilisateur,
            ancien_statut=ancien_statut,
            nouveau_statut=demande.statut,
            details=f"Demande annulée par {utilisateur}. Motif: {motif}"
        )

        # Les notifications sont gérées automatiquement par les signaux (signals.py)

        logger.info(f"Demande {demande.numero} annulée par {utilisateur}")

        return demande

    @staticmethod
    def _verifier_budget(demande):
        """
        Vérifie que le budget est suffisant pour la demande.

        Args:
            demande: La demande à vérifier

        Raises:
            BudgetInsuffisantError: Si le budget est insuffisant
        """
        if not demande.budget:
            return

        budget = demande.budget
        montant_disponible = budget.montant_disponible()

        if montant_disponible < demande.montant_total_ttc:
            raise BudgetInsuffisantError(
                f"Budget insuffisant. Disponible: {montant_disponible} FCFA, "
                f"Demandé: {demande.montant_total_ttc} FCFA"
            )

    @staticmethod
    def get_demandes_a_valider_n1(validateur):
        """
        Récupère les demandes à valider pour un validateur N1.

        Args:
            validateur: Le validateur N1

        Returns:
            QuerySet: Les demandes à valider
        """
        return GACDemandeAchat.objects.filter(
            statut=STATUT_DEMANDE_SOUMISE,
            validateur_n1=validateur
        ).order_by('-date_soumission')

    @staticmethod
    def get_demandes_a_valider_n2(validateur):
        """
        Récupère les demandes à valider pour un validateur N2.

        Args:
            validateur: Le validateur N2

        Returns:
            QuerySet: Les demandes à valider
        """
        return GACDemandeAchat.objects.filter(
            statut=STATUT_DEMANDE_VALIDEE_N1,
            validateur_n2=validateur
        ).order_by('-date_validation_n1')
