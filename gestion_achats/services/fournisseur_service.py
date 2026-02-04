"""
Service métier pour la gestion des fournisseurs.

Ce service encapsule toute la logique métier liée aux fournisseurs,
incluant la création, l'évaluation, les statistiques et la gestion des contacts.
"""

import logging
from decimal import Decimal
from datetime import datetime
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum, Avg, Q

from gestion_achats.models import (
    GACFournisseur,
    GACArticle,
    GACBonCommande,
    GACHistorique,
)
from gestion_achats.constants import (
    STATUT_FOURNISSEUR_ACTIF,
    STATUT_FOURNISSEUR_INACTIF,
    STATUT_FOURNISSEUR_SUSPENDU,
)
from gestion_achats.exceptions import (
    FournisseurError,
    ValidationError as GACValidationError,
)
from gestion_achats.utils import valider_nif

logger = logging.getLogger(__name__)


class FournisseurService:
    """Service pour la gestion des fournisseurs."""

    @staticmethod
    @transaction.atomic
    def creer_fournisseur(raison_sociale, email, telephone, adresse,
                         nif=None, code_postal=None, ville=None, pays='Togo',
                         conditions_paiement=None, nom_contact=None,
                         email_contact=None, telephone_contact=None,
                         iban=None, numero_tva=None, fax=None,
                         cree_par=None):
        """
        Crée un nouveau fournisseur.

        Args:
            raison_sociale: Raison sociale
            email: Email du fournisseur
            telephone: Téléphone
            adresse: Adresse
            nif: Numéro d'Identification Fiscale (optionnel, 9-10 chiffres)
            code_postal: Code postal (optionnel)
            ville: Ville (optionnel)
            pays: Pays (défaut: Togo)
            conditions_paiement: Conditions de paiement (optionnel)
            nom_contact: Nom du contact principal (optionnel)
            email_contact: Email du contact (optionnel)
            telephone_contact: Téléphone du contact (optionnel)
            iban: IBAN (optionnel)
            numero_tva: Numéro de TVA (optionnel)
            fax: Fax (optionnel)
            cree_par: Utilisateur créateur (optionnel)

        Returns:
            GACFournisseur: Le fournisseur créé

        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Valider le format NIF si fourni
            if nif and not valider_nif(nif):
                raise GACValidationError(f"Le NIF {nif} n'est pas valide")

            # Créer le fournisseur (le code sera généré automatiquement par la méthode save())
            fournisseur = GACFournisseur.objects.create(
                raison_sociale=raison_sociale,
                nif=nif,
                email=email,
                telephone=telephone,
                adresse=adresse,
                code_postal=code_postal,
                ville=ville,
                pays=pays,
                conditions_paiement=conditions_paiement,
                nom_contact=nom_contact,
                email_contact=email_contact,
                telephone_contact=telephone_contact,
                iban=iban,
                numero_tva=numero_tva,
                fax=fax,
                statut=STATUT_FOURNISSEUR_ACTIF,
                cree_par=cree_par
            )

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=fournisseur,
                action='CREATION',
                utilisateur=cree_par,
                details=f"Création du fournisseur {fournisseur.code} - {raison_sociale}"
            )

            logger.info(f"Fournisseur {fournisseur.code} créé: {raison_sociale}")

            return fournisseur

        except Exception as e:
            logger.error(f"Erreur lors de la création du fournisseur: {str(e)}")
            raise FournisseurError(f"Impossible de créer le fournisseur: {str(e)}")

    @staticmethod
    @transaction.atomic
    def modifier_fournisseur(fournisseur, utilisateur, **kwargs):
        """
        Modifie un fournisseur existant.

        Args:
            fournisseur: Le fournisseur à modifier
            utilisateur: L'utilisateur qui modifie
            **kwargs: Les champs à modifier

        Returns:
            GACFournisseur: Le fournisseur modifié
        """
        try:
            # Sauvegarder les anciennes valeurs pour l'historique
            modifications = []

            for field, value in kwargs.items():
                if hasattr(fournisseur, field):
                    old_value = getattr(fournisseur, field)
                    if old_value != value:
                        setattr(fournisseur, field, value)
                        modifications.append(f"{field}: {old_value} → {value}")

            fournisseur.modifie_par = utilisateur
            fournisseur.save()

            if modifications:
                # Créer l'historique
                GACHistorique.enregistrer_action(
                    objet=fournisseur,
                    action='MODIFICATION',
                    utilisateur=utilisateur,
                    details=f"Modification du fournisseur. " + ", ".join(modifications)
                )

                logger.info(f"Fournisseur {fournisseur.code} modifié par {utilisateur}")

            return fournisseur

        except Exception as e:
            logger.error(f"Erreur lors de la modification du fournisseur: {str(e)}")
            raise FournisseurError(f"Impossible de modifier le fournisseur: {str(e)}")

    @staticmethod
    @transaction.atomic
    def evaluer_fournisseur(fournisseur, evaluateur, note_qualite, note_delai,
                           note_prix, commentaire=None):
        """
        Enregistre une évaluation de fournisseur.

        Args:
            fournisseur: Le fournisseur à évaluer
            evaluateur: L'utilisateur qui évalue
            note_qualite: Note sur 5 pour la qualité
            note_delai: Note sur 5 pour les délais
            note_prix: Note sur 5 pour les prix
            commentaire: Commentaire (optionnel)

        Returns:
            GACFournisseur: Le fournisseur mis à jour

        Raises:
            ValidationError: Si les notes sont invalides
        """
        # Valider les notes (doivent être entre 0 et 5)
        for note in [note_qualite, note_delai, note_prix]:
            if not (0 <= note <= 5):
                raise GACValidationError("Les notes doivent être comprises entre 0 et 5")

        try:
            # Calculer la note moyenne de cette évaluation
            note_moyenne = (note_qualite + note_delai + note_prix) / 3

            # TODO: Créer une entrée GACEvaluationFournisseur si le modèle existe
            # Pour l'instant, on met à jour directement la note du fournisseur

            # Recalculer la note moyenne globale du fournisseur
            # Si c'est la première évaluation
            if fournisseur.evaluation_moyenne is None or fournisseur.evaluation_moyenne == 0:
                fournisseur.evaluation_moyenne = note_moyenne
            else:
                # Moyenne pondérée (on donne plus de poids aux évaluations récentes)
                # On peut améliorer cela en gardant un compteur d'évaluations
                fournisseur.evaluation_moyenne = (
                    (fournisseur.evaluation_moyenne * 0.7) + (note_moyenne * 0.3)
                )

            fournisseur.save()

            # Créer l'historique
            details = (
                f"Évaluation par {evaluateur}: "
                f"Qualité={note_qualite}/5, Délai={note_delai}/5, Prix={note_prix}/5. "
                f"Moyenne: {note_moyenne:.2f}/5"
            )
            if commentaire:
                details += f". Commentaire: {commentaire}"

            GACHistorique.enregistrer_action(
                objet=fournisseur,
                action='EVALUATION',
                utilisateur=evaluateur,
                details=details
            )

            logger.info(
                f"Fournisseur {fournisseur.code} évalué par {evaluateur}: "
                f"note moyenne {note_moyenne:.2f}/5"
            )

            return fournisseur

        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du fournisseur: {str(e)}")
            raise FournisseurError(f"Impossible d'évaluer le fournisseur: {str(e)}")

    @staticmethod
    @transaction.atomic
    def suspendre_fournisseur(fournisseur, utilisateur, motif):
        """
        Suspend un fournisseur.

        Args:
            fournisseur: Le fournisseur à suspendre
            utilisateur: L'utilisateur qui suspend
            motif: Le motif de la suspension

        Returns:
            GACFournisseur: Le fournisseur suspendu
        """
        try:
            ancien_statut = fournisseur.statut
            fournisseur.statut = STATUT_FOURNISSEUR_SUSPENDU
            fournisseur.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=fournisseur,
                action='SUSPENSION',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut,
                nouveau_statut=fournisseur.statut,
                details=f"Fournisseur suspendu par {utilisateur}. Motif: {motif}"
            )

            logger.warning(f"Fournisseur {fournisseur.code} suspendu: {motif}")

            return fournisseur

        except Exception as e:
            logger.error(f"Erreur lors de la suspension du fournisseur: {str(e)}")
            raise FournisseurError(f"Impossible de suspendre le fournisseur: {str(e)}")

    @staticmethod
    @transaction.atomic
    def reactiver_fournisseur(fournisseur, utilisateur):
        """
        Réactive un fournisseur suspendu ou inactif.

        Args:
            fournisseur: Le fournisseur à réactiver
            utilisateur: L'utilisateur qui réactive

        Returns:
            GACFournisseur: Le fournisseur réactivé
        """
        try:
            ancien_statut = fournisseur.statut
            fournisseur.statut = STATUT_FOURNISSEUR_ACTIF
            fournisseur.save()

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=fournisseur,
                action='REACTIVATION',
                utilisateur=utilisateur,
                ancien_statut=ancien_statut,
                nouveau_statut=fournisseur.statut,
                details=f"Fournisseur réactivé par {utilisateur}"
            )

            logger.info(f"Fournisseur {fournisseur.code} réactivé")

            return fournisseur

        except Exception as e:
            logger.error(f"Erreur lors de la réactivation du fournisseur: {str(e)}")
            raise FournisseurError(f"Impossible de réactiver le fournisseur: {str(e)}")

    @staticmethod
    def get_fournisseurs_pour_article(article):
        """
        Récupère les fournisseurs pouvant fournir un article.

        Args:
            article: L'article recherché

        Returns:
            QuerySet: Fournisseurs triés par note
        """
        # TODO: Implémenter avec une table de relation Article-Fournisseur
        # Pour l'instant, on retourne tous les fournisseurs actifs triés par note
        return GACFournisseur.objects.filter(
            statut=STATUT_FOURNISSEUR_ACTIF
        ).order_by('-evaluation_moyenne', 'raison_sociale')

    @staticmethod
    def rechercher_fournisseurs(query, statut=None, actif_uniquement=True):
        """
        Recherche de fournisseurs.

        Args:
            query: Terme de recherche (code, raison sociale, NIF)
            statut: Filtrer par statut (optionnel)
            actif_uniquement: Ne retourner que les fournisseurs actifs

        Returns:
            QuerySet: Fournisseurs correspondants
        """
        queryset = GACFournisseur.objects.all()

        if actif_uniquement:
            queryset = queryset.filter(statut=STATUT_FOURNISSEUR_ACTIF)
        elif statut:
            queryset = queryset.filter(statut=statut)

        if query:
            queryset = queryset.filter(
                Q(code__icontains=query) |
                Q(raison_sociale__icontains=query) |
                Q(nif__icontains=query) |
                Q(email__icontains=query)
            )

        return queryset.order_by('raison_sociale')

    @staticmethod
    def get_statistiques_fournisseur(fournisseur, date_debut=None, date_fin=None):
        """
        Récupère les statistiques sur un fournisseur.

        Args:
            fournisseur: Le fournisseur
            date_debut: Date de début de la période (optionnel)
            date_fin: Date de fin de la période (optionnel)

        Returns:
            dict: Statistiques du fournisseur
        """
        # Récupérer les bons de commande du fournisseur
        queryset = GACBonCommande.objects.filter(fournisseur=fournisseur)

        if date_debut:
            queryset = queryset.filter(date_creation__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_creation__lte=date_fin)

        # Nombre de commandes
        nombre_commandes = queryset.count()

        # Montants
        stats_montants = queryset.aggregate(
            montant_total=Sum('montant_total_ttc'),
            montant_moyen=Avg('montant_total_ttc')
        )
        montant_total = stats_montants['montant_total'] or Decimal('0')
        montant_moyen = stats_montants['montant_moyen'] or Decimal('0')

        # Taux de livraison à temps
        # BC confirmés avec date de livraison
        bc_avec_dates = queryset.filter(
            date_livraison_souhaitee__isnull=False,
            date_reception_complete__isnull=False
        )

        nombre_livraisons = bc_avec_dates.count()
        if nombre_livraisons > 0:
            livraisons_temps = bc_avec_dates.filter(
                date_reception_complete__lte=models.F('date_livraison_souhaitee')
            ).count()
            taux_livraison_temps = (livraisons_temps / nombre_livraisons) * 100
        else:
            taux_livraison_temps = 0

        # Délai moyen de livraison (en jours)
        delais = []
        for bc in bc_avec_dates:
            if bc.date_emission and bc.date_reception_complete:
                delai = (bc.date_reception_complete - bc.date_emission.date()).days
                delais.append(delai)

        delai_moyen_livraison = sum(delais) / len(delais) if delais else 0

        return {
            'nombre_commandes': nombre_commandes,
            'montant_total_commandes': montant_total,
            'montant_moyen_commande': montant_moyen,
            'taux_livraison_temps': round(taux_livraison_temps, 2),
            'delai_moyen_livraison_jours': round(delai_moyen_livraison, 1),
            'evaluation_moyenne': fournisseur.evaluation_moyenne or 0,
        }

    @staticmethod
    def get_top_fournisseurs(limit=10, date_debut=None, date_fin=None):
        """
        Récupère les meilleurs fournisseurs.

        Args:
            limit: Nombre de fournisseurs à retourner
            date_debut: Date de début de la période (optionnel)
            date_fin: Date de fin de la période (optionnel)

        Returns:
            list: Top fournisseurs avec leurs statistiques
        """
        fournisseurs = GACFournisseur.objects.filter(
            statut=STATUT_FOURNISSEUR_ACTIF
        )

        # Annoter avec le nombre de commandes et montant total
        queryset_bc = GACBonCommande.objects.all()
        if date_debut:
            queryset_bc = queryset_bc.filter(date_creation__gte=date_debut)
        if date_fin:
            queryset_bc = queryset_bc.filter(date_creation__lte=date_fin)

        fournisseurs = fournisseurs.annotate(
            nombre_commandes=Count('bons_commande', filter=queryset_bc.query.where),
            montant_total=Sum('bons_commande__montant_total_ttc', filter=queryset_bc.query.where)
        ).filter(
            nombre_commandes__gt=0
        ).order_by('-montant_total')[:limit]

        return [
            {
                'fournisseur': f.raison_sociale,
                'code': f.code,
                'nombre_commandes': f.nombre_commandes,
                'montant_total': f.montant_total or Decimal('0'),
                'evaluation': f.evaluation_moyenne or 0,
            }
            for f in fournisseurs
        ]
