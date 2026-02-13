"""
Modèles pour le module Planning simplifié.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

from departement.models import ZDDE

User = get_user_model()


class Planning(models.Model):
    """
    Planning principal pour la gestion des plannings.
    """
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('PUBLIE', 'Publié'),
        ('VALIDE', 'Validé'),
        ('ARCHIVE', 'Archivé'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    REFERENCE = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Référence"
    )
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre du planning"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    date_debut = models.DateField(
        verbose_name="Date de début"
    )
    date_fin = models.DateField(
        verbose_name="Date de fin"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='BROUILLON',
        verbose_name="Statut"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Créé par"
    )
    departement = models.ForeignKey(
        ZDDE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Département",
        related_name='plannings'
    )

    class Meta:
        db_table = 'planning_planning'
        verbose_name = "Planning"
        verbose_name_plural = "Plannings"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.REFERENCE} - {self.titre}"

    def save(self, *args, **kwargs):
        if not self.REFERENCE:
            self.REFERENCE = self._generer_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _generer_reference():
        """Genere une reference unique au format PLN-YYYY-XXXX."""
        from django.db.models import Max
        annee = timezone.now().year
        prefix = f'PLN-{annee}-'
        dernier = Planning.objects.filter(
            REFERENCE__startswith=prefix
        ).aggregate(max_ref=Max('REFERENCE'))['max_ref']
        if dernier:
            dernier_numero = int(dernier.split('-')[-1])
        else:
            dernier_numero = 0
        return f'{prefix}{str(dernier_numero + 1).zfill(4)}'

    @property
    def nombre_semaines(self):
        """Calcule le nombre de semaines du planning."""
        delta = self.date_fin - self.date_debut
        return delta.days // 7 + 1


class SiteTravail(models.Model):
    """
    Site de travail.
    """
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du site"
    )
    adresse = models.TextField(
        blank=True,
        verbose_name="Adresse"
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone"
    )
    heure_ouverture = models.TimeField(
        default="08:00",
        verbose_name="Heure d'ouverture"
    )
    heure_fermeture = models.TimeField(
        default="18:00",
        verbose_name="Heure de fermeture"
    )
    fuseau_horaire = models.CharField(
        max_length=50,
        default="Africa/Lome",
        verbose_name="Fuseau horaire"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'planning_site_travail'
        verbose_name = "Site de travail"
        verbose_name_plural = "Sites de travail"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class PosteTravail(models.Model):
    """
    Poste de travail.
    """
    TYPE_POSTE_CHOICES = [
        ('JOURNEE', 'Poste journée'),
        ('SOIR', 'Poste soir'),
        ('NUIT', 'Poste nuit'),
        ('WEEKEND', 'Poste week-end'),
        ('SPECIAL', 'Poste spécial'),
    ]

    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du poste"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    type_poste = models.CharField(
        max_length=20,
        choices=TYPE_POSTE_CHOICES,
        default='JOURNEE',
        verbose_name="Type de poste"
    )
    site = models.ForeignKey(
        SiteTravail,
        on_delete=models.CASCADE,
        verbose_name="Site"
    )
    heure_debut = models.TimeField(
        default="09:00",
        verbose_name="Heure de début"
    )
    heure_fin = models.TimeField(
        default="17:00",
        verbose_name="Heure de fin"
    )
    pause_dejeune = models.DurationField(
        default="00:30:00",
        verbose_name="Pause déjeuner"
    )
    taux_horaire = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=12.50,
        verbose_name="Taux horaire (FCFA)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'planning_poste_travail'
        verbose_name = "Poste de travail"
        verbose_name_plural = "Postes de travail"
        ordering = ['site', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.site.nom})"

    @property
    def duree_travail(self):
        """Calcule la durée de travail en heures."""
        from datetime import datetime, timedelta
        
        debut = datetime.strptime(str(self.heure_debut), "%H:%M:%S")
        fin = datetime.strptime(str(self.heure_fin), "%H:%M:%S")
        
        # Convertir pause en timedelta
        pause_str = str(self.pause_dejeune)
        if pause_str:
            heures, minutes, secondes = map(int, pause_str.split(':'))
            pause = timedelta(hours=heures, minutes=minutes, seconds=secondes)
        else:
            pause = timedelta(0)
        
        duree = fin - debut - pause
        return duree.total_seconds() / 3600


class Affectation(models.Model):
    """Affectation d'un employe a un poste de travail sur une date donnee."""

    STATUT_CHOICES = [
        ('PLANIFIE', 'Planifie'),
        ('CONFIRME', 'Confirme'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Termine'),
        ('ANNULE', 'Annule'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    planning = models.ForeignKey(
        Planning,
        on_delete=models.CASCADE,
        related_name='affectations',
        verbose_name="Planning"
    )
    employe = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='affectations_planning',
        verbose_name="Employe"
    )
    poste = models.ForeignKey(
        PosteTravail,
        on_delete=models.CASCADE,
        related_name='affectations',
        verbose_name="Poste de travail"
    )
    date = models.DateField(verbose_name="Date")
    heure_debut = models.TimeField(verbose_name="Heure de debut")
    heure_fin = models.TimeField(verbose_name="Heure de fin")
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PLANIFIE',
        verbose_name="Statut"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affectations_creees',
        verbose_name="Cree par"
    )

    class Meta:
        db_table = 'planning_affectation'
        verbose_name = "Affectation"
        verbose_name_plural = "Affectations"
        ordering = ['date', 'heure_debut']
        unique_together = ['employe', 'date', 'heure_debut']

    def __str__(self):
        return f"{self.employe} - {self.poste} ({self.date})"

    @property
    def duree_heures(self):
        """Calcule la duree en heures."""
        from datetime import datetime
        d = datetime.combine(self.date, self.heure_fin) - datetime.combine(self.date, self.heure_debut)
        return d.total_seconds() / 3600


class Evenement(models.Model):
    """Evenement de calendrier (reunion, formation, tache, etc.)."""

    TYPE_CHOICES = [
        ('REUNION', 'Reunion'),
        ('FORMATION', 'Formation'),
        ('TACHE', 'Tache'),
        ('AUTRE', 'Autre'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    date_debut = models.DateTimeField(verbose_name="Date/heure de debut")
    date_fin = models.DateTimeField(verbose_name="Date/heure de fin")
    type_evenement = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='REUNION',
        verbose_name="Type"
    )
    employes = models.ManyToManyField(
        'employee.ZY00',
        related_name='evenements_planning',
        blank=True,
        verbose_name="Participants"
    )
    lieu = models.CharField(max_length=200, blank=True, verbose_name="Lieu")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evenements_crees',
        verbose_name="Cree par"
    )

    class Meta:
        db_table = 'planning_evenement'
        verbose_name = "Evenement"
        verbose_name_plural = "Evenements"
        ordering = ['date_debut']

    def __str__(self):
        return f"{self.titre} ({self.get_type_evenement_display()})"
