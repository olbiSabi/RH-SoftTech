# gestionnaire/forms.py

from django import forms
from django.core.validators import RegexValidator
from .models import Entreprise
from absence.models import ConfigurationConventionnelle


class EntrepriseForm(forms.ModelForm):
    """
    Formulaire pour la gestion des entreprises
    """

    class Meta:
        model = Entreprise
        fields = [
            'code', 'nom', 'raison_sociale', 'sigle',
            'adresse', 'ville', 'pays', 'telephone', 'email', 'site_web',
            'rccm', 'numero_impot', 'numero_cnss',
            'configuration_conventionnelle', 'date_creation', 'date_application_convention',
            'actif', 'logo', 'description'
        ]

        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex: ONIAN',
                'maxlength': 10
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: ONIAN SARL'
            }),
            'raison_sociale': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: ONIAN Société à Responsabilité Limitée'
            }),
            'sigle': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex: ONIAN',
                'maxlength': 20
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Adresse complète'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Lomé'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex: TOGO'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+228 XX XX XX XX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@entreprise.tg'
            }),
            'site_web': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.entreprise.tg'
            }),
            'rccm': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: TG-LOM-XXX'
            }),
            'numero_impot': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro d\'identification fiscale'
            }),
            'numero_cnss': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro CNSS'
            }),
            'configuration_conventionnelle': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_creation': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_application_convention': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de l\'entreprise'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer uniquement les conventions actives et en vigueur
        self.fields['configuration_conventionnelle'].queryset = \
            ConfigurationConventionnelle.objects.filter(actif=True)

        # Personnaliser les labels
        self.fields['configuration_conventionnelle'].label = "Convention collective"
        self.fields['configuration_conventionnelle'].help_text = \
            "Sélectionner la convention collective applicable"

        # Rendre certains champs non requis
        self.fields['raison_sociale'].required = False
        self.fields['sigle'].required = False
        self.fields['telephone'].required = False
        self.fields['email'].required = False
        self.fields['site_web'].required = False
        self.fields['rccm'].required = False
        self.fields['numero_impot'].required = False
        self.fields['numero_cnss'].required = False
        self.fields['configuration_conventionnelle'].required = False
        self.fields['date_creation'].required = False
        self.fields['date_application_convention'].required = False
        self.fields['logo'].required = False
        self.fields['description'].required = False

    def clean_code(self):
        """Validation du code"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()

            # Vérifier la longueur
            if len(code) < 2:
                raise forms.ValidationError("Le code doit contenir au moins 2 caractères")

            # Vérifier qu'il est alphanumérique
            if not code.replace('-', '').replace('_', '').isalnum():
                raise forms.ValidationError("Le code ne doit contenir que des lettres, chiffres, tirets ou underscores")

            # Vérifier l'unicité (sauf pour l'instance actuelle)
            queryset = Entreprise.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(f"Le code '{code}' est déjà utilisé")

            return code
        return code

    def clean_nom(self):
        """Validation du nom"""
        nom = self.cleaned_data.get('nom')
        if nom:
            nom = nom.strip()
            if len(nom) < 2:
                raise forms.ValidationError("Le nom doit contenir au moins 2 caractères")
            return nom
        return nom

    def clean_telephone(self):
        """Validation du téléphone"""
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Nettoyer les espaces
            telephone = telephone.strip()

            # Validation format togolais
            phone_validator = RegexValidator(
                regex=r'^(\+228|00228)?\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}$',
                message="Format téléphone invalide. Ex: +228 XX XX XX XX"
            )
            phone_validator(telephone)

            return telephone
        return telephone

    def clean_email(self):
        """Validation de l'email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            return email
        return email

    def clean_pays(self):
        """Validation du pays"""
        pays = self.cleaned_data.get('pays')
        if pays:
            return pays.upper().strip()
        return pays

    def clean(self):
        """Validation globale"""
        cleaned_data = super().clean()

        # Si une convention est sélectionnée, vérifier qu'elle est en vigueur
        convention = cleaned_data.get('configuration_conventionnelle')
        if convention and not convention.est_en_vigueur:
            self.add_error(
                'configuration_conventionnelle',
                f"La convention '{convention.code}' n'est pas en vigueur. "
                f"Veuillez sélectionner une convention active."
            )

        # Si date_application_convention est renseignée, vérifier cohérence
        date_application = cleaned_data.get('date_application_convention')
        date_creation = cleaned_data.get('date_creation')

        if date_application and date_creation:
            if date_application < date_creation:
                self.add_error(
                    'date_application_convention',
                    "La date d'application de la convention ne peut pas être antérieure "
                    "à la date de création de l'entreprise"
                )

        return cleaned_data