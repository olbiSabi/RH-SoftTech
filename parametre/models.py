from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


# ==========================================
# MODÈLE ZDAB (Type d'Absence)
# ==========================================

class ZDAB(models.Model):
    """Modèle Type d'Absence"""
    CODE = models.CharField(
        max_length=3,
        unique=True,
        verbose_name="Code absence",
        help_text="3 lettres majuscules (ex: CPN, RTT, MAL)"  # ← Exemples plus pertinents
    )
    LIBELLE = models.CharField(
        max_length=100,
        verbose_name="Libellé du type d'absence"  # ← Correction orthographe "tyope"
    )
    STATUT = models.BooleanField(
        default=True,
        verbose_name="Statut actif"
    )

    class Meta:
        db_table = 'ZDAB'
        verbose_name = "Type d'Absence"  # ← Plus clair
        verbose_name_plural = "Types d'Absence"  # ← Correction du pluriel
        ordering = ['CODE']  # ← Tri par défaut

    def clean(self):
        """Validation des données"""
        if self.CODE:
            self.CODE = self.CODE.upper().strip()

        if len(self.CODE) != 3:
            raise ValidationError({'CODE': 'Le code doit contenir exactement 3 caractères.'})

        # Transformer le premier caractère du LIBELLE en majuscule
        if self.LIBELLE:
            self.LIBELLE = self.LIBELLE.strip()
            if self.LIBELLE:  # Vérifier que le libellé n'est pas vide après strip
                self.LIBELLE = self.LIBELLE[0].upper() + self.LIBELLE[1:]

        if not self.CODE.isalpha():
            raise ValidationError({'CODE': 'Le code ne doit contenir que des lettres.'})

    def save(self, *args, **kwargs):
        self.CODE = self.CODE.upper().strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        statut = "Actif" if self.STATUT else "Inactif"
        return f"{self.CODE} - {self.LIBELLE} ({statut})"