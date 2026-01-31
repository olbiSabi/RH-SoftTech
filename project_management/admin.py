from django.contrib import admin
from .models import (
    JRClient, JRProject, JRTicket, JRCommentaire,
    JRPieceJointe, JRHistorique, JRImputation, JRSprint
)


@admin.register(JRClient)
class JRClientAdmin(admin.ModelAdmin):
    list_display = ('code_client', 'raison_sociale', 'email_contact', 'telephone_contact', 'statut', 'created_at')
    list_filter = ('statut', 'created_at')
    search_fields = ('code_client', 'raison_sociale', 'email_contact')
    ordering = ('-created_at',)


@admin.register(JRProject)
class JRProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'client', 'chef_projet', 'statut', 'date_debut', 'date_fin_prevue')
    list_filter = ('statut', 'client', 'date_debut')
    search_fields = ('code', 'nom', 'client__raison_sociale')
    autocomplete_fields = ('client', 'chef_projet')
    ordering = ('-created_at',)
    date_hierarchy = 'date_debut'


@admin.register(JRTicket)
class JRTicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'titre', 'projet', 'type_ticket', 'priorite', 'statut', 'assigne', 'date_echeance')
    list_filter = ('statut', 'priorite', 'type_ticket', 'projet', 'dans_backlog')
    search_fields = ('code', 'titre', 'description', 'projet__nom')
    autocomplete_fields = ('projet', 'assigne')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_editable = ('statut', 'priorite', 'assigne')


@admin.register(JRCommentaire)
class JRCommentaireAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'auteur', 'contenu_court', 'created_at')
    list_filter = ('created_at', 'ticket__projet')
    search_fields = ('contenu', 'ticket__code', 'auteur__nom')
    ordering = ('-created_at',)

    def contenu_court(self, obj):
        return obj.contenu[:50] + '...' if len(obj.contenu) > 50 else obj.contenu
    contenu_court.short_description = 'Contenu'


@admin.register(JRPieceJointe)
class JRPieceJointeAdmin(admin.ModelAdmin):
    list_display = ('nom_original', 'ticket', 'uploaded_by', 'taille', 'uploaded_at')
    list_filter = ('uploaded_at', 'ticket__projet')
    search_fields = ('nom_original', 'ticket__code')
    ordering = ('-uploaded_at',)


@admin.register(JRHistorique)
class JRHistoriqueAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'utilisateur', 'type_changement', 'champ_modifie', 'created_at')
    list_filter = ('type_changement', 'created_at', 'ticket__projet')
    search_fields = ('ticket__code', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('ticket', 'utilisateur', 'type_changement', 'champ_modifie',
                       'ancienne_valeur', 'nouvelle_valeur', 'description', 'created_at')


@admin.register(JRImputation)
class JRImputationAdmin(admin.ModelAdmin):
    list_display = ('date_imputation', 'employe', 'ticket', 'type_activite', 'heures', 'minutes',
                    'statut_validation', 'valide_par')
    list_filter = ('statut_validation', 'type_activite', 'date_imputation', 'ticket__projet')
    search_fields = ('employe__nom', 'ticket__code', 'description')
    autocomplete_fields = ('employe', 'ticket', 'valide_par')
    ordering = ('-date_imputation', '-created_at')
    date_hierarchy = 'date_imputation'
    list_editable = ('statut_validation',)

    fieldsets = (
        ('Informations principales', {
            'fields': ('employe', 'ticket', 'date_imputation', 'type_activite')
        }),
        ('Temps', {
            'fields': ('heures', 'minutes', 'description')
        }),
        ('Validation', {
            'fields': ('statut_validation', 'valide_par', 'date_validation', 'commentaire_validation')
        }),
    )


@admin.register(JRSprint)
class JRSprintAdmin(admin.ModelAdmin):
    list_display = ('nom', 'projet', 'statut', 'date_debut', 'date_fin', 'progression_display')
    list_filter = ('statut', 'projet', 'date_debut')
    search_fields = ('nom', 'projet__nom', 'description')
    autocomplete_fields = ('projet',)
    filter_horizontal = ('tickets',)
    ordering = ('-date_debut',)
    date_hierarchy = 'date_debut'

    def progression_display(self, obj):
        progression = obj.progression
        if progression >= 100:
            return f'100%'
        elif progression >= 50:
            return f'{progression}%'
        else:
            return f'{progression}%'
    progression_display.short_description = 'Progression'
