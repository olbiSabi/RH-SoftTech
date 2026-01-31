from django import forms
from django.utils import timezone
from ..models import JRClient


class ClientForm(forms.ModelForm):
    """Formulaire pour la création et modification des clients"""
    
    class Meta:
        model = JRClient
        fields = [
            'raison_sociale', 'contact_principal', 'email_contact', 
            'telephone_contact', 'adresse', 'code_postal', 'ville', 'pays',
            'numero_tva', 'conditions_paiement', 'statut'
        ]
        widgets = {
            'raison_sociale': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'entreprise'
            }),
            'contact_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du contact principal'
            }),
            'email_contact': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemple.com'
            }),
            'telephone_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '06 12 34 56 78'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '75000'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Paris'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'France'
            }),
            'numero_tva': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR12345678901'
            }),
            'conditions_paiement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Conditions de paiement...'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def clean_email_contact(self):
        """Validation de l'email"""
        email = self.cleaned_data.get('email_contact')
        if email:
            # Validation basique de format email
            if '@' not in email or '.' not in email:
                raise forms.ValidationError("Veuillez entrer une adresse email valide.")
        return email
    
    def clean_telephone_contact(self):
        """Validation du téléphone"""
        telephone = self.cleaned_data.get('telephone_contact')
        if telephone:
            # Nettoyage du numéro de téléphone
            telephone = telephone.replace(' ', '').replace('.', '').replace('-', '')
            if not telephone.isdigit() or len(telephone) < 10:
                raise forms.ValidationError("Veuillez entrer un numéro de téléphone valide.")
        return telephone


class ClientSearchForm(forms.Form):
    """Formulaire de recherche pour les clients"""
    
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, email, code...'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + JRClient.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    pays = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pays'
        })
    )
