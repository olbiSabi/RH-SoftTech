"""
Admin pour le module Planning simplifié.
"""
from django.contrib import admin
from .models import SiteTravail, PosteTravail, Planning, Affectation, Evenement


@admin.register(SiteTravail)
class SiteTravailAdmin(admin.ModelAdmin):
    """Admin pour les sites de travail."""
    list_display = ['nom', 'telephone', 'heure_ouverture', 'heure_fermeture', 'is_active']
    list_filter = ['is_active', 'fuseau_horaire']
    search_fields = ['nom', 'adresse']
    ordering = ['nom']


@admin.register(PosteTravail)
class PosteTravailAdmin(admin.ModelAdmin):
    """Admin pour les postes de travail."""
    list_display = ['nom', 'site', 'type_poste', 'heure_debut', 'heure_fin', 'taux_horaire', 'is_active']
    list_filter = ['type_poste', 'site', 'is_active']
    search_fields = ['nom', 'description', 'site__nom']
    ordering = ['site', 'nom']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('site')


@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    """Admin pour les plannings."""
    list_display = ['titre', 'date_debut', 'date_fin', 'statut', 'created_by', 'created_at']
    list_filter = ['statut', 'date_debut', 'date_fin', 'created_at']
    search_fields = ['titre', 'description']
    ordering = ['-date_debut']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    """Admin pour les affectations."""
    list_display = ['employe', 'poste', 'date', 'heure_debut', 'heure_fin', 'statut', 'created_by']
    list_filter = ['statut', 'date', 'poste__site']
    search_fields = ['employe__nom', 'employe__prenoms', 'poste__nom']
    ordering = ['-date', 'heure_debut']
    readonly_fields = ['uuid', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'employe', 'poste', 'poste__site', 'planning', 'created_by'
        )


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    """Admin pour les evenements."""
    list_display = ['titre', 'type_evenement', 'date_debut', 'date_fin', 'lieu', 'created_by']
    list_filter = ['type_evenement', 'date_debut']
    search_fields = ['titre', 'description', 'lieu']
    ordering = ['-date_debut']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    filter_horizontal = ['employes']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
