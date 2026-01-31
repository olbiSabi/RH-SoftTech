from django import forms
from django.db.models import Q
from django.utils import timezone
from ..models import JRImputation, JRTicket
from employee.models import ZY00


class ImputationForm(forms.ModelForm):
    """Formulaire pour la saisie des imputations de temps"""

    class Meta:
        model = JRImputation
        fields = [
            'ticket', 'date_imputation', 'heures', 'minutes',
            'description', 'type_activite'
        ]
        widgets = {
            'ticket': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_imputation': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'heures': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '24',
                'step': '1',
                'placeholder': '8'
            }),
            'minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '59',
                'placeholder': '30'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du travail effectué...'
            }),
            'type_activite': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendre heures et minutes optionnels dans le formulaire
        self.fields['heures'].required = False
        self.fields['minutes'].required = False

        # Obtenir l'instance ZY00 correspondant à l'utilisateur
        try:
            self.employe = ZY00.objects.get(user=user)
        except ZY00.DoesNotExist:
            self.employe = None

        # Afficher tous les tickets ouverts (non terminés)
        self.fields['ticket'].queryset = JRTicket.objects.filter(
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVUE']
        ).select_related('projet').order_by('projet__code', 'code')
        
        # Date par défaut : aujourd'hui
        if not self.instance.date_imputation:
            self.fields['date_imputation'].initial = timezone.now().date()
    
    def clean_date_imputation(self):
        """Validation de la date d'imputation"""
        date_imputation = self.cleaned_data.get('date_imputation')
        if date_imputation and date_imputation > timezone.now().date():
            raise forms.ValidationError(
                "La date d'imputation ne peut pas être dans le futur."
            )
        return date_imputation
    
    def clean_heures(self):
        """Validation des heures"""
        heures = self.cleaned_data.get('heures')
        if heures is not None and heures < 0:
            raise forms.ValidationError("Le nombre d'heures ne peut pas être négatif.")
        if heures and heures > 24:
            raise forms.ValidationError("Le nombre d'heures ne peut pas dépasser 24.")
        return heures
    
    def clean_minutes(self):
        """Validation des minutes"""
        minutes = self.cleaned_data.get('minutes')
        if minutes is not None and minutes < 0:
            raise forms.ValidationError("Le nombre de minutes ne peut pas être négatif.")
        if minutes and minutes > 59:
            raise forms.ValidationError("Le nombre de minutes ne peut pas dépasser 59.")
        return minutes
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        heures = cleaned_data.get('heures')
        minutes = cleaned_data.get('minutes')
        
        # Vérifier qu'au moins des heures ou des minutes sont saisies
        if (heures is None or heures == 0) and (minutes is None or minutes == 0):
            raise forms.ValidationError(
                "Veuillez saisir au moins des heures ou des minutes."
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Surcharge de la méthode save pour définir l'employé"""
        instance = super().save(commit=False)
        instance.employe = self.employe
        instance.statut_validation = 'EN_ATTENTE'

        # S'assurer que heures et minutes ont des valeurs par défaut
        if instance.heures is None:
            instance.heures = 0
        if instance.minutes is None:
            instance.minutes = 0

        if commit:
            instance.save()

        return instance


class ImputationSearchForm(forms.Form):
    """Formulaire de recherche pour les imputations"""
    
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par ticket, description...'
        })
    )
    
    employe = forms.ModelChoiceField(
        queryset=ZY00.objects.all(),
        required=False,
        empty_label="Tous les employés",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    projet = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Code ou nom du projet'
        })
    )
    
    statut_validation = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + JRImputation.STATUT_VALIDATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    type_activite = forms.ChoiceField(
        choices=[('', 'Tous les types')] + JRImputation.TYPE_ACTIVITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    mentions = forms.ModelMultipleChoiceField(
        queryset=ZY00.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'id': 'commentaire_mentions'
        })
    )
    
    date_min = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_max = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class ValidationImputationForm(forms.Form):
    """Formulaire pour la validation/rejet des imputations"""
    
    commentaire_validation = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire de validation (optionnel)...'
        })
    )
    
    action = forms.ChoiceField(
        choices=[
            ('valider', 'Valider'),
            ('rejeter', 'Rejeter')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
