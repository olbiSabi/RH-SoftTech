import uuid
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings


class JRClient(models.Model):
    """Modèle pour la gestion des clients"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_client = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code Client",
        editable=False
    )
    raison_sociale = models.CharField(
        max_length=200,
        verbose_name="Raison Sociale"
    )
    
    # Informations de contact
    contact_principal = models.CharField(
        max_length=100,
        verbose_name="Contact principal"
    )
    email_contact = models.EmailField(
        verbose_name="Email contact"
    )
    telephone_contact = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone"
    )
    
    # Adresse
    adresse = models.TextField(
        blank=True,
        null=True,
        verbose_name="Adresse"
    )
    code_postal = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Code Postal"
    )
    ville = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Ville"
    )
    pays = models.CharField(
        max_length=50,
        default="France",
        verbose_name="Pays"
    )
    
    # Informations de facturation
    numero_tva = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Numéro TVA"
    )
    conditions_paiement = models.TextField(
        blank=True,
        null=True,
        verbose_name="Conditions de paiement"
    )
    
    # Statut
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('SUSPENDU', 'Suspendu'),
    ]
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIF'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['raison_sociale']
    
    def __str__(self):
        return f"{self.code_client} - {self.raison_sociale}"
    
    def save(self, *args, **kwargs):
        # Génération automatique du code client
        if not self.code_client:
            prefix = "CL"
            last_client = JRClient.objects.filter(
                code_client__startswith=prefix
            ).order_by('code_client').last()
            
            if last_client:
                try:
                    last_num = int(last_client.code_client.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.code_client = f"{prefix}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def nombre_projets(self):
        """Retourne le nombre de projets du client"""
        return self.projets.count()
    
    @property
    def chiffre_affaires_total(self):
        """Calcule le chiffre d'affaires total avec ce client"""
        return sum(projet.montant_total or 0 for projet in self.projets.all())

    @property
    def projets_actifs(self):
        """Retourne le nombre de projets actifs du client"""
        return self.projets.filter(statut='ACTIF').count()

    @property
    def projets_termines(self):
        """Retourne le nombre de projets terminés du client"""
        return self.projets.filter(statut='TERMINE').count()


class JRProject(models.Model):
    """Modèle pour la gestion des projets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, verbose_name="Code Projet")
    nom = models.CharField(max_length=200, verbose_name="Nom du projet")
    description = models.TextField(blank=True, null=True)
    
    # Gestion du projet
    client = models.ForeignKey(
        JRClient,
        on_delete=models.PROTECT,
        related_name='projets',
        verbose_name="Client"
    )
    
    chef_projet = models.ForeignKey(
        'employee.ZY00', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='pm_projets_diriges',
        verbose_name="Chef de projet"
    )
    
    # Informations financières
    montant_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant total (€)"
    )
    
    # Dates et statut
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin_prevue = models.DateField(verbose_name="Date de fin prévue")
    date_fin_reelle = models.DateField(null=True, blank=True)
    
    STATUT_CHOICES = [
        ('PLANIFIE', 'Planifié'),
        ('ACTIF', 'Actif'),
        ('EN_PAUSE', 'En pause'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='PLANIFIE')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.nom}"

    def save(self, *args, **kwargs):
        """Generation automatique du code projet si non fourni"""
        if not self.code:
            # Format: PROJ-XXXX (numero sequentiel)
            last_project = JRProject.objects.order_by('-created_at').first()
            if last_project and last_project.code and last_project.code.startswith('PROJ-'):
                try:
                    last_num = int(last_project.code.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                # Compter tous les projets pour eviter les doublons
                new_num = JRProject.objects.count() + 1

            self.code = f"PROJ-{new_num:04d}"

            # Verifier l'unicite et incrementer si necessaire
            while JRProject.objects.filter(code=self.code).exists():
                new_num += 1
                self.code = f"PROJ-{new_num:04d}"

        super().save(*args, **kwargs)

    @property
    def progression(self):
        """Calcule la progression du projet basée sur les tickets"""
        total_tickets = self.tickets.count()
        if total_tickets == 0:
            return 0
        tickets_termines = self.tickets.filter(statut='TERMINE').count()
        return round((tickets_termines / total_tickets) * 100, 2)


class JRTicket(models.Model):
    """Modèle principal pour les tickets/tâches"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, verbose_name="Code Ticket")
    
    # Liaison avec le projet
    projet = models.ForeignKey(
        JRProject,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Projet"
    )
    
    # Informations de base
    titre = models.CharField(max_length=200, verbose_name="Titre du ticket")
    description = models.TextField(verbose_name="Description détaillée")
    
    # Priorité
    PRIORITE_CHOICES = [
        ('BASSE', 'Basse'),
        ('MOYENNE', 'Moyenne'),
        ('HAUTE', 'Haute'),
        ('CRITIQUE', 'Critique'),
    ]
    priorite = models.CharField(
        max_length=20, 
        choices=PRIORITE_CHOICES, 
        default='MOYENNE',
        verbose_name="Priorité"
    )
    
    # Workflow
    STATUT_CHOICES = [
        ('OUVERT', 'Ouvert'),
        ('EN_COURS', 'En cours'),
        ('EN_REVUE', 'En revue'),
        ('TERMINE', 'Terminé'),
    ]
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='OUVERT',
        verbose_name="Statut"
    )
    
    # Assignation
    assigne = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pm_tickets_assignes',
        verbose_name="Assigné à"
    )
    
    # Type de ticket
    TYPE_CHOICES = [
        ('TACHE', 'Tâche'),
        ('AMELIORATION', 'Amélioration'),
        ('NOUVELLE_FONCTIONNALITE', 'Nouvelle fonctionnalité'),
        ('BUG', 'Bug'),
    ]
    type_ticket = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default='TACHE',
        verbose_name="Type de ticket"
    )
    
    # Gestion du temps
    estimation_heures = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Estimation (heures)"
    )
    temps_passe = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0,
        verbose_name="Temps passé (heures)"
    )
    
    # Dates
    date_echeance = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date d'échéance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Backlog
    dans_backlog = models.BooleanField(
        default=False,
        verbose_name="Dans le backlog"
    )
    ordre_backlog = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre dans le backlog"
    )
    
    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.titre}"
    
    def save(self, *args, **kwargs):
        # Génération automatique du code si non fourni
        if not self.code:
            prefix = "TK"
            last_ticket = JRTicket.objects.filter(
                code__startswith=prefix
            ).order_by('code').last()

            if last_ticket:
                try:
                    last_num = int(last_ticket.code.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.code = f"{prefix}-{new_num:04d}"

        super().save(*args, **kwargs)


class JRCommentaire(models.Model):
    """Modèle pour les commentaires sur les tickets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        JRTicket,
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name="Ticket"
    )
    
    auteur = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='commentaires_tickets',
        verbose_name="Auteur"
    )
    
    contenu = models.TextField(verbose_name="Contenu du commentaire")
    
    # Mentions d'autres utilisateurs
    mentions = models.ManyToManyField(
        'employee.ZY00',
        blank=True,
        related_name='mentions_commentaires',
        verbose_name="Mentions"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.auteur} sur {self.ticket.code}"


class JRPieceJointe(models.Model):
    """Modèle pour les pièces jointes des tickets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        JRTicket,
        on_delete=models.CASCADE,
        related_name='pieces_jointes',
        verbose_name="Ticket"
    )
    
    fichier = models.FileField(
        upload_to='tickets_pieces_jointes/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf', 'doc', 'docx', 'xls', 'xlsx', 
                    'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar'
                ]
            )
        ],
        verbose_name="Fichier"
    )
    
    nom_original = models.CharField(max_length=255, verbose_name="Nom original")
    taille = models.PositiveIntegerField(verbose_name="Taille (octets)")
    type_mime = models.CharField(max_length=100, verbose_name="Type MIME")
    
    uploaded_by = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Uploadé par"
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.nom_original} - {self.ticket.code}"
    
    @property
    def taille_formattee(self):
        """Retourne la taille formatée en KB/MB"""
        taille = self.taille
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if taille < 1024.0:
                return f"{taille:.1f} {unit}"
            taille /= 1024.0
        return f"{taille:.1f} To"


class JRHistorique(models.Model):
    """Modèle pour suivre l'historique des changements sur les tickets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        JRTicket,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name="Ticket"
    )
    
    utilisateur = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        verbose_name="Utilisateur"
    )
    
    TYPE_CHANGEMENT_CHOICES = [
        ('CREATION', 'Création'),
        ('MODIFICATION', 'Modification'),
        ('STATUT', 'Changement de statut'),
        ('ASSIGNATION', 'Réassignation'),
        ('PRIORITE', 'Changement de priorité'),
        ('COMMENTAIRE', 'Ajout de commentaire'),
        ('PIECE_JOINTE', 'Ajout de pièce jointe'),
    ]
    
    type_changement = models.CharField(
        max_length=30,
        choices=TYPE_CHANGEMENT_CHOICES,
        verbose_name="Type de changement"
    )
    
    champ_modifie = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Champ modifié"
    )
    
    ancienne_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name="Ancienne valeur"
    )
    
    nouvelle_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name="Nouvelle valeur"
    )
    
    description = models.TextField(verbose_name="Description du changement")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique"
        verbose_name_plural = "Historiques"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ticket.code} - {self.type_changement} par {self.utilisateur}"


class JRImputation(models.Model):
    """Modèle pour les imputations de temps sur les tickets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Liaison avec l'employé et le ticket
    employe = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.CASCADE,
        related_name='pm_imputations',
        verbose_name="Employé"
    )
    
    ticket = models.ForeignKey(
        JRTicket,
        on_delete=models.CASCADE,
        related_name='imputations',
        verbose_name="Ticket"
    )
    
    # Période d'imputation
    date_imputation = models.DateField(
        verbose_name="Date d'imputation"
    )
    
    # Temps passé
    heures = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Heures travaillées"
    )
    
    minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Minutes supplémentaires"
    )
    
    # Description du travail effectué
    description = models.TextField(
        verbose_name="Description du travail"
    )
    
    # Type d'activité
    TYPE_ACTIVITE_CHOICES = [
        ('DEVELOPPEMENT', 'Développement'),
        ('ANALYSE', 'Analyse'),
        ('TEST', 'Test'),
        ('REUNION', 'Réunion'),
        ('DOCUMENTATION', 'Documentation'),
        ('SUPPORT', 'Support'),
        ('AUTRE', 'Autre'),
    ]
    
    type_activite = models.CharField(
        max_length=30,
        choices=TYPE_ACTIVITE_CHOICES,
        default='DEVELOPPEMENT',
        verbose_name="Type d'activité"
    )
    
    # Validation
    STATUT_VALIDATION_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
    ]
    
    statut_validation = models.CharField(
        max_length=20,
        choices=STATUT_VALIDATION_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut de validation"
    )
    
    valide_par = models.ForeignKey(
        'employee.ZY00',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pm_imputations_validees',
        verbose_name="Validé par"
    )
    
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    
    commentaire_validation = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire de validation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Imputation de temps"
        verbose_name_plural = "Imputations de temps"
        ordering = ['-date_imputation', '-created_at']
        unique_together = ['employe', 'ticket', 'date_imputation']
    
    def __str__(self):
        return f"{self.employe} - {self.ticket.code} - {self.date_imputation} - {self.total_heures}h"
    
    @property
    def total_heures(self):
        """Calcule le total des heures (heures + minutes)"""
        return float(self.heures) + (self.minutes / 60)

    @property
    def heures_affichage(self):
        """Retourne les heures entières pour l'affichage (prend en compte les heures décimales)"""
        # Convertir tout en minutes, puis extraire les heures entières
        total_minutes = int(float(self.heures) * 60) + (self.minutes or 0)
        return total_minutes // 60

    @property
    def minutes_affichage(self):
        """Retourne les minutes restantes pour l'affichage (prend en compte les heures décimales)"""
        # Convertir tout en minutes, puis extraire les minutes restantes
        total_minutes = int(float(self.heures) * 60) + (self.minutes or 0)
        return total_minutes % 60

    @property
    def total_heures_formatte(self):
        """Retourne le total formaté HH:MM"""
        return f"{self.heures_affichage:02d}:{self.minutes_affichage:02d}"
    
    def valider(self, valide_par, commentaire=""):
        """Valide l'imputation"""
        self.statut_validation = 'VALIDE'
        self.valide_par = valide_par
        self.date_validation = timezone.now()
        self.commentaire_validation = commentaire
        self.save()
        
        # Mettre à jour le temps passé sur le ticket
        self.mettre_a_jour_temps_ticket()
    
    def rejeter(self, valide_par, commentaire):
        """Rejette l'imputation"""
        self.statut_validation = 'REJETE'
        self.valide_par = valide_par
        self.date_validation = timezone.now()
        self.commentaire_validation = commentaire
        self.save()
    
    def mettre_a_jour_temps_ticket(self):
        """Met à jour le temps total passé sur le ticket"""
        if self.statut_validation == 'VALIDE':
            total_temps = JRImputation.objects.filter(
                ticket=self.ticket,
                statut_validation='VALIDE'
            ).aggregate(
                total=Sum(
                    models.F('heures') + models.F('minutes') / 60.0,
                    output_field=models.FloatField()
                )
            )['total'] or 0

            self.ticket.temps_passe = total_temps
            self.ticket.save()


class JRSprint(models.Model):
    """Modèle pour la gestion des sprints"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, verbose_name="Nom du sprint")
    description = models.TextField(blank=True, null=True)
    
    projet = models.ForeignKey(
        JRProject,
        on_delete=models.CASCADE,
        related_name='sprints',
        verbose_name="Projet"
    )
    
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    
    STATUT_CHOICES = [
        ('PLANIFIE', 'Planifié'),
        ('ACTIF', 'Actif'),
        ('TERMINE', 'Terminé'),
    ]
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PLANIFIE'
    )
    
    tickets = models.ManyToManyField(
        JRTicket,
        blank=True,
        related_name='sprints',
        verbose_name="Tickets du sprint"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.nom} - {self.projet.code}"
    
    @property
    def duree_jours(self):
        """Calcule la durée du sprint en jours"""
        return (self.date_fin - self.date_debut).days + 1
    
    @property
    def progression(self):
        """Calcule la progression du sprint"""
        total_tickets = self.tickets.count()
        if total_tickets == 0:
            return 0
        tickets_termines = self.tickets.filter(statut='TERMINE').count()
        return round((tickets_termines / total_tickets) * 100, 2)

    @property
    def tickets_termines(self):
        """Retourne le nombre de tickets terminés"""
        return self.tickets.filter(statut='TERMINE').count()

    @property
    def tickets_en_cours(self):
        """Retourne le nombre de tickets en cours"""
        return self.tickets.filter(statut='EN_COURS').count()

    @property
    def tickets_ouverts(self):
        """Retourne le nombre de tickets ouverts"""
        return self.tickets.filter(statut='OUVERT').count()

    @property
    def tickets_en_revue(self):
        """Retourne le nombre de tickets en revue"""
        return self.tickets.filter(statut='EN_REVUE').count()

    @property
    def tickets_restants(self):
        """Retourne le nombre de tickets non terminés"""
        return self.tickets.exclude(statut='TERMINE').count()

    @property
    def jours_restants(self):
        """Calcule le nombre de jours restants avant la fin du sprint"""
        from django.utils import timezone
        if self.statut != 'ACTIF':
            return 0
        today = timezone.now().date()
        if today > self.date_fin:
            return 0
        return (self.date_fin - today).days
