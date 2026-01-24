# frais/services/note_frais_service.py
"""
Service pour la gestion des notes de frais.
"""
from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.db.models import QuerySet, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError


class NoteFraisService:
    """Service pour les opérations sur les notes de frais."""

    # ==========================================================================
    # CRÉATION ET MODIFICATION
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def creer_note_frais(
        employe,
        periode_debut,
        periode_fin,
        objet: Optional[str] = None,
        created_by=None
    ):
        """
        Crée une nouvelle note de frais.

        Args:
            employe: Instance ZY00 de l'employé
            periode_debut: Date de début de période
            periode_fin: Date de fin de période
            objet: Description/objet de la mission (optionnel)
            created_by: Employé créateur (optionnel)

        Returns:
            Instance NFNF créée
        """
        from frais.models import NFNF

        if periode_fin < periode_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début")

        note = NFNF.objects.create(
            EMPLOYE=employe,
            PERIODE_DEBUT=periode_debut,
            PERIODE_FIN=periode_fin,
            OBJET=objet,
            CREATED_BY=created_by or employe,
            STATUT='BROUILLON'
        )

        return note

    @staticmethod
    def modifier_note_frais(note, **kwargs) -> 'NFNF':
        """
        Modifie une note de frais existante.

        Args:
            note: Instance NFNF à modifier
            **kwargs: Champs à modifier

        Returns:
            Note modifiée

        Raises:
            ValidationError: Si la note ne peut pas être modifiée
        """
        if not note.peut_etre_modifie():
            raise ValidationError(
                f"La note de frais ne peut pas être modifiée dans le statut '{note.get_STATUT_display()}'"
            )

        champs_modifiables = ['PERIODE_DEBUT', 'PERIODE_FIN', 'OBJET']

        for champ, valeur in kwargs.items():
            if champ in champs_modifiables:
                setattr(note, champ, valeur)

        # Valider les dates
        if note.PERIODE_FIN < note.PERIODE_DEBUT:
            raise ValidationError("La date de fin doit être postérieure à la date de début")

        note.save()
        return note

    # ==========================================================================
    # LIGNES DE FRAIS
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def ajouter_ligne(
        note,
        categorie,
        date_depense,
        description: str,
        montant: Decimal,
        justificatif=None,
        numero_facture: Optional[str] = None,
        devise: str = 'XOF',
        taux_change: Decimal = Decimal('1')
    ):
        """
        Ajoute une ligne de frais à une note.

        Args:
            note: Instance NFNF
            categorie: Instance NFCA
            date_depense: Date de la dépense
            description: Description de la dépense
            montant: Montant de la dépense
            justificatif: Fichier justificatif (optionnel)
            numero_facture: Numéro de facture/reçu (optionnel)
            devise: Code devise (défaut XOF)
            taux_change: Taux de change vers XOF (défaut 1)

        Returns:
            Instance NFLF créée
        """
        from frais.models import NFLF

        if not note.peut_etre_modifie():
            raise ValidationError("La note de frais ne peut pas être modifiée")

        # Vérifier que la date est dans la période
        if not (note.PERIODE_DEBUT <= date_depense <= note.PERIODE_FIN):
            raise ValidationError(
                f"La date de dépense doit être comprise entre {note.PERIODE_DEBUT} et {note.PERIODE_FIN}"
            )

        # Vérifier le justificatif obligatoire
        if categorie.JUSTIFICATIF_OBLIGATOIRE and not justificatif:
            raise ValidationError(
                f"Un justificatif est obligatoire pour la catégorie '{categorie.LIBELLE}'"
            )

        # Vérifier le plafond de la catégorie
        if categorie.PLAFOND_DEFAUT and montant > categorie.PLAFOND_DEFAUT:
            raise ValidationError(
                f"Le montant dépasse le plafond de {categorie.PLAFOND_DEFAUT} pour cette catégorie"
            )

        ligne = NFLF.objects.create(
            NOTE_FRAIS=note,
            CATEGORIE=categorie,
            DATE_DEPENSE=date_depense,
            DESCRIPTION=description,
            MONTANT=montant,
            JUSTIFICATIF=justificatif,
            NUMERO_FACTURE=numero_facture,
            DEVISE=devise,
            TAUX_CHANGE=taux_change
        )

        return ligne

    @staticmethod
    def modifier_ligne(ligne, **kwargs):
        """
        Modifie une ligne de frais.

        Args:
            ligne: Instance NFLF à modifier
            **kwargs: Champs à modifier

        Returns:
            Ligne modifiée
        """
        if not ligne.NOTE_FRAIS.peut_etre_modifie():
            raise ValidationError("La note de frais ne peut pas être modifiée")

        if ligne.STATUT_LIGNE != 'EN_ATTENTE':
            raise ValidationError("Seules les lignes en attente peuvent être modifiées")

        champs_modifiables = [
            'CATEGORIE', 'DATE_DEPENSE', 'DESCRIPTION', 'MONTANT',
            'JUSTIFICATIF', 'NUMERO_FACTURE', 'DEVISE', 'TAUX_CHANGE'
        ]

        for champ, valeur in kwargs.items():
            if champ in champs_modifiables:
                setattr(ligne, champ, valeur)

        ligne.save()
        return ligne

    @staticmethod
    def supprimer_ligne(ligne) -> bool:
        """
        Supprime une ligne de frais.

        Args:
            ligne: Instance NFLF à supprimer

        Returns:
            True si suppression réussie
        """
        if not ligne.NOTE_FRAIS.peut_etre_modifie():
            raise ValidationError("La note de frais ne peut pas être modifiée")

        note = ligne.NOTE_FRAIS
        ligne.delete()
        note.calculer_totaux()
        return True

    # ==========================================================================
    # WORKFLOW
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def soumettre_note(note) -> 'NFNF':
        """
        Soumet une note de frais pour validation.

        Args:
            note: Instance NFNF à soumettre

        Returns:
            Note mise à jour
        """
        if not note.peut_etre_soumis():
            raise ValidationError(
                "La note ne peut pas être soumise. Vérifiez qu'elle contient des lignes."
            )

        note.STATUT = 'SOUMIS'
        note.DATE_SOUMISSION = timezone.now()
        note.save()

        return note

    @staticmethod
    @transaction.atomic
    def valider_note(note, valideur, commentaire: Optional[str] = None) -> 'NFNF':
        """
        Valide une note de frais.

        Args:
            note: Instance NFNF à valider
            valideur: Employé valideur
            commentaire: Commentaire de validation (optionnel)

        Returns:
            Note validée
        """
        if not note.peut_etre_valide():
            raise ValidationError(
                f"La note ne peut pas être validée dans le statut '{note.get_STATUT_display()}'"
            )

        # Valider toutes les lignes en attente
        note.lignes.filter(STATUT_LIGNE='EN_ATTENTE').update(STATUT_LIGNE='VALIDE')

        note.STATUT = 'VALIDE'
        note.VALIDEUR = valideur
        note.DATE_VALIDATION = timezone.now()
        note.COMMENTAIRE_VALIDATION = commentaire
        note.calculer_totaux()
        note.save()

        return note

    @staticmethod
    @transaction.atomic
    def rejeter_note(note, valideur, commentaire: str) -> 'NFNF':
        """
        Rejette une note de frais.

        Args:
            note: Instance NFNF à rejeter
            valideur: Employé rejetant
            commentaire: Motif du rejet (obligatoire)

        Returns:
            Note rejetée
        """
        if not note.peut_etre_valide():
            raise ValidationError(
                f"La note ne peut pas être rejetée dans le statut '{note.get_STATUT_display()}'"
            )

        if not commentaire:
            raise ValidationError("Un motif de rejet est obligatoire")

        note.STATUT = 'REJETE'
        note.VALIDEUR = valideur
        note.DATE_VALIDATION = timezone.now()
        note.COMMENTAIRE_VALIDATION = commentaire
        note.save()

        return note

    @staticmethod
    @transaction.atomic
    def valider_ligne(ligne, valideur) -> 'NFLF':
        """Valide une ligne de frais individuellement."""
        ligne.STATUT_LIGNE = 'VALIDE'
        ligne.save()
        ligne.NOTE_FRAIS.calculer_totaux()
        return ligne

    @staticmethod
    @transaction.atomic
    def rejeter_ligne(ligne, valideur, motif: str) -> 'NFLF':
        """Rejette une ligne de frais individuellement."""
        if not motif:
            raise ValidationError("Un motif de rejet est obligatoire")

        ligne.STATUT_LIGNE = 'REJETE'
        ligne.COMMENTAIRE_REJET = motif
        ligne.save()
        ligne.NOTE_FRAIS.calculer_totaux()
        return ligne

    @staticmethod
    @transaction.atomic
    def marquer_rembourse(
        note,
        date_remboursement,
        reference_paiement: Optional[str] = None
    ) -> 'NFNF':
        """
        Marque une note comme remboursée.

        Args:
            note: Instance NFNF
            date_remboursement: Date du remboursement
            reference_paiement: Référence du virement/paiement

        Returns:
            Note mise à jour
        """
        if note.STATUT != 'VALIDE':
            raise ValidationError("Seules les notes validées peuvent être remboursées")

        note.STATUT = 'REMBOURSE'
        note.DATE_REMBOURSEMENT = date_remboursement
        note.REFERENCE_PAIEMENT = reference_paiement
        note.MONTANT_REMBOURSE = note.MONTANT_VALIDE
        note.save()

        return note

    @staticmethod
    def annuler_note(note) -> 'NFNF':
        """Annule une note de frais."""
        if note.STATUT in ['REMBOURSE', 'ANNULE']:
            raise ValidationError("Cette note ne peut pas être annulée")

        note.STATUT = 'ANNULE'
        note.save()
        return note

    # ==========================================================================
    # REQUÊTES
    # ==========================================================================

    @staticmethod
    def get_notes_employe(employe, statut: Optional[str] = None) -> QuerySet:
        """
        Récupère les notes de frais d'un employé.

        Args:
            employe: Instance ZY00
            statut: Filtrer par statut (optionnel)

        Returns:
            QuerySet de NFNF
        """
        from frais.models import NFNF

        qs = NFNF.objects.filter(EMPLOYE=employe)
        if statut:
            qs = qs.filter(STATUT=statut)
        return qs.select_related('EMPLOYE', 'VALIDEUR')

    @staticmethod
    def get_notes_a_valider(valideur=None) -> QuerySet:
        """
        Récupère les notes de frais en attente de validation.

        Args:
            valideur: Si fourni, filtre par département du valideur (optionnel)

        Returns:
            QuerySet de NFNF
        """
        from frais.models import NFNF

        qs = NFNF.objects.filter(STATUT__in=['SOUMIS', 'EN_VALIDATION'])
        return qs.select_related('EMPLOYE', 'CREATED_BY').prefetch_related('lignes')

    @staticmethod
    def get_notes_a_rembourser() -> QuerySet:
        """Récupère les notes validées en attente de remboursement."""
        from frais.models import NFNF

        return NFNF.objects.filter(
            STATUT='VALIDE'
        ).select_related('EMPLOYE', 'VALIDEUR')

    @staticmethod
    def get_detail_note(note_id: int) -> Optional['NFNF']:
        """
        Récupère une note avec tous ses détails.

        Args:
            note_id: ID de la note

        Returns:
            Instance NFNF ou None
        """
        from frais.models import NFNF

        try:
            return NFNF.objects.select_related(
                'EMPLOYE', 'VALIDEUR', 'CREATED_BY'
            ).prefetch_related(
                'lignes__CATEGORIE', 'avances'
            ).get(pk=note_id)
        except NFNF.DoesNotExist:
            return None

    @staticmethod
    def get_notes_par_periode(
        date_debut,
        date_fin,
        employe=None,
        statut: Optional[str] = None
    ) -> QuerySet:
        """
        Récupère les notes de frais pour une période donnée.
        """
        from frais.models import NFNF

        qs = NFNF.objects.filter(
            PERIODE_DEBUT__lte=date_fin,
            PERIODE_FIN__gte=date_debut
        )

        if employe:
            qs = qs.filter(EMPLOYE=employe)
        if statut:
            qs = qs.filter(STATUT=statut)

        return qs.select_related('EMPLOYE')
