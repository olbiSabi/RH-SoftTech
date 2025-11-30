from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from employee.models import ZY00
from parametre.models import ZDAB


# ==========================================
# MODÈLE PRINCIPAL - DEMANDE D'ABSENCE (ZDDA)
# ==========================================

class ZDDA(models.Model):
    """
    Table principale des demandes de congés et absences
    ZDDA = Zelio Demande D'Absence
    """

    # Choix pour les statuts
    STATUS_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDEE_MANAGER', 'Validée Manager'),
        ('VALIDEE_RH', 'Validée RH'),
        ('REFUSEE_MANAGER', 'Refusée Manager'),
        ('REFUSEE_RH', 'Refusée RH'),
        ('ANNULEE', 'Annulée'),
    ]

    # Choix pour la durée
    DUREE_CHOICES = [
        ('COMPLETE', 'Journée complète'),
        ('DEMI', 'Demi-journée'),
    ]

    # Choix pour la période (demi-journée)
    PERIODE_CHOICES = [
        ('MATIN', 'Matin'),
        ('APRES_MIDI', 'Après-midi'),
    ]

    # Identifiant et numéro
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_demande = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Numéro de demande"
    )

    # Relations principales
    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='demandes_absence',
        verbose_name="Employé"
    )
    type_absence = models.ForeignKey(
        ZDAB,
        on_delete=models.PROTECT,
        related_name='demandes',
        verbose_name="Type d'absence"
    )

    # Dates et durée
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    duree = models.CharField(
        max_length=10,
        choices=DUREE_CHOICES,
        default='COMPLETE',
        verbose_name="Durée"
    )
    periode = models.CharField(
        max_length=15,
        choices=PERIODE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Période (si demi-journée)"
    )
    nombre_jours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0.5'))],
        verbose_name="Nombre de jours"
    )

    # Motif et justification
    motif = models.TextField(
        blank=True,
        verbose_name="Motif de la demande"
    )
    justificatif = models.FileField(
        upload_to='absences/justificatifs/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Justificatif"
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut"
    )

    # ============ VALIDATION MANAGER ============
    validee_manager = models.BooleanField(default=False, verbose_name="Validée par le manager")
    date_validation_manager = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date validation manager"
    )
    validateur_manager = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_manager_absence',
        verbose_name="Manager validateur"
    )
    commentaire_manager = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire manager"
    )
    motif_refus_manager = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motif refus manager"
    )

    # ============ VALIDATION RH ============
    validee_rh = models.BooleanField(default=False, verbose_name="Validée par RH")
    date_validation_rh = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date validation RH"
    )
    validateur_rh = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_rh_absence',
        verbose_name="RH validateur"
    )
    commentaire_rh = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire RH"
    )
    motif_refus_rh = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motif refus RH"
    )

    # ============ GESTION ============
    est_urgent = models.BooleanField(default=False, verbose_name="Demande urgente")
    est_annulee = models.BooleanField(default=False, verbose_name="Annulée")
    date_annulation = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date d'annulation"
    )
    motif_annulation = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motif d'annulation"
    )

    # ============ SOLDES ============
    solde_avant = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Solde avant"
    )
    solde_apres = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Solde après"
    )

    # ============ NOTIFICATIONS ============
    notification_envoyee_manager = models.BooleanField(
        default=False,
        verbose_name="Notification envoyée au manager"
    )
    notification_envoyee_rh = models.BooleanField(
        default=False,
        verbose_name="Notification envoyée à RH"
    )
    notification_envoyee_employe = models.BooleanField(
        default=False,
        verbose_name="Notification envoyée à l'employé"
    )

    # ============ AUDIT ============
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    created_by = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_absence_creees',
        verbose_name="Créé par"
    )
    updated_by = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_absence_modifiees',
        verbose_name="Modifié par"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="Adresse IP"
    )

    class Meta:
        db_table = 'ZDDA'
        verbose_name = 'Demande d\'absence'
        verbose_name_plural = 'Demandes d\'absence'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employe', 'statut']),
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['statut']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.numero_demande} - {self.employe.nom} {self.employe.prenoms}"

    def clean(self):
        """Validation personnalisée"""
        errors = {}

        # Vérifier que date_fin >= date_debut
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            errors['date_fin'] = "La date de fin doit être supérieure ou égale à la date de début."

        # Vérifier la cohérence durée/période
        if self.duree == 'DEMI' and not self.periode:
            errors['periode'] = "La période doit être spécifiée pour une demi-journée."

        if self.duree == 'COMPLETE' and self.periode:
            self.periode = None

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Générer le numéro de demande si nouveau
        if not self.numero_demande:
            year = timezone.now().year
            last_demande = ZDDA.objects.filter(
                numero_demande__startswith=f'ABS-{year}-'
            ).order_by('-numero_demande').first()

            if last_demande:
                last_number = int(last_demande.numero_demande.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.numero_demande = f'ABS-{year}-{new_number:05d}'

        # Mettre à jour les flags de validation
        self.validee_manager = self.statut in ['VALIDEE_MANAGER', 'VALIDEE_RH']
        self.validee_rh = self.statut == 'VALIDEE_RH'
        self.est_annulee = self.statut == 'ANNULEE'

        # Validation sans updated_by (sera défini par le signal)
        # self.full_clean()  # Commenté car updated_by n'est pas encore défini
        super().save(*args, **kwargs)

    @property
    def est_validee(self):
        """Retourne True si la demande est complètement validée"""
        return self.statut == 'VALIDEE_RH'

    @property
    def est_en_attente_validation(self):
        """Retourne True si la demande est en attente de validation"""
        return self.statut in ['EN_ATTENTE', 'VALIDEE_MANAGER']

    @property
    def est_refusee(self):
        """Retourne True si la demande a été refusée"""
        return self.statut in ['REFUSEE_MANAGER', 'REFUSEE_RH']

    def get_manager(self):
        """Retourne le manager responsable de l'employé"""
        return self.employe.get_manager_responsable()

    def peut_etre_annulee(self):
        """Vérifie si la demande peut être annulée"""
        return self.statut in ['EN_ATTENTE', 'VALIDEE_MANAGER'] and self.date_debut > timezone.now().date()


# ==========================================
# SOLDE DE CONGÉS (ZDSO)
# ==========================================

class ZDSO(models.Model):
    """
    Table des soldes de congés par employé et par année
    ZDSO = Zelio Données SOlde
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employe = models.ForeignKey(
        ZY00,
        on_delete=models.CASCADE,
        related_name='soldes_conges',
        verbose_name="Employé"
    )
    annee = models.IntegerField(verbose_name="Année")

    # ============ CONGÉS PAYÉS ============
    jours_acquis = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=25.0,
        verbose_name="Jours acquis"
    )
    jours_pris = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        verbose_name="Jours pris"
    )
    jours_en_attente = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        verbose_name="Jours en attente"
    )
    jours_disponibles = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=25.0,
        verbose_name="Jours disponibles"
    )
    jours_reportes = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        verbose_name="Jours reportés N-1"
    )

    # ============ RTT ============
    rtt_acquis = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        verbose_name="RTT acquis"
    )
    rtt_pris = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        verbose_name="RTT pris"
    )
    rtt_disponibles = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        verbose_name="RTT disponibles"
    )

    # ============ AUDIT ============
    derniere_maj = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ZDSO'
        verbose_name = 'Solde de congés'
        verbose_name_plural = 'Soldes de congés'
        unique_together = ['employe', 'annee']
        ordering = ['-annee', 'employe']

    def __str__(self):
        return f"{self.employe.nom} {self.employe.prenoms} - {self.annee} - {self.jours_disponibles} jours"

    def calculer_soldes(self):
        """Recalcule automatiquement les soldes disponibles"""
        self.jours_disponibles = (
            self.jours_acquis +
            self.jours_reportes -
            self.jours_pris -
            self.jours_en_attente
        )
        self.rtt_disponibles = self.rtt_acquis - self.rtt_pris
        self.save()

    @classmethod
    def get_or_create_solde(cls, employe, annee=None):
        """Récupère ou crée le solde pour un employé et une année"""
        if annee is None:
            annee = timezone.now().year

        solde, created = cls.objects.get_or_create(
            employe=employe,
            annee=annee,
            defaults={
                'jours_acquis': 25.0,
                'jours_disponibles': 25.0,
            }
        )
        return solde


# ==========================================
# HISTORIQUE DES ABSENCES (ZDHA)
# ==========================================

class ZDHA(models.Model):
    """
    Historique des modifications sur les demandes d'absence
    ZDHA = Zelio Données Historique Absence
    """

    ACTION_CHOICES = [
        ('CREATION', 'Création'),
        ('MODIFICATION', 'Modification'),
        ('VALIDATION_MANAGER', 'Validation Manager'),
        ('VALIDATION_RH', 'Validation RH'),
        ('REFUS_MANAGER', 'Refus Manager'),
        ('REFUS_RH', 'Refus RH'),
        ('ANNULATION', 'Annulation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    demande = models.ForeignKey(
        ZDDA,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name="Demande"
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    utilisateur = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Utilisateur"
    )
    ancien_statut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Ancien statut"
    )
    nouveau_statut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Nouveau statut"
    )
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire"
    )
    donnees_modifiees = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Données modifiées"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="Adresse IP"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date/Heure")

    class Meta:
        db_table = 'ZDHA'
        verbose_name = 'Historique absence'
        verbose_name_plural = 'Historiques absences'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.demande.numero_demande} - {self.action} - {self.timestamp}"


# ==========================================
# JOURS FÉRIÉS (ZDJF)
# ==========================================

class ZDJF(models.Model):
    """
    Table des jours fériés
    ZDJF = Zelio Données Jour Férié
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True, verbose_name="Date")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    fixe = models.BooleanField(default=True, verbose_name="Date fixe")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ZDJF'
        verbose_name = 'Jour férié'
        verbose_name_plural = 'Jours fériés'
        ordering = ['date']

    def __str__(self):
        return f"{self.date.strftime('%d/%m/%Y')} - {self.libelle}"

    @classmethod
    def est_jour_ferie(cls, date):
        """Vérifie si une date est un jour férié"""
        return cls.objects.filter(date=date, actif=True).exists()



######################
### Notifications ZANO ###
######################
class ZANO(models.Model):
    """Table des notifications"""

    TYPE_NOTIFICATION_CHOICES = [
        ('ABSENCE_NOUVELLE', 'Nouvelle demande d\'absence'),
        ('ABSENCE_VALIDEE_MANAGER', 'Absence validée par le manager'),
        ('ABSENCE_REJETEE_MANAGER', 'Absence rejetée par le manager'),
        ('ABSENCE_VALIDEE_RH', 'Absence validée par les RH'),
        ('ABSENCE_REJETEE_RH', 'Absence rejetée par les RH'),
        ('ABSENCE_ANNULEE', 'Absence annulée'),
    ]

    destinataire = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire"
    )
    type_notification = models.CharField(
        max_length=30,
        choices=TYPE_NOTIFICATION_CHOICES,
        verbose_name="Type de notification"
    )
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    message = models.TextField(
        verbose_name="Message"
    )
    lien = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Lien associé",
        help_text="URL vers l'élément concerné"
    )
    demande_absence = models.ForeignKey(
        ZDDA,  # ✅ Utiliser ZDDA directement (pas de guillemets car la classe est déjà définie)
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name="Demande d'absence"
    )
    lue = models.BooleanField(
        default=False,
        verbose_name="Lue"
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
        db_table = 'ZANO'
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['destinataire', 'lue']),
            models.Index(fields=['date_creation']),
        ]

    def __str__(self):
        return f"{self.destinataire.matricule} - {self.titre}"

    def marquer_comme_lue(self):
        """Marquer la notification comme lue"""
        if not self.lue:
            self.lue = True
            self.date_lecture = timezone.now()
            self.save()

    @staticmethod
    def creer_notification_absence(demande_absence, type_notification, destinataire):
        """Créer une notification pour une demande d'absence"""
        from django.urls import reverse

        # Définir le titre et le message selon le type
        messages_config = {
            'ABSENCE_NOUVELLE': {
                'titre': f"Nouvelle demande d'absence - {demande_absence.employe.nom} {demande_absence.employe.prenoms}",
                'message': f"{demande_absence.employe.nom} {demande_absence.employe.prenoms} a fait une demande d'absence du {demande_absence.date_debut.strftime('%d/%m/%Y')} au {demande_absence.date_fin.strftime('%d/%m/%Y')} ({demande_absence.type_absence.LIBELLE})."
            },
            'ABSENCE_VALIDEE_MANAGER': {
                'titre': "Votre demande d'absence a été validée par votre manager",
                'message': f"Votre demande d'absence du {demande_absence.date_debut.strftime('%d/%m/%Y')} au {demande_absence.date_fin.strftime('%d/%m/%Y')} a été validée par votre manager et est en attente de validation RH."
            },
            'ABSENCE_REJETEE_MANAGER': {
                'titre': "Votre demande d'absence a été rejetée",
                'message': f"Votre demande d'absence du {demande_absence.date_debut.strftime('%d/%m/%Y')} au {demande_absence.date_fin.strftime('%d/%m/%Y')} a été rejetée par votre manager."
            },
            'ABSENCE_VALIDEE_RH': {
                'titre': "Votre demande d'absence a été validée",
                'message': f"Votre demande d'absence du {demande_absence.date_debut.strftime('%d/%m/%Y')} au {demande_absence.date_fin.strftime('%d/%m/%Y')} a été validée par les RH. Votre absence est confirmée."
            },
            'ABSENCE_REJETEE_RH': {
                'titre': "Votre demande d'absence a été rejetée par les RH",
                'message': f"Votre demande d'absence du {demande_absence.date_debut.strftime('%d/%m/%Y')} au {demande_absence.date_fin.strftime('%d/%m/%Y')} a été rejetée par les RH."
            },
            'ABSENCE_ANNULEE': {
                'titre': "Une demande d'absence a été annulée",
                'message': f"La demande d'absence du {demande_absence.date_debut.strftime('%d/%m/%Y')} au {demande_absence.date_fin.strftime('%d/%m/%Y')} a été annulée."
            },
        }

        config = messages_config.get(type_notification, {
            'titre': 'Notification',
            'message': 'Vous avez une nouvelle notification.'
        })

        # 🆕 CRÉER LE LIEN SELON LE TYPE DE NOTIFICATION ET LE DESTINATAIRE
        lien = '#'
        try:
            # Si c'est une nouvelle demande, vérifier si le destinataire est RH ou Manager
            if type_notification == 'ABSENCE_NOUVELLE':
                # Vérifier si le destinataire a le rôle DRH
                if destinataire.has_role('DRH'):
                    lien = reverse('absence:rh_validation')
                else:
                    # Sinon c'est un manager
                    lien = reverse('absence:manager_validation')

            # Si c'est une validation/rejet, rediriger vers la liste des demandes de l'employé
            elif type_notification in ['ABSENCE_VALIDEE_MANAGER', 'ABSENCE_REJETEE_MANAGER',
                                       'ABSENCE_VALIDEE_RH', 'ABSENCE_REJETEE_RH']:
                lien = reverse('absence:employe_demandes')

            # Si c'est une annulation
            elif type_notification == 'ABSENCE_ANNULEE':
                if destinataire.has_role('DRH'):
                    lien = reverse('absence:rh_validation')
                else:
                    lien = reverse('absence:manager_validation')
        except Exception as e:
            print(f"Erreur création lien notification: {e}")
            lien = '#'

        # Créer la notification
        notification = ZANO.objects.create(
            destinataire=destinataire,
            type_notification=type_notification,
            titre=config['titre'],
            message=config['message'],
            lien=lien,
            demande_absence=demande_absence
        )

        return notification

    @staticmethod
    def notifier_nouvelle_demande(demande_absence):
        """Notifier le manager lors d'une nouvelle demande"""
        manager = demande_absence.get_manager()
        if manager and manager.employe:
            ZANO.creer_notification_absence(
                demande_absence,
                'ABSENCE_NOUVELLE',
                manager.employe
            )

    @staticmethod
    def notifier_validation_manager(demande_absence):
        """Notifier l'employé et les RH après validation manager"""
        # Notifier l'employé
        ZANO.creer_notification_absence(
            demande_absence,
            'ABSENCE_VALIDEE_MANAGER',
            demande_absence.employe
        )

        # Notifier les utilisateurs RH
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Trouver les utilisateurs ayant le rôle RH
        try:
            from employee.models import ZY00
            employes_rh = ZY00.objects.filter(
                user__groups__name='RH'
            ).distinct()

            for employe_rh in employes_rh:
                ZANO.creer_notification_absence(
                    demande_absence,
                    'ABSENCE_NOUVELLE',
                    employe_rh
                )
        except Exception as e:
            print(f"Erreur notification RH: {e}")

    @staticmethod
    def notifier_rejet_manager(demande_absence):
        """Notifier l'employé après rejet manager"""
        ZANO.creer_notification_absence(
            demande_absence,
            'ABSENCE_REJETEE_MANAGER',
            demande_absence.employe
        )

    @staticmethod
    def notifier_validation_rh(demande_absence):
        """Notifier l'employé après validation RH"""
        ZANO.creer_notification_absence(
            demande_absence,
            'ABSENCE_VALIDEE_RH',
            demande_absence.employe
        )

    @staticmethod
    def notifier_rejet_rh(demande_absence):
        """Notifier l'employé après rejet RH"""
        ZANO.creer_notification_absence(
            demande_absence,
            'ABSENCE_REJETEE_RH',
            demande_absence.employe
        )


# ==========================================
# PÉRIODES DE FERMETURE (ZDPF)
# ==========================================

class ZDPF(models.Model):
    """
    Périodes de fermeture de l'entreprise
    ZDPF = Zelio Données Période Fermeture
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Créé par"
    )

    class Meta:
        db_table = 'ZDPF'
        verbose_name = 'Période de fermeture'
        verbose_name_plural = 'Périodes de fermeture'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.libelle} ({self.date_debut} - {self.date_fin})"

    def clean(self):
        """Validation"""
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError({
                'date_fin': 'La date de fin doit être supérieure ou égale à la date de début.'
            })


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def calculer_jours_ouvres(date_debut, date_fin):
    """
    Calcule le nombre de jours ouvrés entre deux dates
    Exclut les week-ends et les jours fériés
    """
    from datetime import timedelta

    nb_jours = 0
    date_courante = date_debut

    while date_courante <= date_fin:
        # Vérifier si c'est un jour de semaine (0 = lundi, 6 = dimanche)
        if date_courante.weekday() < 5:  # Lundi à vendredi
            # Vérifier si ce n'est pas un jour férié
            if not ZDJF.est_jour_ferie(date_courante):
                nb_jours += 1

        date_courante += timedelta(days=1)

    return Decimal(str(nb_jours))


def mettre_a_jour_solde_conges(employe, annee=None):
    """
    Met à jour le solde de congés d'un employé pour une année donnée
    """
    if annee is None:
        annee = timezone.now().year

    solde = ZDSO.get_or_create_solde(employe, annee)

    # Calculer les jours pris (validés RH)
    jours_pris = ZDDA.objects.filter(
        employe=employe,
        statut='VALIDEE_RH',
        date_debut__year=annee,
        type_absence__CODE__in=['CPN', 'RTT']  # Types qui déduisent du solde
    ).aggregate(total=models.Sum('nombre_jours'))['total'] or Decimal('0.0')

    # Calculer les jours en attente
    jours_en_attente = ZDDA.objects.filter(
        employe=employe,
        statut__in=['EN_ATTENTE', 'VALIDEE_MANAGER'],
        date_debut__year=annee,
        type_absence__CODE__in=['CPN', 'RTT']
    ).aggregate(total=models.Sum('nombre_jours'))['total'] or Decimal('0.0')

    # Mettre à jour le solde
    solde.jours_pris = jours_pris
    solde.jours_en_attente = jours_en_attente
    solde.calculer_soldes()

    return solde