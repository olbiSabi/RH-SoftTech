from django.contrib import admin

# Register your models here.
# admin.py
from django.contrib import admin
from django.utils import timezone
from .models import ZDDE  # Remplacez par le nom réel de votre modèle


@admin.register(ZDDE)
class ZDDEAdmin(admin.ModelAdmin):
    # Colonnes affichées dans la liste
    list_display = ['CODE', 'LIBELLE', 'STATUT', 'DATEDEB', 'DATEFIN', 'est_actuel']

    # Filtres dans la sidebar
    list_filter = ['STATUT', 'DATEDEB']

    # Champ de recherche
    search_fields = ['CODE', 'LIBELLE']

    # Champs éditables directement dans la liste
    list_editable = ['STATUT']

    # Tri par défaut
    ordering = ['CODE']

    # Pagination
    list_per_page = 20

    # Actions personnalisées
    actions = ['activer_departements', 'desactiver_departements']

    def est_actuel(self, obj):
        """Colonne personnalisée pour vérifier si le département est actuellement valide"""
        aujourdhui = timezone.now().date()
        if obj.DATEFIN and obj.DATEFIN < aujourdhui:
            return "❌ Expiré"
        elif obj.DATEDEB > aujourdhui:
            return "⏳ Futur"
        else:
            return "✅ Actuel"

    est_actuel.short_description = "Statut de validité"

    def activer_departements(self, request, queryset):
        """Action pour activer les départements sélectionnés"""
        updated = queryset.update(STATUT=True)
        self.message_user(request, f"{updated} département(s) activé(s) avec succès.")

    activer_departements.short_description = "Activer les départements sélectionnés"

    def desactiver_departements(self, request, queryset):
        """Action pour désactiver les départements sélectionnés"""
        updated = queryset.update(STATUT=False)
        self.message_user(request, f"{updated} département(s) désactivé(s) avec succès.")

    desactiver_departements.short_description = "Désactiver les départements sélectionnés"

    # Configuration du formulaire d'édition
    fieldsets = (
        ('Informations département', {
            'fields': ('CODE', 'LIBELLE', 'STATUT')
        }),
        ('Période de validité', {
            'fields': ('DATEDEB', 'DATEFIN'),
            'description': 'Définir la période de validité du département'
        }),
    )

    # Textes d'aide pour les champs
    help_texts = {
        'CODE': 'Le code doit contenir exactement 3 caractères',
        'DATEFIN': 'Laisser vide si pas de date de fin prévue',
    }