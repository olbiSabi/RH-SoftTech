from django import forms
from django.utils import timezone
from ..models import JRProject, JRClient
from employee.models import ZY00


class ProjetForm(forms.ModelForm):
    """Formulaire pour la création et modification des projets"""
    
    class Meta:
        model = JRProject
        fields = [
            'nom', 'description', 'client', 'chef_projet', 'montant_total',
            'date_debut', 'date_fin_prevue', 'statut'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du projet'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du projet...'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'chef_projet': forms.Select(attrs={
                'class': 'form-control'
            }),
            'montant_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_prevue': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les clients actifs
        self.fields['client'].queryset = JRClient.objects.filter(statut='ACTIF')
        
        # Filtrer les employés actifs
        self.fields['chef_projet'].queryset = ZY00.objects.filter(
            etat='actif'
        ).order_by('nom', 'prenoms')
    
    def clean_date_fin_prevue(self):
        """Validation que la date de fin est après la date de début"""
        date_debut = self.cleaned_data.get('date_debut')
        date_fin_prevue = self.cleaned_data.get('date_fin_prevue')
        
        if date_debut and date_fin_prevue:
            if date_fin_prevue <= date_debut:
                raise forms.ValidationError(
                    "La date de fin prévue doit être postérieure à la date de début."
                )
        
        return date_fin_prevue
    
    def clean_montant_total(self):
        """Validation du montant total"""
        montant = self.cleaned_data.get('montant_total')
        if montant and montant < 0:
            raise forms.ValidationError("Le montant total ne peut pas être négatif.")
        return montant


class ProjetSearchForm(forms.Form):
    """Formulaire de recherche pour les projets"""

    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, code...'
        })
    )

    client = forms.ModelChoiceField(
        queryset=JRClient.objects.none(),
        required=False,
        empty_label="Tous les clients",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    chef_projet = forms.ModelChoiceField(
        queryset=ZY00.objects.none(),
        required=False,
        empty_label="Tous les chefs de projet",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + JRProject.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    date_debut_min = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_debut_max = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger tous les clients (actifs et inactifs pour la recherche)
        self.fields['client'].queryset = JRClient.objects.all().order_by('raison_sociale')
        # Charger tous les chefs de projet (employés actifs)
        self.fields['chef_projet'].queryset = ZY00.objects.filter(
            etat='actif'
        ).order_by('nom', 'prenoms')
