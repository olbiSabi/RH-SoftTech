"""
Admin Django pour la gestion des congés et absences
Application: absence
Système HR_ONIAN
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
import json

from .models import ZDDA, ZDSO, ZDHA, ZDJF, ZDPF


# ==========================================
# ADMIN DEMANDE D'ABSENCE (ZDDA)
# ==========================================

@admin.register(ZDDA)
class ZDDAAdmin(admin.ModelAdmin):
    """
    Administration des demandes d'absence
    """

    list_display = [
        'numero_demande_colored',
        'employe_link',
        'type_absence_colored',
        'date_debut',
        'date_fin',
        'nombre_jours_formatted',
        'statut_badge',
        'validee_manager_icon',
        'validee_rh_icon',
        'created_at',
    ]

    list_filter = [
        'statut',
        'type_absence',
        'duree',
        'validee_manager',
        'validee_rh',
        'est_urgent',
        'created_at',
        'date_debut',
    ]

    search_fields = [
        'numero_demande',
        'employe__nom',
        'employe__prenoms',
        'employe__matricule',
        'motif',
    ]

    readonly_fields = [
        'numero_demande',
        'id',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'ip_address',
        'solde_avant',
        'solde_apres',
        'historique_detail',
    ]

    fieldsets = (
        ('📋 Informations principales', {
            'fields': (
                'numero_demande',
                'id',
                'employe',
                'type_absence',
            )
        }),
        ('📅 Dates et durée', {
            'fields': (
                'date_debut',
                'date_fin',
                'duree',
                'periode',
                'nombre_jours',
            )
        }),
        ('📝 Détails', {
            'fields': (
                'motif',
                'justificatif',
            )
        }),
        ('🔄 Statut', {
            'fields': (
                'statut',
                'est_urgent',
                'est_annulee',
                'date_annulation',
                'motif_annulation',
            )
        }),
        ('✅ Validation Manager', {
            'fields': (
                'validee_manager',
                'date_validation_manager',
                'validateur_manager',
                'commentaire_manager',
                'motif_refus_manager',
            ),
            'classes': ('collapse',),
        }),
        ('✅ Validation RH', {
            'fields': (
                'validee_rh',
                'date_validation_rh',
                'validateur_rh',
                'commentaire_rh',
                'motif_refus_rh',
            ),
            'classes': ('collapse',),
        }),
        ('💰 Soldes', {
            'fields': (
                'solde_avant',
                'solde_apres',
            ),
            'classes': ('collapse',),
        }),
        ('📧 Notifications', {
            'fields': (
                'notification_envoyee_manager',
                'notification_envoyee_rh',
                'notification_envoyee_employe',
            ),
            'classes': ('collapse',),
        }),
        ('🔍 Audit', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
                'ip_address',
            ),
            'classes': ('collapse',),
        }),
        ('📜 Historique', {
            'fields': (
                'historique_detail',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'date_debut'

    actions = [
        'valider_manager',
        'valider_rh',
        'refuser_manager',
        'refuser_rh',
        'annuler_demande',
    ]

    # Méthodes d'affichage personnalisées

    def numero_demande_colored(self, obj):
        """Numéro de demande avec couleur selon statut"""
        colors = {
            'EN_ATTENTE': '#fbbf24',
            'VALIDEE_MANAGER': '#60a5fa',
            'VALIDEE_RH': '#34d399',
            'REFUSEE_MANAGER': '#f87171',
            'REFUSEE_RH': '#ef4444',
            'ANNULEE': '#9ca3af',
        }
        color = colors.get(obj.statut, '#6b7280')
        return format_html(
            '<strong style="color: {};">{}</strong>',
            color,
            obj.numero_demande
        )
    numero_demande_colored.short_description = 'Numéro'
    numero_demande_colored.admin_order_field = 'numero_demande'

    def employe_link(self, obj):
        """Lien vers l'employé"""
        url = reverse('admin:employee_zy00_change', args=[obj.employe.pk])
        return format_html(
            '<a href="{}" target="_blank">{} {}</a>',
            url,
            obj.employe.nom,
            obj.employe.prenoms
        )
    employe_link.short_description = 'Employé'
    employe_link.admin_order_field = 'employe__nom'

    def type_absence_colored(self, obj):
        """Type d'absence avec icône"""
        icons = {
            'CPN': '🏖️',
            'RTT': '⏰',
            'MAL': '🤒',
            'FAM': '👨‍👩‍👧',
            'FOR': '📚',
            'CSS': '🚫',
            'MAT': '🤰',
            'PAT': '👶',
            'PAR': '👶',
        }
        icon = icons.get(obj.type_absence.CODE, '📋')
        return format_html(
            '{} {}',
            icon,
            obj.type_absence.LIBELLE
        )
    type_absence_colored.short_description = 'Type'
    type_absence_colored.admin_order_field = 'type_absence'

    def nombre_jours_formatted(self, obj):
        """Nombre de jours formaté"""
        if obj.nombre_jours:
            return f"{obj.nombre_jours} jour{'s' if obj.nombre_jours > 1 else ''}"
        return '-'
    nombre_jours_formatted.short_description = 'Jours'
    nombre_jours_formatted.admin_order_field = 'nombre_jours'

    def statut_badge(self, obj):
        """Badge de statut"""
        badges = {
            'EN_ATTENTE': ('<span style="background: #fef3c7; color: #92400e; padding: 3px 8px; '
                          'border-radius: 12px; font-size: 11px; font-weight: 600;">⏳ En attente</span>'),
            'VALIDEE_MANAGER': ('<span style="background: #dbeafe; color: #1e40af; padding: 3px 8px; '
                               'border-radius: 12px; font-size: 11px; font-weight: 600;">✅ Validée Manager</span>'),
            'VALIDEE_RH': ('<span style="background: #d1fae5; color: #065f46; padding: 3px 8px; '
                          'border-radius: 12px; font-size: 11px; font-weight: 600;">✅ Validée RH</span>'),
            'REFUSEE_MANAGER': ('<span style="background: #fee2e2; color: #991b1b; padding: 3px 8px; '
                               'border-radius: 12px; font-size: 11px; font-weight: 600;">❌ Refusée Manager</span>'),
            'REFUSEE_RH': ('<span style="background: #fecaca; color: #7f1d1d; padding: 3px 8px; '
                          'border-radius: 12px; font-size: 11px; font-weight: 600;">❌ Refusée RH</span>'),
            'ANNULEE': ('<span style="background: #e5e7eb; color: #374151; padding: 3px 8px; '
                       'border-radius: 12px; font-size: 11px; font-weight: 600;">🚫 Annulée</span>'),
        }
        return format_html(badges.get(obj.statut, obj.statut))
    statut_badge.short_description = 'Statut'
    statut_badge.admin_order_field = 'statut'

    def validee_manager_icon(self, obj):
        """Icône validation manager"""
        if obj.validee_manager:
            return format_html('<span style="color: #10b981; font-size: 18px;">✅</span>')
        return format_html('<span style="color: #d1d5db; font-size: 18px;">⭕</span>')
    validee_manager_icon.short_description = 'Manager'
    validee_manager_icon.admin_order_field = 'validee_manager'

    def validee_rh_icon(self, obj):
        """Icône validation RH"""
        if obj.validee_rh:
            return format_html('<span style="color: #10b981; font-size: 18px;">✅</span>')
        return format_html('<span style="color: #d1d5db; font-size: 18px;">⭕</span>')
    validee_rh_icon.short_description = 'RH'
    validee_rh_icon.admin_order_field = 'validee_rh'

    def historique_detail(self, obj):
        """Affichage de l'historique"""
        historique = obj.historique.all()[:10]
        if not historique:
            return format_html('<em>Aucun historique</em>')

        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f3f4f6; font-weight: 600;">'
        html += '<th style="padding: 8px; text-align: left;">Date</th>'
        html += '<th style="padding: 8px; text-align: left;">Action</th>'
        html += '<th style="padding: 8px; text-align: left;">Utilisateur</th>'
        html += '<th style="padding: 8px; text-align: left;">Commentaire</th>'
        html += '</tr>'

        for h in historique:
            html += '<tr style="border-bottom: 1px solid #e5e7eb;">'
            html += f'<td style="padding: 8px;">{h.timestamp.strftime("%d/%m/%Y %H:%M")}</td>'
            html += f'<td style="padding: 8px;"><strong>{h.get_action_display()}</strong></td>'
            html += f'<td style="padding: 8px;">{h.utilisateur.nom if h.utilisateur else "-"}</td>'
            html += f'<td style="padding: 8px;">{h.commentaire[:50] if h.commentaire else "-"}</td>'
            html += '</tr>'

        html += '</table>'
        return format_html(html)
    historique_detail.short_description = 'Historique des actions'

    # Actions personnalisées

    def valider_manager(self, request, queryset):
        """Valider les demandes en tant que manager"""
        updated = queryset.filter(statut='EN_ATTENTE').update(
            statut='VALIDEE_MANAGER',
            validee_manager=True,
            date_validation_manager=timezone.now(),
        )
        self.message_user(request, f'{updated} demande(s) validée(s) par le manager.')
    valider_manager.short_description = '✅ Valider (Manager)'

    def valider_rh(self, request, queryset):
        """Valider les demandes en tant que RH"""
        updated = queryset.filter(statut='VALIDEE_MANAGER').update(
            statut='VALIDEE_RH',
            validee_rh=True,
            date_validation_rh=timezone.now(),
        )
        self.message_user(request, f'{updated} demande(s) validée(s) par RH.')
    valider_rh.short_description = '✅ Valider (RH)'

    def refuser_manager(self, request, queryset):
        """Refuser les demandes en tant que manager"""
        updated = queryset.filter(statut='EN_ATTENTE').update(
            statut='REFUSEE_MANAGER'
        )
        self.message_user(request, f'{updated} demande(s) refusée(s) par le manager.')
    refuser_manager.short_description = '❌ Refuser (Manager)'

    def refuser_rh(self, request, queryset):
        """Refuser les demandes en tant que RH"""
        updated = queryset.filter(statut='VALIDEE_MANAGER').update(
            statut='REFUSEE_RH'
        )
        self.message_user(request, f'{updated} demande(s) refusée(s) par RH.')
    refuser_rh.short_description = '❌ Refuser (RH)'

    def annuler_demande(self, request, queryset):
        """Annuler les demandes"""
        updated = queryset.filter(
            statut__in=['EN_ATTENTE', 'VALIDEE_MANAGER']
        ).update(
            statut='ANNULEE',
            est_annulee=True,
            date_annulation=timezone.now(),
        )
        self.message_user(request, f'{updated} demande(s) annulée(s).')
    annuler_demande.short_description = '🚫 Annuler'


# ==========================================
# ADMIN SOLDE DE CONGÉS (ZDSO)
# ==========================================

@admin.register(ZDSO)
class ZDSOAdmin(admin.ModelAdmin):
    """
    Administration des soldes de congés
    """

    list_display = [
        'employe_link',
        'annee',
        'jours_disponibles_colored',
        'jours_acquis',
        'jours_pris',
        'jours_en_attente',
        'jours_reportes',
        'rtt_disponibles',
        'derniere_maj',
    ]

    list_filter = [
        'annee',
        'derniere_maj',
    ]

    search_fields = [
        'employe__nom',
        'employe__prenoms',
        'employe__matricule',
    ]

    readonly_fields = [
        'id',
        'derniere_maj',
        'created_at',
        'updated_at',
        'jours_disponibles_progress',
    ]

    fieldsets = (
        ('👤 Employé', {
            'fields': (
                'id',
                'employe',
                'annee',
            )
        }),
        ('🏖️ Congés Payés', {
            'fields': (
                'jours_acquis',
                'jours_reportes',
                'jours_pris',
                'jours_en_attente',
                'jours_disponibles',
                'jours_disponibles_progress',
            )
        }),
        ('⏰ RTT', {
            'fields': (
                'rtt_acquis',
                'rtt_pris',
                'rtt_disponibles',
            )
        }),
        ('🔍 Audit', {
            'fields': (
                'derniere_maj',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'derniere_maj'

    actions = ['recalculer_soldes']

    def employe_link(self, obj):
        """Lien vers l'employé"""
        url = reverse('admin:employee_zy00_change', args=[obj.employe.pk])
        return format_html(
            '<a href="{}" target="_blank">{} {}</a>',
            url,
            obj.employe.nom,
            obj.employe.prenoms
        )
    employe_link.short_description = 'Employé'
    employe_link.admin_order_field = 'employe__nom'

    def jours_disponibles_colored(self, obj):
        """Jours disponibles avec couleur"""
        if obj.jours_disponibles < 5:
            color = '#ef4444'  # Rouge
        elif obj.jours_disponibles < 10:
            color = '#f59e0b'  # Orange
        else:
            color = '#10b981'  # Vert

        return format_html(
            '<strong style="color: {}; font-size: 16px;">{} jours</strong>',
            color,
            obj.jours_disponibles
        )
    jours_disponibles_colored.short_description = 'Disponibles'
    jours_disponibles_colored.admin_order_field = 'jours_disponibles'

    def jours_disponibles_progress(self, obj):
        """Barre de progression des jours"""
        total = obj.jours_acquis + obj.jours_reportes
        if total == 0:
            pourcentage = 0
        else:
            pourcentage = (obj.jours_disponibles / total) * 100

        if pourcentage < 30:
            color = '#ef4444'
        elif pourcentage < 60:
            color = '#f59e0b'
        else:
            color = '#10b981'

        html = f'''
        <div style="width: 100%; background: #e5e7eb; border-radius: 8px; overflow: hidden;">
            <div style="width: {pourcentage}%; background: {color}; height: 24px; 
                        display: flex; align-items: center; justify-content: center; 
                        color: white; font-weight: 600; font-size: 12px;">
                {pourcentage:.1f}%
            </div>
        </div>
        <div style="margin-top: 5px; font-size: 12px; color: #6b7280;">
            {obj.jours_disponibles} / {total} jours
        </div>
        '''
        return format_html(html)
    jours_disponibles_progress.short_description = 'Progression'

    def recalculer_soldes(self, request, queryset):
        """Recalculer les soldes"""
        for solde in queryset:
            solde.calculer_soldes()
        self.message_user(request, f'{queryset.count()} solde(s) recalculé(s).')
    recalculer_soldes.short_description = '🔄 Recalculer les soldes'


# ==========================================
# ADMIN HISTORIQUE (ZDHA)
# ==========================================

@admin.register(ZDHA)
class ZDHAAdmin(admin.ModelAdmin):
    """
    Administration de l'historique des absences
    """

    list_display = [
        'timestamp',
        'demande_link',
        'action_badge',
        'utilisateur_link',
        'ancien_statut',
        'nouveau_statut',
        'commentaire_short',
    ]

    list_filter = [
        'action',
        'timestamp',
        'ancien_statut',
        'nouveau_statut',
    ]

    search_fields = [
        'demande__numero_demande',
        'utilisateur__nom',
        'utilisateur__prenoms',
        'commentaire',
    ]

    readonly_fields = [
        'id',
        'demande',
        'action',
        'utilisateur',
        'ancien_statut',
        'nouveau_statut',
        'commentaire',
        'donnees_modifiees_formatted',
        'ip_address',
        'timestamp',
    ]

    fieldsets = (
        ('📋 Informations', {
            'fields': (
                'id',
                'demande',
                'timestamp',
            )
        }),
        ('⚡ Action', {
            'fields': (
                'action',
                'utilisateur',
                'ancien_statut',
                'nouveau_statut',
                'commentaire',
            )
        }),
        ('📊 Données modifiées', {
            'fields': (
                'donnees_modifiees_formatted',
            ),
            'classes': ('collapse',),
        }),
        ('🔍 Technique', {
            'fields': (
                'ip_address',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Désactiver l'ajout manuel"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Désactiver la suppression"""
        return False

    def demande_link(self, obj):
        """Lien vers la demande"""
        url = reverse('admin:absence_zdda_change', args=[obj.demande.id])
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url,
            obj.demande.numero_demande
        )
    demande_link.short_description = 'Demande'
    demande_link.admin_order_field = 'demande__numero_demande'

    def action_badge(self, obj):
        """Badge pour l'action"""
        colors = {
            'CREATION': '#3b82f6',
            'MODIFICATION': '#f59e0b',
            'VALIDATION_MANAGER': '#10b981',
            'VALIDATION_RH': '#059669',
            'REFUS_MANAGER': '#ef4444',
            'REFUS_RH': '#dc2626',
            'ANNULATION': '#6b7280',
        }
        color = colors.get(obj.action, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
    action_badge.admin_order_field = 'action'

    def utilisateur_link(self, obj):
        """Lien vers l'utilisateur"""
        if not obj.utilisateur:
            return '-'
        url = reverse('admin:employee_zy00_change', args=[obj.utilisateur.pk])
        return format_html(
            '<a href="{}" target="_blank">{} {}</a>',
            url,
            obj.utilisateur.nom,
            obj.utilisateur.prenoms
        )
    utilisateur_link.short_description = 'Utilisateur'
    utilisateur_link.admin_order_field = 'utilisateur__nom'

    def commentaire_short(self, obj):
        """Commentaire tronqué"""
        if obj.commentaire:
            return obj.commentaire[:50] + ('...' if len(obj.commentaire) > 50 else '')
        return '-'
    commentaire_short.short_description = 'Commentaire'

    def donnees_modifiees_formatted(self, obj):
        """Données modifiées formatées"""
        if not obj.donnees_modifiees:
            return format_html('<em>Aucune donnée</em>')

        try:
            data = json.dumps(obj.donnees_modifiees, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f3f4f6; padding: 10px; border-radius: 4px;">{}</pre>', data)
        except:
            return str(obj.donnees_modifiees)
    donnees_modifiees_formatted.short_description = 'Données JSON'


# ==========================================
# ADMIN JOURS FÉRIÉS (ZDJF)
# ==========================================

@admin.register(ZDJF)
class ZDJFAdmin(admin.ModelAdmin):
    """
    Administration des jours fériés
    """

    list_display = [
        'date_formatted',
        'libelle',
        'fixe_icon',
        'actif_icon',
    ]

    list_filter = [
        'fixe',
        'actif',
        'date',
    ]

    search_fields = [
        'libelle',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('📅 Jour férié', {
            'fields': (
                'id',
                'date',
                'libelle',
                'fixe',
                'actif',
            )
        }),
        ('🔍 Audit', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'date'

    actions = ['activer', 'desactiver']

    def date_formatted(self, obj):
        """Date formatée avec jour de la semaine"""
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        jour = jours[obj.date.weekday()]
        return format_html(
            '<strong>{}</strong><br><small style="color: #6b7280;">{}</small>',
            obj.date.strftime('%d/%m/%Y'),
            jour
        )
    date_formatted.short_description = 'Date'
    date_formatted.admin_order_field = 'date'

    def fixe_icon(self, obj):
        """Icône pour date fixe"""
        if obj.fixe:
            return format_html('<span style="color: #10b981; font-size: 18px;">📌</span>')
        return format_html('<span style="color: #d1d5db; font-size: 18px;">📅</span>')
    fixe_icon.short_description = 'Fixe'
    fixe_icon.admin_order_field = 'fixe'

    def actif_icon(self, obj):
        """Icône pour actif"""
        if obj.actif:
            return format_html('<span style="color: #10b981; font-size: 18px;">✅</span>')
        return format_html('<span style="color: #ef4444; font-size: 18px;">❌</span>')
    actif_icon.short_description = 'Actif'
    actif_icon.admin_order_field = 'actif'

    def activer(self, request, queryset):
        """Activer les jours fériés"""
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} jour(s) férié(s) activé(s).')
    activer.short_description = '✅ Activer'

    def desactiver(self, request, queryset):
        """Désactiver les jours fériés"""
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} jour(s) férié(s) désactivé(s).')
    desactiver.short_description = '❌ Désactiver'


# ==========================================
# ADMIN PÉRIODES DE FERMETURE (ZDPF)
# ==========================================

@admin.register(ZDPF)
class ZDPFAdmin(admin.ModelAdmin):
    """
    Administration des périodes de fermeture
    """

    list_display = [
        'libelle',
        'date_debut',
        'date_fin',
        'duree_jours',
        'actif_icon',
        'created_by',
    ]

    list_filter = [
        'actif',
        'date_debut',
        'created_at',
    ]

    search_fields = [
        'libelle',
        'description',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'duree_jours',
    ]

    fieldsets = (
        ('🏢 Période de fermeture', {
            'fields': (
                'id',
                'libelle',
                'description',
                'date_debut',
                'date_fin',
                'duree_jours',
                'actif',
            )
        }),
        ('🔍 Audit', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'date_debut'

    actions = ['activer', 'desactiver']

    def duree_jours(self, obj):
        """Calcul de la durée en jours"""
        if obj.date_debut and obj.date_fin:
            duree = (obj.date_fin - obj.date_debut).days + 1
            return f"{duree} jour{'s' if duree > 1 else ''}"
        return '-'
    duree_jours.short_description = 'Durée'

    def actif_icon(self, obj):
        """Icône pour actif"""
        if obj.actif:
            return format_html('<span style="color: #10b981; font-size: 18px;">✅</span>')
        return format_html('<span style="color: #ef4444; font-size: 18px;">❌</span>')
    actif_icon.short_description = 'Actif'
    actif_icon.admin_order_field = 'actif'

    def activer(self, request, queryset):
        """Activer les périodes"""
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} période(s) activée(s).')
    activer.short_description = '✅ Activer'

    def desactiver(self, request, queryset):
        """Désactiver les périodes"""
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} période(s) désactivée(s).')
    desactiver.short_description = '❌ Désactiver'