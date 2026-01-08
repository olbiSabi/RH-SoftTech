# gestion_temps_activite/forms.py - VERSION COMPLÈTE AVEC VALIDATION D'UNICITÉ

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from employee.models import ZY00
from .models import ZDCL, ZDAC, ZDPJ, ZDTA, ZDDO, ZDIT, ZDCM


class ZDCLForm(forms.ModelForm):
    """Formulaire pour la gestion des clients"""

    class Meta:
        model = ZDCL
        fields = [
            'raison_sociale',
            'type_client',
            'secteur_activite',
            'personne_contact',
            'fonction_contact',
            'telephone',
            'email',
            'adresse_ligne1',
            'adresse_ligne2',
            'ville',
            'code_postal',
            'pays',
            'notes',
            'actif'
        ]

        widgets = {
            'raison_sociale': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'entreprise',
                'autofocus': True
            }),
            'type_client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'secteur_activite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Technologies, Finance, etc.'
            }),
            'personne_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du contact principal'
            }),
            'fonction_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Directeur, Responsable, etc.'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+228 XX XX XX XX',
                'type': 'tel'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@entreprise.com'
            }),
            'adresse_ligne1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro et nom de rue'
            }),
            'adresse_ligne2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Complément d\'adresse (optionnel)'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Lomé, Kara, etc.'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes additionnelles sur le client'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

        labels = {
            'raison_sociale': 'Raison Sociale *',
            'type_client': 'Type de Client',
            'secteur_activite': 'Secteur d\'Activité',
            'personne_contact': 'Personne de Contact',
            'fonction_contact': 'Fonction',
            'telephone': 'Téléphone',
            'email': 'Email',
            'adresse_ligne1': 'Adresse Ligne 1',
            'adresse_ligne2': 'Adresse Ligne 2',
            'ville': 'Ville',
            'code_postal': 'Code Postal',
            'pays': 'Pays',
            'notes': 'Notes',
            'actif': 'Client Actif'
        }


class ZDACForm(forms.ModelForm):
    """Formulaire pour la gestion des types d'activités"""

    class Meta:
        model = ZDAC
        fields = [
            'code_activite',
            'libelle',
            'description',
            'facturable',
            'taux_horaire_defaut',
            'date_debut',
            'date_fin',
            'actif'
        ]

        widgets = {
            'code_activite': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex: DEV, REUNION, etc.',
                'maxlength': '10'
            }),
            'libelle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Développement, Réunion, Support'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée de l\'activité'
            }),
            'facturable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'taux_horaire_defaut': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

        labels = {
            'code_activite': 'Code Activité *',
            'libelle': 'Libellé *',
            'description': 'Description',
            'facturable': 'Activité Facturable',
            'taux_horaire_defaut': 'Taux Horaire par Défaut (FCFA)',
            'date_debut': 'Date de Début *',
            'date_fin': 'Date de Fin',
            'actif': 'Actif'
        }

    def clean_code_activite(self):
        """Convertir le code activité en majuscules et vérifier l'unicité"""
        code = self.cleaned_data.get('code_activite')
        if code:
            code = code.upper().strip()

            # Vérifier l'unicité
            existing = ZDAC.objects.filter(code_activite=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(
                    f'Le code activité "{code}" existe déjà. Veuillez choisir un autre code.'
                )

            return code
        return code

    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_fin < date_debut:
            raise ValidationError({
                'date_fin': 'La date de fin doit être postérieure à la date de début.'
            })

        return cleaned_data


class ZDPJForm(forms.ModelForm):
    """Formulaire pour la gestion des projets"""

    class Meta:
        model = ZDPJ
        fields = [
            'nom_projet',
            'description',
            'client',
            'chef_projet',
            'budget_heures',
            'budget_montant',
            'date_debut',
            'date_fin_prevue',
            'date_fin_reelle',
            'statut',
            'priorite',
            'type_facturation',
            'actif'
        ]

        # Rendre le champ code_projet invisible dans le formulaire
        exclude = ['code_projet', 'cree_par', 'date_creation', 'date_modification']

        widgets = {
            'nom_projet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du projet',
                'autofocus': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du projet'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'chef_projet': forms.Select(attrs={
                'class': 'form-control'
            }),
            'budget_heures': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'budget_montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_prevue': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_reelle': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-control'
            }),
            'type_facturation': forms.Select(attrs={
                'class': 'form-control'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

        labels = {
            'nom_projet': 'Nom du Projet *',
            'description': 'Description',
            'client': 'Client *',
            'chef_projet': 'Chef de Projet',
            'budget_heures': 'Budget (heures)',
            'budget_montant': 'Budget (FCFA)',
            'date_debut': 'Date de Début *',
            'date_fin_prevue': 'Date de Fin Prévue *',
            'date_fin_reelle': 'Date de Fin Réelle',
            'statut': 'Statut',
            'priorite': 'Priorité',
            'type_facturation': 'Type de Facturation',
            'actif': 'Projet Actif'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les clients actifs uniquement
        self.fields['client'].queryset = ZDCL.objects.filter(actif=True)
        # Filtrer les employés actifs pour chef de projet
        self.fields['chef_projet'].queryset = ZY00.objects.filter(etat='actif').order_by('nom', 'prenoms')


    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin_prevue = cleaned_data.get('date_fin_prevue')
        date_fin_reelle = cleaned_data.get('date_fin_reelle')

        if date_debut and date_fin_prevue and date_fin_prevue < date_debut:
            raise ValidationError({
                'date_fin_prevue': 'La date de fin prévue doit être postérieure à la date de début.'
            })

        if date_debut and date_fin_reelle and date_fin_reelle < date_debut:
            raise ValidationError({
                'date_fin_reelle': 'La date de fin réelle doit être postérieure à la date de début.'
            })

        return cleaned_data


class ZDTAForm(forms.ModelForm):
    """Formulaire pour les tâches"""

    class Meta:
        model = ZDTA
        fields = [
            'titre', 'description',
            'projet', 'tache_parente', 'assignee',
            'estimation_heures', 'avancement',
            'date_debut_prevue', 'date_fin_prevue',
            'date_debut_reelle', 'date_fin_reelle',
            'statut', 'priorite'
        ]

        exclude = ['code_tache', 'cree_par', 'date_creation', 'date_modification']

        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de la tâche',
                'autofocus': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée de la tâche'
            }),
            'projet': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tache_parente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assignee': forms.Select(attrs={
                'class': 'form-control'
            }),
            'estimation_heures': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'avancement': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'value': '0'
            }),
            'date_debut_prevue': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_prevue': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_debut_reelle': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_reelle': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['assignee'].queryset = ZY00.objects.filter(etat='actif').order_by('nom', 'prenoms')

        # Filtrer les projets actifs
        self.fields['projet'].queryset = ZDPJ.objects.filter(actif=True).order_by('nom_projet')

        # Labels en français
        self.fields['titre'].label = 'Titre'
        self.fields['description'].label = 'Description'
        self.fields['projet'].label = 'Projet'
        self.fields['tache_parente'].label = 'Tâche Parente'
        self.fields['assignee'].label = 'Assigné à'
        self.fields['estimation_heures'].label = 'Estimation (heures)'
        self.fields['avancement'].label = 'Avancement (%)'
        self.fields['date_debut_prevue'].label = 'Date de Début Prévue'
        self.fields['date_fin_prevue'].label = 'Date de Fin Prévue'
        self.fields['date_debut_reelle'].label = 'Date de Début Réelle'
        self.fields['date_fin_reelle'].label = 'Date de Fin Réelle'
        self.fields['statut'].label = 'Statut'
        self.fields['priorite'].label = 'Priorité'

        # Champs optionnels
        self.fields['description'].required = False
        self.fields['tache_parente'].required = False
        self.fields['assignee'].required = False
        self.fields['estimation_heures'].required = False
        self.fields['date_debut_prevue'].required = False
        self.fields['date_fin_prevue'].required = False
        self.fields['date_debut_reelle'].required = False
        self.fields['date_fin_reelle'].required = False

        #  Vérifier si l'instance existe et a un projet
        if self.instance and self.instance.pk and self.instance.projet_id:
            self.fields['tache_parente'].queryset = ZDTA.objects.filter(
                projet=self.instance.projet
            ).exclude(pk=self.instance.pk).order_by('titre')
        else:
            # Si nouvelle tâche, la liste des tâches parentes est vide par défaut
            # Elle sera mise à jour par JavaScript selon le projet sélectionné
            self.fields['tache_parente'].queryset = ZDTA.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        date_debut_prevue = cleaned_data.get('date_debut_prevue')
        date_fin_prevue = cleaned_data.get('date_fin_prevue')
        date_debut_reelle = cleaned_data.get('date_debut_reelle')
        date_fin_reelle = cleaned_data.get('date_fin_reelle')
        avancement = cleaned_data.get('avancement')
        tache_parente = cleaned_data.get('tache_parente')

        # Validation des dates prévues
        if date_debut_prevue and date_fin_prevue:
            if date_fin_prevue < date_debut_prevue:
                raise forms.ValidationError(
                    "La date de fin prévue doit être postérieure à la date de début prévue."
                )

        # Validation des dates réelles
        if date_debut_reelle and date_fin_reelle:
            if date_fin_reelle < date_debut_reelle:
                raise forms.ValidationError(
                    "La date de fin réelle doit être postérieure à la date de début réelle."
                )

        # Validation avancement
        if avancement is not None:
            if avancement < 0 or avancement > 100:
                raise forms.ValidationError(
                    "L'avancement doit être entre 0 et 100%."
                )

        # Validation tâche parente (pas de boucle)
        if tache_parente and self.instance.pk:
            if tache_parente.pk == self.instance.pk:
                raise forms.ValidationError(
                    "Une tâche ne peut pas être sa propre parente."
                )

        return cleaned_data


class ZDDOForm(forms.ModelForm):
    """Formulaire pour la gestion des documents"""

    class Meta:
        model = ZDDO
        fields = [
            'nom_document',
            'description',
            'fichier',
            'type_rattachement',
            'projet',
            'tache',
            'categorie',
            'version',
            'actif'
        ]

        widgets = {
            'nom_document': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du document'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du document'
            }),
            'fichier': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.png,.jpg,.jpeg'
            }),
            'type_rattachement': forms.Select(attrs={
                'class': 'form-select form-control',
                'onchange': 'toggleRattachement()'
            }),
            'projet': forms.Select(attrs={
                'class': 'form-select form-control'
            }),
            'tache': forms.Select(attrs={
                'class': 'form-select form-control'
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-select form-control'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 1.0, v2.3, etc.'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

        labels = {
            'nom_document': 'Nom du Document *',
            'description': 'Description',
            'fichier': 'Fichier *',
            'type_rattachement': 'Rattacher à *',
            'projet': 'Projet',
            'tache': 'Tâche',
            'categorie': 'Catégorie',
            'version': 'Version',
            'actif': 'Actif'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les projets et tâches actifs
        self.fields['projet'].queryset = ZDPJ.objects.filter(actif=True)
        self.fields['tache'].queryset = ZDTA.objects.select_related('projet').all()

        # Rendre les champs conditionnellement requis
        self.fields['projet'].required = False
        self.fields['tache'].required = False

    def clean(self):
        """Validation du rattachement"""
        cleaned_data = super().clean()
        type_rattachement = cleaned_data.get('type_rattachement')
        projet = cleaned_data.get('projet')
        tache = cleaned_data.get('tache')

        if type_rattachement == 'PROJET' and not projet:
            raise ValidationError({
                'projet': 'Vous devez sélectionner un projet.'
            })

        if type_rattachement == 'TACHE' and not tache:
            raise ValidationError({
                'tache': 'Vous devez sélectionner une tâche.'
            })

        return cleaned_data


class ZDITForm(forms.ModelForm):
    """Formulaire pour la saisie des imputations temps"""

    class Meta:
        model = ZDIT
        fields = [
            'employe',
            'tache',
            'activite',
            'date',
            'duree',
            'commentaire',
            'facturable'
        ]

        widgets = {
            'employe': forms.Select(attrs={
                'class': 'form-select form-control'
            }),
            'tache': forms.Select(attrs={
                'class': 'form-select form-control',
                'onchange': 'updateProjetInfo()'
            }),
            'activite': forms.Select(attrs={
                'class': 'form-select form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'duree': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.25',
                'min': '0.25',
                'max': '24'
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Détails de l\'activité réalisée'
            }),
            'facturable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

        labels = {
            'employe': 'Employé *',
            'tache': 'Tâche *',
            'activite': 'Type d\'Activité *',
            'date': 'Date *',
            'duree': 'Durée (heures) *',
            'commentaire': 'Commentaire',
            'facturable': 'Facturable'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si un utilisateur est passé, le sélectionner par défaut
        if user and hasattr(user, 'employe'):
            self.fields['employe'].initial = user.employe
            # Masquer le champ employé pour les utilisateurs normaux
            self.fields['employe'].widget = forms.HiddenInput()

        # Filtrer les employés actifs
        self.fields['employe'].queryset = ZY00.objects.filter(etat='actif')

        # Filtrer les tâches des projets actifs et non terminés
        self.fields['tache'].queryset = ZDTA.objects.filter(
            projet__actif=True
        ).exclude(statut='TERMINE').select_related('projet')

        # Filtrer les activités en vigueur
        date_actuelle = timezone.now().date()
        self.fields['activite'].queryset = ZDAC.objects.filter(
            actif=True,
            date_debut__lte=date_actuelle
        ).filter(
            models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=date_actuelle)
        )

        # Date par défaut = aujourd'hui
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()

    def clean_duree(self):
        """Valider la durée"""
        duree = self.cleaned_data.get('duree')
        if duree:
            if duree <= 0:
                raise ValidationError('La durée doit être supérieure à 0.')
            if duree > 24:
                raise ValidationError('La durée ne peut pas dépasser 24 heures.')
        return duree

    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()
        employe = cleaned_data.get('employe')
        tache = cleaned_data.get('tache')
        date = cleaned_data.get('date')
        activite = cleaned_data.get('activite')

        # Vérifier que l'activité est en vigueur à la date saisie
        if activite and date:
            if not activite.est_en_vigueur(date):
                raise ValidationError({
                    'activite': f'L\'activité "{activite.libelle}" n\'est pas en vigueur à cette date.'
                })

        # Vérifier les doublons (même employé, tâche, date, activité)
        if employe and tache and date and activite:
            existing = ZDIT.objects.filter(
                employe=employe,
                tache=tache,
                date=date,
                activite=activite
            )

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(
                    'Une imputation existe déjà pour cet employé, cette tâche, '
                    'cette date et ce type d\'activité.'
                )

        # Vérifier que la date n'est pas dans le futur
        if date and date > timezone.now().date():
            raise ValidationError({
                'date': 'Vous ne pouvez pas saisir du temps pour une date future.'
            })

        return cleaned_data


class ZDITValidationForm(forms.ModelForm):
    """Formulaire pour la validation des imputations"""

    class Meta:
        model = ZDIT
        fields = ['valide', 'commentaire']

        widgets = {
            'valide': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Commentaire sur la validation (optionnel)'
            })
        }

        labels = {
            'valide': 'Valider cette imputation',
            'commentaire': 'Commentaire'
        }


class TimerForm(forms.Form):
    """Formulaire pour le mode timer en temps réel"""

    tache = forms.ModelChoiceField(
        queryset=ZDTA.objects.none(),
        label='Tâche *',
        widget=forms.Select(attrs={
            'class': 'form-select form-control'
        })
    )

    activite = forms.ModelChoiceField(
        queryset=ZDAC.objects.none(),
        label='Type d\'Activité *',
        widget=forms.Select(attrs={
            'class': 'form-select form-control'
        })
    )

    commentaire = forms.CharField(
        required=False,
        label='Commentaire',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Que faites-vous ?'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrer les tâches actives
        self.fields['tache'].queryset = ZDTA.objects.filter(
            projet__actif=True
        ).exclude(statut='TERMINE').select_related('projet')

        # Filtrer les activités en vigueur
        date_actuelle = timezone.now().date()
        from django.db.models import Q
        self.fields['activite'].queryset = ZDAC.objects.filter(
            actif=True,
            date_debut__lte=date_actuelle
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=date_actuelle)
        )


class RechercheImputationForm(forms.Form):
    """Formulaire de recherche/filtrage des imputations"""

    employe = forms.ModelChoiceField(
        queryset=ZY00.objects.filter(etat='actif'),
        required=False,
        label='Employé',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    projet = forms.ModelChoiceField(
        queryset=ZDPJ.objects.filter(actif=True),
        required=False,
        label='Projet',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    tache = forms.ModelChoiceField(
        queryset=ZDTA.objects.all(),
        required=False,
        label='Tâche',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    activite = forms.ModelChoiceField(
        queryset=ZDAC.objects.filter(actif=True),
        required=False,
        label='Type d\'Activité',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    date_debut = forms.DateField(
        required=False,
        label='Date de Début',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_fin = forms.DateField(
        required=False,
        label='Date de Fin',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    valide = forms.ChoiceField(
        required=False,
        label='Statut Validation',
        choices=[
            ('', 'Tous'),
            ('True', 'Validé'),
            ('False', 'Non validé')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    facture = forms.ChoiceField(
        required=False,
        label='Statut Facturation',
        choices=[
            ('', 'Tous'),
            ('True', 'Facturé'),
            ('False', 'Non facturé')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class ZDCMForm(forms.ModelForm):
    """Formulaire pour les commentaires"""

    class Meta:
        model = ZDCM
        fields = ['contenu', 'prive']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Écrivez votre commentaire... (utilisez @nom pour mentionner quelqu\'un)',
                'maxlength': '1000',
                'id': 'id_contenu',
            }),
            'prive': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'commentaire-prive'
            })
        }
        labels = {
            'contenu': '',
            'prive': 'Commentaire privé'
        }

    def __init__(self, *args, **kwargs):
        self.tache = kwargs.pop('tache', None)
        self.employe = kwargs.pop('employe', None)
        self.parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)

        if self.parent:
            self.fields['contenu'].label = 'Réponse'
            self.fields['contenu'].widget.attrs['placeholder'] = 'Écrivez votre réponse...'

    def clean_contenu(self):
        contenu = self.cleaned_data.get('contenu')
        if not contenu or not contenu.strip():
            raise ValidationError('Le commentaire ne peut pas être vide.')

        if len(contenu.strip()) < 2:
            raise ValidationError('Le commentaire est trop court.')

        if len(contenu) > 1000:
            raise ValidationError('Le commentaire ne peut pas dépasser 1000 caractères.')

        return contenu.strip()