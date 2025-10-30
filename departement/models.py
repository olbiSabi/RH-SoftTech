from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date

# Constante pour la date maximale
DATE_MAX = date(2999, 12, 31)


class ZDDE(models.Model):
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
        default=DATE_MAX,  # Utilisation de la constante
        verbose_name="Date de fin de validité",
        help_text="31/12/2999 si non renseigné"
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

        # S'assurer que DATEFIN n'est jamais null
        if self.DATEFIN is None:
            self.DATEFIN = DATE_MAX

        if self.DATEFIN <= self.DATEDEB:
            raise ValidationError({'DATEFIN': 'La date de fin doit être postérieure à la date de début.'})

    def save(self, *args, **kwargs):
        self.CODE = self.CODE.upper().strip()

        # Garantir une valeur pour DATEFIN
        if self.DATEFIN is None:
            self.DATEFIN = DATE_MAX

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        statut = "Actif" if self.STATUT else "Inactif"
        date_fin_display = "∞" if self.DATEFIN == DATE_MAX else self.DATEFIN.strftime('%d/%m/%Y')
        return f"{self.CODE} - {self.LIBELLE} ({statut}) [{self.DATEDEB} → {date_fin_display}]"