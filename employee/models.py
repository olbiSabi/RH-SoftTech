#employee/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
import uuid
from django.db.models import Q
import os

# Import du modèle ZDPO depuis l'application departement
from departement.models import ZDPO

def employee_photo_path(instance, filename):
    """Fonction pour définir le chemin de sauvegarde de la photo"""
    ext = filename.split('.')[-1]
    filename = f"{instance.matricule}_photo.{ext}"
    return os.path.join('photos/employes/', filename)


######################
### QuerySet Personnalisé
######################
class ZY00QuerySet(models.QuerySet):
    def actifs(self):
        """Retourne les employés avec AU MOINS UN contrat actif"""
        aujourdhui = timezone.now().date()

        # Note: ZYCO sera défini plus tard, mais c'est OK dans une méthode
        return self.filter(
            contrats__actif=True,
        ).filter(
            Q(contrats__date_fin__isnull=True) |
            Q(contrats__date_fin__gte=aujourdhui)
        ).distinct()

    def actifs_v2(self):
        """Version alternative plus explicite"""
        aujourdhui = timezone.now().date()

        return self.filter(
            Q(contrats__actif=True) & (
                    Q(contrats__date_fin__isnull=True) |
                    Q(contrats__date_fin__gte=aujourdhui)
            )
        ).distinct()

    def inactifs(self):
        """Retourne les employés SANS contrat actif"""
        aujourdhui = timezone.now().date()

        # L'import doit être à l'intérieur de la méthode
        from django.db.models import Exists, OuterRef

        # Nous utiliserons une référence en string pour éviter l'import circulaire
        from django.apps import apps
        ZYCO = apps.get_model('employee', 'ZYCO')

        contrats_actifs = ZYCO.objects.filter(
            employe=OuterRef('pk'),
            actif=True
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=aujourdhui)
        )

        return self.exclude(Exists(contrats_actifs))


######################
###  Manager personnalisé ###
######################
class ZY00Manager(models.Manager):
    def get_queryset(self):
        return ZY00QuerySet(self.model, using=self._db)

    def actifs(self):
        return self.get_queryset().actifs()

    def inactifs(self):
        return self.get_queryset().inactifs()


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
    username = models.CharField(
        max_length=100,
        verbose_name="Nom d'utilisateur",
        blank=True,
        help_text="Nom utilisé pour l'authentification et l'affichage"
    )
    prenomuser = models.CharField(
        max_length=200,
        verbose_name="Prénom utilisateur",
        blank=True,
        help_text="Prénom utilisé pour l'authentification et l'affichage"
    )
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
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employe',
        verbose_name="Compte utilisateur"
    )

    # 🔵 Lien vers l'entreprise (obligatoire pour les employés)
    entreprise = models.ForeignKey(
        'entreprise.Entreprise',
        on_delete=models.PROTECT,  # Empêche la suppression si des employés existent
        null=True,  # Temporairement null pour les employés existants
        blank=True,
        related_name='employes',
        verbose_name="Entreprise",
        help_text="Entreprise à laquelle l'employé est rattaché"
    )

    # 🔵 Convention personnalisée (optionnelle - surcharge de l'entreprise)
    convention_personnalisee = models.ForeignKey(
        'absence.ConfigurationConventionnelle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employes_personnalises',
        verbose_name="Convention personnalisée",
        help_text="Convention spécifique (prioritaire sur celle de l'entreprise)"
    )

    # 🔵 Date d'entrée dans l'entreprise (pour calcul ancienneté)
    date_entree_entreprise = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'entrée dans l'entreprise",
        help_text="Date de première prise de service dans l'entreprise"
    )

    # 🔵 Coefficient temps de travail (pour temps partiel)
    coefficient_temps_travail = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.00,
        verbose_name="Coefficient temps travail",
        help_text="1.00 = temps plein, 0.50 = mi-temps, etc."
    )

    objects = ZY00Manager()

    class Meta:
        db_table = 'ZY00'
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        indexes = [
            models.Index(fields=['entreprise', 'etat']),
        ]

    def __str__(self):
        return f" {self.username} {self.prenomuser}" if self.username else f"{self.nom} {self.prenoms}"

    def clean(self):
        """Validation personnalisée"""
        # Mettre le nom en majuscules
        if self.nom:
            self.nom = self.nom.upper()

        # Initialiser username et prenomuser si vides
        if not self.username:
            self.username = self.nom
        if not self.prenomuser:
            self.prenomuser = self.prenoms

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

        # S'assurer que username et prenomuser sont remplis
        if not self.username:
            self.username = self.nom
        if not self.prenomuser:
            self.prenomuser = self.prenoms

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def est_actif(self):
        """Calcule dynamiquement si l'employé est actif basé sur les contrats."""
        from employee.services.status_service import StatusService
        return StatusService.is_active(self)

    def synchroniser_etat(self):
        """Synchronise le champ `etat` avec la réalité métier."""
        from employee.services.status_service import StatusService
        return StatusService.synchronize_status(self)

    @property
    def convention_applicable(self):
        """Retourne la convention applicable à l'employé."""
        from employee.services.status_service import StatusService
        return StatusService.get_applicable_convention(self)

    @property
    def anciennete_annees(self):
        """Calcule l'ancienneté en années complètes."""
        from employee.services.status_service import StatusService
        return StatusService.calculate_seniority_years(self)

    def est_manager_departement(self):
        """Vérifie si l'employé est manager d'un département."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.is_manager(self)

    def get_departements_geres(self):
        """Retourne les départements gérés par cet employé (s'il est manager)."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.get_managed_departments(self)

    def get_subordonnes_hierarchiques(self):
        """Retourne tous les subordonnés (employés des départements gérés)."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.get_subordinates(self)

    def peut_valider_absence_rh(self):
        """Vérifie si l'employé peut valider les absences RH."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_validate_absence_as_rh(self)

    def peut_valider_absence_manager(self):
        """Vérifie si l'employé peut valider les absences en tant que manager."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_validate_absence_as_manager(self)

    def fait_partie_equipe_de(self, autre_employe):
        """Vérifie si cet employé fait partie de l'équipe d'un autre employé."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.is_in_team_of(self, autre_employe)

    def est_manager_de(self, autre_employe):
        """Vérifie si cet employé est manager d'un autre employé."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.is_manager_of(self, autre_employe)

    def est_dans_departement_manager(self, manager):
        """Vérifie si cet employé est dans un département géré par le manager."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.is_in_department_of_manager(self, manager)

    def get_manager_departement(self):
        """Retourne le manager du département de l'employé."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.get_manager_of_employee(self)

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
        from employee.services.status_service import StatusService
        StatusService.deactivate_associated_data(self)

    def get_manager_responsable(self):
        """Retourne l'objet ZYMA du manager responsable de cet employé."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.get_manager_record(self)

    def is_manager(self):
        """Vérifie si l'employé est un manager."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.is_manager(self)

    def has_role(self, role_code):
        """
        Vérifie si l'employé a un rôle spécifique actif.
        Délègue à PermissionService.

        Args:
            role_code (str): Code du rôle (ex: 'DRH', 'MANAGER', 'COMPTABLE')

        Returns:
            bool: True si l'employé a ce rôle actif
        """
        from employee.services.permission_service import PermissionService
        return PermissionService.has_role(self, role_code)

    def get_roles(self):
        """
        Récupère tous les rôles actifs de l'employé.
        Délègue à PermissionService.

        Returns:
            QuerySet: Liste des attributions de rôles actives
        """
        from employee.services.permission_service import PermissionService
        return PermissionService.get_roles(self)

    def has_permission(self, permission_name):
        """
        Vérifie si l'employé a une permission spécifique via ses rôles.
        Délègue à PermissionService.

        Args:
            permission_name (str): Nom de la permission

        Returns:
            bool: True si au moins un des rôles actifs a cette permission
        """
        from employee.services.permission_service import PermissionService
        return PermissionService.has_permission(self, permission_name)

    def add_role(self, role_code, date_debut=None, created_by=None):
        """
        Ajoute un rôle à l'employé.
        Délègue à PermissionService.

        Args:
            role_code (str): Code du rôle à ajouter
            date_debut (date): Date de début (défaut: aujourd'hui)
            created_by (ZY00): Employé qui crée l'attribution

        Returns:
            ZYRE: L'attribution créée
        """
        from employee.services.permission_service import PermissionService
        return PermissionService.add_role(self, role_code, date_debut, created_by)

    def remove_role(self, role_code):
        """
        Retire un rôle à l'employé (désactive l'attribution).
        Délègue à PermissionService.

        Args:
            role_code (str): Code du rôle à retirer
        """
        from employee.services.permission_service import PermissionService
        PermissionService.remove_role(self, role_code)

    def peut_gerer_parametrage_app(self):
        """Vérifie si l'employé peut gérer le paramétrage de l'application."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_app_settings(self)

    def peut_gerer_parametrage_absence(self):
        """Alias pour la gestion des absences."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_app_settings(self)

    def peut_gerer_parametrage_entreprise(self):
        """Alias pour la gestion de l'entreprise."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_app_settings(self)

    def est_drh(self):
        """Vérifie si l'employé est DRH."""
        from employee.services.permission_service import PermissionService
        return PermissionService.is_drh(self)

    def est_assistant_rh(self):
        """Vérifie si l'employé est assistant RH."""
        from employee.services.permission_service import PermissionService
        return PermissionService.is_assistant_rh(self)

    def peut_gerer_employes(self):
        """Vérifie si l'employé peut accéder au menu Salariés."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_employees(self)

    def peut_embaucher(self):
        """Vérifie si l'employé peut embaucher."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_hire(self)

    def get_equipe_manager(self):
        """Retourne l'équipe complète du manager."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.get_team_members(self)

    def get_collaborateurs_meme_departement(self):
        """Retourne tous les collaborateurs du même département."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.get_colleagues_same_department(self)

    def get_departement_actuel(self):
        """Retourne le département actuel de l'employé."""
        from employee.services.hierarchy_service import HierarchyService
        return HierarchyService.get_current_department(self)


    # ==================== MÉTHODES GESTION TEMPS & ACTIVITÉS ====================
    def peut_gerer_clients(self):
        """Vérifie si l'employé peut gérer les clients."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_clients(self)

    def peut_gerer_activites(self):
        """Vérifie si l'employé peut gérer les activités."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_activities(self)

    def peut_gerer_projets(self):
        """Vérifie si l'employé peut gérer les projets."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_projects(self)

    def peut_gerer_taches(self):
        """Vérifie si l'employé peut créer/modifier/supprimer des tâches."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_manage_tasks(self)

    def peut_valider_imputations(self):
        """Vérifie si l'employé peut valider les imputations de temps."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_validate_time_entries(self)

    def peut_voir_toutes_imputations(self):
        """Vérifie si l'employé peut voir toutes les imputations."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_view_all_time_entries(self)

    def peut_creer_imputation(self):
        """Vérifie si l'employé peut créer des imputations de temps."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_create_time_entry(self)

    def peut_voir_taches(self):
        """Vérifie si l'employé peut voir les tâches."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_view_tasks(self)

    def peut_uploader_documents(self):
        """Vérifie si l'employé peut uploader des documents."""
        from employee.services.permission_service import PermissionService
        return PermissionService.can_upload_documents(self)



######################
###  Security  ###
######################
class UserSecurity(models.Model):
    """Modèle pour gérer la sécurité des utilisateurs"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='security'
    )
    login_attempts = models.IntegerField(default=0)
    last_login_attempt = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_security'
        verbose_name = "Sécurité utilisateur"
        verbose_name_plural = "Sécurités utilisateurs"

    def __str__(self):
        return f"Sécurité de {self.user.username}"

    def increment_attempts(self):
        """Incrémenter les tentatives et vérifier le blocage"""
        self.login_attempts += 1
        self.last_login_attempt = timezone.now()

        if self.login_attempts >= 3:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(hours=24)
            print(f"🔒 COMPTE BLOQUÉ: {self.user.username}")

        self.save()
        return self.is_locked

    def is_account_locked(self):
        """Vérifier si le compte est actuellement bloqué"""
        # Si pas bloqué, retourner False
        if not self.is_locked:
            return False

        # Si bloqué sans date de fin, retourner True
        if self.is_locked and not self.locked_until:
            return True

        # Si bloqué avec date de fin expirée, débloquer
        if self.is_locked and self.locked_until and timezone.now() > self.locked_until:
            print(f"🔓 DÉBLOCAGE AUTOMATIQUE: période expirée pour {self.user.username}")
            self.reset_attempts()
            return False

        # Si bloqué avec date de fin valide, retourner True
        return True

    def reset_attempts(self):
        """Réinitialiser complètement les tentatives - VERSION CORRIGÉE"""
        print(f"🔄 RÉINITIALISATION pour {self.user.username}")
        print(f"AVANT: attempts={self.login_attempts}, locked={self.is_locked}")

        self.login_attempts = 0
        self.last_login_attempt = None
        self.is_locked = False  # ← CE CHAMP DOIT DEVENIR FALSE
        self.locked_until = None

        self.save()

        print(f"APRÈS: attempts={self.login_attempts}, locked={self.is_locked}")
        print(f"✅ COMPTE {self.user.username} DÉBLOQUÉ")


######################
### Historique Nom Prénom ZYNP ###
######################
class ZYNP(models.Model):
    """Table d'historique des noms et prénoms des employés"""

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='historique_noms_prenoms',
        verbose_name="Employé"
    )
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenoms = models.CharField(max_length=200, verbose_name="Prénom(s)")
    date_debut_validite = models.DateField(verbose_name="Date de début de validité")
    date_fin_validite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de validité"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'ZYNP'
        verbose_name = "Historique nom/prénom"
        verbose_name_plural = "Historiques noms/prénoms"
        ordering = ['-date_debut_validite', '-date_creation']

    def __str__(self):
        return f"{self.employe.matricule} - {self.nom} {self.prenoms} ({self.date_debut_validite})"

    def clean(self):
        """Validation personnalisée"""
        # Mettre le nom en majuscules
        if self.nom:
            self.nom = self.nom.upper()

        # Transformer le premier caractère du prenoms en majuscule
        if self.prenoms:
            self.prenoms = self.prenoms.strip()
            if self.prenoms:
                self.prenoms = self.prenoms[0].upper() + self.prenoms[1:]

        # Vérifier que la date de fin est après la date de début
        if self.date_fin_validite and self.date_fin_validite <= self.date_debut_validite:
            raise ValidationError({
                'date_fin_validite': "La date de fin doit être supérieure à la date de début."
            })

        # VALIDATION: Éviter les chevauchements de dates
        if self.employe and self.date_debut_validite:
            chevauchements = ZYNP.objects.filter(
                employe=self.employe
            ).exclude(pk=self.pk)  # Exclure l'instance courante en cas de modification

            for existant in chevauchements:
                # Vérifier les chevauchements
                debut_chevauche = (
                        existant.date_debut_validite <= self.date_debut_validite and
                        (existant.date_fin_validite is None or existant.date_fin_validite >= self.date_debut_validite)
                )

                fin_chevauche = (
                        self.date_fin_validite and
                        existant.date_debut_validite <= self.date_fin_validite and
                        (existant.date_fin_validite is None or existant.date_fin_validite >= self.date_fin_validite)
                )

                encadrement = (
                        self.date_debut_validite <= existant.date_debut_validite and
                        (self.date_fin_validite is None or self.date_fin_validite >= existant.date_debut_validite)
                )

                if debut_chevauche or fin_chevauche or encadrement:
                    raise ValidationError({
                        'date_debut_validite': f"Chevauchement avec l'historique du {existant.date_debut_validite} au {existant.date_fin_validite or 'présent'}. Veuillez ajuster les dates."
                    })

    def save(self, *args, **kwargs):
        """S'assurer que les validations sont exécutées"""
        self.full_clean()
        # 🆕 Mettre à jour ZY00 si cet historique est actif
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si c'est un nouvel historique actif ou si un historique existant devient actif
        if self.actif and not self.date_fin_validite:
            self.update_employe_username()

    def update_employe_username(self):
        """Mettre à jour les champs username et prenomuser dans ZY00"""
        try:
            self.employe.username = self.nom
            self.employe.prenomuser = self.prenoms
            self.employe.save(update_fields=['username', 'prenomuser'])
        except Exception as e:
            # Logger l'erreur mais ne pas bloquer la sauvegarde
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la mise à jour des champs username/prenomuser: {e}")

    def delete(self, *args, **kwargs):
        """Gérer la suppression d'un historique actif"""
        employe = self.employe
        was_active = self.actif and not self.date_fin_validite

        super().delete(*args, **kwargs)

        # 🆕 Si l'historique supprimé était actif, trouver le prochain historique actif
        if was_active:
            nouveau_actif = ZYNP.objects.filter(
                employe=employe,
                actif=True,
                date_fin_validite__isnull=True
            ).exclude(pk=self.pk).first()

            if nouveau_actif:
                # Mettre à jour avec le nouvel historique actif
                employe.username = nouveau_actif.nom
                employe.prenomuser = nouveau_actif.prenoms
                employe.save(update_fields=['username', 'prenomuser'])
            else:
                # Revenir aux valeurs originales de ZY00
                employe.username = employe.nom
                employe.prenomuser = employe.prenoms
                employe.save(update_fields=['username', 'prenomuser'])


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


######################
### Personne à Prévenir ZYPP ###
######################
class ZYPP(models.Model):
    """Table des personnes à prévenir en cas d'urgence"""

    LIEN_PARENTE_CHOICES = [
        ('CONJOINT', 'Conjoint(e)'),
        ('PARENT', 'Parent'),
        ('ENFANT', 'Enfant'),
        ('FRERE_SOEUR', 'Frère/Sœur'),
        ('AMI', 'Ami(e)'),
        ('COLLEGUE', 'Collègue'),
        ('VOISIN', 'Voisin(e)'),
        ('AUTRE', 'Autre'),
    ]

    ORDRE_PRIORITE_CHOICES = [
        (1, 'Contact principal'),
        (2, 'Contact secondaire'),
        (3, 'Contact tertiaire'),
    ]

    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='personnes_prevenir',
        verbose_name="Employé"
    )
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=200, verbose_name="Prénom")
    lien_parente = models.CharField(
        max_length=20,
        choices=LIEN_PARENTE_CHOICES,
        verbose_name="Lien de parenté"
    )
    telephone_principal = models.CharField(
        max_length=20,
        verbose_name="Téléphone principal"
    )
    telephone_secondaire = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone secondaire"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email"
    )
    adresse = models.TextField(
        blank=True,
        null=True,
        verbose_name="Adresse complète"
    )
    ordre_priorite = models.IntegerField(
        choices=ORDRE_PRIORITE_CHOICES,
        default=1,
        verbose_name="Ordre de priorité"
    )
    remarques = models.TextField(
        blank=True,
        null=True,
        verbose_name="Remarques"
    )
    date_debut_validite = models.DateField(
        verbose_name="Date de début de validité",
        default=timezone.now
    )
    date_fin_validite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin de validité"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'ZYPP'
        verbose_name = "Personne à prévenir"
        verbose_name_plural = "Personnes à prévenir"
        ordering = ['ordre_priorite', '-date_debut_validite']

    def __str__(self):
        return f"{self.employe.matricule} - {self.prenom} {self.nom} ({self.get_lien_parente_display()}) - Priorité {self.ordre_priorite}"

    def clean(self):
        """Validation personnalisée"""
        # Mettre le nom en majuscules
        if self.nom:
            self.nom = self.nom.upper()

        # Transformer le premier caractère du prénom en majuscule
        if self.prenom:
            self.prenom = self.prenom.strip()
            if self.prenom:
                self.prenom = self.prenom[0].upper() + self.prenom[1:]

        # Vérifier que la date de fin est après la date de début
        if self.date_fin_validite and self.date_fin_validite <= self.date_debut_validite:
            raise ValidationError({
                'date_fin_validite': "La date de fin doit être supérieure à la date de début."
            })

        # Validation: Vérifier qu'il n'y a pas de doublon de priorité actif pour le même employé
        if not self.date_fin_validite:  # Contact actif
            contacts_meme_priorite = ZYPP.objects.filter(
                employe=self.employe,
                ordre_priorite=self.ordre_priorite,
                date_fin_validite__isnull=True
            ).exclude(pk=self.pk)

            if contacts_meme_priorite.exists():
                raise ValidationError({
                    'ordre_priorite': f"Un contact avec la priorité {self.get_ordre_priorite_display()} existe déjà pour cet employé."
                })

        # VALIDATION: Éviter les chevauchements de dates pour la même personne et priorité
        if self.employe and self.date_debut_validite:
            chevauchements = ZYPP.objects.filter(
                employe=self.employe,
                ordre_priorite=self.ordre_priorite
            ).exclude(pk=self.pk)

            for existant in chevauchements:
                debut_chevauche = (
                    existant.date_debut_validite <= self.date_debut_validite and
                    (existant.date_fin_validite is None or existant.date_fin_validite >= self.date_debut_validite)
                )

                fin_chevauche = (
                    self.date_fin_validite and
                    existant.date_debut_validite <= self.date_fin_validite and
                    (existant.date_fin_validite is None or existant.date_fin_validite >= self.date_fin_validite)
                )

                encadrement = (
                    self.date_debut_validite <= existant.date_debut_validite and
                    (self.date_fin_validite is None or self.date_fin_validite >= existant.date_debut_validite)
                )

                if debut_chevauche or fin_chevauche or encadrement:
                    raise ValidationError({
                        'date_debut_validite': f"Chevauchement de dates pour la priorité {self.get_ordre_priorite_display()} avec le contact du {existant.date_debut_validite} au {existant.date_fin_validite or 'présent'}."
                    })

    def save(self, *args, **kwargs):
        """S'assurer que les validations sont exécutées"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_nom_complet(self):
        """Retourne le nom complet de la personne"""
        return f"{self.prenom} {self.nom}"

    def get_telephones(self):
        """Retourne tous les numéros de téléphone disponibles"""
        telephones = [self.telephone_principal]
        if self.telephone_secondaire:
            telephones.append(self.telephone_secondaire)
        return telephones

    def est_actif(self):
        """Vérifie si le contact est actuellement actif"""
        today = timezone.now().date()
        if not self.actif:
            return False
        if self.date_fin_validite and self.date_fin_validite < today:
            return False
        return self.date_debut_validite <= today


######################
### Identité Bancaire ZYIB ###
######################
class ZYIB(models.Model):
    """Table des identités bancaires (RIB)"""

    TYPE_COMPTE_CHOICES = [
        ('COURANT', 'Compte courant'),
        ('EPARGNE', 'Compte épargne'),
        ('JOINT', 'Compte joint'),
    ]

    employe = models.OneToOneField(
        ZY00,
        on_delete=models.CASCADE,
        related_name='identite_bancaire',
        verbose_name="Employé",
        unique=True
    )
    titulaire_compte = models.CharField(
        max_length=200,
        verbose_name="Titulaire du compte",
        help_text="Nom du ou des titulaires du compte"
    )
    nom_banque = models.CharField(
        max_length=100,
        verbose_name="Nom de la banque"
    )
    code_banque = models.CharField(
        max_length=5,
        verbose_name="Code banque",
        help_text="5 chiffres"
    )
    code_guichet = models.CharField(
        max_length=5,
        verbose_name="Code guichet",
        help_text="5 chiffres"
    )
    numero_compte = models.CharField(
        max_length=11,
        verbose_name="Numéro de compte",
        help_text="11 caractères"
    )
    cle_rib = models.CharField(
        max_length=2,
        verbose_name="Clé RIB",
        help_text="2 chiffres"
    )
    iban = models.CharField(
        max_length=34,
        verbose_name="IBAN",
        blank=True,
        null=True,
        help_text="Numéro IBAN international (max 34 caractères)"
    )
    bic = models.CharField(
        max_length=11,
        verbose_name="BIC/SWIFT",
        blank=True,
        null=True,
        help_text="Code BIC/SWIFT (8 ou 11 caractères)"
    )
    type_compte = models.CharField(
        max_length=20,
        choices=TYPE_COMPTE_CHOICES,
        default='COURANT',
        verbose_name="Type de compte"
    )
    domiciliation = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Domiciliation bancaire",
        help_text="Adresse complète de l'agence"
    )
    date_ouverture = models.DateField(
        verbose_name="Date d'ouverture du compte",
        blank=True,
        null=True
    )
    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    remarques = models.TextField(
        blank=True,
        null=True,
        verbose_name="Remarques"
    )

    class Meta:
        db_table = 'ZYIB'
        verbose_name = "Identité bancaire"
        verbose_name_plural = "Identités bancaires"
        ordering = ['-date_modification']

    def __str__(self):
        return f"{self.employe.matricule} - {self.nom_banque} - {self.get_rib()}"

    def clean(self):
        """Validation personnalisée"""
        # Validation code banque (5 chiffres)
        if self.code_banque and not self.code_banque.isdigit():
            raise ValidationError({
                'code_banque': 'Le code banque doit contenir uniquement des chiffres.'
            })
        if self.code_banque and len(self.code_banque) != 5:
            raise ValidationError({
                'code_banque': 'Le code banque doit contenir exactement 5 chiffres.'
            })

        # Validation code guichet (5 chiffres)
        if self.code_guichet and not self.code_guichet.isdigit():
            raise ValidationError({
                'code_guichet': 'Le code guichet doit contenir uniquement des chiffres.'
            })
        if self.code_guichet and len(self.code_guichet) != 5:
            raise ValidationError({
                'code_guichet': 'Le code guichet doit contenir exactement 5 chiffres.'
            })

        # Validation numéro de compte (11 caractères alphanumériques)
        if self.numero_compte and len(self.numero_compte) != 11:
            raise ValidationError({
                'numero_compte': 'Le numéro de compte doit contenir exactement 11 caractères.'
            })

        # Validation clé RIB (2 chiffres)
        if self.cle_rib and not self.cle_rib.isdigit():
            raise ValidationError({
                'cle_rib': 'La clé RIB doit contenir uniquement des chiffres.'
            })
        if self.cle_rib and len(self.cle_rib) != 2:
            raise ValidationError({
                'cle_rib': 'La clé RIB doit contenir exactement 2 chiffres.'
            })

        # Validation IBAN (format français si fourni)
        if self.iban:
            iban_clean = self.iban.replace(' ', '').upper()
            if len(iban_clean) > 34:
                raise ValidationError({
                    'iban': 'L\'IBAN ne peut pas dépasser 34 caractères.'
                })
            # Format français : FR76 suivi de 23 caractères
            if iban_clean.startswith('FR') and len(iban_clean) != 27:
                raise ValidationError({
                    'iban': 'L\'IBAN français doit contenir 27 caractères (FR + 25 caractères).'
                })

        # Validation BIC (8 ou 11 caractères)
        if self.bic:
            bic_clean = self.bic.replace(' ', '').upper()
            if len(bic_clean) not in [8, 11]:
                raise ValidationError({
                    'bic': 'Le code BIC/SWIFT doit contenir 8 ou 11 caractères.'
                })

        # Mettre en majuscules
        if self.titulaire_compte:
            self.titulaire_compte = self.titulaire_compte.upper()
        if self.nom_banque:
            self.nom_banque = self.nom_banque.upper()
        if self.iban:
            self.iban = self.iban.replace(' ', '').upper()
        if self.bic:
            self.bic = self.bic.replace(' ', '').upper()

    def save(self, *args, **kwargs):
        """S'assurer que les validations sont exécutées"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_rib(self):
        """Retourne le RIB complet formaté"""
        return f"{self.code_banque} {self.code_guichet} {self.numero_compte} {self.cle_rib}"

    def get_iban_formate(self):
        """Retourne l'IBAN formaté (par groupes de 4)"""
        if not self.iban:
            return ""
        iban_clean = self.iban.replace(' ', '')
        return ' '.join([iban_clean[i:i + 4] for i in range(0, len(iban_clean), 4)])

    def generer_iban_depuis_rib(self):
        """Génère l'IBAN à partir du RIB (pour la France)"""
        if not all([self.code_banque, self.code_guichet, self.numero_compte, self.cle_rib]):
            return None

        # Construction du BBAN (Basic Bank Account Number)
        bban = f"{self.code_banque}{self.code_guichet}{self.numero_compte}{self.cle_rib}"

        # Calcul de la clé de contrôle IBAN
        # Algorithme : (97 - ((BBAN + "FR00") modulo 97)) = clé
        temp = bban + "152100"  # FR = 1518, 00 = 00 → 152100
        cle = 98 - (int(temp) % 97)

        # Construction de l'IBAN
        iban = f"FR{cle:02d}{bban}"
        return iban

    def valider_rib(self):
        """Valide la cohérence du RIB (calcul de la clé)"""
        if not all([self.code_banque, self.code_guichet, self.numero_compte, self.cle_rib]):
            return False

        # Algorithme de validation de la clé RIB
        # Remplacer les lettres par des chiffres
        compte_numerique = self.numero_compte.upper()
        correspondance = {
            'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5', 'F': '6', 'G': '7', 'H': '8', 'I': '9',
            'J': '1', 'K': '2', 'L': '3', 'M': '4', 'N': '5', 'O': '6', 'P': '7', 'Q': '8', 'R': '9',
            'S': '2', 'T': '3', 'U': '4', 'V': '5', 'W': '6', 'X': '7', 'Y': '8', 'Z': '9'
        }

        for lettre, chiffre in correspondance.items():
            compte_numerique = compte_numerique.replace(lettre, chiffre)

        # Calcul : (89 * code_banque + 15 * code_guichet + 3 * numero_compte + cle) modulo 97 = 0
        try:
            valeur = (
                    89 * int(self.code_banque) +
                    15 * int(self.code_guichet) +
                    3 * int(compte_numerique) +
                    int(self.cle_rib)
            )
            return (valeur % 97) == 0
        except ValueError:
            return False


"""
Modèle de rôles pour les employés
À ajouter dans employee/models.py
"""
######################
### Role ###
######################
class ZYRO(models.Model):
    """
    Table des rôles des employés
    Permet de définir des rôles spécifiques (DRH, Manager, etc.)
    """
    CODE = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code du rôle"
    )
    LIBELLE = models.CharField(
        max_length=100,
        verbose_name="Libellé du rôle"
    )
    DESCRIPTION = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description du rôle"
    )

    # ✅ NOUVEAU : Lien avec Django Groups
    django_group = models.OneToOneField(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_zyro',
        verbose_name="Groupe Django associé",
        help_text="Groupe Django pour les permissions natives"
    )

    # ✅ RENOMMÉ : PERMISSIONS → PERMISSIONS_CUSTOM
    PERMISSIONS_CUSTOM = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Permissions personnalisées",
        help_text="Permissions métier non gérées par Django. Ex: {'can_validate_rh': True}"
    )

    actif = models.BooleanField(
        default=True,
        verbose_name="Rôle actif"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ZYRO'
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        ordering = ['CODE']
        # ✅ NOUVEAU : Permissions Django natives sur le modèle ZYRO
        permissions = [
            ('manage_roles', 'Peut gérer les rôles'),
            ('assign_roles', 'Peut attribuer des rôles'),
            ('view_all_roles', 'Peut voir tous les rôles'),
        ]

    def __str__(self):
        return f"{self.CODE} - {self.LIBELLE}"

    # ✅ NOUVEAU : Synchroniser avec Django Groups
    def sync_to_django_group(self):
        """Synchronise le rôle avec le groupe Django"""
        if not self.django_group:
            # Créer le groupe Django
            group, created = Group.objects.get_or_create(
                name=f"ROLE_{self.CODE}"
            )
            self.django_group = group
            self.save()

        return self.django_group

    # ✅ MODIFIÉ : Vérifier dans Django OU custom
    def has_permission(self, permission_name):
        """
        Vérifie si le rôle a une permission spécifique
        Cherche d'abord dans les permissions Django, puis dans les permissions custom
        """
        # 1. Vérifier dans les permissions Django
        if self.django_group:
            # Format Django complet : 'app_label.codename'
            if '.' in permission_name:
                app_label, codename = permission_name.split('.', 1)
                if self.django_group.permissions.filter(
                        content_type__app_label=app_label,
                        codename=codename
                ).exists():
                    return True
            # Format court : juste le codename
            else:
                if self.django_group.permissions.filter(codename=permission_name).exists():
                    return True

        # 2. Vérifier dans les permissions custom
        return self.PERMISSIONS_CUSTOM.get(permission_name, False)


class ZYRE(models.Model):
    """
    Table d'attribution des rôles aux employés
    Un employé peut avoir plusieurs rôles
    """
    employe = models.ForeignKey(
        'ZY00',
        on_delete=models.CASCADE,
        related_name='roles_attribues',
        verbose_name="Employé"
    )
    role = models.ForeignKey(
        ZYRO,
        on_delete=models.CASCADE,
        related_name='attributions',
        verbose_name="Rôle"
    )
    date_debut = models.DateField(
        verbose_name="Date de début"
    )
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Attribution active"
    )
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roles_crees',
        verbose_name="Créé par"
    )

    class Meta:
        db_table = 'ZYRE'
        verbose_name = "Attribution de rôle"
        verbose_name_plural = "Attributions de rôles"
        ordering = ['-date_debut']
        # ✅ RETIRER unique_together qui cause des problèmes
        # unique_together = [['employe', 'role', 'actif']]  # À RETIRER

    def __str__(self):
        return f"{self.employe.nom} - {self.role.CODE}"

    def clean(self):
        """Validation: une seule attribution active par rôle et employé"""
        from django.core.exceptions import ValidationError

        # ✅ Vérification améliorée
        if self.actif and not self.date_fin:
            existing = ZYRE.objects.filter(
                employe=self.employe,
                role=self.role,
                actif=True,
                date_fin__isnull=True
            ).exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError(
                    f"L'employé a déjà le rôle {self.role.CODE} actif."
                )

    def save(self, *args, **kwargs):
        # ✅ APPELER clean() avant la sauvegarde
        if not kwargs.pop('skip_validation', False):
            self.full_clean()

        super().save(*args, **kwargs)

        # Synchroniser avec les groupes Django
        if hasattr(self.employe, 'user') and self.employe.user:
            if self.actif and not self.date_fin:
                if self.role.django_group:
                    self.employe.user.groups.add(self.role.django_group)
            else:
                if self.role.django_group:
                    self.employe.user.groups.remove(self.role.django_group)


