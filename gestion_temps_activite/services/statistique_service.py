# gestion_temps_activite/services/statistique_service.py
"""
Service de calcul des statistiques pour le module GTA.
"""
from django.db.models import Sum, Count, Q, DecimalField
from django.db.models.functions import Coalesce


class StatistiqueService:
    """Service centralisé pour les statistiques GTA."""

    @classmethod
    def get_stats_dashboard(cls):
        """
        Calcule les statistiques du dashboard principal.

        Returns:
            dict: Statistiques globales
        """
        from gestion_temps_activite.models import ZDCL, ZDPJ, ZDTA

        return {
            'total_clients': ZDCL.objects.filter(actif=True).count(),
            'total_projets': ZDPJ.objects.filter(actif=True).count(),
            'projets_en_cours': ZDPJ.objects.filter(statut='EN_COURS').count(),
            'total_taches': ZDTA.objects.exclude(statut='TERMINE').count(),
        }

    @classmethod
    def get_stats_projet(cls, projet):
        """
        Calcule les statistiques d'un projet.

        Args:
            projet: Instance ZDPJ

        Returns:
            dict: Statistiques du projet
        """
        from gestion_temps_activite.models import ZDTA
        from django.db.models import Sum

        taches = projet.taches.all()
        total_taches = taches.count()
        taches_terminees = taches.filter(statut='TERMINE').count()

        heures_totales = taches.aggregate(
            total=Sum('imputations__duree')
        )['total'] or 0

        budget_restant = None
        pourcentage_budget = None
        if projet.budget_heures:
            budget_restant = float(projet.budget_heures) - float(heures_totales)
            pourcentage_budget = (float(heures_totales) / float(projet.budget_heures)) * 100

        return {
            'total_taches': total_taches,
            'taches_terminees': taches_terminees,
            'heures_totales': heures_totales,
            'budget_restant': budget_restant,
            'pourcentage_budget': pourcentage_budget,
            'avancement': projet.get_avancement_pourcentage(),
        }

    @classmethod
    def get_stats_tache(cls, tache):
        """
        Calcule les statistiques d'une tâche.

        Args:
            tache: Instance ZDTA

        Returns:
            dict: Statistiques de la tâche
        """
        from django.db.models import Sum

        heures_totales = tache.imputations.aggregate(
            total=Sum('duree')
        )['total'] or 0

        return {
            'heures_totales': heures_totales,
            'ecart_estimation': tache.get_ecart_estimation(),
            'sous_taches_count': tache.sous_taches.count(),
            'documents_count': tache.documents.filter(actif=True).count(),
        }

    @classmethod
    def get_stats_client(cls, client):
        """
        Calcule les statistiques d'un client.

        Args:
            client: Instance ZDCL

        Returns:
            dict: Statistiques du client
        """
        projets = client.projets.all()

        return {
            'total_projets': projets.count(),
            'projets_actifs': projets.filter(actif=True).count(),
            'projets_termines': projets.filter(statut='TERMINE').count(),
        }

    @classmethod
    def get_stats_employe(cls, employe, date_debut=None, date_fin=None):
        """
        Calcule les statistiques d'un employé.

        Args:
            employe: Instance ZY00
            date_debut: Date de début (optionnel)
            date_fin: Date de fin (optionnel)

        Returns:
            dict: Statistiques de l'employé
        """
        from gestion_temps_activite.models import ZDTA, ZDIT
        from django.utils import timezone

        if date_debut is None:
            date_debut = timezone.now().date().replace(day=1)
        if date_fin is None:
            date_fin = timezone.now().date()

        # Tâches assignées
        mes_taches = ZDTA.objects.filter(assignee=employe).exclude(statut='TERMINE')

        # Imputations
        mes_imputations = ZDIT.objects.filter(
            employe=employe,
            date__gte=date_debut,
            date__lte=date_fin
        )

        heures_totales = mes_imputations.aggregate(total=Sum('duree'))['total'] or 0
        heures_validees = mes_imputations.filter(valide=True).aggregate(total=Sum('duree'))['total'] or 0

        return {
            'taches_en_cours': mes_taches.count(),
            'heures_totales': heures_totales,
            'heures_validees': heures_validees,
            'heures_en_attente': heures_totales - heures_validees,
            'imputations_a_valider': mes_imputations.filter(valide=False).count(),
        }

    @classmethod
    def get_stats_imputations(cls, queryset):
        """
        Calcule les statistiques agrégées d'un ensemble d'imputations.

        Args:
            queryset: QuerySet de ZDIT

        Returns:
            dict: Statistiques agrégées
        """
        from django.db.models import Sum

        total = queryset.aggregate(total=Sum('duree'))['total'] or 0
        validees = queryset.filter(valide=True).aggregate(total=Sum('duree'))['total'] or 0
        facturables = queryset.filter(
            facturable=True, valide=True
        ).aggregate(total=Sum('duree'))['total'] or 0

        return {
            'total_heures': total,
            'heures_validees': validees,
            'heures_facturables': facturables,
            'total_imputations': queryset.count(),
        }

    @classmethod
    def get_projets_recents(cls, limit=5):
        """
        Récupère les projets les plus récents.

        Args:
            limit: Nombre maximum de projets

        Returns:
            QuerySet: Projets récents
        """
        from gestion_temps_activite.models import ZDPJ

        return ZDPJ.objects.select_related('client').filter(
            actif=True
        ).order_by('-date_creation')[:limit]

    @classmethod
    def get_taches_urgentes(cls, limit=10):
        """
        Récupère les tâches urgentes (haute/critique priorité).

        Args:
            limit: Nombre maximum de tâches

        Returns:
            QuerySet: Tâches urgentes
        """
        from gestion_temps_activite.models import ZDTA

        return ZDTA.objects.select_related('projet', 'assignee').filter(
            priorite__in=['HAUTE', 'CRITIQUE']
        ).exclude(statut='TERMINE').order_by('date_fin_prevue')[:limit]

    @classmethod
    def annotate_projets_stats(cls, queryset):
        """
        Ajoute des annotations de statistiques aux projets.

        Args:
            queryset: QuerySet de ZDPJ

        Returns:
            QuerySet: Projets annotés
        """
        return queryset.annotate(
            nombre_taches=Count('taches'),
            taches_terminees=Count('taches', filter=Q(taches__statut='TERMINE')),
            heures_consommees=Coalesce(
                Sum('taches__imputations__duree'),
                0,
                output_field=DecimalField()
            )
        )

    @classmethod
    def annotate_taches_stats(cls, queryset):
        """
        Ajoute des annotations de statistiques aux tâches.

        Args:
            queryset: QuerySet de ZDTA

        Returns:
            QuerySet: Tâches annotées
        """
        return queryset.annotate(
            heures_realisees=Coalesce(
                Sum('imputations__duree'),
                0,
                output_field=DecimalField()
            )
        )

    @classmethod
    def annotate_clients_stats(cls, queryset):
        """
        Ajoute des annotations de statistiques aux clients.

        Args:
            queryset: QuerySet de ZDCL

        Returns:
            QuerySet: Clients annotés
        """
        return queryset.annotate(
            nombre_projets=Count('projets'),
            projets_actifs=Count('projets', filter=Q(projets__actif=True))
        )
