# gestion_temps_activite/utils/notifications.py
from absence.models import NotificationAbsence
from employee.models import ZY00
from django.db.models import Q


def notifier_nouveau_commentaire(commentaire):
    """
    Notifie les personnes concernées par un nouveau commentaire
    """
    tache = commentaire.tache
    auteur = commentaire.employe
    notifications = []

    # 1. Notifier l'assigné de la tâche (si différent de l'auteur)
    if tache.assignee and tache.assignee != auteur:
        notifications.append(
            NotificationAbsence.creer_notification(
                destinataire=tache.assignee,
                type_notif='COMMENTAIRE_TACHE',
                message=f"💬 Nouveau commentaire sur votre tâche '{tache.titre}'",
                contexte='GTA',
                tache=tache
            )
        )

    # 2. Notifier les personnes mentionnées dans le commentaire
    for mentionne in commentaire.mentions.all():
        if mentionne != auteur:
            notifications.append(
                NotificationAbsence.creer_notification(
                    destinataire=mentionne,
                    type_notif='COMMENTAIRE_TACHE',
                    message=f"💬 Vous avez été mentionné dans un commentaire sur la tâche '{tache.titre}'",
                    contexte='GTA',
                    tache=tache
                )
            )

    # 3. Notifier le chef de projet (si différent de l'auteur et de l'assigné)
    if tache.projet.chef_projet and tache.projet.chef_projet != auteur and tache.projet.chef_projet != tache.assignee:
        notifications.append(
            NotificationAbsence.creer_notification(
                destinataire=tache.projet.chef_projet,
                type_notif='COMMENTAIRE_TACHE',
                message=f"💬 Nouveau commentaire sur la tâche '{tache.titre}' de votre projet",
                contexte='GTA',
                tache=tache
            )
        )

    # 4. Notifier l'auteur du commentaire parent pour les réponses
    if commentaire.reponse_a and commentaire.reponse_a.employe != auteur:
        parent_auteur = commentaire.reponse_a.employe

        # Vérifier qu'on ne l'a pas déjà notifié
        if parent_auteur not in [n.destinataire for n in notifications]:
            notifications.append(
                NotificationAbsence.creer_notification(
                    destinataire=parent_auteur,
                    type_notif='COMMENTAIRE_TACHE',
                    message=f"💬 Quelqu'un a répondu à votre commentaire sur la tâche '{tache.titre}'",
                    contexte='GTA',
                    tache=tache
                )
            )

    return notifications


def notifier_modification_commentaire(commentaire, ancien_contenu):
    """
    Notifie si un commentaire important a été modifié
    (seulement si mentionné des nouvelles personnes)
    """
    # Extraire les anciennes mentions
    import re
    anciennes_mentions = re.findall(r'@([A-Za-zÀ-ÖØ-öø-ÿ\s]+)', ancien_contenu or '')
    nouvelles_mentions = re.findall(r'@([A-Za-zÀ-ÖØ-öø-ÿ\s]+)', commentaire.contenu or '')

    # Nouvelles personnes mentionnées
    nouvelles_personnes = set(nouvelles_mentions) - set(anciennes_mentions)

    notifications = []

    if nouvelles_personnes and commentaire.mentions.exists():
        # Notifier les nouvelles personnes mentionnées
        for mentionne in commentaire.mentions.all():
            # Vérifier si c'est une nouvelle mention
            mentionne_nom = f"{mentionne.nom} {mentionne.prenoms}"
            if any(nom.lower() in mentionne_nom.lower() for nom in nouvelles_personnes):
                if mentionne != commentaire.employe:
                    notifications.append(
                        NotificationAbsence.creer_notification(
                            destinataire=mentionne,
                            type_notif='COMMENTAIRE_TACHE',
                            message=f"💬 Vous avez été mentionné dans un commentaire modifié sur la tâche '{commentaire.tache.titre}'",
                            contexte='GTA',
                            tache=commentaire.tache
                        )
                    )

    return notifications