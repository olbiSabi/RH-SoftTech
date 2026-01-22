# departement/services/manager_service.py
"""
Service de gestion des managers de département (ZYMA).
"""
from datetime import date


class ManagerService:
    """Service centralisé pour la gestion des managers."""

    @classmethod
    def get_manager_actif(cls, departement):
        """
        Récupère le manager actif d'un département.

        Args:
            departement: Instance ZDDE

        Returns:
            ZYMA ou None
        """
        from departement.models import ZYMA
        return ZYMA.get_manager_actif(departement)

    @classmethod
    def get_all_managers(cls, actifs_seulement=False):
        """
        Récupère tous les managers.

        Args:
            actifs_seulement: Si True, ne retourne que les managers actifs

        Returns:
            QuerySet: Managers
        """
        from departement.models import ZYMA

        queryset = ZYMA.objects.select_related(
            'departement', 'employe'
        ).order_by('-date_debut')

        if actifs_seulement:
            queryset = queryset.filter(date_fin__isnull=True)

        return queryset

    @classmethod
    def get_departements_sans_manager(cls):
        """
        Récupère les départements actifs sans manager.

        Returns:
            QuerySet: Départements sans manager
        """
        from departement.models import ZYMA
        return ZYMA.get_departements_sans_manager()

    @classmethod
    def get_employes_eligibles(cls):
        """
        Récupère les employés éligibles pour être managers.

        Returns:
            QuerySet: Employés salariés actifs
        """
        from departement.models import ZYMA
        return ZYMA.get_employes_eligibles_managers()

    @classmethod
    def nommer_manager(cls, departement, employe, date_debut, date_fin=None):
        """
        Nomme un employé comme manager d'un département.

        Args:
            departement: Instance ZDDE
            employe: Instance ZY00
            date_debut: Date de début de management
            date_fin: Date de fin (optionnel)

        Returns:
            ZYMA: Manager créé

        Raises:
            ValidationError: Si les données sont invalides
        """
        from departement.models import ZYMA

        manager = ZYMA(
            departement=departement,
            employe=employe,
            date_debut=date_debut,
            date_fin=date_fin
        )
        manager.save()
        return manager

    @classmethod
    def cloturer_manager(cls, departement, date_fin=None):
        """
        Clôture le manager actif d'un département.

        Args:
            departement: Instance ZDDE
            date_fin: Date de fin (défaut: aujourd'hui)

        Returns:
            bool: True si clôturé avec succès
        """
        from departement.models import ZYMA

        if date_fin is None:
            date_fin = date.today()

        return ZYMA.cloturer_manager_actuel(departement, date_fin)

    @classmethod
    def changer_manager(cls, departement, nouvel_employe, date_changement=None):
        """
        Change le manager d'un département (clôture l'ancien et nomme le nouveau).

        Args:
            departement: Instance ZDDE
            nouvel_employe: Instance ZY00
            date_changement: Date du changement (défaut: aujourd'hui)

        Returns:
            ZYMA: Nouveau manager

        Raises:
            ValidationError: Si les données sont invalides
        """
        if date_changement is None:
            date_changement = date.today()

        # Clôturer l'ancien manager si existant
        cls.cloturer_manager(departement, date_changement)

        # Nommer le nouveau manager
        return cls.nommer_manager(departement, nouvel_employe, date_changement)

    @classmethod
    def get_historique_managers(cls, departement):
        """
        Récupère l'historique des managers d'un département.

        Args:
            departement: Instance ZDDE

        Returns:
            QuerySet: Historique des managers
        """
        from departement.models import ZYMA
        return ZYMA.get_historique_managers_departement(departement)

    @classmethod
    def est_manager(cls, employe):
        """
        Vérifie si un employé est manager d'un département.

        Args:
            employe: Instance ZY00

        Returns:
            bool: True si l'employé est manager actif
        """
        from departement.models import ZYMA
        return ZYMA.get_manager_actuel_employe(employe) is not None

    @classmethod
    def get_departement_manage(cls, employe):
        """
        Récupère le département géré par un employé.

        Args:
            employe: Instance ZY00

        Returns:
            ZDDE ou None
        """
        from departement.models import ZYMA

        management = ZYMA.get_manager_actuel_employe(employe)
        return management.departement if management else None

    @classmethod
    def get_manager_employe(cls, employe):
        """
        Récupère le manager d'un employé basé sur son département.

        Args:
            employe: Instance ZY00

        Returns:
            ZYMA ou None
        """
        from employee.models import ZYAF

        try:
            affectation_active = ZYAF.objects.filter(
                employe=employe,
                date_fin__isnull=True
            ).first()

            if affectation_active:
                return cls.get_manager_actif(affectation_active.poste.DEPARTEMENT)
            return None
        except Exception:
            return None

    @classmethod
    def valider_nomination(cls, departement, employe, exclude_pk=None):
        """
        Valide une nomination de manager.

        Args:
            departement: Instance ZDDE
            employe: Instance ZY00
            exclude_pk: PK à exclure (pour modification)

        Returns:
            tuple: (is_valid, errors_dict)
        """
        from departement.models import ZYMA

        errors = {}

        # Vérifier que l'employé est un salarié
        if employe.type_dossier != 'SAL':
            errors['employe'] = "Seuls les employés salariés peuvent être désignés comme managers."

        # Vérifier qu'il n'y a pas déjà un manager actif pour ce département
        existing_manager = ZYMA.objects.filter(
            departement=departement,
            date_fin__isnull=True
        )
        if exclude_pk:
            existing_manager = existing_manager.exclude(pk=exclude_pk)

        if existing_manager.exists():
            manager = existing_manager.first()
            errors['departement'] = (
                f"Un manager actif existe déjà : {manager.employe.nom} {manager.employe.prenoms}"
            )

        # Vérifier que l'employé n'est pas déjà manager d'un autre département
        other_management = ZYMA.objects.filter(
            employe=employe,
            date_fin__isnull=True
        )
        if exclude_pk:
            other_management = other_management.exclude(pk=exclude_pk)

        if other_management.exists():
            autre_dept = other_management.first().departement
            errors['employe'] = (
                f"Cet employé est déjà manager du département {autre_dept.LIBELLE}."
            )

        return len(errors) == 0, errors

    @classmethod
    def get_statistiques_managers(cls):
        """
        Calcule les statistiques globales des managers.

        Returns:
            dict: Statistiques
        """
        from departement.models import ZDDE, ZYMA

        total_departements = ZDDE.objects.filter(STATUT=True).count()
        departements_avec_manager = ZYMA.objects.filter(
            date_fin__isnull=True
        ).values('departement').distinct().count()

        return {
            'total_departements_actifs': total_departements,
            'departements_avec_manager': departements_avec_manager,
            'departements_sans_manager': total_departements - departements_avec_manager,
            'taux_couverture': (
                (departements_avec_manager / total_departements * 100)
                if total_departements > 0 else 0
            ),
        }
