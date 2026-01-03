# departement/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

# ==========================================
# MODÈLE ZDDE POUR LE DEPARTEMENT
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
        return f"{self.LIBELLE}"

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
            raise ValidationError({'CODE': 'Le code doit contenir exactement 6 caractères.'})

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
        return f"{self.CODE} - {self.LIBELLE}"


# ==========================================
# MODÈLE ZYMA POUR LES MANAGERS
# ==========================================

class ZYMA(models.Model):
    """Table des managers par département"""

    departement = models.ForeignKey(
        ZDDE,
        on_delete=models.CASCADE,
        related_name='managers',
        verbose_name="Département"
    )
    employe = models.ForeignKey(
        'employee.ZY00',  # ← MODIFIER ICI - utiliser une référence par chaîne
        on_delete=models.CASCADE,
        related_name='managements',
        verbose_name="Manager",
        help_text="Employé désigné comme manager du département"
    )
    date_debut = models.DateField(
        verbose_name="Date de début de gestion",
        help_text="Date à laquelle l'employé devient manager du département"
    )
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de gestion",
        help_text="Date à laquelle l'employé n'est plus manager (laisser vide si toujours en poste)"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Manager actif"
    )

    class Meta:
        db_table = 'ZYMA'
        verbose_name = "Manager de département"
        verbose_name_plural = "Managers de département"
        ordering = ['-date_debut', 'departement__LIBELLE']
        constraints = [
            models.UniqueConstraint(
                fields=['departement'],
                condition=models.Q(date_fin__isnull=True),
                name='unique_manager_actif_par_departement'
            )
        ]

    def __str__(self):
        statut = "Actif" if self.actif else "Inactif"
        return f"{self.employe.nom} {self.employe.prenoms} - {self.departement.LIBELLE} ({statut})"

    def clean(self):
        """Validation personnalisée"""
        errors = {}

        # Vérifier que la date de fin est après la date de début
        if self.date_fin and self.date_fin <= self.date_debut:
            errors['date_fin'] = "La date de fin doit être postérieure à la date de début."

        # Vérifier que l'employé est un salarié (type_dossier = 'SAL')
        if self.employe.type_dossier != 'SAL':
            errors['employe'] = "Seuls les employés salariés peuvent être désignés comme managers."

        # Vérifier qu'il n'y a qu'un seul manager actif par département
        if not self.date_fin:  # Manager actif
            managers_actifs = ZYMA.objects.filter(
                departement=self.departement,
                date_fin__isnull=True
            ).exclude(pk=self.pk)

            if managers_actifs.exists():
                manager_actif = managers_actifs.first()
                errors['departement'] = (
                    f"Un manager actif existe déjà pour ce département : "
                    f"{manager_actif.employe.nom} {manager_actif.employe.prenoms} "
                    f"(depuis le {manager_actif.date_debut.strftime('%d/%m/%Y')}). "
                    f"Veuillez clôturer le manager actuel avant d'en désigner un nouveau."
                )

        # Vérifier que l'employé n'est pas déjà manager actif d'un autre département
        if not self.date_fin:  # Manager actif
            autres_managements = ZYMA.objects.filter(
                employe=self.employe,
                date_fin__isnull=True
            ).exclude(pk=self.pk)

            if autres_managements.exists():
                autre_departement = autres_managements.first().departement
                errors['employe'] = (
                    f"Cet employé est déjà manager actif du département {autre_departement.LIBELLE}. "
                    f"Un employé ne peut gérer qu'un seul département à la fois."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Mettre à jour le statut actif avant sauvegarde"""
        self.actif = self.date_fin is None
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def est_actif(self):
        """Retourne True si le manager est actuellement actif"""
        return self.date_fin is None

    @classmethod
    def get_manager_actif(cls, departement):
        """Retourne le manager actif d'un département"""
        try:
            return cls.objects.get(departement=departement, date_fin__isnull=True)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_departements_sans_manager(cls):
        """Retourne les départements sans manager actif"""
        departements_avec_manager = cls.objects.filter(
            date_fin__isnull=True
        ).values_list('departement_id', flat=True)

        return ZDDE.objects.exclude(id__in=departements_avec_manager).filter(STATUT=True)

    @classmethod
    def get_manager_actuel_employe(cls, employe):
        """Retourne le département managé par un employé (s'il est manager actif)"""
        try:
            return cls.objects.get(employe=employe, date_fin__isnull=True)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_historique_managers_departement(cls, departement):
        """Retourne l'historique complet des managers d'un département"""
        return cls.objects.filter(departement=departement).order_by('-date_debut')

    @classmethod
    def cloturer_manager_actuel(cls, departement, date_fin):
        """Clôture le manager actuel d'un département"""
        manager_actuel = cls.get_manager_actif(departement)
        if manager_actuel:
            manager_actuel.date_fin = date_fin
            manager_actuel.save()
            return True
        return False

    @classmethod
    def get_employes_eligibles_managers(cls):
        """Retourne les employés éligibles pour être managers (salariés actifs)"""
        from employee.models import ZY00  # ← Import local pour éviter l'importation circulaire
        return ZY00.objects.filter(type_dossier='SAL', etat='actif')