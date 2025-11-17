from django.contrib import admin
from django.utils.html import format_html

from .models import ZDDE, ZYMA
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


@admin.register(ZYMA)
class ZYMAAdmin(admin.ModelAdmin):
    """Admin pour les managers de département"""
    list_display = (
        'departement_display',
        'employe_display',
        'date_debut',
        'date_fin',
        'statut_actif'  # ← CORRIGER ICI - changer le nom
    )
    list_filter = (
        'departement',
        'actif',
        'date_debut',
        'date_fin'
    )
    search_fields = (
        'departement__LIBELLE',
        'employe__nom',
        'employe__prenoms',
        'employe__matricule'
    )
    readonly_fields = ('actif',)

    def departement_display(self, obj):
        return f"{obj.departement.LIBELLE} ({obj.departement.CODE})"
    departement_display.short_description = 'Département'

    def employe_display(self, obj):
        return f"{obj.employe.nom} {obj.employe.prenoms} ({obj.employe.matricule})"
    employe_display.short_description = 'Manager'

    def statut_actif(self, obj):  # ← CORRIGER ICI - renommer la méthode
        if obj.actif:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: red;">● Inactif</span>')
    statut_actif.short_description = 'Statut'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('departement', 'employe')