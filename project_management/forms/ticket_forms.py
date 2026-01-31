from django import forms
from django.utils import timezone
from ..models import JRTicket, JRProject
from employee.models import ZY00


class TicketForm(forms.ModelForm):
    """Formulaire pour la création et modification des tickets"""
    
    class Meta:
        model = JRTicket
        fields = [
            'projet', 'titre', 'description', 'priorite', 'statut',
            'assigne', 'type_ticket', 'estimation_heures', 'date_echeance',
            'dans_backlog'
        ]
        widgets = {
            'projet': forms.Select(attrs={
                'class': 'form-control'
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du ticket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Description détaillée du ticket...'
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-control'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assigne': forms.Select(attrs={
                'class': 'form-control'
            }),
            'type_ticket': forms.Select(attrs={
                'class': 'form-control'
            }),
            'estimation_heures': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.5',
                'min': '0'
            }),
            'date_echeance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'dans_backlog': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les projets actifs
        self.fields['projet'].queryset = JRProject.objects.filter(
            statut__in=['PLANIFIE', 'ACTIF']
        ).order_by('nom')
        
        # Filtrer les employés actifs
        self.fields['assigne'].queryset = ZY00.objects.filter(
            etat='actif'
        ).order_by('nom', 'prenoms')
        
        # Pour un nouveau ticket, le statut par défaut est OUVERT (caché)
        # Pour un ticket existant, on affiche le statut sauf s'il est dans le backlog
        if not self.instance.pk:
            # Nouveau ticket - statut caché, défaut OUVERT
            self.fields['statut'].widget = forms.HiddenInput()
            self.fields['statut'].initial = 'OUVERT'
        elif self.instance.dans_backlog:
            # Ticket dans le backlog - statut caché
            self.fields['statut'].widget = forms.HiddenInput()
    
    def clean_date_echeance(self):
        """Validation de la date d'échéance"""
        date_echeance = self.cleaned_data.get('date_echeance')
        if date_echeance and date_echeance < timezone.now().date():
            raise forms.ValidationError(
                "La date d'échéance ne peut pas être dans le passé."
            )
        return date_echeance
    
    def clean_estimation_heures(self):
        """Validation de l'estimation"""
        estimation = self.cleaned_data.get('estimation_heures')
        if estimation and estimation <= 0:
            raise forms.ValidationError(
                "L'estimation doit être supérieure à 0."
            )
        return estimation


class TicketSearchForm(forms.Form):
    """Formulaire de recherche pour les tickets"""
    
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par titre, code, description...'
        })
    )
    
    projet = forms.ModelChoiceField(
        queryset=JRProject.objects.filter(
            statut__in=['PLANIFIE', 'ACTIF']
        ),
        required=False,
        empty_label="Tous les projets",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigne = forms.ModelChoiceField(
        queryset=ZY00.objects.all(),
        required=False,
        empty_label="Non assigné",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + JRTicket.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priorite = forms.ChoiceField(
        choices=[('', 'Toutes les priorités')] + JRTicket.PRIORITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    type_ticket = forms.ChoiceField(
        choices=[('', 'Tous les types')] + JRTicket.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    dans_backlog = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    date_creation_min = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_creation_max = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class CommentaireForm(forms.ModelForm):
    """Formulaire pour les commentaires sur les tickets"""
    
    class Meta:
        model = JRTicket
        fields = []  # Pas de champs du modèle
        
    contenu = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ajouter un commentaire...',
            'id': 'commentaire_contenu'
        })
    )
    
    mentions = forms.ModelMultipleChoiceField(
        queryset=ZY00.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'id': 'commentaire_mentions'
        })
    )


class PieceJointeForm(forms.ModelForm):
    """Formulaire pour l'upload de pièces jointes"""
    
    class Meta:
        model = JRTicket
        fields = []  # Pas de champs du modèle
        
    fichier = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.zip,.rar'
        })
    )
