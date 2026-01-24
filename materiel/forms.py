# materiel/forms.py
"""
Formulaires pour le module Suivi du Matériel & Parc.
"""
from django import forms
from django.utils import timezone
from .models import MTCA, MTFO, MTMT, MTAF, MTMA, MTMV

# Liste d'icônes courantes pour les catégories
ICONE_CHOICES = [
    ('', 'Sélectionner une icône'),
    # Matériel informatique
    ('fa-laptop', ' Ordinateur portable'),
    ('fa-desktop', ' Ordinateur de bureau'),
    ('fa-server', ' Serveur'),
    ('fa-keyboard', ' Clavier'),
    ('fa-mouse', ' Souris'),
    ('fa-print', ' Imprimante'),
    ('fa-scanner', ' Scanner'),
    ('fa-wifi', ' WiFi'),
    ('fa-network-wired', ' Réseau'),
    ('fa-hard-drive', ' Disque dur'),
    ('fa-memory', ' Mémoire RAM'),
    ('fa-microchip', ' Processeur'),
    ('fa-usb', ' USB'),
    ('fa-headphones', ' Écouteurs'),
    ('fa-camera', ' Appareil photo'),
    ('fa-video', ' Caméra'),
    ('fa-phone', ' Téléphone'),
    ('fa-tablet-alt', ' Tablette'),
    ('fa-mobile-alt', ' Mobile'),
    
    # Matériel de bureau
    ('fa-chair', ' Chaise'),
    ('fa-desk', ' Bureau'),
    ('fa-couch', ' Canapé'),
    ('fa-door-open', ' Porte'),
    ('fa-lightbulb', ' Ampoule'),
    ('fa-fan', ' Ventilateur'),
    ('fa-temperature-high', ' Climatisation'),
    
    # Véhicules
    ('fa-car', ' Voiture'),
    ('fa-truck', ' Camion'),
    ('fa-motorcycle', ' Moto'),
    ('fa-bicycle', ' Vélo'),
    
    # Outils
    ('fa-tools', ' Outils'),
    ('fa-wrench', ' Clé à molette'),
    ('fa-hammer', ' Marteau'),
    ('fa-screwdriver', ' Tournevis'),
    ('fa-drill', ' Perceuse'),
    
    # Autres
    ('fa-box', ' Colis'),
    ('fa-archive', ' Archive'),
    ('fa-folder', ' Dossier'),
    ('fa-tag', ' Étiquette'),
    ('fa-qrcode', ' QR Code'),
    ('fa-barcode', ' Code barre'),
    ('fa-shield-alt', ' Sécurité'),
    ('fa-lock', ' Cadenas'),
    ('fa-key', ' Clé'),
    ('fa-clock', ' Horloge'),
    ('fa-calendar', ' Calendrier'),
    ('fa-map-marker-alt', ' Localisation'),
    ('fa-home', ' Maison'),
    ('fa-building', ' Bâtiment'),
    ('fa-industry', ' Industrie'),
    ('fa-warehouse', ' Entrepôt'),
]


class MTCAForm(forms.ModelForm):
    """Formulaire pour les catégories de matériel."""
    
    ICONE = forms.ChoiceField(
        choices=ICONE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label='Icône'
    )

    class Meta:
        model = MTCA
        fields = [
            'CODE', 'LIBELLE', 'DESCRIPTION', 'DUREE_AMORTISSEMENT',
            'ICONE', 'STATUT', 'ORDRE'
        ]
        widgets = {
            'CODE': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: INFO', 'style': 'text-transform: uppercase;'}),
            'LIBELLE': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Matériel Informatique'}),
            'DESCRIPTION': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'DUREE_AMORTISSEMENT': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'ORDRE': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'STATUT': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 20px; height: 20px; cursor: pointer;'}),
        }


class MTFOForm(forms.ModelForm):
    """Formulaire pour les fournisseurs."""

    class Meta:
        model = MTFO
        fields = [
            'RAISON_SOCIALE', 'CONTACT', 'ADRESSE',
            'TELEPHONE', 'EMAIL', 'SITE_WEB', 'NOTES', 'STATUT'
        ]
        widgets = {
            'RAISON_SOCIALE': forms.TextInput(attrs={'class': 'form-control'}),
            'CONTACT': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du contact'}),
            'ADRESSE': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'TELEPHONE': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+225 XX XX XX XX'}),
            'EMAIL': forms.EmailInput(attrs={'class': 'form-control'}),
            'SITE_WEB': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'NOTES': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'STATUT': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 20px; height: 20px; cursor: pointer;'}),
        }


class MTMTForm(forms.ModelForm):
    """Formulaire pour le matériel."""

    class Meta:
        model = MTMT
        fields = [
            'CATEGORIE', 'DESIGNATION', 'CARACTERISTIQUES',
            'MARQUE', 'MODELE', 'NUMERO_SERIE', 'DATE_ACQUISITION',
            'FOURNISSEUR', 'PRIX_ACQUISITION', 'NUMERO_FACTURE',
            'DATE_FIN_GARANTIE', 'CONDITIONS_GARANTIE', 'ETAT',
            'LOCALISATION', 'NOTES'
        ]
        widgets = {
            'CATEGORIE': forms.Select(attrs={'class': 'form-control select2'}),
            'DESIGNATION': forms.TextInput(attrs={'class': 'form-control'}),
            'CARACTERISTIQUES': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'MARQUE': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Dell, HP, Lenovo'}),
            'MODELE': forms.TextInput(attrs={'class': 'form-control'}),
            'NUMERO_SERIE': forms.TextInput(attrs={'class': 'form-control'}),
            'DATE_ACQUISITION': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'FOURNISSEUR': forms.Select(attrs={'class': 'form-control select2'}),
            'PRIX_ACQUISITION': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '1'}),
            'NUMERO_FACTURE': forms.TextInput(attrs={'class': 'form-control'}),
            'DATE_FIN_GARANTIE': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'CONDITIONS_GARANTIE': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'ETAT': forms.Select(attrs={'class': 'form-control'}),
            'LOCALISATION': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bureau, étage, bâtiment...'}),
            'NOTES': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['CATEGORIE'].queryset = MTCA.objects.filter(STATUT=True).order_by('ORDRE', 'LIBELLE')
        self.fields['FOURNISSEUR'].queryset = MTFO.objects.filter(STATUT=True).order_by('RAISON_SOCIALE')
        self.fields['FOURNISSEUR'].required = False


class MTMTEditForm(forms.ModelForm):
    """Formulaire d'édition du matériel (champs restreints)."""

    class Meta:
        model = MTMT
        fields = [
            'DESIGNATION', 'CARACTERISTIQUES', 'ETAT', 'LOCALISATION',
            'DATE_FIN_GARANTIE', 'CONDITIONS_GARANTIE', 'NOTES'
        ]
        widgets = {
            'DESIGNATION': forms.TextInput(attrs={'class': 'form-control'}),
            'CARACTERISTIQUES': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ETAT': forms.Select(attrs={'class': 'form-control'}),
            'LOCALISATION': forms.TextInput(attrs={'class': 'form-control'}),
            'DATE_FIN_GARANTIE': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'CONDITIONS_GARANTIE': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'NOTES': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AffectationForm(forms.Form):
    """Formulaire pour affecter un matériel à un employé."""

    TYPE_CHOICES = [
        ('AFFECTATION', 'Affectation définitive'),
        ('PRET', 'Prêt temporaire'),
    ]

    # employe_id reçoit le matricule de l'employé sélectionné via Select2
    employe_id = forms.CharField(
        required=False,
        label='Employé'
    )
    type_affectation = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Type'
    )
    date_retour_prevue = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date de retour prévue (prêt)'
    )
    motif = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label='Motif'
    )

    def clean(self):
        cleaned_data = super().clean()
        employe_id = cleaned_data.get('employe_id')
        type_affectation = cleaned_data.get('type_affectation')
        date_retour = cleaned_data.get('date_retour_prevue')

        # Vérifier que l'employé est sélectionné
        if not employe_id:
            self.add_error('employe_id', 'Veuillez sélectionner un employé dans la liste.')

        # Validation de la date de retour uniquement pour les prêts
        if type_affectation == 'PRET':
            if not date_retour:
                self.add_error('date_retour_prevue', 'La date de retour est obligatoire pour un prêt.')
            elif date_retour <= timezone.now().date():
                self.add_error('date_retour_prevue', 'La date de retour doit être dans le futur.')

        return cleaned_data


class RetourForm(forms.Form):
    """Formulaire pour le retour d'un matériel."""

    etat_retour = forms.ChoiceField(
        choices=MTMT.ETAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='État au retour'
    )
    observations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Observations'
    )


class MTMAForm(forms.ModelForm):
    """Formulaire pour les maintenances."""

    class Meta:
        model = MTMA
        fields = [
            'TYPE_MAINTENANCE', 'DATE_PLANIFIEE', 'DESCRIPTION',
            'PRESTATAIRE', 'INTERVENANT_INTERNE'
        ]
        widgets = {
            'TYPE_MAINTENANCE': forms.Select(attrs={'class': 'form-control'}),
            'DATE_PLANIFIEE': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'DESCRIPTION': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'PRESTATAIRE': forms.Select(attrs={'class': 'form-control select2'}),
            'INTERVENANT_INTERNE': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['PRESTATAIRE'].queryset = MTFO.objects.filter(STATUT=True).order_by('RAISON_SOCIALE')
        self.fields['PRESTATAIRE'].required = False
        # L'intervenant interne sera géré via autocomplete
        self.fields['INTERVENANT_INTERNE'].required = False


class TerminerMaintenanceForm(forms.Form):
    """Formulaire pour terminer une maintenance."""

    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date de fin',
        initial=timezone.now().date
    )
    cout_pieces = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': 0}),
        label='Coût des pièces (XOF)'
    )
    cout_main_oeuvre = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': 0}),
        label='Coût main d\'œuvre (XOF)'
    )
    etat_materiel = forms.ChoiceField(
        choices=MTMT.ETAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='État du matériel après maintenance'
    )
    rapport = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label='Rapport d\'intervention'
    )


class ReformeForm(forms.Form):
    """Formulaire pour réformer un matériel."""

    motif = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Motif de la réforme'
    )
    valeur_residuelle = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': 0}),
        label='Valeur résiduelle (XOF)'
    )


class FiltresMaterielForm(forms.Form):
    """Formulaire de filtres pour la liste du matériel."""

    STATUT_CHOICES = [('', 'Tous les statuts')] + list(MTMT.STATUT_CHOICES)
    ETAT_CHOICES = [('', 'Tous les états')] + list(MTMT.ETAT_CHOICES)

    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Code, désignation, n° série...'
        })
    )
    categorie = forms.ModelChoiceField(
        required=False,
        queryset=MTCA.objects.filter(STATUT=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Toutes catégories'
    )
    statut = forms.ChoiceField(
        required=False,
        choices=STATUT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    etat = forms.ChoiceField(
        required=False,
        choices=ETAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fournisseur = forms.ModelChoiceField(
        required=False,
        queryset=MTFO.objects.filter(STATUT=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Tous fournisseurs'
    )


class FiltresMaintenanceForm(forms.Form):
    """Formulaire de filtres pour les maintenances."""

    TYPE_CHOICES = [('', 'Tous types')] + list(MTMA.TYPE_CHOICES)
    STATUT_CHOICES = [('', 'Tous statuts')] + list(MTMA.STATUT_CHOICES)

    type_maintenance = forms.ChoiceField(
        required=False,
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    statut = forms.ChoiceField(
        required=False,
        choices=STATUT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
