# entreprise/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Entreprise


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = [
        'logo_preview',
        'code',
        'nom',
        'ville',
        'effectif_badge',
        'convention_badge',
        'actif_badge'
    ]

    list_filter = ['actif', 'pays', 'ville']

    search_fields = ['nom', 'code', 'raison_sociale', 'sigle', 'rccm', 'numero_impot']

    readonly_fields = [
        'uuid',
        'effectif_total',
        'employes_actifs_display',
        'convention_en_vigueur',
        'logo_preview_large'
    ]

    fieldsets = (
        ('Identification', {
            'fields': (
                'uuid',
                'code',
                'nom',
                'raison_sociale',
                'sigle'
            )
        }),

        ('Adresse et Contact', {
            'fields': (
                'adresse',
                'ville',
                'pays',
                'telephone',
                'email',
                'site_web'
            )
        }),

        ('Identifiants Légaux', {
            'fields': (
                'rccm',
                'numero_impot',
                'numero_cnss'
            ),
            'classes': ('collapse',)
        }),

        ('Convention Collective', {
            'fields': (
                'configuration_conventionnelle',
                'convention_en_vigueur',
                'date_application_convention'
            ),
            'description': 'Configuration de la convention collective applicable à l\'entreprise'
        }),

        ('Effectif', {
            'fields': (
                'effectif_total',
                'employes_actifs_display'
            ),
            'classes': ('collapse',)
        }),

        ('Logo', {
            'fields': (
                'logo',
                'logo_preview_large'
            )
        }),

        ('Informations Complémentaires', {
            'fields': (
                'date_creation',
                'description',
                'actif'
            ),
            'classes': ('collapse',)
        }),
    )

    # ========================================
    # MÉTHODES D'AFFICHAGE PERSONNALISÉES
    # ========================================

    def logo_preview(self, obj):
        """Aperçu du logo dans la liste"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; '
                'object-fit: contain; border-radius: 4px; border: 1px solid #ddd;" />',
                obj.logo.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; background-color: #f0f0f0; '
            'border-radius: 4px; display: flex; align-items: center; '
            'justify-content: center; color: #999; font-size: 20px;">🏢</div>'
        )

    logo_preview.short_description = 'Logo'

    def logo_preview_large(self, obj):
        """Aperçu du logo en grand dans le formulaire"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; '
                'object-fit: contain; border: 1px solid #ddd; border-radius: 8px;" />',
                obj.logo.url
            )
        return format_html(
            '<div style="width: 200px; height: 200px; background-color: #f0f0f0; '
            'border-radius: 8px; display: flex; align-items: center; '
            'justify-content: center; color: #999; font-size: 48px;">🏢</div>'
        )

    logo_preview_large.short_description = 'Aperçu du logo'

    def effectif_badge(self, obj):
        """Badge d'effectif avec couleur selon le nombre"""
        effectif = obj.effectif_total

        if effectif == 0:
            color = '#dc3545'  # Rouge
        elif effectif < 10:
            color = '#f39c12'  # Orange
        elif effectif < 50:
            color = '#3498db'  # Bleu
        else:
            color = '#28a745'  # Vert

        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 12px; font-weight: bold; font-size: 12px;">{} employé{}</span>',
            color,
            effectif,
            's' if effectif > 1 else ''
        )

    effectif_badge.short_description = 'Effectif'

    def convention_badge(self, obj):
        """Badge de convention avec lien"""
        if obj.configuration_conventionnelle:
            conv = obj.configuration_conventionnelle

            # Couleur selon le type
            if conv.type_convention == 'ENTREPRISE':
                bg_color = '#28a745'
                icon = '🏢'
            else:
                bg_color = '#17a2b8'
                icon = '👤'

            # Badge avec statut
            if conv.actif:
                status_icon = '✓'
                status_color = bg_color
            else:
                status_icon = '✗'
                status_color = '#dc3545'

            return format_html(
                '<div style="display: inline-block;">'
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; margin-right: 4px;">'
                '{} {}</span>'
                '<span style="color: {}; font-size: 14px;">{}</span>'
                '</div>',
                bg_color,
                icon,
                conv.code,
                status_color,
                status_icon
            )

        return format_html(
            '<span style="color: #dc3545; font-style: italic;">Aucune convention</span>'
        )

    convention_badge.short_description = 'Convention'

    def actif_badge(self, obj):
        """Badge de statut actif/inactif"""
        if obj.actif:
            return format_html(
                '<span style="color: #28a745; font-size: 16px;" title="Entreprise active">●</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-size: 16px;" title="Entreprise inactive">●</span>'
        )

    actif_badge.short_description = 'Statut'

    def employes_actifs_display(self, obj):
        """Liste des employés actifs avec liens"""
        employes = obj.employes_actifs[:10]  # Limiter à 10 pour la performance
        total = obj.effectif_total

        if not employes:
            return format_html('<em style="color: #999;">Aucun employé actif</em>')

        html_parts = []
        for emp in employes:
            html_parts.append(
                f'<div style="padding: 4px 0; border-bottom: 1px solid #f0f0f0;">'
                f'<strong>{emp.matricule}</strong> - {emp.nom} {emp.prenoms}'
                f'</div>'
            )

        result = ''.join(html_parts)

        if total > 10:
            result += format_html(
                '<div style="padding: 8px 0; color: #666; font-style: italic;">'
                '... et {} autre{} employé{}</div>',
                total - 10,
                's' if total - 10 > 1 else '',
                's' if total - 10 > 1 else ''
            )

        return format_html(
            '<div style="max-height: 300px; overflow-y: auto;">{}</div>',
            mark_safe(result)
        )

    employes_actifs_display.short_description = 'Employés actifs'

    # ========================================
    # ACTIONS PERSONNALISÉES
    # ========================================

    actions = ['activer_entreprises', 'desactiver_entreprises']

    def activer_entreprises(self, request, queryset):
        """Action pour activer plusieurs entreprises"""
        updated = queryset.update(actif=True)
        self.message_user(
            request,
            f'{updated} entreprise{"s" if updated > 1 else ""} activée{"s" if updated > 1 else ""}.'
        )

    activer_entreprises.short_description = "Activer les entreprises sélectionnées"

    def desactiver_entreprises(self, request, queryset):
        """Action pour désactiver plusieurs entreprises"""
        updated = queryset.update(actif=False)
        self.message_user(
            request,
            f'{updated} entreprise{"s" if updated > 1 else ""} désactivée{"s" if updated > 1 else ""}.'
        )

    desactiver_entreprises.short_description = "Désactiver les entreprises sélectionnées"

    # ========================================
    # MÉTHODES DE CONFIGURATION
    # ========================================

    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related uniquement"""
        qs = super().get_queryset(request)
        # ✅ CORRECTION : Retirer prefetch_related('employes_actifs')
        # car employes_actifs est une property, pas une relation
        return qs.select_related('configuration_conventionnelle')