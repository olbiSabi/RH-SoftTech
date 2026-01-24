# frais/services/validation_service.py
"""
Service de validation pour les notes de frais.
"""
from decimal import Decimal
from typing import Optional, List, Dict, Any
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError


class ValidationFraisService:
    """Service pour les validations métier des frais."""

    @staticmethod
    def valider_ligne_frais(
        categorie,
        montant: Decimal,
        date_depense,
        employe=None,
        justificatif=None
    ) -> Dict[str, Any]:
        """
        Valide une ligne de frais avant création.

        Args:
            categorie: Catégorie de frais
            montant: Montant de la dépense
            date_depense: Date de la dépense
            employe: Employé concerné (optionnel)
            justificatif: Fichier justificatif (optionnel)

        Returns:
            Dict avec 'is_valid', 'errors', 'warnings'
        """
        errors = []
        warnings = []

        # Vérifier montant positif
        if montant <= 0:
            errors.append("Le montant doit être positif")

        # Vérifier justificatif obligatoire
        if categorie.JUSTIFICATIF_OBLIGATOIRE and not justificatif:
            errors.append(f"Un justificatif est obligatoire pour la catégorie '{categorie.LIBELLE}'")

        # Vérifier plafond par défaut de la catégorie
        if categorie.PLAFOND_DEFAUT and montant > categorie.PLAFOND_DEFAUT:
            warnings.append(
                f"Le montant ({montant}) dépasse le plafond recommandé de {categorie.PLAFOND_DEFAUT}"
            )

        # Vérifier date pas dans le futur
        if date_depense > timezone.now().date():
            errors.append("La date de dépense ne peut pas être dans le futur")

        # Vérifier plafond spécifique si employé fourni
        if employe:
            from frais.services.categorie_service import CategorieService
            plafond = CategorieService.get_plafond_applicable(
                categorie, employe, date_depense
            )

            if plafond:
                if plafond.MONTANT_PAR_DEPENSE and montant > plafond.MONTANT_PAR_DEPENSE:
                    warnings.append(
                        f"Le montant dépasse le plafond par dépense de {plafond.MONTANT_PAR_DEPENSE}"
                    )

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    @staticmethod
    def valider_note_frais(note) -> Dict[str, Any]:
        """
        Valide une note de frais complète.

        Args:
            note: Instance NFNF

        Returns:
            Dict avec 'is_valid', 'errors', 'warnings'
        """
        errors = []
        warnings = []

        # Vérifier qu'il y a des lignes
        if not note.lignes.exists():
            errors.append("La note de frais doit contenir au moins une ligne")

        # Vérifier la cohérence des dates
        if note.PERIODE_FIN < note.PERIODE_DEBUT:
            errors.append("La date de fin doit être postérieure à la date de début")

        # Vérifier que toutes les lignes sont dans la période
        lignes_hors_periode = note.lignes.exclude(
            DATE_DEPENSE__gte=note.PERIODE_DEBUT,
            DATE_DEPENSE__lte=note.PERIODE_FIN
        )

        if lignes_hors_periode.exists():
            errors.append(
                f"{lignes_hors_periode.count()} ligne(s) ont une date hors de la période de la note"
            )

        # Vérifier les justificatifs manquants
        lignes_sans_justif = note.lignes.filter(
            CATEGORIE__JUSTIFICATIF_OBLIGATOIRE=True,
            JUSTIFICATIF=''
        ) | note.lignes.filter(
            CATEGORIE__JUSTIFICATIF_OBLIGATOIRE=True,
            JUSTIFICATIF__isnull=True
        )

        if lignes_sans_justif.exists():
            warnings.append(
                f"{lignes_sans_justif.count()} ligne(s) n'ont pas de justificatif (obligatoire)"
            )

        # Vérifier le montant total
        if note.MONTANT_TOTAL <= 0:
            errors.append("Le montant total doit être positif")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    @staticmethod
    def verifier_droits_validation(valideur, note) -> bool:
        """
        Vérifie si un employé peut valider une note de frais.

        Args:
            valideur: Employé valideur
            note: Note de frais à valider

        Returns:
            True si autorisé
        """
        # L'employé ne peut pas valider sa propre note
        if valideur == note.EMPLOYE:
            return False

        # Vérifier le rôle de validation
        # Utiliser le système de rôles existant
        roles_valideurs = ['DRH', 'RESP_ADMIN', 'DAF']

        for role in roles_valideurs:
            if valideur.has_role(role):
                return True

        # Vérifier si c'est le manager de l'employé
        if hasattr(valideur, 'est_manager_de'):
            if valideur.est_manager_de(note.EMPLOYE):
                return True

        return False

    @staticmethod
    def verifier_plafond_mensuel(
        employe,
        categorie,
        montant: Decimal,
        mois: int,
        annee: int
    ) -> Dict[str, Any]:
        """
        Vérifie si le plafond mensuel est dépassé pour une catégorie.

        Args:
            employe: Employé concerné
            categorie: Catégorie de frais
            montant: Nouveau montant à ajouter
            mois: Mois concerné
            annee: Année concernée

        Returns:
            Dict avec 'is_valid', 'montant_utilise', 'plafond', 'restant'
        """
        from frais.models import NFLF
        from frais.services.categorie_service import CategorieService

        # Récupérer le plafond applicable
        plafond = CategorieService.get_plafond_applicable(
            categorie, employe, timezone.now().date()
        )

        if not plafond or not plafond.MONTANT_MENSUEL:
            return {
                'is_valid': True,
                'montant_utilise': Decimal('0'),
                'plafond': None,
                'restant': None
            }

        # Calculer le montant déjà utilisé ce mois
        from datetime import date
        debut_mois = date(annee, mois, 1)
        if mois == 12:
            fin_mois = date(annee + 1, 1, 1)
        else:
            fin_mois = date(annee, mois + 1, 1)

        montant_utilise = NFLF.objects.filter(
            NOTE_FRAIS__EMPLOYE=employe,
            CATEGORIE=categorie,
            DATE_DEPENSE__gte=debut_mois,
            DATE_DEPENSE__lt=fin_mois,
            NOTE_FRAIS__STATUT__in=['SOUMIS', 'EN_VALIDATION', 'VALIDE', 'REMBOURSE']
        ).aggregate(total=Sum('MONTANT'))['total'] or Decimal('0')

        restant = plafond.MONTANT_MENSUEL - montant_utilise
        nouveau_total = montant_utilise + montant

        return {
            'is_valid': nouveau_total <= plafond.MONTANT_MENSUEL,
            'montant_utilise': montant_utilise,
            'plafond': plafond.MONTANT_MENSUEL,
            'restant': max(Decimal('0'), restant)
        }

    @staticmethod
    def get_anomalies_note(note) -> List[Dict[str, Any]]:
        """
        Détecte les anomalies potentielles dans une note de frais.

        Args:
            note: Instance NFNF

        Returns:
            Liste des anomalies détectées
        """
        anomalies = []

        # Montant total élevé
        seuil_alerte = Decimal('500000')  # 500K XOF
        if note.MONTANT_TOTAL > seuil_alerte:
            anomalies.append({
                'type': 'MONTANT_ELEVE',
                'severity': 'warning',
                'message': f"Montant total élevé: {note.MONTANT_TOTAL} XOF"
            })

        # Beaucoup de lignes sans justificatif
        total_lignes = note.lignes.count()
        lignes_sans_justif = note.lignes.filter(
            JUSTIFICATIF__isnull=True
        ).count() + note.lignes.filter(JUSTIFICATIF='').count()

        if total_lignes > 0 and lignes_sans_justif / total_lignes > 0.5:
            anomalies.append({
                'type': 'JUSTIFICATIFS_MANQUANTS',
                'severity': 'warning',
                'message': f"{lignes_sans_justif}/{total_lignes} lignes sans justificatif"
            })

        # Dépenses le week-end
        lignes_weekend = note.lignes.filter(
            DATE_DEPENSE__week_day__in=[1, 7]  # Django: 1=Dimanche, 7=Samedi
        ).count()

        if lignes_weekend > 0:
            anomalies.append({
                'type': 'DEPENSES_WEEKEND',
                'severity': 'info',
                'message': f"{lignes_weekend} dépense(s) effectuée(s) le week-end"
            })

        # Doublons potentiels (même montant, même catégorie, même jour)
        from django.db.models import Count
        doublons = note.lignes.values(
            'CATEGORIE', 'DATE_DEPENSE', 'MONTANT'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)

        if doublons.exists():
            anomalies.append({
                'type': 'DOUBLONS_POTENTIELS',
                'severity': 'warning',
                'message': f"{doublons.count()} doublon(s) potentiel(s) détecté(s)"
            })

        return anomalies
