from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

# ==========================================
# MODÈLE ZDPO POUR LE DEPARTEMENT
# ==========================================
class ZDDE(models.Model):
    """Modèle Département"""
    CODE = models.CharField(
        max_length=3,
        unique=True,
        verbose_name="Code département",
        help_text="3 lettres majuscules (ex: ABC)"
    )
    LIBELLE = models.CharField(
        max_length=100,
        verbose_name="Libellé du département"
    )
    STATUT = models.BooleanField(
        default=True,
        verbose_name="Statut actif"
    )
    DATEDEB = models.DateField(
        default=timezone.now,
        verbose_name="Date de début de validité"
    )
    DATEFIN = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de validité",
        help_text="Laisser vide si date non définie"
    )

    class Meta:
        db_table = 'ZDDE'
        verbose_name = "Département"
        verbose_name_plural = "Départements"

    def clean(self):
        """Validation des données"""
        if self.CODE:
            self.CODE = self.CODE.upper().strip()

        if len(self.CODE) != 3:
            raise ValidationError({'CODE': 'Le code doit contenir exactement 3 caractères.'})

        if not self.CODE.isalpha():
            raise ValidationError({'CODE': 'Le code ne doit contenir que des lettres.'})

        # Transformer le premier caractère du LIBELLE en majuscule
        if self.LIBELLE:
            self.LIBELLE = self.LIBELLE.strip()
            if self.LIBELLE:  # Vérifier que le libellé n'est pas vide après strip
                self.LIBELLE = self.LIBELLE[0].upper() + self.LIBELLE[1:]

        # Valider la date de fin seulement si elle est renseignée
        if self.DATEFIN and self.DATEFIN <= self.DATEDEB:
            raise ValidationError({'DATEFIN': 'La date de fin doit être postérieure à la date de début.'})

    def save(self, *args, **kwargs):
        self.CODE = self.CODE.upper().strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        statut = "Actif" if self.STATUT else "Inactif"
        date_fin_display = "-- --" if not self.DATEFIN else self.DATEFIN.strftime('%d/%m/%Y')
        return f"{self.LIBELLE} "
        #return f"{self.CODE} - {self.LIBELLE} ({statut}) [{self.DATEDEB.strftime('%d/%m/%Y')} → {date_fin_display}]"

# ==========================================
# MODÈLE ZDPO POUR LE POSTE
# ==========================================
class ZDPO(models.Model):
    """Modèle Poste"""
    CODE = models.CharField(
        max_length=6,
        unique=True,
        verbose_name="Code poste",
        help_text="6 caractères alphanumériques (ex: PST001)"
    )
    LIBELLE = models.CharField(
        max_length=100,
        verbose_name="Libellé du poste"
    )
    DEPARTEMENT = models.ForeignKey(
        ZDDE,
        on_delete=models.PROTECT,
        related_name='postes',
        verbose_name="Département",
        help_text="Département auquel appartient le poste"
    )
    STATUT = models.BooleanField(
        default=True,
        verbose_name="Statut actif"
    )
    DATEDEB = models.DateField(
        default=timezone.now,
        verbose_name="Date de début de validité"
    )
    DATEFIN = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de validité",
        help_text="Laisser vide si date non définie"
    )

    class Meta:
        db_table = 'ZDPO'
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['CODE']

    def clean(self):
        """Validation des données"""
        if self.CODE:
            self.CODE = self.CODE.upper().strip()

        if len(self.CODE) != 6:
            raise ValidationError({'CODE': 'Le code doit contenir exactement 5 caractères.'})

        if not self.CODE.isalnum():
            raise ValidationError({'CODE': 'Le code ne doit contenir que des lettres et des chiffres.'})

        # Transformer le premier caractère du LIBELLE en majuscule
        if self.LIBELLE:
            self.LIBELLE = self.LIBELLE.strip()
            if self.LIBELLE:  # Vérifier que le libellé n'est pas vide après strip
                self.LIBELLE = self.LIBELLE[0].upper() + self.LIBELLE[1:]

        # Valider la date de fin seulement si elle est renseignée
        if self.DATEFIN and self.DATEFIN <= self.DATEDEB:
            raise ValidationError({'DATEFIN': 'La date de fin doit être postérieure à la date de début.'})

    def save(self, *args, **kwargs):
        self.CODE = self.CODE.upper().strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        statut = "Actif" if self.STATUT else "Inactif"
        date_fin_display = "-- --" if not self.DATEFIN else self.DATEFIN.strftime('%d/%m/%Y')
        return f"{self.CODE} - {self.LIBELLE} "

