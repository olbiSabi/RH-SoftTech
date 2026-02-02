"""
Service métier pour la gestion des réceptions.

Ce service encapsule toute la logique métier liée aux réceptions de marchandises,
incluant la création, l'enregistrement des quantités, la validation et le contrôle de conformité.
"""

import logging
from decimal import Decimal
from datetime import datetime
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum

from gestion_achats.models import (
    GACReception,
    GACLigneReception,
    GACBonCommande,
    GACHistorique,
)
from gestion_achats.constants import (
    STATUT_RECEPTION_BROUILLON,
    STATUT_RECEPTION_VALIDEE,
    STATUT_RECEPTION_ANNULEE,
)
from gestion_achats.exceptions import (
    ReceptionError,
    WorkflowError,
    ValidationError as GACValidationError,
)

logger = logging.getLogger(__name__)


class ReceptionService:
    """Service pour la gestion des réceptions de marchandises."""

    @staticmethod
    @transaction.atomic
    def creer_reception(bon_commande, receptionnaire, date_reception=None):
        """
        Crée une réception de marchandises.

        Args:
            bon_commande: Le bon de commande concerné
            receptionnaire: La personne qui réceptionne
            date_reception: Date de réception (optionnel, défaut: aujourd'hui)

        Returns:
            GACReception: La réception créée

        Raises:
            ValidationError: Si les données sont invalides
            WorkflowError: Si le BC ne peut pas être réceptionné
        """
        # Vérifier que le BC peut être réceptionné
        if bon_commande.statut not in ['CONFIRME', 'RECU_PARTIEL']:
            raise WorkflowError(
                "Seuls les BC confirmés ou partiellement reçus peuvent être réceptionnés"
            )

        try:
            # Créer la réception (le numéro est généré automatiquement dans le modèle)
            reception = GACReception.objects.create(
                bon_commande=bon_commande,
                receptionnaire=receptionnaire,
                date_reception=date_reception or timezone.now().date(),
                statut=STATUT_RECEPTION_BROUILLON,
                cree_par=receptionnaire
            )

            # Copier les lignes du BC comme lignes de réception
            # On crée une ligne de réception pour chaque ligne BC non totalement reçue
            for ligne_bc in bon_commande.lignes.all():
                # Calculer la quantité restante à recevoir
                quantite_deja_recue = ligne_bc.quantite_recue or Decimal('0')
                quantite_restante = ligne_bc.quantite_commandee - quantite_deja_recue

                if quantite_restante > 0:
                    GACLigneReception.objects.create(
                        reception=reception,
                        ligne_bon_commande=ligne_bc,
                        quantite_recue=Decimal('0'),
                        quantite_acceptee=Decimal('0'),
                        quantite_refusee=Decimal('0'),
                        conforme=True  # Par défaut conforme
                    )

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=reception,
                action='CREATION',
                utilisateur=receptionnaire,
                details=f"Création de la réception {reception.numero} pour BC {bon_commande.numero}"
            )

            logger.info(
                f"Réception {reception.numero} créée par {receptionnaire} "
                f"pour BC {bon_commande.numero}"
            )

            return reception

        except Exception as e:
            logger.error(f"Erreur lors de la création de la réception: {str(e)}")
            raise ReceptionError(f"Impossible de créer la réception: {str(e)}")

    @staticmethod
    @transaction.atomic
    def enregistrer_ligne_reception(ligne_reception, quantite_recue, quantite_acceptee,
                                    quantite_refusee, conforme, commentaire=None):
        """
        Enregistre les quantités reçues pour une ligne.

        Args:
            ligne_reception: La ligne de réception concernée
            quantite_recue: Quantité totale reçue
            quantite_acceptee: Quantité acceptée
            quantite_refusee: Quantité refusée
            conforme: Conformité globale de la ligne
            commentaire: Commentaire sur la réception (optionnel)

        Returns:
            GACLigneReception: La ligne mise à jour

        Raises:
            ValidationError: Si les quantités sont incohérentes
            WorkflowError: Si la réception n'est pas en brouillon
        """
        # Vérifier que la réception est en brouillon
        if ligne_reception.reception.statut != STATUT_RECEPTION_BROUILLON:
            raise WorkflowError(
                "Impossible de modifier une ligne de réception validée"
            )

        # Vérifier la cohérence des quantités
        if quantite_acceptee + quantite_refusee != quantite_recue:
            raise GACValidationError(
                "La somme des quantités acceptée et refusée doit égaler la quantité reçue"
            )

        # Vérifier que la quantité reçue ne dépasse pas la quantité commandée
        ligne_bc = ligne_reception.ligne_bon_commande
        quantite_deja_recue = ligne_bc.quantite_recue or Decimal('0')
        quantite_restante = ligne_bc.quantite_commandee - quantite_deja_recue

        if quantite_recue > quantite_restante:
            raise GACValidationError(
                f"Quantité reçue ({quantite_recue}) supérieure à la quantité restante "
                f"à recevoir ({quantite_restante})"
            )

        try:
            # Mettre à jour la ligne de réception
            ligne_reception.quantite_recue = quantite_recue
            ligne_reception.quantite_acceptee = quantite_acceptee
            ligne_reception.quantite_refusee = quantite_refusee
            ligne_reception.conforme = conforme
            ligne_reception.commentaire_reception = commentaire
            ligne_reception.save()

            logger.info(
                f"Ligne réception {ligne_reception.id} enregistrée: "
                f"{quantite_acceptee} acceptées, {quantite_refusee} refusées"
            )

            return ligne_reception

        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la ligne: {str(e)}")
            raise ReceptionError(f"Impossible d'enregistrer la ligne: {str(e)}")

    @staticmethod
    @transaction.atomic
    def valider_reception(reception, utilisateur):
        """
        Valide une réception complète.

        Args:
            reception: La réception à valider
            utilisateur: L'utilisateur qui valide

        Returns:
            GACReception: La réception validée

        Raises:
            ValidationError: Si la réception est invalide
            WorkflowError: Si la réception n'est pas en brouillon
        """
        if reception.statut != STATUT_RECEPTION_BROUILLON:
            raise WorkflowError("Seules les réceptions en brouillon peuvent être validées")

        lignes = reception.lignes.all()
        if not lignes.exists():
            raise GACValidationError("La réception doit contenir au moins une ligne")

        # Vérifier que toutes les lignes ont des quantités renseignées
        for ligne in lignes:
            if ligne.quantite_recue is None or ligne.quantite_recue == 0:
                raise GACValidationError(
                    f"Toutes les lignes doivent avoir une quantité reçue. "
                    f"Ligne article {ligne.ligne_bon_commande.article.reference} non renseignée."
                )

        try:
            # Déterminer la conformité globale
            conformite_globale = all(ligne.conforme for ligne in lignes)

            # Mettre à jour la réception
            reception.statut = STATUT_RECEPTION_VALIDEE
            reception.date_validation = timezone.now()
            reception.conforme = conformite_globale
            reception.save()

            # Mettre à jour les quantités reçues sur les lignes BC
            for ligne in lignes:
                ligne_bc = ligne.ligne_bon_commande

                # Recalculer le total reçu pour cette ligne BC
                total_accepte = ligne_bc.lignes_reception.filter(
                    reception__statut=STATUT_RECEPTION_VALIDEE
                ).aggregate(
                    total=Sum('quantite_acceptee')
                )['total'] or Decimal('0')

                ligne_bc.quantite_recue = total_accepte
                ligne_bc.save()

            # Mettre à jour le statut du BC
            bc = reception.bon_commande

            # Vérifier si le BC est totalement reçu
            bc_totalement_recu = True
            for ligne_bc in bc.lignes.all():
                if ligne_bc.quantite_recue < ligne_bc.quantite_commandee:
                    bc_totalement_recu = False
                    break

            ancien_statut_bc = bc.statut
            if bc_totalement_recu:
                bc.statut = 'RECU_COMPLET'
                bc.date_reception_complete = timezone.now()
            else:
                bc.statut = 'RECU_PARTIEL'

            bc.save()

            # Consommer le budget si applicable
            if bc.demande_achat and bc.demande_achat.budget:
                # Calculer le montant à consommer (quantités acceptées uniquement)
                montant_recu = sum(
                    ligne.quantite_acceptee * ligne.ligne_bon_commande.prix_unitaire *
                    (1 + ligne.ligne_bon_commande.taux_tva / 100)
                    for ligne in lignes
                )

                from gestion_achats.services.budget_service import BudgetService
                BudgetService.consommer_montant(
                    budget=bc.demande_achat.budget,
                    montant=montant_recu,
                    reference=f"Réception {reception.numero}"
                )

            # Créer l'historique pour la réception
            GACHistorique.enregistrer_action(
                objet=reception,
                action='VALIDATION',
                utilisateur=utilisateur,
                details=f"Réception validée. Conformité: {'Oui' if conformite_globale else 'Non'}"
            )

            # Créer l'historique pour le BC
            GACHistorique.enregistrer_action(
                objet=bc,
                action='RECEPTION',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut_bc,
                nouveau_statut=bc.statut,
                details=f"Réception {reception.numero} validée. Statut: {bc.get_statut_display()}"
            )

            # TODO: Notifier l'acheteur et le demandeur
            # NotificationService.notifier_reception_validee(reception)

            logger.info(
                f"Réception {reception.numero} validée par {utilisateur}. "
                f"BC {bc.numero} statut: {bc.statut}"
            )

            return reception

        except Exception as e:
            logger.error(f"Erreur lors de la validation de la réception: {str(e)}")
            raise ReceptionError(f"Impossible de valider la réception: {str(e)}")

    @staticmethod
    @transaction.atomic
    def annuler_reception(reception, utilisateur, motif):
        """
        Annule une réception.

        Args:
            reception: La réception à annuler
            utilisateur: L'utilisateur qui annule
            motif: Le motif d'annulation

        Returns:
            GACReception: La réception annulée

        Raises:
            WorkflowError: Si la réception ne peut pas être annulée
        """
        if reception.statut == STATUT_RECEPTION_ANNULEE:
            raise WorkflowError("Cette réception est déjà annulée")

        try:
            # Si la réception était validée, il faut mettre à jour les quantités du BC
            if reception.statut == STATUT_RECEPTION_VALIDEE:
                for ligne in reception.lignes.all():
                    ligne_bc = ligne.ligne_bon_commande

                    # Recalculer le total reçu en excluant cette réception
                    total_accepte = ligne_bc.lignes_reception.filter(
                        reception__statut=STATUT_RECEPTION_VALIDEE
                    ).exclude(
                        reception=reception
                    ).aggregate(
                        total=Sum('quantite_acceptee')
                    )['total'] or Decimal('0')

                    ligne_bc.quantite_recue = total_accepte
                    ligne_bc.save()

                # Recalculer le statut du BC
                bc = reception.bon_commande
                bc_totalement_recu = all(
                    ligne_bc.quantite_recue >= ligne_bc.quantite_commandee
                    for ligne_bc in bc.lignes.all()
                )

                ancien_statut_bc = bc.statut
                if bc_totalement_recu:
                    bc.statut = 'RECU_COMPLET'
                elif any(ligne_bc.quantite_recue > 0 for ligne_bc in bc.lignes.all()):
                    bc.statut = 'RECU_PARTIEL'
                else:
                    bc.statut = 'CONFIRME'

                bc.save()

                # Si budget, libérer le montant consommé
                if bc.demande_achat and bc.demande_achat.budget:
                    montant_a_liberer = sum(
                        ligne.quantite_acceptee * ligne.ligne_bon_commande.prix_unitaire *
                        (1 + ligne.ligne_bon_commande.taux_tva / 100)
                        for ligne in reception.lignes.all()
                    )

                    from gestion_achats.services.budget_service import BudgetService
                    BudgetService.liberer_montant(
                        budget=bc.demande_achat.budget,
                        montant=montant_a_liberer,
                        reference=f"Annulation réception {reception.numero}"
                    )

            # Annuler la réception
            ancien_statut = reception.statut
            reception.statut = STATUT_RECEPTION_ANNULEE
            reception.motif_annulation = motif
            reception.date_annulation = timezone.now()
            reception.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=reception,
                action='ANNULATION',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut,
                nouveau_statut=reception.statut,
                details=f"Réception annulée par {utilisateur}. Motif: {motif}"
            )

            logger.info(f"Réception {reception.numero} annulée par {utilisateur}")

            return reception

        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de la réception: {str(e)}")
            raise ReceptionError(f"Impossible d'annuler la réception: {str(e)}")

    @staticmethod
    def get_receptions_en_attente():
        """
        Récupère les réceptions en attente de validation.

        Returns:
            QuerySet: Réceptions en brouillon
        """
        return GACReception.objects.filter(
            statut=STATUT_RECEPTION_BROUILLON
        ).order_by('-date_reception')

    @staticmethod
    def get_receptions_non_conformes(date_debut=None, date_fin=None):
        """
        Récupère les réceptions non conformes.

        Args:
            date_debut: Date de début de la période (optionnel)
            date_fin: Date de fin de la période (optionnel)

        Returns:
            QuerySet: Réceptions non conformes
        """
        queryset = GACReception.objects.filter(
            statut=STATUT_RECEPTION_VALIDEE,
            conforme=False
        )

        if date_debut:
            queryset = queryset.filter(date_reception__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_reception__lte=date_fin)

        return queryset.order_by('-date_reception')

    @staticmethod
    def get_statistiques_receptions(date_debut=None, date_fin=None):
        """
        Récupère les statistiques sur les réceptions.

        Args:
            date_debut: Date de début de la période (optionnel)
            date_fin: Date de fin de la période (optionnel)

        Returns:
            dict: Statistiques
        """
        from django.db.models import Count, Avg

        queryset = GACReception.objects.filter(statut=STATUT_RECEPTION_VALIDEE)

        if date_debut:
            queryset = queryset.filter(date_reception__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_reception__lte=date_fin)

        # Total réceptions
        total_receptions = queryset.count()

        # Réceptions conformes vs non conformes
        conformes = queryset.filter(conforme=True).count()
        non_conformes = queryset.filter(conforme=False).count()

        # Taux de conformité
        taux_conformite = (conformes / total_receptions * 100) if total_receptions > 0 else 0

        # Statistiques par statut
        par_statut = GACReception.objects.values('statut').annotate(
            nombre=Count('id')
        )

        return {
            'total_receptions': total_receptions,
            'receptions_conformes': conformes,
            'receptions_non_conformes': non_conformes,
            'taux_conformite': round(taux_conformite, 2),
            'par_statut': {item['statut']: item['nombre'] for item in par_statut},
        }
