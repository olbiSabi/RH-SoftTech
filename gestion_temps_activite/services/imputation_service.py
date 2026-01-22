# gestion_temps_activite/services/imputation_service.py
"""
Service de gestion des imputations de temps.
"""
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


class ImputationService:
    """Service centralisé pour les imputations de temps."""

    @classmethod
    def valider_imputation(cls, imputation, validateur):
        """
        Valide une imputation de temps.

        Args:
            imputation: Instance ZDIT
            validateur: Employé qui valide

        Returns:
            bool: True si validé avec succès
        """
        if imputation.valide:
            return False

        imputation.valide = True
        imputation.valide_par = validateur
        imputation.date_validation = timezone.now()
        imputation.save()
        return True

    @classmethod
    def rejeter_imputation(cls, imputation, motif):
        """
        Rejette une imputation de temps.

        Args:
            imputation: Instance ZDIT
            motif: Motif du rejet

        Returns:
            bool: True si rejeté avec succès
        """
        if not motif:
            return False

        imputation.valide = False
        imputation.commentaire = f"[REJETÉ] {motif}\n{imputation.commentaire or ''}"
        imputation.save()
        return True

    @classmethod
    def peut_modifier(cls, imputation, employe):
        """
        Vérifie si un employé peut modifier une imputation.

        Args:
            imputation: Instance ZDIT
            employe: Employé qui veut modifier

        Returns:
            bool: True si modification autorisée
        """
        # Si validé ou facturé, pas de modification
        if imputation.valide or imputation.facture:
            return False

        # L'employé peut modifier ses propres imputations
        if imputation.employe == employe:
            return True

        # Les admins peuvent modifier
        if employe.has_role('DRH') or employe.has_role('GESTION_APP'):
            return True

        return False

    @classmethod
    def peut_supprimer(cls, imputation, employe):
        """
        Vérifie si un employé peut supprimer une imputation.

        Args:
            imputation: Instance ZDIT
            employe: Employé qui veut supprimer

        Returns:
            bool: True si suppression autorisée
        """
        # Mêmes règles que modification
        return cls.peut_modifier(imputation, employe)

    @classmethod
    def get_heures_periode(cls, employe, date_debut, date_fin):
        """
        Calcule les heures d'un employé sur une période.

        Args:
            employe: Instance ZY00
            date_debut: Date de début
            date_fin: Date de fin

        Returns:
            dict: {total, validees, en_attente}
        """
        from gestion_temps_activite.models import ZDIT

        imputations = ZDIT.objects.filter(
            employe=employe,
            date__gte=date_debut,
            date__lte=date_fin
        )

        total = imputations.aggregate(total=Sum('duree'))['total'] or 0
        validees = imputations.filter(valide=True).aggregate(total=Sum('duree'))['total'] or 0

        return {
            'total': total,
            'validees': validees,
            'en_attente': total - validees
        }

    @classmethod
    def get_heures_mois_courant(cls, employe):
        """
        Calcule les heures du mois courant pour un employé.

        Args:
            employe: Instance ZY00

        Returns:
            dict: {total, validees, en_attente, moyenne_jour}
        """
        from gestion_temps_activite.models import ZDIT

        date_actuelle = timezone.now().date()
        debut_mois = date_actuelle.replace(day=1)

        if date_actuelle.month == 12:
            fin_mois = date_actuelle.replace(day=31)
        else:
            fin_mois = date_actuelle.replace(month=date_actuelle.month + 1, day=1) - timedelta(days=1)

        heures = cls.get_heures_periode(employe, debut_mois, fin_mois)

        # Calcul moyenne par jour
        imputations = ZDIT.objects.filter(
            employe=employe,
            date__gte=debut_mois,
            date__lte=fin_mois
        )
        jours_travailles = imputations.values('date').distinct().count()
        heures['moyenne_jour'] = (heures['total'] / jours_travailles) if jours_travailles > 0 else 0
        heures['jours_travailles'] = jours_travailles

        return heures

    @classmethod
    def get_heures_par_projet(cls, employe, date_debut, date_fin):
        """
        Calcule les heures par projet sur une période.

        Args:
            employe: Instance ZY00
            date_debut: Date de début
            date_fin: Date de fin

        Returns:
            QuerySet: Heures groupées par projet
        """
        from gestion_temps_activite.models import ZDIT

        return ZDIT.objects.filter(
            employe=employe,
            date__gte=date_debut,
            date__lte=date_fin
        ).values(
            'tache__projet__nom_projet',
            'tache__projet__code_projet'
        ).annotate(
            total_heures=Sum('duree')
        ).order_by('-total_heures')

    @classmethod
    def calculer_montant_facturable(cls, imputation):
        """
        Calcule le montant facturable d'une imputation.

        Args:
            imputation: Instance ZDIT

        Returns:
            float: Montant facturable
        """
        if not imputation.facturable or not imputation.duree or not imputation.taux_horaire_applique:
            return 0

        return float(imputation.duree) * float(imputation.taux_horaire_applique)

    @classmethod
    def get_dates_periode(cls, periode, date_actuelle=None):
        """
        Calcule les dates de début et fin pour une période donnée.

        Args:
            periode: 'semaine', 'mois', 'annee'
            date_actuelle: Date de référence (défaut: aujourd'hui)

        Returns:
            tuple: (date_debut, date_fin)
        """
        if date_actuelle is None:
            date_actuelle = timezone.now().date()

        if periode == 'semaine':
            date_debut = date_actuelle - timedelta(days=date_actuelle.weekday())
            date_fin = date_debut + timedelta(days=6)
        elif periode == 'annee':
            date_debut = date_actuelle.replace(month=1, day=1)
            date_fin = date_actuelle.replace(month=12, day=31)
        else:  # mois par défaut
            date_debut = date_actuelle.replace(day=1)
            if date_actuelle.month == 12:
                date_fin = date_actuelle.replace(day=31)
            else:
                date_fin = date_actuelle.replace(month=date_actuelle.month + 1, day=1) - timedelta(days=1)

        return date_debut, date_fin
