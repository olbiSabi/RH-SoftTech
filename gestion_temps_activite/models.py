# gestion_temps_activite/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import uuid
from decimal import Decimal

from django.db.models import Q

from employee.models import ZY00


class ZDCL(models.Model):
    """Modèle Client - Gestion des clients"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_client = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code Client",
        editable=False  # Rendre non éditable manuellement
    )
    raison_sociale = models.CharField(
        max_length=200,
        verbose_name="Raison Sociale"
    )

    # Informations de contact
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{8,15}$',
            message="Numéro de téléphone invalide"
        )],
        verbose_name="Téléphone"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email"
    )
    personne_contact = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Personne de Contact"
    )
    fonction_contact = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Fonction du Contact"
    )

    # Adresse complète
    adresse_ligne1 = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Adresse Ligne 1"
    )
    adresse_ligne2 = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Adresse Ligne 2"
    )
    ville = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Ville"
    )
    code_postal = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Code Postal"
    )
    pays = models.CharField(
        max_length=100,
        default="Togo",
        verbose_name="Pays"
    )

    # Informations commerciales
    secteur_activite = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Secteur d'Activité"
    )
    type_client = models.CharField(
        max_length=50,
        choices=[
            ('PROSPECT', 'Prospect'),
            ('CLIENT', 'Client Actif'),
            ('INACTIF', 'Client Inactif'),
        ],
        default='PROSPECT',
        verbose_name="Type de Client"
    )

    # Métadonnées
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de Création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de Modification"
    )
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients_crees',
        verbose_name="Créé par"
    )

    class Meta:
        db_table = 'zdcl'
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['raison_sociale']

    def __str__(self):
        return f"{self.code_client} - {self.raison_sociale}"

    def clean(self):
        """Validation et conversion en majuscules"""
        super().clean()
        if self.code_client:
            self.code_client = self.code_client.upper().strip()

    def save(self, *args, **kwargs):
        """Override save pour générer le code client automatiquement"""
        # Si c'est un nouveau client (pas encore de code)
        if not self.code_client:
            # Générer le prochain code
            self.code_client = self.generer_nouveau_code()

        self.full_clean()
        super().save(*args, **kwargs)

    def generer_nouveau_code(self):
        """Génère un nouveau code client formaté CLT-XXX"""
        # Chercher le dernier code client
        dernier_client = ZDCL.objects.all().order_by('-date_creation').first()

        if not dernier_client:
            # Premier client
            nouveau_numero = 1
        else:
            # Extraire le numéro du dernier code
            try:
                dernier_code = dernier_client.code_client
                if '-' in dernier_code:
                    # Format: CLT-001
                    dernier_numero = int(dernier_code.split('-')[1])
                else:
                    # Ancien format ou format différent
                    # Essayer d'extraire les chiffres
                    import re
                    chiffres = re.findall(r'\d+', dernier_code)
                    if chiffres:
                        dernier_numero = int(chiffres[-1])
                    else:
                        dernier_numero = 0
            except (ValueError, IndexError, AttributeError):
                # En cas d'erreur, commencer à 1
                dernier_numero = 0

            nouveau_numero = dernier_numero + 1

        # Formater le code: CLT-001, CLT-002, etc.
        return f"CLT-{nouveau_numero:03d}"

    def clean(self):
        """Validation et conversion en majuscules"""
        super().clean()


    def get_adresse_complete(self):
        """Retourne l'adresse complète formatée"""
        adresse_parts = []
        if self.adresse_ligne1:
            adresse_parts.append(self.adresse_ligne1)
        if self.adresse_ligne2:
            adresse_parts.append(self.adresse_ligne2)
        if self.code_postal or self.ville:
            ville_cp = f"{self.code_postal} {self.ville}".strip()
            adresse_parts.append(ville_cp)
        if self.pays and self.pays != "Togo":
            adresse_parts.append(self.pays)
        return ", ".join(adresse_parts) if adresse_parts else "Adresse non renseignée"


class ZDAC(models.Model):
    """Modèle Types d'Activités - Catégorisation des activités"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_activite = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code Activité"
    )
    libelle = models.CharField(
        max_length=100,
        verbose_name="Libellé"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )

    # Facturation
    facturable = models.BooleanField(
        default=True,
        verbose_name="Facturable"
    )
    taux_horaire_defaut = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux Horaire par Défaut (FCFA)"
    )

    # Période de validité
    date_debut = models.DateField(
        verbose_name="Date de Début",
        help_text="Date à partir de laquelle l'activité est disponible"
    )
    date_fin = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de Fin",
        help_text="Date de fin de validité (vide = illimitée)"
    )

    # Statut
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Désactiver manuellement une activité"
    )

    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de Création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de Modification"
    )

    class Meta:
        db_table = 'zdac'
        verbose_name = "Type d'Activité"
        verbose_name_plural = "Types d'Activités"
        ordering = ['code_activite']

    def __str__(self):
        return f"{self.code_activite} - {self.libelle}"

    def clean(self):
        """Validation et conversion en majuscules"""
        super().clean()
        if self.code_activite:
            self.code_activite = self.code_activite.upper().strip()

        # Validation: date_fin doit être après date_debut
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError({
                'date_fin': 'La date de fin doit être postérieure à la date de début.'
            })

    def save(self, *args, **kwargs):
        """Override save pour forcer la validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def est_en_vigueur(self, date_reference=None):
        """
        Vérifie si l'activité est en vigueur à une date donnée
        Prend en compte le champ actif ET les dates de validité
        """
        from django.utils import timezone

        if not self.actif:
            return False

        if date_reference is None:
            date_reference = timezone.now().date()

        # Vérifier si la date de référence est après la date de début
        if date_reference < self.date_debut:
            return False

        # Vérifier si la date de référence est avant la date de fin (si définie)
        if self.date_fin and date_reference > self.date_fin:
            return False

        return True

    def get_statut_display(self):
        """Retourne le statut formaté pour affichage"""
        from django.utils import timezone

        if not self.actif:
            return "Inactif (manuel)"

        date_actuelle = timezone.now().date()

        if date_actuelle < self.date_debut:
            return f"À venir (dès le {self.date_debut.strftime('%d/%m/%Y')})"

        if self.date_fin:
            if date_actuelle > self.date_fin:
                return f"Expiré (depuis le {self.date_fin.strftime('%d/%m/%Y')})"
            else:
                return f"Actif (jusqu'au {self.date_fin.strftime('%d/%m/%Y')})"

        return "Actif"


class ZDPJ(models.Model):
    """Modèle Projets - Gestion des projets clients"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_projet = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code Projet",
        editable=False  # Rendre non éditable manuellement
    )
    nom_projet = models.CharField(
        max_length=200,
        verbose_name="Nom du Projet"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )

    # Relations
    client = models.ForeignKey(
        ZDCL,
        on_delete=models.PROTECT,
        related_name='projets',
        verbose_name="Client"
    )
    chef_projet = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='projets_diriges',
        verbose_name="Chef de Projet"
    )

    # Budget et planification
    budget_heures = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Budget (heures)"
    )
    budget_montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Budget (FCFA)"
    )
    date_debut = models.DateField(
        verbose_name="Date de Début"
    )
    date_fin_prevue = models.DateField(
        verbose_name="Date de Fin Prévue"
    )
    date_fin_reelle = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de Fin Réelle"
    )

    # Statut et type
    statut = models.CharField(
        max_length=50,
        choices=[
            ('PLANIFIE', 'Planifié'),
            ('EN_COURS', 'En Cours'),
            ('EN_PAUSE', 'En Pause'),
            ('TERMINE', 'Terminé'),
            ('ANNULE', 'Annulé'),
        ],
        default='PLANIFIE',
        verbose_name="Statut"
    )
    type_facturation = models.CharField(
        max_length=50,
        choices=[
            ('FORFAIT', 'Forfait'),
            ('REGIE', 'Régie'),
            ('TEMPS_PASSE', 'Temps Passé'),
        ],
        default='TEMPS_PASSE',
        verbose_name="Type de Facturation"
    )

    # Métadonnées
    priorite = models.CharField(
        max_length=20,
        choices=[
            ('BASSE', 'Basse'),
            ('NORMALE', 'Normale'),
            ('HAUTE', 'Haute'),
            ('CRITIQUE', 'Critique'),
        ],
        default='NORMALE',
        verbose_name="Priorité"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de Création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de Modification"
    )
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='projets_crees',
        verbose_name="Créé par"
    )

    class Meta:
        db_table = 'zdpj'
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.code_projet} - {self.nom_projet}"

    def clean(self):
        """Validation et conversion en majuscules"""
        super().clean()
        # Ne pas modifier le code_projet s'il existe déjà
        # Il est généré automatiquement

        # Garder les validations de dates
        if self.date_fin_prevue and self.date_debut and self.date_fin_prevue < self.date_debut:
            raise ValidationError({
                'date_fin_prevue': 'La date de fin prévue doit être postérieure à la date de début.'
            })

        if self.date_fin_reelle and self.date_debut and self.date_fin_reelle < self.date_debut:
            raise ValidationError({
                'date_fin_reelle': 'La date de fin réelle doit être postérieure à la date de début.'
            })

    def save(self, *args, **kwargs):
        """Override save pour générer le code projet automatiquement"""
        # Si c'est un nouveau projet (pas encore de code)
        if not self.code_projet:
            # Générer le prochain code
            self.code_projet = self.generer_nouveau_code()

        self.full_clean()
        super().save(*args, **kwargs)

    def generer_nouveau_code(self):
        """Génère un nouveau code projet formaté PRJ-XXX"""
        # Chercher le dernier projet par ordre de création
        dernier_projet = ZDPJ.objects.all().order_by('-date_creation').first()

        if not dernier_projet:
            # Premier projet
            nouveau_numero = 1
        else:
            try:
                dernier_code = dernier_projet.code_projet

                # Essayer d'extraire les chiffres du code
                import re
                chiffres = re.findall(r'\d+', dernier_code)

                if chiffres:
                    # Prendre le dernier groupe de chiffres trouvé
                    dernier_numero = int(chiffres[-1])
                else:
                    dernier_numero = 0

            except (ValueError, IndexError, AttributeError):
                # En cas d'erreur, commencer à 1
                dernier_numero = 0

            nouveau_numero = dernier_numero + 1

        # Formater: PRJ-001, PRJ-002, etc.
        return f"PRJ-{nouveau_numero:03d}"

    def generer_nouveau_code_simple(self):
        """Génère un code simple PRJ-XXX (fallback)"""
        dernier_projet = ZDPJ.objects.all().order_by('-date_creation').first()

        if not dernier_projet:
            nouveau_numero = 1
        else:
            try:
                dernier_code = dernier_projet.code_projet
                if '-' in dernier_code:
                    dernier_numero = int(dernier_code.split('-')[1])
                else:
                    dernier_numero = 0
            except (ValueError, IndexError, AttributeError):
                dernier_numero = 0

            nouveau_numero = dernier_numero + 1

        return f"PRJ-{nouveau_numero:03d}"

    def get_avancement_pourcentage(self):
        """Calcule le pourcentage d'avancement basé sur les tâches"""
        taches = self.taches.all()
        if not taches.exists():
            return 0

        taches_terminees = taches.filter(statut='TERMINE').count()
        return round((taches_terminees / taches.count()) * 100, 2)

    def get_heures_consommees(self):
        """Retourne le total des heures consommées sur le projet"""
        from django.db.models import Sum
        total = self.taches.aggregate(
            total_heures=Sum('imputations__duree')
        )['total_heures']
        return total or 0


class ZDTA(models.Model):
    """Modèle Tâches - Gestion des tâches de projet"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_tache = models.CharField(
        max_length=50,  # Augmenter la longueur pour le format PRJ-XXX-TASK-YYY
        unique=True,
        verbose_name="Code Tâche",
        editable=False  # Rendre non éditable manuellement
    )
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )

    # Relations
    projet = models.ForeignKey(
        ZDPJ,
        on_delete=models.CASCADE,
        related_name='taches',
        verbose_name="Projet"
    )
    assignee = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches_assignees',
        verbose_name="Assigné à"
    )
    tache_parente = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sous_taches',
        verbose_name="Tâche Parente"
    )

    # Estimations et suivi
    estimation_heures = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Estimation (heures)"
    )
    date_debut_prevue = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de Début Prévue"
    )
    date_fin_prevue = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de Fin Prévue"
    )
    date_debut_reelle = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de Début Réelle"
    )
    date_fin_reelle = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de Fin Réelle"
    )

    # Statut et priorité
    statut = models.CharField(
        max_length=50,
        choices=[
            ('A_FAIRE', 'À Faire'),
            ('EN_COURS', 'En Cours'),
            ('EN_ATTENTE', 'En Attente'),
            ('TERMINE', 'Terminé'),
            ('ANNULE', 'Annulé'),
        ],
        default='A_FAIRE',
        verbose_name="Statut"
    )
    priorite = models.CharField(
        max_length=20,
        choices=[
            ('BASSE', 'Basse'),
            ('NORMALE', 'Normale'),
            ('HAUTE', 'Haute'),
            ('CRITIQUE', 'Critique'),
        ],
        default='NORMALE',
        verbose_name="Priorité"
    )
    avancement = models.IntegerField(
        default=0,
        verbose_name="Avancement (%)",
        help_text="Pourcentage d'avancement (0-100)"
    )

    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de Création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de Modification"
    )
    cree_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='taches_creees',
        verbose_name="Créé par"
    )

    class Meta:
        db_table = 'zdta'
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
        ordering = ['-priorite', 'date_fin_prevue']

    def __str__(self):
        return f"{self.code_tache} - {self.titre}"

    def save(self, *args, **kwargs):
        """Override save pour générer le code tâche automatiquement"""
        # Si c'est une nouvelle tâche (pas encore de code)
        if not self.code_tache and self.projet:
            # Générer le prochain code
            self.code_tache = self.generer_nouveau_code()

        self.full_clean()
        super().save(*args, **kwargs)

    def generer_nouveau_code(self):
        """Génère un nouveau code tâche formaté TASK-XXX"""
        # Chercher la dernière tâche par ordre de création
        dernier_tache = ZDTA.objects.all().order_by('-date_creation').first()

        if not dernier_tache:
            # Première tâche
            nouveau_numero = 1
        else:
            try:
                dernier_code = dernier_tache.code_tache

                # Essayer d'extraire les chiffres du code
                import re
                chiffres = re.findall(r'\d+', dernier_code)

                if chiffres:
                    # Prendre le dernier groupe de chiffres trouvé
                    dernier_numero = int(chiffres[-1])
                else:
                    dernier_numero = 0

            except (ValueError, IndexError, AttributeError):
                # En cas d'erreur, commencer à 1
                dernier_numero = 0

            nouveau_numero = dernier_numero + 1

        # Formater: TASK-0001, TASK-0002, etc.
        return f"TASK-{nouveau_numero:04d}"

    def generer_nouveau_code_simple(self):
        """Génère un code simple TASK-XXX (fallback)"""
        dernier_tache = ZDTA.objects.all().order_by('-date_creation').first()

        if not dernier_tache:
            nouveau_numero = 1
        else:
            try:
                dernier_code = dernier_tache.code_tache
                if '-TASK-' in dernier_code:
                    dernier_numero = int(dernier_code.split('-TASK-')[1])
                elif '-' in dernier_code:
                    dernier_numero = int(dernier_code.split('-')[-1])
                else:
                    dernier_numero = 0
            except (ValueError, IndexError, AttributeError):
                dernier_numero = 0

            nouveau_numero = dernier_numero + 1

        return f"TASK-{nouveau_numero:03d}"

    def clean(self):
        """Validation"""
        super().clean()
        # Ne pas modifier le code_tache s'il existe déjà
        # Il est généré automatiquement

        # Garder les autres validations
        if self.avancement < 0 or self.avancement > 100:
            raise ValidationError({
                'avancement': 'L\'avancement doit être entre 0 et 100.'
            })

        if self.date_fin_prevue and self.date_debut_prevue and self.date_fin_prevue < self.date_debut_prevue:
            raise ValidationError({
                'date_fin_prevue': 'La date de fin prévue doit être postérieure à la date de début prévue.'
            })

        if self.date_fin_reelle and self.date_debut_reelle and self.date_fin_reelle < self.date_debut_reelle:
            raise ValidationError({
                'date_fin_reelle': 'La date de fin réelle doit être postérieure à la date de début réelle.'
            })

    def get_heures_realisees(self):
        """Retourne le total des heures réalisées sur la tâche"""
        from django.db.models import Sum
        total = self.imputations.aggregate(
            total_heures=Sum('duree')
        )['total_heures']
        return total or 0

    def get_ecart_estimation(self):
        """Retourne l'écart entre estimation et réalisé"""
        if not self.estimation_heures:
            return None

        heures_realisees = self.get_heures_realisees()

        # S'assurer que les deux valeurs sont numériques
        try:
            # Convertir estimation_heures (Decimal) en float
            estimation = float(self.estimation_heures)

            # heures_realisees devrait déjà être un float (de la méthode get_heures_realisees)
            # mais on s'assure
            if isinstance(heures_realisees, (int, float, Decimal)):
                realise = float(heures_realisees)
            else:
                realise = 0.0

            return realise - estimation
        except (TypeError, ValueError, AttributeError):
            return None


class ZDDO(models.Model):
    """Modèle Documents - Gestion des documents liés aux projets et tâches"""

    TYPE_RATTACHEMENT_CHOICES = [
        ('PROJET', 'Projet'),
        ('TACHE', 'Tâche'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom_document = models.CharField(
        max_length=200,
        verbose_name="Nom du Document"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    fichier = models.FileField(
        upload_to='documents/gestion_temps/%Y/%m/',
        verbose_name="Fichier"
    )

    # Rattachement flexible (soit projet, soit tâche)
    type_rattachement = models.CharField(
        max_length=10,
        choices=TYPE_RATTACHEMENT_CHOICES,
        verbose_name="Type de Rattachement"
    )
    projet = models.ForeignKey(
        ZDPJ,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        verbose_name="Projet"
    )
    tache = models.ForeignKey(
        ZDTA,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        verbose_name="Tâche"
    )

    # Métadonnées du fichier
    type_fichier = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Type de Fichier",
        help_text="Extension du fichier (pdf, docx, xlsx, etc.)"
    )
    taille_fichier = models.BigIntegerField(
        blank=True,
        null=True,
        verbose_name="Taille (octets)"
    )

    # Catégorisation
    categorie = models.CharField(
        max_length=50,
        choices=[
            ('CONTRAT', 'Contrat'),
            ('CAHIER_CHARGES', 'Cahier des Charges'),
            ('SPECIFICATION', 'Spécification Technique'),
            ('RAPPORT', 'Rapport'),
            ('FACTURE', 'Facture'),
            ('LIVRABLE', 'Livrable'),
            ('AUTRE', 'Autre'),
        ],
        default='AUTRE',
        verbose_name="Catégorie"
    )

    # Versioning
    version = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Version"
    )
    document_precedent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions_suivantes',
        verbose_name="Version Précédente"
    )

    # Métadonnées
    date_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'Upload"
    )
    uploade_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_uploades',
        verbose_name="Uploadé par"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    class Meta:
        db_table = 'zddo'
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-date_upload']

    def __str__(self):
        rattachement = self.projet if self.type_rattachement == 'PROJET' else self.tache
        return f"{self.nom_document} - {rattachement}"

    def clean(self):
        """Validation du rattachement"""
        super().clean()

        # Validation: un document doit être rattaché à un projet OU une tâche
        if self.type_rattachement == 'PROJET' and not self.projet:
            raise ValidationError({
                'projet': 'Vous devez sélectionner un projet.'
            })

        if self.type_rattachement == 'TACHE' and not self.tache:
            raise ValidationError({
                'tache': 'Vous devez sélectionner une tâche.'
            })

    def save(self, *args, **kwargs):
        """Override save pour extraire les métadonnées du fichier et forcer validation"""
        if self.fichier:
            # Extraire l'extension
            import os
            self.type_fichier = os.path.splitext(self.fichier.name)[1][1:].lower()

            # Extraire la taille
            if hasattr(self.fichier, 'size'):
                self.taille_fichier = self.fichier.size

        # Validation: un seul rattachement à la fois
        if self.type_rattachement == 'PROJET' and self.tache:
            self.tache = None
        elif self.type_rattachement == 'TACHE' and self.projet:
            self.projet = None

        self.full_clean()
        super().save(*args, **kwargs)

    def get_taille_formatee(self):
        """Retourne la taille du fichier formatée"""
        if not self.taille_fichier:
            return "N/A"

        taille = self.taille_fichier
        for unite in ['octets', 'Ko', 'Mo', 'Go']:
            if taille < 1024.0:
                return f"{taille:.1f} {unite}"
            taille /= 1024.0
        return f"{taille:.1f} To"

    def get_objet_rattache(self):
        """Retourne l'objet auquel le document est rattaché"""
        return self.projet if self.type_rattachement == 'PROJET' else self.tache


class ZDIT(models.Model):
    """Modèle Imputations Temps - Saisie du temps passé sur les tâches"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    employe = models.ForeignKey(
        ZY00,
        on_delete=models.PROTECT,
        related_name='imputations_temps',
        verbose_name="Employé"
    )
    tache = models.ForeignKey(
        ZDTA,
        on_delete=models.CASCADE,
        related_name='imputations',
        verbose_name="Tâche"
    )
    activite = models.ForeignKey(
        ZDAC,
        on_delete=models.PROTECT,
        related_name='imputations',
        verbose_name="Type d'Activité"
    )

    # Temps
    date = models.DateField(
        verbose_name="Date"
    )
    duree = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Durée (heures)",
        help_text="Durée en heures (ex: 1.5 pour 1h30)"
    )

    # Timer (optionnel pour mode temps réel)
    timer_debut = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Début Timer"
    )
    timer_fin = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fin Timer"
    )

    # Détails
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire"
    )

    # Validation
    valide = models.BooleanField(
        default=False,
        verbose_name="Validé"
    )
    valide_par = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imputations_validees',
        verbose_name="Validé par"
    )
    date_validation = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de Validation"
    )

    # Facturation
    facturable = models.BooleanField(
        default=True,
        verbose_name="Facturable"
    )
    facture = models.BooleanField(
        default=False,
        verbose_name="Facturé"
    )
    taux_horaire_applique = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux Horaire Appliqué (FCFA)"
    )

    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de Création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de Modification"
    )

    class Meta:
        db_table = 'zdit'
        verbose_name = "Imputation Temps"
        verbose_name_plural = "Imputations Temps"
        ordering = ['-date', '-date_creation']
        unique_together = [['employe', 'tache', 'date', 'activite']]

    def __str__(self):
        return f"{self.employe} - {self.tache} - {self.date} ({self.duree}h)"

    def clean(self):
        """Validation des données"""
        super().clean()

        # Validation: durée doit être positive
        if self.duree and self.duree <= 0:
            raise ValidationError({
                'duree': 'La durée doit être supérieure à 0.'
            })

        # Validation: durée maximum 24h par jour
        if self.duree and self.duree > 24:
            raise ValidationError({
                'duree': 'La durée ne peut pas dépasser 24 heures par jour.'
            })

        # Validation: timer_fin après timer_debut
        if self.timer_debut and self.timer_fin and self.timer_fin <= self.timer_debut:
            raise ValidationError({
                'timer_fin': 'L\'heure de fin doit être postérieure à l\'heure de début.'
            })

    def save(self, *args, **kwargs):
        """Override save pour appliquer le taux horaire par défaut et forcer validation"""
        if not self.taux_horaire_applique and self.activite.taux_horaire_defaut:
            self.taux_horaire_applique = self.activite.taux_horaire_defaut

        self.full_clean()
        super().save(*args, **kwargs)

    def get_montant_facturable(self):
        """Calcule le montant facturable"""
        if not self.facturable or not self.taux_horaire_applique:
            return 0
        return float(self.duree) * float(self.taux_horaire_applique)


class ZDCMQuerySet(models.QuerySet):
    def visible_pour_employe(self, employe):
        """
        Retourne les commentaires visibles pour un employé donné
        Utilise les relations pour optimiser les performances
        """
        from django.db.models import Q

        # Conditions de visibilité
        conditions = Q(prive=False)

        if employe:
            # 1. Commentaires non privés
            conditions |= Q(prive=False)

            # 2. Commentaires de l'employé
            conditions |= Q(employe=employe)

            # 3. Tâche assignée à l'employé
            conditions |= Q(tache__assignee=employe)

            # 4. Employé est chef de projet
            conditions |= Q(tache__projet__chef_projet=employe)

            # 5. Employé est dans le même département que la personne assignée
            # Cette partie est plus complexe et peut nécessiter une sous-requête
            if hasattr(employe, 'affectations'):
                affectation_employe = employe.affectations.filter(
                    date_fin__isnull=True
                ).first()

                if affectation_employe and affectation_employe.poste.DEPARTEMENT:
                    departement_employe = affectation_employe.poste.DEPARTEMENT

                    # Sous-requête pour les employés du même département
                    conditions |= Q(
                        tache__assignee__affectations__poste__DEPARTEMENT=departement_employe,
                        tache__assignee__affectations__date_fin__isnull=True
                    )

            # 6. Employé est manager du département de la personne assignée
            conditions |= Q(
                tache__assignee__in=ZY00.objects.filter(
                    manager_responsable=employe
                )
            )

            # 7. Rôles RH et administrateurs
            if employe.has_role('DRH') or employe.has_role('GESTION_APP'):
                conditions |= Q()  # Voir tous les commentaires

        return self.filter(conditions).distinct()

class ZDCM(models.Model):
    """Modèle Commentaires - Gestion des commentaires sur les tâches"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    tache = models.ForeignKey(
        ZDTA,
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name="Tâche"
    )
    employe = models.ForeignKey(
        ZY00,
        on_delete=models.SET_NULL,
        null=True,
        related_name='commentaires',
        verbose_name="Auteur"
    )

    # Contenu
    contenu = models.TextField(
        verbose_name="Contenu du commentaire"
    )

    # Réponse à un autre commentaire (pour les threads)
    reponse_a = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reponses',
        verbose_name="Réponse à"
    )

    # Édition
    edite = models.BooleanField(
        default=False,
        verbose_name="Modifié"
    )
    date_edition = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'édition"
    )

    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )

    # Confidentialité
    prive = models.BooleanField(
        default=False,
        verbose_name="Commentaire privé",
        help_text="Seul l'auteur et les managers peuvent voir ce commentaire"
    )

    # Mentions
    mentions = models.ManyToManyField(
        ZY00,
        related_name='mentions_dans_commentaires',
        blank=True,
        verbose_name="Mentionner",
        help_text="Personnes mentionnées dans le commentaire"
    )

    class Meta:
        db_table = 'zdcm'
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Commentaire de {self.employe} sur {self.tache}"

    def save(self, *args, **kwargs):
        """Override save pour extraire les mentions"""
        if self.contenu:
            # Extraction des mentions (@nom)
            self.extract_mentions()
        super().save(*args, **kwargs)

    def extract_mentions(self):
        """Extrait les mentions du contenu"""
        import re
        # Recherche des motifs @nom @prenom
        pattern = r'@([A-Za-zÀ-ÖØ-öø-ÿ\s]+)'
        mentions_trouvees = re.findall(pattern, self.contenu)

        if mentions_trouvees and self.employe:
            # Chercher les employés correspondants
            for mention in mentions_trouvees:
                employes = ZY00.objects.filter(
                    Q(nom__icontains=mention) | Q(prenoms__icontains=mention),
                    etat='actif'
                ).exclude(pk=self.employe.pk)

                for employe in employes:
                    self.mentions.add(employe)

    def get_auteur_display(self):
        """Retourne le nom de l'auteur formaté"""
        if self.employe:
            return f"{self.employe.nom} {self.employe.prenoms}"
        return "Utilisateur inconnu"

    def get_temps_ecoule(self):
        """Retourne le temps écoulé depuis la création"""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - self.date_creation

        if diff.days > 365:
            return f"il y a {diff.days // 365} an(s)"
        elif diff.days > 30:
            return f"il y a {diff.days // 30} mois"
        elif diff.days > 0:
            return f"il y a {diff.days} jour(s)"
        elif diff.seconds > 3600:
            return f"il y a {diff.seconds // 3600} heure(s)"
        elif diff.seconds > 60:
            return f"il y a {diff.seconds // 60} minute(s)"
        else:
            return "à l'instant"

    def peut_voir(self, employe):
        """
        Vérifie si un employé peut voir ce commentaire
        VERSION 1 : Visibilité stricte par équipe/département
        """
        if not employe:
            print(f"[DEBUG peut_voir] Employé None → False")
            return False

        print(f"\n[DEBUG peut_voir] Vérification pour {employe.nom} {employe.prenoms}")
        print(f"[DEBUG peut_voir] Commentaire de: {self.employe.nom}")
        print(f"[DEBUG peut_voir] Tâche assignée à: {self.tache.assignee}")

        # 1. L'auteur peut toujours voir son commentaire
        if self.employe == employe:
            print(f"[DEBUG peut_voir] ✅ Auteur du commentaire → True")
            return True

        # 2. L'assigné de la tâche peut toujours voir
        if self.tache.assignee == employe:
            print(f"[DEBUG peut_voir] ✅ Assigné de la tâche → True")
            return True

        # 3. Le chef de projet peut toujours voir
        if self.tache.projet.chef_projet == employe:
            print(f"[DEBUG peut_voir] ✅ Chef de projet → True")
            return True

        # 4. RH et administrateurs peuvent tout voir
        has_drh = employe.has_role('DRH')
        has_admin = employe.has_role('GESTION_APP')
        print(f"[DEBUG peut_voir] Rôles - DRH: {has_drh}, Admin: {has_admin}")

        if has_drh or has_admin:
            print(f"[DEBUG peut_voir] ✅ RH/Admin → True")
            return True

        # Si la tâche n'a pas d'assigné, seuls les rôles ci-dessus peuvent voir
        if not self.tache.assignee:
            print(f"[DEBUG peut_voir] ❌ Tâche sans assigné → False")
            return False

        # 5. Vérifier si l'employé est dans la même équipe
        meme_equipe = self._est_dans_meme_equipe(employe, self.tache.assignee)
        print(f"[DEBUG peut_voir] Même équipe: {meme_equipe}")

        if meme_equipe:
            print(f"[DEBUG peut_voir] ✅ Même équipe → True")
            return True

        # 6. Vérifier si l'employé est le manager du département
        est_manager = self._est_manager_de_assignee(employe, self.tache.assignee)
        print(f"[DEBUG peut_voir] Est manager: {est_manager}")

        if est_manager:
            print(f"[DEBUG peut_voir] ✅ Manager du département → True")
            return True

        # Si on arrive ici, l'employé n'a pas accès
        print(f"[DEBUG peut_voir] ❌ Aucune condition remplie → False")
        return False

    def _est_dans_meme_equipe(self, employe1, employe2):
        """Vérifie si deux employés sont dans la même équipe (même département)"""
        try:
            dept1 = employe1.get_departement_actuel()
            dept2 = employe2.get_departement_actuel()

            print(f"[DEBUG _est_dans_meme_equipe] Dept {employe1.nom}: {dept1}")
            print(f"[DEBUG _est_dans_meme_equipe] Dept {employe2.nom}: {dept2}")

            if not dept1 or not dept2:
                print(f"[DEBUG _est_dans_meme_equipe] ❌ Un des départements est None")
                return False

            resultat = dept1.id == dept2.id
            print(f"[DEBUG _est_dans_meme_equipe] Résultat: {resultat} (ID1={dept1.id}, ID2={dept2.id})")
            return resultat

        except Exception as e:
            print(f"[DEBUG _est_dans_meme_equipe] ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _est_manager_de_assignee(self, employe, assignee):
        """Vérifie si l'employé est le manager du département de l'assigné"""
        try:
            from departement.models import ZYMA

            affectation_assignee = assignee.affectations.filter(
                date_fin__isnull=True
            ).select_related('poste__DEPARTEMENT').first()

            print(f"[DEBUG _est_manager_de_assignee] Affectation assigné: {affectation_assignee}")

            if not affectation_assignee or not affectation_assignee.poste.DEPARTEMENT:
                print(f"[DEBUG _est_manager_de_assignee] ❌ Pas d'affectation ou département")
                return False

            dept_assignee = affectation_assignee.poste.DEPARTEMENT
            print(f"[DEBUG _est_manager_de_assignee] Département assigné: {dept_assignee}")

            resultat = ZYMA.objects.filter(
                employe=employe,
                departement=dept_assignee,
                actif=True,
                date_fin__isnull=True
            ).exists()

            print(f"[DEBUG _est_manager_de_assignee] Est manager: {resultat}")
            return resultat

        except Exception as e:
            print(f"[DEBUG _est_manager_de_assignee] ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False

    def peut_modifier(self, employe):
        """
        Vérifie si un employé peut modifier ce commentaire

        Règles :
        - L'auteur peut modifier pendant 15 minutes
        - Les managers et administrateurs peuvent toujours modifier
        - Le chef de projet peut modifier
        """
        if not employe:
            return False

        # L'auteur peut modifier pendant 15 minutes
        if self.employe == employe:
            from django.utils import timezone
            diff = timezone.now() - self.date_creation
            if diff.total_seconds() <= 900:  # 15 minutes = 900 secondes
                return True

        # Le chef de projet peut modifier
        if self.tache.projet.chef_projet == employe:
            return True

        # Les managers et administrateurs
        if (employe.has_role('DRH') or
                employe.has_role('GESTION_APP') or
                self._est_manager_de_assignee(employe, self.tache.assignee)):
            return True

        return False

    def peut_supprimer(self, employe):
        """
        Vérifie si un employé peut supprimer ce commentaire

        Règles :
        - L'auteur peut supprimer pendant 30 minutes (augmenté)
        - Les managers et administrateurs peuvent toujours supprimer
        - Le chef de projet peut supprimer
        """
        if not employe:
            return False

        # L'auteur peut supprimer pendant 30 minutes
        if self.employe == employe:
            from django.utils import timezone
            diff = timezone.now() - self.date_creation
            if diff.total_seconds() <= 1800:  # 30 minutes = 1800 secondes
                return True

        # Le chef de projet peut supprimer
        if self.tache.projet.chef_projet == employe:
            return True

        # Les managers et administrateurs
        if (employe.has_role('DRH') or
                employe.has_role('GESTION_APP') or
                self._est_manager_de_assignee(employe, self.tache.assignee)):
            return True

        return False

    objects = ZDCMQuerySet.as_manager()