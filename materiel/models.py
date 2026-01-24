# materiel/models.py
"""
Modèles pour le module de Suivi du Matériel & Parc.

Structure:
- MTCA: Catégories de matériel (informatique, mobilier, véhicule, etc.)
- MTMT: Matériel (équipements individuels)
- MTAF: Affectations de matériel aux employés
- MTMV: Mouvements de matériel (entrées, sorties, transferts)
- MTMA: Maintenance et interventions
- MTFO: Fournisseurs
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
from django.db.models import Count, Sum, Q


class MTCAManager(models.Manager):
    """Manager personnalisé pour MTCA avec annotations de statistiques."""
    
    def annotate_stats(self):
        """Ajoute des annotations de statistiques aux catégories."""
        return self.annotate(
            nb_materiels=Count('materiels', filter=Q(materiels__STATUT='DISPONIBLE')),
            nb_materiels_affectes=Count('materiels', filter=Q(materiels__STATUT='AFFECTE')),
            nb_materiels_maintenance=Count('materiels', filter=Q(materiels__STATUT='EN_MAINTENANCE')),
            valeur_totale=Sum('materiels__PRIX_ACQUISITION', filter=Q(materiels__STATUT__in=['DISPONIBLE', 'AFFECTE']))
        )


class MTCA(models.Model):
    """
    Catégorie de matériel.
    Ex: Informatique, Mobilier, Véhicule, Téléphonie, etc.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    CODE = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code catégorie"
    )
    LIBELLE = models.CharField(
        max_length=100,
        verbose_name="Libellé"
    )
    DESCRIPTION = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    ICONE = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Icône",
        help_text="Classe CSS de l'icône (ex: fa-laptop, fa-car)"
    )
    DUREE_AMORTISSEMENT = models.PositiveIntegerField(
        default=36,
        verbose_name="Durée d'amortissement (mois)",
        help_text="Durée d'amortissement en mois"
    )
    STATUT = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    ORDRE = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    objects = MTCAManager()

    class Meta:
        db_table = 'materiel_categorie'
        verbose_name = "Catégorie de matériel"
        verbose_name_plural = "Catégories de matériel"
        ordering = ['ORDRE', 'LIBELLE']

    def __str__(self):
        return f"{self.CODE} - {self.LIBELLE}"

    def save(self, *args, **kwargs):
        # Forcer le code en majuscules
        if self.CODE:
            self.CODE = self.CODE.upper().strip()
        super().save(*args, **kwargs)


class MTFOManager(models.Manager):
    """Manager personnalisé pour MTFO avec annotations de statistiques."""
    
    def annotate_stats(self):
        """Ajoute des annotations de statistiques aux fournisseurs."""
        return self.annotate(
            nb_materiels_fournis=Count('materiels_fournis', filter=Q(materiels_fournis__STATUT__in=['DISPONIBLE', 'AFFECTE'])),
            valeur_totale_materiels=Sum('materiels_fournis__PRIX_ACQUISITION', filter=Q(materiels_fournis__STATUT__in=['DISPONIBLE', 'AFFECTE'])),
            nb_maintenances=Count('maintenances', filter=Q(maintenances__STATUT__in=['PLANIFIE', 'EN_COURS']))
        )


class MTFO(models.Model):
    """
    Fournisseur de matériel.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    CODE = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code fournisseur"
    )
    RAISON_SOCIALE = models.CharField(
        max_length=200,
        verbose_name="Raison sociale"
    )
    CONTACT = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Personne contact"
    )
    TELEPHONE = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone"
    )
    EMAIL = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email"
    )
    ADRESSE = models.TextField(
        blank=True,
        null=True,
        verbose_name="Adresse"
    )
    SITE_WEB = models.URLField(
        blank=True,
        null=True,
        verbose_name="Site web"
    )
    NOTES = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    STATUT = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    objects = MTFOManager()

    class Meta:
        db_table = 'materiel_fournisseur'
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['RAISON_SOCIALE']

    def __str__(self):
        return f"{self.CODE} - {self.RAISON_SOCIALE}"

    def save(self, *args, **kwargs):
        if not self.CODE:
            self.CODE = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        """Génère un code unique pour le fournisseur (FOUR-XXXX)."""
        from django.db.models import Max
        prefix = "FOUR"

        last_code = MTFO.objects.filter(
            CODE__startswith=prefix
        ).aggregate(Max('CODE'))['CODE__max']

        if last_code:
            try:
                num = int(last_code.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1

        return f"{prefix}-{num:04d}"


class MTMT(models.Model):
    """
    Matériel (équipement individuel).
    """
    ETAT_CHOICES = [
        ('NEUF', 'Neuf'),
        ('BON', 'Bon état'),
        ('USAGE', 'Usagé'),
        ('DEFAILLANT', 'Défaillant'),
        ('HORS_SERVICE', 'Hors service'),
        ('REFORME', 'Réformé'),
    ]

    STATUT_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('AFFECTE', 'Affecté'),
        ('EN_MAINTENANCE', 'En maintenance'),
        ('EN_PRET', 'En prêt'),
        ('PERDU', 'Perdu/Volé'),
        ('REFORME', 'Réformé'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    CODE_INTERNE = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code interne",
        help_text="Identifiant unique du matériel (ex: PC-2024-001)"
    )
    CATEGORIE = models.ForeignKey(
        MTCA,
        on_delete=models.PROTECT,
        related_name='materiels',
        verbose_name="Catégorie"
    )
    DESIGNATION = models.CharField(
        max_length=200,
        verbose_name="Désignation"
    )
    MARQUE = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Marque"
    )
    MODELE = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modèle"
    )
    NUMERO_SERIE = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Numéro de série"
    )
    CARACTERISTIQUES = models.TextField(
        blank=True,
        null=True,
        verbose_name="Caractéristiques techniques"
    )

    # Acquisition
    FOURNISSEUR = models.ForeignKey(
        MTFO,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materiels_fournis',
        verbose_name="Fournisseur"
    )
    DATE_ACQUISITION = models.DateField(
        verbose_name="Date d'acquisition"
    )
    PRIX_ACQUISITION = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Prix d'acquisition (HT)"
    )
    NUMERO_FACTURE = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="N° facture"
    )
    NUMERO_BON_COMMANDE = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="N° bon de commande"
    )

    # Garantie
    DATE_FIN_GARANTIE = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date fin de garantie"
    )
    CONDITIONS_GARANTIE = models.TextField(
        blank=True,
        null=True,
        verbose_name="Conditions de garantie"
    )

    # Localisation
    LOCALISATION = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Localisation",
        help_text="Bâtiment, étage, bureau, etc."
    )

    # État et statut
    ETAT = models.CharField(
        max_length=20,
        choices=ETAT_CHOICES,
        default='NEUF',
        verbose_name="État"
    )
    STATUT = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='DISPONIBLE',
        verbose_name="Statut"
    )

    # Documents
    PHOTO = models.ImageField(
        upload_to='materiel/photos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo"
    )
    DOCUMENT = models.FileField(
        upload_to='materiel/documents/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
        )],
        verbose_name="Document joint"
    )

    # Affectation actuelle (denormalisé pour performance)
    AFFECTE_A = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materiels_affectes',
        verbose_name="Affecté à"
    )
    DATE_AFFECTATION = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'affectation"
    )

    # Métadonnées
    NOTES = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    CREATED_BY = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materiels_crees',
        verbose_name="Créé par"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materiel_equipement'
        verbose_name = "Matériel"
        verbose_name_plural = "Matériels"
        ordering = ['-CREATED_AT']
        permissions = [
            ('can_manage_materiel', 'Peut gérer le matériel'),
            ('can_view_all_materiel', 'Peut voir tout le matériel'),
            ('can_affecter_materiel', 'Peut affecter le matériel'),
        ]

    def __str__(self):
        return f"{self.CODE_INTERNE} - {self.DESIGNATION}"

    @property
    def est_sous_garantie(self):
        """Vérifie si le matériel est encore sous garantie."""
        if not self.DATE_FIN_GARANTIE:
            return False
        return self.DATE_FIN_GARANTIE >= timezone.now().date()

    @property
    def valeur_residuelle(self):
        """Calcule la valeur résiduelle du matériel."""
        if not self.DATE_ACQUISITION or not self.PRIX_ACQUISITION:
            return Decimal('0')

        duree_amortissement = self.CATEGORIE.DUREE_AMORTISSEMENT if self.CATEGORIE else 36
        mois_ecoules = (timezone.now().date() - self.DATE_ACQUISITION).days / 30

        if mois_ecoules >= duree_amortissement:
            return Decimal('0')

        taux_amortissement = Decimal(str(mois_ecoules / duree_amortissement))
        return self.PRIX_ACQUISITION * (1 - taux_amortissement)

    @property
    def age_mois(self):
        """Retourne l'âge du matériel en mois."""
        if not self.DATE_ACQUISITION:
            return 0
        return int((timezone.now().date() - self.DATE_ACQUISITION).days / 30)

    def save(self, *args, **kwargs):
        if not self.CODE_INTERNE:
            self.CODE_INTERNE = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        """Génère un code unique pour le matériel (CAT-YYYY-XXXX)."""
        from django.db.models import Max
        annee = timezone.now().year

        # Utiliser le code de la catégorie si disponible
        cat_code = self.CATEGORIE.CODE if self.CATEGORIE else "MAT"
        prefix = f"{cat_code}-{annee}"

        last_code = MTMT.objects.filter(
            CODE_INTERNE__startswith=prefix
        ).aggregate(Max('CODE_INTERNE'))['CODE_INTERNE__max']

        if last_code:
            try:
                num = int(last_code.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1

        return f"{prefix}-{num:04d}"


class MTAF(models.Model):
    """
    Affectation de matériel à un employé.
    Historique complet des affectations.
    """
    TYPE_CHOICES = [
        ('AFFECTATION', 'Affectation'),
        ('PRET', 'Prêt temporaire'),
        ('MISE_A_DISPOSITION', 'Mise à disposition'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    MATERIEL = models.ForeignKey(
        MTMT,
        on_delete=models.CASCADE,
        related_name='affectations',
        verbose_name="Matériel"
    )
    EMPLOYE = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.PROTECT,
        related_name='affectations_materiel',
        verbose_name="Employé"
    )
    TYPE_AFFECTATION = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='AFFECTATION',
        verbose_name="Type"
    )
    DATE_DEBUT = models.DateField(
        verbose_name="Date de début"
    )
    DATE_FIN = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )
    DATE_RETOUR_PREVUE = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de retour prévue",
        help_text="Pour les prêts temporaires"
    )
    MOTIF = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motif"
    )
    ETAT_SORTIE = models.CharField(
        max_length=20,
        choices=MTMT.ETAT_CHOICES,
        verbose_name="État à la sortie"
    )
    ETAT_RETOUR = models.CharField(
        max_length=20,
        choices=MTMT.ETAT_CHOICES,
        blank=True,
        null=True,
        verbose_name="État au retour"
    )
    COMMENTAIRE_RETOUR = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire au retour"
    )

    # Documents
    FICHE_AFFECTATION = models.FileField(
        upload_to='materiel/affectations/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Fiche d'affectation signée"
    )

    # Métadonnées
    AFFECTE_PAR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affectations_effectuees',
        verbose_name="Affecté par"
    )
    RETOUR_PAR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retours_effectues',
        verbose_name="Retour enregistré par"
    )
    ACTIF = models.BooleanField(
        default=True,
        verbose_name="Affectation active"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materiel_affectation'
        verbose_name = "Affectation"
        verbose_name_plural = "Affectations"
        ordering = ['-DATE_DEBUT']

    def __str__(self):
        return f"{self.MATERIEL.CODE_INTERNE} → {self.EMPLOYE}"

    @property
    def est_en_cours(self):
        """Vérifie si l'affectation est en cours."""
        return self.ACTIF and self.DATE_FIN is None

    @property
    def est_en_retard(self):
        """Vérifie si le retour est en retard (pour les prêts)."""
        if not self.DATE_RETOUR_PREVUE or self.DATE_FIN:
            return False
        return self.DATE_RETOUR_PREVUE < timezone.now().date()


class MTMV(models.Model):
    """
    Mouvement de matériel (entrées, sorties, transferts).
    """
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée en stock'),
        ('SORTIE', 'Sortie définitive'),
        ('TRANSFERT', 'Transfert'),
        ('REFORME', 'Réforme'),
        ('PERTE', 'Perte/Vol'),
        ('INVENTAIRE', 'Ajustement inventaire'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    REFERENCE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Référence"
    )
    MATERIEL = models.ForeignKey(
        MTMT,
        on_delete=models.CASCADE,
        related_name='mouvements',
        verbose_name="Matériel"
    )
    TYPE_MOUVEMENT = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type de mouvement"
    )
    DATE_MOUVEMENT = models.DateField(
        verbose_name="Date du mouvement"
    )
    MOTIF = models.TextField(
        verbose_name="Motif"
    )

    # Pour les transferts
    LOCALISATION_ORIGINE = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Localisation d'origine"
    )
    LOCALISATION_DESTINATION = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Localisation de destination"
    )

    # Pour les réformes/sorties
    VALEUR_SORTIE = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valeur à la sortie"
    )
    DOCUMENT_JUSTIFICATIF = models.FileField(
        upload_to='materiel/mouvements/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Document justificatif"
    )

    # Métadonnées
    EFFECTUE_PAR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mouvements_materiel',
        verbose_name="Effectué par"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materiel_mouvement'
        verbose_name = "Mouvement"
        verbose_name_plural = "Mouvements"
        ordering = ['-DATE_MOUVEMENT']

    def __str__(self):
        return f"{self.REFERENCE} - {self.get_TYPE_MOUVEMENT_display()}"

    def save(self, *args, **kwargs):
        if not self.REFERENCE:
            self.REFERENCE = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        """Génère une référence unique pour le mouvement."""
        from django.db.models import Max
        annee = timezone.now().year
        prefix = f"MV{annee}"

        last_ref = MTMV.objects.filter(
            REFERENCE__startswith=prefix
        ).aggregate(Max('REFERENCE'))['REFERENCE__max']

        if last_ref:
            try:
                num = int(last_ref[-5:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:05d}"


class MTMA(models.Model):
    """
    Maintenance et interventions sur le matériel.
    """
    TYPE_CHOICES = [
        ('PREVENTIVE', 'Maintenance préventive'),
        ('CORRECTIVE', 'Maintenance corrective'),
        ('REPARATION', 'Réparation'),
        ('REVISION', 'Révision'),
        ('MISE_A_JOUR', 'Mise à jour'),
    ]

    STATUT_CHOICES = [
        ('PLANIFIE', 'Planifié'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    REFERENCE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Référence"
    )
    MATERIEL = models.ForeignKey(
        MTMT,
        on_delete=models.CASCADE,
        related_name='maintenances',
        verbose_name="Matériel"
    )
    TYPE_MAINTENANCE = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type de maintenance"
    )
    DESCRIPTION = models.TextField(
        verbose_name="Description de l'intervention"
    )
    DATE_PLANIFIEE = models.DateField(
        verbose_name="Date planifiée"
    )
    DATE_DEBUT = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de début"
    )
    DATE_FIN = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )

    # Prestataire
    PRESTATAIRE = models.ForeignKey(
        MTFO,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenances',
        verbose_name="Prestataire"
    )
    INTERVENANT_INTERNE = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenances_effectuees',
        verbose_name="Intervenant interne"
    )

    # Coûts
    COUT_PIECES = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Coût pièces"
    )
    COUT_MAIN_OEUVRE = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Coût main d'œuvre"
    )
    NUMERO_FACTURE = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="N° facture"
    )

    # Résultat
    STATUT = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PLANIFIE',
        verbose_name="Statut"
    )
    RESULTAT = models.TextField(
        blank=True,
        null=True,
        verbose_name="Résultat / Observations"
    )
    ETAT_APRES = models.CharField(
        max_length=20,
        choices=MTMT.ETAT_CHOICES,
        blank=True,
        null=True,
        verbose_name="État après intervention"
    )

    # Documents
    RAPPORT = models.FileField(
        upload_to='materiel/maintenances/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Rapport d'intervention"
    )

    # Prochaine maintenance
    PROCHAINE_MAINTENANCE = models.DateField(
        null=True,
        blank=True,
        verbose_name="Prochaine maintenance"
    )

    # Métadonnées
    DEMANDE_PAR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_maintenance',
        verbose_name="Demandé par"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materiel_maintenance'
        verbose_name = "Maintenance"
        verbose_name_plural = "Maintenances"
        ordering = ['-DATE_PLANIFIEE']

    def __str__(self):
        return f"{self.REFERENCE} - {self.MATERIEL.CODE_INTERNE}"

    def save(self, *args, **kwargs):
        if not self.REFERENCE:
            self.REFERENCE = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        """Génère une référence unique pour la maintenance."""
        from django.db.models import Max
        annee = timezone.now().year
        prefix = f"MA{annee}"

        last_ref = MTMA.objects.filter(
            REFERENCE__startswith=prefix
        ).aggregate(Max('REFERENCE'))['REFERENCE__max']

        if last_ref:
            try:
                num = int(last_ref[-5:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:05d}"

    @property
    def cout_total(self):
        """Calcule le coût total de la maintenance."""
        return self.COUT_PIECES + self.COUT_MAIN_OEUVRE
