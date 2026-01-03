# entreprise/models.py
from django.db import models
from employee.models import ZY00
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import uuid


class Entreprise(models.Model):
    """Modèle représentant une entreprise ou société"""

    # Identifiants
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code entreprise",
        help_text="Code interne unique"
    )
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom de l'entreprise"
    )
    raison_sociale = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Raison sociale"
    )
    sigle = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Sigle"
    )

    # Adresse
    adresse = models.TextField(verbose_name="Adresse")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    pays = models.CharField(
        max_length=100,
        default="TOGO",
        verbose_name="Pays"
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone"
    )
    email = models.EmailField(blank=True, verbose_name="Email")
    site_web = models.URLField(blank=True, verbose_name="Site web")

    # Identifiants légaux
    rccm = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="RCCM",
        help_text="Registre de Commerce et du Crédit Mobilier"
    )
    numero_impot = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro d'impôt"
    )
    numero_cnss = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro CNSS"
    )

    # 🔵 Convention collective (référence à l'application absence)
    configuration_conventionnelle = models.ForeignKey(
        'absence.ConfigurationConventionnelle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entreprises',
        verbose_name="Convention collective applicable",
        help_text="Convention collective principale de l'entreprise"
    )

    # Dates importantes
    date_creation = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de création"
    )
    date_application_convention = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'application de la convention"
    )

    # Statut
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="L'entreprise est-elle active ?"
    )

    # Logo
    logo = models.ImageField(
        upload_to='logos_entreprise/',
        null=True,
        blank=True,
        verbose_name="Logo",
        help_text="Logo de l'entreprise"
    )

    # Informations complémentaires
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description de l'entreprise"
    )

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ['nom']
        db_table = 'ENTREPRISE'

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def clean(self):
        """Validation des données"""
        errors = {}

        # Validation du téléphone (optionnel)
        if self.telephone:
            # Format simple : +228 XX XX XX XX ou 00228 XX XX XX XX
            phone_validator = RegexValidator(
                regex=r'^(\+228|00228)?\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}$',
                message="Format téléphone invalide. Ex: +228 XX XX XX XX"
            )
            try:
                phone_validator(self.telephone)
            except ValidationError:
                errors['telephone'] = "Format téléphone invalide. Ex: +228 XX XX XX XX"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Sauvegarde avec nettoyage"""
        # Mettre le nom en majuscules
        if self.nom:
            self.nom = self.nom.upper()

        # Mettre le pays en majuscules
        if self.pays:
            self.pays = self.pays.upper()

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def employes_actifs(self):
        """Retourne tous les employés actifs de l'entreprise"""
        return ZY00.objects.filter(entreprise=self, etat='actif')

    @property
    def effectif_total(self):
        """Nombre total d'employés actifs"""
        return self.employes_actifs.count()

    @property
    def convention_en_vigueur(self):
        """Retourne la convention en vigueur"""
        if self.configuration_conventionnelle and self.configuration_conventionnelle.actif:
            return self.configuration_conventionnelle
        return None