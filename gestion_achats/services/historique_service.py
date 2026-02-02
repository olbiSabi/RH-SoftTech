"""
Service métier pour la gestion de l'historique.

Ce service encapsule toute la logique métier liée à l'historique,
incluant l'ajout d'entrées et la récupération de l'historique des objets.
"""

import logging
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from gestion_achats.models import GACHistorique

logger = logging.getLogger(__name__)


class HistoriqueService:
    """Service pour la gestion de l'historique."""

    @staticmethod
    def ajouter_entree(objet, utilisateur, action, details, ancien_statut=None, nouveau_statut=None):
        """
        Ajoute une entrée dans l'historique.

        Args:
            objet: L'objet concerné (GenericForeignKey)
            utilisateur: L'utilisateur auteur (optionnel)
            action: Code de l'action (CREATION, MODIFICATION, VALIDATION, etc.)
            details: Description textuelle
            ancien_statut: Ancien statut (optionnel)
            nouveau_statut: Nouveau statut (optionnel)

        Returns:
            GACHistorique: L'entrée d'historique créée
        """
        try:
            historique = GACHistorique.objects.create(
                content_type=ContentType.objects.get_for_model(objet),
                object_id=objet.pk,
                utilisateur=utilisateur,
                action=action,
                description=details,
                ancien_statut=ancien_statut,
                nouveau_statut=nouveau_statut,
                date_action=timezone.now()
            )

            logger.debug(
                f"Historique ajouté: {action} sur {objet.__class__.__name__} "
                f"#{objet.pk} par {utilisateur or 'Système'}"
            )

            return historique

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'historique: {str(e)}")
            # On ne lève pas d'exception pour ne pas bloquer le workflow principal
            return None

    @staticmethod
    def get_historique_objet(objet, limit=None):
        """
        Récupère l'historique d'un objet.

        Args:
            objet: L'objet concerné
            limit: Nombre maximum d'entrées à retourner (optionnel)

        Returns:
            QuerySet: Entrées d'historique triées par date décroissante
        """
        queryset = GACHistorique.objects.filter(
            content_type=ContentType.objects.get_for_model(objet),
            object_id=objet.pk
        ).order_by('-date_action')

        if limit:
            queryset = queryset[:limit]

        return queryset

    @staticmethod
    def get_historique_utilisateur(utilisateur, limit=None):
        """
        Récupère l'historique des actions d'un utilisateur.

        Args:
            utilisateur: L'utilisateur concerné
            limit: Nombre maximum d'entrées à retourner (optionnel)

        Returns:
            QuerySet: Entrées d'historique triées par date décroissante
        """
        queryset = GACHistorique.objects.filter(
            utilisateur=utilisateur
        ).order_by('-date_action')

        if limit:
            queryset = queryset[:limit]

        return queryset

    @staticmethod
    def get_historique_par_action(action, limit=None):
        """
        Récupère l'historique filtré par type d'action.

        Args:
            action: Le code d'action (CREATION, VALIDATION, etc.)
            limit: Nombre maximum d'entrées à retourner (optionnel)

        Returns:
            QuerySet: Entrées d'historique triées par date décroissante
        """
        queryset = GACHistorique.objects.filter(
            action=action
        ).order_by('-date_action')

        if limit:
            queryset = queryset[:limit]

        return queryset

    @staticmethod
    def get_statistiques_actions(date_debut=None, date_fin=None):
        """
        Récupère les statistiques sur les actions enregistrées.

        Args:
            date_debut: Date de début de la période (optionnel)
            date_fin: Date de fin de la période (optionnel)

        Returns:
            dict: Statistiques par type d'action
        """
        from django.db.models import Count

        queryset = GACHistorique.objects.all()

        if date_debut:
            queryset = queryset.filter(date_action__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_action__lte=date_fin)

        # Compter par action
        par_action = queryset.values('action').annotate(
            nombre=Count('id')
        ).order_by('-nombre')

        # Compter par utilisateur
        par_utilisateur = queryset.filter(
            utilisateur__isnull=False
        ).values(
            'utilisateur__first_name',
            'utilisateur__last_name'
        ).annotate(
            nombre=Count('id')
        ).order_by('-nombre')[:10]

        return {
            'total_actions': queryset.count(),
            'par_action': {item['action']: item['nombre'] for item in par_action},
            'top_utilisateurs': list(par_utilisateur),
        }
