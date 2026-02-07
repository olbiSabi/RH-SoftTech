"""
Modèles de données pour le module Gestion des Achats & Commandes (GAC).
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, EmailValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from employee.models import ZY00
from departement.models import ZDDE
from project_management.models import JRProject
from gestion_achats import constants
from gestion_achats.constants import (
    STATUT_RECEPTION_CHOICES,
    ACTION_CHOICES,
)
from gestion_achats.utils import (
    generer_numero_demande,
    generer_numero_bon_commande,
    generer_numero_reception,
    calculer_montant_ttc,
    calculer_montant_tva,
)


# ==============================================================================
# MODÈLE: GACFournisseur
# ==============================================================================

class GACFournisseur(models.Model):
    """
    Modèle représentant un fournisseur.
    
    Un fournisseur est une entreprise externe qui peut fournir des articles
    et recevoir des bons de commande.
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    code = models.CharField(
        max_length=constants.MAX_LENGTH_CODE,
        unique=True,
        verbose_name="Code fournisseur"
    )
    
    raison_sociale = models.CharField(
        max_length=constants.MAX_LENGTH_NOM,
        verbose_name="Raison sociale"
    )

    nif = models.CharField(
        max_length=constants.MAX_LENGTH_NIF,
        blank=True,
        null=True,
        verbose_name="NIF (Numéro d'Identification Fiscale)",
        help_text="9 à 10 chiffres (optionnel)"
    )

    numero_tva = models.CharField(
        max_length=constants.MAX_LENGTH_TVA,
        blank=True,
        verbose_name="Numéro de TVA intracommunautaire"
    )
    
    # Coordonnées
    email = models.EmailField(
        max_length=constants.MAX_LENGTH_EMAIL,
        validators=[EmailValidator()],
        verbose_name="Email"
    )
    
    telephone = models.CharField(
        max_length=constants.MAX_LENGTH_TELEPHONE,
        verbose_name="Téléphone"
    )
    
    fax = models.CharField(
        max_length=constants.MAX_LENGTH_TELEPHONE,
        blank=True,
        verbose_name="Fax"
    )
    
    # Adresse
    adresse = models.TextField(
        verbose_name="Adresse"
    )
    
    code_postal = models.CharField(
        max_length=10,
        verbose_name="Code postal"
    )
    
    ville = models.CharField(
        max_length=100,
        verbose_name="Ville"
    )
    
    pays = models.CharField(
        max_length=100,
        default="Togo",
        verbose_name="Pays"
    )
    
    # Contact principal
    nom_contact = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nom du contact"
    )
    
    email_contact = models.EmailField(
        max_length=constants.MAX_LENGTH_EMAIL,
        blank=True,
        verbose_name="Email du contact"
    )
    
    telephone_contact = models.CharField(
        max_length=constants.MAX_LENGTH_TELEPHONE,
        blank=True,
        verbose_name="Téléphone du contact"
    )
    
    # Informations commerciales
    conditions_paiement = models.CharField(
        max_length=50,
        choices=constants.PAIEMENT_CHOICES,
        default=constants.PAIEMENT_30_JOURS,
        verbose_name="Conditions de paiement"
    )
    
    iban = models.CharField(
        max_length=constants.MAX_LENGTH_IBAN,
        blank=True,
        verbose_name="IBAN"
    )
    
    # Évaluation
    evaluation_moyenne = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Évaluation moyenne"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=constants.STATUT_FOURNISSEUR_CHOICES,
        default=constants.STATUT_FOURNISSEUR_ACTIF,
        verbose_name="Statut"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fournisseurs_crees',
        verbose_name="Créé par"
    )
    
    # Relations inverses
    pieces_jointes = GenericRelation('GACPieceJointe')
    historique = GenericRelation('GACHistorique')
    
    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['raison_sociale']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['nif']),
            models.Index(fields=['statut']),
        ]
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le code fournisseur."""
        if not self.code:
            from gestion_achats.utils import generer_code_fournisseur
            self.code = generer_code_fournisseur()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.raison_sociale}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('gestion_achats:fournisseur_detail', args=[self.uuid])


# ==============================================================================
# MODÈLE: GACCategorie
# ==============================================================================

class GACCategorie(models.Model):
    """
    Modèle représentant une catégorie de produits hiérarchique.
    
    Les catégories peuvent avoir des sous-catégories (arbre hiérarchique).
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    nom = models.CharField(
        max_length=constants.MAX_LENGTH_NOM,
        verbose_name="Nom"
    )
    
    code = models.CharField(
        max_length=constants.MAX_LENGTH_CODE,
        unique=True,
        verbose_name="Code"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sous_categories',
        verbose_name="Catégorie parente"
    )
    
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )

    cree_par = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_creees_gac',
        verbose_name="Créé par"
    )

    modifie_par = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_modifiees_gac',
        verbose_name="Modifié par"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['ordre', 'nom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['parent']),
        ]

    def save(self, *args, **kwargs):
        """Génère automatiquement le code de catégorie."""
        if not self.code:
            from gestion_achats.utils import generer_code_categorie
            self.code = generer_code_categorie()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.nom} > {self.nom}"
        return self.nom
    
    def get_chemin_complet(self):
        """Retourne le chemin complet de la catégorie."""
        if self.parent:
            return f"{self.parent.get_chemin_complet()} > {self.nom}"
        return self.nom


# ==============================================================================
# MODÈLE: GACArticle
# ==============================================================================

class GACArticle(models.Model):
    """
    Modèle représentant un article du catalogue.
    
    Un article peut être commandé auprès de un ou plusieurs fournisseurs.
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    reference = models.CharField(
        max_length=constants.MAX_LENGTH_REFERENCE,
        unique=True,
        verbose_name="Référence"
    )
    
    designation = models.CharField(
        max_length=constants.MAX_LENGTH_NOM,
        verbose_name="Désignation"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    categorie = models.ForeignKey(
        GACCategorie,
        on_delete=models.PROTECT,
        related_name='articles',
        verbose_name="Catégorie"
    )
    
    # Caractéristiques
    unite = models.CharField(
        max_length=20,
        choices=constants.UNITE_CHOICES,
        default=constants.UNITE_PIECE,
        verbose_name="Unité"
    )
    
    prix_unitaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire HT"
    )
    
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(str(constants.TAUX_TVA_DEFAUT)),
        verbose_name="Taux de TVA (%)"
    )
    
    # Fournisseurs
    fournisseurs = models.ManyToManyField(
        GACFournisseur,
        through='GACArticleFournisseur',
        related_name='articles',
        verbose_name="Fournisseurs"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=constants.STATUT_ARTICLE_CHOICES,
        default=constants.STATUT_ARTICLE_ACTIF,
        verbose_name="Statut"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles_crees',
        verbose_name="Créé par"
    )
    
    # Relations inverses
    pieces_jointes = GenericRelation('GACPieceJointe')
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['reference']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['categorie']),
            models.Index(fields=['statut']),
        ]
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le code article (référence)."""
        if not self.reference:
            from gestion_achats.utils import generer_code_article
            self.reference = generer_code_article()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.designation}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('gestion_achats:article_detail', args=[self.uuid])

    def calculer_prix_ttc(self):
        """Calcule le prix TTC."""
        return calculer_montant_ttc(self.prix_unitaire, self.taux_tva)


# ==============================================================================
# MODÈLE: GACArticleFournisseur (Table intermédiaire)
# ==============================================================================

class GACArticleFournisseur(models.Model):
    """
    Table intermédiaire entre Article et Fournisseur.
    
    Permet de stocker les conditions spécifiques par fournisseur.
    """
    
    article = models.ForeignKey(
        GACArticle,
        on_delete=models.CASCADE,
        verbose_name="Article"
    )
    
    fournisseur = models.ForeignKey(
        GACFournisseur,
        on_delete=models.CASCADE,
        verbose_name="Fournisseur"
    )
    
    reference_fournisseur = models.CharField(
        max_length=constants.MAX_LENGTH_REFERENCE,
        blank=True,
        verbose_name="Référence fournisseur"
    )
    
    prix_fournisseur = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix fournisseur HT"
    )
    
    delai_livraison = models.IntegerField(
        default=0,
        verbose_name="Délai de livraison (jours)"
    )
    
    fournisseur_principal = models.BooleanField(
        default=False,
        verbose_name="Fournisseur principal"
    )
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Article-Fournisseur"
        verbose_name_plural = "Articles-Fournisseurs"
        unique_together = ['article', 'fournisseur']
    
    def __str__(self):
        return f"{self.article.reference} chez {self.fournisseur.code}"


# ==============================================================================
# MODÈLE: GACBudget
# ==============================================================================

class GACBudget(models.Model):
    """
    Modèle représentant une enveloppe budgétaire.
    
    Permet de contrôler les dépenses et de générer des alertes.
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    code = models.CharField(
        max_length=constants.MAX_LENGTH_CODE,
        unique=True,
        verbose_name="Code budget"
    )
    
    libelle = models.CharField(
        max_length=constants.MAX_LENGTH_NOM,
        verbose_name="Libellé"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Montants
    montant_initial = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant initial"
    )
    
    montant_engage = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant engagé"
    )
    
    montant_commande = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant commandé"
    )
    
    montant_consomme = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant consommé"
    )
    
    # Périodes
    exercice = models.IntegerField(
        verbose_name="Exercice (année)"
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début"
    )
    
    date_fin = models.DateField(
        verbose_name="Date de fin"
    )
    
    # Responsable
    gestionnaire = models.ForeignKey(
        ZY00,
        on_delete=models.PROTECT,
        related_name='budgets_geres',
        verbose_name="Gestionnaire"
    )
    
    departement = models.ForeignKey(
        ZDDE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='budgets',
        verbose_name="Département"
    )
    
    # Alertes
    seuil_alerte_1 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(str(constants.SEUIL_ALERTE_BUDGET_1)),
        verbose_name="Seuil alerte 1 (%)"
    )
    
    seuil_alerte_2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(str(constants.SEUIL_ALERTE_BUDGET_2)),
        verbose_name="Seuil alerte 2 (%)"
    )
    
    alerte_1_envoyee = models.BooleanField(
        default=False,
        verbose_name="Alerte 1 envoyée"
    )
    
    alerte_2_envoyee = models.BooleanField(
        default=False,
        verbose_name="Alerte 2 envoyée"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='budgets_crees',
        verbose_name="Créé par"
    )
    
    # Relations inverses
    historique = GenericRelation('GACHistorique')
    
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        ordering = ['-exercice', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['exercice']),
            models.Index(fields=['gestionnaire']),
        ]
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le code budget."""
        if not self.code:
            from gestion_achats.utils import generer_code_budget
            self.code = generer_code_budget()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.libelle} ({self.exercice})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('gestion_achats:budget_detail', args=[self.uuid])
    
    def montant_disponible(self):
        """Calcule le montant disponible."""
        total_utilise = self.montant_engage + self.montant_commande + self.montant_consomme
        return self.montant_initial - total_utilise
    
    def taux_consommation(self):
        """Calcule le taux de consommation en %."""
        if self.montant_initial == 0:
            return Decimal('0.00')
        
        total_utilise = self.montant_engage + self.montant_commande + self.montant_consomme
        taux = (total_utilise / self.montant_initial) * Decimal('100')
        return taux.quantize(Decimal('0.01'))


# Suite dans la partie 2...

# ==============================================================================
# MODÈLE: GACDemandeAchat
# ==============================================================================

class GACDemandeAchat(models.Model):
    """
    Modèle représentant une demande d'achat.
    
    Workflow: BROUILLON → SOUMISE → VALIDEE_N1 → VALIDEE_N2 → CONVERTIE_BC
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    numero = models.CharField(
        max_length=constants.MAX_LENGTH_NUMERO,
        unique=True,
        editable=False,
        verbose_name="Numéro"
    )
    
    # Informations générales
    objet = models.CharField(
        max_length=constants.MAX_LENGTH_NOM,
        verbose_name="Objet"
    )
    
    justification = models.TextField(
        verbose_name="Justification"
    )
    
    priorite = models.CharField(
        max_length=20,
        choices=constants.PRIORITE_CHOICES,
        default=constants.PRIORITE_NORMALE,
        verbose_name="Priorité"
    )
    
    # Demandeur
    demandeur = models.ForeignKey(
        ZY00,
        on_delete=models.PROTECT,
        related_name='demandes_achat',
        verbose_name="Demandeur"
    )
    
    departement = models.ForeignKey(
        ZDDE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_achat',
        verbose_name="Département"
    )
    
    projet = models.ForeignKey(
        JRProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_achat',
        verbose_name="Projet lié"
    )
    
    # Budget
    budget = models.ForeignKey(
        GACBudget,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes',
        verbose_name="Budget"
    )
    
    # Workflow de validation
    statut = models.CharField(
        max_length=20,
        choices=constants.STATUT_DEMANDE_CHOICES,
        default=constants.STATUT_DEMANDE_BROUILLON,
        verbose_name="Statut"
    )
    
    # Validation N1
    validateur_n1 = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_a_valider_n1',
        verbose_name="Validateur N1"
    )
    
    date_validation_n1 = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date validation N1"
    )
    
    commentaire_validation_n1 = models.TextField(
        blank=True,
        verbose_name="Commentaire validation N1"
    )
    
    # Validation N2
    validateur_n2 = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_a_valider_n2',
        verbose_name="Validateur N2"
    )
    
    date_validation_n2 = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date validation N2"
    )
    
    commentaire_validation_n2 = models.TextField(
        blank=True,
        verbose_name="Commentaire validation N2"
    )
    
    # Refus/Annulation
    motif_refus = models.TextField(
        blank=True,
        verbose_name="Motif de refus"
    )
    
    date_refus = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de refus"
    )
    
    motif_annulation = models.TextField(
        blank=True,
        verbose_name="Motif d'annulation"
    )
    
    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'annulation"
    )
    
    # Conversion en BC
    bon_commande = models.ForeignKey(
        'GACBonCommande',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demande_origine',
        verbose_name="Bon de commande"
    )
    
    # Montants (calculés automatiquement)
    montant_total_ht = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total HT"
    )
    
    montant_total_tva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total TVA"
    )
    
    montant_total_ttc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total TTC"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    date_soumission = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de soumission"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='demandes_creees',
        verbose_name="Créé par"
    )
    
    # Relations inverses
    pieces_jointes = GenericRelation('GACPieceJointe')
    historique = GenericRelation('GACHistorique')
    
    class Meta:
        verbose_name = "Demande d'achat"
        verbose_name_plural = "Demandes d'achat"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['demandeur']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.objet}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = generer_numero_demande()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('gestion_achats:demande_detail', args=[self.uuid])
    
    def calculer_totaux(self):
        """Calcule les totaux HT, TVA et TTC."""
        total_ht = Decimal('0.00')
        total_tva = Decimal('0.00')
        
        for ligne in self.lignes.all():
            total_ht += ligne.montant
            total_tva += ligne.montant_tva
        
        self.montant_total_ht = total_ht
        self.montant_total_tva = total_tva
        self.montant_total_ttc = total_ht + total_tva
        self.save(update_fields=['montant_total_ht', 'montant_total_tva', 'montant_total_ttc'])

    def get_statut_badge_class(self):
        """Retourne la classe CSS Bootstrap pour le badge de statut."""
        statut_classes = {
            'BROUILLON': 'secondary',
            'SOUMISE': 'info',
            'VALIDEE_N1': 'primary',
            'VALIDEE_N2': 'success',
            'CONVERTIE_BC': 'success',
            'REFUSEE': 'danger',
            'ANNULEE': 'warning',
        }
        return statut_classes.get(self.statut, 'secondary')

    def get_priorite_badge_class(self):
        """Retourne la classe CSS Bootstrap pour le badge de priorité."""
        priorite_classes = {
            'BASSE': 'secondary',
            'NORMALE': 'info',
            'HAUTE': 'warning',
            'URGENTE': 'danger',
        }
        return priorite_classes.get(self.priorite, 'info')


# ==============================================================================
# MODÈLE: GACLigneDemandeAchat
# ==============================================================================

class GACLigneDemandeAchat(models.Model):
    """
    Modèle représentant une ligne de demande d'achat.
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    demande_achat = models.ForeignKey(
        GACDemandeAchat,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name="Demande d'achat"
    )
    
    article = models.ForeignKey(
        GACArticle,
        on_delete=models.PROTECT,
        related_name='lignes_demande',
        verbose_name="Article"
    )
    
    quantite = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantité"
    )
    
    prix_unitaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire HT"
    )
    
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(str(constants.TAUX_TVA_DEFAUT)),
        verbose_name="Taux TVA (%)"
    )
    
    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant HT"
    )
    
    montant_tva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant TVA"
    )
    
    montant_ttc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant TTC"
    )
    
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre"
    )
    
    class Meta:
        verbose_name = "Ligne de demande d'achat"
        verbose_name_plural = "Lignes de demandes d'achat"
        ordering = ['ordre', 'id']
    
    def __str__(self):
        return f"{self.article.reference} x {self.quantite}"
    
    def save(self, *args, **kwargs):
        # Calculer les montants
        self.montant = (self.quantite * self.prix_unitaire).quantize(Decimal('0.01'))
        self.montant_tva = calculer_montant_tva(self.montant, self.taux_tva)
        self.montant_ttc = self.montant + self.montant_tva
        super().save(*args, **kwargs)
        
        # Recalculer les totaux de la demande
        self.demande_achat.calculer_totaux()


# Suite dans la partie 3 (BC, Réception)...

# ==============================================================================
# MODÈLE: GACBonCommande
# ==============================================================================

class GACBonCommande(models.Model):
    """
    Modèle représentant un bon de commande.
    
    Workflow: BROUILLON → EMIS → ENVOYE → CONFIRME → RECU_PARTIEL/RECU_COMPLET
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    numero = models.CharField(
        max_length=constants.MAX_LENGTH_NUMERO,
        unique=True,
        editable=False,
        verbose_name="Numéro"
    )
    
    # Origine
    demande_achat = models.ForeignKey(
        GACDemandeAchat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bons_commande',
        verbose_name="Demande d'achat"
    )
    
    # Fournisseur
    fournisseur = models.ForeignKey(
        GACFournisseur,
        on_delete=models.PROTECT,
        related_name='bons_commande',
        verbose_name="Fournisseur"
    )
    
    # Acheteur
    acheteur = models.ForeignKey(
        ZY00,
        on_delete=models.PROTECT,
        related_name='bons_commande_crees',
        verbose_name="Acheteur"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=constants.STATUT_BC_CHOICES,
        default=constants.STATUT_BC_BROUILLON,
        verbose_name="Statut"
    )
    
    # Livraison
    date_livraison_souhaitee = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de livraison souhaitée"
    )
    
    date_livraison_confirmee = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de livraison confirmée"
    )
    
    adresse_livraison = models.TextField(
        blank=True,
        verbose_name="Adresse de livraison"
    )
    
    # Paiement
    conditions_paiement = models.CharField(
        max_length=50,
        choices=constants.PAIEMENT_CHOICES,
        blank=True,
        verbose_name="Conditions de paiement"
    )
    
    # Confirmation fournisseur
    numero_confirmation_fournisseur = models.CharField(
        max_length=constants.MAX_LENGTH_NUMERO,
        blank=True,
        verbose_name="Numéro de confirmation fournisseur"
    )
    
    # Montants
    montant_total_ht = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total HT"
    )
    
    montant_total_tva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total TVA"
    )
    
    montant_total_ttc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total TTC"
    )
    
    # PDF
    fichier_pdf = models.FileField(
        upload_to='gestion_achats/bons_commande/',
        blank=True,
        null=True,
        verbose_name="Fichier PDF"
    )
    
    # Envoi
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'envoi"
    )
    
    email_envoi = models.EmailField(
        max_length=constants.MAX_LENGTH_EMAIL,
        blank=True,
        verbose_name="Email d'envoi"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    date_emission = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'émission"
    )
    
    date_reception_complete = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de réception complète"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bc_crees',
        verbose_name="Créé par"
    )
    
    # Annulation
    motif_annulation = models.TextField(
        blank=True,
        verbose_name="Motif d'annulation"
    )
    
    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'annulation"
    )
    
    # Relations inverses
    pieces_jointes = GenericRelation('GACPieceJointe')
    historique = GenericRelation('GACHistorique')
    
    class Meta:
        verbose_name = "Bon de commande"
        verbose_name_plural = "Bons de commande"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['fournisseur']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.fournisseur.raison_sociale}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = generer_numero_bon_commande()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('gestion_achats:bon_commande_detail', args=[self.uuid])
    
    def calculer_totaux(self):
        """Calcule les totaux HT, TVA et TTC."""
        total_ht = Decimal('0.00')
        total_tva = Decimal('0.00')
        
        for ligne in self.lignes.all():
            total_ht += ligne.montant
            total_tva += ligne.montant_tva
        
        self.montant_total_ht = total_ht
        self.montant_total_tva = total_tva
        self.montant_total_ttc = total_ht + total_tva
        self.save(update_fields=['montant_total_ht', 'montant_total_tva', 'montant_total_ttc'])
    
    def est_totalement_recu(self):
        """Vérifie si toutes les lignes sont totalement reçues."""
        for ligne in self.lignes.all():
            if ligne.quantite_recue < ligne.quantite_commandee:
                return False
        return True

    def get_statut_badge_class(self):
        """Retourne la classe CSS Bootstrap pour le badge de statut."""
        statut_classes = {
            'BROUILLON': 'secondary',
            'EMIS': 'primary',
            'ENVOYE': 'info',
            'CONFIRME': 'success',
            'RECU_PARTIEL': 'warning',
            'RECU_COMPLET': 'success',
            'ANNULE': 'danger',
        }
        return statut_classes.get(self.statut, 'secondary')


# ==============================================================================
# MODÈLE: GACLigneBonCommande
# ==============================================================================

class GACLigneBonCommande(models.Model):
    """
    Modèle représentant une ligne de bon de commande.
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    bon_commande = models.ForeignKey(
        GACBonCommande,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name="Bon de commande"
    )
    
    article = models.ForeignKey(
        GACArticle,
        on_delete=models.PROTECT,
        related_name='lignes_bc',
        verbose_name="Article"
    )
    
    quantite_commandee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantité commandée"
    )
    
    quantite_recue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Quantité reçue"
    )
    
    prix_unitaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire HT"
    )
    
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(str(constants.TAUX_TVA_DEFAUT)),
        verbose_name="Taux TVA (%)"
    )
    
    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant HT"
    )
    
    montant_tva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant TVA"
    )
    
    montant_ttc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant TTC"
    )
    
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre"
    )
    
    class Meta:
        verbose_name = "Ligne de bon de commande"
        verbose_name_plural = "Lignes de bons de commande"
        ordering = ['ordre', 'id']
    
    def __str__(self):
        return f"{self.article.reference} x {self.quantite_commandee}"
    
    def save(self, *args, **kwargs):
        # Calculer les montants
        self.montant = (self.quantite_commandee * self.prix_unitaire).quantize(Decimal('0.01'))
        self.montant_tva = calculer_montant_tva(self.montant, self.taux_tva)
        self.montant_ttc = self.montant + self.montant_tva
        super().save(*args, **kwargs)
        
        # Recalculer les totaux du BC
        self.bon_commande.calculer_totaux()


# Suite partie 4 (Réception, PieceJointe, Historique)...

class GACReception(models.Model):
    """
    Modèle pour gérer les réceptions de marchandises.
    Une réception peut être partielle ou complète.
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant unique"
    )
    numero = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Numéro de réception"
    )
    bon_commande = models.ForeignKey(
        'GACBonCommande',
        on_delete=models.PROTECT,
        related_name='receptions',
        verbose_name="Bon de commande"
    )
    receptionnaire = models.ForeignKey(
        ZY00,
        on_delete=models.PROTECT,
        related_name='receptions_gac',
        verbose_name="Réceptionnaire"
    )
    date_reception = models.DateField(
        verbose_name="Date de réception"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_RECEPTION_CHOICES,
        default='BROUILLON',
        verbose_name="Statut"
    )
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    bon_livraison_fournisseur = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="N° bon de livraison fournisseur"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    validateur = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receptions_validees_gac',
        verbose_name="Validateur"
    )

    # Conformité
    conforme = models.BooleanField(
        default=True,
        verbose_name="Réception conforme"
    )

    # Annulation
    motif_annulation = models.TextField(
        blank=True,
        verbose_name="Motif d'annulation"
    )

    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'annulation"
    )

    # Métadonnées
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receptions_creees_gac',
        verbose_name="Créé par"
    )

    # Relations inverses
    pieces_jointes = GenericRelation(
        'GACPieceJointe',
        related_query_name='reception'
    )
    historique = GenericRelation(
        'GACHistorique',
        related_query_name='reception'
    )

    @property
    def id(self):
        """Alias pour pk, nécessaire pour GenericRelation."""
        return self.pk

    class Meta:
        verbose_name = "Réception"
        verbose_name_plural = "Réceptions"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['bon_commande', 'statut']),
            models.Index(fields=['date_reception']),
        ]

    def __str__(self):
        return f"{self.numero} - {self.bon_commande.numero}"

    def save(self, *args, **kwargs):
        """Génère automatiquement le numéro de réception."""
        if not self.numero:
            self.numero = generer_numero_reception()
        super().save(*args, **kwargs)

    def est_complete(self):
        """
        Vérifie si toutes les lignes du bon de commande ont été totalement reçues.
        
        Returns:
            bool: True si la réception est complète, False sinon
        """
        for ligne_bc in self.bon_commande.lignes.all():
            quantite_totale_recue = sum(
                ligne.quantite_acceptee 
                for reception in self.bon_commande.receptions.filter(statut='VALIDEE')
                for ligne in reception.lignes.filter(ligne_bon_commande=ligne_bc)
            )
            if quantite_totale_recue < ligne_bc.quantite_commandee:
                return False
        return True

    def valider(self, user):
        """
        Valide la réception et met à jour les quantités reçues du bon de commande.
        
        Args:
            user: L'utilisateur qui valide la réception
            
        Raises:
            ValidationError: Si la réception n'est pas au statut BROUILLON
        """
        if self.statut != 'BROUILLON':
            raise ValidationError("Seules les réceptions au statut BROUILLON peuvent être validées")
        
        self.statut = 'VALIDEE'
        self.date_validation = timezone.now()
        self.validateur = user
        self.save()
        
        # Mettre à jour les quantités reçues du bon de commande
        for ligne_reception in self.lignes.all():
            ligne_bc = ligne_reception.ligne_bon_commande
            ligne_bc.quantite_recue += ligne_reception.quantite_acceptee
            ligne_bc.save()


class GACLigneReception(models.Model):
    """
    Ligne d'une réception avec détail des quantités reçues, acceptées et refusées.
    """
    reception = models.ForeignKey(
        GACReception,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name="Réception"
    )
    ligne_bon_commande = models.ForeignKey(
        GACLigneBonCommande,
        on_delete=models.PROTECT,
        related_name='lignes_reception',
        verbose_name="Ligne bon de commande"
    )
    quantite_recue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantité reçue"
    )
    quantite_acceptee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Quantité acceptée"
    )
    quantite_refusee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Quantité refusée"
    )
    motif_refus = models.TextField(
        blank=True,
        verbose_name="Motif de refus"
    )

    # Conformité
    conforme = models.BooleanField(
        default=True,
        verbose_name="Ligne conforme"
    )

    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )

    commentaire_reception = models.TextField(
        blank=True,
        verbose_name="Commentaire de réception"
    )

    class Meta:
        verbose_name = "Ligne de réception"
        verbose_name_plural = "Lignes de réception"
        ordering = ['id']
        unique_together = [['reception', 'ligne_bon_commande']]

    def __str__(self):
        return f"{self.reception.numero} - {self.ligne_bon_commande.article.designation}"

    def clean(self):
        """Valide que quantité acceptée + refusée = quantité reçue."""
        super().clean()
        if self.quantite_acceptee + self.quantite_refusee != self.quantite_recue:
            raise ValidationError(
                "La somme des quantités acceptée et refusée doit être égale à la quantité reçue"
            )
        
        # Vérifier qu'on ne dépasse pas la quantité commandée
        quantite_deja_recue = sum(
            ligne.quantite_acceptee 
            for ligne in self.ligne_bon_commande.lignes_reception.exclude(pk=self.pk)
            if ligne.reception.statut == 'VALIDEE'
        )
        if quantite_deja_recue + self.quantite_acceptee > self.ligne_bon_commande.quantite_commandee:
            raise ValidationError(
                f"La quantité totale reçue ({quantite_deja_recue + self.quantite_acceptee}) "
                f"dépasse la quantité commandée ({self.ligne_bon_commande.quantite_commandee})"
            )

    def save(self, *args, **kwargs):
        """Valide avant sauvegarde."""
        self.full_clean()
        super().save(*args, **kwargs)


# ==============================================================================
# MODÈLE: GACBonRetour
# ==============================================================================

class GACBonRetour(models.Model):
    """
    Modèle pour gérer les bons de retour fournisseur.
    Créé suite à une réception non conforme pour retourner des articles défectueux.
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant unique"
    )

    numero = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Numéro de bon de retour"
    )

    reception = models.ForeignKey(
        GACReception,
        on_delete=models.PROTECT,
        related_name='bons_retour',
        verbose_name="Réception concernée"
    )

    bon_commande = models.ForeignKey(
        'GACBonCommande',
        on_delete=models.PROTECT,
        related_name='bons_retour',
        verbose_name="Bon de commande"
    )

    fournisseur = models.ForeignKey(
        'GACFournisseur',
        on_delete=models.PROTECT,
        related_name='bons_retour',
        verbose_name="Fournisseur"
    )

    statut = models.CharField(
        max_length=20,
        choices=constants.STATUT_RETOUR_CHOICES,
        default=constants.STATUT_RETOUR_BROUILLON,
        verbose_name="Statut"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    date_emission = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'émission"
    )

    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'envoi au fournisseur"
    )

    date_reception_fournisseur = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de réception par le fournisseur"
    )

    motif_retour = models.TextField(
        verbose_name="Motif du retour"
    )

    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )

    montant_total_ht = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total HT"
    )

    montant_total_tva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total TVA"
    )

    montant_total_ttc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant total TTC"
    )

    # Avoir ou remboursement
    avoir_recu = models.BooleanField(
        default=False,
        verbose_name="Avoir reçu"
    )

    montant_avoir = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant de l'avoir"
    )

    numero_avoir = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro de l'avoir"
    )

    date_avoir = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de l'avoir"
    )

    # Métadonnées
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bons_retour_crees_gac',
        verbose_name="Créé par"
    )

    emis_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bons_retour_emis_gac',
        verbose_name="Émis par"
    )

    # Relations inverses
    pieces_jointes = GenericRelation(
        'GACPieceJointe',
        related_query_name='bon_retour'
    )
    historique = GenericRelation(
        'GACHistorique',
        related_query_name='bon_retour'
    )

    class Meta:
        verbose_name = "Bon de retour fournisseur"
        verbose_name_plural = "Bons de retour fournisseur"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['fournisseur', 'statut']),
            models.Index(fields=['date_creation']),
        ]

    def __str__(self):
        return f"{self.numero} - {self.fournisseur.nom}"

    def save(self, *args, **kwargs):
        """Génère automatiquement le numéro de bon de retour."""
        if not self.numero:
            from gestion_achats.utils import generer_numero_bon_retour
            self.numero = generer_numero_bon_retour()
        super().save(*args, **kwargs)

    def calculer_totaux(self):
        """Calcule les totaux HT, TVA et TTC du bon de retour."""
        total_ht = Decimal('0.00')
        total_tva = Decimal('0.00')

        for ligne in self.lignes.all():
            total_ht += ligne.montant
            total_tva += ligne.montant_tva

        self.montant_total_ht = total_ht
        self.montant_total_tva = total_tva
        self.montant_total_ttc = total_ht + total_tva
        self.save(update_fields=['montant_total_ht', 'montant_total_tva', 'montant_total_ttc'])

    def get_statut_badge_class(self):
        """Retourne la classe CSS Bootstrap pour le badge de statut."""
        statut_classes = {
            'BROUILLON': 'secondary',
            'EMIS': 'info',
            'ENVOYE': 'primary',
            'RECU_FOURNISSEUR': 'warning',
            'REMBOURSE': 'success',
            'AVOIR_EMIS': 'success',
            'ANNULE': 'danger',
        }
        return statut_classes.get(self.statut, 'secondary')


# ==============================================================================
# MODÈLE: GACLigneBonRetour
# ==============================================================================

class GACLigneBonRetour(models.Model):
    """
    Ligne d'un bon de retour avec détail des quantités et articles retournés.
    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )

    bon_retour = models.ForeignKey(
        GACBonRetour,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name="Bon de retour"
    )

    ligne_reception = models.ForeignKey(
        GACLigneReception,
        on_delete=models.PROTECT,
        related_name='lignes_retour',
        verbose_name="Ligne de réception"
    )

    article = models.ForeignKey(
        GACArticle,
        on_delete=models.PROTECT,
        related_name='lignes_retour',
        verbose_name="Article"
    )

    quantite_retournee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantité retournée"
    )

    prix_unitaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire HT"
    )

    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(str(constants.TAUX_TVA_DEFAUT)),
        verbose_name="Taux TVA (%)"
    )

    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant HT"
    )

    montant_tva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant TVA"
    )

    montant_ttc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant TTC"
    )

    motif_retour = models.TextField(
        verbose_name="Motif du retour"
    )

    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )

    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre"
    )

    class Meta:
        verbose_name = "Ligne de bon de retour"
        verbose_name_plural = "Lignes de bons de retour"
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.article.reference} x {self.quantite_retournee}"

    def save(self, *args, **kwargs):
        """Calcule les montants avant sauvegarde."""
        from gestion_achats.utils import calculer_montant_tva

        self.montant = (self.quantite_retournee * self.prix_unitaire).quantize(Decimal('0.01'))
        self.montant_tva = calculer_montant_tva(self.montant, self.taux_tva)
        self.montant_ttc = self.montant + self.montant_tva
        super().save(*args, **kwargs)

        # Recalculer les totaux du bon de retour
        self.bon_retour.calculer_totaux()


class GACPieceJointe(models.Model):
    """
    Modèle pour gérer les pièces jointes liées à n'importe quel objet du module GAC.
    Utilise GenericForeignKey pour permettre l'attachement à différents types d'objets.
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant unique"
    )
    
    # Champs pour GenericForeignKey
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Type d'objet"
    )
    object_id = models.UUIDField(
        verbose_name="ID de l'objet"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    fichier = models.FileField(
        upload_to='gestion_achats/pieces_jointes/%Y/%m/',
        verbose_name="Fichier"
    )
    nom_fichier = models.CharField(
        max_length=255,
        verbose_name="Nom du fichier"
    )
    type_fichier = models.CharField(
        max_length=20,
        choices=[
            ('DEVIS', 'Devis'),
            ('FACTURE', 'Facture'),
            ('BL', 'Bon de livraison'),
            ('CONTRAT', 'Contrat'),
            ('CAHIER_CHARGES', 'Cahier des charges'),
            ('AUTRE', 'Autre'),
        ],
        default='AUTRE',
        verbose_name="Type de fichier"
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Description"
    )
    taille_fichier = models.IntegerField(
        verbose_name="Taille du fichier (octets)"
    )
    ajoute_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pieces_jointes_gac',
        verbose_name="Ajouté par"
    )
    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
        ordering = ['-date_ajout']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.nom_fichier} - {self.get_type_fichier_display()}"

    def save(self, *args, **kwargs):
        """Récupère le nom et la taille du fichier automatiquement."""
        if self.fichier:
            if not self.nom_fichier:
                self.nom_fichier = self.fichier.name
            if not self.taille_fichier:
                self.taille_fichier = self.fichier.size
        super().save(*args, **kwargs)

    def get_extension(self):
        """Retourne l'extension du fichier."""
        import os
        return os.path.splitext(self.nom_fichier)[1].lower()

    def get_taille_lisible(self):
        """Retourne la taille du fichier dans un format lisible."""
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if self.taille_fichier < 1024.0:
                return f"{self.taille_fichier:.1f} {unit}"
            self.taille_fichier /= 1024.0
        return f"{self.taille_fichier:.1f} To"


class GACHistorique(models.Model):
    """
    Modèle pour tracer toutes les actions effectuées dans le module GAC.
    Utilise GenericForeignKey pour permettre le traçage de n'importe quel objet.
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant unique"
    )
    
    # Champs pour GenericForeignKey
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Type d'objet"
    )
    object_id = models.UUIDField(
        verbose_name="ID de l'objet"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    utilisateur = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historique_gac',
        verbose_name="Utilisateur"
    )
    date_action = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de l'action"
    )
    details = models.TextField(
        blank=True,
        verbose_name="Détails"
    )
    ancien_statut = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ancien statut"
    )
    nouveau_statut = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Nouveau statut"
    )
    donnees_avant = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Données avant modification"
    )
    donnees_apres = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Données après modification"
    )
    adresse_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )

    class Meta:
        verbose_name = "Historique"
        verbose_name_plural = "Historiques"
        ordering = ['-date_action']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', 'date_action']),
            models.Index(fields=['utilisateur', 'date_action']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.utilisateur} - {self.date_action}"

    @classmethod
    def enregistrer_action(cls, objet, action, utilisateur, details='', ancien_statut='', 
                          nouveau_statut='', donnees_avant=None, donnees_apres=None, 
                          adresse_ip=None):
        """
        Méthode utilitaire pour enregistrer facilement une action dans l'historique.
        
        Args:
            objet: L'objet concerné par l'action
            action: Le type d'action (choix de ACTION_CHOICES)
            utilisateur: L'utilisateur qui effectue l'action
            details: Détails supplémentaires (optionnel)
            ancien_statut: Statut avant l'action (optionnel)
            nouveau_statut: Statut après l'action (optionnel)
            donnees_avant: Données avant modification (optionnel)
            donnees_apres: Données après modification (optionnel)
            adresse_ip: Adresse IP de l'utilisateur (optionnel)
        
        Returns:
            GACHistorique: L'entrée d'historique créée
        """
        content_type = ContentType.objects.get_for_model(objet)
        return cls.objects.create(
            content_type=content_type,
            object_id=objet.uuid,
            action=action,
            utilisateur=utilisateur,
            details=details,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            adresse_ip=adresse_ip
        )


# ==============================================================================
# MODÈLE: GACParametres (Singleton)
# ==============================================================================

class GACParametres(models.Model):
    """
    Modèle singleton pour stocker les paramètres de configuration du module GAC.
    
    Ce modèle ne doit avoir qu'une seule instance dans la base de données.
    """
    
    # Seuil de validation
    seuil_validation_n2 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('5000.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Seuil de validation N2",
        help_text="Montant TTC à partir duquel une validation N2 est requise (en euros)"
    )
    
    # Délais
    delai_livraison_defaut = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        verbose_name="Délai de livraison par défaut",
        help_text="Délai de livraison par défaut en jours"
    )
    
    # Notifications
    notifier_demandeur = models.BooleanField(
        default=True,
        verbose_name="Notifier le demandeur",
        help_text="Envoyer une notification au demandeur lors des changements de statut"
    )
    
    notifier_validateurs = models.BooleanField(
        default=True,
        verbose_name="Notifier les validateurs",
        help_text="Envoyer une notification aux validateurs lors de nouvelles demandes"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    
    modifie_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parametres_gac_modifies',
        verbose_name="Modifié par"
    )
    
    class Meta:
        verbose_name = "Paramètres GAC"
        verbose_name_plural = "Paramètres GAC"
    
    def __str__(self):
        return f"Paramètres GAC (Seuil N2: {self.seuil_validation_n2} €)"
    
    def save(self, *args, **kwargs):
        """Surcharge save pour implémenter le pattern singleton et invalider le cache."""
        from django.core.cache import cache
        
        # Pattern singleton : une seule instance autorisée
        if not self.pk and GACParametres.objects.exists():
            # Si on essaie de créer une nouvelle instance alors qu'une existe déjà
            # on récupère l'instance existante et on la met à jour
            existing = GACParametres.objects.first()
            self.pk = existing.pk
        
        super().save(*args, **kwargs)
        
        # Invalider le cache après modification
        cache.delete('gac_parametres')
    
    @classmethod
    def get_parametres(cls):
        """
        Récupère les paramètres (avec cache).
        
        Returns:
            GACParametres: L'instance unique des paramètres
        """
        from django.core.cache import cache
        
        # Essayer de récupérer depuis le cache
        parametres = cache.get('gac_parametres')
        
        if parametres is None:
            # Si pas en cache, récupérer depuis la DB
            parametres, created = cls.objects.get_or_create(
                pk=1,
                defaults={
                    'seuil_validation_n2': Decimal('5000.00'),
                    'delai_livraison_defaut': 30,
                    'notifier_demandeur': True,
                    'notifier_validateurs': True,
                }
            )
            
            # Mettre en cache pour 1 heure
            cache.set('gac_parametres', parametres, 3600)
        
        return parametres
    
    @classmethod
    def get_seuil_validation_n2(cls):
        """
        Récupère le seuil de validation N2.
        
        Returns:
            Decimal: Le seuil de validation N2
        """
        return cls.get_parametres().seuil_validation_n2
