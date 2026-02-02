"""
Service métier pour la gestion des notifications.

Ce service encapsule toute la logique métier liée aux notifications,
incluant la création de notifications in-app et l'envoi d'emails.
"""

import logging
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour la gestion des notifications."""

    @staticmethod
    def _envoyer_email(destinataire, sujet, message_texte, message_html=None):
        """
        Envoie un email.

        Args:
            destinataire: Email du destinataire
            sujet: Sujet de l'email
            message_texte: Message au format texte
            message_html: Message au format HTML (optionnel)

        Returns:
            bool: True si envoyé avec succès
        """
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hronian.local')

            if message_html:
                from django.core.mail import EmailMultiAlternatives
                email = EmailMultiAlternatives(
                    subject=sujet,
                    body=message_texte,
                    from_email=from_email,
                    to=[destinataire]
                )
                email.attach_alternative(message_html, "text/html")
                email.send()
            else:
                email = EmailMessage(
                    subject=sujet,
                    body=message_texte,
                    from_email=from_email,
                    to=[destinataire]
                )
                email.send()

            logger.info(f"Email envoyé à {destinataire}: {sujet}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'email à {destinataire}: {str(e)}")
            return False

    @staticmethod
    def _creer_notification_inapp(utilisateur, titre, message, lien=None, niveau='INFO'):
        """
        Crée une notification in-app.

        Args:
            utilisateur: L'utilisateur destinataire
            titre: Titre de la notification
            message: Message de la notification
            lien: Lien vers la ressource concernée (optionnel)
            niveau: Niveau de la notification (INFO, AVERTISSEMENT, CRITIQUE)

        Returns:
            Notification créée (ou None si pas de modèle Notification)

        Note:
            Cette méthode nécessiterait un modèle GACNotification qui n'est pas
            dans les specs actuelles. Pour l'instant, on log seulement.
        """
        # TODO: Implémenter avec un modèle GACNotification si ajouté
        logger.info(
            f"Notification [{niveau}] pour {utilisateur}: {titre} - {message}"
        )

        # Une fois le modèle créé, ajouter:
        # notification = GACNotification.objects.create(
        #     utilisateur=utilisateur,
        #     titre=titre,
        #     message=message,
        #     lien=lien,
        #     niveau=niveau,
        #     lu=False
        # )
        # return notification

        return None

    # ==========================================
    # NOTIFICATIONS POUR LES DEMANDES D'ACHAT
    # ==========================================

    @staticmethod
    def notifier_validation_n1(demande):
        """
        Notifie le validateur N1 qu'une demande est en attente de validation.

        Args:
            demande: La demande d'achat soumise
        """
        validateur = demande.validateur_n1

        if not validateur:
            logger.warning(f"Pas de validateur N1 pour la demande {demande.numero}")
            return

        # Notification in-app
        NotificationService._creer_notification_inapp(
            utilisateur=validateur,
            titre=f"Demande d'achat à valider: {demande.numero}",
            message=f"Nouvelle demande de {demande.demandeur} - Montant: {demande.montant_total_ttc} €",
            lien=f"/gestion-achats/demandes/{demande.id}/",
            niveau='INFO'
        )

        # Email
        if hasattr(validateur, 'email') and validateur.email:
            sujet = f"[GAC] Demande d'achat à valider: {demande.numero}"

            message = f"""Bonjour {validateur.get_full_name() if hasattr(validateur, 'get_full_name') else validateur},

Une nouvelle demande d'achat nécessite votre validation (niveau N1).

Détails de la demande:
- Numéro: {demande.numero}
- Demandeur: {demande.demandeur}
- Objet: {demande.objet}
- Montant TTC: {demande.montant_total_ttc} €
- Date de soumission: {demande.date_soumission.strftime('%d/%m/%Y %H:%M')}

Justification:
{demande.justification}

Veuillez vous connecter pour valider ou refuser cette demande.

Cordialement,
Système de gestion des achats
            """

            NotificationService._envoyer_email(validateur.email, sujet, message)

    @staticmethod
    def notifier_validation_n2(demande):
        """
        Notifie le validateur N2 qu'une demande est en attente de validation.

        Args:
            demande: La demande d'achat validée N1
        """
        validateur = demande.validateur_n2

        if not validateur:
            logger.warning(f"Pas de validateur N2 pour la demande {demande.numero}")
            return

        # Notification in-app
        NotificationService._creer_notification_inapp(
            utilisateur=validateur,
            titre=f"Demande d'achat à valider (N2): {demande.numero}",
            message=f"Demande validée N1 - Montant: {demande.montant_total_ttc} €",
            lien=f"/gestion-achats/demandes/{demande.id}/",
            niveau='INFO'
        )

        # Email
        if hasattr(validateur, 'email') and validateur.email:
            sujet = f"[GAC] Demande d'achat à valider (N2): {demande.numero}"

            message = f"""Bonjour {validateur.get_full_name() if hasattr(validateur, 'get_full_name') else validateur},

Une demande d'achat validée N1 nécessite votre validation (niveau N2).

Détails de la demande:
- Numéro: {demande.numero}
- Demandeur: {demande.demandeur}
- Objet: {demande.objet}
- Montant TTC: {demande.montant_total_ttc} €
- Validée N1 par: {demande.validateur_n1}
- Date validation N1: {demande.date_validation_n1.strftime('%d/%m/%Y %H:%M') if demande.date_validation_n1 else 'N/A'}

Veuillez vous connecter pour valider ou refuser cette demande.

Cordialement,
Système de gestion des achats
            """

            NotificationService._envoyer_email(validateur.email, sujet, message)

    @staticmethod
    def notifier_demande_validee(demande):
        """
        Notifie le demandeur que sa demande est validée.

        Args:
            demande: La demande d'achat validée
        """
        demandeur = demande.demandeur

        # Notification in-app
        NotificationService._creer_notification_inapp(
            utilisateur=demandeur,
            titre=f"Demande validée: {demande.numero}",
            message=f"Votre demande d'achat a été validée - Montant: {demande.montant_total_ttc} €",
            lien=f"/gestion-achats/demandes/{demande.id}/",
            niveau='INFO'
        )

        # Email
        if hasattr(demandeur, 'email') and demandeur.email:
            sujet = f"[GAC] Demande d'achat validée: {demande.numero}"

            message = f"""Bonjour {demandeur.get_full_name() if hasattr(demandeur, 'get_full_name') else demandeur},

Votre demande d'achat a été validée et sera traitée par le service achats.

Détails de la demande:
- Numéro: {demande.numero}
- Objet: {demande.objet}
- Montant TTC: {demande.montant_total_ttc} €
- Validée le: {demande.date_validation_n2.strftime('%d/%m/%Y %H:%M') if demande.date_validation_n2 else 'N/A'}

Vous serez notifié de l'avancement du traitement.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(demandeur.email, sujet, message)

    @staticmethod
    def notifier_demande_refusee(demande, motif):
        """
        Notifie le demandeur que sa demande est refusée.

        Args:
            demande: La demande d'achat refusée
            motif: Le motif du refus
        """
        demandeur = demande.demandeur

        # Notification in-app
        NotificationService._creer_notification_inapp(
            utilisateur=demandeur,
            titre=f"Demande refusée: {demande.numero}",
            message=f"Votre demande a été refusée. Motif: {motif}",
            lien=f"/gestion-achats/demandes/{demande.id}/",
            niveau='AVERTISSEMENT'
        )

        # Email
        if hasattr(demandeur, 'email') and demandeur.email:
            sujet = f"[GAC] Demande d'achat refusée: {demande.numero}"

            message = f"""Bonjour {demandeur.get_full_name() if hasattr(demandeur, 'get_full_name') else demandeur},

Votre demande d'achat a été refusée.

Détails de la demande:
- Numéro: {demande.numero}
- Objet: {demande.objet}
- Montant TTC: {demande.montant_total_ttc} €

Motif du refus:
{motif}

Pour plus d'informations, veuillez contacter votre manager ou le service achats.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(demandeur.email, sujet, message)

    @staticmethod
    def notifier_bc_cree_depuis_demande(demande, bc):
        """
        Notifie le demandeur qu'un bon de commande a été créé depuis sa demande.

        Args:
            demande: La demande d'achat
            bc: Le bon de commande créé
        """
        demandeur = demande.demandeur

        # Notification in-app
        NotificationService._creer_notification_inapp(
            utilisateur=demandeur,
            titre=f"Bon de commande créé: {bc.numero}",
            message=f"Un BC a été créé pour votre demande {demande.numero}",
            lien=f"/gestion-achats/bons-commande/{bc.id}/",
            niveau='INFO'
        )

        # Email
        if hasattr(demandeur, 'email') and demandeur.email:
            sujet = f"[GAC] Bon de commande créé: {bc.numero}"

            message = f"""Bonjour {demandeur.get_full_name() if hasattr(demandeur, 'get_full_name') else demandeur},

Un bon de commande a été créé pour votre demande d'achat.

Détails:
- Demande: {demande.numero}
- Bon de commande: {bc.numero}
- Fournisseur: {bc.fournisseur.raison_sociale if bc.fournisseur else 'Non défini'}
- Montant TTC: {bc.montant_total_ttc} €

Vous serez notifié lors de la réception des marchandises.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(demandeur.email, sujet, message)

    # ==========================================
    # NOTIFICATIONS POUR LES RÉCEPTIONS
    # ==========================================

    @staticmethod
    def notifier_reception_validee(reception):
        """
        Notifie l'acheteur et le demandeur qu'une réception a été validée.

        Args:
            reception: La réception validée
        """
        bc = reception.bon_commande

        # Notifier l'acheteur
        if bc.acheteur:
            NotificationService._creer_notification_inapp(
                utilisateur=bc.acheteur,
                titre=f"Réception validée: {reception.numero}",
                message=f"BC {bc.numero} - {'Conforme' if reception.conforme else 'Non conforme'}",
                lien=f"/gestion-achats/receptions/{reception.id}/",
                niveau='INFO' if reception.conforme else 'AVERTISSEMENT'
            )

            if hasattr(bc.acheteur, 'email') and bc.acheteur.email:
                sujet = f"[GAC] Réception validée: {reception.numero}"

                message = f"""Bonjour {bc.acheteur.get_full_name() if hasattr(bc.acheteur, 'get_full_name') else bc.acheteur},

Une réception de marchandises a été validée.

Détails:
- Réception: {reception.numero}
- Bon de commande: {bc.numero}
- Date de réception: {reception.date_reception}
- Conformité: {'Conforme' if reception.conforme else 'NON CONFORME'}

{'Aucune action requise.' if reception.conforme else 'ATTENTION: Des non-conformités ont été détectées. Veuillez traiter ce dossier.'}

Cordialement,
Service Réception
                """

                NotificationService._envoyer_email(bc.acheteur.email, sujet, message)

        # Notifier le demandeur si applicable
        if bc.demande_achat and bc.demande_achat.demandeur:
            demandeur = bc.demande_achat.demandeur

            NotificationService._creer_notification_inapp(
                utilisateur=demandeur,
                titre=f"Réception: {reception.numero}",
                message=f"Votre commande (DA {bc.demande_achat.numero}) a été réceptionnée",
                lien=f"/gestion-achats/receptions/{reception.id}/",
                niveau='INFO'
            )

    # ==========================================
    # NOTIFICATIONS POUR LES BUDGETS
    # ==========================================

    @staticmethod
    def notifier_alerte_budget(budget, niveau, message):
        """
        Notifie les gestionnaires de budget d'une alerte.

        Args:
            budget: L'enveloppe budgétaire
            niveau: Niveau d'alerte (AVERTISSEMENT, CRITIQUE)
            message: Message d'alerte
        """
        # Notifier le gestionnaire du budget
        if budget.gestionnaire:
            NotificationService._creer_notification_inapp(
                utilisateur=budget.gestionnaire,
                titre=f"Alerte budget: {budget.code}",
                message=message,
                lien=f"/gestion-achats/budgets/{budget.id}/",
                niveau=niveau
            )

            if hasattr(budget.gestionnaire, 'email') and budget.gestionnaire.email:
                sujet = f"[GAC] Alerte budget {niveau}: {budget.code}"

                email_message = f"""Bonjour {budget.gestionnaire.get_full_name() if hasattr(budget.gestionnaire, 'get_full_name') else budget.gestionnaire},

{message}

Détails du budget:
- Code: {budget.code}
- Libellé: {budget.libelle}
- Montant initial: {budget.montant_initial} €
- Montant engagé: {budget.montant_engage} €
- Montant commandé: {budget.montant_commande} €
- Montant consommé: {budget.montant_consomme} €
- Disponible: {budget.montant_disponible()} €
- Taux de consommation: {budget.taux_consommation():.1f}%

Veuillez prendre les mesures nécessaires.

Cordialement,
Système de gestion budgétaire
                """

                NotificationService._envoyer_email(budget.gestionnaire.email, sujet, email_message)

        logger.warning(f"Alerte budget [{niveau}]: {budget.code} - {message}")
