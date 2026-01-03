# absence/forms.py
from .models import JourFerie, ValidationAbsence
from datetime import datetime
from .models import ConfigurationConventionnelle
from .models import ParametreCalculConges
from employee.models import ZY00
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from django.db import models
from .models import Absence, TypeAbsence, AcquisitionConges


class ConfigurationConventionnelleForm(forms.ModelForm):
    """Formulaire pour ConfigurationConventionnelle"""

    class Meta:
        model = ConfigurationConventionnelle
        fields = [
            'nom', 'code', 'annee_reference',
            'date_debut', 'date_fin', 'actif',
            'jours_acquis_par_mois', 'duree_conges_principale',
            'periode_prise_debut', 'periode_prise_fin',
            'methode_calcul'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Convention Cadres 2025'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CONV_CADRES_2025'
            }),
            'annee_reference': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2025',
                'min': '2020',
                'max': '2099'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'jours_acquis_par_mois': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '5'
            }),
            'duree_conges_principale': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30'
            }),
            'periode_prise_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'periode_prise_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'methode_calcul': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Marquer les champs requis
        self.fields['nom'].required = True
        self.fields['code'].required = True
        self.fields['annee_reference'].required = True
        self.fields['date_debut'].required = True
        self.fields['periode_prise_debut'].required = True
        self.fields['periode_prise_fin'].required = True

        # date_fin est optionnelle
        self.fields['date_fin'].required = False

    def clean_code(self):
        """Valider l'unicité du code"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()

            # Vérifier l'unicité (sauf pour l'instance en cours de modification)
            qs = ConfigurationConventionnelle.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise ValidationError(
                    f"Le code '{code}' est déjà utilisé par une autre convention"
                )

        return code

    def clean(self):
        """Validations inter-champs"""
        cleaned_data = super().clean()

        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        periode_prise_debut = cleaned_data.get('periode_prise_debut')
        periode_prise_fin = cleaned_data.get('periode_prise_fin')

        # Validation date_fin > date_debut
        if date_fin and date_debut and date_fin <= date_debut:
            self.add_error('date_fin',
                           'La date de fin doit être postérieure à la date de début')

        # Validation période de prise
        if periode_prise_fin and periode_prise_debut:
            if periode_prise_fin <= periode_prise_debut:
                self.add_error('periode_prise_fin',
                               'La date de fin de période doit être postérieure à la date de début')

        return cleaned_data


class JourFerieForm(forms.ModelForm):
    """
    Formulaire pour la gestion des jours fériés
    """

    class Meta:
        model = JourFerie
        fields = ['nom', 'date', 'type_ferie', 'recurrent', 'description', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Jour de l\'an, Fête du travail...',
                'maxlength': 100
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'type_ferie': forms.Select(attrs={
                'class': 'form-control'
            }),
            'recurrent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Informations complémentaires...'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_nom(self):
        """Validation du nom"""
        nom = self.cleaned_data.get('nom')
        if nom:
            nom = nom.strip()
            if len(nom) < 3:
                raise forms.ValidationError("Le nom doit contenir au moins 3 caractères")
        return nom

    def clean_date(self):
        """Validation de la date"""
        date = self.cleaned_data.get('date')
        if date:
            # Vérifier que la date n'est pas trop ancienne (plus de 5 ans)
            annee_min = datetime.now().year - 5
            if date.year < annee_min:
                raise forms.ValidationError(
                    f"La date ne peut pas être antérieure à {annee_min}"
                )

            # Vérifier que la date n'est pas trop dans le futur (plus de 5 ans)
            annee_max = datetime.now().year + 5
            if date.year > annee_max:
                raise forms.ValidationError(
                    f"La date ne peut pas être postérieure à {annee_max}"
                )

            # ✅ AJOUT : Vérifier l'unicité de la date
            queryset = JourFerie.objects.filter(date=date)

            # Exclure l'instance actuelle si on est en mode édition
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                jour_existant = queryset.first()
                raise forms.ValidationError(
                    f"Un jour férié existe déjà pour cette date : '{jour_existant.nom}' le {date.strftime('%d/%m/%Y')}"
                )

        return date

    def clean(self):
        """Validation inter-champs"""
        cleaned_data = super().clean()
        return cleaned_data


class TypeAbsenceForm(forms.ModelForm):
    """
    Formulaire pour la gestion des types d'absence
    """

    class Meta:
        model = TypeAbsence
        fields = [
            'code', 'libelle', 'categorie', 'paye', 'decompte_solde',
            'justificatif_obligatoire', 'couleur', 'ordre', 'actif'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex: CPN, MAL, AUT',
                'maxlength': 3,
                'style': 'text-transform: uppercase;'
            }),
            'libelle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Congés payés, Maladie...'
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-control'
            }),
            'couleur': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
            'paye': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'decompte_solde': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'justificatif_obligatoire': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_code(self):
        """Validation du code"""
        code = self.cleaned_data.get('code')
        if code:
            # ✅ Convertir en majuscules et supprimer les espaces
            code = code.upper().strip()

            # Vérifier la longueur exacte
            if len(code) != 3:
                raise forms.ValidationError('Le code doit contenir exactement 3 caractères')

            # Vérifier que c'est alphanumérique
            if not code.isalnum():
                raise forms.ValidationError('Le code ne doit contenir que des lettres et des chiffres')

            # Vérifier l'unicité (case-insensitive)
            queryset = TypeAbsence.objects.filter(code__iexact=code)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(f'Le code "{code}" existe déjà')

        return code

    def clean_libelle(self):
        """Validation du libellé"""
        libelle = self.cleaned_data.get('libelle')
        if libelle:
            # ✅ Première lettre en majuscule
            libelle = libelle.strip().capitalize()

            if len(libelle) < 3:
                raise forms.ValidationError('Le libellé doit contenir au moins 3 caractères')

        return libelle

    def clean_couleur(self):
        """Validation de la couleur"""
        couleur = self.cleaned_data.get('couleur')
        if couleur:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', couleur):
                raise forms.ValidationError('Format invalide. Utilisez le format #RRGGBB')
        return couleur

    def clean(self):
        cleaned_data = super().clean()
        type_absence = cleaned_data.get('type_absence')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        periode = cleaned_data.get('periode')
        justificatif = cleaned_data.get('justificatif')

        # ✅ DEBUG
        print(f"🔍 VALIDATION FORMULAIRE")
        print(f"   - User employe: {self.user_employe}")
        print(f"   - Date début: {date_debut}")
        print(f"   - Date fin: {date_fin}")

        if not all([type_absence, date_debut, date_fin]):
            return cleaned_data

        # 1. Date de fin >= Date de début
        if date_fin < date_debut:
            raise ValidationError({
                'date_fin': 'La date de fin ne peut pas être antérieure à la date de début.'
            })

        # 2. Demi-journées uniquement pour un seul jour
        if date_debut != date_fin:
            if periode != 'JOURNEE_COMPLETE':
                raise ValidationError({
                    'periode': 'Les demi-journées ne sont autorisées que pour une absence d\'un seul jour'
                })

        # ✅ 3. CRITIQUE : Vérifier les chevauchements
        if self.user_employe:
            print(f"   ✅ Appel de verifier_chevauchements...")
            self.verifier_chevauchements(self.user_employe, date_debut, date_fin)
        else:
            print(f"   ❌ ATTENTION : user_employe est None, validation des chevauchements ignorée !")

        # 4. Justificatif obligatoire
        if type_absence.justificatif_obligatoire:
            if not self.instance.pk and not justificatif:
                raise ValidationError({
                    'justificatif': f'Un justificatif est obligatoire pour "{type_absence.libelle}"'
                })

            if self.instance.pk and not justificatif and not self.instance.justificatif:
                raise ValidationError({
                    'justificatif': f'Un justificatif est obligatoire pour "{type_absence.libelle}"'
                })

        # 5. Vérifier le solde
        if type_absence.decompte_solde and self.user_employe:
            solde_disponible = self.get_solde_disponible(self.user_employe, date_debut)
            jours_demandes = self.calculer_jours_ouvrables_avec_periode(
                date_debut, date_fin, periode
            )

            if solde_disponible <= Decimal('0.00'):
                raise ValidationError({
                    '__all__': f'Vous n\'avez aucun jour de congé disponible. '
                               f'Solde actuel : {solde_disponible} jours.'
                })

            if jours_demandes > solde_disponible:
                raise ValidationError({
                    '__all__': f'Solde insuffisant. Vous demandez {jours_demandes} jours mais '
                               f'vous n\'avez que {solde_disponible} jours disponibles.'
                })

        return cleaned_data

    def verifier_chevauchements(self, employe, date_debut, date_fin):
        """
        Vérifie qu'il n'y a pas de chevauchement avec des absences existantes
        """
        print(f"🔍 VÉRIFICATION CHEVAUCHEMENTS")
        print(f"   - Employé: {employe}")
        print(f"   - Période: {date_debut} → {date_fin}")

        # Chercher les absences qui chevauchent
        query = Absence.objects.filter(
            employe=employe,
            statut__in=['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'VALIDE'],
            date_debut__lte=date_fin,
            date_fin__gte=date_debut
        )

        print(f"   - Absences trouvées avant exclusion: {query.count()}")

        # Exclure l'absence en cours de modification
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
            print(f"   - Absences après exclusion (pk={self.instance.pk}): {query.count()}")

        if query.exists():
            print(f"   ❌ CHEVAUCHEMENT DÉTECTÉ !")

            absences_chevauches = query.order_by('date_debut')
            details = []

            for abs in absences_chevauches[:3]:
                details.append(
                    f"• {abs.type_absence.libelle} : "
                    f"{abs.date_debut.strftime('%d/%m/%Y')} au {abs.date_fin.strftime('%d/%m/%Y')} "
                    f"(Statut: {abs.get_statut_display()})"
                )
                print(f"     - Chevauchement avec: {abs.date_debut} → {abs.date_fin} (ID: {abs.pk})")

            message = "Cette période chevauche une ou plusieurs absences existantes :\n\n" + "\n".join(details)

            if query.count() > 3:
                message += f"\n\n... et {query.count() - 3} autre(s) absence(s)."

            raise ValidationError({
                '__all__': message
            })

        print(f"   ✅ Aucun chevauchement détecté")


class ParametreCalculCongesForm(forms.ModelForm):
    """Formulaire pour les paramètres de calcul des congés"""

    # Champ personnalisé pour l'ancienneté (facilite la saisie)
    anciennete_5_ans = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        max_value=10,
        label="Jours supplémentaires après 5 ans",
        help_text="Nombre de jours de congés supplémentaires accordés après 5 ans d'ancienneté"
    )

    anciennete_10_ans = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        max_value=10,
        label="Jours supplémentaires après 10 ans",
        help_text="Nombre de jours de congés supplémentaires accordés après 10 ans d'ancienneté"
    )

    anciennete_15_ans = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        max_value=10,
        label="Jours supplémentaires après 15 ans",
        help_text="Nombre de jours de congés supplémentaires accordés après 15 ans d'ancienneté"
    )

    anciennete_20_ans = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        max_value=10,
        label="Jours supplémentaires après 20 ans",
        help_text="Nombre de jours de congés supplémentaires accordés après 20 ans d'ancienneté"
    )

    class Meta:
        model = ParametreCalculConges
        fields = [
            'configuration',
            'mois_acquisition_min',
            'plafond_jours_an',
            'report_autorise',
            'jours_report_max',
            'delai_prise_report',
            'prise_compte_temps_partiel',
        ]
        widgets = {
            'configuration': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'mois_acquisition_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 12,
                'placeholder': '1'
            }),
            'plafond_jours_an': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 60,
                'placeholder': '30'
            }),
            'report_autorise': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'jours_report_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 30,
                'placeholder': '15'
            }),
            'delai_prise_report': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 730,
                'placeholder': '365'
            }),
            'prise_compte_temps_partiel': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Charger les valeurs d'ancienneté depuis le JSON
        if self.instance and self.instance.pk:
            jours_supp = self.instance.jours_supp_anciennete or {}
            self.fields['anciennete_5_ans'].initial = jours_supp.get('5', 0)
            self.fields['anciennete_10_ans'].initial = jours_supp.get('10', 0)
            self.fields['anciennete_15_ans'].initial = jours_supp.get('15', 0)
            self.fields['anciennete_20_ans'].initial = jours_supp.get('20', 0)

    def clean(self):
        cleaned_data = super().clean()

        # Validation : Si report autorisé, jours_report_max doit être > 0
        if cleaned_data.get('report_autorise') and not cleaned_data.get('jours_report_max'):
            raise forms.ValidationError(
                "Si le report est autorisé, vous devez indiquer un nombre de jours maximum."
            )

        # Construire le JSON d'ancienneté
        jours_supp_anciennete = {}

        if cleaned_data.get('anciennete_5_ans', 0) > 0:
            jours_supp_anciennete['5'] = cleaned_data['anciennete_5_ans']

        if cleaned_data.get('anciennete_10_ans', 0) > 0:
            jours_supp_anciennete['10'] = cleaned_data['anciennete_10_ans']

        if cleaned_data.get('anciennete_15_ans', 0) > 0:
            jours_supp_anciennete['15'] = cleaned_data['anciennete_15_ans']

        if cleaned_data.get('anciennete_20_ans', 0) > 0:
            jours_supp_anciennete['20'] = cleaned_data['anciennete_20_ans']

        # Stocker dans cleaned_data pour le save
        cleaned_data['jours_supp_anciennete'] = jours_supp_anciennete

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Assigner le JSON d'ancienneté
        instance.jours_supp_anciennete = self.cleaned_data.get('jours_supp_anciennete', {})

        if commit:
            instance.save()

        return instance


class AcquisitionCongesForm(forms.ModelForm):
    """Formulaire pour l'acquisition de congés (principalement lecture/calcul)"""

    class Meta:
        model = AcquisitionConges
        fields = [
            'employe',
            'annee_reference',
            'jours_acquis',
            'jours_pris',
            'jours_report_anterieur',
            'jours_report_nouveau',
        ]
        widgets = {
            'employe': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'annee_reference': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2099,
                'required': True
            }),
            'jours_acquis': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,  # Calculé automatiquement
            }),
            'jours_pris': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,  # Mis à jour par les absences
            }),
            'jours_report_anterieur': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
            }),
            'jours_report_nouveau': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,  # Calculé automatiquement
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer uniquement les employés actifs avec entreprise
        self.fields['employe'].queryset = ZY00.objects.filter(
            etat='actif',
            entreprise__isnull=False
        ).select_related('entreprise').order_by('nom', 'prenoms')

        # Labels personnalisés
        self.fields['jours_acquis'].label = "Jours acquis (calculés)"
        self.fields['jours_pris'].label = "Jours pris (validés)"
        self.fields['jours_report_anterieur'].label = "Report de l'année précédente"
        self.fields['jours_report_nouveau'].label = "Nouveau report"

    def clean(self):
        cleaned_data = super().clean()
        employe = cleaned_data.get('employe')
        annee_reference = cleaned_data.get('annee_reference')

        # Vérifier que l'employé a une convention applicable
        if employe and not employe.convention_applicable:
            raise forms.ValidationError({
                'employe': "Cet employé n'a pas de convention collective applicable. "
                           "Veuillez configurer la convention de l'entreprise ou une convention personnalisée."
            })

        # Vérifier unicité employe/année
        if employe and annee_reference and self.instance.pk is None:
            if AcquisitionConges.objects.filter(
                    employe=employe,
                    annee_reference=annee_reference
            ).exists():
                raise forms.ValidationError({
                    'annee_reference': f"Une acquisition existe déjà pour {employe} en {annee_reference}"
                })

        return cleaned_data


class CalculAcquisitionForm(forms.Form):
    """Formulaire pour calculer/recalculer les acquisitions en masse"""

    annee_reference = forms.IntegerField(
        label="Année de référence",
        min_value=2020,
        max_value=2099,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2025'
        }),
        help_text="Année pour laquelle calculer les acquisitions"
    )

    recalculer_existantes = forms.BooleanField(
        label="Recalculer les acquisitions existantes",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Si coché, recalcule même si une acquisition existe déjà"
    )

    employes = forms.ModelMultipleChoiceField(
        queryset=ZY00.objects.filter(etat='actif', entreprise__isnull=False),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'size': 10
        }),
        help_text="Laissez vide pour calculer pour tous les employés actifs"
    )


class AbsenceForm(forms.ModelForm):
    """Formulaire pour créer/modifier une absence"""

    class Meta:
        model = Absence
        fields = [
            'type_absence',
            'date_debut',
            'date_fin',
            'periode',
            'motif',
            'justificatif',
        ]
        widgets = {
            'type_absence': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'periode': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'motif': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Motif de l\'absence (optionnel)...'
            }),
            'justificatif': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user_employe = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['type_absence'].queryset = TypeAbsence.objects.filter(actif=True)
        self.fields['motif'].required = False

        if not self.instance.pk:
            self.initial['periode'] = 'JOURNEE_COMPLETE'

    def clean(self):
        cleaned_data = super().clean()
        type_absence = cleaned_data.get('type_absence')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        periode = cleaned_data.get('periode')
        justificatif = cleaned_data.get('justificatif')

        if not all([type_absence, date_debut, date_fin]):
            return cleaned_data

        # ✅ 0. FORCER JOURNEE_COMPLETE POUR PLUSIEURS JOURS (AVANT VALIDATION)
        if date_debut != date_fin:
            if periode and periode != 'JOURNEE_COMPLETE':
                # ⚠️ NE PAS lever d'erreur, FORCER LA VALEUR
                cleaned_data['periode'] = 'JOURNEE_COMPLETE'
                periode = 'JOURNEE_COMPLETE'
                print(f"⚠️ Période forcée à JOURNEE_COMPLETE car plusieurs jours")

        # ✅ 1. Date de fin >= Date de début
        if date_fin < date_debut:
            raise ValidationError({
                'date_fin': 'La date de fin ne peut pas être antérieure à la date de début.'
            })

        # ✅ 2. Demi-journées uniquement pour un seul jour (DEVRAIT JAMAIS ARRIVER maintenant)
        if date_debut != date_fin:
            if periode != 'JOURNEE_COMPLETE':
                raise ValidationError({
                    'periode': 'Les demi-journées ne sont autorisées que pour une absence d\'un seul jour'
                })

        # ✅ 3. CRITIQUE : Vérifier les chevauchements
        if self.user_employe:
            print(f"   ✅ Appel de verifier_chevauchements...")
            self.verifier_chevauchements(self.user_employe, date_debut, date_fin)
        else:
            print(f"   ❌ ATTENTION : user_employe est None, validation des chevauchements ignorée !")

        # 4. Justificatif obligatoire
        if type_absence.justificatif_obligatoire:
            if not self.instance.pk and not justificatif:
                raise ValidationError({
                    'justificatif': f'Un justificatif est obligatoire pour "{type_absence.libelle}"'
                })

            if self.instance.pk and not justificatif and not self.instance.justificatif:
                raise ValidationError({
                    'justificatif': f'Un justificatif est obligatoire pour "{type_absence.libelle}"'
                })

        # 5. Vérifier le solde
        if type_absence.decompte_solde and self.user_employe:
            solde_disponible = self.get_solde_disponible(self.user_employe, date_debut)
            jours_demandes = self.calculer_jours_ouvrables_avec_periode(
                date_debut, date_fin, periode
            )

            if solde_disponible <= Decimal('0.00'):
                raise ValidationError({
                    '__all__': f'Vous n\'avez aucun jour de congé disponible. '
                               f'Solde actuel : {solde_disponible} jours.'
                })

            if jours_demandes > solde_disponible:
                raise ValidationError({
                    '__all__': f'Solde insuffisant. Vous demandez {jours_demandes} jours mais '
                               f'vous n\'avez que {solde_disponible} jours disponibles.'
                })

        return cleaned_data

    def verifier_chevauchements(self, employe, date_debut, date_fin):
        """
        Vérifie qu'il n'y a pas de chevauchement avec des absences existantes
        ✅ VALIDATION RENFORCÉE
        """
        # Chercher les absences qui chevauchent
        query = Absence.objects.filter(
            employe=employe,
            statut__in=['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'VALIDE']
        ).filter(
            # ✅ Condition de chevauchement :
            # (date_debut_nouvelle <= date_fin_existante) ET (date_fin_nouvelle >= date_debut_existante)
            models.Q(date_debut__lte=date_fin) & models.Q(date_fin__gte=date_debut)
        )

        # Exclure l'absence en cours de modification
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            absences_chevauches = query.order_by('date_debut')
            details = []

            for abs in absences_chevauches[:3]:  # Afficher max 3 exemples
                details.append(
                    f"• {abs.type_absence.libelle} : "
                    f"{abs.date_debut.strftime('%d/%m/%Y')} au {abs.date_fin.strftime('%d/%m/%Y')} "
                    f"({abs.get_statut_display()})"
                )

            message = f"Cette période chevauche une ou plusieurs absences existantes :\n\n" + "\n".join(details)

            if query.count() > 3:
                message += f"\n... et {query.count() - 3} autre(s) absence(s)."

            raise ValidationError({
                '__all__': message
            })

    def get_solde_disponible(self, employe, date_absence):
        """Calcule le solde disponible selon le système N+1"""
        from .models import AcquisitionConges

        annee_absence = date_absence.year
        annee_acquisition = annee_absence - 1

        try:
            acquisition = AcquisitionConges.objects.get(
                employe=employe,
                annee_reference=annee_acquisition
            )
            return acquisition.jours_restants
        except AcquisitionConges.DoesNotExist:
            return Decimal('0.00')

    def calculer_jours_ouvrables_avec_periode(self, date_debut, date_fin, periode):
        """Calcule le nombre de jours ouvrables avec la période"""
        jours = Decimal('0.00')
        current = date_debut

        while current <= date_fin:
            if current.weekday() < 5:  # Lundi à Vendredi

                # Même jour : Tenir compte de la période
                if date_debut == date_fin:
                    if periode == 'JOURNEE_COMPLETE':
                        jours += Decimal('1.00')
                    else:
                        jours += Decimal('0.50')  # MATIN ou APRES_MIDI

                # Plusieurs jours : Toujours journée complète
                else:
                    jours += Decimal('1.00')

            current += timezone.timedelta(days=1)

        return jours


class AbsenceRechercheForm(forms.Form):
    """Formulaire de recherche d'absences"""

    type_absence = forms.ModelChoiceField(
        queryset=TypeAbsence.objects.filter(actif=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Type d'absence"
    )

    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Absence.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Statut"
    )

    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Date de début"
    )

    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Date de fin"
    )


class ValidationAbsenceForm(forms.Form):
    """
    Formulaire de validation d'absence (pour l'interface utilisateur)
    Ce formulaire ne correspond PAS directement au modèle ValidationAbsence,
    mais sert à collecter la décision du validateur
    """

    DECISION_CHOICES = [
        ('APPROUVE', 'Approuver'),
        ('REJETE', 'Rejeter'),
        ('RETOURNE', 'Retourner pour modification'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Décision'
    )

    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire (optionnel)...'
        }),
        label='Commentaire'
    )


class ValidationAbsenceModelForm(forms.ModelForm):
    """
    Formulaire basé sur le modèle ValidationAbsence
    (Pour l'admin Django ou gestion avancée)
    """

    class Meta:
        model = ValidationAbsence
        fields = [
            'absence',
            'etape',
            'ordre',
            'validateur',
            'decision',
            'commentaire',
        ]
        widgets = {
            'absence': forms.Select(attrs={'class': 'form-control'}),
            'etape': forms.Select(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'validateur': forms.Select(attrs={'class': 'form-control'}),
            'decision': forms.Select(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }