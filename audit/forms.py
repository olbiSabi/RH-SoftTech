# audit/forms.py
"""
Formulaires pour le module Conformité & Audit.
"""
from django import forms
from django.utils import timezone
from .models import AURC, AUAL, AURA


class AURCForm(forms.ModelForm):
    """Formulaire pour les règles de conformité.
    Le CODE est généré automatiquement lors de la création.
    """

    class Meta:
        model = AURC
        fields = [
            'LIBELLE', 'DESCRIPTION', 'TYPE_REGLE', 'SEVERITE',
            'FREQUENCE_VERIFICATION', 'JOURS_AVANT_EXPIRATION',
            'NOTIFIER_EMPLOYE', 'NOTIFIER_MANAGER', 'NOTIFIER_RH',
            'EMAILS_SUPPLEMENTAIRES', 'STATUT'
        ]
        widgets = {
            'LIBELLE': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Contrat expirant sous 30 jours'}),
            'DESCRIPTION': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'TYPE_REGLE': forms.Select(attrs={'class': 'form-control'}),
            'SEVERITE': forms.Select(attrs={'class': 'form-control'}),
            'FREQUENCE_VERIFICATION': forms.Select(attrs={'class': 'form-control'}),
            'JOURS_AVANT_EXPIRATION': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'EMAILS_SUPPLEMENTAIRES': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Un email par ligne'}),
            'STATUT': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResoudreAlerteForm(forms.Form):
    """Formulaire pour résoudre une alerte."""

    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire de résolution...'
        }),
        label='Commentaire'
    )


class AssignerAlerteForm(forms.Form):
    """Formulaire pour assigner une alerte."""

    employe_id = forms.CharField(
        widget=forms.HiddenInput(),
        label='Employé'
    )


class FiltresLogsForm(forms.Form):
    """Formulaire de filtres pour les logs."""

    TYPE_CHOICES = [
        ('', 'Tous les types'),
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
    ]

    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...'
        })
    )
    table_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de la table'
        })
    )
    type_mouvement = forms.ChoiceField(
        required=False,
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class FiltresAlertesForm(forms.Form):
    """Formulaire de filtres pour les alertes."""

    STATUT_CHOICES = [('', 'Tous les statuts')] + list(AUAL.STATUT_CHOICES)
    PRIORITE_CHOICES = [('', 'Toutes les priorités')] + list(AUAL.PRIORITE_CHOICES)
    TYPE_CHOICES = [('', 'Tous les types')] + list(AURC.TYPE_CHOICES)

    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...'
        })
    )
    type_alerte = forms.ChoiceField(
        required=False,
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    statut = forms.ChoiceField(
        required=False,
        choices=STATUT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priorite = forms.ChoiceField(
        required=False,
        choices=PRIORITE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class GenererRapportForm(forms.Form):
    """Formulaire pour générer un rapport d'audit."""

    TYPE_CHOICES = AURA.TYPE_CHOICES
    FORMAT_CHOICES = AURA.FORMAT_CHOICES

    type_rapport = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Type de rapport'
    )
    format_export = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Format'
    )
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date de début'
    )
    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date de fin'
    )

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_debut > date_fin:
            raise forms.ValidationError("La date de début doit être antérieure à la date de fin.")

        return cleaned_data
