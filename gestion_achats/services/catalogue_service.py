"""
Service métier pour la gestion du catalogue.

Ce service encapsule toute la logique métier liée au catalogue produits,
incluant la gestion des articles, des catégories et des associations articles-fournisseurs.
"""

import logging
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count

from gestion_achats.models import (
    GACArticle,
    GACCategorie,
    GACFournisseur,
    GACHistorique,
)
from gestion_achats.constants import (
    TAUX_TVA_DEFAUT,
)
from gestion_achats.exceptions import (
    ValidationError as GACValidationError,
)

logger = logging.getLogger(__name__)


class CatalogueService:
    """Service pour la gestion du catalogue produits."""

    @staticmethod
    @transaction.atomic
    def creer_categorie(nom, parent=None, description=None, cree_par=None):
        """
        Crée une catégorie de produits.

        Args:
            nom: Nom de la catégorie
            parent: Catégorie parente (optionnel, pour hiérarchie)
            description: Description de la catégorie (optionnel)
            cree_par: Utilisateur créateur (optionnel)

        Returns:
            GACCategorie: La catégorie créée

        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Vérifier l'unicité du nom au même niveau
            if parent:
                if GACCategorie.objects.filter(nom=nom, parent=parent).exists():
                    raise GACValidationError(
                        f"Une catégorie '{nom}' existe déjà sous '{parent.nom}'"
                    )
            else:
                if GACCategorie.objects.filter(nom=nom, parent__isnull=True).exists():
                    raise GACValidationError(
                        f"Une catégorie racine '{nom}' existe déjà"
                    )

            # Créer la catégorie
            categorie = GACCategorie.objects.create(
                nom=nom,
                parent=parent,
                description=description,
                cree_par=cree_par
            )

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=categorie,
                action='CREATION',
                utilisateur=cree_par,
                details=f"Création de la catégorie '{nom}'" +
                       (f" sous '{parent.nom}'" if parent else " (racine)")
            )

            logger.info(f"Catégorie '{nom}' créée" + (f" sous '{parent.nom}'" if parent else ""))

            return categorie

        except GACValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création de la catégorie: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def creer_article(reference, designation, categorie, prix_unitaire, unite,
                     taux_tva=None, description=None, specifications_techniques=None,
                     cree_par=None):
        """
        Crée un article dans le catalogue.

        Args:
            reference: Référence unique de l'article
            designation: Désignation de l'article
            categorie: Catégorie de l'article
            prix_unitaire: Prix unitaire HT
            unite: Unité de mesure
            taux_tva: Taux de TVA (optionnel, défaut: TAUX_TVA_DEFAUT)
            description: Description de l'article (optionnel)
            specifications_techniques: Spécifications techniques (optionnel)
            cree_par: Utilisateur créateur (optionnel)

        Returns:
            GACArticle: L'article créé

        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Vérifier l'unicité de la référence
            if GACArticle.objects.filter(reference=reference).exists():
                raise GACValidationError(
                    f"Un article avec la référence '{reference}' existe déjà"
                )

            # Valider le prix
            if prix_unitaire < 0:
                raise GACValidationError("Le prix unitaire ne peut pas être négatif")

            # Taux TVA par défaut
            if taux_tva is None:
                taux_tva = TAUX_TVA_DEFAUT

            # Créer l'article
            article = GACArticle.objects.create(
                reference=reference,
                designation=designation,
                categorie=categorie,
                prix_unitaire=prix_unitaire,
                unite=unite,
                taux_tva=taux_tva,
                description=description,
                specifications_techniques=specifications_techniques,
                statut='ACTIF',
                cree_par=cree_par
            )

            # Créer l'historique
            GACHistorique.enregistrer_action(
                objet=article,
                action='CREATION',
                utilisateur=cree_par,
                details=f"Création de l'article '{reference}' - {designation} ({prix_unitaire} €)"
            )

            logger.info(f"Article '{reference}' créé: {designation}")

            return article

        except GACValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'article: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def modifier_article(article, utilisateur, **kwargs):
        """
        Modifie un article existant.

        Args:
            article: L'article à modifier
            utilisateur: L'utilisateur qui modifie
            **kwargs: Les champs à modifier

        Returns:
            GACArticle: L'article modifié
        """
        try:
            modifications = []

            for field, value in kwargs.items():
                if hasattr(article, field):
                    old_value = getattr(article, field)
                    if old_value != value:
                        setattr(article, field, value)
                        modifications.append(f"{field}: {old_value} → {value}")

            article.modifie_par = utilisateur
            article.save()

            if modifications:
                # Créer l'historique
                GACHistorique.enregistrer_action(
                    objet=article,
                    action='MODIFICATION',
                    utilisateur=utilisateur,
                    details=f"Modification de l'article. " + ", ".join(modifications)
                )

                logger.info(f"Article '{article.reference}' modifié par {utilisateur}")

            return article

        except Exception as e:
            logger.error(f"Erreur lors de la modification de l'article: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def desactiver_article(article, utilisateur, motif=None):
        """
        Désactive un article (le rend non commandable).

        Args:
            article: L'article à désactiver
            utilisateur: L'utilisateur qui désactive
            motif: Motif de la désactivation (optionnel)

        Returns:
            GACArticle: L'article désactivé
        """
        try:
            article.actif = False
            article.save()

            details = f"Article désactivé par {utilisateur}"
            if motif:
                details += f". Motif: {motif}"

            GACHistorique.enregistrer_action(
                objet=article,
                action='DESACTIVATION',
                utilisateur=utilisateur,
                details=details
            )

            logger.info(f"Article '{article.reference}' désactivé")

            return article

        except Exception as e:
            logger.error(f"Erreur lors de la désactivation de l'article: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def reactiver_article(article, utilisateur):
        """
        Réactive un article désactivé.

        Args:
            article: L'article à réactiver
            utilisateur: L'utilisateur qui réactive

        Returns:
            GACArticle: L'article réactivé
        """
        try:
            article.actif = True
            article.save()

            GACHistorique.enregistrer_action(
                objet=article,
                action='REACTIVATION',
                utilisateur=utilisateur,
                details=f"Article réactivé par {utilisateur}"
            )

            logger.info(f"Article '{article.reference}' réactivé")

            return article

        except Exception as e:
            logger.error(f"Erreur lors de la réactivation de l'article: {str(e)}")
            raise

    @staticmethod
    def associer_fournisseur_article(article, fournisseur, prix_fournisseur,
                                     delai_livraison, reference_fournisseur=None,
                                     cree_par=None):
        """
        Associe un fournisseur à un article avec ses conditions.

        Args:
            article: L'article
            fournisseur: Le fournisseur
            prix_fournisseur: Prix proposé par le fournisseur
            delai_livraison: Délai de livraison en jours
            reference_fournisseur: Référence de l'article chez le fournisseur (optionnel)
            cree_par: Utilisateur créateur (optionnel)

        Returns:
            Relation créée

        Note:
            Cette méthode nécessiterait un modèle ArticleFournisseur qui n'est pas
            dans les specs actuelles. Pour l'instant, on retourne None.
            À implémenter si le modèle est ajouté.
        """
        # TODO: Implémenter avec un modèle GACArticleFournisseur si ajouté
        logger.info(
            f"Association article-fournisseur: {article.reference} - {fournisseur.code} "
            f"(prix: {prix_fournisseur} €, délai: {delai_livraison}j)"
        )

        # Pour l'instant, on log seulement
        # Une fois le modèle créé, ajouter:
        # relation = GACArticleFournisseur.objects.create(...)
        # GACHistorique.enregistrer_action(...)

        return None

    @staticmethod
    def rechercher_articles(query, categorie=None, actif_uniquement=True):
        """
        Recherche d'articles dans le catalogue.

        Args:
            query: Terme de recherche (référence, désignation)
            categorie: Filtrer par catégorie (optionnel)
            actif_uniquement: Ne retourner que les articles actifs

        Returns:
            QuerySet: Articles correspondants
        """
        queryset = GACArticle.objects.all()

        if actif_uniquement:
            queryset = queryset.filter(statut='ACTIF')

        if categorie:
            # Recherche dans la catégorie et ses sous-catégories
            categories = CatalogueService._get_categories_et_sous_categories(categorie)
            queryset = queryset.filter(categorie__in=categories)

        if query:
            queryset = queryset.filter(
                Q(reference__icontains=query) |
                Q(designation__icontains=query) |
                Q(description__icontains=query)
            )

        return queryset.order_by('categorie__nom', 'designation')

    @staticmethod
    def _get_categories_et_sous_categories(categorie):
        """
        Récupère une catégorie et toutes ses sous-catégories (récursif).

        Args:
            categorie: La catégorie parente

        Returns:
            list: Liste des catégories (parent + enfants)
        """
        categories = [categorie]

        # Récupérer les enfants directs
        enfants = GACCategorie.objects.filter(parent=categorie)

        # Récursivement pour chaque enfant
        for enfant in enfants:
            categories.extend(
                CatalogueService._get_categories_et_sous_categories(enfant)
            )

        return categories

    @staticmethod
    def get_categories_racines():
        """
        Récupère les catégories de premier niveau (sans parent).

        Returns:
            QuerySet: Catégories racines
        """
        return GACCategorie.objects.filter(parent__isnull=True).order_by('nom')

    @staticmethod
    def get_sous_categories(categorie):
        """
        Récupère les sous-catégories directes d'une catégorie.

        Args:
            categorie: La catégorie parente

        Returns:
            QuerySet: Sous-catégories directes
        """
        return GACCategorie.objects.filter(parent=categorie).order_by('nom')

    @staticmethod
    def get_arborescence_categories():
        """
        Récupère l'arborescence complète des catégories.

        Returns:
            list: Arborescence hiérarchique
        """
        def build_tree(parent=None, level=0):
            categories = GACCategorie.objects.filter(parent=parent).order_by('nom')
            tree = []

            for categorie in categories:
                tree.append({
                    'categorie': categorie,
                    'level': level,
                    'children': build_tree(categorie, level + 1)
                })

            return tree

        return build_tree()

    @staticmethod
    def get_statistiques_catalogue():
        """
        Récupère les statistiques du catalogue.

        Returns:
            dict: Statistiques
        """
        # Nombre total d'articles
        total_articles = GACArticle.objects.count()
        articles_actifs = GACArticle.objects.filter(statut='ACTIF').count()
        articles_inactifs = total_articles - articles_actifs

        # Nombre de catégories
        total_categories = GACCategorie.objects.count()

        # Articles par catégorie
        par_categorie = GACArticle.objects.values(
            'categorie__nom'
        ).annotate(
            nombre=Count('id')
        ).order_by('-nombre')[:10]

        # Prix moyen
        from django.db.models import Avg, Min, Max
        stats_prix = GACArticle.objects.filter(statut='ACTIF').aggregate(
            prix_moyen=Avg('prix_unitaire'),
            prix_min=Min('prix_unitaire'),
            prix_max=Max('prix_unitaire')
        )

        return {
            'total_articles': total_articles,
            'articles_actifs': articles_actifs,
            'articles_inactifs': articles_inactifs,
            'total_categories': total_categories,
            'top_categories': [
                {'nom': item['categorie__nom'], 'nombre': item['nombre']}
                for item in par_categorie
            ],
            'prix_moyen': stats_prix['prix_moyen'] or Decimal('0'),
            'prix_min': stats_prix['prix_min'] or Decimal('0'),
            'prix_max': stats_prix['prix_max'] or Decimal('0'),
        }

    @staticmethod
    def get_articles_populaires(limit=10):
        """
        Récupère les articles les plus commandés.

        Args:
            limit: Nombre d'articles à retourner

        Returns:
            list: Articles populaires avec nombre de commandes
        """
        from gestion_achats.models import GACLigneBonCommande

        # Compter les occurrences dans les lignes de BC
        articles = GACArticle.objects.filter(statut='ACTIF').annotate(
            nombre_commandes=Count('lignes_bon_commande')
        ).filter(
            nombre_commandes__gt=0
        ).order_by('-nombre_commandes')[:limit]

        return [
            {
                'article': article,
                'reference': article.reference,
                'designation': article.designation,
                'nombre_commandes': article.nombre_commandes,
            }
            for article in articles
        ]
