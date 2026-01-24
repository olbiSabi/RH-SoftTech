# entreprise/services/entreprise_service.py
"""Service de gestion de l'entreprise."""

from django.db import transaction
from django.core.exceptions import ValidationError


class EntrepriseService:
    """Service centralisé pour la gestion de l'entreprise."""

    @classmethod
    def get_entreprise(cls):
        """
        Récupère l'entreprise unique.

        Returns:
            Entreprise ou None
        """
        from entreprise.models import Entreprise
        return Entreprise.objects.first()

    @classmethod
    def entreprise_existe(cls):
        """
        Vérifie si une entreprise existe.

        Returns:
            bool: True si une entreprise existe
        """
        from entreprise.models import Entreprise
        return Entreprise.objects.exists()

    @classmethod
    def create_entreprise(cls, **kwargs):
        """
        Crée une nouvelle entreprise.

        Args:
            **kwargs: Données de l'entreprise

        Returns:
            Entreprise: Instance créée

        Raises:
            ValidationError: Si une entreprise existe déjà ou données invalides
        """
        from entreprise.models import Entreprise

        if cls.entreprise_existe():
            raise ValidationError(
                "Une entreprise existe déjà. "
                "Veuillez la modifier au lieu d'en créer une nouvelle."
            )

        with transaction.atomic():
            entreprise = Entreprise(**kwargs)
            entreprise.save()
            return entreprise

    @classmethod
    def update_entreprise(cls, entreprise, **kwargs):
        """
        Met à jour une entreprise.

        Args:
            entreprise: Instance Entreprise
            **kwargs: Données à mettre à jour

        Returns:
            Entreprise: Instance mise à jour

        Raises:
            ValidationError: Si données invalides
        """
        with transaction.atomic():
            for key, value in kwargs.items():
                if hasattr(entreprise, key):
                    setattr(entreprise, key, value)
            entreprise.save()
            return entreprise

    @classmethod
    def delete_entreprise(cls, entreprise):
        """
        Supprime une entreprise.

        Args:
            entreprise: Instance Entreprise

        Returns:
            bool: True si supprimée

        Raises:
            ValidationError: Si l'entreprise a des employés
        """
        if entreprise.effectif_total > 0:
            raise ValidationError(
                f"Impossible de supprimer l'entreprise '{entreprise.nom}'. "
                f"Elle possède {entreprise.effectif_total} employé(s) actif(s)."
            )

        with transaction.atomic():
            entreprise.delete()
            return True

    @classmethod
    def get_entreprise_by_uuid(cls, uuid):
        """
        Récupère une entreprise par son UUID.

        Args:
            uuid: UUID de l'entreprise

        Returns:
            Entreprise ou None
        """
        from entreprise.models import Entreprise

        try:
            return Entreprise.objects.get(uuid=uuid)
        except Entreprise.DoesNotExist:
            return None

    @classmethod
    def get_entreprise_by_code(cls, code):
        """
        Récupère une entreprise par son code.

        Args:
            code: Code de l'entreprise

        Returns:
            Entreprise ou None
        """
        from entreprise.models import Entreprise

        try:
            return Entreprise.objects.get(code=code)
        except Entreprise.DoesNotExist:
            return None

    @classmethod
    def activer_entreprise(cls, entreprise):
        """
        Active une entreprise.

        Args:
            entreprise: Instance Entreprise

        Returns:
            bool: True si activée
        """
        entreprise.actif = True
        entreprise.save()
        return True

    @classmethod
    def desactiver_entreprise(cls, entreprise):
        """
        Désactive une entreprise.

        Args:
            entreprise: Instance Entreprise

        Returns:
            bool: True si désactivée
        """
        entreprise.actif = False
        entreprise.save()
        return True

    @classmethod
    def get_convention_en_vigueur(cls, entreprise=None):
        """
        Récupère la convention collective en vigueur.

        Args:
            entreprise: Instance Entreprise (optionnel, sinon entreprise par défaut)

        Returns:
            ConfigurationConventionnelle ou None
        """
        if entreprise is None:
            entreprise = cls.get_entreprise()

        if entreprise is None:
            return None

        return entreprise.convention_en_vigueur

    @classmethod
    def set_convention(cls, entreprise, convention, date_application=None):
        """
        Définit la convention collective de l'entreprise.

        Args:
            entreprise: Instance Entreprise
            convention: Instance ConfigurationConventionnelle
            date_application: Date d'application (optionnel)

        Returns:
            Entreprise: Instance mise à jour
        """
        from datetime import date

        entreprise.configuration_conventionnelle = convention
        if date_application:
            entreprise.date_application_convention = date_application
        elif not entreprise.date_application_convention:
            entreprise.date_application_convention = date.today()

        entreprise.save()
        return entreprise

    @classmethod
    def valider_code(cls, code, exclude_pk=None):
        """
        Valide un code d'entreprise.

        Args:
            code: Code à valider
            exclude_pk: PK à exclure (pour modification)

        Returns:
            tuple: (is_valid, errors_dict)
        """
        from entreprise.models import Entreprise

        errors = {}

        if not code:
            errors['code'] = "Le code est requis."
            return False, errors

        if len(code) > 10:
            errors['code'] = "Le code ne doit pas dépasser 10 caractères."

        # Vérifier l'unicité
        queryset = Entreprise.objects.filter(code=code)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)

        if queryset.exists():
            errors['code'] = "Ce code est déjà utilisé."

        return len(errors) == 0, errors

    @classmethod
    def get_statistiques(cls, entreprise=None):
        """
        Calcule les statistiques de l'entreprise.

        Args:
            entreprise: Instance Entreprise (optionnel)

        Returns:
            dict: Statistiques
        """
        from employee.models import ZY00

        if entreprise is None:
            entreprise = cls.get_entreprise()

        if entreprise is None:
            return {
                'entreprise_existe': False,
                'effectif_total': 0,
                'effectif_salaries': 0,
                'effectif_stagiaires': 0,
                'effectif_prestataires': 0,
                'convention_en_vigueur': None,
            }

        # Calculer les effectifs par type
        employes = ZY00.objects.filter(entreprise=entreprise, etat='actif')

        return {
            'entreprise_existe': True,
            'nom': entreprise.nom,
            'code': entreprise.code,
            'effectif_total': employes.count(),
            'effectif_salaries': employes.filter(type_dossier='SAL').count(),
            'effectif_stagiaires': employes.filter(type_dossier='STA').count(),
            'effectif_prestataires': employes.filter(type_dossier='PRE').count(),
            'convention_en_vigueur': (
                entreprise.configuration_conventionnelle.nom
                if entreprise.configuration_conventionnelle
                else None
            ),
            'date_creation': entreprise.date_creation,
            'actif': entreprise.actif,
        }

    @classmethod
    def to_dict(cls, entreprise):
        """
        Convertit une entreprise en dictionnaire.

        Args:
            entreprise: Instance Entreprise

        Returns:
            dict: Données de l'entreprise
        """
        return {
            'id': entreprise.id,
            'uuid': str(entreprise.uuid),
            'code': entreprise.code,
            'nom': entreprise.nom,
            'raison_sociale': entreprise.raison_sociale or '',
            'sigle': entreprise.sigle or '',
            'adresse': entreprise.adresse,
            'ville': entreprise.ville,
            'pays': entreprise.pays,
            'telephone': entreprise.telephone or '',
            'email': entreprise.email or '',
            'site_web': entreprise.site_web or '',
            'rccm': entreprise.rccm or '',
            'numero_impot': entreprise.numero_impot or '',
            'numero_cnss': entreprise.numero_cnss or '',
            'configuration_conventionnelle_id': entreprise.configuration_conventionnelle_id,
            'date_creation': (
                entreprise.date_creation.strftime('%Y-%m-%d')
                if entreprise.date_creation else ''
            ),
            'date_application_convention': (
                entreprise.date_application_convention.strftime('%Y-%m-%d')
                if entreprise.date_application_convention else ''
            ),
            'actif': entreprise.actif,
            'description': entreprise.description or '',
            'effectif_total': entreprise.effectif_total,
        }

    @classmethod
    def get_conventions_disponibles(cls):
        """
        Récupère les conventions collectives disponibles.

        Returns:
            QuerySet: Conventions actives
        """
        from absence.models import ConfigurationConventionnelle
        return ConfigurationConventionnelle.objects.filter(actif=True).order_by('nom')
