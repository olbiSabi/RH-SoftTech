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
    def notifier_demande_soumise(demande):
        """
        Notifie le validateur N1 qu'une demande a été soumise.

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
            titre=f"Nouvelle demande d'achat à valider: {demande.numero}",
            message=f"Demande de {demande.demandeur} - Montant: {demande.montant_total_ttc} €",
            lien=f"/gestion-achats/demandes/{demande.uuid}/",
            niveau='INFO'
        )

        # Email
        email = None
        if hasattr(validateur, 'employe') and hasattr(validateur.employe, 'EMAIL'):
            email = validateur.employe.EMAIL
        elif hasattr(validateur, 'email'):
            email = validateur.email

        if email:
            sujet = f"[GAC] Nouvelle demande d'achat à valider: {demande.numero}"

            message = f"""Bonjour {validateur.get_full_name() if hasattr(validateur, 'get_full_name') else validateur},

Une nouvelle demande d'achat nécessite votre validation (niveau N1).

Détails de la demande:
- Numéro: {demande.numero}
- Demandeur: {demande.demandeur}
- Objet: {demande.objet}
- Montant TTC: {demande.montant_total_ttc} €
- Date de soumission: {demande.date_soumission.strftime('%d/%m/%Y %H:%M') if demande.date_soumission else 'N/A'}

Justification:
{demande.justification}

Veuillez vous connecter pour valider ou refuser cette demande.

Cordialement,
Système de gestion des achats
            """

            NotificationService._envoyer_email(email, sujet, message)

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
    def notifier_demande_validee_n1(demande):
        """
        Notifie le validateur N2 qu'une demande a été validée N1.

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
            lien=f"/gestion-achats/demandes/{demande.uuid}/",
            niveau='INFO'
        )

        # Email
        email = None
        if hasattr(validateur, 'employe') and hasattr(validateur.employe, 'EMAIL'):
            email = validateur.employe.EMAIL
        elif hasattr(validateur, 'email'):
            email = validateur.email

        if email:
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

            NotificationService._envoyer_email(email, sujet, message)

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
    def notifier_demande_validee_n2(demande):
        """
        Notifie le demandeur et l'acheteur que la demande a été validée N2.

        Args:
            demande: La demande d'achat validée N2
        """
        # Notifier le demandeur
        demandeur = demande.demandeur

        NotificationService._creer_notification_inapp(
            utilisateur=demandeur,
            titre=f"Demande validée: {demande.numero}",
            message=f"Votre demande d'achat a été validée - Montant: {demande.montant_total_ttc} €",
            lien=f"/gestion-achats/demandes/{demande.uuid}/",
            niveau='INFO'
        )

        email = None
        if hasattr(demandeur, 'employe') and hasattr(demandeur.employe, 'EMAIL'):
            email = demandeur.employe.EMAIL
        elif hasattr(demandeur, 'email'):
            email = demandeur.email

        if email:
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

            NotificationService._envoyer_email(email, sujet, message)

        # TODO: Notifier aussi l'acheteur/le service achats si nécessaire

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
    def notifier_demande_annulee(demande):
        """
        Notifie les parties prenantes qu'une demande a été annulée.

        Args:
            demande: La demande d'achat annulée
        """
        # Notifier le demandeur
        demandeur = demande.demandeur

        NotificationService._creer_notification_inapp(
            utilisateur=demandeur,
            titre=f"Demande annulée: {demande.numero}",
            message=f"La demande d'achat {demande.numero} a été annulée",
            lien=f"/gestion-achats/demandes/{demande.uuid}/",
            niveau='AVERTISSEMENT'
        )

        email = None
        if hasattr(demandeur, 'employe') and hasattr(demandeur.employe, 'EMAIL'):
            email = demandeur.employe.EMAIL
        elif hasattr(demandeur, 'email'):
            email = demandeur.email

        if email:
            sujet = f"[GAC] Demande d'achat annulée: {demande.numero}"

            message = f"""Bonjour {demandeur.get_full_name() if hasattr(demandeur, 'get_full_name') else demandeur},

La demande d'achat suivante a été annulée.

Détails de la demande:
- Numéro: {demande.numero}
- Objet: {demande.objet}
- Montant TTC: {demande.montant_total_ttc} €

Pour plus d'informations, veuillez contacter le service achats.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

        # Notifier les validateurs si la demande était en cours de validation
        if demande.validateur_n1:
            NotificationService._creer_notification_inapp(
                utilisateur=demande.validateur_n1,
                titre=f"Demande annulée: {demande.numero}",
                message=f"La demande que vous deviez valider a été annulée",
                lien=f"/gestion-achats/demandes/{demande.uuid}/",
                niveau='INFO'
            )

    @staticmethod
    def notifier_demande_convertie(demande):
        """
        Notifie le demandeur et l'acheteur qu'une demande a été convertie en BC.

        Args:
            demande: La demande d'achat convertie
        """
        # Notifier le demandeur
        demandeur = demande.demandeur

        NotificationService._creer_notification_inapp(
            utilisateur=demandeur,
            titre=f"Demande convertie en BC: {demande.numero}",
            message=f"Votre demande a été convertie en bon de commande",
            lien=f"/gestion-achats/demandes/{demande.uuid}/",
            niveau='INFO'
        )

        email = None
        if hasattr(demandeur, 'employe') and hasattr(demandeur.employe, 'EMAIL'):
            email = demandeur.employe.EMAIL
        elif hasattr(demandeur, 'email'):
            email = demandeur.email

        if email:
            sujet = f"[GAC] Demande convertie en BC: {demande.numero}"

            message = f"""Bonjour {demandeur.get_full_name() if hasattr(demandeur, 'get_full_name') else demandeur},

Votre demande d'achat a été convertie en bon de commande.

Détails de la demande:
- Numéro: {demande.numero}
- Objet: {demande.objet}
- Montant TTC: {demande.montant_total_ttc} €

Vous serez notifié lors de la réception des marchandises.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

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

    @staticmethod
    def notifier_bc_emis(bon_commande):
        """
        Notifie l'acheteur qu'un bon de commande a été émis.

        Args:
            bon_commande: Le bon de commande émis
        """
        acheteur = bon_commande.acheteur

        # Notification in-app
        NotificationService._creer_notification_inapp(
            utilisateur=acheteur,
            titre=f"Bon de commande émis: {bon_commande.numero}",
            message=f"BC {bon_commande.numero} émis - Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'N/A'}",
            lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
            niveau='INFO'
        )

        email = None
        if hasattr(acheteur, 'employe') and hasattr(acheteur.employe, 'EMAIL'):
            email = acheteur.employe.EMAIL
        elif hasattr(acheteur, 'email'):
            email = acheteur.email

        if email:
            sujet = f"[GAC] Bon de commande émis: {bon_commande.numero}"

            message = f"""Bonjour {acheteur.get_full_name() if hasattr(acheteur, 'get_full_name') else acheteur},

Un bon de commande a été émis.

Détails:
- Numéro: {bon_commande.numero}
- Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'Non défini'}
- Montant TTC: {bon_commande.montant_total_ttc} €
- Date d'émission: {bon_commande.date_emission.strftime('%d/%m/%Y') if bon_commande.date_emission else 'N/A'}

Le bon de commande peut maintenant être envoyé au fournisseur.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

    @staticmethod
    def notifier_bc_envoye(bon_commande):
        """
        Notifie les parties prenantes qu'un BC a été envoyé au fournisseur.

        Args:
            bon_commande: Le bon de commande envoyé
        """
        # Notifier l'acheteur
        acheteur = bon_commande.acheteur

        NotificationService._creer_notification_inapp(
            utilisateur=acheteur,
            titre=f"BC envoyé: {bon_commande.numero}",
            message=f"Le BC a été envoyé au fournisseur {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'N/A'}",
            lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
            niveau='INFO'
        )

        email = None
        if hasattr(acheteur, 'employe') and hasattr(acheteur.employe, 'EMAIL'):
            email = acheteur.employe.EMAIL
        elif hasattr(acheteur, 'email'):
            email = acheteur.email

        if email:
            sujet = f"[GAC] BC envoyé au fournisseur: {bon_commande.numero}"

            message = f"""Bonjour {acheteur.get_full_name() if hasattr(acheteur, 'get_full_name') else acheteur},

Le bon de commande a été envoyé au fournisseur.

Détails:
- Numéro: {bon_commande.numero}
- Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'Non défini'}
- Montant TTC: {bon_commande.montant_total_ttc} €
- Date d'envoi: {bon_commande.date_envoi.strftime('%d/%m/%Y') if bon_commande.date_envoi else 'N/A'}

En attente de confirmation du fournisseur.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

        # Notifier le demandeur si applicable
        if bon_commande.demande_achat and bon_commande.demande_achat.demandeur:
            demandeur = bon_commande.demande_achat.demandeur
            NotificationService._creer_notification_inapp(
                utilisateur=demandeur,
                titre=f"BC envoyé: {bon_commande.numero}",
                message=f"Le BC pour votre demande {bon_commande.demande_achat.numero} a été envoyé au fournisseur",
                lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
                niveau='INFO'
            )

    @staticmethod
    def notifier_bc_confirme(bon_commande):
        """
        Notifie les parties prenantes qu'un BC a été confirmé par le fournisseur.

        Args:
            bon_commande: Le bon de commande confirmé
        """
        # Notifier l'acheteur
        acheteur = bon_commande.acheteur

        NotificationService._creer_notification_inapp(
            utilisateur=acheteur,
            titre=f"BC confirmé: {bon_commande.numero}",
            message=f"Le fournisseur a confirmé le BC {bon_commande.numero}",
            lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
            niveau='INFO'
        )

        email = None
        if hasattr(acheteur, 'employe') and hasattr(acheteur.employe, 'EMAIL'):
            email = acheteur.employe.EMAIL
        elif hasattr(acheteur, 'email'):
            email = acheteur.email

        if email:
            sujet = f"[GAC] BC confirmé par le fournisseur: {bon_commande.numero}"

            message = f"""Bonjour {acheteur.get_full_name() if hasattr(acheteur, 'get_full_name') else acheteur},

Le fournisseur a confirmé le bon de commande.

Détails:
- Numéro: {bon_commande.numero}
- Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'Non défini'}
- Montant TTC: {bon_commande.montant_total_ttc} €
- Date de livraison prévue: {bon_commande.date_livraison_prevue.strftime('%d/%m/%Y') if bon_commande.date_livraison_prevue else 'N/A'}

En attente de la réception des marchandises.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

    @staticmethod
    def notifier_bc_recu_partiel(bon_commande):
        """
        Notifie les parties prenantes d'une réception partielle.

        Args:
            bon_commande: Le bon de commande avec réception partielle
        """
        # Notifier l'acheteur
        acheteur = bon_commande.acheteur

        NotificationService._creer_notification_inapp(
            utilisateur=acheteur,
            titre=f"Réception partielle: {bon_commande.numero}",
            message=f"Réception partielle pour le BC {bon_commande.numero}",
            lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
            niveau='AVERTISSEMENT'
        )

        email = None
        if hasattr(acheteur, 'employe') and hasattr(acheteur.employe, 'EMAIL'):
            email = acheteur.employe.EMAIL
        elif hasattr(acheteur, 'email'):
            email = acheteur.email

        if email:
            sujet = f"[GAC] Réception partielle: {bon_commande.numero}"

            message = f"""Bonjour {acheteur.get_full_name() if hasattr(acheteur, 'get_full_name') else acheteur},

Une réception partielle a été enregistrée pour ce bon de commande.

Détails:
- Numéro: {bon_commande.numero}
- Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'Non défini'}
- Montant TTC: {bon_commande.montant_total_ttc} €

Veuillez vérifier les détails de la réception et suivre avec le fournisseur pour les articles manquants.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

    @staticmethod
    def notifier_bc_recu_complet(bon_commande):
        """
        Notifie les parties prenantes d'une réception complète.

        Args:
            bon_commande: Le bon de commande complètement reçu
        """
        # Notifier l'acheteur
        acheteur = bon_commande.acheteur

        NotificationService._creer_notification_inapp(
            utilisateur=acheteur,
            titre=f"Réception complète: {bon_commande.numero}",
            message=f"Le BC {bon_commande.numero} a été complètement réceptionné",
            lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
            niveau='INFO'
        )

        email = None
        if hasattr(acheteur, 'employe') and hasattr(acheteur.employe, 'EMAIL'):
            email = acheteur.employe.EMAIL
        elif hasattr(acheteur, 'email'):
            email = acheteur.email

        if email:
            sujet = f"[GAC] Réception complète: {bon_commande.numero}"

            message = f"""Bonjour {acheteur.get_full_name() if hasattr(acheteur, 'get_full_name') else acheteur},

Le bon de commande a été complètement réceptionné.

Détails:
- Numéro: {bon_commande.numero}
- Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'Non défini'}
- Montant TTC: {bon_commande.montant_total_ttc} €

Le dossier peut maintenant être clôturé.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

        # Notifier le demandeur si applicable
        if bon_commande.demande_achat and bon_commande.demande_achat.demandeur:
            demandeur = bon_commande.demande_achat.demandeur

            NotificationService._creer_notification_inapp(
                utilisateur=demandeur,
                titre=f"Commande réceptionnée: {bon_commande.numero}",
                message=f"Votre commande (DA {bon_commande.demande_achat.numero}) a été complètement réceptionnée",
                lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
                niveau='INFO'
            )

            email_dem = None
            if hasattr(demandeur, 'employe') and hasattr(demandeur.employe, 'EMAIL'):
                email_dem = demandeur.employe.EMAIL
            elif hasattr(demandeur, 'email'):
                email_dem = demandeur.email

            if email_dem:
                sujet = f"[GAC] Votre commande a été réceptionnée: {bon_commande.numero}"

                message = f"""Bonjour {demandeur.get_full_name() if hasattr(demandeur, 'get_full_name') else demandeur},

Votre commande a été complètement réceptionnée.

Détails:
- Demande d'achat: {bon_commande.demande_achat.numero}
- Bon de commande: {bon_commande.numero}
- Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'Non défini'}

Cordialement,
Service Achats
                """

                NotificationService._envoyer_email(email_dem, sujet, message)

    @staticmethod
    def notifier_bc_annule(bon_commande):
        """
        Notifie les parties prenantes qu'un BC a été annulé.

        Args:
            bon_commande: Le bon de commande annulé
        """
        # Notifier l'acheteur
        acheteur = bon_commande.acheteur

        NotificationService._creer_notification_inapp(
            utilisateur=acheteur,
            titre=f"BC annulé: {bon_commande.numero}",
            message=f"Le BC {bon_commande.numero} a été annulé",
            lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
            niveau='AVERTISSEMENT'
        )

        email = None
        if hasattr(acheteur, 'employe') and hasattr(acheteur.employe, 'EMAIL'):
            email = acheteur.employe.EMAIL
        elif hasattr(acheteur, 'email'):
            email = acheteur.email

        if email:
            sujet = f"[GAC] BC annulé: {bon_commande.numero}"

            message = f"""Bonjour {acheteur.get_full_name() if hasattr(acheteur, 'get_full_name') else acheteur},

Le bon de commande a été annulé.

Détails:
- Numéro: {bon_commande.numero}
- Fournisseur: {bon_commande.fournisseur.raison_sociale if bon_commande.fournisseur else 'Non défini'}
- Montant TTC: {bon_commande.montant_total_ttc} €

Veuillez contacter le fournisseur pour confirmer l'annulation.

Cordialement,
Service Achats
            """

            NotificationService._envoyer_email(email, sujet, message)

        # Notifier le demandeur si applicable
        if bon_commande.demande_achat and bon_commande.demande_achat.demandeur:
            demandeur = bon_commande.demande_achat.demandeur

            NotificationService._creer_notification_inapp(
                utilisateur=demandeur,
                titre=f"BC annulé: {bon_commande.numero}",
                message=f"Le BC pour votre demande {bon_commande.demande_achat.numero} a été annulé",
                lien=f"/gestion-achats/bons-commande/{bon_commande.uuid}/",
                niveau='AVERTISSEMENT'
            )

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

    @staticmethod
    def notifier_reception_creee(reception):
        """
        Notifie l'acheteur qu'une nouvelle réception a été créée.

        Args:
            reception: La réception créée
        """
        bc = reception.bon_commande

        # Notifier l'acheteur
        if bc.acheteur:
            NotificationService._creer_notification_inapp(
                utilisateur=bc.acheteur,
                titre=f"Nouvelle réception: {reception.numero}",
                message=f"Réception créée pour le BC {bc.numero}",
                lien=f"/gestion-achats/receptions/{reception.uuid}/",
                niveau='INFO'
            )

            email = None
            if hasattr(bc.acheteur, 'employe') and hasattr(bc.acheteur.employe, 'EMAIL'):
                email = bc.acheteur.employe.EMAIL
            elif hasattr(bc.acheteur, 'email'):
                email = bc.acheteur.email

            if email:
                sujet = f"[GAC] Nouvelle réception créée: {reception.numero}"

                message = f"""Bonjour {bc.acheteur.get_full_name() if hasattr(bc.acheteur, 'get_full_name') else bc.acheteur},

Une nouvelle réception de marchandises a été créée.

Détails:
- Réception: {reception.numero}
- Bon de commande: {bc.numero}
- Date de réception: {reception.date_reception.strftime('%d/%m/%Y') if reception.date_reception else 'N/A'}
- Réceptionnaire: {reception.receptionnaire}

Veuillez vérifier et valider la réception.

Cordialement,
Service Réception
                """

                NotificationService._envoyer_email(email, sujet, message)

    @staticmethod
    def notifier_reception_annulee(reception):
        """
        Notifie les parties prenantes qu'une réception a été annulée.

        Args:
            reception: La réception annulée
        """
        bc = reception.bon_commande

        # Notifier l'acheteur
        if bc.acheteur:
            NotificationService._creer_notification_inapp(
                utilisateur=bc.acheteur,
                titre=f"Réception annulée: {reception.numero}",
                message=f"La réception {reception.numero} a été annulée",
                lien=f"/gestion-achats/receptions/{reception.uuid}/",
                niveau='AVERTISSEMENT'
            )

            email = None
            if hasattr(bc.acheteur, 'employe') and hasattr(bc.acheteur.employe, 'EMAIL'):
                email = bc.acheteur.employe.EMAIL
            elif hasattr(bc.acheteur, 'email'):
                email = bc.acheteur.email

            if email:
                sujet = f"[GAC] Réception annulée: {reception.numero}"

                message = f"""Bonjour {bc.acheteur.get_full_name() if hasattr(bc.acheteur, 'get_full_name') else bc.acheteur},

Une réception de marchandises a été annulée.

Détails:
- Réception: {reception.numero}
- Bon de commande: {bc.numero}
- Date de réception: {reception.date_reception.strftime('%d/%m/%Y') if reception.date_reception else 'N/A'}

Veuillez vérifier le dossier et prendre les mesures nécessaires.

Cordialement,
Service Réception
                """

                NotificationService._envoyer_email(email, sujet, message)

        # Notifier le réceptionnaire
        if reception.receptionnaire:
            NotificationService._creer_notification_inapp(
                utilisateur=reception.receptionnaire,
                titre=f"Réception annulée: {reception.numero}",
                message=f"La réception que vous avez créée a été annulée",
                lien=f"/gestion-achats/receptions/{reception.uuid}/",
                niveau='AVERTISSEMENT'
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

    @staticmethod
    def notifier_budget_seuil_1(budget, taux):
        """
        Notifie le gestionnaire que le premier seuil budgétaire a été atteint.

        Args:
            budget: L'enveloppe budgétaire
            taux: Le taux de consommation actuel
        """
        message = f"Le budget {budget.code} a atteint {taux:.1f}% de consommation (seuil d'alerte 1: {budget.seuil_alerte_1}%)"

        # Notifier le gestionnaire
        if budget.gestionnaire:
            NotificationService._creer_notification_inapp(
                utilisateur=budget.gestionnaire,
                titre=f"Alerte budget (Seuil 1): {budget.code}",
                message=message,
                lien=f"/gestion-achats/budgets/{budget.uuid}/",
                niveau='AVERTISSEMENT'
            )

            email = None
            if hasattr(budget.gestionnaire, 'employe') and hasattr(budget.gestionnaire.employe, 'EMAIL'):
                email = budget.gestionnaire.employe.EMAIL
            elif hasattr(budget.gestionnaire, 'email'):
                email = budget.gestionnaire.email

            if email:
                sujet = f"[GAC] Alerte budget - Seuil 1 atteint: {budget.code}"

                email_message = f"""Bonjour {budget.gestionnaire.get_full_name() if hasattr(budget.gestionnaire, 'get_full_name') else budget.gestionnaire},

Le premier seuil d'alerte budgétaire a été atteint.

Détails du budget:
- Code: {budget.code}
- Libellé: {budget.libelle}
- Montant initial: {budget.montant_initial} €
- Montant engagé: {budget.montant_engage} €
- Montant commandé: {budget.montant_commande} €
- Montant consommé: {budget.montant_consomme} €
- Disponible: {budget.montant_disponible()} €
- Taux de consommation: {taux:.1f}%
- Seuil d'alerte 1: {budget.seuil_alerte_1}%

Veuillez surveiller les dépenses et prendre les mesures nécessaires.

Cordialement,
Système de gestion budgétaire
                """

                NotificationService._envoyer_email(email, sujet, email_message)

        logger.warning(f"Seuil 1 atteint pour budget {budget.code}: {taux:.1f}%")

    @staticmethod
    def notifier_budget_seuil_2(budget, taux):
        """
        Notifie le gestionnaire que le deuxième seuil budgétaire a été atteint.

        Args:
            budget: L'enveloppe budgétaire
            taux: Le taux de consommation actuel
        """
        message = f"ALERTE CRITIQUE: Le budget {budget.code} a atteint {taux:.1f}% de consommation (seuil d'alerte 2: {budget.seuil_alerte_2}%)"

        # Notifier le gestionnaire
        if budget.gestionnaire:
            NotificationService._creer_notification_inapp(
                utilisateur=budget.gestionnaire,
                titre=f"ALERTE CRITIQUE - Budget: {budget.code}",
                message=message,
                lien=f"/gestion-achats/budgets/{budget.uuid}/",
                niveau='CRITIQUE'
            )

            email = None
            if hasattr(budget.gestionnaire, 'employe') and hasattr(budget.gestionnaire.employe, 'EMAIL'):
                email = budget.gestionnaire.employe.EMAIL
            elif hasattr(budget.gestionnaire, 'email'):
                email = budget.gestionnaire.email

            if email:
                sujet = f"[GAC] ALERTE CRITIQUE - Seuil 2 atteint: {budget.code}"

                email_message = f"""Bonjour {budget.gestionnaire.get_full_name() if hasattr(budget.gestionnaire, 'get_full_name') else budget.gestionnaire},

ALERTE CRITIQUE: Le deuxième seuil d'alerte budgétaire a été atteint.

Détails du budget:
- Code: {budget.code}
- Libellé: {budget.libelle}
- Montant initial: {budget.montant_initial} €
- Montant engagé: {budget.montant_engage} €
- Montant commandé: {budget.montant_commande} €
- Montant consommé: {budget.montant_consomme} €
- Disponible: {budget.montant_disponible()} €
- Taux de consommation: {taux:.1f}%
- Seuil d'alerte 2: {budget.seuil_alerte_2}%

ACTION URGENTE REQUISE: Le budget est presque épuisé.
Veuillez bloquer ou limiter les nouvelles dépenses sur ce budget.

Cordialement,
Système de gestion budgétaire
                """

                NotificationService._envoyer_email(email, sujet, email_message)

        logger.error(f"SEUIL 2 ATTEINT pour budget {budget.code}: {taux:.1f}%")

    # ========== Notifications de rappel (commandes management) ==========

    @staticmethod
    def rappel_validation_n1(demande):
        """Envoie un rappel au validateur N1 pour une demande en attente."""
        if not demande.validateur_n1:
            logger.warning(f"Demande {demande.numero}: aucun validateur N1 assigné")
            return

        try:
            validateur = demande.validateur_n1
            email = getattr(validateur, 'EMAIL', None) or getattr(validateur.user, 'email', None)

            if not email:
                logger.warning(f"Aucun email pour validateur N1 {validateur}")
                return

            jours_attente = (timezone.now() - demande.date_soumission).days

            sujet = f"[GAC] RAPPEL - Demande {demande.numero} en attente de validation N1"
            message = f"""
Bonjour {validateur.PRENOM} {validateur.NOM},

RAPPEL: Une demande d'achat est en attente de votre validation depuis {jours_attente} jour(s).

Demande : {demande.numero}
Demandeur : {demande.demandeur.PRENOM} {demande.demandeur.NOM}
Objet : {demande.objet}
Montant TTC : {demande.montant_total_ttc} €
Date de soumission : {demande.date_soumission.strftime('%d/%m/%Y à %H:%M')}

Merci de traiter cette demande dans les plus brefs délais :
{settings.SITE_URL}/gestion-achats/demandes/{demande.uuid}/

Cordialement,
Le système GAC
            """

            NotificationService._envoyer_email(email, sujet, message)
            NotificationService._creer_notification_inapp(
                utilisateur=validateur,
                titre=f"RAPPEL - Demande {demande.numero} en attente",
                message=f"En attente depuis {jours_attente} jours",
                lien=f"/gestion-achats/demandes/{demande.uuid}/",
                niveau='WARNING'
            )

        except Exception as e:
            logger.error(f"Erreur rappel validation N1 demande {demande.numero}: {str(e)}")

    @staticmethod
    def rappel_validation_n2(demande):
        """Envoie un rappel au validateur N2 pour une demande en attente."""
        if not demande.validateur_n2:
            logger.warning(f"Demande {demande.numero}: aucun validateur N2 assigné")
            return

        try:
            validateur = demande.validateur_n2
            email = getattr(validateur, 'EMAIL', None) or getattr(validateur.user, 'email', None)

            if not email:
                logger.warning(f"Aucun email pour validateur N2 {validateur}")
                return

            jours_attente = (timezone.now() - demande.date_validation_n1).days

            sujet = f"[GAC] RAPPEL - Demande {demande.numero} en attente de validation N2"
            message = f"""
Bonjour {validateur.PRENOM} {validateur.NOM},

RAPPEL: Une demande d'achat est en attente de votre validation N2 depuis {jours_attente} jour(s).

Demande : {demande.numero}
Demandeur : {demande.demandeur.PRENOM} {demande.demandeur.NOM}
Objet : {demande.objet}
Montant TTC : {demande.montant_total_ttc} €
Date validation N1 : {demande.date_validation_n1.strftime('%d/%m/%Y à %H:%M')}

Merci de traiter cette demande dans les plus brefs délais :
{settings.SITE_URL}/gestion-achats/demandes/{demande.uuid}/

Cordialement,
Le système GAC
            """

            NotificationService._envoyer_email(email, sujet, message)
            NotificationService._creer_notification_inapp(
                utilisateur=validateur,
                titre=f"RAPPEL - Demande {demande.numero} en attente N2",
                message=f"En attente depuis {jours_attente} jours",
                lien=f"/gestion-achats/demandes/{demande.uuid}/",
                niveau='WARNING'
            )

        except Exception as e:
            logger.error(f"Erreur rappel validation N2 demande {demande.numero}: {str(e)}")

    @staticmethod
    def alerte_livraison_retard(bon_commande, jours_retard):
        """Envoie une alerte pour un BC dont la livraison est en retard."""
        try:
            # Notifier l'acheteur
            if bon_commande.acheteur:
                email = getattr(bon_commande.acheteur, 'EMAIL', None) or getattr(bon_commande.acheteur.user, 'email', None)

                if email:
                    sujet = f"[GAC] ALERTE - BC {bon_commande.numero} en retard de livraison"
                    message = f"""
Bonjour {bon_commande.acheteur.PRENOM} {bon_commande.acheteur.NOM},

ALERTE: Le bon de commande suivant est en retard de livraison.

BC : {bon_commande.numero}
Fournisseur : {bon_commande.fournisseur.raison_sociale}
Date livraison prévue : {bon_commande.date_livraison_souhaitee.strftime('%d/%m/%Y')}
Retard : {jours_retard} jour(s)
Montant TTC : {bon_commande.montant_total_ttc} €
Statut : {bon_commande.get_statut_display()}

Actions recommandées :
- Contacter le fournisseur pour connaître le statut de la livraison
- Mettre à jour la date de livraison si nécessaire
- Créer une réception si la livraison a eu lieu

Consulter le BC :
{settings.SITE_URL}/gestion-achats/bons-commande/{bon_commande.pk}/

Cordialement,
Le système GAC
                    """

                    NotificationService._envoyer_email(email, sujet, message)
                    NotificationService._creer_notification_inapp(
                        utilisateur=bon_commande.acheteur,
                        titre=f"BC {bon_commande.numero} en retard",
                        message=f"Retard de {jours_retard} jours",
                        lien=f"/gestion-achats/bons-commande/{bon_commande.pk}/",
                        niveau='ERROR'
                    )

        except Exception as e:
            logger.error(f"Erreur alerte retard BC {bon_commande.numero}: {str(e)}")

    @staticmethod
    def rappel_livraison_proche(bon_commande, jours_restants):
        """Envoie un rappel pour un BC dont la livraison approche."""
        try:
            # Notifier l'acheteur
            if bon_commande.acheteur:
                email = getattr(bon_commande.acheteur, 'EMAIL', None) or getattr(bon_commande.acheteur.user, 'email', None)

                if email:
                    sujet = f"[GAC] Livraison proche - BC {bon_commande.numero}"
                    message = f"""
Bonjour {bon_commande.acheteur.PRENOM} {bon_commande.acheteur.NOM},

RAPPEL: La date de livraison d'un bon de commande approche.

BC : {bon_commande.numero}
Fournisseur : {bon_commande.fournisseur.raison_sociale}
Date livraison prévue : {bon_commande.date_livraison_souhaitee.strftime('%d/%m/%Y')}
Jours restants : {jours_restants}
Montant TTC : {bon_commande.montant_total_ttc} €
Statut : {bon_commande.get_statut_display()}

Pensez à :
- Vérifier avec le fournisseur que la livraison est bien prévue
- Préparer la réception des marchandises
- Désigner un réceptionnaire si nécessaire

Consulter le BC :
{settings.SITE_URL}/gestion-achats/bons-commande/{bon_commande.pk}/

Cordialement,
Le système GAC
                    """

                    NotificationService._envoyer_email(email, sujet, message)
                    NotificationService._creer_notification_inapp(
                        utilisateur=bon_commande.acheteur,
                        titre=f"Livraison proche - BC {bon_commande.numero}",
                        message=f"Dans {jours_restants} jour(s)",
                        lien=f"/gestion-achats/bons-commande/{bon_commande.pk}/",
                        niveau='INFO'
                    )

        except Exception as e:
            logger.error(f"Erreur rappel livraison proche BC {bon_commande.numero}: {str(e)}")

    @staticmethod
    def rappel_reception_brouillon(reception, jours_attente):
        """Envoie un rappel au réceptionnaire pour une réception en brouillon."""
        try:
            receptionnaire = reception.receptionnaire
            email = getattr(receptionnaire, 'EMAIL', None) or getattr(receptionnaire.user, 'email', None)

            if not email:
                logger.warning(f"Aucun email pour réceptionnaire {receptionnaire}")
                return

            sujet = f"[GAC] RAPPEL - Réception {reception.numero} en attente de finalisation"
            message = f"""
Bonjour {receptionnaire.PRENOM} {receptionnaire.NOM},

RAPPEL: Une réception en brouillon est en attente de finalisation depuis {jours_attente} jour(s).

Réception : {reception.numero}
BC : {reception.bon_commande.numero}
Fournisseur : {reception.bon_commande.fournisseur.raison_sociale}
Date création : {reception.date_creation.strftime('%d/%m/%Y à %H:%M')}

Merci de compléter les quantités reçues et valider la réception :
{settings.SITE_URL}/gestion-achats/receptions/{reception.pk}/

Cordialement,
Le système GAC
            """

            NotificationService._envoyer_email(email, sujet, message)
            NotificationService._creer_notification_inapp(
                utilisateur=receptionnaire,
                titre=f"RAPPEL - Réception {reception.numero}",
                message=f"En attente depuis {jours_attente} jours",
                lien=f"/gestion-achats/receptions/{reception.pk}/",
                niveau='WARNING'
            )

        except Exception as e:
            logger.error(f"Erreur rappel réception brouillon {reception.numero}: {str(e)}")

    @staticmethod
    def rappel_validation_reception(reception, jours_attente):
        """Envoie un rappel pour une réception prête à être validée."""
        try:
            # Notifier l'acheteur et le réceptionnaire
            destinataires = []

            if reception.bon_commande.acheteur:
                destinataires.append(reception.bon_commande.acheteur)

            if reception.receptionnaire and reception.receptionnaire != reception.bon_commande.acheteur:
                destinataires.append(reception.receptionnaire)

            for destinataire in destinataires:
                email = getattr(destinataire, 'EMAIL', None) or getattr(destinataire.user, 'email', None)

                if not email:
                    continue

                sujet = f"[GAC] Réception {reception.numero} prête à être validée"
                message = f"""
Bonjour {destinataire.PRENOM} {destinataire.NOM},

INFO: Une réception est complète et en attente de validation depuis {jours_attente} jour(s).

Réception : {reception.numero}
BC : {reception.bon_commande.numero}
Fournisseur : {reception.bon_commande.fournisseur.raison_sociale}
Toutes les lignes ont été renseignées.

Merci de valider la réception :
{settings.SITE_URL}/gestion-achats/receptions/{reception.pk}/validate/

Cordialement,
Le système GAC
                """

                NotificationService._envoyer_email(email, sujet, message)
                NotificationService._creer_notification_inapp(
                    utilisateur=destinataire,
                    titre=f"Réception {reception.numero} prête",
                    message="Toutes les lignes renseignées",
                    lien=f"/gestion-achats/receptions/{reception.pk}/validate/",
                    niveau='INFO'
                )

        except Exception as e:
            logger.error(f"Erreur rappel validation réception {reception.numero}: {str(e)}")
