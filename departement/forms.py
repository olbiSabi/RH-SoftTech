from django import forms
from .models import ZDDE
from datetime import date

DATE_MAX = date(2999, 12, 31)


class ZDDEForm(forms.ModelForm):
    """Formulaire pour le modèle ZDDE"""

    class Meta:
        model = ZDDE
        fields = ['CODE', 'LIBELLE', 'STATUT', 'DATEDEB', 'DATEFIN']
        widgets = {
            'CODE': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'code',
                'maxlength': '3',
                'placeholder': 'Ex: RH',
                'style': 'text-transform: uppercase;'
            }),
            'LIBELLE': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'libelle',
                'placeholder': 'Ex: Ressources Humaines'
            }),
            'STATUT': forms.Select(
                choices=[(True, 'Actif'), (False, 'Inactif')],
                attrs={
                    'class': 'form-control',
                    'id': 'statut'
                }
            ),
            'DATEDEB': forms.DateInput(attrs={
                'class': 'form-control',
                'id': 'dateDebut',
                'type': 'date'
            }),
            'DATEFIN': forms.DateInput(attrs={
                'class': 'form-control date-input',
                'id': 'dateFin',
                'placeholder': '__/__/____',
                'pattern': '\d{2}/\d{2}/\d{4}',
                'title': 'Format: JJ/MM/AAAA'
            }),
        }
        labels = {
            'CODE': 'Code Département *',
            'LIBELLE': 'Libellé *',
            'STATUT': 'Statut *',
            'DATEDEB': 'Date de début *',
            'DATEFIN': 'Date de fin',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre DATEFIN optionnel
        self.fields['DATEFIN'].required = False

        # Si on édite un département existant avec DATEFIN = DATE_MAX, on vide le champ
        if self.instance and self.instance.pk:
            if self.instance.DATEFIN == DATE_MAX:
                self.initial['DATEFIN'] = None

    def clean_CODE(self):
        """Validation du code"""
        code = self.cleaned_data.get('CODE', '').upper().strip()

        if len(code) != 3:
            raise forms.ValidationError('Le code doit contenir exactement 3 caractères.')

        if not code.isalpha():
            raise forms.ValidationError('Le code ne doit contenir que des lettres.')

        # Vérifier l'unicité (sauf pour l'instance actuelle en édition)
        qs = ZDDE.objects.filter(CODE=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('Ce code département existe déjà.')

        return code

    def clean_DATEFIN(self):
        """Si DATEFIN est vide, utiliser DATE_MAX"""
        date_fin = self.cleaned_data.get('DATEFIN')
        if not date_fin:
            return DATE_MAX
        return date_fin

    def clean(self):
        """Validation croisée des dates"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('DATEDEB')
        date_fin = cleaned_data.get('DATEFIN')

        if date_debut and date_fin:
            if date_fin != DATE_MAX and date_fin <= date_debut:
                raise forms.ValidationError({
                    'DATEFIN': 'La date de fin doit être postérieure à la date de début.'
                })

        return cleaned_data