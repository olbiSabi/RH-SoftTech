# departement/services/poste_service.py
"""
Service de gestion des postes (ZDPO).
"""
from django.db.models import Count


class PosteService:
    """Service centralisé pour les postes."""

    @classmethod
    def get_all_postes(cls, actifs_seulement=False, departement=None):
        """
        Récupère tous les postes.

        Args:
            actifs_seulement: Si True, ne retourne que les postes actifs
            departement: Filtrer par département (optionnel)

        Returns:
            QuerySet: Postes
        """
        from departement.models import ZDPO

        queryset = ZDPO.objects.select_related('DEPARTEMENT').all().order_by('CODE')

        if actifs_seulement:
            queryset = queryset.filter(STATUT=True)

        if departement:
            queryset = queryset.filter(DEPARTEMENT=departement)

        return queryset

    @classmethod
    def get_poste_by_code(cls, code):
        """
        Récupère un poste par son code.

        Args:
            code: Code du poste (6 caractères)

        Returns:
            ZDPO ou None
        """
        from departement.models import ZDPO

        try:
            return ZDPO.objects.get(CODE=code.upper())
        except ZDPO.DoesNotExist:
            return None

    @classmethod
    def creer_poste(cls, code, libelle, departement, date_debut, date_fin=None, statut=True):
        """
        Crée un nouveau poste.

        Args:
            code: Code du poste (6 caractères)
            libelle: Libellé du poste
            departement: Instance ZDDE
            date_debut: Date de début de validité
            date_fin: Date de fin de validité (optionnel)
            statut: Statut actif (défaut: True)

        Returns:
            ZDPO: Poste créé

        Raises:
            ValidationError: Si les données sont invalides
        """
        from departement.models import ZDPO

        poste = ZDPO(
            CODE=code,
            LIBELLE=libelle,
            DEPARTEMENT=departement,
            DATEDEB=date_debut,
            DATEFIN=date_fin,
            STATUT=statut
        )
        poste.save()
        return poste

    @classmethod
    def modifier_poste(cls, poste, **kwargs):
        """
        Modifie un poste existant.

        Args:
            poste: Instance ZDPO
            **kwargs: Champs à modifier

        Returns:
            ZDPO: Poste modifié
        """
        for key, value in kwargs.items():
            if hasattr(poste, key):
                setattr(poste, key, value)
        poste.save()
        return poste

    @classmethod
    def supprimer_poste(cls, poste):
        """
        Supprime un poste.

        Args:
            poste: Instance ZDPO

        Returns:
            bool: True si supprimé avec succès

        Raises:
            Exception: Si le poste a des affectations actives
        """
        affectations_actives = poste.affectations.filter(date_fin__isnull=True).count()
        if affectations_actives > 0:
            raise Exception(
                f"Impossible de supprimer le poste {poste.CODE}. "
                f"Il a {affectations_actives} affectation(s) active(s)."
            )
        poste.delete()
        return True

    @classmethod
    def get_postes_par_departement(cls, departement, actifs_seulement=True):
        """
        Récupère les postes d'un département.

        Args:
            departement: Instance ZDDE
            actifs_seulement: Si True, ne retourne que les actifs

        Returns:
            QuerySet: Postes du département
        """
        return cls.get_all_postes(
            actifs_seulement=actifs_seulement,
            departement=departement
        )

    @classmethod
    def get_statistiques_poste(cls, poste):
        """
        Calcule les statistiques d'un poste.

        Args:
            poste: Instance ZDPO

        Returns:
            dict: Statistiques du poste
        """
        affectations = poste.affectations.all()

        return {
            'nombre_affectations_totales': affectations.count(),
            'affectations_actives': affectations.filter(date_fin__isnull=True).count(),
            'departement': poste.DEPARTEMENT,
            'est_actif': poste.STATUT,
        }

    @classmethod
    def valider_code(cls, code, exclude_pk=None):
        """
        Valide un code de poste.

        Args:
            code: Code à valider
            exclude_pk: PK à exclure (pour modification)

        Returns:
            tuple: (is_valid, error_message)
        """
        from departement.models import ZDPO

        if not code:
            return False, "Le code est requis."

        code = code.upper().strip()

        if len(code) != 6:
            return False, "Le code doit contenir exactement 6 caractères."

        if not code.isalnum():
            return False, "Le code ne doit contenir que des lettres et des chiffres."

        # Vérifier l'unicité
        existing = ZDPO.objects.filter(CODE=code)
        if exclude_pk:
            existing = existing.exclude(pk=exclude_pk)
        if existing.exists():
            return False, f"Le code {code} existe déjà."

        return True, None

    @classmethod
    def get_postes_vacants(cls, departement=None):
        """
        Récupère les postes sans affectation active.

        Args:
            departement: Filtrer par département (optionnel)

        Returns:
            QuerySet: Postes vacants
        """
        from departement.models import ZDPO

        queryset = ZDPO.objects.filter(STATUT=True).annotate(
            nb_affectations_actives=Count(
                'affectations',
                filter=models.Q(affectations__date_fin__isnull=True)
            )
        ).filter(nb_affectations_actives=0)

        if departement:
            queryset = queryset.filter(DEPARTEMENT=departement)

        return queryset
