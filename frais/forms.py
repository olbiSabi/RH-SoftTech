# frais/forms.py
"""
Formulaires pour le module Notes de Frais.
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

from frais.models import NFNF, NFLF, NFAV, NFCA, NFPL


class NoteFraisForm(forms.ModelForm):
    """Formulaire de création/modification d'une note de frais."""

    class Meta:
        model = NFNF
        fields = ['PERIODE_DEBUT', 'PERIODE_FIN', 'OBJET']
        widgets = {
            'PERIODE_DEBUT': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'PERIODE_FIN': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'OBJET': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ex: Mission Abidjan du 15 au 20 janvier'
                }
            ),
        }
        labels = {
            'PERIODE_DEBUT': 'Début de période',
            'PERIODE_FIN': 'Fin de période',
            'OBJET': 'Objet / Mission',
        }

    def clean(self):
        cleaned_data = super().clean()
        debut = cleaned_data.get('PERIODE_DEBUT')
        fin = cleaned_data.get('PERIODE_FIN')

        if debut and fin and fin < debut:
            raise ValidationError(
                "La date de fin doit être postérieure à la date de début"
            )

        return cleaned_data


class LigneFraisForm(forms.ModelForm):
    """Formulaire d'ajout/modification d'une ligne de frais."""

    class Meta:
        model = NFLF
        fields = [
            'CATEGORIE', 'DATE_DEPENSE', 'DESCRIPTION',
            'MONTANT', 'DEVISE', 'JUSTIFICATIF', 'NUMERO_FACTURE'
        ]
        widgets = {
            'CATEGORIE': forms.Select(attrs={'class': 'form-select'}),
            'DATE_DEPENSE': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'DESCRIPTION': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Description de la dépense'
                }
            ),
            'MONTANT': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '1',
                    'min': '1'
                }
            ),
            'DEVISE': forms.Select(
                attrs={'class': 'form-select'},
                choices=[
                    ('XOF', 'XOF - Franc CFA'),
                    ('EUR', 'EUR - Euro'),
                    ('USD', 'USD - Dollar US'),
                ]
            ),
            'JUSTIFICATIF': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.pdf,.jpg,.jpeg,.png'
                }
            ),
            'NUMERO_FACTURE': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'N° facture ou reçu'
                }
            ),
        }
        labels = {
            'CATEGORIE': 'Catégorie',
            'DATE_DEPENSE': 'Date de la dépense',
            'DESCRIPTION': 'Description',
            'MONTANT': 'Montant',
            'DEVISE': 'Devise',
            'JUSTIFICATIF': 'Justificatif',
            'NUMERO_FACTURE': 'N° facture/reçu',
        }

    def __init__(self, *args, **kwargs):
        self.note_frais = kwargs.pop('note_frais', None)
        super().__init__(*args, **kwargs)

        # Ne montrer que les catégories actives
        self.fields['CATEGORIE'].queryset = NFCA.objects.filter(STATUT=True)

    def clean_MONTANT(self):
        montant = self.cleaned_data.get('MONTANT')
        if montant and montant <= 0:
            raise ValidationError("Le montant doit être positif")
        return montant

    def clean_DATE_DEPENSE(self):
        date_depense = self.cleaned_data.get('DATE_DEPENSE')

        if self.note_frais and date_depense:
            if not (self.note_frais.PERIODE_DEBUT <= date_depense <= self.note_frais.PERIODE_FIN):
                raise ValidationError(
                    f"La date doit être comprise entre {self.note_frais.PERIODE_DEBUT} "
                    f"et {self.note_frais.PERIODE_FIN}"
                )

        return date_depense

    def clean(self):
        cleaned_data = super().clean()
        categorie = cleaned_data.get('CATEGORIE')
        justificatif = cleaned_data.get('JUSTIFICATIF')

        # Vérifier justificatif obligatoire
        if categorie and categorie.JUSTIFICATIF_OBLIGATOIRE:
            if not justificatif and not self.instance.JUSTIFICATIF:
                raise ValidationError(
                    f"Un justificatif est obligatoire pour la catégorie '{categorie.LIBELLE}'"
                )

        return cleaned_data


class AvanceForm(forms.ModelForm):
    """Formulaire de demande d'avance sur frais."""

    class Meta:
        model = NFAV
        fields = [
            'MONTANT_DEMANDE', 'MOTIF',
            'DATE_MISSION_DEBUT', 'DATE_MISSION_FIN'
        ]
        widgets = {
            'MONTANT_DEMANDE': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '1000',
                    'min': '1000'
                }
            ),
            'MOTIF': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Justification de la demande d\'avance'
                }
            ),
            'DATE_MISSION_DEBUT': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'DATE_MISSION_FIN': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }
        labels = {
            'MONTANT_DEMANDE': 'Montant demandé (XOF)',
            'MOTIF': 'Motif de la demande',
            'DATE_MISSION_DEBUT': 'Date début mission',
            'DATE_MISSION_FIN': 'Date fin mission',
        }

    def clean_MONTANT_DEMANDE(self):
        montant = self.cleaned_data.get('MONTANT_DEMANDE')
        if montant and montant < 1000:
            raise ValidationError("Le montant minimum est de 1000 XOF")
        return montant

    def clean(self):
        cleaned_data = super().clean()
        debut = cleaned_data.get('DATE_MISSION_DEBUT')
        fin = cleaned_data.get('DATE_MISSION_FIN')

        if debut and fin and fin < debut:
            raise ValidationError(
                "La date de fin de mission doit être postérieure à la date de début"
            )

        return cleaned_data


class ApprobationAvanceForm(forms.Form):
    """Formulaire d'approbation d'une avance."""

    montant_approuve = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'step': '1000'}
        ),
        label="Montant approuvé",
        help_text="Laisser vide pour approuver le montant demandé"
    )
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'rows': 2}
        ),
        label="Commentaire"
    )


class RejetForm(forms.Form):
    """Formulaire de rejet (note de frais ou avance)."""

    commentaire = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Motif du rejet (obligatoire)'
            }
        ),
        label="Motif du rejet"
    )


class ValidationLigneForm(forms.Form):
    """Formulaire de validation/rejet d'une ligne de frais."""

    action = forms.ChoiceField(
        choices=[
            ('valider', 'Valider'),
            ('rejeter', 'Rejeter'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'rows': 2}
        ),
        label="Commentaire (obligatoire si rejet)"
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        commentaire = cleaned_data.get('commentaire')

        if action == 'rejeter' and not commentaire:
            raise ValidationError("Un commentaire est obligatoire pour le rejet")

        return cleaned_data


class RemboursementForm(forms.Form):
    """Formulaire pour marquer une note comme remboursée."""

    date_remboursement = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        label="Date de remboursement"
    )
    reference_paiement = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Référence du virement'
            }
        ),
        label="Référence de paiement"
    )


class VersementAvanceForm(forms.Form):
    """Formulaire pour marquer une avance comme versée."""

    date_versement = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        label="Date de versement"
    )
    reference_versement = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Référence du virement'
            }
        ),
        label="Référence du versement"
    )


class CategorieForm(forms.ModelForm):
    """Formulaire pour les catégories de frais (admin)."""

    class Meta:
        model = NFCA
        fields = [
            'CODE', 'LIBELLE', 'DESCRIPTION',
            'JUSTIFICATIF_OBLIGATOIRE', 'PLAFOND_DEFAUT',
            'ICONE', 'ORDRE', 'STATUT'
        ]
        widgets = {
            'CODE': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform: uppercase;'}),
            'LIBELLE': forms.TextInput(attrs={'class': 'form-control'}),
            'DESCRIPTION': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2}
            ),
            'JUSTIFICATIF_OBLIGATOIRE': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'PLAFOND_DEFAUT': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '1000'}
            ),
            'ICONE': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'fa-car, fa-utensils, etc.'
                }
            ),
            'ORDRE': forms.NumberInput(attrs={'class': 'form-control'}),
            'STATUT': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PlafondForm(forms.ModelForm):
    """Formulaire pour les plafonds de frais (admin)."""

    class Meta:
        model = NFPL
        fields = [
            'CATEGORIE', 'GRADE', 'DATE_DEBUT', 'DATE_FIN',
            'MONTANT_JOURNALIER', 'MONTANT_MENSUEL', 'MONTANT_PAR_DEPENSE',
            'STATUT'
        ]
        widgets = {
            'CATEGORIE': forms.Select(attrs={'class': 'form-select'}),
            'GRADE': forms.TextInput(attrs={'class': 'form-control'}),
            'DATE_DEBUT': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'DATE_FIN': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'MONTANT_JOURNALIER': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '1000'}
            ),
            'MONTANT_MENSUEL': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '1000'}
            ),
            'MONTANT_PAR_DEPENSE': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '1000'}
            ),
            'STATUT': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FiltreNotesForm(forms.Form):
    """Formulaire de filtrage des notes de frais."""

    statut = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + NFNF.STATUT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        label="Du"
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        label="Au"
    )
    employe = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nom ou matricule'
            }
        ),
        label="Employé"
    )


class FiltreAvancesForm(forms.Form):
    """Formulaire de filtrage des avances."""

    statut = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + NFAV.STATUT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        label="Du"
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        label="Au"
    )
