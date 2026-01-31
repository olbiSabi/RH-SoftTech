# audit/admin.py
"""
Configuration Django Admin pour le module Conformité & Audit.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AURC, AUAL, AURA


@admin.register(AURC)
class AURCAdmin(admin.ModelAdmin):
    """Admin pour les Règles de conformité."""

    list_display = [
        'CODE', 'LIBELLE', 'TYPE_REGLE', 'severite_badge',
        'FREQUENCE_VERIFICATION', 'JOURS_AVANT_EXPIRATION',
        'notifications_display', 'statut_display', 'alertes_count'
    ]
    list_filter = [
        'TYPE_REGLE', 'SEVERITE', 'STATUT',
        'FREQUENCE_VERIFICATION', 'NOTIFIER_RH'
    ]
    search_fields = ['CODE', 'LIBELLE', 'DESCRIPTION']
    readonly_fields = ['CODE', 'uuid', 'CREATED_AT', 'UPDATED_AT']
    ordering = ['TYPE_REGLE', 'CODE']

    fieldsets = (
        ('Identification', {
            'fields': ('CODE', 'uuid', 'LIBELLE', 'DESCRIPTION')
        }),
        ('Configuration', {
            'fields': ('TYPE_REGLE', 'SEVERITE', 'FREQUENCE_VERIFICATION', 'JOURS_AVANT_EXPIRATION')
        }),
        ('Paramètres avancés', {
            'fields': ('PARAMETRES',),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('NOTIFIER_EMPLOYE', 'NOTIFIER_MANAGER', 'NOTIFIER_RH', 'EMAILS_SUPPLEMENTAIRES')
        }),
        ('Statut', {
            'fields': ('STATUT',)
        }),
        ('Métadonnées', {
            'fields': ('CREATED_AT', 'UPDATED_AT'),
            'classes': ('collapse',)
        }),
    )

    def severite_badge(self, obj):
        """Affiche la sévérité avec un badge coloré."""
        colors = {
            'INFO': '#17a2b8',
            'WARNING': '#ffc107',
            'CRITICAL': '#dc3545',
        }
        color = colors.get(obj.SEVERITE, '#6c757d')
        text_color = '#212529' if obj.SEVERITE == 'WARNING' else 'white'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 500;">{}</span>',
            color, text_color, obj.get_SEVERITE_display()
        )
    severite_badge.short_description = 'Sévérité'
    severite_badge.admin_order_field = 'SEVERITE'

    def statut_display(self, obj):
        """Affiche le statut avec une icône."""
        if obj.STATUT:
            return format_html(
                '<span style="color: #28a745;">✓ Actif</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">✗ Inactif</span>'
        )
    statut_display.short_description = 'Statut'
    statut_display.admin_order_field = 'STATUT'

    def notifications_display(self, obj):
        """Affiche les destinataires des notifications."""
        notifs = []
        if obj.NOTIFIER_EMPLOYE:
            notifs.append('👤')
        if obj.NOTIFIER_MANAGER:
            notifs.append('👔')
        if obj.NOTIFIER_RH:
            notifs.append('👥')
        return ' '.join(notifs) if notifs else '-'
    notifications_display.short_description = 'Notif.'

    def alertes_count(self, obj):
        """Affiche le nombre d'alertes liées."""
        count = obj.alertes.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #6c757d; color: white; '
                'padding: 2px 8px; border-radius: 10px;">{}</span>',
                count
            )
        return '-'
    alertes_count.short_description = 'Alertes'


@admin.register(AUAL)
class AUALAdmin(admin.ModelAdmin):
    """Admin pour les Alertes de conformité."""

    list_display = [
        'REFERENCE', 'TITRE', 'TYPE_ALERTE', 'priorite_badge',
        'statut_badge', 'employe_link', 'DATE_DETECTION',
        'DATE_ECHEANCE', 'retard_display'
    ]
    list_filter = [
        'STATUT', 'PRIORITE', 'TYPE_ALERTE',
        'NOTIFICATION_ENVOYEE', 'DATE_DETECTION'
    ]
    search_fields = [
        'REFERENCE', 'TITRE', 'DESCRIPTION',
        'EMPLOYE__NOM', 'EMPLOYE__PRENOM', 'EMPLOYE__MATRICULE'
    ]
    readonly_fields = [
        'REFERENCE', 'uuid', 'DATE_DETECTION',
        'CREATED_AT', 'UPDATED_AT', 'est_en_retard_display', 'jours_restants_display'
    ]
    raw_id_fields = ['EMPLOYE', 'ASSIGNE_A', 'RESOLU_PAR', 'REGLE']
    date_hierarchy = 'DATE_DETECTION'
    ordering = ['-DATE_DETECTION']

    fieldsets = (
        ('Identification', {
            'fields': ('REFERENCE', 'uuid', 'REGLE')
        }),
        ('Détails de l\'alerte', {
            'fields': ('TYPE_ALERTE', 'TITRE', 'DESCRIPTION', 'PRIORITE', 'STATUT')
        }),
        ('Entité concernée', {
            'fields': ('EMPLOYE', 'TABLE_REFERENCE', 'RECORD_ID')
        }),
        ('Dates', {
            'fields': ('DATE_DETECTION', 'DATE_ECHEANCE', 'DATE_RESOLUTION',
                      'est_en_retard_display', 'jours_restants_display')
        }),
        ('Traitement', {
            'fields': ('ASSIGNE_A', 'RESOLU_PAR', 'COMMENTAIRE_RESOLUTION')
        }),
        ('Notifications', {
            'fields': ('NOTIFICATION_ENVOYEE', 'DATE_NOTIFICATION'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('CREATED_AT', 'UPDATED_AT'),
            'classes': ('collapse',)
        }),
    )

    actions = ['marquer_resolu', 'marquer_en_cours', 'marquer_ignore']

    def priorite_badge(self, obj):
        """Affiche la priorité avec un badge coloré."""
        colors = {
            'BASSE': '#28a745',
            'MOYENNE': '#17a2b8',
            'HAUTE': '#ffc107',
            'CRITIQUE': '#dc3545',
        }
        color = colors.get(obj.PRIORITE, '#6c757d')
        text_color = '#212529' if obj.PRIORITE == 'HAUTE' else 'white'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 500;">{}</span>',
            color, text_color, obj.get_PRIORITE_display()
        )
    priorite_badge.short_description = 'Priorité'
    priorite_badge.admin_order_field = 'PRIORITE'

    def statut_badge(self, obj):
        """Affiche le statut avec un badge coloré."""
        colors = {
            'NOUVEAU': '#007bff',
            'EN_COURS': '#ffc107',
            'RESOLU': '#28a745',
            'IGNORE': '#6c757d',
            'EXPIRE': '#dc3545',
        }
        color = colors.get(obj.STATUT, '#6c757d')
        text_color = '#212529' if obj.STATUT == 'EN_COURS' else 'white'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 500;">{}</span>',
            color, text_color, obj.get_STATUT_display()
        )
    statut_badge.short_description = 'Statut'
    statut_badge.admin_order_field = 'STATUT'

    def employe_link(self, obj):
        """Affiche un lien vers l'employé."""
        if obj.EMPLOYE:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:employee_zy00_change', args=[obj.EMPLOYE.pk]),
                obj.EMPLOYE.nom_complet
            )
        return '-'
    employe_link.short_description = 'Employé'

    def retard_display(self, obj):
        """Affiche si l'alerte est en retard."""
        if obj.est_en_retard:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ En retard</span>'
            )
        return ''
    retard_display.short_description = 'Retard'

    def est_en_retard_display(self, obj):
        """Affiche le statut de retard."""
        return 'Oui' if obj.est_en_retard else 'Non'
    est_en_retard_display.short_description = 'En retard'

    def jours_restants_display(self, obj):
        """Affiche les jours restants."""
        jours = obj.jours_restants
        if jours is None:
            return '-'
        if jours < 0:
            return format_html(
                '<span style="color: #dc3545;">{} jours de retard</span>',
                abs(jours)
            )
        elif jours == 0:
            return format_html(
                '<span style="color: #ffc107;">Aujourd\'hui</span>'
            )
        else:
            return f'{jours} jours'
    jours_restants_display.short_description = 'Jours restants'

    @admin.action(description='Marquer comme résolu')
    def marquer_resolu(self, request, queryset):
        count = queryset.update(
            STATUT='RESOLU',
            DATE_RESOLUTION=timezone.now()
        )
        self.message_user(request, f'{count} alerte(s) marquée(s) comme résolue(s).')

    @admin.action(description='Marquer comme en cours')
    def marquer_en_cours(self, request, queryset):
        count = queryset.update(STATUT='EN_COURS')
        self.message_user(request, f'{count} alerte(s) marquée(s) comme en cours.')

    @admin.action(description='Ignorer')
    def marquer_ignore(self, request, queryset):
        count = queryset.update(STATUT='IGNORE')
        self.message_user(request, f'{count} alerte(s) ignorée(s).')


@admin.register(AURA)
class AURAAdmin(admin.ModelAdmin):
    """Admin pour les Rapports d'audit."""

    list_display = [
        'REFERENCE', 'TITRE', 'TYPE_RAPPORT', 'FORMAT',
        'statut_badge', 'periode_display', 'NB_ENREGISTREMENTS',
        'fichier_link', 'genere_par_link', 'DATE_GENERATION'
    ]
    list_filter = [
        'TYPE_RAPPORT', 'FORMAT', 'STATUT', 'DATE_GENERATION'
    ]
    search_fields = [
        'REFERENCE', 'TITRE',
        'GENERE_PAR__NOM', 'GENERE_PAR__PRENOM'
    ]
    readonly_fields = [
        'REFERENCE', 'uuid', 'DATE_GENERATION', 'TAILLE_FICHIER',
        'CREATED_AT', 'UPDATED_AT', 'taille_fichier_display'
    ]
    raw_id_fields = ['GENERE_PAR']
    date_hierarchy = 'DATE_GENERATION'
    ordering = ['-DATE_GENERATION']

    fieldsets = (
        ('Identification', {
            'fields': ('REFERENCE', 'uuid', 'TITRE')
        }),
        ('Configuration', {
            'fields': ('TYPE_RAPPORT', 'FORMAT', 'STATUT')
        }),
        ('Période', {
            'fields': ('DATE_DEBUT', 'DATE_FIN')
        }),
        ('Filtres', {
            'fields': ('FILTRES',),
            'classes': ('collapse',)
        }),
        ('Fichier généré', {
            'fields': ('FICHIER', 'TAILLE_FICHIER', 'taille_fichier_display')
        }),
        ('Statistiques', {
            'fields': ('NB_ENREGISTREMENTS', 'RESUME'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('GENERE_PAR', 'DATE_GENERATION', 'MESSAGE_ERREUR',
                      'CREATED_AT', 'UPDATED_AT'),
            'classes': ('collapse',)
        }),
    )

    def statut_badge(self, obj):
        """Affiche le statut avec un badge coloré."""
        colors = {
            'EN_COURS': '#ffc107',
            'TERMINE': '#28a745',
            'ERREUR': '#dc3545',
        }
        color = colors.get(obj.STATUT, '#6c757d')
        text_color = '#212529' if obj.STATUT == 'EN_COURS' else 'white'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 500;">{}</span>',
            color, text_color, obj.get_STATUT_display()
        )
    statut_badge.short_description = 'Statut'
    statut_badge.admin_order_field = 'STATUT'

    def periode_display(self, obj):
        """Affiche la période du rapport."""
        return f'{obj.DATE_DEBUT.strftime("%d/%m/%Y")} - {obj.DATE_FIN.strftime("%d/%m/%Y")}'
    periode_display.short_description = 'Période'

    def fichier_link(self, obj):
        """Affiche un lien vers le fichier."""
        if obj.FICHIER:
            return format_html(
                '<a href="{}" target="_blank">📥 Télécharger</a>',
                obj.FICHIER.url
            )
        return '-'
    fichier_link.short_description = 'Fichier'

    def genere_par_link(self, obj):
        """Affiche un lien vers l'employé qui a généré le rapport."""
        if obj.GENERE_PAR:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:employee_zy00_change', args=[obj.GENERE_PAR.pk]),
                obj.GENERE_PAR.nom_complet
            )
        return '-'
    genere_par_link.short_description = 'Généré par'

    def taille_fichier_display(self, obj):
        """Affiche la taille du fichier en format lisible."""
        if not obj.TAILLE_FICHIER:
            return '-'
        size = obj.TAILLE_FICHIER
        for unit in ['octets', 'Ko', 'Mo', 'Go']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} To'
    taille_fichier_display.short_description = 'Taille'
