from django.contrib import admin
from .models import ZDAB


@admin.register(ZDAB)
class ZDABAdmin(admin.ModelAdmin):
    list_display = ('CODE', 'LIBELLE', 'STATUT', 'get_status_color')
    list_filter = ('STATUT',)
    search_fields = ('CODE', 'LIBELLE')
    ordering = ('CODE',)

    fieldsets = (
        ('Informations principales', {
            'fields': ('CODE', 'LIBELLE', 'STATUT')
        }),
    )

    def get_status_color(self, obj):
        """Afficher le statut avec couleur"""
        if obj.STATUT:
            return '🟢 Actif'
        return '🔴 Inactif'

    get_status_color.short_description = 'Statut'


# Actions personnalisées
@admin.action(description='Activer les types d\'absence sélectionnés')
def activer_absences(modeladmin, request, queryset):
    queryset.update(STATUT=True)


@admin.action(description='Désactiver les types d\'absence sélectionnés')
def desactiver_absences(modeladmin, request, queryset):
    queryset.update(STATUT=False)


ZDABAdmin.actions = [activer_absences, desactiver_absences]