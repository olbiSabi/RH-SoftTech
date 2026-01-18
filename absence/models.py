# absence/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date
from django.db import transaction
import os


# ========================================
# FONCTION D'UPLOAD
# ========================================

def upload_justificatif(instance, filename):
    """
    Génère le chemin d'upload des justificatifs
    Structure: justificatifs_absences/MATRICULE/YYYY/MM/fichier.ext
    """
    ext = filename.split('.')[-1]
    date_now = timezone.now()

    # Nom de fichier avec horodatage lisible + timestamp pour unicité
    filename = f"{instance.employe.matricule}_{date_now.strftime('%Y%m%d_%H%M%S')}_{int(date_now.timestamp())}.{ext}"

    # Chemin: employé → année → mois
    return os.path.join(
        'justificatifs_absences',
        str(instance.employe.matricule),
        date_now.strftime('%Y'),
        date_now.strftime('%m'),
        filename
    )


# 1. ConfigurationConventionnelle
class ConfigurationConventionnelle(models.Model):
    """Configuration d'une convention collective"""

    METHODE_CALCUL_CHOICES = [
        ('MOIS_TRAVAILLES', 'Par mois travaillés'),
        ('HEURES_TRAVAILLEES', 'Par heures travaillées'),
        ('JOURS_TRAVAILLES', 'Par jours travaillés'),
    ]

    # ✅ NOUVEAU : Type de convention
    TYPE_CONVENTION_CHOICES = [
        ('ENTREPRISE', 'Convention d\'entreprise'),
        ('PERSONNALISEE', 'Convention personnalisée'),
    ]

    type_convention = models.CharField(
        max_length=20,
        choices=TYPE_CONVENTION_CHOICES,
        default='ENTREPRISE',
        verbose_name="Type de convention",
        help_text="Convention d'entreprise (unique) ou personnalisée (pour employés spécifiques)"
    )

    nom = models.CharField(max_length=100, verbose_name="Nom de la convention")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    annee_reference = models.IntegerField(verbose_name="Année de référence")

    # Période de validité
    date_debut = models.DateField(verbose_name="Date de début d'effet")
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin d'effet",
        help_text="Laisser vide si la convention est toujours en vigueur"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    # Paramètres de calcul
    jours_acquis_par_mois = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('2.5'),
        verbose_name="Jours acquis par mois",
        help_text="Nombre de jours de congé acquis par mois travaillé"
    )
    duree_conges_principale = models.IntegerField(
        default=12,
        verbose_name="Durée congés principale",
        help_text="Durée minimale en jours pour les congés principaux consécutifs"
    )

    # Période de prise des congés
    periode_prise_debut = models.DateField(
        verbose_name="Début période de prise",
        help_text="Date de début de la période de prise des congés (ex: 1er mai)"
    )
    periode_prise_fin = models.DateField(
        verbose_name="Fin période de prise",
        help_text="Date de fin de la période de prise des congés (ex: 30 avril)"
    )

    methode_calcul = models.CharField(
        max_length=20,
        choices=METHODE_CALCUL_CHOICES,
        default='MOIS_TRAVAILLES',
        verbose_name="Méthode de calcul"
    )

    periode_prise_fin_annee_suivante = models.BooleanField(
        default=False,
        verbose_name="Fin en année N+1",
        help_text="Cochez si la période de prise se termine l'année suivante (ex: mai N → avril N+1)"
    )


    class Meta:
        ordering = ['-annee_reference']
        verbose_name = "Configuration conventionnelle"
        verbose_name_plural = "Configurations conventionnelles"

    def __str__(self):
        type_label = "ENT" if self.type_convention == 'ENTREPRISE' else "PERSO"
        return f"[{type_label}] {self.nom} ({self.annee_reference})"


    def get_periode_acquisition(self, annee_reference):
        """
        Retourne les dates de début et fin de la période d'acquisition
        pour une année de référence donnée

        Args:
            annee_reference (int): Année de référence (N)

        Returns:
            tuple: (date_debut, date_fin)
        """
        debut = date(
            annee_reference,
            self.periode_prise_debut.month,
            self.periode_prise_debut.day
        )

        if self.periode_prise_fin_annee_suivante:
            # Fin en N+1
            fin = date(
                annee_reference + 1,
                self.periode_prise_fin.month,
                self.periode_prise_fin.day
            )
        else:
            # Fin en N
            fin = date(
                annee_reference,
                self.periode_prise_fin.month,
                self.periode_prise_fin.day
            )

        return (debut, fin)

    @property
    def est_en_vigueur(self):
        """
        Vérifie si la convention est actuellement en vigueur
        """
        today = date.today()

        if not self.actif:
            return False

        if today < self.date_debut:
            return False

        if self.date_fin and today > self.date_fin:
            return False

        return True

    @property
    def est_clôturée(self):
        """
        Vérifie si la convention est clôturée (possède une date de fin)
        """
        return self.date_fin is not None

    def clean(self):
        """Validation des dates et règles de gestion"""
        super().clean()

        errors = {}

        # ============================================================
        # VALIDATION 1 : Date de fin > Date de début
        # ============================================================
        if self.date_fin and self.date_fin <= self.date_debut:
            errors['date_fin'] = "La date de fin doit être postérieure à la date de début"

        # ============================================================
        # VALIDATION 2 : Période de prise (peut s'étendre sur 2 ans)
        # ============================================================
        if self.periode_prise_fin and self.periode_prise_debut:
            diff_mois = (self.periode_prise_fin.year - self.periode_prise_debut.year) * 12 + \
                        (self.periode_prise_fin.month - self.periode_prise_debut.month)

            if diff_mois < 0:
                errors['periode_prise_fin'] = \
                    "La date de fin de période doit être postérieure à la date de début. " \
                    "Vérifiez les années (N/N+1) sélectionnées."

            if diff_mois > 18:
                errors['periode_prise_fin'] = \
                    "La période de prise ne peut pas dépasser 18 mois. " \
                    "La durée habituelle est de 12 mois (ex: 1er mai N → 30 avril N+1)."

        # ============================================================
        # VALIDATION 3 & 4 : UNIQUEMENT POUR LES CONVENTIONS D'ENTREPRISE
        # ============================================================
        if self.type_convention == 'ENTREPRISE':
            # ✅ VALIDATION 3 : Pas de chevauchement de périodes (ENTREPRISE uniquement)
            if self.date_debut:
                queryset = ConfigurationConventionnelle.objects.filter(
                    type_convention='ENTREPRISE'  # ✅ Filtrer uniquement les conventions d'entreprise
                )

                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)

                chevauchements = []
                for conv in queryset:
                    notre_fin = self.date_fin if self.date_fin else date(9999, 12, 31)
                    conv_fin = conv.date_fin if conv.date_fin else date(9999, 12, 31)

                    if self.date_debut <= conv_fin and notre_fin >= conv.date_debut:
                        chevauchements.append(conv)

                if chevauchements:
                    conv_list = []
                    for c in chevauchements:
                        fin_str = c.date_fin.strftime('%d/%m/%Y') if c.date_fin else 'en cours'
                        conv_list.append(f"'{c.code}' ({c.date_debut.strftime('%d/%m/%Y')} - {fin_str})")

                    errors['date_debut'] = \
                        f"Chevauchement de période détecté avec la(les) convention(s) d'entreprise : {', '.join(conv_list)}. " \
                        f"Veuillez ajuster les dates ou clôturer la convention existante."

            # ✅ VALIDATION 4 : Une seule convention d'entreprise active sans date de fin
            if self.actif and not self.date_fin:
                queryset = ConfigurationConventionnelle.objects.filter(
                    type_convention='ENTREPRISE',  # ✅ Filtrer uniquement les conventions d'entreprise
                    actif=True,
                    date_fin__isnull=True
                )

                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)

                conventions_actives = queryset

                if conventions_actives.exists():
                    conv_list = ', '.join([f"'{c.code}'" for c in conventions_actives])
                    errors['date_fin'] = \
                        f"Impossible d'enregistrer une convention d'entreprise active sans date de fin. " \
                        f"Les conventions d'entreprise suivantes sont déjà actives sans date de fin : {conv_list}. " \
                        f"Veuillez d'abord ajouter une date de fin à ces conventions ou les désactiver."

        # ============================================================
        # LEVER LES ERREURS SI NÉCESSAIRE
        # ============================================================
        if errors:
            raise ValidationError(errors)


# 2. TypeAbsence
class TypeAbsence(models.Model):
    """Types d'absence (congés payés, maladie, etc.)"""

    CATEGORIE_CHOICES = [
        ('CONGES_PAYES', 'Congés Payés'),
        ('MALADIE', 'Maladie/Accident'),
        ('AUTORISATION', 'Autorisation spéciale'),
        ('SANS_SOLDE', 'Sans solde'),
        ('MATERNITE', 'Maternité/Paternité'),
        ('FORMATION', 'Formation'),
        ('MISSION', 'Mission'),
    ]

    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name="Code",
        help_text="Code sur 3 caractères (ex: CPN, MAL, AUT)"
    )
    libelle = models.CharField(
        max_length=100,
        verbose_name="Libellé"
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES,
        verbose_name="Catégorie"
    )

    paye = models.BooleanField(
        default=True,
        verbose_name="Payé"
    )
    decompte_solde = models.BooleanField(
        default=True,
        verbose_name="Décompte du solde",
        help_text="Décompte du solde de congés"
    )
    justificatif_obligatoire = models.BooleanField(
        default=False,
        verbose_name="Justificatif obligatoire"
    )

    couleur = models.CharField(
        max_length=7,
        default='#3498db',
        verbose_name="Couleur",
        help_text="Code couleur hexadécimal (#RRGGBB)"
    )
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    class Meta:
        db_table = 'absence_type_absence'
        verbose_name = "Type d'absence"
        verbose_name_plural = "Types d'absence"
        ordering = ['ordre', 'libelle']

    def __str__(self):
        return f"{self.code} - {self.libelle}"

    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError

        # ✅ Convertir le code en majuscules
        if self.code:
            self.code = self.code.upper().strip()

            # Vérifier que le code fait exactement 3 caractères
            if len(self.code) != 3:
                raise ValidationError({
                    'code': 'Le code doit contenir exactement 3 caractères'
                })

            # Vérifier que le code est alphanumérique
            if not self.code.isalnum():
                raise ValidationError({
                    'code': 'Le code ne doit contenir que des lettres et des chiffres'
                })

            # Vérifier l'unicité (case-insensitive)
            queryset = TypeAbsence.objects.filter(code__iexact=self.code)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            if queryset.exists():
                raise ValidationError({
                    'code': f'Le code "{self.code}" existe déjà'
                })

        # ✅ Capitaliser le libellé (première lettre en majuscule)
        if self.libelle:
            self.libelle = self.libelle.strip().capitalize()

        # Valider le code couleur
        if self.couleur:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', self.couleur):
                raise ValidationError({
                    'couleur': 'Format invalide. Utilisez le format #RRGGBB (ex: #3498db)'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# 3. JourFerie
class JourFerie(models.Model):
    """
    Gestion des jours fériés par année
    Permet de définir les jours fériés légaux et spécifiques à l'entreprise
    """

    TYPE_CHOICES = [
        ('LEGAL', 'Légal (Code du travail)'),
        ('ENTREPRISE', 'Spécifique à l\'entreprise'),
    ]

    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du jour férié",
        help_text="Ex: Jour de l'an, Fête du travail, etc."
    )

    date = models.DateField(
        verbose_name="Date",
        help_text="Date du jour férié",
        unique=True
    )

    type_ferie = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='LEGAL',
        verbose_name="Type de jour férié"
    )

    recurrent = models.BooleanField(
        default=True,
        verbose_name="Récurrent",
        help_text="Si coché, ce jour férié sera automatiquement reporté chaque année"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Informations complémentaires"
    )

    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jours_feries_crees',
        verbose_name="Créé par"
    )

    class Meta:
        db_table = 'absence_jour_ferie'
        verbose_name = "Jour férié"
        verbose_name_plural = "Jours fériés"
        ordering = ['date']
        # ✅ SUPPRESSION de unique_together (remplacé par unique sur date)

    def __str__(self):
        return f"{self.nom} - {self.date.strftime('%d/%m/%Y')}"

    @property
    def annee(self):
        """Retourne l'année du jour férié"""
        return self.date.year

    @property
    def mois_nom(self):
        """Retourne le nom du mois en français"""
        mois = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return mois[self.date.month - 1]

    @property
    def jour_semaine(self):
        """Retourne le jour de la semaine en français"""
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return jours[self.date.weekday()]

    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError

        # ✅ Vérifier l'unicité de la date
        if self.date:
            queryset = JourFerie.objects.filter(date=self.date)

            # Exclure l'instance actuelle en cas de modification
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            if queryset.exists():
                jour_existant = queryset.first()
                raise ValidationError({
                    'date': f"Un jour férié existe déjà pour cette date : '{jour_existant.nom}' le {self.date.strftime('%d/%m/%Y')}"
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# 4. ParametreCalculConges
class ParametreCalculConges(models.Model):
    """Paramètres avancés pour le calcul des congés"""

    configuration = models.OneToOneField(
        ConfigurationConventionnelle,
        on_delete=models.CASCADE,
        related_name='parametres_calcul'
    )

    mois_acquisition_min = models.IntegerField(
        default=1,
        verbose_name="Mois d'acquisition minimum"
    )
    plafond_jours_an = models.IntegerField(
        default=30,
        verbose_name="Plafond jours/an"
    )

    report_autorise = models.BooleanField(
        default=True,
        verbose_name="Report autorisé"
    )
    jours_report_max = models.IntegerField(
        default=15,
        verbose_name="Jours de report maximum"
    )
    delai_prise_report = models.IntegerField(
        default=365,
        verbose_name="Délai de prise du report (jours)"
    )

    jours_supp_anciennete = models.JSONField(
        default=dict,
        verbose_name="Jours supplémentaires ancienneté",
        help_text='Format JSON: {"5": 1, "10": 2} = +1 jour après 5 ans, +2 après 10 ans'
    )

    prise_compte_temps_partiel = models.BooleanField(
        default=True,
        verbose_name="Prise en compte temps partiel"
    )

    class Meta:
        verbose_name = "Paramètre calcul congés"
        verbose_name_plural = "Paramètres calcul congés"

    def __str__(self):
        return f"Paramètres - {self.configuration.nom}"


# 5. AcquisitionConges
class AcquisitionConges(models.Model):
    """Solde de congés d'un employé pour une année"""

    employe = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='acquisitions_conges'
    )
    annee_reference = models.IntegerField(verbose_name="Année de référence")

    jours_acquis = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Jours acquis"
    )
    jours_pris = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Jours pris"
    )
    jours_restants = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Jours restants"
    )

    jours_report_anterieur = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Report antérieur"
    )
    jours_report_nouveau = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Nouveau report"
    )

    date_calcul = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de calcul"
    )
    date_maj = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de mise à jour"
    )

    class Meta:
        unique_together = ['employe', 'annee_reference']
        indexes = [
            models.Index(fields=['employe', 'annee_reference']),
        ]
        verbose_name = "Acquisition de congés"
        verbose_name_plural = "Acquisitions de congés"

    def __str__(self):
        return f"{self.employe} - {self.annee_reference}"

    def save(self, *args, **kwargs):
        """Recalcule les jours restants automatiquement"""
        self.jours_restants = (
                self.jours_acquis +
                self.jours_report_anterieur -
                self.jours_pris
        )
        super().save(*args, **kwargs)


# ========================================
# 6. ABSENCE (MODÈLE PRINCIPAL)
# ========================================
class Absence(models.Model):
    """Déclaration d'absence d'un employé"""

    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('EN_ATTENTE_MANAGER', 'En attente du manager'),
        ('EN_ATTENTE_RH', 'En attente des RH'),
        ('VALIDE', 'Validée'),
        ('REJETE', 'Rejetée'),
        ('ANNULE', 'Annulée'),
    ]

    PERIODE_CHOICES = [
        ('JOURNEE_COMPLETE', 'Journée complète'),
        ('MATIN', 'Matin'),
        ('APRES_MIDI', 'Après-midi'),
    ]

    # 1. Identité
    employe = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='absences',
        verbose_name="Employé"
    )

    type_absence = models.ForeignKey(
        'absence.TypeAbsence',
        on_delete=models.PROTECT,
        verbose_name="Type d'absence"
    )

    # 2. Période
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")

    # ✅ UN SEUL CHAMP : période
    periode = models.CharField(
        max_length=20,
        choices=PERIODE_CHOICES,
        default='JOURNEE_COMPLETE',
        verbose_name="Période"
    )

    # 3. Calculs
    jours_ouvrables = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Jours ouvrables"
    )
    jours_calendaires = models.IntegerField(
        default=0,
        verbose_name="Jours calendaires"
    )

    # 4. Statut et validation
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='BROUILLON',
        verbose_name="Statut"
    )

    manager_validateur = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='absences_validees_manager',
        verbose_name="Validateur manager"
    )

    rh_validateur = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='absences_validees_rh',
        verbose_name="Validateur RH"
    )

    date_validation_manager = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date validation manager"
    )
    date_validation_rh = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date validation RH"
    )

    # 5. Justificatifs et commentaires
    justificatif = models.FileField(
        upload_to=upload_justificatif,
        null=True,
        blank=True,
        verbose_name="Justificatif"
    )

    motif = models.TextField(
        blank=True,
        verbose_name="Motif",
        help_text="Raison de l'absence"
    )

    commentaire_manager = models.TextField(
        blank=True,
        verbose_name="Commentaire du manager"
    )

    commentaire_rh = models.TextField(
        blank=True,
        verbose_name="Commentaire des RH"
    )

    # 6. Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    created_by = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        related_name='absences_crees',
        verbose_name="Créé par"
    )

    class Meta:
        verbose_name = "Absence"
        verbose_name_plural = "Absences"
        ordering = ['-date_debut', '-created_at']
        indexes = [
            models.Index(fields=['employe', 'statut']),
            models.Index(fields=['statut', 'date_debut']),
            models.Index(fields=['type_absence', 'date_debut']),
        ]

    def __str__(self):
        return f"{self.employe} - {self.type_absence} ({self.date_debut} au {self.date_fin})"

    def save(self, *args, **kwargs):
        """Sauvegarde avec calculs automatiques et notifications"""
        is_new = self.pk is None

        # Calculer les jours
        self.calculer_jours()

        # Nettoyer les données
        self.full_clean()

        # Pour les nouvelles absences, définir le statut
        if not self.pk and self.statut == 'BROUILLON':
            if self.motif or self.justificatif:
                self.statut = 'EN_ATTENTE_MANAGER'

        super().save(*args, **kwargs)

        # ✅ NOTIFICATION : Nouvelle demande créée
        if is_new and self.statut == 'EN_ATTENTE_MANAGER':
            self._notifier_nouvelle_demande()

    def clean(self):
        """Validation des données"""
        super().clean()

        # ✅ 0. FORCER JOURNEE_COMPLETE POUR PLUSIEURS JOURS (AVANT VALIDATION)
        if self.date_debut and self.date_fin:
            if self.date_debut != self.date_fin:
                if self.periode and self.periode != 'JOURNEE_COMPLETE':
                    self.periode = 'JOURNEE_COMPLETE'

        # ✅ 1. Vérifier les dates
        if self.date_fin < self.date_debut:
            raise ValidationError({
                'date_fin': "La date de fin ne peut pas être antérieure à la date de début"
            })

        # ✅ 2. Vérifier que les demi-journées sont UNIQUEMENT pour un même jour
        if self.date_debut != self.date_fin:
            if self.periode != 'JOURNEE_COMPLETE':
                raise ValidationError({
                    'periode': 'Les demi-journées ne sont autorisées que pour une absence d\'un seul jour'
                })

        # 3. Vérifier le justificatif si obligatoire
        if (self.type_absence.justificatif_obligatoire and
                not self.justificatif and
                self.statut != 'BROUILLON'):
            raise ValidationError({
                'justificatif': "Un justificatif est obligatoire pour ce type d'absence"
            })

    def calculer_jours(self):
        """
        Calcule automatiquement le nombre de jours avec support des demi-journées
        ✅ CORRECTION : Demi-journées UNIQUEMENT pour un même jour
        """
        if not self.date_debut or not self.date_fin:
            return

        # Jours calendaires
        delta = self.date_fin - self.date_debut
        self.jours_calendaires = delta.days + 1

        # ✅ Si plusieurs jours, forcer "Journée complète"
        if self.date_debut != self.date_fin:
            self.periode = 'JOURNEE_COMPLETE'

        # Calcul jours ouvrables
        jours = Decimal('0.00')
        current = self.date_debut

        while current <= self.date_fin:
            # Ignorer week-ends
            if current.weekday() < 5:  # Lundi à Vendredi

                # ✅ Même jour : Tenir compte de la période
                if self.date_debut == self.date_fin:
                    if self.periode == 'JOURNEE_COMPLETE':
                        jours += Decimal('1.00')
                    else:
                        jours += Decimal('0.50')  # MATIN ou APRES_MIDI

                # ✅ Plusieurs jours : Toujours journée complète
                else:
                    jours += Decimal('1.00')

            current += timezone.timedelta(days=1)

        self.jours_ouvrables = jours

    # ========================================
    # MÉTHODES DE NOTIFICATION
    # ========================================

    def _notifier_nouvelle_demande(self):
        """Notifier le manager d'une nouvelle demande"""
        manager = self.employe.get_manager_departement()

        if manager:
            NotificationAbsence.creer_notification(
                destinataire=manager,
                absence=self,
                type_notif='DEMANDE_CREEE',
                contexte='MANAGER',  # ✅ CONTEXTE MANAGER
                message=f"{self.employe.nom} {self.employe.prenoms} a créé une demande d'absence ({self.type_absence.libelle}) du {self.date_debut.strftime('%d/%m/%Y')} au {self.date_fin.strftime('%d/%m/%Y')}"
            )

    def _notifier_validation_manager(self):
        """Notifier l'employé et les RH après validation manager"""

        # 1. Notification à l'employé (CONTEXTE EMPLOYE)
        NotificationAbsence.creer_notification(
            destinataire=self.employe,
            absence=self,
            type_notif='VALIDATION_MANAGER',
            contexte='EMPLOYE',  # ✅ CONTEXTE EMPLOYE
            message=f"Votre demande d'absence ({self.type_absence.libelle}) a été approuvée par votre manager {self.manager_validateur.nom}"
        )

        # 2. Notification aux RH (CONTEXTE RH) - MÊME si c'est la même personne
        from employee.models import ZY00
        responsables_rh = ZY00.objects.filter(
            roles_attribues__role__CODE='RH',
            roles_attribues__actif=True,
            roles_attribues__date_fin__isnull=True,
            etat='actif'
        ).distinct()

        for rh in responsables_rh:
            NotificationAbsence.creer_notification(
                destinataire=rh,
                absence=self,
                type_notif='DEMANDE_VALIDEE_MANAGER',
                contexte='RH',  # ✅ CONTEXTE RH
                message=f"Nouvelle demande à valider (RH) : {self.employe.nom} {self.employe.prenoms} - {self.type_absence.libelle} - Approuvée par {self.manager_validateur.nom}"
            )

    def _notifier_rejet_manager(self):
        """Notifier l'employé du rejet par le manager"""
        NotificationAbsence.creer_notification(
            destinataire=self.employe,
            absence=self,
            type_notif='REJET_MANAGER',
            contexte='EMPLOYE',  # ✅ CONTEXTE EMPLOYE
            message=f"Votre demande d'absence ({self.type_absence.libelle}) a été rejetée par votre manager"
        )

    def _notifier_validation_rh(self):
        """Notifier l'employé de la validation finale par les RH"""
        NotificationAbsence.creer_notification(
            destinataire=self.employe,
            absence=self,
            type_notif='VALIDATION_RH',
            contexte='EMPLOYE',  # ✅ CONTEXTE EMPLOYE
            message=f"Votre demande d'absence ({self.type_absence.libelle}) a été validée par les RH. Elle est maintenant confirmée."
        )

    def _notifier_rejet_rh(self):
        """Notifier l'employé du rejet par les RH"""
        NotificationAbsence.creer_notification(
            destinataire=self.employe,
            absence=self,
            type_notif='REJET_RH',
            contexte='EMPLOYE',  # ✅ CONTEXTE EMPLOYE
            message=f"Votre demande d'absence ({self.type_absence.libelle}) a été rejetée par les RH"
        )

    def _notifier_annulation(self):
        """Notifier le manager de l'annulation"""
        manager = self.employe.get_manager_departement()

        if manager:
            NotificationAbsence.creer_notification(
                destinataire=manager,
                absence=self,
                type_notif='ABSENCE_ANNULEE',
                contexte='MANAGER',  # ✅ CONTEXTE MANAGER
                message=f"{self.employe.nom} {self.employe.prenoms} a annulé sa demande d'absence ({self.type_absence.libelle})"
            )

    # ========================================
    # MÉTHODES DE GESTION DES SOLDES
    # ========================================

    def get_solde_disponible(self):
        """Retourne le solde de congés disponible selon le système N+1"""
        from .models import AcquisitionConges

        annee_absence = self.date_debut.year
        annee_acquisition = annee_absence - 1

        try:
            acquisition = AcquisitionConges.objects.get(
                employe=self.employe,
                annee_reference=annee_acquisition
            )
            return acquisition.jours_restants
        except AcquisitionConges.DoesNotExist:
            return Decimal('0.00')

    def decompter_solde(self):
        """Déduit les jours du solde selon le système N+1"""
        from .models import AcquisitionConges

        if not self.type_absence.decompte_solde:
            return

        annee_absence = self.date_debut.year
        annee_acquisition = annee_absence - 1

        try:
            with transaction.atomic():
                acquisition = AcquisitionConges.objects.select_for_update().get(
                    employe=self.employe,
                    annee_reference=annee_acquisition
                )
                acquisition.jours_pris += self.jours_ouvrables
                acquisition.save()

        except AcquisitionConges.DoesNotExist:
            AcquisitionConges.objects.create(
                employe=self.employe,
                annee_reference=annee_acquisition,
                jours_acquis=Decimal('0.00'),
                jours_pris=self.jours_ouvrables,
                jours_restants=-self.jours_ouvrables,
                jours_report_anterieur=Decimal('0.00'),
                jours_report_nouveau=Decimal('0.00'),
            )

    def restituer_solde(self):
        """Restitue les jours au solde (en cas d'annulation)"""
        from .models import AcquisitionConges

        if not self.type_absence.decompte_solde:
            return

        annee_absence = self.date_debut.year
        annee_acquisition = annee_absence - 1

        try:
            with transaction.atomic():
                acquisition = AcquisitionConges.objects.select_for_update().get(
                    employe=self.employe,
                    annee_reference=annee_acquisition
                )
                acquisition.jours_pris -= self.jours_ouvrables
                acquisition.save()

        except AcquisitionConges.DoesNotExist:
            pass

    # ========================================
    # TRAÇABILITÉ DES VALIDATIONS
    # ========================================

    def creer_trace_validation(self, etape, validateur, decision, commentaire=""):
        """Crée une trace de validation pour la traçabilité"""
        from .models import ValidationAbsence

        ordre = 1 if etape == 'MANAGER' else 2

        ValidationAbsence.objects.create(
            absence=self,
            etape=etape,
            ordre=ordre,
            validateur=validateur,
            decision=decision,
            commentaire=commentaire,
            date_validation=timezone.now()
        )

    # ========================================
    # MÉTHODES DE VALIDATION AVEC NOTIFICATIONS
    # ========================================

    def valider_par_manager(self, manager, decision, commentaire=""):
        """Validation par le manager avec vérification départementale et notifications"""
        if self.statut != 'EN_ATTENTE_MANAGER':
            raise ValidationError("Cette absence n'est pas en attente de validation manager")

        # 1. Vérification des permissions générales
        if not manager.peut_valider_absence_manager():
            raise ValidationError("Vous n'avez pas la permission de valider les absences")

        # 2. VÉRIFICATION CRITIQUE : L'employé est-il dans le département du manager ?
        if not self.employe.est_dans_departement_manager(manager):
            raise ValidationError(
                f"Vous n'êtes pas le manager du département de {self.employe.nom}. "
                f"Seul le manager de son département peut valider cette absence."
            )

        # 3. Vérifier que le manager est bien le manager actif du département
        try:
            from django.apps import apps
            ZYMA = apps.get_model('departement', 'ZYMA')
            ZYAF = apps.get_model('employee', 'ZYAF')

            affectation = ZYAF.objects.filter(
                employe=self.employe,
                date_fin__isnull=True
            ).select_related('poste__DEPARTEMENT').first()

            if not affectation:
                raise ValidationError("L'employé n'a pas d'affectation active")

            is_manager_of_dept = ZYMA.objects.filter(
                employe=manager,
                departement=affectation.poste.DEPARTEMENT,
                actif=True,
                date_fin__isnull=True
            ).exists()

            if not is_manager_of_dept:
                raise ValidationError(
                    f"Vous n'êtes pas le manager actif du département "
                    f"{affectation.poste.DEPARTEMENT.LIBELLE}"
                )

        except Exception as e:
            raise ValidationError(f"Erreur de vérification manager: {str(e)}")

        # 4. Appliquer la décision
        with transaction.atomic():
            if decision == 'APPROUVE':
                self.statut = 'EN_ATTENTE_RH'
                self.manager_validateur = manager
                self.date_validation_manager = timezone.now()
                self.commentaire_manager = commentaire

                # Créer trace de validation
                self.creer_trace_validation('MANAGER', manager, 'APPROUVE', commentaire)

                # Sauvegarder
                self.save(update_fields=[
                    'statut', 'manager_validateur',
                    'date_validation_manager', 'commentaire_manager'
                ])

                # ✅ NOTIFICATIONS
                self._notifier_validation_manager()

            elif decision in ['REJETE', 'RETOURNE']:
                self.statut = decision
                self.manager_validateur = manager
                self.date_validation_manager = timezone.now()
                self.commentaire_manager = commentaire

                # Créer trace de validation
                self.creer_trace_validation('MANAGER', manager, decision, commentaire)

                # Sauvegarder
                self.save(update_fields=[
                    'statut', 'manager_validateur',
                    'date_validation_manager', 'commentaire_manager'
                ])

                # ✅ NOTIFICATION
                self._notifier_rejet_manager()

        return True

    def valider_par_rh(self, rh, decision, commentaire=""):
        """Validation par les RH avec notifications"""
        if self.statut != 'EN_ATTENTE_RH':
            raise ValidationError("Cette absence n'est pas en attente de validation RH")

        # Vérification par permission OU rôle
        if not rh.peut_valider_absence_rh():
            raise ValidationError("Vous n'avez pas la permission de valider les absences RH")

        with transaction.atomic():
            if decision == 'APPROUVE':
                self.statut = 'VALIDE'
                self.rh_validateur = rh
                self.date_validation_rh = timezone.now()
                self.commentaire_rh = commentaire

                # Créer trace de validation
                self.creer_trace_validation('RH', rh, 'APPROUVE', commentaire)

                # Sauvegarder
                self.save(update_fields=[
                    'statut', 'rh_validateur',
                    'date_validation_rh', 'commentaire_rh'
                ])

                # ✅ Décompter les jours du solde (système N+1)
                self.decompter_solde()

                # ✅ NOTIFICATION
                self._notifier_validation_rh()

            elif decision == 'REJETE':
                self.statut = 'REJETE'
                self.rh_validateur = rh
                self.date_validation_rh = timezone.now()
                self.commentaire_rh = commentaire

                # Créer trace de validation
                self.creer_trace_validation('RH', rh, 'REJETE', commentaire)

                # Sauvegarder
                self.save(update_fields=[
                    'statut', 'rh_validateur',
                    'date_validation_rh', 'commentaire_rh'
                ])

                # ✅ NOTIFICATION
                self._notifier_rejet_rh()

        return True

    def annuler(self, utilisateur):
        """
        Annulation d'une absence par l'employé avec notifications

        Scénarios :
        1. EN_ATTENTE_MANAGER : Simple annulation (pas encore validée)
        2. EN_ATTENTE_RH : Annulation après validation manager
        3. VALIDE : Annulation avec restitution des jours
        4. REJETE : Impossible d'annuler
        """
        # ✅ Vérifier que l'absence peut être annulée
        if self.statut == 'REJETE':
            raise ValidationError("Impossible d'annuler une absence rejetée")

        if self.statut == 'ANNULE':
            raise ValidationError("Cette absence est déjà annulée")

        if self.statut == 'BROUILLON':
            raise ValidationError("Cette absence est en brouillon, supprimez-la directement")

        # ✅ Vérifier que c'est bien l'employé propriétaire qui annule
        if self.employe != utilisateur:
            raise ValidationError("Seul l'employé peut annuler sa propre absence")

        with transaction.atomic():
            # Si l'absence était validée ET qu'elle décompte le solde, restituer les jours
            if self.statut == 'VALIDE' and self.type_absence.decompte_solde:
                self.restituer_solde()

            # Changer le statut
            self.statut = 'ANNULE'
            self.save(update_fields=['statut'])

            # ✅ NOTIFICATION
            self._notifier_annulation()

        return True

    # ========================================
    # PROPRIÉTÉS UTILES
    # ========================================

    @property
    def est_validee(self):
        return self.statut == 'VALIDE'

    @property
    def est_en_attente(self):
        return self.statut in ['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH']

    @property
    def duree_jours(self):
        return self.jours_calendaires

    @property
    def prochain_validateur(self):
        """Retourne le prochain validateur attendu"""
        if self.statut == 'EN_ATTENTE_MANAGER':
            return self.employe.get_manager_departement()
        elif self.statut == 'EN_ATTENTE_RH':
            from employee.models import ZY00
            return ZY00.objects.filter(
                roles_attribues__role__CODE='RH',
                roles_attribues__actif=True,
                roles_attribues__date_fin__isnull=True,
                etat='actif'
            ).first()
        return None

    @property
    def peut_modifier(self):
        """
        L'employé peut modifier son absence si :
        - BROUILLON
        - RETOURNE (pour correction)
        """
        return self.statut in ['BROUILLON', 'RETOURNE']

    @property
    def peut_supprimer(self):
        """
        L'employé peut supprimer son absence si :
        - BROUILLON
        - EN_ATTENTE_MANAGER (avant validation du manager)
        - REJETE (après rejet)
        - ANNULE (déjà annulée)
        """
        return self.statut in ['BROUILLON', 'EN_ATTENTE_MANAGER', 'REJETE', 'ANNULE']

    @property
    def peut_annuler(self):
        """
        L'employé peut annuler son absence si :
        - EN_ATTENTE_MANAGER (avant validation)
        - EN_ATTENTE_RH (entre les deux validations)
        - VALIDE (après validation complète, avec restitution des jours)
        """
        return self.statut in ['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'VALIDE']

    @property
    def annee_acquisition_utilisee(self):
        """Retourne l'année d'acquisition utilisée (système N+1)"""
        return self.date_debut.year - 1

    # ========================================
    # MÉTHODES DE CLASSE
    # ========================================

    @classmethod
    def get_absences_a_valider_par_manager(cls, manager):
        """
        Retourne les absences que ce manager peut valider
        (uniquement les employés de ses départements)
        """
        from django.apps import apps
        ZYMA = apps.get_model('departement', 'ZYMA')
        ZYAF = apps.get_model('employee', 'ZYAF')

        departements_geres = ZYMA.objects.filter(
            employe=manager,
            actif=True,
            date_fin__isnull=True
        ).values_list('departement', flat=True)

        if not departements_geres:
            return cls.objects.none()

        employes_departements = ZYAF.objects.filter(
            poste__DEPARTEMENT__in=departements_geres,
            date_fin__isnull=True,
            employe__etat='actif'
        ).values_list('employe', flat=True).distinct()

        return cls.objects.filter(
            employe__in=employes_departements,
            statut='EN_ATTENTE_MANAGER'
        ).select_related('employe', 'type_absence')

    @classmethod
    def get_absences_a_valider_par_rh(cls, rh):
        """
        Retourne toutes les absences en attente de validation RH
        (si l'utilisateur a les permissions RH)
        """
        if not rh.peut_valider_absence_rh():
            return cls.objects.none()

        return cls.objects.filter(
            statut='EN_ATTENTE_RH'
        ).select_related('employe', 'type_absence', 'manager_validateur')


# ========================================
# MODÈLE DE NOTIFICATION
# ========================================

class NotificationAbsence(models.Model):
    """Notifications pour le workflow des absences ET des tâches GTA"""

    TYPE_CHOICES = [
        # Absences
        ('DEMANDE_CREEE', 'Nouvelle demande d\'absence'),
        ('DEMANDE_VALIDEE_MANAGER', 'Demande validée par le manager'),
        ('VALIDATION_MANAGER', 'Validation manager'),
        ('REJET_MANAGER', 'Rejet manager'),
        ('VALIDATION_RH', 'Validation RH'),
        ('REJET_RH', 'Rejet RH'),
        ('ABSENCE_ANNULEE', 'Absence annulée'),

        # ✅ NOUVEAU : Tâches GTA
        ('TACHE_ASSIGNEE', 'Tâche assignée'),
        ('TACHE_REASSIGNEE', 'Tâche réassignée'),
        ('TACHE_MODIFIEE', 'Tâche modifiée'),
        ('STATUT_TACHE_CHANGE', 'Statut de tâche modifié'),
        ('ECHEANCE_TACHE_PROCHE', 'Échéance de tâche proche'),
        ('TACHE_TERMINEE', 'Tâche terminée'),
        ('COMMENTAIRE_TACHE', 'Nouveau commentaire sur tâche'),
    ]

    CONTEXTE_CHOICES = [
        ('EMPLOYE', 'En tant qu\'employé'),
        ('MANAGER', 'En tant que manager'),
        ('RH', 'En tant que RH'),
        ('GTA', 'Gestion Temps et Activités'),  # ✅ NOUVEAU
    ]

    destinataire = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='notifications_absences',
        verbose_name="Destinataire"
    )

    # ✅ MODIFIER : Rendre absence optionnelle
    absence = models.ForeignKey(
        'Absence',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Absence",
        null=True,  # ✅ NOUVEAU
        blank=True  # ✅ NOUVEAU
    )

    # ✅ NOUVEAU : Référence vers la tâche
    tache = models.ForeignKey(
        'gestion_temps_activite.ZDTA',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Tâche",
        null=True,
        blank=True
    )

    type_notification = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        verbose_name="Type de notification"
    )

    contexte = models.CharField(
        max_length=20,
        choices=CONTEXTE_CHOICES,
        default='EMPLOYE',
        verbose_name="Contexte de la notification"
    )

    message = models.TextField(
        verbose_name="Message"
    )

    lue = models.BooleanField(
        default=False,
        verbose_name="Notification lue"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    date_lecture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )

    class Meta:
        db_table = 'notification_absence'  # Garder le même nom de table
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['destinataire', 'lue']),
            models.Index(fields=['-date_creation']),
            models.Index(fields=['contexte']),
            models.Index(fields=['tache']),  # ✅ NOUVEL INDEX
        ]

    def __str__(self):
        return f"{self.destinataire.nom} - {self.get_type_notification_display()} ({self.get_contexte_display()})"

    def marquer_comme_lue(self):
        """Marquer la notification comme lue"""
        if not self.lue:
            self.lue = True
            self.date_lecture = timezone.now()
            self.save(update_fields=['lue', 'date_lecture'])

    # ✅ NOUVEAU : Méthode pour obtenir l'objet lié (absence ou tâche)
    def get_objet_lie(self):
        """Retourne l'objet lié (absence ou tâche)"""
        if self.absence:
            return self.absence
        elif self.tache:
            return self.tache
        return None

    # ✅ NOUVEAU : Méthode pour obtenir l'URL de l'objet lié
    def get_url(self):
        """Retourne l'URL vers l'objet concerné"""
        if self.absence:
            from django.urls import reverse
            return reverse('absence:notification_detail', args=[self.id])
        elif self.tache:
            from django.urls import reverse
            return reverse('gestion_temps_activite:notification_tache_detail', args=[self.id])
        return '#'

    @classmethod
    def creer_notification(cls, destinataire, type_notif, message, contexte='EMPLOYE', absence=None, tache=None):
        """
        Créer une nouvelle notification (absence OU tâche)

        Args:
            destinataire: Employé destinataire
            type_notif: Type de notification
            message: Message de la notification
            contexte: Contexte (EMPLOYE, MANAGER, RH, GTA)
            absence: Instance d'Absence (optionnel)
            tache: Instance de ZDTA (optionnel)
        """
        return cls.objects.create(
            destinataire=destinataire,
            absence=absence,
            tache=tache,
            type_notification=type_notif,
            contexte=contexte,
            message=message
        )

    @classmethod
    def get_non_lues(cls, employe):
        """Récupérer toutes les notifications non lues d'un employé"""
        return cls.objects.filter(
            destinataire=employe,
            lue=False
        ).select_related('absence', 'tache', 'absence__employe', 'absence__type_absence', 'tache__projet')

    @classmethod
    def count_non_lues(cls, employe):
        """Compter les notifications non lues"""
        return cls.objects.filter(
            destinataire=employe,
            lue=False
        ).count()

    # ✅ NOUVEAU : Filtrer par type (absence ou tâche)
    @classmethod
    def get_notifications_absences(cls, employe):
        """Notifications d'absences uniquement"""
        return cls.objects.filter(
            destinataire=employe,
            absence__isnull=False
        ).select_related('absence', 'absence__employe', 'absence__type_absence')

    @classmethod
    def get_notifications_taches(cls, employe):
        """Notifications de tâches uniquement"""
        return cls.objects.filter(
            destinataire=employe,
            tache__isnull=False
        ).select_related('tache', 'tache__projet', 'tache__assignee')


# 7. ValidationAbsence (Optionnel - pour traçabilité détaillée)
class ValidationAbsence(models.Model):
    """Trace chaque étape de validation"""

    ETAPE_CHOICES = [
        ('MANAGER', 'Validation manager'),
        ('RH', 'Validation RH'),
    ]

    DECISION_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('APPROUVE', 'Approuvé'),
        ('REJETE', 'Rejeté'),
        ('RETOURNE', 'Retourné pour modification'),
    ]

    absence = models.ForeignKey(
        Absence,
        on_delete=models.CASCADE,
        related_name='validations_detail'
    )
    etape = models.CharField(max_length=20, choices=ETAPE_CHOICES)
    ordre = models.IntegerField()

    validateur = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='validations_effectuees'
    )

    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default='EN_ATTENTE'
    )
    commentaire = models.TextField(blank=True)

    date_demande = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['absence', 'etape']
        ordering = ['absence', 'ordre']
        verbose_name = "Validation d'absence"
        verbose_name_plural = "Validations d'absence"

    def __str__(self):
        return f"Validation {self.etape} - {self.absence}"

