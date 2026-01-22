# absence/services/absence_service.py
"""
Service de gestion des absences.
"""
from decimal import Decimal
from datetime import timedelta
import logging

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class AbsenceService:
    """Service pour gérer les absences."""

    # Statuts des absences
    BROUILLON = 'BROUILLON'
    EN_ATTENTE_MANAGER = 'EN_ATTENTE_MANAGER'
    EN_ATTENTE_RH = 'EN_ATTENTE_RH'
    VALIDE = 'VALIDE'
    REJETE = 'REJETE'
    ANNULE = 'ANNULE'

    @staticmethod
    def calculer_nombre_jours(date_debut, date_fin, type_absence=None):
        """
        Calcule le nombre de jours d'une absence.

        Args:
            date_debut: Date de début
            date_fin: Date de fin
            type_absence: Type d'absence (optionnel)

        Returns:
            Decimal: Nombre de jours
        """
        from absence.models import JourFerie

        if date_debut > date_fin:
            return Decimal('0.00')

        jours = Decimal('0.00')
        current = date_debut

        while current <= date_fin:
            # Ignorer les weekends
            if current.weekday() < 5:  # Lundi=0 à Vendredi=4
                # Vérifier si c'est un jour férié
                est_ferie = JourFerie.objects.filter(
                    date=current,
                    actif=True
                ).exists()

                if not est_ferie:
                    jours += Decimal('1.00')

            current += timedelta(days=1)

        return jours

    @staticmethod
    def verifier_solde(employe, type_absence, nombre_jours, annee=None):
        """
        Vérifie si l'employé a un solde suffisant.

        Args:
            employe: Instance de l'employé
            type_absence: Type d'absence
            nombre_jours: Nombre de jours demandés
            annee: Année de référence (optionnel)

        Returns:
            dict: Résultat de la vérification
        """
        from absence.models import AcquisitionConges

        if annee is None:
            annee = timezone.now().year - 1  # Année N-1

        # Si le type ne décompte pas le solde, c'est OK
        if not type_absence.decompte_solde:
            return {
                'suffisant': True,
                'solde_disponible': None,
                'message': 'Ce type d\'absence ne décompte pas le solde'
            }

        try:
            acquisition = AcquisitionConges.objects.get(
                employe=employe,
                annee_reference=annee
            )
            solde = acquisition.jours_solde

            return {
                'suffisant': solde >= nombre_jours,
                'solde_disponible': str(solde),
                'jours_demandes': str(nombre_jours),
                'message': 'Solde suffisant' if solde >= nombre_jours else 'Solde insuffisant'
            }

        except AcquisitionConges.DoesNotExist:
            return {
                'suffisant': False,
                'solde_disponible': '0.00',
                'jours_demandes': str(nombre_jours),
                'message': 'Aucune acquisition trouvée pour cette année'
            }

    @staticmethod
    def soumettre_absence(absence, user):
        """
        Soumet une absence pour validation.

        Args:
            absence: Instance de l'absence
            user: Utilisateur effectuant la soumission

        Returns:
            dict: Résultat de la soumission
        """
        from absence.services.notification_service import NotificationService

        if absence.statut != AbsenceService.BROUILLON:
            return {
                'success': False,
                'error': 'Seule une absence en brouillon peut être soumise'
            }

        with transaction.atomic():
            absence.statut = AbsenceService.EN_ATTENTE_MANAGER
            absence.date_soumission = timezone.now()
            absence.save()

            # Créer notification pour le manager
            NotificationService.notifier_nouvelle_demande(absence)

        return {
            'success': True,
            'message': 'Absence soumise pour validation'
        }

    @staticmethod
    def valider_manager(absence, user, commentaire=''):
        """
        Validation par le manager.

        Args:
            absence: Instance de l'absence
            user: Manager effectuant la validation
            commentaire: Commentaire optionnel

        Returns:
            dict: Résultat de la validation
        """
        from absence.models import ValidationAbsence
        from absence.services.notification_service import NotificationService

        if absence.statut != AbsenceService.EN_ATTENTE_MANAGER:
            return {
                'success': False,
                'error': 'Cette absence n\'est pas en attente de validation manager'
            }

        with transaction.atomic():
            absence.statut = AbsenceService.EN_ATTENTE_RH
            absence.date_validation_manager = timezone.now()
            absence.valide_par_manager = user
            absence.commentaire_manager = commentaire
            absence.save()

            # Traçabilité
            ValidationAbsence.objects.create(
                absence=absence,
                etape='MANAGER',
                action='VALIDE',
                valide_par=user,
                commentaire=commentaire
            )

            # Notifications
            NotificationService.notifier_validation_manager(absence, 'VALIDE')

        return {
            'success': True,
            'message': 'Absence validée par le manager'
        }

    @staticmethod
    def rejeter_manager(absence, user, commentaire=''):
        """
        Rejet par le manager.

        Args:
            absence: Instance de l'absence
            user: Manager effectuant le rejet
            commentaire: Motif du rejet

        Returns:
            dict: Résultat du rejet
        """
        from absence.models import ValidationAbsence
        from absence.services.notification_service import NotificationService

        if absence.statut != AbsenceService.EN_ATTENTE_MANAGER:
            return {
                'success': False,
                'error': 'Cette absence n\'est pas en attente de validation manager'
            }

        with transaction.atomic():
            absence.statut = AbsenceService.REJETE
            absence.date_validation_manager = timezone.now()
            absence.valide_par_manager = user
            absence.commentaire_manager = commentaire
            absence.save()

            ValidationAbsence.objects.create(
                absence=absence,
                etape='MANAGER',
                action='REJETE',
                valide_par=user,
                commentaire=commentaire
            )

            NotificationService.notifier_validation_manager(absence, 'REJETE')

        return {
            'success': True,
            'message': 'Absence rejetée par le manager'
        }

    @staticmethod
    def valider_rh(absence, user, commentaire=''):
        """
        Validation par les RH (finale).

        Args:
            absence: Instance de l'absence
            user: RH effectuant la validation
            commentaire: Commentaire optionnel

        Returns:
            dict: Résultat de la validation
        """
        from absence.models import ValidationAbsence, AcquisitionConges
        from absence.services.notification_service import NotificationService

        if absence.statut != AbsenceService.EN_ATTENTE_RH:
            return {
                'success': False,
                'error': 'Cette absence n\'est pas en attente de validation RH'
            }

        with transaction.atomic():
            absence.statut = AbsenceService.VALIDE
            absence.date_validation_rh = timezone.now()
            absence.valide_par_rh = user
            absence.commentaire_rh = commentaire
            absence.save()

            # Traçabilité
            ValidationAbsence.objects.create(
                absence=absence,
                etape='RH',
                action='VALIDE',
                valide_par=user,
                commentaire=commentaire
            )

            # Décompter du solde si nécessaire
            if absence.type_absence.decompte_solde:
                annee_acquisition = absence.date_debut.year - 1
                try:
                    acquisition = AcquisitionConges.objects.get(
                        employe=absence.employe,
                        annee_reference=annee_acquisition
                    )
                    acquisition.jours_pris += absence.nombre_jours
                    acquisition.jours_solde = acquisition.jours_acquis - acquisition.jours_pris
                    acquisition.save()
                except AcquisitionConges.DoesNotExist:
                    logger.warning(
                        "Acquisition non trouvée pour %s année %s",
                        absence.employe, annee_acquisition
                    )

            NotificationService.notifier_validation_rh(absence, 'VALIDE')

        return {
            'success': True,
            'message': 'Absence validée par les RH'
        }

    @staticmethod
    def rejeter_rh(absence, user, commentaire=''):
        """
        Rejet par les RH.

        Args:
            absence: Instance de l'absence
            user: RH effectuant le rejet
            commentaire: Motif du rejet

        Returns:
            dict: Résultat du rejet
        """
        from absence.models import ValidationAbsence
        from absence.services.notification_service import NotificationService

        if absence.statut != AbsenceService.EN_ATTENTE_RH:
            return {
                'success': False,
                'error': 'Cette absence n\'est pas en attente de validation RH'
            }

        with transaction.atomic():
            absence.statut = AbsenceService.REJETE
            absence.date_validation_rh = timezone.now()
            absence.valide_par_rh = user
            absence.commentaire_rh = commentaire
            absence.save()

            ValidationAbsence.objects.create(
                absence=absence,
                etape='RH',
                action='REJETE',
                valide_par=user,
                commentaire=commentaire
            )

            NotificationService.notifier_validation_rh(absence, 'REJETE')

        return {
            'success': True,
            'message': 'Absence rejetée par les RH'
        }

    @staticmethod
    def annuler_absence(absence, user, motif=''):
        """
        Annule une absence.

        Args:
            absence: Instance de l'absence
            user: Utilisateur effectuant l'annulation
            motif: Motif de l'annulation

        Returns:
            dict: Résultat de l'annulation
        """
        from absence.models import ValidationAbsence, AcquisitionConges

        statuts_annulables = [
            AbsenceService.BROUILLON,
            AbsenceService.EN_ATTENTE_MANAGER,
            AbsenceService.EN_ATTENTE_RH,
            AbsenceService.VALIDE
        ]

        if absence.statut not in statuts_annulables:
            return {
                'success': False,
                'error': 'Cette absence ne peut pas être annulée'
            }

        with transaction.atomic():
            ancien_statut = absence.statut

            # Si était validée, restituer le solde
            if ancien_statut == AbsenceService.VALIDE and absence.type_absence.decompte_solde:
                annee_acquisition = absence.date_debut.year - 1
                try:
                    acquisition = AcquisitionConges.objects.get(
                        employe=absence.employe,
                        annee_reference=annee_acquisition
                    )
                    acquisition.jours_pris -= absence.nombre_jours
                    acquisition.jours_solde = acquisition.jours_acquis - acquisition.jours_pris
                    acquisition.save()
                except AcquisitionConges.DoesNotExist:
                    pass

            absence.statut = AbsenceService.ANNULE
            absence.save()

            ValidationAbsence.objects.create(
                absence=absence,
                etape='ANNULATION',
                action='ANNULE',
                valide_par=user,
                commentaire=motif
            )

        return {
            'success': True,
            'message': 'Absence annulée avec succès',
            'solde_restitue': ancien_statut == AbsenceService.VALIDE
        }

    @staticmethod
    def get_absences_employe(employe, annee=None, statut=None):
        """
        Récupère les absences d'un employé.

        Args:
            employe: Instance de l'employé
            annee: Année de filtrage (optionnel)
            statut: Statut de filtrage (optionnel)

        Returns:
            QuerySet: Absences filtrées
        """
        from absence.models import Absence

        qs = Absence.objects.filter(employe=employe)

        if annee:
            qs = qs.filter(date_debut__year=annee)

        if statut:
            qs = qs.filter(statut=statut)

        return qs.order_by('-date_debut')

    @staticmethod
    def get_absences_a_valider_manager(manager):
        """
        Récupère les absences à valider pour un manager.

        Args:
            manager: Instance du manager (ZY00)

        Returns:
            QuerySet: Absences en attente de validation
        """
        from absence.models import Absence
        from departement.models import ZYMA

        # Récupérer les départements gérés
        departements_geres = ZYMA.objects.filter(
            employe=manager,
            actif=True,
            date_fin__isnull=True
        ).values_list('departement_id', flat=True)

        return Absence.objects.filter(
            statut=AbsenceService.EN_ATTENTE_MANAGER,
            employe__affectations__poste__DEPARTEMENT_id__in=departements_geres,
            employe__affectations__date_fin__isnull=True
        ).distinct().order_by('date_debut')

    @staticmethod
    def get_absences_a_valider_rh():
        """
        Récupère les absences à valider par les RH.

        Returns:
            QuerySet: Absences en attente de validation RH
        """
        from absence.models import Absence

        return Absence.objects.filter(
            statut=AbsenceService.EN_ATTENTE_RH
        ).order_by('date_debut')
