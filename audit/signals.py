# audit/signals.py
"""
Signaux pour le module Audit.
Gère les notifications automatiques pour les alertes.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import AUAL
from absence.models import NotificationAbsence

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AUAL)
def notifier_alerte_creee(sender, instance, created, **kwargs):
    """
    Envoie une notification automatique aux DRH et ASSISTANT_RH
    lorsqu'une nouvelle alerte est créée.
    """
    if not created:
        # Ne notifier que lors de la création, pas lors des mises à jour
        return

    alerte = instance

    # Récupérer les employés avec le rôle DRH ou ASSISTANT_RH
    try:
        from employee.models import ZY00

        rh_users = ZY00.objects.filter(
            Q(roles_attribues__role__CODE='DRH') | Q(roles_attribues__role__CODE='ASSISTANT_RH'),
            roles_attribues__actif=True,
            etat='actif'
        ).distinct()

        # Créer une notification dans le système pour chaque RH
        for rh in rh_users:
            try:
                # Préparer le message de notification
                message_notification = f"📋 {alerte.REFERENCE}\n"
                message_notification += f"{alerte.TITRE}\n\n"

                message_notification += f"🚨 Priorité : {alerte.get_PRIORITE_display()}\n"
                message_notification += f"📂 Type : {alerte.get_TYPE_ALERTE_display()}\n"

                if alerte.EMPLOYE:
                    message_notification += f"👤 Employé : {alerte.EMPLOYE.nom} {alerte.EMPLOYE.prenoms}\n"

                if alerte.DATE_ECHEANCE:
                    from datetime import date
                    jours_restants = (alerte.DATE_ECHEANCE - date.today()).days
                    if jours_restants < 0:
                        message_notification += f"⚠️ Échéance : {alerte.DATE_ECHEANCE.strftime('%d/%m/%Y')} ({abs(jours_restants)} jours de retard)\n"
                    elif jours_restants == 0:
                        message_notification += f"⚠️ Échéance : {alerte.DATE_ECHEANCE.strftime('%d/%m/%Y')} (Aujourd'hui)\n"
                    else:
                        message_notification += f"📅 Échéance : {alerte.DATE_ECHEANCE.strftime('%d/%m/%Y')} ({jours_restants} jours restants)\n"

                message_notification += f"\n📝 {alerte.DESCRIPTION[:150]}{'...' if len(alerte.DESCRIPTION) > 150 else ''}\n\n"

                # Ajouter l'URL vers le détail de l'alerte
                url_alerte = f"{settings.SITE_URL}/audit/alertes/{alerte.uuid}/"
                message_notification += f"👉 Voir le détail : {url_alerte}"

                NotificationAbsence.objects.create(
                    destinataire=rh,
                    type_notification='ALERTE_CONFORMITE',
                    contexte='AUDIT',
                    message=message_notification
                )
                logger.info(f"Notification créée pour {rh.nom} {rh.prenoms} - Alerte {alerte.REFERENCE}")
            except Exception as e:
                logger.error(f"Erreur création notification pour {rh.nom}: {str(e)}")

        # Envoyer également un email si configuré
        _envoyer_email_notification(alerte, rh_users)

    except Exception as e:
        logger.error(f"Erreur lors de la notification automatique d'alerte: {str(e)}")


def _envoyer_email_notification(alerte, destinataires_rh):
    """
    Envoie un email de notification aux RH.
    """
    if not destinataires_rh:
        return

    # Collecter les emails
    emails = []
    for rh in destinataires_rh:
        if hasattr(rh, 'user') and rh.user.email:
            emails.append(rh.user.email)

    if not emails:
        logger.warning(f"Aucun email trouvé pour les RH - Alerte {alerte.REFERENCE}")
        return

    # Préparer le message
    sujet = f"[{alerte.PRIORITE}] Nouvelle alerte de conformité - {alerte.REFERENCE}"

    message = f"""
Bonjour,

Une nouvelle alerte de conformité a été générée dans le système ONIAN-EasyM :

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RÉFÉRENCE : {alerte.REFERENCE}
🚨 PRIORITÉ : {alerte.get_PRIORITE_display()}
📂 TYPE : {alerte.get_TYPE_ALERTE_display()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 TITRE : {alerte.TITRE}

📝 DESCRIPTION :
{alerte.DESCRIPTION}

"""

    # Ajouter les informations de l'employé concerné
    if alerte.EMPLOYE:
        message += f"""
👤 EMPLOYÉ CONCERNÉ :
   - Nom : {alerte.EMPLOYE.nom} {alerte.EMPLOYE.prenoms}
   - Matricule : {alerte.EMPLOYE.matricule}

"""

    # Ajouter la date d'échéance si elle existe
    if alerte.DATE_ECHEANCE:
        jours_restants = alerte.jours_restants
        if jours_restants is not None:
            if jours_restants < 0:
                message += f"⚠️  ÉCHÉANCE : {alerte.DATE_ECHEANCE.strftime('%d/%m/%Y')} ({alerte.jours_retard} jours de retard)\n\n"
            elif jours_restants == 0:
                message += f"⚠️  ÉCHÉANCE : {alerte.DATE_ECHEANCE.strftime('%d/%m/%Y')} (AUJOURD'HUI)\n\n"
            else:
                message += f"📅 ÉCHÉANCE : {alerte.DATE_ECHEANCE.strftime('%d/%m/%Y')} ({jours_restants} jours restants)\n\n"

    message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Consulter l'alerte : {settings.SITE_URL}/audit/alertes/{alerte.uuid}/

Veuillez prendre les mesures nécessaires dans les meilleurs délais.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 Cet email a été envoyé automatiquement par ONIAN-EasyM
🕐 Date : {alerte.DATE_DETECTION.strftime('%d/%m/%Y à %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Envoyer l'email
    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            fail_silently=False,
        )

        # Marquer la notification comme envoyée
        alerte.NOTIFICATION_ENVOYEE = True
        from django.utils import timezone
        alerte.DATE_NOTIFICATION = timezone.now()
        alerte.save(update_fields=['NOTIFICATION_ENVOYEE', 'DATE_NOTIFICATION'])

        logger.info(f"Email de notification envoyé pour l'alerte {alerte.REFERENCE} à {len(emails)} destinataire(s)")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email pour l'alerte {alerte.REFERENCE}: {str(e)}")
