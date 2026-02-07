"""
Formulaires pour le module GAC (Gestion des Achats & Commandes).

Ce module contient tous les formulaires Django pour la création et
modification des différents objets du module.
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import (
    GACDemandeAchat,
    GACLigneDemandeAchat,
    GACBonCommande,
    GACLigneBonCommande,
    GACFournisseur,
    GACReception,
    GACLigneReception,
    GACArticle,
    GACCategorie,
    GACBudget,
    GACParametres,
)
from employee.models import ZY00
from departement.models import ZDDE
from project_management.models import JRProject


# ========== Formulaires pour les Demandes d'achat ==========

class DemandeAchatForm(forms.ModelForm):
    """Formulaire pour créer/modifier une demande d'achat."""

    class Meta:
        model = GACDemandeAchat
        fields = [
            'objet',
            'justification',
            'departement',
            'projet',
            'budget',
            'priorite',
        ]
        widgets = {
            'objet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Objet de la demande',
            }),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Justification métier de la demande',
            }),
            'departement': forms.Select(attrs={
                'class': 'form-control',
            }),
            'projet': forms.Select(attrs={
                'class': 'form-control',
            }),
            'budget': forms.Select(attrs={
                'class': 'form-control',
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Rendre certains champs optionnels
        self.fields['departement'].required = False
        self.fields['projet'].required = False
        self.fields['budget'].required = False

        # Filtrer les budgets actifs (dont la date de fin n'est pas dépassée)
        from django.utils import timezone
        today = timezone.now().date()
        self.fields['budget'].queryset = GACBudget.objects.filter(date_fin__gte=today)


class LigneDemandeAchatForm(forms.ModelForm):
    """Formulaire pour ajouter une ligne à une demande d'achat."""

    class Meta:
        model = GACLigneDemandeAchat
        fields = [
            'article',
            'quantite',
            'prix_unitaire',
            'taux_tva',
            'commentaire',
        ]
        widgets = {
            'article': forms.Select(attrs={
                'class': 'form-control',
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'taux_tva': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Commentaire optionnel',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les articles actifs uniquement
        self.fields['article'].queryset = GACArticle.objects.filter(statut='ACTIF')

        # Rendre le commentaire optionnel
        self.fields['commentaire'].required = False

        # Pré-remplir le taux de TVA si l'article est sélectionné (modification uniquement)
        if self.instance and hasattr(self.instance, 'article') and self.instance.article:
            self.fields['taux_tva'].initial = self.instance.article.taux_tva


class DemandeRefusForm(forms.Form):
    """Formulaire pour refuser une demande."""

    motif_refus = forms.CharField(
        label='Motif du refus',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Veuillez indiquer le motif du refus',
        })
    )


class DemandeAnnulationForm(forms.Form):
    """Formulaire pour annuler une demande."""

    motif_annulation = forms.CharField(
        label='Motif d\'annulation',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Veuillez indiquer le motif de l\'annulation',
        })
    )


class DemandeValidationForm(forms.Form):
    """Formulaire pour valider une demande (N1 ou N2)."""

    commentaire = forms.CharField(
        label='Commentaire',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire optionnel',
        })
    )


# ========== Formulaires pour les Bons de commande ==========

class BonCommandeForm(forms.ModelForm):
    """Formulaire pour créer/modifier un bon de commande."""

    class Meta:
        model = GACBonCommande
        fields = [
            'fournisseur',
            'date_livraison_souhaitee',
            'conditions_paiement',
            'adresse_livraison',
        ]
        widgets = {
            'fournisseur': forms.Select(attrs={
                'class': 'form-control',
            }),
            'date_livraison_souhaitee': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'conditions_paiement': forms.Select(attrs={
                'class': 'form-control',
            }),
            'adresse_livraison': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les fournisseurs actifs uniquement
        self.fields['fournisseur'].queryset = GACFournisseur.objects.filter(
            statut='ACTIF'
        )

        # Rendre certains champs optionnels
        self.fields['date_livraison_souhaitee'].required = False
        self.fields['conditions_paiement'].required = False


class LigneBonCommandeForm(forms.ModelForm):
    """Formulaire pour ajouter une ligne à un bon de commande."""

    class Meta:
        model = GACLigneBonCommande
        fields = [
            'article',
            'quantite_commandee',
            'prix_unitaire',
            'taux_tva',
            'commentaire',
        ]
        widgets = {
            'article': forms.Select(attrs={
                'class': 'form-control',
            }),
            'quantite_commandee': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'taux_tva': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['article'].queryset = GACArticle.objects.filter(statut='ACTIF')
        self.fields['commentaire'].required = False


class BonCommandeEnvoiForm(forms.Form):
    """Formulaire pour envoyer un BC au fournisseur."""

    email_destinataire = forms.EmailField(
        label='Email destinataire',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Laisser vide pour utiliser l\'email du fournisseur',
        })
    )


class BonCommandeConfirmationForm(forms.Form):
    """Formulaire pour confirmer un BC."""

    numero_confirmation_fournisseur = forms.CharField(
        label='N° de confirmation fournisseur',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro de confirmation du fournisseur',
        })
    )

    date_livraison_confirmee = forms.DateField(
        label='Date de livraison confirmée',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )


# ========== Formulaires pour les Fournisseurs ==========

class FournisseurForm(forms.ModelForm):
    """Formulaire pour créer/modifier un fournisseur."""

    class Meta:
        model = GACFournisseur
        fields = [
            'raison_sociale',
            'nif',
            'numero_tva',
            'email',
            'telephone',
            'fax',
            'adresse',
            'code_postal',
            'ville',
            'pays',
            'nom_contact',
            'email_contact',
            'telephone_contact',
            'conditions_paiement',
            'iban',
        ]
        widgets = {
            'raison_sociale': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'nif': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '9 à 10 chiffres (optionnel)',
            }),
            'numero_tva': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR12345678901',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'nom_contact': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'email_contact': forms.EmailInput(attrs={
                'class': 'form-control',
            }),
            'telephone_contact': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'conditions_paiement': forms.Select(attrs={
                'class': 'form-control',
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
            }),
        }

    def clean_nif(self):
        """Valide le format du NIF."""
        nif = self.cleaned_data.get('nif')
        if nif:
            # Retirer les espaces
            nif = nif.replace(' ', '')

            # Vérifier que ce sont des chiffres et que c'est entre 9 et 10 chiffres
            if not nif.isdigit() or len(nif) < 9 or len(nif) > 10:
                raise ValidationError('Le NIF doit contenir entre 9 et 10 chiffres')

        return nif


class FournisseurEvaluationForm(forms.Form):
    """Formulaire pour évaluer un fournisseur."""

    note_qualite = forms.IntegerField(
        label='Note qualité',
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '5',
        })
    )

    note_delai = forms.IntegerField(
        label='Note délai',
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '5',
        })
    )

    note_prix = forms.IntegerField(
        label='Note prix',
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '5',
        })
    )

    commentaire = forms.CharField(
        label='Commentaire',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        })
    )


# ========== Formulaires pour les Réceptions ==========

class ReceptionForm(forms.ModelForm):
    """Formulaire pour créer une réception."""

    class Meta:
        model = GACReception
        fields = [
            'date_reception',
        ]
        widgets = {
            'date_reception': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.bon_commande = kwargs.pop('bon_commande', None)
        super().__init__(*args, **kwargs)

        # Si un bon de commande est fourni, créer des champs dynamiques pour chaque ligne
        if self.bon_commande:
            for ligne_bc in self.bon_commande.lignes.all():
                # Champ pour la quantité reçue
                self.fields[f'quantite_recue_{ligne_bc.uuid}'] = forms.DecimalField(
                    label=f'Quantité reçue',
                    required=False,
                    initial=0,
                    min_value=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': '0',
                        'step': '0.01',
                    })
                )

                # Champ pour la quantité acceptée
                self.fields[f'quantite_acceptee_{ligne_bc.uuid}'] = forms.DecimalField(
                    label=f'Quantité acceptée',
                    required=False,
                    initial=0,
                    min_value=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': '0',
                        'step': '0.01',
                    })
                )

                # Champ pour la quantité refusée
                self.fields[f'quantite_refusee_{ligne_bc.uuid}'] = forms.DecimalField(
                    label=f'Quantité refusée',
                    required=False,
                    initial=0,
                    min_value=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': '0',
                        'step': '0.01',
                    })
                )

                # Champ pour le motif de refus
                self.fields[f'motif_refus_{ligne_bc.uuid}'] = forms.CharField(
                    label=f'Motif de refus',
                    required=False,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 2,
                    })
                )


class LigneReceptionForm(forms.ModelForm):
    """Formulaire pour enregistrer une ligne de réception."""

    class Meta:
        model = GACLigneReception
        fields = [
            'ligne_bon_commande',
            'quantite_recue',
            'quantite_acceptee',
            'quantite_refusee',
            'motif_refus',
            'commentaire',
        ]
        widgets = {
            'ligne_bon_commande': forms.Select(attrs={
                'class': 'form-control',
            }),
            'quantite_recue': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'quantite_acceptee': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'quantite_refusee': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'value': '0',
            }),
            'motif_refus': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def clean(self):
        """Valide que quantite_acceptee + quantite_refusee = quantite_recue."""
        cleaned_data = super().clean()
        quantite_recue = cleaned_data.get('quantite_recue')
        quantite_acceptee = cleaned_data.get('quantite_acceptee')
        quantite_refusee = cleaned_data.get('quantite_refusee')

        if all([quantite_recue, quantite_acceptee is not None, quantite_refusee is not None]):
            if quantite_acceptee + quantite_refusee != quantite_recue:
                raise ValidationError(
                    'La somme des quantités acceptée et refusée doit égaler '
                    'la quantité reçue.'
                )

        return cleaned_data


# ========== Formulaires pour le Catalogue ==========

class CategorieForm(forms.ModelForm):
    """Formulaire pour créer/modifier une catégorie."""

    class Meta:
        model = GACCategorie
        fields = [
            'nom',
            'parent',
            'description',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False
        self.fields['description'].required = False


class ArticleForm(forms.ModelForm):
    """Formulaire pour créer/modifier un article."""

    class Meta:
        model = GACArticle
        fields = [
            'designation',
            'categorie',
            'description',
            'prix_unitaire',
            'unite',
            'taux_tva',
            'statut',
        ]
        widgets = {
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'unite': forms.Select(attrs={
                'class': 'form-control',
            }),
            'taux_tva': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


# ========== Formulaires pour les Budgets ==========

class BudgetForm(forms.ModelForm):
    """Formulaire pour créer/modifier un budget."""

    class Meta:
        model = GACBudget
        fields = [
            'libelle',
            'description',
            'exercice',
            'date_debut',
            'date_fin',
            'montant_initial',
            'departement',
            'gestionnaire',
            'seuil_alerte_1',
            'seuil_alerte_2',
        ]
        widgets = {
            'libelle': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
            'exercice': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2020',
                'max': '2050',
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'montant_initial': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'departement': forms.Select(attrs={
                'class': 'form-control',
            }),
            'gestionnaire': forms.Select(attrs={
                'class': 'form-control',
            }),
            'seuil_alerte_1': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.1',
            }),
            'seuil_alerte_2': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.1',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['departement'].required = False
        self.fields['description'].required = False


# ========== Formulaires pour les Réceptions (compléments) ==========

class ReceptionValidationForm(forms.Form):
    """Formulaire pour valider une réception."""

    commentaire = forms.CharField(
        label='Commentaire',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire sur la validation...'
        })
    )


class ReceptionAnnulationForm(forms.Form):
    """Formulaire pour annuler une réception."""

    motif = forms.CharField(
        label='Motif d\'annulation',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Expliquez la raison de l\'annulation...'
        })
    )


# ========== Formulaires pour les ArticleFournisseur ==========

class ArticleFournisseurForm(forms.ModelForm):
    """Formulaire pour associer un article à un fournisseur."""

    class Meta:
        model = GACArticle.fournisseurs.through
        fields = [
            'fournisseur',
            'reference_fournisseur',
            'prix_fournisseur',
            'delai_livraison',
            'fournisseur_principal',
        ]
        widgets = {
            'fournisseur': forms.Select(attrs={
                'class': 'form-control',
            }),
            'reference_fournisseur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence chez le fournisseur',
            }),
            'prix_fournisseur': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'delai_livraison': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
            'fournisseur_principal': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


# ========================================
# FORMULAIRE PARAMÈTRES
# ========================================

class GACParametresForm(forms.ModelForm):
    """
    Formulaire pour modifier les paramètres de configuration GAC.
    """

    class Meta:
        model = GACParametres
        fields = [
            'seuil_validation_n2',
            'delai_livraison_defaut',
            'notifier_demandeur',
            'notifier_validateurs',
        ]
        widgets = {
            'seuil_validation_n2': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '5000.00',
            }),
            'delai_livraison_defaut': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '30',
            }),
            'notifier_demandeur': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'notifier_validateurs': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si aucune instance n'est fournie, récupérer les paramètres existants
        if not self.instance.pk:
            self.instance = GACParametres.get_parametres()
