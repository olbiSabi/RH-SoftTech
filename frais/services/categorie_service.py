# frais/services/categorie_service.py
"""
Service pour la gestion des catégories de frais.
"""
from decimal import Decimal
from typing import Optional, List
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.core.exceptions import ValidationError


class CategorieService:
    """Service pour les opérations sur les catégories de frais."""

    # ==========================================================================
    # GESTION DES CATÉGORIES
    # ==========================================================================

    @staticmethod
    def creer_categorie(
        code: str,
        libelle: str,
        description: Optional[str] = None,
        justificatif_obligatoire: bool = True,
        plafond_defaut: Optional[Decimal] = None,
        icone: Optional[str] = None,
        ordre: int = 0
    ):
        """
        Crée une nouvelle catégorie de frais.

        Args:
            code: Code unique de la catégorie
            libelle: Libellé de la catégorie
            description: Description (optionnel)
            justificatif_obligatoire: Si un justificatif est requis
            plafond_defaut: Plafond par défaut (optionnel)
            icone: Classe CSS de l'icône (optionnel)
            ordre: Ordre d'affichage

        Returns:
            Instance NFCA créée
        """
        from frais.models import NFCA

        if NFCA.objects.filter(CODE=code).exists():
            raise ValidationError(f"Une catégorie avec le code '{code}' existe déjà")

        categorie = NFCA.objects.create(
            CODE=code.upper(),
            LIBELLE=libelle,
            DESCRIPTION=description,
            JUSTIFICATIF_OBLIGATOIRE=justificatif_obligatoire,
            PLAFOND_DEFAUT=plafond_defaut,
            ICONE=icone,
            ORDRE=ordre,
            STATUT=True
        )

        return categorie

    @staticmethod
    def modifier_categorie(categorie, **kwargs):
        """
        Modifie une catégorie existante.

        Args:
            categorie: Instance NFCA à modifier
            **kwargs: Champs à modifier

        Returns:
            Catégorie modifiée
        """
        champs_modifiables = [
            'LIBELLE', 'DESCRIPTION', 'JUSTIFICATIF_OBLIGATOIRE',
            'PLAFOND_DEFAUT', 'ICONE', 'ORDRE', 'STATUT'
        ]

        for champ, valeur in kwargs.items():
            if champ in champs_modifiables:
                setattr(categorie, champ, valeur)

        categorie.save()
        return categorie

    @staticmethod
    def desactiver_categorie(categorie) -> bool:
        """Désactive une catégorie (ne la supprime pas)."""
        categorie.STATUT = False
        categorie.save()
        return True

    @staticmethod
    def activer_categorie(categorie) -> bool:
        """Réactive une catégorie."""
        categorie.STATUT = True
        categorie.save()
        return True

    # ==========================================================================
    # GESTION DES PLAFONDS
    # ==========================================================================

    @staticmethod
    def creer_plafond(
        categorie,
        date_debut,
        montant_journalier: Optional[Decimal] = None,
        montant_mensuel: Optional[Decimal] = None,
        montant_par_depense: Optional[Decimal] = None,
        grade: Optional[str] = None,
        date_fin=None
    ):
        """
        Crée un plafond pour une catégorie.

        Args:
            categorie: Instance NFCA
            date_debut: Date de début de validité
            montant_journalier: Plafond journalier (optionnel)
            montant_mensuel: Plafond mensuel (optionnel)
            montant_par_depense: Plafond par dépense (optionnel)
            grade: Grade/catégorie employé concerné (optionnel)
            date_fin: Date de fin de validité (optionnel)

        Returns:
            Instance NFPL créée
        """
        from frais.models import NFPL

        # Au moins un montant doit être défini
        if not any([montant_journalier, montant_mensuel, montant_par_depense]):
            raise ValidationError("Au moins un type de plafond doit être défini")

        plafond = NFPL.objects.create(
            CATEGORIE=categorie,
            DATE_DEBUT=date_debut,
            DATE_FIN=date_fin,
            MONTANT_JOURNALIER=montant_journalier,
            MONTANT_MENSUEL=montant_mensuel,
            MONTANT_PAR_DEPENSE=montant_par_depense,
            GRADE=grade,
            STATUT=True
        )

        return plafond

    @staticmethod
    def get_plafond_applicable(categorie, employe=None, date=None):
        """
        Récupère le plafond applicable pour une catégorie.

        Args:
            categorie: Instance NFCA
            employe: Employé concerné (pour filtrer par grade)
            date: Date de référence (défaut: aujourd'hui)

        Returns:
            Instance NFPL ou None
        """
        from frais.models import NFPL

        if date is None:
            date = timezone.now().date()

        # Chercher un plafond spécifique au grade si employé fourni
        plafonds = NFPL.objects.filter(
            CATEGORIE=categorie,
            STATUT=True,
            DATE_DEBUT__lte=date
        ).filter(
            models.Q(DATE_FIN__isnull=True) | models.Q(DATE_FIN__gte=date)
        ).order_by('-DATE_DEBUT')

        # TODO: Si employe fourni, filtrer par grade de l'employé
        # Pour l'instant, retourner le premier plafond applicable

        return plafonds.first()

    # ==========================================================================
    # REQUÊTES
    # ==========================================================================

    @staticmethod
    def get_categories_actives() -> QuerySet:
        """Récupère toutes les catégories actives."""
        from frais.models import NFCA

        return NFCA.objects.filter(STATUT=True).order_by('ORDRE', 'LIBELLE')

    @staticmethod
    def get_toutes_categories() -> QuerySet:
        """Récupère toutes les catégories (actives et inactives)."""
        from frais.models import NFCA

        return NFCA.objects.all().order_by('ORDRE', 'LIBELLE')

    @staticmethod
    def get_categorie_par_code(code: str):
        """Récupère une catégorie par son code."""
        from frais.models import NFCA

        try:
            return NFCA.objects.get(CODE=code.upper())
        except NFCA.DoesNotExist:
            return None

    @staticmethod
    def get_plafonds_categorie(categorie) -> QuerySet:
        """Récupère tous les plafonds d'une catégorie."""
        from frais.models import NFPL

        return NFPL.objects.filter(
            CATEGORIE=categorie
        ).order_by('-DATE_DEBUT')

    @staticmethod
    def get_categories_avec_stats() -> List[dict]:
        """
        Récupère les catégories avec leurs statistiques d'utilisation.

        Returns:
            Liste de dictionnaires avec catégorie et stats
        """
        from frais.models import NFCA, NFLF
        from django.db.models import Count, Sum

        categories = NFCA.objects.annotate(
            nb_lignes=Count('lignes_frais'),
            montant_total=Sum('lignes_frais__MONTANT')
        ).order_by('ORDRE', 'LIBELLE')

        result = []
        for cat in categories:
            result.append({
                'categorie': cat,
                'nb_utilisations': cat.nb_lignes,
                'montant_total': cat.montant_total or Decimal('0')
            })

        return result

    # ==========================================================================
    # CATÉGORIES PAR DÉFAUT
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def creer_categories_defaut() -> List:
        """
        Crée les catégories de frais par défaut.

        Returns:
            Liste des catégories créées
        """
        categories_defaut = [
            {
                'code': 'TRANSPORT',
                'libelle': 'Transport',
                'description': 'Frais de transport (taxi, carburant, péage, etc.)',
                'icone': 'fa-car',
                'justificatif_obligatoire': True,
                'ordre': 1
            },
            {
                'code': 'REPAS',
                'libelle': 'Repas',
                'description': 'Frais de restauration',
                'icone': 'fa-utensils',
                'justificatif_obligatoire': True,
                'ordre': 2
            },
            {
                'code': 'HEBERGEMENT',
                'libelle': 'Hébergement',
                'description': 'Frais d\'hôtel et hébergement',
                'icone': 'fa-bed',
                'justificatif_obligatoire': True,
                'ordre': 3
            },
            {
                'code': 'TELEPHONE',
                'libelle': 'Téléphone',
                'description': 'Frais de communication téléphonique',
                'icone': 'fa-phone',
                'justificatif_obligatoire': False,
                'ordre': 4
            },
            {
                'code': 'FOURNITURES',
                'libelle': 'Fournitures',
                'description': 'Fournitures de bureau et matériel',
                'icone': 'fa-pencil-alt',
                'justificatif_obligatoire': True,
                'ordre': 5
            },
            {
                'code': 'MISSION',
                'libelle': 'Frais de mission',
                'description': 'Autres frais liés aux déplacements professionnels',
                'icone': 'fa-plane',
                'justificatif_obligatoire': True,
                'ordre': 6
            },
            {
                'code': 'DIVERS',
                'libelle': 'Divers',
                'description': 'Autres frais professionnels',
                'icone': 'fa-ellipsis-h',
                'justificatif_obligatoire': True,
                'ordre': 99
            },
        ]

        categories_creees = []
        for cat_data in categories_defaut:
            try:
                cat = CategorieService.creer_categorie(**cat_data)
                categories_creees.append(cat)
            except ValidationError:
                # Catégorie existe déjà, on ignore
                pass

        return categories_creees
