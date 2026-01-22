# departement/services/departement_service.py
"""
Service de gestion des départements (ZDDE).
"""
from django.db.models import Count, Q


class DepartementService:
    """Service centralisé pour les départements."""

    @classmethod
    def get_all_departements(cls, actifs_seulement=False):
        """
        Récupère tous les départements.

        Args:
            actifs_seulement: Si True, ne retourne que les départements actifs

        Returns:
            QuerySet: Départements
        """
        from departement.models import ZDDE

        queryset = ZDDE.objects.all().order_by('CODE')
        if actifs_seulement:
            queryset = queryset.filter(STATUT=True)
        return queryset

    @classmethod
    def get_departement_by_code(cls, code):
        """
        Récupère un département par son code.

        Args:
            code: Code du département (3 lettres)

        Returns:
            ZDDE ou None
        """
        from departement.models import ZDDE

        try:
            return ZDDE.objects.get(CODE=code.upper())
        except ZDDE.DoesNotExist:
            return None

    @classmethod
    def creer_departement(cls, code, libelle, date_debut, date_fin=None, statut=True):
        """
        Crée un nouveau département.

        Args:
            code: Code du département (3 lettres)
            libelle: Libellé du département
            date_debut: Date de début de validité
            date_fin: Date de fin de validité (optionnel)
            statut: Statut actif (défaut: True)

        Returns:
            ZDDE: Département créé

        Raises:
            ValidationError: Si les données sont invalides
        """
        from departement.models import ZDDE

        departement = ZDDE(
            CODE=code,
            LIBELLE=libelle,
            DATEDEB=date_debut,
            DATEFIN=date_fin,
            STATUT=statut
        )
        departement.save()
        return departement

    @classmethod
    def modifier_departement(cls, departement, **kwargs):
        """
        Modifie un département existant.

        Args:
            departement: Instance ZDDE
            **kwargs: Champs à modifier

        Returns:
            ZDDE: Département modifié
        """
        for key, value in kwargs.items():
            if hasattr(departement, key):
                setattr(departement, key, value)
        departement.save()
        return departement

    @classmethod
    def supprimer_departement(cls, departement):
        """
        Supprime un département.

        Args:
            departement: Instance ZDDE

        Returns:
            bool: True si supprimé avec succès

        Raises:
            Exception: Si le département a des postes associés
        """
        if departement.postes.exists():
            raise Exception(
                f"Impossible de supprimer le département {departement.CODE}. "
                f"Il possède {departement.postes.count()} poste(s) associé(s)."
            )
        departement.delete()
        return True

    @classmethod
    def get_statistiques_departement(cls, departement):
        """
        Calcule les statistiques d'un département.

        Args:
            departement: Instance ZDDE

        Returns:
            dict: Statistiques du département
        """
        from departement.models import ZYMA

        postes = departement.postes.all()
        manager = ZYMA.get_manager_actif(departement)

        # Compter les employés via les affectations actives
        employes_count = 0
        for poste in postes:
            employes_count += poste.affectations.filter(date_fin__isnull=True).count()

        return {
            'nombre_postes': postes.count(),
            'postes_actifs': postes.filter(STATUT=True).count(),
            'nombre_employes': employes_count,
            'manager': manager.employe if manager else None,
            'a_manager': manager is not None,
        }

    @classmethod
    def get_departements_avec_stats(cls, actifs_seulement=False):
        """
        Récupère les départements avec leurs statistiques.

        Args:
            actifs_seulement: Si True, ne retourne que les actifs

        Returns:
            list: Liste de tuples (departement, stats)
        """
        departements = cls.get_all_departements(actifs_seulement)
        result = []
        for dept in departements:
            stats = cls.get_statistiques_departement(dept)
            result.append((dept, stats))
        return result

    @classmethod
    def valider_code(cls, code, exclude_pk=None):
        """
        Valide un code de département.

        Args:
            code: Code à valider
            exclude_pk: PK à exclure (pour modification)

        Returns:
            tuple: (is_valid, error_message)
        """
        from departement.models import ZDDE

        if not code:
            return False, "Le code est requis."

        code = code.upper().strip()

        if len(code) != 3:
            return False, "Le code doit contenir exactement 3 caractères."

        if not code.isalpha():
            return False, "Le code ne doit contenir que des lettres."

        # Vérifier l'unicité
        existing = ZDDE.objects.filter(CODE=code)
        if exclude_pk:
            existing = existing.exclude(pk=exclude_pk)
        if existing.exists():
            return False, f"Le code {code} existe déjà."

        return True, None
