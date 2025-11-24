"""
Formulaires Django pour la gestion des congés et absences
Application: absence
Système HR_ONIAN
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import ZDDA, ZDSO, ZDJF, ZDAB, calculer_jours_ouvres
from employee.models import ZY00


# ==========================================
# FORMULAIRE DE DEMANDE D'ABSENCE (Employé)
# ==========================================

class DemandeAbsenceForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une demande d'absence
    Utilisé par les employés
    """

    class Meta:
        model = ZDDA
        fields = [
            'type_absence',
            'date_debut',
            'date_fin',
            'duree',
            'periode',
            'nombre_jours',
            'motif',
            'justificatif',
        ]
        widgets = {
            'type_absence': forms.Select(attrs={
                'class': 'form-control',
                'id': 'typeDemande',
                'required': True
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'duree': forms.RadioSelect(attrs={
                'class': 'form-check-input',
            }),
            'periode': forms.Select(attrs={
                'class': 'form-control',
                'id': 'periode',
            }),
            'nombre_jours': forms.HiddenInput(),
            'motif': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'motif',
                'rows': 4,
                'placeholder': 'Décrivez brièvement le motif de votre demande (optionnel)...',
                'required': False
            }),
            'justificatif': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
        }
        labels = {
            'type_absence': 'Type de demande',
            'date_debut': 'Date de début',
            'date_fin': 'Date de fin',
            'duree': 'Durée',
            'periode': 'Période de la demi-journée',
            'nombre_jours': 'Nombre de jours',
            'motif': 'Motif / Commentaire (optionnel)',
            'justificatif': 'Justificatif (optionnel)',
        }

    def __init__(self, *args, **kwargs):
        self.employe = kwargs.pop('employe', None)
        super().__init__(*args, **kwargs)

        # Filtrer seulement les types d'absence actifs
        self.fields['type_absence'].queryset = ZDAB.objects.filter(STATUT=True).order_by('CODE')

        # Rendre la période optionnelle par défaut
        self.fields['periode'].required = False

        # Rendre le motif optionnel
        self.fields['motif'].required = False

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        duree = cleaned_data.get('duree')
        periode = cleaned_data.get('periode')
        type_absence = cleaned_data.get('type_absence')

        # ========================================
        # VALIDATION 1 : Dates obligatoires
        # ========================================
        if not date_debut or not date_fin:
            return cleaned_data

        # ========================================
        # VALIDATION 2 : Date de fin >= Date de début
        # ========================================
        # CORRECTION ICI : Utiliser < au lieu de <=
        if date_fin < date_debut:
            raise ValidationError({
                'date_fin': 'La date de fin doit être supérieure ou égale à la date de début.'
            })

        # ========================================
        # VALIDATION 3 : Pas de dates dans le passé
        # ========================================
        today = timezone.now().date()
        if date_debut < today:
            raise ValidationError({
                'date_debut': 'La date de début ne peut pas être dans le passé.'
            })

        if date_fin < today:
            raise ValidationError({
                'date_fin': 'La date de fin ne peut pas être dans le passé.'
            })

        # ========================================
        # VALIDATION 4 : Vérifier les chevauchements
        # ========================================
        if self.employe:
            # Récupérer toutes les demandes non annulées et non refusées de cet employé
            demandes_existantes = ZDDA.objects.filter(
                employe=self.employe,
                statut__in=['EN_ATTENTE', 'VALIDEE_MANAGER', 'VALIDEE_RH']
            )

            # Exclure la demande en cours de modification
            if self.instance and self.instance.pk:
                demandes_existantes = demandes_existantes.exclude(pk=self.instance.pk)

            # Vérifier les chevauchements
            for demande_exist in demandes_existantes:
                if (date_debut <= demande_exist.date_fin and date_fin >= demande_exist.date_debut):
                    raise ValidationError(
                        f'Chevauchement détecté avec une demande existante : '
                        f'{demande_exist.numero_demande} du {demande_exist.date_debut.strftime("%d/%m/%Y")} '
                        f'au {demande_exist.date_fin.strftime("%d/%m/%Y")} '
                        f'(Statut: {demande_exist.get_statut_display()}).'
                    )

        # ========================================
        # VALIDATION 5 : Durée et période
        # ========================================
        if duree == 'DEMI':
            if not periode:
                raise ValidationError({
                    'periode': 'La période doit être spécifiée pour une demi-journée.'
                })
            # Pour une demi-journée, date_debut doit être égale à date_fin
            if date_debut != date_fin:
                raise ValidationError({
                    'date_fin': 'Pour une demi-journée, la date de début et de fin doivent être identiques.'
                })
        else:
            # Si journée complète, période doit être vide
            cleaned_data['periode'] = None

        # ========================================
        # VALIDATION 6 : Calculer le nombre de jours
        # ========================================
        if duree == 'DEMI':
            cleaned_data['nombre_jours'] = Decimal('0.5')
        else:
            nb_jours = calculer_jours_ouvres(date_debut, date_fin)
            if nb_jours == 0:
                raise ValidationError({
                    'date_debut': 'La période sélectionnée ne contient aucun jour ouvré (week-ends et jours fériés exclus).'
                })
            cleaned_data['nombre_jours'] = nb_jours

        # ========================================
        # VALIDATION 7 : Vérifier le solde disponible
        # ========================================
        if self.employe and type_absence:
            if type_absence.CODE in ['CPN', 'RTT']:  # Types qui déduisent du solde
                annee = date_debut.year
                solde = ZDSO.get_or_create_solde(self.employe, annee)
                nb_jours = cleaned_data.get('nombre_jours', 0)

                # Si modification, ajouter les jours de l'ancienne demande au solde disponible
                jours_ancienne_demande = 0
                if self.instance and self.instance.pk:
                    # Vérifier que type_absence existe sur l'instance existante
                    try:
                        if self.instance.type_absence and self.instance.type_absence.CODE in ['CPN', 'RTT']:
                            jours_ancienne_demande = self.instance.nombre_jours or 0
                    except:
                        # Si type_absence n'existe pas sur l'ancienne instance, ignorer
                        pass

                solde_disponible = solde.jours_disponibles + jours_ancienne_demande

                if solde_disponible < nb_jours:
                    raise ValidationError(
                        f'Solde insuffisant. Vous avez {solde_disponible} jour(s) disponible(s) '
                        f'mais vous demandez {nb_jours} jour(s).'
                    )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # S'assurer que nombre_jours est défini (calculé dans clean())
        if not instance.nombre_jours and 'nombre_jours' in self.cleaned_data:
            instance.nombre_jours = self.cleaned_data['nombre_jours']

        if self.employe:
            instance.employe = self.employe
            instance.created_by = self.employe
            instance.updated_by = self.employe

            # Enregistrer le solde avant la demande
            # Vérifier que type_absence existe avant d'y accéder
            if instance.type_absence and instance.type_absence.CODE in ['CPN', 'RTT'] and instance.nombre_jours:
                annee = instance.date_debut.year
                solde = ZDSO.get_or_create_solde(self.employe, annee)
                instance.solde_avant = solde.jours_disponibles
                instance.solde_apres = solde.jours_disponibles - instance.nombre_jours

        if commit:
            instance.save()

        return instance


# ==========================================
# FORMULAIRE DE VALIDATION MANAGER
# ==========================================

class ValidationManagerForm(forms.Form):
    """
    Formulaire pour la validation ou le refus par le manager
    """
    action = forms.ChoiceField(
        choices=[
            ('valider', 'Valider'),
            ('refuser', 'Refuser'),
        ],
        widget=forms.HiddenInput(),
        required=True
    )

    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire (optionnel pour validation, obligatoire pour refus)...',
        }),
        required=False,
        label='Commentaire'
    )

    motif_refus = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'motifRefus',
            'rows': 4,
            'placeholder': 'Veuillez expliquer la raison du refus...',
        }),
        required=False,
        label='Motif du refus'
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        motif_refus = cleaned_data.get('motif_refus')

        # Si action = refuser, le motif_refus est obligatoire
        if action == 'refuser' and not motif_refus:
            raise ValidationError({
                'motif_refus': 'Le motif du refus est obligatoire.'
            })

        return cleaned_data


# ==========================================
# FORMULAIRE DE VALIDATION RH
# ==========================================

class ValidationRHForm(forms.Form):
    """
    Formulaire pour la validation finale ou le refus par RH
    """
    action = forms.ChoiceField(
        choices=[
            ('valider', 'Valider'),
            ('refuser', 'Refuser'),
        ],
        widget=forms.HiddenInput(),
        required=True
    )

    commentaire_rh = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'commentaireValidation',
            'rows': 3,
            'placeholder': 'Ajouter un commentaire ou des notes...',
        }),
        required=False,
        label='Commentaire RH'
    )

    motif_refus_rh = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'motifRefusRH',
            'rows': 4,
            'placeholder': 'Veuillez expliquer la raison du refus...',
        }),
        required=False,
        label='Motif du refus'
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        motif_refus_rh = cleaned_data.get('motif_refus_rh')

        # Si action = refuser, le motif_refus_rh est obligatoire
        if action == 'refuser' and not motif_refus_rh:
            raise ValidationError({
                'motif_refus_rh': 'Le motif du refus est obligatoire.'
            })

        return cleaned_data


# ==========================================
# FORMULAIRE D'ANNULATION
# ==========================================

class AnnulationDemandeForm(forms.Form):
    """
    Formulaire pour annuler une demande
    """
    motif_annulation = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Veuillez expliquer la raison de l\'annulation...',
            'required': True
        }),
        required=True,
        label='Motif de l\'annulation'
    )


# ==========================================
# FORMULAIRE DE RECHERCHE (RH)
# ==========================================

class RechercheDemandeForm(forms.Form):
    """
    Formulaire de recherche avancée pour RH
    """
    employe = forms.ModelChoiceField(
        queryset=ZY00.objects.filter(type_dossier='SAL', etat='actif').order_by('nom', 'prenoms'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Employé'
    )

    type_absence = forms.ModelChoiceField(
        queryset=ZDAB.objects.filter(STATUT=True).order_by('CODE'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Type d\'absence'
    )

    statut = forms.ChoiceField(
        choices=[('', 'Tous')] + ZDDA.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Statut'
    )

    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='Date de début'
    )

    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='Date de fin'
    )


# ==========================================
# FORMULAIRE DE GESTION DES JOURS FÉRIÉS
# ==========================================

class JourFerieForm(forms.ModelForm):
    """
    Formulaire pour gérer les jours fériés
    """

    class Meta:
        model = ZDJF
        fields = ['date', 'libelle', 'fixe', 'actif']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'libelle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Jour de l\'An',
                'required': True
            }),
            'fixe': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'date': 'Date',
            'libelle': 'Libellé',
            'fixe': 'Date fixe chaque année',
            'actif': 'Actif',
        }

    def clean_date(self):
        date_value = self.cleaned_data.get('date')

        # Vérifier si cette date n'existe pas déjà (sauf si modification)
        if date_value:
            existing = ZDJF.objects.filter(date=date_value)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError('Un jour férié existe déjà pour cette date.')

        return date_value


# ==========================================
# FORMULAIRE INITIAL DE SOLDE (RH)
# ==========================================

class SoldeCongesInitialForm(forms.ModelForm):
    """
    Formulaire pour initialiser ou modifier le solde de congés d'un employé
    Utilisé par RH
    """

    class Meta:
        model = ZDSO
        fields = [
            'employe',
            'annee',
            'jours_acquis',
            'jours_reportes',
            'rtt_acquis',
        ]
        widgets = {
            'employe': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'annee': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2050,
                'required': True
            }),
            'jours_acquis': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
                'required': True
            }),
            'jours_reportes': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
            }),
            'rtt_acquis': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
            }),
        }
        labels = {
            'employe': 'Employé',
            'annee': 'Année',
            'jours_acquis': 'Jours acquis (CP)',
            'jours_reportes': 'Jours reportés N-1',
            'rtt_acquis': 'RTT acquis',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer seulement les salariés actifs
        self.fields['employe'].queryset = ZY00.objects.filter(
            type_dossier='SAL',
            etat='actif'
        ).order_by('nom', 'prenoms')

        # Année par défaut = année en cours
        if not self.instance.pk:
            self.fields['annee'].initial = timezone.now().year

    def clean(self):
        cleaned_data = super().clean()
        employe = cleaned_data.get('employe')
        annee = cleaned_data.get('annee')

        # Vérifier qu'il n'existe pas déjà un solde pour cet employé/année
        if employe and annee:
            existing = ZDSO.objects.filter(employe=employe, annee=annee)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(
                    f'Un solde existe déjà pour {employe.nom} {employe.prenoms} pour l\'année {annee}.'
                )

        return cleaned_data