# frais/admin.py
"""
Configuration de l'interface d'administration pour le module Frais.
"""
from django.contrib import admin
from frais.models import NFCA, NFPL, NFNF, NFLF, NFAV


@admin.register(NFCA)
class CategorieAdmin(admin.ModelAdmin):
    """Admin pour les catégories de frais."""
    list_display = ['CODE', 'LIBELLE', 'JUSTIFICATIF_OBLIGATOIRE', 'PLAFOND_DEFAUT', 'ORDRE', 'STATUT']
    list_filter = ['STATUT', 'JUSTIFICATIF_OBLIGATOIRE']
    search_fields = ['CODE', 'LIBELLE']
    ordering = ['ORDRE', 'LIBELLE']
    list_editable = ['ORDRE', 'STATUT']


@admin.register(NFPL)
class PlafondAdmin(admin.ModelAdmin):
    """Admin pour les plafonds de frais."""
    list_display = ['CATEGORIE', 'GRADE', 'MONTANT_JOURNALIER', 'MONTANT_MENSUEL', 'MONTANT_PAR_DEPENSE', 'DATE_DEBUT', 'DATE_FIN', 'STATUT']
    list_filter = ['CATEGORIE', 'STATUT']
    search_fields = ['CATEGORIE__CODE', 'GRADE']
    date_hierarchy = 'DATE_DEBUT'


class LigneFraisInline(admin.TabularInline):
    """Inline pour les lignes de frais."""
    model = NFLF
    extra = 0
    readonly_fields = ['uuid', 'MONTANT_CONVERTI', 'CREATED_AT']
    fields = ['CATEGORIE', 'DATE_DEPENSE', 'DESCRIPTION', 'MONTANT', 'DEVISE', 'STATUT_LIGNE', 'JUSTIFICATIF']


@admin.register(NFNF)
class NoteFraisAdmin(admin.ModelAdmin):
    """Admin pour les notes de frais."""
    list_display = ['REFERENCE', 'EMPLOYE', 'PERIODE_DEBUT', 'PERIODE_FIN', 'MONTANT_TOTAL', 'STATUT', 'CREATED_AT']
    list_filter = ['STATUT', 'CREATED_AT']
    search_fields = ['REFERENCE', 'EMPLOYE__NOM', 'EMPLOYE__PRENOMS', 'EMPLOYE__MATRICULE']
    date_hierarchy = 'CREATED_AT'
    readonly_fields = ['uuid', 'REFERENCE', 'MONTANT_TOTAL', 'MONTANT_VALIDE', 'MONTANT_REMBOURSE', 'CREATED_AT', 'UPDATED_AT']
    inlines = [LigneFraisInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('REFERENCE', 'EMPLOYE', 'PERIODE_DEBUT', 'PERIODE_FIN', 'OBJET')
        }),
        ('Montants', {
            'fields': ('MONTANT_TOTAL', 'MONTANT_VALIDE', 'MONTANT_REMBOURSE')
        }),
        ('Statut et validation', {
            'fields': ('STATUT', 'DATE_SOUMISSION', 'VALIDEUR', 'DATE_VALIDATION', 'COMMENTAIRE_VALIDATION')
        }),
        ('Remboursement', {
            'fields': ('DATE_REMBOURSEMENT', 'REFERENCE_PAIEMENT'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('uuid', 'CREATED_BY', 'CREATED_AT', 'UPDATED_AT'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NFLF)
class LigneFraisAdmin(admin.ModelAdmin):
    """Admin pour les lignes de frais."""
    list_display = ['NOTE_FRAIS', 'CATEGORIE', 'DATE_DEPENSE', 'DESCRIPTION', 'MONTANT', 'STATUT_LIGNE']
    list_filter = ['STATUT_LIGNE', 'CATEGORIE', 'DATE_DEPENSE']
    search_fields = ['NOTE_FRAIS__REFERENCE', 'DESCRIPTION']
    date_hierarchy = 'DATE_DEPENSE'
    readonly_fields = ['uuid', 'MONTANT_CONVERTI', 'CREATED_AT', 'UPDATED_AT']


@admin.register(NFAV)
class AvanceAdmin(admin.ModelAdmin):
    """Admin pour les avances sur frais."""
    list_display = ['REFERENCE', 'EMPLOYE', 'MONTANT_DEMANDE', 'MONTANT_APPROUVE', 'STATUT', 'CREATED_AT']
    list_filter = ['STATUT', 'CREATED_AT']
    search_fields = ['REFERENCE', 'EMPLOYE__NOM', 'EMPLOYE__PRENOMS', 'EMPLOYE__MATRICULE']
    date_hierarchy = 'CREATED_AT'
    readonly_fields = ['uuid', 'REFERENCE', 'CREATED_AT', 'UPDATED_AT']

    fieldsets = (
        ('Informations générales', {
            'fields': ('REFERENCE', 'EMPLOYE', 'MONTANT_DEMANDE', 'MOTIF')
        }),
        ('Mission', {
            'fields': ('DATE_MISSION_DEBUT', 'DATE_MISSION_FIN'),
            'classes': ('collapse',)
        }),
        ('Approbation', {
            'fields': ('STATUT', 'MONTANT_APPROUVE', 'APPROBATEUR', 'DATE_APPROBATION', 'COMMENTAIRE_APPROBATION')
        }),
        ('Versement', {
            'fields': ('DATE_VERSEMENT', 'REFERENCE_VERSEMENT'),
            'classes': ('collapse',)
        }),
        ('Régularisation', {
            'fields': ('NOTE_FRAIS', 'MONTANT_REGULARISE', 'DATE_REGULARISATION'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('uuid', 'CREATED_BY', 'CREATED_AT', 'UPDATED_AT'),
            'classes': ('collapse',)
        }),
    )
