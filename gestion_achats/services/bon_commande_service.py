"""
Service métier pour la gestion des bons de commande.

Ce service encapsule toute la logique métier liée aux bons de commande,
incluant la création, l'émission, l'envoi, la confirmation et l'annulation.
"""

import logging
from decimal import Decimal
from datetime import datetime
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

from gestion_achats.models import (
    GACBonCommande,
    GACLigneBonCommande,
    GACDemandeAchat,
    GACFournisseur,
    GACHistorique,
)
from gestion_achats.constants import (
    STATUT_BC_BROUILLON,
    STATUT_BC_EMIS,
    STATUT_BC_ENVOYE,
    STATUT_BC_CONFIRME,
    STATUT_BC_ANNULE,
)
from gestion_achats.exceptions import (
    BonCommandeError,
    WorkflowError,
    ValidationError as GACValidationError,
    PDFGenerationError,
    EmailSendError,
)

logger = logging.getLogger(__name__)


class BonCommandeService:
    """Service pour la gestion des bons de commande."""

    @staticmethod
    @transaction.atomic
    def creer_bon_commande(demande_achat=None, fournisseur=None, acheteur=None,
                           date_livraison_souhaitee=None, conditions_paiement=None):
        """
        Crée un bon de commande.

        Args:
            demande_achat: La demande d'achat d'origine (optionnel)
            fournisseur: Le fournisseur
            acheteur: L'acheteur qui crée le BC
            date_livraison_souhaitee: Date de livraison souhaitée (optionnel)
            conditions_paiement: Conditions de paiement spécifiques (optionnel)

        Returns:
            GACBonCommande: Le bon de commande créé

        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Conditions de paiement
            if not conditions_paiement and fournisseur:
                conditions_paiement = fournisseur.conditions_paiement

            # Créer le BC (le numéro est généré automatiquement dans le modèle)
            bc = GACBonCommande.objects.create(
                demande_achat=demande_achat,
                fournisseur=fournisseur,
                acheteur=acheteur,
                statut=STATUT_BC_BROUILLON,
                date_livraison_souhaitee=date_livraison_souhaitee,
                conditions_paiement=conditions_paiement,
                cree_par=acheteur
            )

            # Si création depuis demande, copier les lignes
            if demande_achat:
                for ligne_da in demande_achat.lignes.all():
                    GACLigneBonCommande.objects.create(
                        bon_commande=bc,
                        article=ligne_da.article,
                        quantite_commandee=ligne_da.quantite,
                        prix_unitaire=ligne_da.prix_unitaire,
                        taux_tva=ligne_da.taux_tva,
                        commentaire=ligne_da.commentaire
                    )

                # Les totaux sont calculés automatiquement dans le save()

            # Créer l'historique
            description = f"Création du BC {bc.numero}"
            if demande_achat:
                description += f" depuis DA {demande_achat.numero}"

            GACHistorique.enregistrer_action(
                objet=bc,
                action='CREATION',
                utilisateur=acheteur,
                details=description
            )

            logger.info(
                f"BC {bc.numero} créé par {acheteur}" +
                (f" depuis DA {demande_achat.numero}" if demande_achat else "")
            )

            return bc

        except Exception as e:
            logger.error(f"Erreur lors de la création du BC: {str(e)}")
            raise BonCommandeError(f"Impossible de créer le bon de commande: {str(e)}")

    @staticmethod
    @transaction.atomic
    def ajouter_ligne(bc, article, quantite_commandee, prix_unitaire, taux_tva=None, commentaire=''):
        """
        Ajoute une ligne à un bon de commande.

        Args:
            bc: Le bon de commande
            article: L'article à ajouter
            quantite_commandee: La quantité commandée
            prix_unitaire: Le prix unitaire HT
            taux_tva: Le taux de TVA (si None, utilise celui de l'article)
            commentaire: Commentaire sur la ligne (optionnel)

        Returns:
            GACLigneBonCommande: La ligne créée

        Raises:
            WorkflowError: Si le BC n'est pas en brouillon
            ValidationError: Si les données sont invalides
        """
        if bc.statut != STATUT_BC_BROUILLON:
            raise WorkflowError(
                "Impossible d'ajouter une ligne à un BC qui n'est pas en brouillon"
            )

        try:
            # Utiliser le taux TVA de l'article si non spécifié
            if taux_tva is None:
                taux_tva = article.taux_tva

            # Déterminer l'ordre
            dernier_ordre = bc.lignes.aggregate(
                max_ordre=models.Max('ordre')
            )['max_ordre'] or 0

            # Créer la ligne
            ligne = GACLigneBonCommande.objects.create(
                bon_commande=bc,
                article=article,
                quantite_commandee=quantite_commandee,
                prix_unitaire=prix_unitaire,
                taux_tva=taux_tva,
                commentaire=commentaire,
                ordre=dernier_ordre + 1
            )

            # Les montants sont calculés automatiquement dans le save() du modèle
            # Les totaux du BC sont aussi recalculés automatiquement

            logger.info(
                f"Ligne ajoutée au BC {bc.numero}: "
                f"{article.reference} x {quantite_commandee}"
            )

            return ligne

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de ligne: {str(e)}")
            raise BonCommandeError(f"Impossible d'ajouter la ligne: {str(e)}")

    @staticmethod
    @transaction.atomic
    def emettre_bon_commande(bc, utilisateur):
        """
        Émet un bon de commande (finalise et verrouille).

        Args:
            bc: Le bon de commande à émettre
            utilisateur: L'utilisateur acheteur

        Returns:
            GACBonCommande: Le BC mis à jour

        Raises:
            WorkflowError: Si le BC n'est pas en brouillon
            ValidationError: Si le BC est invalide (pas de lignes, etc.)
        """
        if bc.statut != STATUT_BC_BROUILLON:
            raise WorkflowError("Seuls les BC en brouillon peuvent être émis")

        if not bc.lignes.exists():
            raise GACValidationError("Impossible d'émettre un BC sans lignes")

        if not bc.fournisseur:
            raise GACValidationError("Le BC doit avoir un fournisseur")

        try:
            # Générer le PDF
            from gestion_achats.services.pdf_service import PDFService
            pdf_content = PDFService.generer_pdf_bon_commande(bc)

            # Sauvegarder le PDF
            from django.core.files.base import ContentFile
            bc.fichier_pdf.save(
                f'BC_{bc.numero}.pdf',
                ContentFile(pdf_content),
                save=False
            )

            # Mettre à jour le BC
            ancien_statut = bc.statut
            bc.statut = STATUT_BC_EMIS
            bc.date_emission = timezone.now()
            bc.save()

            # Mettre à jour le budget si applicable
            if bc.demande_achat and bc.demande_achat.budget:
                from gestion_achats.services.budget_service import BudgetService
                BudgetService.commander_montant(
                    budget=bc.demande_achat.budget,
                    montant=bc.montant_total_ttc,
                    reference=f"BC {bc.numero}"
                )

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=bc,
                action='EMISSION',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut,
                nouveau_statut=bc.statut,
                details=f"BC {bc.numero} émis (Montant: {bc.montant_total_ttc} €)"
            )

            logger.info(f"BC {bc.numero} émis par {utilisateur}")

            return bc

        except Exception as e:
            logger.error(f"Erreur lors de l'émission du BC: {str(e)}")
            raise BonCommandeError(f"Impossible d'émettre le BC: {str(e)}")

    @staticmethod
    @transaction.atomic
    def envoyer_au_fournisseur(bc, utilisateur, email_destinataire=None):
        """
        Envoie le BC au fournisseur par email.

        Args:
            bc: Le bon de commande à envoyer
            utilisateur: L'utilisateur acheteur
            email_destinataire: Email du fournisseur (optionnel)

        Returns:
            GACBonCommande: Le BC mis à jour

        Raises:
            WorkflowError: Si le BC n'est pas émis
            ValidationError: Si pas d'email destinataire
            EmailSendError: Si l'envoi échoue
        """
        if bc.statut != STATUT_BC_EMIS:
            raise WorkflowError("Le BC doit être émis avant envoi")

        if not bc.fichier_pdf:
            raise GACValidationError("Aucun PDF généré pour ce BC")

        # Email destinataire
        if not email_destinataire:
            email_destinataire = bc.fournisseur.email

        if not email_destinataire:
            raise GACValidationError(
                "Aucun email de destinataire. "
                "Veuillez spécifier un email ou configurer l'email du fournisseur."
            )

        try:
            # Construire l'email
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hronian.local')

            email = EmailMessage(
                subject=f"Bon de commande {bc.numero}",
                body=f"""Bonjour,

Veuillez trouver ci-joint notre bon de commande {bc.numero}.

Date de livraison souhaitée : {bc.date_livraison_souhaitee or 'À définir'}
Montant total TTC : {bc.montant_total_ttc} €

Conditions de paiement : {bc.conditions_paiement or 'Selon accord'}

Cordialement,
{utilisateur.get_full_name() if hasattr(utilisateur, 'get_full_name') else utilisateur}
Service Achats
                """,
                from_email=from_email,
                to=[email_destinataire],
                reply_to=[utilisateur.email] if hasattr(utilisateur, 'email') and utilisateur.email else None
            )

            # Attacher le PDF
            email.attach_file(bc.fichier_pdf.path)

            # Envoyer
            email.send()

            # Mettre à jour le BC
            ancien_statut = bc.statut
            bc.statut = STATUT_BC_ENVOYE
            bc.date_envoi = timezone.now()
            bc.email_envoi = email_destinataire
            bc.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=bc,
                action='ENVOI',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut,
                nouveau_statut=bc.statut,
                details=f"BC envoyé à {email_destinataire}"
            )

            logger.info(f"BC {bc.numero} envoyé à {email_destinataire}")

            return bc

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du BC: {str(e)}")
            raise EmailSendError(f"Impossible d'envoyer le BC: {str(e)}")

    @staticmethod
    @transaction.atomic
    def confirmer_commande(bc, utilisateur, numero_confirmation_fournisseur=None,
                          date_livraison_confirmee=None):
        """
        Enregistre la confirmation du fournisseur.

        Args:
            bc: Le bon de commande
            utilisateur: L'utilisateur acheteur
            numero_confirmation_fournisseur: Numéro de confirmation (optionnel)
            date_livraison_confirmee: Date de livraison confirmée (optionnel)

        Returns:
            GACBonCommande: Le BC mis à jour

        Raises:
            WorkflowError: Si le BC n'est pas envoyé
        """
        if bc.statut != STATUT_BC_ENVOYE:
            raise WorkflowError(
                "Le BC doit être envoyé avant d'enregistrer une confirmation"
            )

        try:
            # Mettre à jour le BC
            ancien_statut = bc.statut
            bc.statut = STATUT_BC_CONFIRME
            bc.date_confirmation = timezone.now()
            bc.numero_confirmation_fournisseur = numero_confirmation_fournisseur
            bc.date_livraison_confirmee = date_livraison_confirmee
            bc.save()

            # Créer une alerte si date confirmée > date souhaitée
            if date_livraison_confirmee and bc.date_livraison_souhaitee:
                if date_livraison_confirmee > bc.date_livraison_souhaitee:
                    # TODO: Créer notification d'alerte
                    logger.warning(
                        f"BC {bc.numero}: Date confirmée ({date_livraison_confirmee}) "
                        f"postérieure à la date souhaitée ({bc.date_livraison_souhaitee})"
                    )

            # Créer l'historique
            details = f"BC confirmé par le fournisseur"
            if numero_confirmation_fournisseur:
                details += f". N° confirmation: {numero_confirmation_fournisseur}"
            if date_livraison_confirmee:
                details += f". Date livraison confirmée: {date_livraison_confirmee}"

            GACHistorique.enregistrer_action(
                objet=bc,
                action='CONFIRMATION',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut,
                nouveau_statut=bc.statut,
                details=details
            )

            # TODO: Notifier le demandeur
            # NotificationService.notifier_bc_confirme(bc)

            logger.info(f"BC {bc.numero} confirmé par le fournisseur")

            return bc

        except Exception as e:
            logger.error(f"Erreur lors de la confirmation du BC: {str(e)}")
            raise BonCommandeError(f"Impossible de confirmer le BC: {str(e)}")

    @staticmethod
    @transaction.atomic
    def annuler_bon_commande(bc, utilisateur, motif_annulation):
        """
        Annule un bon de commande.

        Args:
            bc: Le bon de commande à annuler
            utilisateur: L'utilisateur acheteur
            motif_annulation: Le motif d'annulation

        Returns:
            GACBonCommande: Le BC mis à jour

        Raises:
            WorkflowError: Si le BC ne peut pas être annulé
        """
        # Vérifier que le BC n'est pas déjà reçu
        if bc.statut in ['RECU_PARTIEL', 'RECU_COMPLET']:
            raise WorkflowError(
                "Impossible d'annuler un BC déjà reçu (partiellement ou totalement)"
            )

        if bc.statut == STATUT_BC_ANNULE:
            raise WorkflowError("Ce BC est déjà annulé")

        try:
            # Libérer le budget si applicable
            if bc.demande_achat and bc.demande_achat.budget:
                from gestion_achats.services.budget_service import BudgetService
                BudgetService.liberer_montant(
                    budget=bc.demande_achat.budget,
                    montant=bc.montant_total_ttc,
                    reference=f"Annulation BC {bc.numero}"
                )

            # Mettre à jour le BC
            ancien_statut = bc.statut
            bc.statut = STATUT_BC_ANNULE
            bc.motif_annulation = motif_annulation
            bc.date_annulation = timezone.now()
            bc.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=bc,
                action='ANNULATION',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut,
                nouveau_statut=bc.statut,
                details=f"BC annulé par {utilisateur}. Motif: {motif_annulation}"
            )

            # Notifier le fournisseur si le BC avait été envoyé
            if ancien_statut in [STATUT_BC_ENVOYE, STATUT_BC_CONFIRME]:
                # TODO: Envoyer email d'annulation au fournisseur
                logger.info(
                    f"BC {bc.numero} était envoyé/confirmé. "
                    f"Email d'annulation devrait être envoyé au fournisseur."
                )

            logger.info(f"BC {bc.numero} annulé par {utilisateur}")

            return bc

        except Exception as e:
            logger.error(f"Erreur lors de l'annulation du BC: {str(e)}")
            raise BonCommandeError(f"Impossible d'annuler le BC: {str(e)}")

    @staticmethod
    def get_bons_commande_fournisseur(fournisseur, statut=None):
        """
        Récupère les bons de commande pour un fournisseur.

        Args:
            fournisseur: Le fournisseur
            statut: Filtrer par statut (optionnel)

        Returns:
            QuerySet: Les bons de commande
        """
        queryset = GACBonCommande.objects.filter(fournisseur=fournisseur)

        if statut:
            queryset = queryset.filter(statut=statut)

        return queryset.order_by('-date_creation')

    @staticmethod
    def get_bons_commande_en_attente_reception():
        """
        Récupère les bons de commande en attente de réception.

        Returns:
            QuerySet: Les bons de commande confirmés non reçus
        """
        return GACBonCommande.objects.filter(
            statut=STATUT_BC_CONFIRME
        ).order_by('date_livraison_confirmee', 'date_livraison_souhaitee')

    @staticmethod
    def get_statistiques_bons_commande(date_debut=None, date_fin=None):
        """
        Récupère les statistiques sur les bons de commande.

        Args:
            date_debut: Date de début de la période (optionnel)
            date_fin: Date de fin de la période (optionnel)

        Returns:
            dict: Statistiques
        """
        from django.db.models import Count, Sum, Avg

        queryset = GACBonCommande.objects.all()

        if date_debut:
            queryset = queryset.filter(date_creation__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_creation__lte=date_fin)

        # Statistiques par statut
        par_statut = queryset.values('statut').annotate(
            nombre=Count('id')
        )

        # Montants
        montant_total = queryset.aggregate(
            total=Sum('montant_total_ttc')
        )['total'] or Decimal('0')

        montant_moyen = queryset.aggregate(
            moyen=Avg('montant_total_ttc')
        )['moyen'] or Decimal('0')

        # Top fournisseurs
        top_fournisseurs = queryset.values(
            'fournisseur__raison_sociale'
        ).annotate(
            nombre=Count('id'),
            montant_total=Sum('montant_total_ttc')
        ).order_by('-montant_total')[:10]

        return {
            'total_bons_commande': queryset.count(),
            'par_statut': {item['statut']: item['nombre'] for item in par_statut},
            'montant_total': montant_total,
            'montant_moyen': montant_moyen,
            'top_fournisseurs': list(top_fournisseurs),
        }
