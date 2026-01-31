from django import forms
from django.utils import timezone
from ..models import JRSprint, JRProject, JRTicket


class SprintForm(forms.ModelForm):
    """Formulaire pour la création et modification des sprints"""
    
    class Meta:
        model = JRSprint
        fields = [
            'nom', 'description', 'projet', 'date_debut', 
            'date_fin', 'statut'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du sprint'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du sprint...'
            }),
            'projet': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les projets actifs
        self.fields['projet'].queryset = JRProject.objects.filter(
            statut__in=['PLANIFIE', 'ACTIF']
        ).order_by('nom')
    
    def clean_date_fin(self):
        """Validation que la date de fin est après la date de début"""
        date_debut = self.cleaned_data.get('date_debut')
        date_fin = self.cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise forms.ValidationError(
                    "La date de fin doit être postérieure à la date de début."
                )
            
            # Vérifier que le sprint ne fait pas plus de 4 semaines
            duree = (date_fin - date_debut).days
            if duree > 28:
                raise forms.ValidationError(
                    "La durée d'un sprint ne doit pas dépasser 4 semaines (28 jours)."
                )
        
        return date_fin
    
    def clean_nom(self):
        """Validation du nom du sprint"""
        nom = self.cleaned_data.get('nom')
        if nom:
            projet = self.cleaned_data.get('projet')
            if projet:
                # Vérifier que le nom est unique pour ce projet
                existing_sprint = JRSprint.objects.filter(
                    projet=projet,
                    nom__iexact=nom
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if existing_sprint.exists():
                    raise forms.ValidationError(
                        "Un sprint avec ce nom existe déjà pour ce projet."
                    )
        
        return nom


class SprintTicketForm(forms.ModelForm):
    """Formulaire pour ajouter/retirer des tickets d'un sprint"""
    
    class Meta:
        model = JRSprint
        fields = ['tickets']
        widgets = {
            'tickets': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, projet, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les tickets du projet qui ne sont pas terminés
        self.fields['tickets'].queryset = JRTicket.objects.filter(
            projet=projet,
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
        ).order_by('ordre_backlog', 'created_at')


class SprintSearchForm(forms.Form):
    """Formulaire de recherche pour les sprints"""
    
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom...'
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
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + JRSprint.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_debut_min = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_debut_max = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class BacklogForm(forms.Form):
    """Formulaire pour la gestion du backlog"""
    
    tickets = forms.ModelMultipleChoiceField(
        queryset=JRTicket.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )
    
    def __init__(self, projet, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les tickets du projet dans le backlog
        self.fields['tickets'].queryset = JRTicket.objects.filter(
            projet=projet,
            dans_backlog=True
        ).order_by('ordre_backlog', 'created_at')
