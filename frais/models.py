# frais/models.py
"""
Modèles pour le module de gestion des Notes de Frais et Avances.

Structure:
- NFCA: Catégories de frais (transport, repas, hébergement, etc.)
- NFPL: Plafonds par catégorie (optionnel, par grade/catégorie employé)
- NFNF: Notes de frais (en-tête)
- NFLF: Lignes de frais (dépenses individuelles)
- NFAV: Avances sur frais
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone


class NFCA(models.Model):
    """
    Catégorie de frais.
    Ex: Transport, Repas, Hébergement, Fournitures, Téléphone, etc.
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
    JUSTIFICATIF_OBLIGATOIRE = models.BooleanField(
        default=True,
        verbose_name="Justificatif obligatoire"
    )
    PLAFOND_DEFAUT = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Plafond par défaut",
        help_text="Montant maximum par dépense (optionnel)"
    )
    ICONE = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Icône",
        help_text="Classe CSS de l'icône (ex: fa-car, fa-utensils)"
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

    class Meta:
        db_table = 'frais_categorie'
        verbose_name = "Catégorie de frais"
        verbose_name_plural = "Catégories de frais"
        ordering = ['ORDRE', 'LIBELLE']

    def __str__(self):
        return f"{self.CODE} - {self.LIBELLE}"

    def save(self, *args, **kwargs):
        # Forcer le code en majuscules
        if self.CODE:
            self.CODE = self.CODE.upper().strip()
        super().save(*args, **kwargs)


class NFPL(models.Model):
    """
    Plafond de frais par catégorie et/ou grade employé.
    Permet de définir des limites spécifiques selon le profil.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    CATEGORIE = models.ForeignKey(
        NFCA,
        on_delete=models.CASCADE,
        related_name='plafonds',
        verbose_name="Catégorie"
    )
    GRADE = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Grade/Catégorie employé",
        help_text="Laisser vide pour appliquer à tous"
    )
    MONTANT_JOURNALIER = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Plafond journalier"
    )
    MONTANT_MENSUEL = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Plafond mensuel"
    )
    MONTANT_PAR_DEPENSE = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Plafond par dépense"
    )
    DATE_DEBUT = models.DateField(
        verbose_name="Date de début"
    )
    DATE_FIN = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )
    STATUT = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'frais_plafond'
        verbose_name = "Plafond de frais"
        verbose_name_plural = "Plafonds de frais"
        ordering = ['-DATE_DEBUT']

    def __str__(self):
        grade = self.GRADE or "Tous"
        return f"{self.CATEGORIE.CODE} - {grade}"

    def est_actif(self):
        """Vérifie si le plafond est actuellement actif."""
        today = timezone.now().date()
        if not self.STATUT:
            return False
        if self.DATE_FIN and self.DATE_FIN < today:
            return False
        return self.DATE_DEBUT <= today


class NFNF(models.Model):
    """
    Note de frais (en-tête).
    Regroupe plusieurs lignes de frais pour une période donnée.
    """
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('SOUMIS', 'Soumis'),
        ('EN_VALIDATION', 'En validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
        ('REMBOURSE', 'Remboursé'),
        ('ANNULE', 'Annulé'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    REFERENCE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Référence"
    )
    EMPLOYE = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.PROTECT,
        related_name='notes_frais',
        verbose_name="Employé"
    )
    PERIODE_DEBUT = models.DateField(
        verbose_name="Début de période"
    )
    PERIODE_FIN = models.DateField(
        verbose_name="Fin de période"
    )
    OBJET = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Objet/Mission"
    )
    STATUT = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='BROUILLON',
        verbose_name="Statut"
    )
    MONTANT_TOTAL = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Montant total"
    )
    MONTANT_VALIDE = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Montant validé"
    )
    MONTANT_REMBOURSE = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Montant remboursé"
    )

    # Validation
    DATE_SOUMISSION = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de soumission"
    )
    VALIDEUR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_frais_validees',
        verbose_name="Valideur"
    )
    DATE_VALIDATION = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    COMMENTAIRE_VALIDATION = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire de validation"
    )

    # Remboursement
    DATE_REMBOURSEMENT = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de remboursement"
    )
    REFERENCE_PAIEMENT = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Référence de paiement"
    )

    # Métadonnées
    CREATED_BY = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_frais_creees',
        verbose_name="Créé par"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'frais_note_frais'
        verbose_name = "Note de frais"
        verbose_name_plural = "Notes de frais"
        ordering = ['-CREATED_AT']
        permissions = [
            ('can_validate_note_frais', 'Peut valider les notes de frais'),
            ('can_process_remboursement', 'Peut traiter les remboursements'),
            ('can_view_all_notes_frais', 'Peut voir toutes les notes de frais'),
        ]

    def __str__(self):
        return f"{self.REFERENCE} - {self.EMPLOYE}"

    def save(self, *args, **kwargs):
        if not self.REFERENCE:
            self.REFERENCE = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        """Génère une référence unique pour la note de frais."""
        from django.db.models import Max
        annee = timezone.now().year
        prefix = f"NF{annee}"

        last_ref = NFNF.objects.filter(
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

    def calculer_totaux(self):
        """Recalcule les totaux depuis les lignes de frais."""
        from django.db.models import Sum

        lignes = self.lignes.all()
        self.MONTANT_TOTAL = lignes.aggregate(
            total=Sum('MONTANT')
        )['total'] or Decimal('0')

        self.MONTANT_VALIDE = lignes.filter(
            STATUT_LIGNE='VALIDE'
        ).aggregate(
            total=Sum('MONTANT')
        )['total'] or Decimal('0')

        self.save(update_fields=['MONTANT_TOTAL', 'MONTANT_VALIDE', 'UPDATED_AT'])

    def peut_etre_modifie(self):
        """Vérifie si la note peut être modifiée."""
        return self.STATUT in ['BROUILLON', 'REJETE']

    def peut_etre_soumis(self):
        """Vérifie si la note peut être soumise."""
        return self.STATUT == 'BROUILLON' and self.lignes.exists()

    def peut_etre_valide(self):
        """Vérifie si la note peut être validée."""
        return self.STATUT in ['SOUMIS', 'EN_VALIDATION']


class NFLF(models.Model):
    """
    Ligne de frais (dépense individuelle).
    """
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    NOTE_FRAIS = models.ForeignKey(
        NFNF,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name="Note de frais"
    )
    CATEGORIE = models.ForeignKey(
        NFCA,
        on_delete=models.PROTECT,
        related_name='lignes_frais',
        verbose_name="Catégorie"
    )
    DATE_DEPENSE = models.DateField(
        verbose_name="Date de la dépense"
    )
    DESCRIPTION = models.CharField(
        max_length=255,
        verbose_name="Description"
    )
    MONTANT = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant"
    )
    DEVISE = models.CharField(
        max_length=3,
        default='XOF',
        verbose_name="Devise"
    )
    TAUX_CHANGE = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('1'),
        verbose_name="Taux de change"
    )
    MONTANT_CONVERTI = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant converti (XOF)"
    )

    # Justificatif
    JUSTIFICATIF = models.FileField(
        upload_to='frais/justificatifs/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
        )],
        verbose_name="Justificatif"
    )
    NUMERO_FACTURE = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="N° facture/reçu"
    )

    # Validation ligne
    STATUT_LIGNE = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut"
    )
    COMMENTAIRE_REJET = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motif de rejet"
    )

    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'frais_ligne_frais'
        verbose_name = "Ligne de frais"
        verbose_name_plural = "Lignes de frais"
        ordering = ['DATE_DEPENSE']

    def __str__(self):
        return f"{self.DATE_DEPENSE} - {self.CATEGORIE.LIBELLE}: {self.MONTANT}"

    def save(self, *args, **kwargs):
        # Calculer le montant converti si devise différente
        if self.DEVISE != 'XOF' and self.TAUX_CHANGE:
            self.MONTANT_CONVERTI = self.MONTANT * self.TAUX_CHANGE
        else:
            self.MONTANT_CONVERTI = self.MONTANT
        super().save(*args, **kwargs)

        # Recalculer les totaux de la note
        self.NOTE_FRAIS.calculer_totaux()


class NFAV(models.Model):
    """
    Avance sur frais.
    Montant versé à l'employé avant la mission, à régulariser ensuite.
    """
    STATUT_CHOICES = [
        ('DEMANDE', 'Demandée'),
        ('APPROUVE', 'Approuvée'),
        ('VERSE', 'Versée'),
        ('REGULARISE', 'Régularisée'),
        ('ANNULE', 'Annulée'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    REFERENCE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Référence"
    )
    EMPLOYE = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.PROTECT,
        related_name='avances_frais',
        verbose_name="Employé"
    )
    MONTANT_DEMANDE = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1'))],
        verbose_name="Montant demandé"
    )
    MONTANT_APPROUVE = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant approuvé"
    )
    MOTIF = models.TextField(
        verbose_name="Motif de la demande"
    )
    DATE_MISSION_DEBUT = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date début mission"
    )
    DATE_MISSION_FIN = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date fin mission"
    )

    STATUT = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='DEMANDE',
        verbose_name="Statut"
    )

    # Approbation
    APPROBATEUR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avances_approuvees',
        verbose_name="Approbateur"
    )
    DATE_APPROBATION = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'approbation"
    )
    COMMENTAIRE_APPROBATION = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire"
    )

    # Versement
    DATE_VERSEMENT = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de versement"
    )
    REFERENCE_VERSEMENT = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Référence versement"
    )

    # Régularisation
    NOTE_FRAIS = models.ForeignKey(
        NFNF,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avances',
        verbose_name="Note de frais de régularisation"
    )
    MONTANT_REGULARISE = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant régularisé"
    )
    DATE_REGULARISATION = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de régularisation"
    )

    # Métadonnées
    CREATED_BY = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avances_creees',
        verbose_name="Créé par"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'frais_avance'
        verbose_name = "Avance sur frais"
        verbose_name_plural = "Avances sur frais"
        ordering = ['-CREATED_AT']
        permissions = [
            ('can_approve_avance', 'Peut approuver les avances'),
            ('can_process_versement', 'Peut traiter les versements'),
            ('can_view_all_avances', 'Peut voir toutes les avances'),
        ]

    def __str__(self):
        return f"{self.REFERENCE} - {self.EMPLOYE}"

    def save(self, *args, **kwargs):
        if not self.REFERENCE:
            self.REFERENCE = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        """Génère une référence unique pour l'avance."""
        from django.db.models import Max
        annee = timezone.now().year
        prefix = f"AV{annee}"

        last_ref = NFAV.objects.filter(
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

    def solde_a_regulariser(self):
        """Calcule le solde restant à régulariser."""
        montant_verse = self.MONTANT_APPROUVE or self.MONTANT_DEMANDE
        montant_utilise = self.MONTANT_REGULARISE or Decimal('0')
        return montant_verse - montant_utilise

    def peut_etre_modifie(self):
        """Vérifie si l'avance peut être modifiée."""
        return self.STATUT == 'DEMANDE'

    def peut_etre_approuve(self):
        """Vérifie si l'avance peut être approuvée."""
        return self.STATUT == 'DEMANDE'

    def peut_etre_verse(self):
        """Vérifie si l'avance peut être versée."""
        return self.STATUT == 'APPROUVE'
