from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

# Import du modèle ZDPO depuis l'application departement
from departement.models import ZDPO


class ZY00(models.Model):
    """Table principale des employés"""

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    SITUATION_FAMILIALE_CHOICES = [
        ('CELIBATAIRE', 'Célibataire'),
        ('MARIE', 'Marié'),
        ('DIVORCE', 'Divorcé'),
        ('VEUVE', 'Veuve'),
        ('VEUF', 'Veuf'),
        ('PACSE', 'Pacsé'),
        ('CONCUBINAGE', 'Concubinage'),
    ]

    TYPE_ID_CHOICES = [
        ('CNI', 'CNI'),
        ('PASSEPORT', 'Passeport'),
        ('AUTRES', 'Autres'),
    ]

    TYPE_DOSSIER_CHOICES = [
        ('PRE', 'Pré-embauche'),
        ('SAL', 'Salarié'),
    ]

    matricule = models.CharField(
        max_length=8,
        unique=True,
        primary_key=True,
        verbose_name="Matricule",
        editable=False
    )
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenoms = models.CharField(max_length=200, verbose_name="Prénom(s)")
    date_naissance = models.DateField(verbose_name="Date de naissance")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name="Sexe")
    ville_naissance = models.CharField(max_length=100, blank=True, verbose_name="Ville de naissance")
    pays_naissance = models.CharField(max_length=100, blank=True, verbose_name="Pays de naissance")
    situation_familiale = models.CharField(
        max_length=20,
        choices=SITUATION_FAMILIALE_CHOICES,
        blank=True,
        verbose_name="Situation familiale"
    )
    type_id = models.CharField(max_length=20, choices=TYPE_ID_CHOICES, verbose_name="Type d'identité")
    numero_id = models.CharField(max_length=50, unique=True, verbose_name="Numéro d'identité")
    date_validite_id = models.DateField(verbose_name="Date de validité ID")
    date_expiration_id = models.DateField(verbose_name="Date d'expiration ID")
    type_dossier = models.CharField(
        max_length=3,
        choices=TYPE_DOSSIER_CHOICES,
        default='PRE',
        verbose_name="Type de dossier"
    )
    date_validation_embauche = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de validation embauche"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        db_table = 'ZY00'
        verbose_name = "Employé"
        verbose_name_plural = "Employés"

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenoms}"

    def clean(self):
        """Validation personnalisée"""
        # Mettre le nom en majuscules
        if self.nom:
            self.nom = self.nom.upper()

        # Mettre le pays_naissance en majuscules
        if self.pays_naissance:
            self.pays_naissance = self.pays_naissance.upper()

        # Vérifier que la date d'expiration est après la date de validité
        if self.date_expiration_id and self.date_validite_id:
            if self.date_expiration_id <= self.date_validite_id:
                raise ValidationError({
                    'date_expiration_id': "La date d'expiration doit être supérieure à la date de validité."
                })

        # Transformer le premier caractère du prenoms en majuscule
        if self.prenoms:
            self.prenoms = self.prenoms.strip()
            if self.prenoms:  # Vérifier que le prenoms n'est pas vide après strip
                self.prenoms = self.prenoms[0].upper() + self.prenoms[1:]

        # Transformer le premier caractère du ville_naissance en majuscule
        if self.ville_naissance:
            self.ville_naissance = self.ville_naissance.strip()
            if self.ville_naissance:  # Vérifier que le ville_naissance n'est pas vide après strip
                self.ville_naissance = self.ville_naissance[0].upper() + self.ville_naissance[1:]

    def save(self, *args, **kwargs):
        """Générer automatiquement le matricule lors de la création"""
        if not self.matricule:
            # Récupérer le dernier matricule
            last_employee = ZY00.objects.all().order_by('matricule').last()
            if last_employee:
                last_number = int(last_employee.matricule[2:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.matricule = f"MT{new_number:06d}"

        self.full_clean()
        super().save(*args, **kwargs)


class ZYCO(models.Model):
    """Table des contrats"""

    TYPE_CONTRAT_CHOICES = [
        ('CDD', 'CDD'),
        ('CDI', 'CDI'),
        ('STAGE', 'Stage'),
        ('ALTERNANCE', 'Alternance'),
        ('APPRENTISSAGE', 'Apprentissage'),
        ('CONTRACTUELLE', 'Contractuelle'),
        ('VACATAIRE', 'Vacataire'),
    ]

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='contrats',
        verbose_name="Employé"
    )
    type_contrat = models.CharField(
        max_length=20,
        choices=TYPE_CONTRAT_CHOICES,
        verbose_name="Type de contrat"
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")

    class Meta:
        db_table = 'ZYCO'
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.employe.matricule} - {self.type_contrat} ({self.date_debut})"

    def clean(self):
        """Validation: un seul contrat actif par employé"""
        if not self.date_fin:  # Contrat actif
            contrats_actifs = ZYCO.objects.filter(
                employe=self.employe,
                date_fin__isnull=True
            ).exclude(pk=self.pk)

            if contrats_actifs.exists():
                raise ValidationError(
                    "Un contrat actif existe déjà pour cet employé. "
                    "Veuillez clôturer l'ancien contrat avant d'en créer un nouveau."
                )


class ZYTE(models.Model):
    """Table des téléphones"""

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='telephones',
        verbose_name="Employé"
    )
    numero = models.CharField(max_length=20, verbose_name="Numéro de téléphone")
    date_debut_validite = models.DateField(verbose_name="Date de début de validité")
    date_fin_validite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de validité"
    )

    class Meta:
        db_table = 'ZYTE'
        verbose_name = "Téléphone"
        verbose_name_plural = "Téléphones"
        ordering = ['-date_debut_validite']

    def __str__(self):
        return f"{self.employe.matricule} - {self.numero}"


class ZYME(models.Model):
    """Table des emails"""

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='emails',
        verbose_name="Employé"
    )
    email = models.EmailField(verbose_name="Email")
    date_debut_validite = models.DateField(verbose_name="Date de début de validité")
    date_fin_validite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de validité"
    )

    class Meta:
        db_table = 'ZYME'
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ['-date_debut_validite']

    def __str__(self):
        return f"{self.employe.matricule} - {self.email}"



class ZYAF(models.Model):
    """Table des affectations"""

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='affectations',
        verbose_name="Employé"
    )
    poste = models.ForeignKey(
        ZDPO,
        on_delete=models.PROTECT,
        verbose_name="Poste"
    )
    date_debut = models.DateField(verbose_name="Date de début d'affectation")
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin d'affectation"
    )

    class Meta:
        db_table = 'ZYAF'
        verbose_name = "Affectation"
        verbose_name_plural = "Affectations"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.employe.matricule} - {self.poste.LIBELLE} ({self.date_debut})"

    def clean(self):
        """Validation: une seule affectation active par employé"""
        if not self.date_fin:  # Affectation active
            affectations_actives = ZYAF.objects.filter(
                employe=self.employe,
                date_fin__isnull=True
            ).exclude(pk=self.pk)

            if affectations_actives.exists():
                raise ValidationError(
                    "Une affectation active existe déjà pour cet employé. "
                    "Veuillez clôturer l'ancienne affectation avant d'en créer une nouvelle."
                )


class ZYAD(models.Model):
    """Table des adresses"""

    TYPE_ADRESSE_CHOICES = [
        ('PRINCIPALE', 'Résidence principale'),
        ('SECONDAIRE', 'Résidence secondaire'),
    ]

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='adresses',
        verbose_name="Employé"
    )
    rue = models.CharField(max_length=200, verbose_name="Rue")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    pays = models.CharField(max_length=100, verbose_name="Pays")
    code_postal = models.CharField(max_length=10, verbose_name="Code postal")
    type_adresse = models.CharField(
        max_length=20,
        choices=TYPE_ADRESSE_CHOICES,
        verbose_name="Type d'adresse"
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )

    class Meta:
        db_table = 'ZYAD'
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.employe.matricule} - {self.ville} ({self.type_adresse})"

    def save(self, *args, **kwargs):
        # Formater le pays en majuscules avant sauvegarde
        if self.pays:
            self.pays = self.pays.upper()

        # Formater la ville : première lettre en majuscule avant sauvegarde
        if self.ville:
            self.ville = self.ville.title()

        super().save(*args, **kwargs)

    def clean(self):
        """Validation: une seule adresse principale active par employé"""
        if self.type_adresse == 'PRINCIPALE' and not self.date_fin:
            adresses_principales = ZYAD.objects.filter(
                employe=self.employe,
                type_adresse='PRINCIPALE',
                date_fin__isnull=True
            ).exclude(pk=self.pk)

            if adresses_principales.exists():
                raise ValidationError(
                    "Une adresse principale active existe déjà pour cet employé."
                )