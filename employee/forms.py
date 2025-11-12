from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZDPO, ZYDO
from .pays_choices import PAYS_CHOICES

class ZY00Form(forms.ModelForm):
    """Formulaire pour l'employé"""

    class Meta:
        model = ZY00
        fields = [
            'nom', 'prenoms', 'date_naissance', 'sexe',
            'ville_naissance', 'pays_naissance', 'situation_familiale',
            'type_id', 'numero_id', 'date_validite_id', 'date_expiration_id'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom(s)'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'ville_naissance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville de naissance'}),
            'pays_naissance': forms.Select(choices=PAYS_CHOICES, attrs={'class': 'form-control'}),
            'situation_familiale': forms.Select(attrs={'class': 'form-control'}),
            'type_id': forms.Select(attrs={'class': 'form-control'}),
            'numero_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro d\'identité'}),
            'date_validite_id': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_expiration_id': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class EmbaucheAgentForm(forms.ModelForm):
    """Formulaire complet pour l'embauche d'un agent (pré-embauche)"""

    # Champs pour le contrat
    type_contrat = forms.ChoiceField(
        choices=ZYCO.TYPE_CONTRAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Type de contrat"
    )
    date_debut_contrat = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date de début de contrat"
    )
    date_fin_contrat = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date de fin de contrat"
    )

    # Champs pour le téléphone
    numero_telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
        label="Numéro de téléphone"
    )

    # Champs pour l'email
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        label="Email"
    )

    # Champs pour l'affectation
    poste = forms.ModelChoiceField(
        queryset=ZDPO.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Poste"
    )

    # Champs pour l'adresse
    rue = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rue'}),
        label="Rue"
    )
    ville = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
        label="Ville"
    )

    pays = forms.ChoiceField(
        choices=PAYS_CHOICES,  # ← ChoiceField supporte 'choices'
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Pays"
    )
    code_postal = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code postal'}),
        label="Code postal"
    )
    date_debut_adresse = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date de début d'occupation"
    )

    class Meta:
        model = ZY00
        fields = [
            'nom', 'prenoms', 'date_naissance', 'sexe',
            'ville_naissance', 'pays_naissance', 'situation_familiale',
            'type_id', 'numero_id', 'date_validite_id', 'date_expiration_id'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom(s)'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'ville_naissance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville de naissance'}),
            'pays_naissance': forms.Select(choices=PAYS_CHOICES, attrs={'class': 'form-control'}),
            'situation_familiale': forms.Select(attrs={'class': 'form-control'}),
            'type_id': forms.Select(attrs={'class': 'form-control'}),
            'numero_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro d\'identité'}),
            'date_validite_id': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_expiration_id': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ZYCOForm(forms.ModelForm):
    """Formulaire pour les contrats"""

    class Meta:
        model = ZYCO
        fields = ['employe', 'type_contrat', 'date_debut', 'date_fin']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'type_contrat': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ZYTEForm(forms.ModelForm):
    """Formulaire pour les téléphones"""

    class Meta:
        model = ZYTE
        fields = ['employe', 'numero', 'date_debut_validite', 'date_fin_validite']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
            'date_debut_validite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_validite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ZYMEForm(forms.ModelForm):
    """Formulaire pour les emails"""

    class Meta:
        model = ZYME
        fields = ['employe', 'email', 'date_debut_validite', 'date_fin_validite']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'date_debut_validite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_validite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ZYAFForm(forms.ModelForm):
    """Formulaire pour les affectations"""

    class Meta:
        model = ZYAF
        fields = ['employe', 'poste', 'date_debut', 'date_fin']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'poste': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ZYADForm(forms.ModelForm):
    """Formulaire pour les adresses"""

    class Meta:
        model = ZYAD
        fields = ['employe', 'rue', 'ville', 'pays', 'code_postal', 'type_adresse', 'date_debut', 'date_fin']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'rue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rue'}),
            'ville': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
            'pays': forms.Select(choices=PAYS_CHOICES, attrs={'class': 'form-control'}),
            'code_postal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code postal'}),
            'type_adresse': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# Formsets pour gérer plusieurs instances en même temps
ContratFormSet = inlineformset_factory(
    ZY00, ZYCO,
    form=ZYCOForm,
    extra=1,
    can_delete=True
)

TelephoneFormSet = inlineformset_factory(
    ZY00, ZYTE,
    form=ZYTEForm,
    extra=1,
    can_delete=True
)

EmailFormSet = inlineformset_factory(
    ZY00, ZYME,
    form=ZYMEForm,
    extra=1,
    can_delete=True
)

AffectationFormSet = inlineformset_factory(
    ZY00, ZYAF,
    form=ZYAFForm,
    extra=1,
    can_delete=True
)

AdresseFormSet = inlineformset_factory(
    ZY00, ZYAD,
    form=ZYADForm,
    extra=1,
    can_delete=True
)


# Champs pour les documents
class ZYDOForm(forms.ModelForm):
    """Formulaire pour joindre des documents"""

    class Meta:
        model = ZYDO
        fields = ['type_document', 'description', 'fichier']
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description (optionnelle)',
                'rows': 3
            }),
            'fichier': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
        }

    def clean_fichier(self):
        """Validation du fichier"""
        fichier = self.cleaned_data.get('fichier')

        if fichier:
            # Vérifier la taille (max 10 Mo)
            if fichier.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Le fichier ne doit pas dépasser 10 Mo.")

            # Vérifier l'extension
            import os
            ext = os.path.splitext(fichier.name)[1].lower()
            extensions_autorisees = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']

            if ext not in extensions_autorisees:
                raise forms.ValidationError(
                    f"Extension non autorisée. Extensions autorisées : {', '.join(extensions_autorisees)}"
                )

        return fichier