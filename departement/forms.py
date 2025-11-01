from django import forms
from .models import ZDDE, ZDPO
from datetime import datetime


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
                'placeholder': 'Ex: RHS',
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
                'type': 'date',
                'placeholder': 'JJ/MM/AAAA'
            }),
            'DATEFIN': forms.DateInput(attrs={
                'class': 'form-control',
                'id': 'dateFin',
                'type': 'date',
                'placeholder': 'JJ/MM/AAAA'
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
        self.fields['DATEDEB'].required = True

        # Ne pas pré-remplir les dates - laisser vides
        if not self.instance or not self.instance.pk:
            # Pour un nouveau département, laisser les champs vides
            self.initial['DATEDEB'] = None
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
        """Si DATEFIN est vide, retourner None au lieu de DATE_MAX"""
        date_fin = self.cleaned_data.get('DATEFIN')
        # Retourner None si vide, sinon la date
        return date_fin if date_fin else None

    def clean(self):
        """Validation croisée des dates"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('DATEDEB')
        date_fin = cleaned_data.get('DATEFIN')

        # Valider seulement si date_fin est renseignée
        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise forms.ValidationError({
                    'DATEFIN': 'La date de fin doit être postérieure à la date de début.'
                })

        return cleaned_data


# ==========================================
# FORMULAIRE POSTE (ZDPO)
# ==========================================

class ZDPOForm(forms.ModelForm):
    """Formulaire pour le modèle ZDPO"""

    class Meta:
        model = ZDPO
        fields = ['CODE', 'LIBELLE', 'DEPARTEMENT', 'STATUT', 'DATEDEB', 'DATEFIN']
        widgets = {
            'CODE': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'code',
                'maxlength': '6',
                'placeholder': 'Ex: PST001',
                'style': 'text-transform: uppercase;'
            }),
            'LIBELLE': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'libelle',
                'placeholder': 'Ex: Développeur Full Stack'
            }),
            'DEPARTEMENT': forms.Select(attrs={
                'class': 'form-control',
                'id': 'departement'
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
                'type': 'date',
                'placeholder': 'JJ/MM/AAAA'
            }),
            'DATEFIN': forms.DateInput(attrs={
                'class': 'form-control',
                'id': 'dateFin',
                'type': 'date',
                'placeholder': 'JJ/MM/AAAA'
            }),
        }
        labels = {
            'CODE': 'Code Poste *',
            'LIBELLE': 'Libellé *',
            'DEPARTEMENT': 'Département *',
            'STATUT': 'Statut *',
            'DATEDEB': 'Date de début *',
            'DATEFIN': 'Date de fin',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['DATEFIN'].required = False
        self.fields['DATEDEB'].required = True

        # Afficher le libellé du département au lieu du code
        self.fields['DEPARTEMENT'].label_from_instance = lambda obj: f"{obj.LIBELLE} ({obj.CODE})"

        # Filtrer uniquement les départements actifs
        self.fields['DEPARTEMENT'].queryset = ZDDE.objects.filter(STATUT=True).order_by('LIBELLE')

        if not self.instance or not self.instance.pk:
            self.initial['DATEDEB'] = None
            self.initial['DATEFIN'] = None

    def clean_CODE(self):
        """Validation du code"""
        code = self.cleaned_data.get('CODE', '').upper().strip()

        if len(code) != 6:
            raise forms.ValidationError('Le code doit contenir exactement 6 caractères.')

        if not code.isalnum():
            raise forms.ValidationError('Le code ne doit contenir que des lettres et des chiffres.')

        qs = ZDPO.objects.filter(CODE=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('Ce code poste existe déjà.')

        return code

    def clean_DATEFIN(self):
        """Si DATEFIN est vide, retourner None"""
        date_fin = self.cleaned_data.get('DATEFIN')
        return date_fin if date_fin else None

    def clean(self):
        """Validation croisée des dates"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('DATEDEB')
        date_fin = cleaned_data.get('DATEFIN')

        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise forms.ValidationError({
                    'DATEFIN': 'La date de fin doit être postérieure à la date de début.'
                })

        return cleaned_data