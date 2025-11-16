from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import os

# Import du modèle ZDPO depuis l'application departement
from departement.models import ZDPO

def employee_photo_path(instance, filename):
    """Fonction pour définir le chemin de sauvegarde de la photo"""
    ext = filename.split('.')[-1]
    filename = f"{instance.matricule}_photo.{ext}"
    return os.path.join('photos/employes/', filename)

######################
###  Employe ZY00  ###
######################
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

    ETAT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
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
    # NOUVEAU CHAMP PHOTO
    photo = models.ImageField(
        upload_to=employee_photo_path,
        null=True,
        blank=True,
        verbose_name="Photo de profil",
        help_text="Photo de profil de l'employé (formats acceptés: JPG, PNG)"
    )

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
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='actif')


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

        # 🆕 VALIDATION DE LA PHOTO
        if self.photo:
            # Vérifier l'extension du fichier
            ext = os.path.splitext(self.photo.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if ext not in valid_extensions:
                raise ValidationError({
                     'photo': f"Format de fichier non autorisé. Formats acceptés: {', '.join(valid_extensions)}"
                })

            # Vérifier la taille du fichier (max 5MB)
            if self.photo.size > 5 * 1024 * 1024:
                raise ValidationError({
                    'photo': "La taille de la photo ne doit pas dépasser 5 MB."
                })

    def save(self, *args, **kwargs):
        """Générer automatiquement le matricule lors de la création"""
        # 🆕 SUPPRIMER L'ANCIENNE PHOTO SI UNE NOUVELLE EST UPLOADÉE
        if self.pk:
            try:
                old_instance = ZY00.objects.get(pk=self.pk)
                if old_instance.photo and old_instance.photo != self.photo:
                    # Supprimer l'ancien fichier
                    if os.path.isfile(old_instance.photo.path):
                        os.remove(old_instance.photo.path)
            except ZY00.DoesNotExist:
                pass

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

    def get_photo_url(self):
        """Retourne l'URL de la photo ou une photo par défaut"""
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        # Retourner une photo par défaut selon le sexe
        if self.sexe == 'F':
            return '/static/assets/img/default_female_avatar.png'
        else:
            return '/static/assets/img/default_male_avatar.png'

    def desactiver_donnees_associees(self):
        """Désactive toutes les données associées lorsque l'employé est radié ou licencié"""
        if self.etat in ['inactif']:
            self.contrats.filter(actif=True).update(actif=False)
            self.telephones.filter(actif=True).update(actif=False)
            self.emails.filter(actif=True).update(actif=False)
            self.affectations.filter(actif=True).update(actif=False)
            self.adresses.filter(actif=True).update(actif=False)

######################
###  Contrat ZYCO  ###
######################
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
    actif = models.BooleanField(default=True)

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

######################
### Telephone ZYTE ###
######################
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
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'ZYTE'
        verbose_name = "Téléphone"
        verbose_name_plural = "Téléphones"
        ordering = ['-date_debut_validite']

    def __str__(self):
        return f"{self.employe.matricule} - {self.numero}"

######################
#####  Mail ZYME  ####
######################
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
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'ZYME'
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ['-date_debut_validite']

    def __str__(self):
        return f"{self.employe.matricule} - {self.email}"

######################
## Affectation ZYAF ##
######################
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
    actif = models.BooleanField(default=True)

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

######################
###  Adresse ZYAD  ###
######################
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
    complement = models.CharField(  # ← AJOUTEZ CE CHAMP
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Complément d'adresse"
    )
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
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'ZYAD'
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.employe.matricule} - {self.ville} ({self.type_adresse})"

    def save(self, *args, **kwargs):
        # Formater la ville : première lettre en majuscule avant sauvegarde
        if self.ville:
            self.ville = self.ville.title()

        super().save(*args, **kwargs)

    def clean(self):
        """Validation: une seule adresse principale ACTIVE par employé"""
        # Vérifier seulement si c'est une adresse principale SANS date de fin (active)
        if self.type_adresse == 'PRINCIPALE' and not self.date_fin:
            # Chercher les autres adresses principales ACTIVES pour le même employé
            adresses_principales_actives = ZYAD.objects.filter(
                employe=self.employe,
                type_adresse='PRINCIPALE',
                date_fin__isnull=True  # Pas de date de fin = active
            ).exclude(pk=self.pk)  # Exclure l'instance courante si elle existe

            if adresses_principales_actives.exists():
                raise ValidationError(
                    "Une adresse principale active existe déjà pour cet employé. "
                    "Veuillez clôturer l'adresse existante en ajoutant une date de fin "
                    "avant de créer une nouvelle adresse principale."
                )

######################
### Documment ZYDO ###
######################
class ZYDO(models.Model):
    """Table des documents joints aux employés"""

    TYPE_DOCUMENT_CHOICES = [
        ('CV', 'CV'),
        ('LETTRE_MOTIVATION', 'Lettre de motivation'),
        ('DIPLOME', 'Diplôme'),
        ('ATTESTATION_FORMATION', 'Attestation de formation'),
        ('CERTIFICAT_TRAVAIL', 'Certificat de travail'),
        ('LETTRE_RECOMMANDATION', 'Lettre de recommandation'),
        ('CNI', 'Carte Nationale d\'Identité'),
        ('PASSEPORT', 'Passeport'),
        ('ACTE_NAISSANCE', 'Acte de naissance'),
        ('CERTIFICAT_RESIDENCE', 'Certificat de résidence'),
        ('RIB', 'RIB'),
        ('ATTESTATION_SECURITE_SOCIALE', 'Attestation sécurité sociale'),
        ('CERTIFICAT_MEDICAL', 'Certificat médical'),
        ('CONTRAT_SIGNE', 'Contrat signé'),
        ('ATTESTATION_ASSURANCE', 'Attestation d\'assurance'),
        ('JUSTIFICATIF_DOMICILE', 'Justificatif de domicile'),
        ('PHOTO_IDENTITE', 'Photo d\'identité'),
        ('AUTRES', 'Autres'),
    ]

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Employé"
    )
    type_document = models.CharField(
        max_length=50,
        choices=TYPE_DOCUMENT_CHOICES,
        verbose_name="Type de document"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    fichier = models.FileField(
        upload_to='documents/employes/%Y/%m/',
        verbose_name="Fichier"
    )
    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    taille_fichier = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Taille (octets)"
    )
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'ZYDO'
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-date_ajout']

    def __str__(self):
        return f"{self.employe.matricule} - {self.get_type_document_display()}"

    def save(self, *args, **kwargs):
        """Calculer la taille du fichier avant sauvegarde"""
        if self.fichier:
            self.taille_fichier = self.fichier.size
        super().save(*args, **kwargs)

    def get_extension(self):
        """Retourne l'extension du fichier"""
        import os
        return os.path.splitext(self.fichier.name)[1].lower()

    def get_taille_lisible(self):
        """Retourne la taille du fichier dans un format lisible"""
        if not self.taille_fichier:
            return "N/A"

        taille = self.taille_fichier
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if taille < 1024.0:
                return f"{taille:.1f} {unit}"
            taille /= 1024.0
        return f"{taille:.1f} To"

    def get_nom_fichier(self):
        """Retourne le nom du fichier original"""
        import os
        return os.path.basename(self.fichier.name)

######################
###  Famille  ZYFA ###
######################
class ZYFA(models.Model):
    """Table des personnes à charge (famille)"""

    PERSONNE_CHARGE_CHOICES = [
        ('ENFANT', 'Enfant'),
        ('CONJOINT', 'Conjoint'),
        ('PARENT', 'Parent'),
        ('AUTRE', 'Autre personne à charge'),
    ]

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='personnes_charge',
        verbose_name="Employé"
    )
    personne_charge = models.CharField(
        max_length=20,
        choices=PERSONNE_CHARGE_CHOICES,
        verbose_name="Personne en charge"
    )
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=200, verbose_name="Prénom")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name="Sexe")
    date_naissance = models.DateField(verbose_name="Date de naissance")
    date_debut_prise_charge = models.DateField(verbose_name="Date de début de prise en charge")
    date_fin_prise_charge = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de prise en charge"
    )
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'ZYFA'
        verbose_name = "Personne à charge"
        verbose_name_plural = "Personnes à charge"
        ordering = ['-date_debut_prise_charge']

    def __str__(self):
        return f"{self.employe.matricule} - {self.prenom} {self.nom} ({self.get_personne_charge_display()})"

    def save(self, *args, **kwargs):
        # Si c'est un enfant et date_debut_prise_charge n'est pas définie, utiliser date_naissance
        if self.personne_charge == 'ENFANT' and not self.date_debut_prise_charge:
            self.date_debut_prise_charge = self.date_naissance
        super().save(*args, **kwargs)

    def clean(self):
        """Validation personnalisée"""
        # Vérifier que la date de fin est après la date de début
        if self.date_fin_prise_charge and self.date_fin_prise_charge <= self.date_debut_prise_charge:
            raise ValidationError({
                'date_fin_prise_charge': 'La date de fin doit être supérieure à la date de début.'
            })

        # Vérifier que la date de naissance est dans le passé
        if self.date_naissance > timezone.now().date():
            raise ValidationError({
                'date_naissance': 'La date de naissance doit être dans le passé.'
            })