# frais/services/avance_service.py
"""
Service pour la gestion des avances sur frais.
"""
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.db.models import QuerySet, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError


class AvanceService:
    """Service pour les opérations sur les avances."""

    # ==========================================================================
    # CRÉATION ET MODIFICATION
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def creer_avance(
        employe,
        montant_demande: Decimal,
        motif: str,
        date_mission_debut=None,
        date_mission_fin=None,
        created_by=None
    ):
        """
        Crée une demande d'avance sur frais.

        Args:
            employe: Instance ZY00 de l'employé
            montant_demande: Montant demandé
            motif: Justification de la demande
            date_mission_debut: Date début mission (optionnel)
            date_mission_fin: Date fin mission (optionnel)
            created_by: Employé créateur (optionnel)

        Returns:
            Instance NFAV créée
        """
        from frais.models import NFAV

        if montant_demande <= 0:
            raise ValidationError("Le montant demandé doit être positif")

        if date_mission_debut and date_mission_fin:
            if date_mission_fin < date_mission_debut:
                raise ValidationError(
                    "La date de fin de mission doit être postérieure à la date de début"
                )

        # Vérifier s'il y a des avances non régularisées
        avances_en_cours = NFAV.objects.filter(
            EMPLOYE=employe,
            STATUT__in=['DEMANDE', 'APPROUVE', 'VERSE']
        )

        if avances_en_cours.exists():
            total_en_cours = avances_en_cours.aggregate(
                total=Sum('MONTANT_DEMANDE')
            )['total'] or Decimal('0')

            # Avertissement (pas bloquant, juste informatif)
            # On pourrait ajouter une logique de plafond ici

        avance = NFAV.objects.create(
            EMPLOYE=employe,
            MONTANT_DEMANDE=montant_demande,
            MOTIF=motif,
            DATE_MISSION_DEBUT=date_mission_debut,
            DATE_MISSION_FIN=date_mission_fin,
            CREATED_BY=created_by or employe,
            STATUT='DEMANDE'
        )

        return avance

    @staticmethod
    def modifier_avance(avance, **kwargs):
        """
        Modifie une demande d'avance.

        Args:
            avance: Instance NFAV à modifier
            **kwargs: Champs à modifier

        Returns:
            Avance modifiée
        """
        if not avance.peut_etre_modifie():
            raise ValidationError(
                "L'avance ne peut plus être modifiée dans ce statut"
            )

        champs_modifiables = [
            'MONTANT_DEMANDE', 'MOTIF',
            'DATE_MISSION_DEBUT', 'DATE_MISSION_FIN'
        ]

        for champ, valeur in kwargs.items():
            if champ in champs_modifiables:
                setattr(avance, champ, valeur)

        avance.save()
        return avance

    # ==========================================================================
    # WORKFLOW
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def approuver_avance(
        avance,
        approbateur,
        montant_approuve: Optional[Decimal] = None,
        commentaire: Optional[str] = None
    ):
        """
        Approuve une demande d'avance.

        Args:
            avance: Instance NFAV
            approbateur: Employé approbateur
            montant_approuve: Montant approuvé (si différent du demandé)
            commentaire: Commentaire (optionnel)

        Returns:
            Avance approuvée
        """
        if not avance.peut_etre_approuve():
            raise ValidationError(
                "L'avance ne peut pas être approuvée dans ce statut"
            )

        avance.STATUT = 'APPROUVE'
        avance.APPROBATEUR = approbateur
        avance.DATE_APPROBATION = timezone.now()
        avance.MONTANT_APPROUVE = montant_approuve or avance.MONTANT_DEMANDE
        avance.COMMENTAIRE_APPROBATION = commentaire
        avance.save()

        return avance

    @staticmethod
    @transaction.atomic
    def rejeter_avance(avance, approbateur, commentaire: str):
        """
        Rejette une demande d'avance.

        Args:
            avance: Instance NFAV
            approbateur: Employé rejetant
            commentaire: Motif du rejet (obligatoire)

        Returns:
            Avance rejetée
        """
        if not avance.peut_etre_approuve():
            raise ValidationError(
                "L'avance ne peut pas être rejetée dans ce statut"
            )

        if not commentaire:
            raise ValidationError("Un motif de rejet est obligatoire")

        avance.STATUT = 'ANNULE'
        avance.APPROBATEUR = approbateur
        avance.DATE_APPROBATION = timezone.now()
        avance.COMMENTAIRE_APPROBATION = commentaire
        avance.save()

        return avance

    @staticmethod
    @transaction.atomic
    def marquer_verse(
        avance,
        date_versement,
        reference_versement: Optional[str] = None
    ):
        """
        Marque une avance comme versée.

        Args:
            avance: Instance NFAV
            date_versement: Date du versement
            reference_versement: Référence du virement

        Returns:
            Avance mise à jour
        """
        if not avance.peut_etre_verse():
            raise ValidationError(
                "L'avance doit être approuvée avant d'être versée"
            )

        avance.STATUT = 'VERSE'
        avance.DATE_VERSEMENT = date_versement
        avance.REFERENCE_VERSEMENT = reference_versement
        avance.save()

        return avance

    @staticmethod
    @transaction.atomic
    def regulariser_avance(
        avance,
        note_frais,
        montant_regularise: Optional[Decimal] = None
    ):
        """
        Régularise une avance avec une note de frais.

        Args:
            avance: Instance NFAV
            note_frais: Instance NFNF de régularisation
            montant_regularise: Montant utilisé (défaut: montant approuvé)

        Returns:
            Avance régularisée
        """
        if avance.STATUT != 'VERSE':
            raise ValidationError(
                "Seules les avances versées peuvent être régularisées"
            )

        if note_frais.EMPLOYE != avance.EMPLOYE:
            raise ValidationError(
                "La note de frais doit appartenir au même employé"
            )

        montant = montant_regularise or avance.MONTANT_APPROUVE or avance.MONTANT_DEMANDE

        avance.STATUT = 'REGULARISE'
        avance.NOTE_FRAIS = note_frais
        avance.MONTANT_REGULARISE = montant
        avance.DATE_REGULARISATION = timezone.now().date()
        avance.save()

        return avance

    @staticmethod
    def annuler_avance(avance):
        """Annule une demande d'avance."""
        if avance.STATUT in ['VERSE', 'REGULARISE']:
            raise ValidationError(
                "Une avance versée ou régularisée ne peut pas être annulée"
            )

        avance.STATUT = 'ANNULE'
        avance.save()
        return avance

    # ==========================================================================
    # REQUÊTES
    # ==========================================================================

    @staticmethod
    def get_avances_employe(employe, statut: Optional[str] = None) -> QuerySet:
        """
        Récupère les avances d'un employé.

        Args:
            employe: Instance ZY00
            statut: Filtrer par statut (optionnel)

        Returns:
            QuerySet de NFAV
        """
        from frais.models import NFAV

        qs = NFAV.objects.filter(EMPLOYE=employe)
        if statut:
            qs = qs.filter(STATUT=statut)
        return qs.select_related('EMPLOYE', 'APPROBATEUR', 'NOTE_FRAIS')

    @staticmethod
    def get_avances_a_approuver() -> QuerySet:
        """Récupère les avances en attente d'approbation."""
        from frais.models import NFAV

        return NFAV.objects.filter(
            STATUT='DEMANDE'
        ).select_related('EMPLOYE', 'CREATED_BY')

    @staticmethod
    def get_avances_a_verser() -> QuerySet:
        """Récupère les avances approuvées en attente de versement."""
        from frais.models import NFAV

        return NFAV.objects.filter(
            STATUT='APPROUVE'
        ).select_related('EMPLOYE', 'APPROBATEUR')

    @staticmethod
    def get_avances_a_regulariser(employe=None) -> QuerySet:
        """
        Récupère les avances versées en attente de régularisation.

        Args:
            employe: Filtrer par employé (optionnel)
        """
        from frais.models import NFAV

        qs = NFAV.objects.filter(STATUT='VERSE')
        if employe:
            qs = qs.filter(EMPLOYE=employe)
        return qs.select_related('EMPLOYE')

    @staticmethod
    def get_solde_avances_employe(employe) -> Decimal:
        """
        Calcule le solde total des avances non régularisées d'un employé.

        Returns:
            Montant total des avances en cours
        """
        from frais.models import NFAV

        avances = NFAV.objects.filter(
            EMPLOYE=employe,
            STATUT__in=['APPROUVE', 'VERSE']
        )

        total = avances.aggregate(
            total=Sum('MONTANT_APPROUVE')
        )['total'] or Decimal('0')

        return total

    @staticmethod
    def get_detail_avance(avance_id: int):
        """Récupère une avance avec tous ses détails."""
        from frais.models import NFAV

        try:
            return NFAV.objects.select_related(
                'EMPLOYE', 'APPROBATEUR', 'CREATED_BY', 'NOTE_FRAIS'
            ).get(pk=avance_id)
        except NFAV.DoesNotExist:
            return None
