# frais/services/statistiques_service.py
"""
Service pour les statistiques et rapports des notes de frais.
"""
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import date, timedelta
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone


class StatistiquesFraisService:
    """Service pour les statistiques des notes de frais."""

    @staticmethod
    def get_stats_employe(employe, annee: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les statistiques de frais d'un employé.

        Args:
            employe: Instance ZY00
            annee: Année de référence (défaut: année courante)

        Returns:
            Dictionnaire de statistiques
        """
        from frais.models import NFNF, NFLF, NFAV

        if annee is None:
            annee = timezone.now().year

        debut_annee = date(annee, 1, 1)
        fin_annee = date(annee, 12, 31)

        # Notes de frais
        notes = NFNF.objects.filter(
            EMPLOYE=employe,
            PERIODE_DEBUT__gte=debut_annee,
            PERIODE_FIN__lte=fin_annee
        )

        notes_stats = notes.aggregate(
            total_notes=Count('id'),
            montant_total=Sum('MONTANT_TOTAL'),
            montant_rembourse=Sum('MONTANT_REMBOURSE')
        )

        # Par statut
        notes_par_statut = dict(
            notes.values('STATUT').annotate(count=Count('id')).values_list('STATUT', 'count')
        )

        # Avances
        avances = NFAV.objects.filter(
            EMPLOYE=employe,
            CREATED_AT__year=annee
        )

        avances_stats = avances.aggregate(
            total_avances=Count('id'),
            montant_demande=Sum('MONTANT_DEMANDE'),
            montant_verse=Sum('MONTANT_APPROUVE', filter=Q(STATUT__in=['VERSE', 'REGULARISE']))
        )

        # Avances non régularisées
        solde_avances = avances.filter(
            STATUT='VERSE'
        ).aggregate(total=Sum('MONTANT_APPROUVE'))['total'] or Decimal('0')

        return {
            'annee': annee,
            'notes': {
                'total': notes_stats['total_notes'] or 0,
                'montant_total': notes_stats['montant_total'] or Decimal('0'),
                'montant_rembourse': notes_stats['montant_rembourse'] or Decimal('0'),
                'par_statut': notes_par_statut
            },
            'avances': {
                'total': avances_stats['total_avances'] or 0,
                'montant_demande': avances_stats['montant_demande'] or Decimal('0'),
                'montant_verse': avances_stats['montant_verse'] or Decimal('0'),
                'solde_non_regularise': solde_avances
            }
        }

    @staticmethod
    def get_stats_globales(annee: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les statistiques globales des frais.

        Args:
            annee: Année de référence (défaut: année courante)

        Returns:
            Dictionnaire de statistiques
        """
        from frais.models import NFNF, NFAV

        if annee is None:
            annee = timezone.now().year

        debut_annee = date(annee, 1, 1)
        fin_annee = date(annee, 12, 31)

        # Notes de frais
        notes = NFNF.objects.filter(
            PERIODE_DEBUT__gte=debut_annee,
            PERIODE_FIN__lte=fin_annee
        )

        notes_stats = notes.aggregate(
            total=Count('id'),
            montant_total=Sum('MONTANT_TOTAL'),
            montant_valide=Sum('MONTANT_VALIDE'),
            montant_rembourse=Sum('MONTANT_REMBOURSE'),
            moyenne_par_note=Avg('MONTANT_TOTAL')
        )

        # En attente de validation
        en_attente = notes.filter(STATUT__in=['SOUMIS', 'EN_VALIDATION']).aggregate(
            count=Count('id'),
            montant=Sum('MONTANT_TOTAL')
        )

        # En attente de remboursement
        a_rembourser = notes.filter(STATUT='VALIDE').aggregate(
            count=Count('id'),
            montant=Sum('MONTANT_VALIDE')
        )

        # Avances
        avances = NFAV.objects.filter(CREATED_AT__year=annee)

        avances_stats = avances.aggregate(
            total=Count('id'),
            montant_total=Sum('MONTANT_DEMANDE'),
            montant_verse=Sum('MONTANT_APPROUVE', filter=Q(STATUT__in=['VERSE', 'REGULARISE']))
        )

        # Avances en cours
        avances_en_cours = avances.filter(STATUT__in=['DEMANDE', 'APPROUVE', 'VERSE']).aggregate(
            count=Count('id'),
            montant=Sum('MONTANT_APPROUVE')
        )

        return {
            'annee': annee,
            'notes_frais': {
                'total': notes_stats['total'] or 0,
                'montant_total': notes_stats['montant_total'] or Decimal('0'),
                'montant_valide': notes_stats['montant_valide'] or Decimal('0'),
                'montant_rembourse': notes_stats['montant_rembourse'] or Decimal('0'),
                'moyenne_par_note': notes_stats['moyenne_par_note'] or Decimal('0'),
                'en_attente_validation': {
                    'count': en_attente['count'] or 0,
                    'montant': en_attente['montant'] or Decimal('0')
                },
                'a_rembourser': {
                    'count': a_rembourser['count'] or 0,
                    'montant': a_rembourser['montant'] or Decimal('0')
                }
            },
            'avances': {
                'total': avances_stats['total'] or 0,
                'montant_total': avances_stats['montant_total'] or Decimal('0'),
                'montant_verse': avances_stats['montant_verse'] or Decimal('0'),
                'en_cours': {
                    'count': avances_en_cours['count'] or 0,
                    'montant': avances_en_cours['montant'] or Decimal('0')
                }
            }
        }

    @staticmethod
    def get_stats_par_categorie(
        annee: Optional[int] = None,
        employe=None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques par catégorie de frais.

        Args:
            annee: Année de référence
            employe: Filtrer par employé (optionnel)

        Returns:
            Liste de stats par catégorie
        """
        from frais.models import NFLF, NFCA

        if annee is None:
            annee = timezone.now().year

        debut_annee = date(annee, 1, 1)
        fin_annee = date(annee, 12, 31)

        lignes = NFLF.objects.filter(
            DATE_DEPENSE__gte=debut_annee,
            DATE_DEPENSE__lte=fin_annee,
            NOTE_FRAIS__STATUT__in=['SOUMIS', 'EN_VALIDATION', 'VALIDE', 'REMBOURSE']
        )

        if employe:
            lignes = lignes.filter(NOTE_FRAIS__EMPLOYE=employe)

        stats = lignes.values(
            'CATEGORIE__CODE', 'CATEGORIE__LIBELLE', 'CATEGORIE__ICONE'
        ).annotate(
            nb_lignes=Count('id'),
            montant_total=Sum('MONTANT'),
            montant_moyen=Avg('MONTANT')
        ).order_by('-montant_total')

        return list(stats)

    @staticmethod
    def get_evolution_mensuelle(annee: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère l'évolution mensuelle des frais.

        Args:
            annee: Année de référence

        Returns:
            Liste avec montants par mois
        """
        from frais.models import NFNF

        if annee is None:
            annee = timezone.now().year

        debut_annee = date(annee, 1, 1)
        fin_annee = date(annee, 12, 31)

        evolution = NFNF.objects.filter(
            PERIODE_DEBUT__gte=debut_annee,
            PERIODE_FIN__lte=fin_annee,
            STATUT__in=['VALIDE', 'REMBOURSE']
        ).annotate(
            mois=TruncMonth('PERIODE_DEBUT')
        ).values('mois').annotate(
            nb_notes=Count('id'),
            montant_total=Sum('MONTANT_TOTAL')
        ).order_by('mois')

        # Compléter avec tous les mois
        result = []
        for m in range(1, 13):
            mois_date = date(annee, m, 1)
            data = next(
                (item for item in evolution if item['mois'].month == m),
                None
            )
            result.append({
                'mois': mois_date,
                'mois_label': mois_date.strftime('%B %Y'),
                'nb_notes': data['nb_notes'] if data else 0,
                'montant_total': data['montant_total'] if data else Decimal('0')
            })

        return result

    @staticmethod
    def get_top_employes(
        annee: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Récupère le classement des employés par montant de frais.

        Args:
            annee: Année de référence
            limit: Nombre max de résultats

        Returns:
            Liste des top employés avec leurs totaux
        """
        from frais.models import NFNF

        if annee is None:
            annee = timezone.now().year

        debut_annee = date(annee, 1, 1)
        fin_annee = date(annee, 12, 31)

        top = NFNF.objects.filter(
            PERIODE_DEBUT__gte=debut_annee,
            PERIODE_FIN__lte=fin_annee,
            STATUT__in=['VALIDE', 'REMBOURSE']
        ).values(
            'EMPLOYE__matricule',
            'EMPLOYE__nom',
            'EMPLOYE__prenoms'
        ).annotate(
            nb_notes=Count('uuid'),
            montant_total=Sum('MONTANT_TOTAL')
        ).order_by('-montant_total')[:limit]

        return list(top)

    @staticmethod
    def get_delai_moyen_traitement(annee: Optional[int] = None) -> Dict[str, Any]:
        """
        Calcule les délais moyens de traitement.

        Args:
            annee: Année de référence

        Returns:
            Dict avec délais moyens
        """
        from frais.models import NFNF
        from django.db.models import F, ExpressionWrapper, DurationField

        if annee is None:
            annee = timezone.now().year

        debut_annee = date(annee, 1, 1)
        fin_annee = date(annee, 12, 31)

        notes_validees = NFNF.objects.filter(
            PERIODE_DEBUT__gte=debut_annee,
            PERIODE_FIN__lte=fin_annee,
            DATE_SOUMISSION__isnull=False,
            DATE_VALIDATION__isnull=False
        )

        notes_remboursees = notes_validees.filter(
            DATE_REMBOURSEMENT__isnull=False
        )

        # Calcul manuel des délais (en jours)
        total_delai_validation = 0
        count_validation = 0
        total_delai_remboursement = 0
        count_remboursement = 0

        for note in notes_validees:
            delai = (note.DATE_VALIDATION - note.DATE_SOUMISSION).days
            total_delai_validation += delai
            count_validation += 1

        for note in notes_remboursees:
            delai = (note.DATE_REMBOURSEMENT - note.DATE_VALIDATION.date()).days
            total_delai_remboursement += delai
            count_remboursement += 1

        return {
            'delai_validation_moyen': (
                total_delai_validation / count_validation if count_validation > 0 else 0
            ),
            'delai_remboursement_moyen': (
                total_delai_remboursement / count_remboursement if count_remboursement > 0 else 0
            ),
            'notes_analysees': count_validation
        }
