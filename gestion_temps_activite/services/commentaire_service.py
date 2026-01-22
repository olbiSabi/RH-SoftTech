# gestion_temps_activite/services/commentaire_service.py
"""
Service de gestion des commentaires pour le module GTA.
"""
import re
from django.db.models import Q


class CommentaireService:
    """Service centralisé pour les commentaires GTA."""

    @classmethod
    def peut_voir_commentaires_prives(cls, employe, tache):
        """
        Vérifie si un employé peut voir les commentaires privés d'une tâche.

        Args:
            employe: Instance ZY00
            tache: Instance ZDTA

        Returns:
            bool: True si autorisé à voir les commentaires privés
        """
        if not employe:
            return False

        return any([
            tache.assignee == employe,
            tache.projet and tache.projet.chef_projet == employe,
            employe.has_role('DRH'),
            employe.has_role('GESTION_APP'),
            employe.est_manager_departement(),
        ])

    @classmethod
    def peut_ajouter_commentaire(cls, employe, tache):
        """
        Vérifie si un employé peut ajouter un commentaire sur une tâche.

        Args:
            employe: Instance ZY00
            tache: Instance ZDTA

        Returns:
            bool: True si autorisé à commenter
        """
        if not employe:
            return False

        # Vérifier les différentes conditions
        conditions = [
            tache.assignee == employe,
            tache.projet and tache.projet.chef_projet == employe,
            employe.has_role('DRH'),
            employe.has_role('GESTION_APP'),
        ]

        # Même département que l'assigné
        if tache.assignee:
            conditions.append(
                employe.get_departement_actuel() == tache.assignee.get_departement_actuel()
            )
            conditions.append(employe.est_manager_de(tache.assignee))

        return any(conditions)

    @classmethod
    def peut_modifier_commentaire(cls, employe, commentaire):
        """
        Vérifie si un employé peut modifier un commentaire.

        Args:
            employe: Instance ZY00
            commentaire: Instance ZDCM

        Returns:
            bool: True si autorisé à modifier
        """
        if not employe:
            return False

        return commentaire.peut_modifier(employe)

    @classmethod
    def peut_supprimer_commentaire(cls, employe, commentaire):
        """
        Vérifie si un employé peut supprimer un commentaire.

        Args:
            employe: Instance ZY00
            commentaire: Instance ZDCM

        Returns:
            bool: True si autorisé à supprimer
        """
        if not employe:
            return False

        return commentaire.peut_supprimer(employe)

    @classmethod
    def get_details_visibilite(cls, employe, tache):
        """
        Obtient les détails de visibilité pour un employé sur une tâche.

        Args:
            employe: Instance ZY00
            tache: Instance ZDTA

        Returns:
            list: Liste de raisons expliquant la visibilité
        """
        details = []

        if tache.assignee == employe:
            details.append("Vous êtes assigné à cette tâche")

        if tache.projet and tache.projet.chef_projet == employe:
            details.append("Vous êtes chef de projet")

        if employe.est_manager_departement():
            details.append("Vous êtes manager de département")

        if employe.has_role('DRH') or employe.has_role('GESTION_APP'):
            details.append("Vous avez un rôle RH/Admin")

        if tache.assignee:
            dept = employe.get_departement_actuel()
            if dept and dept == tache.assignee.get_departement_actuel():
                details.append(f"Vous êtes dans la même équipe ({dept.LIBELLE})")

        return details

    @classmethod
    def filtrer_commentaires_visibles(cls, commentaires, employe):
        """
        Filtre les commentaires visibles pour un employé.

        Args:
            commentaires: QuerySet de ZDCM
            employe: Instance ZY00

        Returns:
            list: Liste des commentaires visibles avec permissions
        """
        commentaires_visibles = []

        for commentaire in commentaires:
            if commentaire.peut_voir(employe):
                # Ajouter les permissions calculées
                commentaire.peut_modifier_par = commentaire.peut_modifier(employe)
                commentaire.peut_supprimer_par = commentaire.peut_supprimer(employe)

                # Filtrer les réponses visibles
                reponses_visibles = []
                for reponse in commentaire.reponses.all():
                    if reponse.peut_voir(employe):
                        reponse.peut_modifier_par = reponse.peut_modifier(employe)
                        reponse.peut_supprimer_par = reponse.peut_supprimer(employe)
                        reponses_visibles.append(reponse)

                commentaire.reponses_visibles = reponses_visibles
                commentaires_visibles.append(commentaire)

        return commentaires_visibles

    @classmethod
    def extraire_mentions(cls, contenu):
        """
        Extrait les mentions (@nom) d'un contenu.

        Args:
            contenu: Texte du commentaire

        Returns:
            list: Liste des noms mentionnés
        """
        return re.findall(r'@([A-Za-zÀ-ÖØ-öø-ÿ\s]+)', contenu)

    @classmethod
    def trouver_employes_mentionnes(cls, contenu, exclude_employe=None):
        """
        Trouve les employés mentionnés dans un contenu.

        Args:
            contenu: Texte du commentaire
            exclude_employe: Employé à exclure (auteur)

        Returns:
            QuerySet: Employés trouvés
        """
        from employee.models import ZY00

        mentions = cls.extraire_mentions(contenu)
        if not mentions:
            return ZY00.objects.none()

        query = Q()
        for mention in mentions:
            mention = mention.strip()
            query |= Q(nom__icontains=mention) | Q(prenoms__icontains=mention)

        employes = ZY00.objects.filter(query, etat='actif')

        if exclude_employe:
            employes = employes.exclude(pk=exclude_employe.pk)

        return employes

    @classmethod
    def rechercher_mentions_autocomplete(cls, query, exclude_employe=None, limit=10):
        """
        Recherche les employés pour l'autocomplétion des mentions.

        Args:
            query: Terme de recherche
            exclude_employe: Employé à exclure
            limit: Nombre maximum de résultats

        Returns:
            list: Liste de dictionnaires {id, text}
        """
        from employee.models import ZY00

        if len(query) < 2:
            return []

        employes = ZY00.objects.filter(
            Q(nom__icontains=query) | Q(prenoms__icontains=query),
            etat='actif'
        )

        if exclude_employe:
            employes = employes.exclude(pk=exclude_employe.pk)

        return [
            {
                'id': emp.pk,
                'text': f"{emp.nom} {emp.prenoms}",
            }
            for emp in employes[:limit]
        ]

    @classmethod
    def get_commentaires_tache(cls, tache, employe):
        """
        Récupère les commentaires d'une tâche filtrés pour un employé.

        Args:
            tache: Instance ZDTA
            employe: Instance ZY00

        Returns:
            list: Commentaires visibles
        """
        commentaires_query = tache.commentaires.filter(
            reponse_a__isnull=True
        ).select_related(
            'employe',
            'tache__assignee',
            'tache__projet__chef_projet'
        ).prefetch_related(
            'reponses__employe',
            'mentions'
        ).order_by('-date_creation')

        return cls.filtrer_commentaires_visibles(commentaires_query, employe)
