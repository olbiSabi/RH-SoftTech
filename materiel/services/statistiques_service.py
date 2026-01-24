# materiel/services/statistiques_service.py
"""
Service pour les statistiques du parc matériel.
"""
from decimal import Decimal
from typing import Optional
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone


class StatistiquesMaterielService:
    """Service pour les statistiques du matériel."""

    @staticmethod
    def get_stats_globales() -> dict:
        """
        Récupère les statistiques globales du parc matériel.

        Returns:
            Dictionnaire avec les stats
        """
        from materiel.models import MTMT, MTAF, MTMA

        # Stats matériel
        materiels = MTMT.objects.all()
        stats_materiels = materiels.aggregate(
            total=Count('id'),
            valeur_totale=Sum('PRIX_ACQUISITION'),
        )

        # Par statut
        par_statut = {}
        for statut, _ in MTMT.STATUT_CHOICES:
            par_statut[statut] = materiels.filter(STATUT=statut).count()

        # Par état
        par_etat = {}
        for etat, _ in MTMT.ETAT_CHOICES:
            par_etat[etat] = materiels.filter(ETAT=etat).count()

        # Affectations actives
        affectations_actives = MTAF.objects.filter(ACTIF=True).count()

        # Maintenances
        maintenances_en_cours = MTMA.objects.filter(
            STATUT__in=['PLANIFIE', 'EN_COURS']
        ).count()

        # Prêts en retard
        prets_en_retard = MTAF.objects.filter(
            ACTIF=True,
            TYPE_AFFECTATION='PRET',
            DATE_RETOUR_PREVUE__lt=timezone.now().date()
        ).count()

        # Matériel sous garantie
        sous_garantie = materiels.filter(
            DATE_FIN_GARANTIE__gte=timezone.now().date()
        ).count()

        return {
            'total_materiels': stats_materiels['total'] or 0,
            'valeur_totale': stats_materiels['valeur_totale'] or Decimal('0'),
            'par_statut': par_statut,
            'par_etat': par_etat,
            'disponibles': par_statut.get('DISPONIBLE', 0),
            'affectes': par_statut.get('AFFECTE', 0),
            'en_maintenance': par_statut.get('EN_MAINTENANCE', 0),
            'affectations_actives': affectations_actives,
            'maintenances_en_cours': maintenances_en_cours,
            'prets_en_retard': prets_en_retard,
            'sous_garantie': sous_garantie,
        }

    @staticmethod
    def get_stats_par_categorie() -> list:
        """
        Récupère les statistiques par catégorie de matériel.

        Returns:
            Liste de dictionnaires avec stats par catégorie
        """
        from materiel.models import MTCA, MTMT

        categories = MTCA.objects.filter(STATUT=True).order_by('ORDRE', 'LIBELLE')

        result = []
        for cat in categories:
            materiels = MTMT.objects.filter(CATEGORIE=cat)
            stats = materiels.aggregate(
                total=Count('id'),
                valeur_totale=Sum('PRIX_ACQUISITION'),
            )

            result.append({
                'categorie': cat,
                'total': stats['total'] or 0,
                'valeur_totale': stats['valeur_totale'] or Decimal('0'),
                'disponibles': materiels.filter(STATUT='DISPONIBLE').count(),
                'affectes': materiels.filter(STATUT='AFFECTE').count(),
                'en_maintenance': materiels.filter(STATUT='EN_MAINTENANCE').count(),
            })

        return result

    @staticmethod
    def get_stats_employe(employe) -> dict:
        """
        Récupère les statistiques matériel pour un employé.

        Args:
            employe: Instance ZY00

        Returns:
            Dictionnaire avec les stats
        """
        from materiel.models import MTMT, MTAF

        # Matériel actuellement affecté
        materiels_affectes = MTMT.objects.filter(AFFECTE_A=employe)

        # Historique des affectations
        historique = MTAF.objects.filter(EMPLOYE=employe)

        return {
            'nb_materiels_affectes': materiels_affectes.count(),
            'valeur_totale_affectee': materiels_affectes.aggregate(
                Sum('PRIX_ACQUISITION')
            )['PRIX_ACQUISITION__sum'] or Decimal('0'),
            'nb_affectations_total': historique.count(),
            'nb_affectations_actives': historique.filter(ACTIF=True).count(),
            'materiels': materiels_affectes.select_related('CATEGORIE'),
        }

    @staticmethod
    def get_couts_maintenance(annee: Optional[int] = None) -> dict:
        """
        Récupère les coûts de maintenance.

        Args:
            annee: Année à analyser (défaut: année courante)

        Returns:
            Dictionnaire avec les coûts
        """
        from materiel.models import MTMA

        if annee is None:
            annee = timezone.now().year

        maintenances = MTMA.objects.filter(
            DATE_FIN__year=annee,
            STATUT='TERMINE'
        )

        stats = maintenances.aggregate(
            nb_maintenances=Count('id'),
            total_pieces=Sum('COUT_PIECES'),
            total_main_oeuvre=Sum('COUT_MAIN_OEUVRE'),
        )

        total_pieces = stats['total_pieces'] or Decimal('0')
        total_main_oeuvre = stats['total_main_oeuvre'] or Decimal('0')

        # Par type de maintenance
        par_type = {}
        for type_m, _ in MTMA.TYPE_CHOICES:
            type_stats = maintenances.filter(TYPE_MAINTENANCE=type_m).aggregate(
                count=Count('id'),
                cout_total=Sum('COUT_PIECES') + Sum('COUT_MAIN_OEUVRE')
            )
            par_type[type_m] = {
                'count': type_stats['count'] or 0,
                'cout': type_stats['cout_total'] or Decimal('0')
            }

        return {
            'annee': annee,
            'nb_maintenances': stats['nb_maintenances'] or 0,
            'cout_pieces': total_pieces,
            'cout_main_oeuvre': total_main_oeuvre,
            'cout_total': total_pieces + total_main_oeuvre,
            'par_type': par_type,
        }

    @staticmethod
    def get_valeur_parc() -> dict:
        """
        Calcule la valeur du parc matériel.

        Returns:
            Dictionnaire avec les valeurs
        """
        from materiel.models import MTMT

        materiels = MTMT.objects.exclude(STATUT='REFORME')

        # Valeur d'acquisition
        valeur_acquisition = materiels.aggregate(
            Sum('PRIX_ACQUISITION')
        )['PRIX_ACQUISITION__sum'] or Decimal('0')

        # Valeur résiduelle (calculée)
        valeur_residuelle = Decimal('0')
        for mat in materiels:
            valeur_residuelle += mat.valeur_residuelle

        return {
            'valeur_acquisition': valeur_acquisition,
            'valeur_residuelle': valeur_residuelle,
            'amortissement_cumule': valeur_acquisition - valeur_residuelle,
            'taux_amortissement': (
                (valeur_acquisition - valeur_residuelle) / valeur_acquisition * 100
                if valeur_acquisition > 0 else 0
            ),
        }

    @staticmethod
    def get_top_fournisseurs(limit: int = 10) -> list:
        """
        Récupère les principaux fournisseurs.

        Args:
            limit: Nombre de fournisseurs à retourner

        Returns:
            Liste des fournisseurs avec stats
        """
        from materiel.models import MTFO, MTMT

        fournisseurs = MTFO.objects.filter(STATUT=True).annotate(
            nb_materiels=Count('materiels_fournis'),
            valeur_totale=Sum('materiels_fournis__PRIX_ACQUISITION')
        ).filter(
            nb_materiels__gt=0
        ).order_by('-valeur_totale')[:limit]

        return list(fournisseurs)

    @staticmethod
    def get_alertes() -> dict:
        """
        Récupère les alertes du parc matériel.

        Returns:
            Dictionnaire avec les différentes alertes
        """
        from materiel.models import MTMT, MTAF, MTMA
        from datetime import timedelta

        today = timezone.now().date()

        # Garanties expirant bientôt (30 jours)
        garanties_expirant = MTMT.objects.filter(
            DATE_FIN_GARANTIE__lte=today + timedelta(days=30),
            DATE_FIN_GARANTIE__gte=today
        ).exclude(STATUT='REFORME')

        # Prêts en retard
        prets_retard = MTAF.objects.filter(
            ACTIF=True,
            TYPE_AFFECTATION='PRET',
            DATE_RETOUR_PREVUE__lt=today
        ).select_related('MATERIEL', 'EMPLOYE')

        # Maintenances en retard
        maintenances_retard = MTMA.objects.filter(
            STATUT='PLANIFIE',
            DATE_PLANIFIEE__lt=today
        ).select_related('MATERIEL')

        # Matériel défaillant
        materiel_defaillant = MTMT.objects.filter(
            ETAT__in=['DEFAILLANT', 'HORS_SERVICE']
        ).exclude(STATUT='REFORME')

        return {
            'garanties_expirant': list(garanties_expirant),
            'prets_retard': list(prets_retard),
            'maintenances_retard': list(maintenances_retard),
            'materiel_defaillant': list(materiel_defaillant),
            'nb_alertes': (
                garanties_expirant.count() +
                prets_retard.count() +
                maintenances_retard.count() +
                materiel_defaillant.count()
            ),
        }
