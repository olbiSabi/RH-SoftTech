from django import forms
from .models import ZDAB


class ZDABForm(forms.ModelForm):
    """Formulaire pour le modèle ZDAB (Type d'Absence)"""  # ← Correction du commentaire

    class Meta:
        model = ZDAB
        fields = ['CODE', 'LIBELLE', 'STATUT']
        widgets = {
            'CODE': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'code',
                'maxlength': '3',
                'placeholder': 'Ex: CPN, RTT, MAL',  # ← Meilleurs exemples
                'style': 'text-transform: uppercase;'
            }),
            'LIBELLE': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'libelle',
                'placeholder': 'Ex: Congé Payé, RTT, Maladie'  # ← Meilleurs exemples
            }),
            'STATUT': forms.Select(
                choices=[(True, 'Actif'), (False, 'Inactif')],
                attrs={
                    'class': 'form-control',
                    'id': 'statut'
                }
            ),
        }
        labels = {
            'CODE': 'Code Absence *',
            'LIBELLE': 'Libellé *',
            'STATUT': 'Statut *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aucune initialisation particulière nécessaire pour l'instant

    def clean_CODE(self):
        """Validation du code"""
        code = self.cleaned_data.get('CODE', '').upper().strip()

        if len(code) != 3:
            raise forms.ValidationError('Le code doit contenir exactement 3 caractères.')

        if not code.isalpha():
            raise forms.ValidationError('Le code ne doit contenir que des lettres.')

        # Vérifier l'unicité (sauf pour l'instance actuelle en édition)
        qs = ZDAB.objects.filter(CODE=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('Ce code absence existe déjà.')

        return code