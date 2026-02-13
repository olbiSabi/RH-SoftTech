"""Formulaires pour le module Planning."""
from django import forms
from .models import Planning, SiteTravail, PosteTravail, Affectation, Evenement


class SiteTravailForm(forms.ModelForm):
    class Meta:
        model = SiteTravail
        fields = ['nom', 'adresse', 'telephone', 'heure_ouverture', 'heure_fermeture', 'fuseau_horaire', 'is_active']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nom du site'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Adresse complete'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex: +228 90 00 00 00'
            }),
            'heure_ouverture': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'heure_fermeture': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'fuseau_horaire': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class PosteTravailForm(forms.ModelForm):
    class Meta:
        model = PosteTravail
        fields = ['nom', 'description', 'type_poste', 'site', 'heure_debut', 'heure_fin',
                  'pause_dejeune', 'taux_horaire', 'is_active']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nom du poste'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
            'type_poste': forms.Select(attrs={'class': 'form-control'}),
            'site': forms.Select(attrs={'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'pause_dejeune': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '00:30:00'
            }),
            'taux_horaire': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['site'].queryset = SiteTravail.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        debut = cleaned_data.get('heure_debut')
        fin = cleaned_data.get('heure_fin')
        if debut and fin and fin <= debut:
            raise forms.ValidationError("L'heure de fin doit etre apres l'heure de debut.")
        return cleaned_data


class PlanningForm(forms.ModelForm):
    class Meta:
        model = Planning
        fields = ['titre', 'description', 'date_debut', 'date_fin', 'statut', 'departement']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Titre du planning'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'departement': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user_role = kwargs.pop('user_role', None)
        super().__init__(*args, **kwargs)
        if user_role != 'admin':
            # Manager : departement auto-set cote vue, pas de choix
            self.fields.pop('departement', None)
        else:
            # Admin : peut choisir le departement ou laisser vide (global)
            from departement.models import ZDDE
            self.fields['departement'].queryset = ZDDE.objects.filter(STATUT=True)
            self.fields['departement'].required = False

    def clean(self):
        cleaned_data = super().clean()
        debut = cleaned_data.get('date_debut')
        fin = cleaned_data.get('date_fin')
        if debut and fin and fin < debut:
            raise forms.ValidationError("La date de fin doit etre apres la date de debut.")
        return cleaned_data


class AffectationForm(forms.ModelForm):
    class Meta:
        model = Affectation
        fields = ['planning', 'employe', 'poste', 'date', 'heure_debut', 'heure_fin', 'statut', 'notes']
        widgets = {
            'planning': forms.Select(attrs={'class': 'form-control'}),
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'poste': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        visible_employees = kwargs.pop('visible_employees', None)
        super().__init__(*args, **kwargs)
        self.fields['poste'].queryset = PosteTravail.objects.filter(
            is_active=True
        ).select_related('site')
        self.fields['planning'].queryset = Planning.objects.filter(
            statut__in=['BROUILLON', 'PUBLIE']
        )
        if visible_employees is not None:
            self.fields['employe'].queryset = visible_employees

    def clean(self):
        cleaned_data = super().clean()
        debut = cleaned_data.get('heure_debut')
        fin = cleaned_data.get('heure_fin')
        if debut and fin and fin <= debut:
            raise forms.ValidationError("L'heure de fin doit etre apres l'heure de debut.")
        return cleaned_data


class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = ['titre', 'description', 'date_debut', 'date_fin', 'type_evenement', 'employes', 'lieu']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Titre'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'date_debut': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
            'date_fin': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
            'type_evenement': forms.Select(attrs={'class': 'form-control'}),
            'employes': forms.SelectMultiple(attrs={
                'class': 'form-control', 'size': 6
            }),
            'lieu': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Lieu'
            }),
        }

    def __init__(self, *args, **kwargs):
        visible_employees = kwargs.pop('visible_employees', None)
        super().__init__(*args, **kwargs)
        if visible_employees is not None:
            self.fields['employes'].queryset = visible_employees

    def clean(self):
        cleaned_data = super().clean()
        debut = cleaned_data.get('date_debut')
        fin = cleaned_data.get('date_fin')
        if debut and fin and fin <= debut:
            raise forms.ValidationError("La date de fin doit etre apres la date de debut.")
        return cleaned_data
