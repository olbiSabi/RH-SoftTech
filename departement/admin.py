from django.contrib import admin
from .models import ZDDE
from datetime import date
from .models import ZDPO

@admin.register(ZDDE)
class ZDDEAdmin(admin.ModelAdmin):
    list_display = ('CODE', 'LIBELLE', 'STATUT', 'DATEDEB', 'get_datefin_display', 'get_status_color')
    list_filter = ('STATUT', 'DATEDEB')
    search_fields = ('CODE', 'LIBELLE')
    ordering = ('CODE',)

    fieldsets = (
        ('Informations principales', {
            'fields': ('CODE', 'LIBELLE', 'STATUT')
        }),
        ('Période de validité', {
            'fields': ('DATEDEB', 'DATEFIN'),
            'description': 'Laisser DATEFIN vide pour une validité infinie'
        }),
    )

    def get_datefin_display(self, obj):
        if not obj.DATEFIN:
            return '-- --'
        return obj.DATEFIN.strftime('%d/%m/%Y')

    get_datefin_display.short_description = 'Date Fin'
    def get_status_color(self, obj):
        """Afficher le statut avec couleur"""
        if obj.STATUT:
            return '🟢 Actif'
        return '🔴 Inactif'

    get_status_color.short_description = 'Statut'

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


# Actions personnalisées
@admin.action(description='Activer les départements sélectionnés')
def activer_departements(modeladmin, request, queryset):
    queryset.update(STATUT=True)


@admin.action(description='Désactiver les départements sélectionnés')
def desactiver_departements(modeladmin, request, queryset):
    queryset.update(STATUT=False)


ZDDEAdmin.actions = [activer_departements, desactiver_departements]


@admin.register(ZDPO)
class ZDPOAdmin(admin.ModelAdmin):
    list_display = ('CODE', 'LIBELLE', 'DEPARTEMENT', 'STATUT', 'DATEDEB', 'get_datefin_display')
    list_filter = ('STATUT', 'DEPARTEMENT', 'DATEDEB')
    search_fields = ('CODE', 'LIBELLE', 'DEPARTEMENT__LIBELLE')
    ordering = ('CODE',)

    def get_datefin_display(self, obj):
        if not obj.DATEFIN:
            return '-- --'
        return obj.DATEFIN.strftime('%d/%m/%Y')

    get_datefin_display.short_description = 'Date Fin'