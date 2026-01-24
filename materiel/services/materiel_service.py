# materiel/services/materiel_service.py
"""
Service pour la gestion du matériel.
"""
from decimal import Decimal
from typing import Optional, List
from django.db import transaction
from django.db.models import QuerySet, Sum, Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError


class MaterielService:
    """Service pour les opérations sur le matériel."""

    # ==========================================================================
    # CRÉATION ET MODIFICATION
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def creer_materiel(
        code_interne: str,
        categorie,
        designation: str,
        date_acquisition,
        prix_acquisition: Decimal,
        created_by=None,
        **kwargs
    ):
        """
        Crée un nouveau matériel.

        Args:
            code_interne: Code unique du matériel
            categorie: Instance MTCA
            designation: Description du matériel
            date_acquisition: Date d'acquisition
            prix_acquisition: Prix d'achat HT
            created_by: Employé créateur
            **kwargs: Autres champs optionnels

        Returns:
            Instance MTMT créée
        """
        from materiel.models import MTMT

        if MTMT.objects.filter(CODE_INTERNE=code_interne).exists():
            raise ValidationError(f"Un matériel avec le code '{code_interne}' existe déjà")

        materiel = MTMT.objects.create(
            CODE_INTERNE=code_interne.upper(),
            CATEGORIE=categorie,
            DESIGNATION=designation,
            DATE_ACQUISITION=date_acquisition,
            PRIX_ACQUISITION=prix_acquisition,
            CREATED_BY=created_by,
            STATUT='DISPONIBLE',
            ETAT='NEUF',
            **kwargs
        )

        # Créer le mouvement d'entrée
        from materiel.models import MTMV
        MTMV.objects.create(
            MATERIEL=materiel,
            TYPE_MOUVEMENT='ENTREE',
            DATE_MOUVEMENT=date_acquisition,
            MOTIF=f"Entrée en stock - Acquisition",
            EFFECTUE_PAR=created_by
        )

        return materiel

    @staticmethod
    def modifier_materiel(materiel, **kwargs):
        """
        Modifie un matériel existant.

        Args:
            materiel: Instance MTMT à modifier
            **kwargs: Champs à modifier

        Returns:
            Matériel modifié
        """
        champs_modifiables = [
            'DESIGNATION', 'MARQUE', 'MODELE', 'NUMERO_SERIE',
            'CARACTERISTIQUES', 'LOCALISATION', 'ETAT', 'NOTES',
            'DATE_FIN_GARANTIE', 'CONDITIONS_GARANTIE', 'PHOTO', 'DOCUMENT'
        ]

        for champ, valeur in kwargs.items():
            if champ in champs_modifiables:
                setattr(materiel, champ, valeur)

        materiel.save()
        return materiel

    # ==========================================================================
    # AFFECTATIONS
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def affecter_materiel(
        materiel,
        employe,
        date_debut,
        affecte_par,
        type_affectation: str = 'AFFECTATION',
        date_retour_prevue=None,
        motif: Optional[str] = None
    ):
        """
        Affecte un matériel à un employé.

        Args:
            materiel: Instance MTMT
            employe: Instance ZY00
            date_debut: Date de début d'affectation
            affecte_par: Employé effectuant l'affectation
            type_affectation: Type (AFFECTATION, PRET, MISE_A_DISPOSITION)
            date_retour_prevue: Date de retour prévue (pour les prêts)
            motif: Motif de l'affectation

        Returns:
            Instance MTAF créée
        """
        from materiel.models import MTAF

        if materiel.STATUT not in ['DISPONIBLE', 'EN_MAINTENANCE']:
            raise ValidationError(
                f"Le matériel n'est pas disponible (statut actuel: {materiel.get_STATUT_display()})"
            )

        # Clôturer l'affectation précédente si existante
        MTAF.objects.filter(
            MATERIEL=materiel,
            ACTIF=True,
            DATE_FIN__isnull=True
        ).update(
            ACTIF=False,
            DATE_FIN=date_debut
        )

        # Créer la nouvelle affectation
        affectation = MTAF.objects.create(
            MATERIEL=materiel,
            EMPLOYE=employe,
            TYPE_AFFECTATION=type_affectation,
            DATE_DEBUT=date_debut,
            DATE_RETOUR_PREVUE=date_retour_prevue,
            MOTIF=motif,
            ETAT_SORTIE=materiel.ETAT,
            AFFECTE_PAR=affecte_par,
            ACTIF=True
        )

        # Mettre à jour le matériel
        materiel.AFFECTE_A = employe
        materiel.DATE_AFFECTATION = date_debut
        materiel.STATUT = 'EN_PRET' if type_affectation == 'PRET' else 'AFFECTE'
        materiel.save()

        return affectation

    @staticmethod
    @transaction.atomic
    def retourner_materiel(
        affectation,
        date_retour,
        retour_par,
        etat_retour: str,
        commentaire: Optional[str] = None
    ):
        """
        Enregistre le retour d'un matériel.

        Args:
            affectation: Instance MTAF
            date_retour: Date de retour
            retour_par: Employé enregistrant le retour
            etat_retour: État du matériel au retour
            commentaire: Commentaire sur le retour

        Returns:
            Affectation mise à jour
        """
        if not affectation.ACTIF:
            raise ValidationError("Cette affectation n'est plus active")

        affectation.DATE_FIN = date_retour
        affectation.ETAT_RETOUR = etat_retour
        affectation.COMMENTAIRE_RETOUR = commentaire
        affectation.RETOUR_PAR = retour_par
        affectation.ACTIF = False
        affectation.save()

        # Mettre à jour le matériel
        materiel = affectation.MATERIEL
        materiel.AFFECTE_A = None
        materiel.DATE_AFFECTATION = None
        materiel.STATUT = 'DISPONIBLE'
        materiel.ETAT = etat_retour
        materiel.save()

        return affectation

    # ==========================================================================
    # MOUVEMENTS
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def creer_mouvement(
        materiel,
        type_mouvement: str,
        date_mouvement,
        motif: str,
        effectue_par,
        **kwargs
    ):
        """
        Crée un mouvement de matériel.

        Args:
            materiel: Instance MTMT
            type_mouvement: Type de mouvement
            date_mouvement: Date du mouvement
            motif: Motif du mouvement
            effectue_par: Employé effectuant le mouvement
            **kwargs: Autres champs optionnels

        Returns:
            Instance MTMV créée
        """
        from materiel.models import MTMV

        mouvement = MTMV.objects.create(
            MATERIEL=materiel,
            TYPE_MOUVEMENT=type_mouvement,
            DATE_MOUVEMENT=date_mouvement,
            MOTIF=motif,
            EFFECTUE_PAR=effectue_par,
            **kwargs
        )

        # Mettre à jour le statut du matériel selon le type de mouvement
        if type_mouvement == 'REFORME':
            materiel.STATUT = 'REFORME'
            materiel.ETAT = 'REFORME'
        elif type_mouvement == 'PERTE':
            materiel.STATUT = 'PERDU'
        elif type_mouvement == 'SORTIE':
            materiel.STATUT = 'REFORME'

        materiel.save()
        return mouvement

    @staticmethod
    @transaction.atomic
    def reformer_materiel(
        materiel,
        date_reforme,
        motif: str,
        effectue_par,
        valeur_sortie: Optional[Decimal] = None
    ):
        """
        Réforme un matériel (sortie définitive).

        Args:
            materiel: Instance MTMT
            date_reforme: Date de réforme
            motif: Motif de la réforme
            effectue_par: Employé effectuant la réforme
            valeur_sortie: Valeur résiduelle à la sortie

        Returns:
            Instance MTMV créée
        """
        # Clôturer l'affectation en cours si existante
        from materiel.models import MTAF
        MTAF.objects.filter(
            MATERIEL=materiel,
            ACTIF=True,
            DATE_FIN__isnull=True
        ).update(
            ACTIF=False,
            DATE_FIN=date_reforme,
            COMMENTAIRE_RETOUR="Réforme du matériel"
        )

        # Mettre à jour le matériel
        materiel.AFFECTE_A = None
        materiel.DATE_AFFECTATION = None

        return MaterielService.creer_mouvement(
            materiel=materiel,
            type_mouvement='REFORME',
            date_mouvement=date_reforme,
            motif=motif,
            effectue_par=effectue_par,
            VALEUR_SORTIE=valeur_sortie or materiel.valeur_residuelle
        )

    # ==========================================================================
    # MAINTENANCE
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def planifier_maintenance(
        materiel,
        type_maintenance: str,
        description: str,
        date_planifiee,
        demande_par,
        prestataire=None,
        intervenant_interne=None
    ):
        """
        Planifie une maintenance pour un matériel.

        Args:
            materiel: Instance MTMT
            type_maintenance: Type de maintenance
            description: Description de l'intervention
            date_planifiee: Date planifiée
            demande_par: Employé demandant la maintenance
            prestataire: Fournisseur prestataire (optionnel)
            intervenant_interne: Employé intervenant (optionnel)

        Returns:
            Instance MTMA créée
        """
        from materiel.models import MTMA

        maintenance = MTMA.objects.create(
            MATERIEL=materiel,
            TYPE_MAINTENANCE=type_maintenance,
            DESCRIPTION=description,
            DATE_PLANIFIEE=date_planifiee,
            PRESTATAIRE=prestataire,
            INTERVENANT_INTERNE=intervenant_interne,
            DEMANDE_PAR=demande_par,
            STATUT='PLANIFIE'
        )

        return maintenance

    @staticmethod
    @transaction.atomic
    def demarrer_maintenance(maintenance, date_debut=None):
        """Démarre une maintenance."""
        if maintenance.STATUT != 'PLANIFIE':
            raise ValidationError("Cette maintenance ne peut pas être démarrée")

        maintenance.STATUT = 'EN_COURS'
        maintenance.DATE_DEBUT = date_debut or timezone.now().date()
        maintenance.save()

        # Mettre le matériel en maintenance
        materiel = maintenance.MATERIEL

        # Clôturer l'affectation temporairement si nécessaire
        if materiel.STATUT == 'AFFECTE':
            materiel.STATUT = 'EN_MAINTENANCE'
            materiel.save()

        return maintenance

    @staticmethod
    @transaction.atomic
    def terminer_maintenance(
        maintenance,
        date_fin,
        resultat: str,
        etat_apres: str,
        cout_pieces: Decimal = Decimal('0'),
        cout_main_oeuvre: Decimal = Decimal('0'),
        prochaine_maintenance=None
    ):
        """
        Termine une maintenance.

        Args:
            maintenance: Instance MTMA
            date_fin: Date de fin
            resultat: Observations/résultat
            etat_apres: État du matériel après intervention
            cout_pieces: Coût des pièces
            cout_main_oeuvre: Coût main d'œuvre
            prochaine_maintenance: Date de prochaine maintenance

        Returns:
            Maintenance mise à jour
        """
        if maintenance.STATUT not in ['PLANIFIE', 'EN_COURS']:
            raise ValidationError("Cette maintenance ne peut pas être terminée")

        maintenance.STATUT = 'TERMINE'
        maintenance.DATE_FIN = date_fin
        maintenance.RESULTAT = resultat
        maintenance.ETAT_APRES = etat_apres
        maintenance.COUT_PIECES = cout_pieces
        maintenance.COUT_MAIN_OEUVRE = cout_main_oeuvre
        maintenance.PROCHAINE_MAINTENANCE = prochaine_maintenance

        if not maintenance.DATE_DEBUT:
            maintenance.DATE_DEBUT = date_fin

        maintenance.save()

        # Mettre à jour le matériel
        materiel = maintenance.MATERIEL
        materiel.ETAT = etat_apres

        # Si le matériel était affecté, remettre le statut AFFECTE
        if materiel.AFFECTE_A:
            materiel.STATUT = 'AFFECTE'
        else:
            materiel.STATUT = 'DISPONIBLE'

        materiel.save()

        return maintenance

    # ==========================================================================
    # REQUÊTES
    # ==========================================================================

    @staticmethod
    def get_materiels(
        categorie=None,
        statut: Optional[str] = None,
        etat: Optional[str] = None,
        employe=None
    ) -> QuerySet:
        """Récupère les matériels avec filtres optionnels."""
        from materiel.models import MTMT

        qs = MTMT.objects.select_related('CATEGORIE', 'FOURNISSEUR', 'AFFECTE_A')

        if categorie:
            qs = qs.filter(CATEGORIE=categorie)
        if statut:
            qs = qs.filter(STATUT=statut)
        if etat:
            qs = qs.filter(ETAT=etat)
        if employe:
            qs = qs.filter(AFFECTE_A=employe)

        return qs

    @staticmethod
    def get_materiels_employe(employe) -> QuerySet:
        """Récupère les matériels affectés à un employé."""
        from materiel.models import MTMT
        return MTMT.objects.filter(
            AFFECTE_A=employe
        ).select_related('CATEGORIE')

    @staticmethod
    def get_materiels_disponibles(categorie=None) -> QuerySet:
        """Récupère les matériels disponibles."""
        from materiel.models import MTMT

        qs = MTMT.objects.filter(STATUT='DISPONIBLE')
        if categorie:
            qs = qs.filter(CATEGORIE=categorie)

        return qs.select_related('CATEGORIE')

    @staticmethod
    def get_materiels_a_renouveler(mois_avant_fin: int = 6) -> QuerySet:
        """Récupère les matériels proches de fin d'amortissement."""
        from materiel.models import MTMT
        from datetime import timedelta

        date_limite = timezone.now().date() + timedelta(days=mois_avant_fin * 30)

        return MTMT.objects.exclude(
            STATUT='REFORME'
        ).filter(
            DATE_ACQUISITION__lte=timezone.now().date() - timedelta(days=30 * 30)
        ).select_related('CATEGORIE', 'AFFECTE_A')

    @staticmethod
    def get_maintenances_planifiees(jours_a_venir: int = 30) -> QuerySet:
        """Récupère les maintenances planifiées dans les prochains jours."""
        from materiel.models import MTMA
        from datetime import timedelta

        date_limite = timezone.now().date() + timedelta(days=jours_a_venir)

        return MTMA.objects.filter(
            STATUT='PLANIFIE',
            DATE_PLANIFIEE__lte=date_limite
        ).select_related('MATERIEL', 'PRESTATAIRE')

    @staticmethod
    def get_affectations_en_retard() -> QuerySet:
        """Récupère les prêts en retard de retour."""
        from materiel.models import MTAF

        return MTAF.objects.filter(
            ACTIF=True,
            TYPE_AFFECTATION='PRET',
            DATE_RETOUR_PREVUE__lt=timezone.now().date()
        ).select_related('MATERIEL', 'EMPLOYE')

    @staticmethod
    def get_historique_materiel(materiel) -> dict:
        """Récupère l'historique complet d'un matériel."""
        return {
            'affectations': materiel.affectations.select_related(
                'EMPLOYE', 'AFFECTE_PAR'
            ).order_by('-DATE_DEBUT'),
            'mouvements': materiel.mouvements.select_related(
                'EFFECTUE_PAR'
            ).order_by('-DATE_MOUVEMENT'),
            'maintenances': materiel.maintenances.select_related(
                'PRESTATAIRE', 'INTERVENANT_INTERNE'
            ).order_by('-DATE_PLANIFIEE'),
        }

    @staticmethod
    def rechercher_materiel(terme: str) -> QuerySet:
        """Recherche de matériel par code, désignation, numéro de série."""
        from materiel.models import MTMT

        return MTMT.objects.filter(
            Q(CODE_INTERNE__icontains=terme) |
            Q(DESIGNATION__icontains=terme) |
            Q(NUMERO_SERIE__icontains=terme) |
            Q(MARQUE__icontains=terme) |
            Q(MODELE__icontains=terme)
        ).select_related('CATEGORIE', 'AFFECTE_A')
