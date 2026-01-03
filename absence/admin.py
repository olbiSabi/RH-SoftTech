# absence/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ConfigurationConventionnelle,
    TypeAbsence,
    JourFerie,
    ParametreCalculConges,
    AcquisitionConges,
    Absence,
    NotificationAbsence,
    ValidationAbsence
)


# ========================================
# 1. ConfigurationConventionnelle
# ========================================

@admin.register(ConfigurationConventionnelle)
class ConfigurationConventionnelleAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'nom', 'type_convention_badge', 'annee_reference',
        'periode_acquisition', 'jours_acquis_par_mois', 'actif_badge', 'en_vigueur_badge'
    ]
    list_filter = ['type_convention', 'actif', 'annee_reference', 'methode_calcul']
    search_fields = ['code', 'nom']
    readonly_fields = ['est_en_vigueur', 'est_clôturée']

    fieldsets = (
        ('Informations générales', {
            'fields': ('type_convention', 'nom', 'code', 'annee_reference')
        }),
        ('Période de validité', {
            'fields': ('date_debut', 'date_fin', 'actif', 'est_en_vigueur', 'est_clôturée')
        }),
        ('Période d\'acquisition', {
            'fields': (
                'periode_prise_debut',
                'periode_prise_fin',
                'periode_prise_fin_annee_suivante'
            ),
            'description': 'Définit la période pendant laquelle les congés sont acquis (ex: 01/05/N → 30/04/N+1)'
        }),
        ('Paramètres de calcul', {
            'fields': (
                'jours_acquis_par_mois',
                'duree_conges_principale',
                'methode_calcul'
            )
        }),
    )

    def type_convention_badge(self, obj):
        if obj.type_convention == 'ENTREPRISE':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">ENTREPRISE</span>'
            )
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">PERSONNALISÉE</span>'
        )

    type_convention_badge.short_description = 'Type'

    def periode_acquisition(self, obj):
        debut, fin = obj.get_periode_acquisition(obj.annee_reference)
        annee_label = 'N+1' if obj.periode_prise_fin_annee_suivante else 'N'
        return format_html(
            '{} → {} <span style="color: #888; font-size: 11px;">({})</span>',
            debut.strftime('%d/%m'),
            fin.strftime('%d/%m'),
            annee_label
        )

    periode_acquisition.short_description = 'Période d\'acquisition'

    def actif_badge(self, obj):
        if obj.actif:
            return format_html(
                '<span style="color: #28a745;">✓ Actif</span>'
            )
        return format_html('<span style="color: #dc3545;">✗ Inactif</span>')

    actif_badge.short_description = 'Statut'

    def en_vigueur_badge(self, obj):
        if obj.est_en_vigueur:
            return format_html(
                '<span style="color: #28a745;">● En vigueur</span>'
            )
        return format_html('<span style="color: #888;">○ Non en vigueur</span>')

    en_vigueur_badge.short_description = 'En vigueur'


# ========================================
# 2. TypeAbsence
# ========================================

@admin.register(TypeAbsence)
class TypeAbsenceAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'libelle', 'categorie_badge', 'paye_badge',
        'decompte_solde_badge', 'justificatif_badge', 'actif_badge', 'couleur_preview'
    ]
    list_filter = ['categorie', 'paye', 'decompte_solde', 'actif', 'justificatif_obligatoire']
    search_fields = ['code', 'libelle']
    ordering = ['ordre', 'libelle']

    fieldsets = (
        ('Identification', {
            'fields': ('code', 'libelle', 'categorie', 'ordre')
        }),
        ('Paramètres', {
            'fields': (
                'paye',
                'decompte_solde',
                'justificatif_obligatoire',
                'actif'
            )
        }),
        ('Apparence', {
            'fields': ('couleur',),
            'description': 'Couleur d\'affichage au format hexadécimal (#RRGGBB)'
        }),
    )

    def categorie_badge(self, obj):
        colors = {
            'CONGES_PAYES': '#3498db',
            'MALADIE': '#e74c3c',
            'AUTORISATION': '#f39c12',
            'SANS_SOLDE': '#95a5a6',
            'MATERNITE': '#9b59b6',
            'FORMATION': '#1abc9c',
            'MISSION': '#34495e',
        }
        color = colors.get(obj.categorie, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_categorie_display()
        )

    categorie_badge.short_description = 'Catégorie'

    def paye_badge(self, obj):
        if obj.paye:
            return format_html('<span style="color: #28a745;">✓ Payé</span>')
        return format_html('<span style="color: #dc3545;">✗ Non payé</span>')

    paye_badge.short_description = 'Payé'

    def decompte_solde_badge(self, obj):
        if obj.decompte_solde:
            return format_html('<span style="color: #f39c12;">● Décompté</span>')
        return format_html('<span style="color: #888;">○ Non décompté</span>')

    decompte_solde_badge.short_description = 'Solde'

    def justificatif_badge(self, obj):
        if obj.justificatif_obligatoire:
            return format_html('<span style="color: #dc3545;">✓ Obligatoire</span>')
        return format_html('<span style="color: #888;">○ Facultatif</span>')

    justificatif_badge.short_description = 'Justificatif'

    def actif_badge(self, obj):
        if obj.actif:
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')

    actif_badge.short_description = 'Actif'

    def couleur_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; '
            'border: 1px solid #ddd; border-radius: 3px;"></div>',
            obj.couleur
        )

    couleur_preview.short_description = 'Couleur'


# ========================================
# 3. JourFerie
# ========================================

@admin.register(JourFerie)
class JourFerieAdmin(admin.ModelAdmin):
    list_display = [
        'nom', 'date', 'jour_semaine', 'type_badge',
        'recurrent_badge', 'actif_badge'
    ]
    # ✅ CORRECTION : Retirer 'date__year' et utiliser uniquement les champs directs
    list_filter = ['type_ferie', 'recurrent', 'actif']  # ✅ Supprimé 'date__year'
    search_fields = ['nom', 'description']
    date_hierarchy = 'date'  # ✅ Ceci permet déjà de filtrer par année
    readonly_fields = ['annee', 'mois_nom', 'jour_semaine', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'date', 'type_ferie', 'recurrent', 'actif')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Informations calculées', {
            'fields': ('annee', 'mois_nom', 'jour_semaine'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def type_badge(self, obj):
        if obj.type_ferie == 'LEGAL':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">LÉGAL</span>'
            )
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">ENTREPRISE</span>'
        )

    type_badge.short_description = 'Type'

    def recurrent_badge(self, obj):
        if obj.recurrent:
            return format_html('<span style="color: #17a2b8;">🔁 Oui</span>')
        return format_html('<span style="color: #888;">✗ Non</span>')

    recurrent_badge.short_description = 'Récurrent'

    def actif_badge(self, obj):
        if obj.actif:
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')

    actif_badge.short_description = 'Actif'


# ========================================
# 4. ParametreCalculConges
# ========================================

@admin.register(ParametreCalculConges)
class ParametreCalculCongesAdmin(admin.ModelAdmin):
    list_display = [
        'configuration', 'plafond_jours_an', 'report_badge',
        'jours_report_max', 'prise_compte_temps_partiel_badge'
    ]
    list_filter = ['report_autorise', 'prise_compte_temps_partiel']
    search_fields = ['configuration__nom', 'configuration__code']

    fieldsets = (
        ('Convention associée', {
            'fields': ('configuration',)
        }),
        ('Acquisition', {
            'fields': ('mois_acquisition_min', 'plafond_jours_an')
        }),
        ('Report', {
            'fields': ('report_autorise', 'jours_report_max', 'delai_prise_report')
        }),
        ('Ancienneté', {
            'fields': ('jours_supp_anciennete',),
            'description': 'Format JSON: {"5": 1, "10": 2} = +1 jour après 5 ans, +2 après 10 ans'
        }),
        ('Temps partiel', {
            'fields': ('prise_compte_temps_partiel',)
        }),
    )

    def report_badge(self, obj):
        if obj.report_autorise:
            return format_html('<span style="color: #28a745;">✓ Autorisé</span>')
        return format_html('<span style="color: #dc3545;">✗ Non autorisé</span>')

    report_badge.short_description = 'Report'

    def prise_compte_temps_partiel_badge(self, obj):
        if obj.prise_compte_temps_partiel:
            return format_html('<span style="color: #17a2b8;">✓ Oui</span>')
        return format_html('<span style="color: #888;">✗ Non</span>')

    prise_compte_temps_partiel_badge.short_description = 'Temps partiel'


# ========================================
# 5. AcquisitionConges
# ========================================

@admin.register(AcquisitionConges)
class AcquisitionCongesAdmin(admin.ModelAdmin):
    list_display = [
        'employe', 'annee_reference', 'jours_acquis_display',
        'jours_pris_display', 'jours_restants_display',
        'jours_report_anterieur_display', 'date_maj'
    ]
    list_filter = ['annee_reference']
    search_fields = ['employe__nom', 'employe__prenoms', 'employe__matricule']
    readonly_fields = ['date_calcul', 'date_maj']
    date_hierarchy = 'date_maj'

    fieldsets = (
        ('Employé', {
            'fields': ('employe', 'annee_reference')
        }),
        ('Solde', {
            'fields': (
                'jours_acquis',
                'jours_pris',
                'jours_restants',
                'jours_report_anterieur',
                'jours_report_nouveau'
            )
        }),
        ('Dates', {
            'fields': ('date_calcul', 'date_maj'),
            'classes': ('collapse',)
        }),
    )

    def jours_acquis_display(self, obj):
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">{} j</span>',
            obj.jours_acquis
        )

    jours_acquis_display.short_description = 'Acquis'

    def jours_pris_display(self, obj):
        return format_html(
            '<span style="color: #f39c12; font-weight: bold;">{} j</span>',
            obj.jours_pris
        )

    jours_pris_display.short_description = 'Pris'

    def jours_restants_display(self, obj):
        color = '#28a745' if obj.jours_restants > 0 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} j</span>',
            color,
            obj.jours_restants
        )

    jours_restants_display.short_description = 'Restants'

    def jours_report_anterieur_display(self, obj):
        if obj.jours_report_anterieur > 0:
            return format_html(
                '<span style="color: #17a2b8;">{} j</span>',
                obj.jours_report_anterieur
            )
        return '-'

    jours_report_anterieur_display.short_description = 'Report ant.'


# ========================================
# 6. Absence
# ========================================

class ValidationAbsenceInline(admin.TabularInline):
    model = ValidationAbsence
    extra = 0
    readonly_fields = ['etape', 'ordre', 'validateur', 'decision', 'date_validation']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = [
        'employe', 'type_absence', 'periode_absence',
        'periode_badge', 'jours_ouvrables_display',
        'statut_badge', 'created_at'
    ]
    list_filter = ['statut', 'type_absence', 'periode', 'date_debut']
    search_fields = ['employe__nom', 'employe__prenoms', 'employe__matricule', 'motif']
    readonly_fields = [
        'jours_ouvrables', 'jours_calendaires',
        'created_at', 'updated_at', 'created_by',
        'annee_acquisition_utilisee'
    ]
    date_hierarchy = 'date_debut'
    inlines = [ValidationAbsenceInline]

    fieldsets = (
        ('Employé et Type', {
            'fields': ('employe', 'type_absence', 'created_by')
        }),
        ('Période', {
            'fields': (
                'date_debut',
                'date_fin',
                'periode',
                'jours_ouvrables',
                'jours_calendaires',
                'annee_acquisition_utilisee'
            )
        }),
        ('Validation Manager', {
            'fields': (
                'manager_validateur',
                'date_validation_manager',
                'commentaire_manager'
            ),
            'classes': ('collapse',)
        }),
        ('Validation RH', {
            'fields': (
                'rh_validateur',
                'date_validation_rh',
                'commentaire_rh'
            ),
            'classes': ('collapse',)
        }),
        ('Justification', {
            'fields': ('motif', 'justificatif')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def periode_absence(self, obj):
        return f"{obj.date_debut.strftime('%d/%m/%Y')} → {obj.date_fin.strftime('%d/%m/%Y')}"

    periode_absence.short_description = 'Période'

    def periode_badge(self, obj):
        colors = {
            'JOURNEE_COMPLETE': '#3498db',
            'MATIN': '#f39c12',
            'APRES_MIDI': '#9b59b6'
        }
        color = colors.get(obj.periode, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_periode_display()
        )

    periode_badge.short_description = 'Période'

    def jours_ouvrables_display(self, obj):
        return format_html('<strong>{} j</strong>', obj.jours_ouvrables)

    jours_ouvrables_display.short_description = 'Jours'

    def statut_badge(self, obj):
        colors = {
            'BROUILLON': '#95a5a6',
            'EN_ATTENTE_MANAGER': '#f39c12',
            'EN_ATTENTE_RH': '#3498db',
            'VALIDE': '#28a745',
            'REJETE': '#dc3545',
            'ANNULE': '#6c757d',
        }
        color = colors.get(obj.statut, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_statut_display()
        )

    statut_badge.short_description = 'Statut'


# ========================================
# 7. NotificationAbsence
# ========================================

@admin.register(NotificationAbsence)
class NotificationAbsenceAdmin(admin.ModelAdmin):
    list_display = [
        'destinataire', 'type_notification_badge', 'contexte_badge',
        'absence_link', 'lue_badge', 'date_creation'
    ]
    list_filter = ['type_notification', 'contexte', 'lue', 'date_creation']
    search_fields = ['destinataire__nom', 'destinataire__prenoms', 'message']
    readonly_fields = ['date_creation', 'date_lecture']
    date_hierarchy = 'date_creation'

    fieldsets = (
        ('Destinataire', {
            'fields': ('destinataire', 'contexte')
        }),
        ('Notification', {
            'fields': ('absence', 'type_notification', 'message')
        }),
        ('Lecture', {
            'fields': ('lue', 'date_creation', 'date_lecture')
        }),
    )

    def type_notification_badge(self, obj):
        return format_html(
            '<span style="font-size: 11px;">{}</span>',
            obj.get_type_notification_display()
        )

    type_notification_badge.short_description = 'Type'

    def contexte_badge(self, obj):
        colors = {
            'EMPLOYE': '#3498db',
            'MANAGER': '#f39c12',
            'RH': '#9b59b6'
        }
        color = colors.get(obj.contexte, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_contexte_display()
        )

    contexte_badge.short_description = 'Contexte'

    def absence_link(self, obj):
        if obj.absence:
            return format_html(
                '{} - {}',
                obj.absence.employe,
                obj.absence.type_absence.code
            )
        return '-'

    absence_link.short_description = 'Absence'

    def lue_badge(self, obj):
        if obj.lue:
            return format_html('<span style="color: #28a745;">✓ Lue</span>')
        return format_html('<span style="color: #dc3545; font-weight: bold;">● Non lue</span>')

    lue_badge.short_description = 'État'


# ========================================
# 8. ValidationAbsence
# ========================================

@admin.register(ValidationAbsence)
class ValidationAbsenceAdmin(admin.ModelAdmin):
    list_display = [
        'absence', 'etape_badge', 'ordre', 'validateur',
        'decision_badge', 'date_validation'
    ]
    list_filter = ['etape', 'decision', 'date_validation']
    search_fields = ['absence__employe__nom', 'validateur__nom', 'commentaire']
    readonly_fields = ['date_demande', 'date_validation']
    date_hierarchy = 'date_validation'

    fieldsets = (
        ('Absence', {
            'fields': ('absence', 'etape', 'ordre')
        }),
        ('Validation', {
            'fields': ('validateur', 'decision', 'commentaire')
        }),
        ('Dates', {
            'fields': ('date_demande', 'date_validation')
        }),
    )

    def etape_badge(self, obj):
        colors = {
            'MANAGER': '#f39c12',
            'RH': '#9b59b6'
        }
        color = colors.get(obj.etape, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_etape_display()
        )

    etape_badge.short_description = 'Étape'

    def decision_badge(self, obj):
        colors = {
            'EN_ATTENTE': '#95a5a6',
            'APPROUVE': '#28a745',
            'REJETE': '#dc3545',
            'RETOURNE': '#f39c12',
        }
        color = colors.get(obj.decision, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_decision_display()
        )

    decision_badge.short_description = 'Décision'