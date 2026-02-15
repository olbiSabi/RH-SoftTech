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
        if bon_commande.statut not in ['ENVOYE', 'CONFIRME', 'RECU_PARTIEL']:
            raise WorkflowError(
                "Seuls les BC envoyés, confirmés ou partiellement reçus peuvent être réceptionnés"
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

            # Note: Les lignes de réception sont créées par la vue,
            # pas automatiquement par le service, pour permettre
            # la saisie des quantités réelles dès la création

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

            # Les notifications sont gérées automatiquement par les signaux (signals.py)

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

    @staticmethod
    @transaction.atomic
    def creer_bon_retour(reception, lignes_non_conformes, motif_retour, utilisateur):
        """
        Crée un bon de retour fournisseur pour les articles non conformes.

        Args:
            reception: La réception concernée
            lignes_non_conformes: Liste de tuples (ligne_reception, quantite_a_retourner)
            motif_retour: Motif général du retour
            utilisateur: L'utilisateur qui crée le bon de retour

        Returns:
            GACBonRetour: Le bon de retour créé

        Raises:
            ValidationError: Si les données sont invalides
            WorkflowError: Si la réception n'est pas validée
        """
        from gestion_achats.models import GACBonRetour, GACLigneBonRetour

        if reception.statut != STATUT_RECEPTION_VALIDEE:
            raise WorkflowError(
                "Un bon de retour ne peut être créé que pour une réception validée"
            )

        if not lignes_non_conformes:
            raise GACValidationError(
                "Au moins une ligne non conforme doit être spécifiée"
            )

        try:
            # Créer le bon de retour
            bon_retour = GACBonRetour.objects.create(
                reception=reception,
                bon_commande=reception.bon_commande,
                fournisseur=reception.bon_commande.fournisseur,
                motif_retour=motif_retour,
                cree_par=utilisateur,
                statut='BROUILLON'
            )

            # Créer les lignes du bon de retour
            ordre = 0
            for ligne_reception, quantite_retournee in lignes_non_conformes:
                ordre += 1

                # Vérifier que la quantité à retourner ne dépasse pas la quantité refusée
                if quantite_retournee > ligne_reception.quantite_refusee:
                    raise GACValidationError(
                        f"La quantité à retourner ({quantite_retournee}) ne peut pas dépasser "
                        f"la quantité refusée ({ligne_reception.quantite_refusee})"
                    )

                ligne_bc = ligne_reception.ligne_bon_commande

                GACLigneBonRetour.objects.create(
                    bon_retour=bon_retour,
                    ligne_reception=ligne_reception,
                    article=ligne_bc.article,
                    quantite_retournee=quantite_retournee,
                    prix_unitaire=ligne_bc.prix_unitaire,
                    taux_tva=ligne_bc.taux_tva,
                    motif_retour=ligne_reception.motif_refus or motif_retour,
                    commentaire=ligne_reception.commentaire_reception,
                    ordre=ordre
                )

            # Recalculer les totaux
            bon_retour.calculer_totaux()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=bon_retour,
                action='CREATION',
                utilisateur=utilisateur,
                details=f"Bon de retour {bon_retour.numero} créé pour réception {reception.numero}"
            )

            logger.info(
                f"Bon de retour {bon_retour.numero} créé par {utilisateur} "
                f"pour réception {reception.numero}"
            )

            return bon_retour

        except Exception as e:
            logger.error(f"Erreur lors de la création du bon de retour: {str(e)}")
            raise ReceptionError(f"Impossible de créer le bon de retour: {str(e)}")

    @staticmethod
    def evaluer_qualite_fournisseur(fournisseur, periode_mois=12):
        """
        Évalue la qualité d'un fournisseur basée sur ses réceptions.

        Args:
            fournisseur: Le fournisseur à évaluer
            periode_mois: Nombre de mois à analyser (défaut: 12)

        Returns:
            dict: Statistiques de qualité du fournisseur
        """
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta

        date_debut = timezone.now() - relativedelta(months=periode_mois)

        # Récupérer toutes les réceptions validées du fournisseur
        receptions = GACReception.objects.filter(
            bon_commande__fournisseur=fournisseur,
            statut=STATUT_RECEPTION_VALIDEE,
            date_reception__gte=date_debut
        )

        total_receptions = receptions.count()
        if total_receptions == 0:
            return {
                'fournisseur': fournisseur,
                'periode_mois': periode_mois,
                'total_receptions': 0,
                'receptions_conformes': 0,
                'receptions_non_conformes': 0,
                'taux_conformite': 0,
                'total_articles_recus': 0,
                'total_articles_acceptes': 0,
                'total_articles_refuses': 0,
                'taux_acceptation': 0,
                'delais_moyen_livraison': None,
                'nombre_retours': 0,
                'note_qualite': 0,
                'commentaire': 'Aucune réception dans la période'
            }

        # Statistiques de conformité
        receptions_conformes = receptions.filter(conforme=True).count()
        receptions_non_conformes = receptions.filter(conforme=False).count()
        taux_conformite = (receptions_conformes / total_receptions * 100) if total_receptions > 0 else 0

        # Statistiques sur les quantités
        total_articles_recus = Decimal('0')
        total_articles_acceptes = Decimal('0')
        total_articles_refuses = Decimal('0')

        for reception in receptions:
            for ligne in reception.lignes.all():
                total_articles_recus += ligne.quantite_recue
                total_articles_acceptes += ligne.quantite_acceptee
                total_articles_refuses += ligne.quantite_refusee

        taux_acceptation = (total_articles_acceptes / total_articles_recus * 100) if total_articles_recus > 0 else 0

        # Délai moyen de livraison
        delais = []
        for reception in receptions:
            bc = reception.bon_commande
            if bc.date_emission and reception.date_reception:
                delai = (reception.date_reception - bc.date_emission.date()).days
                delais.append(delai)

        delais_moyen = sum(delais) / len(delais) if delais else None

        # Nombre de bons de retour
        from gestion_achats.models import GACBonRetour
        nombre_retours = GACBonRetour.objects.filter(
            fournisseur=fournisseur,
            date_creation__gte=date_debut
        ).count()

        # Calcul de la note de qualité (0-100)
        # - 40% taux conformité réceptions
        # - 40% taux acceptation articles
        # - 10% délai moyen (bonus/malus)
        # - 10% nombre de retours (malus)
        note_qualite = 0
        note_qualite += taux_conformite * 0.4
        note_qualite += taux_acceptation * 0.4

        # Bonus/Malus délai (si délai moyen < 10 jours: +10, si > 30 jours: -10)
        if delais_moyen:
            if delais_moyen < 10:
                note_qualite += 10
            elif delais_moyen > 30:
                note_qualite -= 10

        # Malus retours (chaque retour = -5 points, max -10)
        note_qualite -= min(nombre_retours * 5, 10)

        # S'assurer que la note est entre 0 et 100
        note_qualite = max(0, min(100, note_qualite))

        # Déterminer le commentaire
        if note_qualite >= 90:
            commentaire = "Excellent fournisseur"
        elif note_qualite >= 75:
            commentaire = "Bon fournisseur"
        elif note_qualite >= 60:
            commentaire = "Fournisseur correct"
        elif note_qualite >= 40:
            commentaire = "Fournisseur à surveiller"
        else:
            commentaire = "Fournisseur problématique"

        return {
            'fournisseur': fournisseur,
            'periode_mois': periode_mois,
            'total_receptions': total_receptions,
            'receptions_conformes': receptions_conformes,
            'receptions_non_conformes': receptions_non_conformes,
            'taux_conformite': round(taux_conformite, 2),
            'total_articles_recus': float(total_articles_recus),
            'total_articles_acceptes': float(total_articles_acceptes),
            'total_articles_refuses': float(total_articles_refuses),
            'taux_acceptation': round(taux_acceptation, 2),
            'delais_moyen_livraison': round(delais_moyen, 1) if delais_moyen else None,
            'nombre_retours': nombre_retours,
            'note_qualite': round(note_qualite, 1),
            'commentaire': commentaire,
        }

    @staticmethod
    def verifier_conformite_ligne(ligne_reception):
        """
        Vérifie en détail la conformité d'une ligne de réception.

        Args:
            ligne_reception: La ligne à vérifier

        Returns:
            dict: Résultat de la vérification avec détails
        """
        anomalies = []
        warnings = []

        ligne_bc = ligne_reception.ligne_bon_commande

        # Vérifier les quantités
        if ligne_reception.quantite_recue != ligne_reception.quantite_acceptee + ligne_reception.quantite_refusee:
            anomalies.append({
                'type': 'QUANTITE',
                'severite': 'CRITIQUE',
                'message': 'La somme des quantités acceptée et refusée ne correspond pas à la quantité reçue'
            })

        # Vérifier le dépassement de commande
        if ligne_reception.quantite_recue > ligne_bc.quantite_commandee:
            warnings.append({
                'type': 'SURLIVRAISON',
                'severite': 'ATTENTION',
                'message': f'Quantité reçue ({ligne_reception.quantite_recue}) supérieure à la quantité commandée ({ligne_bc.quantite_commandee})'
            })

        # Vérifier les sous-livraisons importantes
        if ligne_reception.quantite_recue < ligne_bc.quantite_commandee * Decimal('0.8'):
            warnings.append({
                'type': 'SOUSLIVRAISON',
                'severite': 'ATTENTION',
                'message': f'Sous-livraison importante: {ligne_reception.quantite_recue} reçus sur {ligne_bc.quantite_commandee} commandés'
            })

        # Vérifier les refus
        if ligne_reception.quantite_refusee > 0:
            if not ligne_reception.motif_refus:
                anomalies.append({
                    'type': 'MOTIF_REFUS',
                    'severite': 'IMPORTANTE',
                    'message': 'Un motif de refus doit être renseigné pour les articles refusés'
                })

            # Taux de refus élevé
            taux_refus = (ligne_reception.quantite_refusee / ligne_reception.quantite_recue * 100) if ligne_reception.quantite_recue > 0 else 0
            if taux_refus > 10:
                warnings.append({
                    'type': 'TAUX_REFUS',
                    'severite': 'ATTENTION',
                    'message': f'Taux de refus élevé: {taux_refus:.1f}%'
                })

        # Vérifier la conformité globale
        conforme_globale = len(anomalies) == 0 and ligne_reception.quantite_refusee == 0

        return {
            'ligne_reception': ligne_reception,
            'conforme': conforme_globale,
            'anomalies': anomalies,
            'warnings': warnings,
            'quantite_commandee': float(ligne_bc.quantite_commandee),
            'quantite_recue': float(ligne_reception.quantite_recue),
            'quantite_acceptee': float(ligne_reception.quantite_acceptee),
            'quantite_refusee': float(ligne_reception.quantite_refusee),
            'taux_service': round((ligne_reception.quantite_acceptee / ligne_bc.quantite_commandee * 100), 2) if ligne_bc.quantite_commandee > 0 else 0,
        }
