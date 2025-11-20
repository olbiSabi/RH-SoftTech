from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZDPO, ZYDO, ZYFA, ZYNP, ZYPP, ZYIB
from .pays_choices import PAYS_CHOICES

######################
###  Employe ZY00  ###
######################
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
    complement = forms.CharField(  # ← NOUVEAU CHAMP AJOUTÉ
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complément d\'adresse'}),
        label="Complément d'adresse"
    )
    ville = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
        label="Ville"
    )
    pays = forms.ChoiceField(
        choices=PAYS_CHOICES,
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

######################
###  Contrat ZYCO  ###
######################
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

    def clean(self):
        """Validation personnalisée pour les contrats"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin': 'La date de fin doit être supérieure à la date de début.'
            })

        return cleaned_data

######################
### Telephone ZYTE ###
######################
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

    def clean(self):
        """Validation personnalisée pour les téléphones"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut_validite')
        date_fin = cleaned_data.get('date_fin_validite')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin_validite': 'La date de fin doit être supérieure à la date de début.'
            })

        return cleaned_data

######################
#####  Mail ZYME  ####
######################
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

    def clean(self):
        """Validation personnalisée pour les emails"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut_validite')
        date_fin = cleaned_data.get('date_fin_validite')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin_validite': 'La date de fin doit être supérieure à la date de début.'
            })

        return cleaned_data

######################
## Affectation ZYAF ##
######################
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

    def clean(self):
        """Validation personnalisée pour les affectations"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin': 'La date de fin doit être supérieure à la date de début.'
            })

        return cleaned_data

######################
###  Adresse ZYAD  ###
######################
class ZYADForm(forms.ModelForm):
    """Formulaire pour les adresses"""

    class Meta:
        model = ZYAD
        fields = ['employe', 'rue', 'complement', 'ville', 'pays', 'code_postal', 'type_adresse', 'date_debut', 'date_fin']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'rue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rue'}),
            'complement': forms.TextInput(attrs={  # ← CHAMP CORRIGÉ (placeholder amélioré)
                'class': 'form-control',
                'placeholder': 'Appartement, étage, bâtiment...'
            }),
            'ville': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
            'pays': forms.Select(choices=PAYS_CHOICES, attrs={'class': 'form-control'}),
            'code_postal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code postal'}),
            'type_adresse': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        """Validation personnalisée pour les adresses"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin': 'La date de fin doit être supérieure à la date de début.'
            })

        return cleaned_data


######################
### Documment ZYDO ###
######################
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

######################
###  Famille  ZYFA ###
######################
class ZYFAForm(forms.ModelForm):
    """Formulaire pour les personnes à charge"""

    class Meta:
        model = ZYFA
        fields = ['employe', 'personne_charge', 'nom', 'prenom', 'sexe',
                 'date_naissance', 'date_debut_prise_charge', 'date_fin_prise_charge']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'personne_charge': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_debut_prise_charge': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_prise_charge': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut_prise_charge')
        date_fin = cleaned_data.get('date_fin_prise_charge')
        date_naissance = cleaned_data.get('date_naissance')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin_prise_charge': 'La date de fin doit être supérieure à la date de début.'
            })

        # Validation: date naissance dans le passé
        if date_naissance and date_naissance > timezone.now().date():
            raise forms.ValidationError({
                'date_naissance': 'La date de naissance doit être dans le passé.'
            })

        return cleaned_data


######################
### Historique Nom Prénom ZYNP ###
######################
class ZYNPForm(forms.ModelForm):
    """Formulaire pour l'historique des noms et prénoms"""

    class Meta:
        model = ZYNP
        fields = ['employe', 'nom', 'prenoms', 'date_debut_validite', 'date_fin_validite', 'actif']
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom(s)'}),
            'date_debut_validite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_validite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut_validite')
        date_fin = cleaned_data.get('date_fin_validite')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin_validite': 'La date de fin doit être supérieure à la date de début.'
            })

        return cleaned_data


######################
### Personne à Prévenir ZYPP ###
######################
class ZYPPForm(forms.ModelForm):
    """Formulaire pour les personnes à prévenir en cas d'urgence"""

    class Meta:
        model = ZYPP
        fields = [
            'employe', 'nom', 'prenom', 'lien_parente',
            'telephone_principal', 'telephone_secondaire', 'email',
            'adresse', 'ordre_priorite', 'remarques',
            'date_debut_validite', 'date_fin_validite', 'actif'
        ]
        widgets = {
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la personne à prévenir'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom de la personne à prévenir'
            }),
            'lien_parente': forms.Select(attrs={'class': 'form-control'}),
            'telephone_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: +33 6 12 34 56 78'
            }),
            'telephone_secondaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone secondaire (optionnel)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email (optionnel)'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse complète (optionnelle)',
                'rows': 3
            }),
            'ordre_priorite': forms.Select(attrs={'class': 'form-control'}),
            'remarques': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Remarques ou informations complémentaires (optionnel)',
                'rows': 3
            }),
            'date_debut_validite': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_validite': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut_validite')
        date_fin = cleaned_data.get('date_fin_validite')
        telephone_principal = cleaned_data.get('telephone_principal')
        telephone_secondaire = cleaned_data.get('telephone_secondaire')

        # Validation: date fin > date début
        if date_fin and date_debut and date_fin <= date_debut:
            raise forms.ValidationError({
                'date_fin_validite': 'La date de fin doit être supérieure à la date de début.'
            })

        # Validation: téléphone principal obligatoire
        if not telephone_principal:
            raise forms.ValidationError({
                'telephone_principal': 'Le téléphone principal est obligatoire.'
            })

        # Validation: les deux téléphones ne doivent pas être identiques
        if telephone_secondaire and telephone_principal == telephone_secondaire:
            raise forms.ValidationError({
                'telephone_secondaire': 'Le téléphone secondaire doit être différent du téléphone principal.'
            })

        return cleaned_data

    def clean_telephone_principal(self):
        """Validation du téléphone principal"""
        telephone = self.cleaned_data.get('telephone_principal')

        if telephone:
            # Nettoyer le numéro (enlever espaces, tirets, etc.)
            telephone_nettoye = ''.join(filter(str.isdigit, telephone.replace('+', '')))

            # Vérifier longueur minimale (au moins 8 chiffres)
            if len(telephone_nettoye) < 8:
                raise forms.ValidationError(
                    'Le numéro de téléphone doit contenir au moins 8 chiffres.'
                )

        return telephone

    def clean_telephone_secondaire(self):
        """Validation du téléphone secondaire"""
        telephone = self.cleaned_data.get('telephone_secondaire')

        if telephone:
            # Nettoyer le numéro
            telephone_nettoye = ''.join(filter(str.isdigit, telephone.replace('+', '')))

            # Vérifier longueur minimale
            if len(telephone_nettoye) < 8:
                raise forms.ValidationError(
                    'Le numéro de téléphone doit contenir au moins 8 chiffres.'
                )

        return telephone


######################
### Identité Bancaire ZYIB ###
######################
class ZYIBForm(forms.ModelForm):
    """Formulaire pour les identités bancaires"""
    class Meta:
        model = ZYIB
        fields = [
            'titulaire_compte', 'nom_banque', 'code_banque', 'code_guichet',
            'numero_compte', 'cle_rib', 'iban', 'bic', 'type_compte',
            'domiciliation', 'date_ouverture', 'remarques', 'actif'
        ]
        widgets = {
            'titulaire_compte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du titulaire du compte'
            }),
            'nom_banque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Crédit Agricole, BNP Paribas...'
            }),
            'code_banque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345',
                'maxlength': '5',
                'pattern': '[0-9]{5}'
            }),
            'code_guichet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345',
                'maxlength': '5',
                'pattern': '[0-9]{5}'
            }),
            'numero_compte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678901',
                'maxlength': '11'
            }),
            'cle_rib': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12',
                'maxlength': '2',
                'pattern': '[0-9]{2}'
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR76 1234 5678 9012 3456 7890 123',
                'maxlength': '34'
            }),
            'bic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BNPAFRPP ou BNPAFRPPXXX',
                'maxlength': '11'
            }),
            'type_compte': forms.Select(attrs={'class': 'form-control'}),
            'domiciliation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse de l\'agence bancaire'
            }),
            'date_ouverture': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'remarques': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Remarques éventuelles...'
            }),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()

        # Validation supplémentaire si nécessaire
        code_banque = cleaned_data.get('code_banque')
        code_guichet = cleaned_data.get('code_guichet')
        numero_compte = cleaned_data.get('numero_compte')
        cle_rib = cleaned_data.get('cle_rib')

        # Vérifier que tous les champs RIB sont remplis ensemble
        rib_fields = [code_banque, code_guichet, numero_compte, cle_rib]
        if any(rib_fields) and not all(rib_fields):
            raise forms.ValidationError(
                "Tous les champs du RIB doivent être remplis (code banque, code guichet, numéro de compte et clé)."
            )

        return cleaned_data

# Formset pour gérer plusieurs personnes à prévenir
PersonnePrevenirFormSet = inlineformset_factory(
    ZY00, ZYPP,
    form=ZYPPForm,
    extra=1,
    can_delete=True
)

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

# Formset pour gérer plusieurs personnes à prévenir
IdentiteBancaireFormSet = inlineformset_factory(
    ZY00, ZYIB,
    form=ZYIBForm,
    extra=1,
    can_delete=True
)


