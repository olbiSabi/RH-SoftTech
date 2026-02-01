# audit/models.py
"""
Modèles pour le module Conformité & Audit.

Structure:
- AUAL: Alertes de non-conformité (contrats expirés, documents manquants, etc.)
- AURA: Rapports d'audit générés
- AURC: Règles de conformité configurables
"""
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class AURC(models.Model):
    """
    Règles de conformité.
    Définit les critères de vérification pour générer des alertes.
    """
    TYPE_CHOICES = [
        ('CONTRAT', 'Contrat'),
        ('DOCUMENT', 'Document'),
        ('FORMATION', 'Formation'),
        ('VISITE_MEDICALE', 'Visite médicale'),
        ('CONGE', 'Congé'),
        ('MATERIEL', 'Matériel'),
        ('AUTRE', 'Autre'),
    ]

    FREQUENCE_CHOICES = [
        ('QUOTIDIEN', 'Quotidien'),
        ('HEBDOMADAIRE', 'Hebdomadaire'),
        ('MENSUEL', 'Mensuel'),
    ]

    SEVERITE_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Avertissement'),
        ('CRITICAL', 'Critique'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    CODE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Code de la règle"
    )
    LIBELLE = models.CharField(
        max_length=200,
        verbose_name="Libellé"
    )
    DESCRIPTION = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    TYPE_REGLE = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type de règle"
    )
    SEVERITE = models.CharField(
        max_length=20,
        choices=SEVERITE_CHOICES,
        default='WARNING',
        verbose_name="Sévérité"
    )
    FREQUENCE_VERIFICATION = models.CharField(
        max_length=20,
        choices=FREQUENCE_CHOICES,
        default='QUOTIDIEN',
        verbose_name="Fréquence de vérification"
    )

    # Paramètres de la règle
    JOURS_AVANT_EXPIRATION = models.PositiveIntegerField(
        default=30,
        verbose_name="Jours avant expiration",
        help_text="Nombre de jours avant expiration pour déclencher l'alerte"
    )
    PARAMETRES = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Paramètres additionnels",
        help_text="Configuration JSON supplémentaire"
    )

    # Notifications
    NOTIFIER_EMPLOYE = models.BooleanField(
        default=False,
        verbose_name="Notifier l'employé"
    )
    NOTIFIER_MANAGER = models.BooleanField(
        default=True,
        verbose_name="Notifier le manager"
    )
    NOTIFIER_RH = models.BooleanField(
        default=True,
        verbose_name="Notifier les RH"
    )
    EMAILS_SUPPLEMENTAIRES = models.TextField(
        blank=True,
        null=True,
        verbose_name="Emails supplémentaires",
        help_text="Un email par ligne"
    )

    STATUT = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_regle_conformite'
        verbose_name = "Règle de conformité"
        verbose_name_plural = "Règles de conformité"
        ordering = ['TYPE_REGLE', 'CODE']

    def __str__(self):
        return f"{self.CODE} - {self.LIBELLE}"

    def save(self, *args, **kwargs):
        if not self.CODE:
            self.CODE = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        """Génère un code unique pour la règle de conformité."""
        from django.db.models import Max

        # Préfixe basé sur le type de règle
        prefixes = {
            'CONTRAT': 'CONT',
            'DOCUMENT': 'DOC',
            'FORMATION': 'FORM',
            'VISITE_MEDICALE': 'VMED',
            'CONGE': 'CONG',
            'MATERIEL': 'MAT',
            'AUTRE': 'AUT',
        }
        prefix = prefixes.get(self.TYPE_REGLE, 'REG')

        # Trouver le dernier numéro pour ce préfixe
        last_code = AURC.objects.filter(
            CODE__startswith=prefix
        ).aggregate(Max('CODE'))['CODE__max']

        if last_code:
            try:
                # Extraire le numéro (format: CONT-0001)
                num = int(last_code.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1

        return f"{prefix}-{num:04d}"


class AUAL(models.Model):
    """
    Alertes de non-conformité.
    Générées automatiquement ou manuellement.
    """
    STATUT_CHOICES = [
        ('NOUVEAU', 'Nouveau'),
        ('EN_COURS', 'En cours de traitement'),
        ('RESOLU', 'Résolu'),
        ('IGNORE', 'Ignoré'),
        ('EXPIRE', 'Expiré'),
    ]

    PRIORITE_CHOICES = [
        ('BASSE', 'Basse'),
        ('MOYENNE', 'Moyenne'),
        ('HAUTE', 'Haute'),
        ('CRITIQUE', 'Critique'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    REFERENCE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Référence"
    )
    REGLE = models.ForeignKey(
        AURC,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes',
        verbose_name="Règle de conformité"
    )
    TYPE_ALERTE = models.CharField(
        max_length=20,
        choices=AURC.TYPE_CHOICES,
        verbose_name="Type d'alerte"
    )
    TITRE = models.CharField(
        max_length=255,
        verbose_name="Titre"
    )
    DESCRIPTION = models.TextField(
        verbose_name="Description"
    )
    PRIORITE = models.CharField(
        max_length=20,
        choices=PRIORITE_CHOICES,
        default='MOYENNE',
        verbose_name="Priorité"
    )
    STATUT = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='NOUVEAU',
        verbose_name="Statut"
    )

    # Entité concernée
    EMPLOYE = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertes_conformite',
        verbose_name="Employé concerné"
    )
    TABLE_REFERENCE = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Table de référence"
    )
    RECORD_ID = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ID de l'enregistrement"
    )

    # Dates
    DATE_DETECTION = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de détection"
    )
    DATE_ECHEANCE = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'échéance"
    )
    DATE_RESOLUTION = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de résolution"
    )

    # Traitement
    ASSIGNE_A = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_assignees',
        verbose_name="Assigné à"
    )
    COMMENTAIRE_RESOLUTION = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire de résolution"
    )
    RESOLU_PAR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_resolues',
        verbose_name="Résolu par"
    )

    # Notifications envoyées
    NOTIFICATION_ENVOYEE = models.BooleanField(
        default=False,
        verbose_name="Notification envoyée"
    )
    DATE_NOTIFICATION = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de notification"
    )

    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_alerte'
        verbose_name = "Alerte de conformité"
        verbose_name_plural = "Alertes de conformité"
        ordering = ['-DATE_DETECTION']
        indexes = [
            models.Index(fields=['STATUT', 'PRIORITE']),
            models.Index(fields=['TYPE_ALERTE']),
            models.Index(fields=['EMPLOYE']),
            models.Index(fields=['DATE_ECHEANCE']),
        ]

    def __str__(self):
        return f"{self.REFERENCE} - {self.TITRE}"

    def save(self, *args, **kwargs):
        if not self.REFERENCE:
            self.REFERENCE = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        """Génère une référence unique pour l'alerte."""
        from django.db.models import Max
        annee = timezone.now().year
        prefix = f"AL{annee}"

        last_ref = AUAL.objects.filter(
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
    def est_en_retard(self):
        """Vérifie si l'alerte est en retard."""
        if not self.DATE_ECHEANCE:
            return False
        return self.DATE_ECHEANCE < timezone.now().date() and self.STATUT not in ['RESOLU', 'IGNORE']

    @property
    def jours_restants(self):
        """Calcule le nombre de jours restants avant l'échéance."""
        if not self.DATE_ECHEANCE:
            return None
        delta = self.DATE_ECHEANCE - timezone.now().date()
        return delta.days

    @property
    def jours_retard(self):
        """Retourne le nombre de jours de retard (valeur positive)."""
        if not self.DATE_ECHEANCE:
            return None
        jours = self.jours_restants
        return abs(jours) if jours is not None and jours < 0 else 0


class AURA(models.Model):
    """
    Rapports d'audit générés.
    """
    TYPE_CHOICES = [
        ('CONFORMITE', 'Rapport de conformité'),
        ('ACTIVITE', 'Rapport d\'activité'),
        ('LOGS', 'Rapport des logs'),
        ('ALERTES', 'Rapport des alertes'),
        ('CONTRATS', 'Rapport des contrats'),
        ('DOCUMENTS', 'Rapport des documents'),
        ('PERSONNALISE', 'Rapport personnalisé'),
    ]

    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
    ]

    STATUT_CHOICES = [
        ('EN_COURS', 'En cours de génération'),
        ('TERMINE', 'Terminé'),
        ('ERREUR', 'Erreur'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    REFERENCE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Référence"
    )
    TITRE = models.CharField(
        max_length=200,
        verbose_name="Titre du rapport"
    )
    TYPE_RAPPORT = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type de rapport"
    )
    FORMAT = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='PDF',
        verbose_name="Format"
    )
    STATUT = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_COURS',
        verbose_name="Statut"
    )

    # Période du rapport
    DATE_DEBUT = models.DateField(
        verbose_name="Date de début"
    )
    DATE_FIN = models.DateField(
        verbose_name="Date de fin"
    )

    # Filtres appliqués
    FILTRES = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Filtres appliqués"
    )

    # Fichier généré
    FICHIER = models.FileField(
        upload_to='audit/rapports/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Fichier"
    )
    TAILLE_FICHIER = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Taille du fichier (bytes)"
    )

    # Statistiques du rapport
    NB_ENREGISTREMENTS = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'enregistrements"
    )
    RESUME = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Résumé statistique"
    )

    # Métadonnées
    GENERE_PAR = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_generes',
        verbose_name="Généré par"
    )
    DATE_GENERATION = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de génération"
    )
    MESSAGE_ERREUR = models.TextField(
        blank=True,
        null=True,
        verbose_name="Message d'erreur"
    )

    CREATED_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_rapport'
        verbose_name = "Rapport d'audit"
        verbose_name_plural = "Rapports d'audit"
        ordering = ['-DATE_GENERATION']

    def __str__(self):
        return f"{self.REFERENCE} - {self.TITRE}"

    def save(self, *args, **kwargs):
        if not self.REFERENCE:
            self.REFERENCE = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        """Génère une référence unique pour le rapport."""
        from django.db.models import Max
        annee = timezone.now().year
        prefix = f"RA{annee}"

        last_ref = AURA.objects.filter(
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
