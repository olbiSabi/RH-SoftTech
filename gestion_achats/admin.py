"""
Configuration de l'interface d'administration Django pour le module Gestion des Achats & Commandes (GAC).
"""

from django.contrib import admin
from django.utils.html import format_html

from gestion_achats.models import (
    GACFournisseur,
    GACCategorie,
    GACArticle,
    GACArticleFournisseur,
    GACBudget,
    GACDemandeAchat,
    GACLigneDemandeAchat,
    GACBonCommande,
    GACLigneBonCommande,
    GACReception,
    GACLigneReception,
    GACBonRetour,
    GACLigneBonRetour,
    GACPieceJointe,
    GACHistorique,
    GACParametres,
)


# ==============================================================================
# FOURNISSEURS
# ==============================================================================

@admin.register(GACFournisseur)
class GACFournisseurAdmin(admin.ModelAdmin):
    """Administration des fournisseurs."""

    list_display = (
        'code',
        'raison_sociale',
        'email',
        'telephone',
        'ville',
        'date_creation',
    )

    list_filter = (
        'pays',
        'date_creation',
    )

    search_fields = (
        'code',
        'raison_sociale',
        'email',
        'nif',
        'numero_tva',
        'ville',
    )

    readonly_fields = (
        'uuid',
        'date_creation',
        'date_modification',
    )


# ==============================================================================
# CATÉGORIES
# ==============================================================================

@admin.register(GACCategorie)
class GACCategorieAdmin(admin.ModelAdmin):
    """Administration des catégories d'articles."""

    list_display = (
        'code',
        'nom',
        'description',
        'date_creation',
    )

    list_filter = (
        'date_creation',
    )

    search_fields = (
        'code',
        'nom',
        'description',
    )

    readonly_fields = (
        'uuid',
        'date_creation',
        'date_modification',
    )


# ==============================================================================
# ARTICLES
# ==============================================================================

class GACArticleFournisseurInline(admin.TabularInline):
    """Inline pour les relations article-fournisseur."""
    model = GACArticleFournisseur
    extra = 1


@admin.register(GACArticle)
class GACArticleAdmin(admin.ModelAdmin):
    """Administration des articles."""

    list_display = (
        'reference',
        'designation',
        'categorie',
        'unite',
        'prix_unitaire',
    )

    list_filter = (
        'categorie',
        'unite',
    )

    search_fields = (
        'reference',
        'designation',
        'description',
    )

    readonly_fields = (
        'uuid',
        'date_creation',
        'date_modification',
    )

    fieldsets = (
        ('Informations générales', {
            'fields': (
                'uuid',
                'reference',
                'designation',
                'categorie',
            )
        }),
        ('Description', {
            'fields': (
                'description',
            )
        }),
        ('Caractéristiques', {
            'fields': (
                'unite',
                'prix_unitaire',
            )
        }),
        ('Dates', {
            'fields': (
                'date_creation',
                'date_modification',
            ),
            'classes': ('collapse',),
        }),
    )

    inlines = [GACArticleFournisseurInline]


# ==============================================================================
# RELATIONS ARTICLE-FOURNISSEUR
# ==============================================================================

@admin.register(GACArticleFournisseur)
class GACArticleFournisseurAdmin(admin.ModelAdmin):
    """Administration des relations article-fournisseur."""

    list_display = (
        'article',
        'fournisseur',
        'reference_fournisseur',
        'prix_fournisseur',
        'delai_livraison',
        'fournisseur_principal',
    )

    list_filter = (
        'fournisseur_principal',
        'fournisseur',
    )

    search_fields = (
        'article__reference',
        'article__designation',
        'fournisseur__raison_sociale',
        'reference_fournisseur',
    )

    readonly_fields = (
        'date_creation',
    )


# ==============================================================================
# BUDGETS
# ==============================================================================

@admin.register(GACBudget)
class GACBudgetAdmin(admin.ModelAdmin):
    """Administration des budgets."""
    pass


# ==============================================================================
# DEMANDES D'ACHAT
# ==============================================================================

class GACLigneDemandeAchatInline(admin.TabularInline):
    """Inline pour les lignes de demande d'achat."""
    model = GACLigneDemandeAchat
    extra = 1
    fields = (
        'article',
        'quantite',
        'prix_unitaire',
        'montant',
    )
    readonly_fields = ('montant',)


@admin.register(GACDemandeAchat)
class GACDemandeAchatAdmin(admin.ModelAdmin):
    """Administration des demandes d'achat."""

    list_display = (
        'numero',
        'objet',
        'demandeur',
        'departement',
        'montant_total_ht',
        'statut_badge',
        'priorite_badge',
        'date_creation',
    )

    list_filter = (
        'statut',
        'priorite',
        'departement',
        'date_creation',
    )

    search_fields = (
        'numero',
        'objet',
        'demandeur__nom',
        'demandeur__prenom',
    )

    readonly_fields = (
        'uuid',
        'numero',
        'montant_total_ht',
        'date_creation',
        'date_modification',
    )

    inlines = [GACLigneDemandeAchatInline]

    def statut_badge(self, obj):
        """Badge pour le statut."""
        colors = {
            'BROUILLON': 'gray',
            'SOUMISE': 'blue',
            'VALIDEE_N1': 'orange',
            'VALIDEE_N2': 'green',
            'REJETEE': 'red',
            'CONVERTIE_BC': 'purple',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.statut, 'gray'),
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'

    def priorite_badge(self, obj):
        """Badge pour la priorité."""
        colors = {
            'NORMALE': 'green',
            'HAUTE': 'orange',
            'URGENTE': 'red',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.priorite, 'gray'),
            obj.get_priorite_display()
        )
    priorite_badge.short_description = 'Priorité'


@admin.register(GACLigneDemandeAchat)
class GACLigneDemandeAchatAdmin(admin.ModelAdmin):
    """Administration des lignes de demande d'achat."""

    list_display = (
        'demande_achat',
        'article',
        'quantite',
        'prix_unitaire',
        'montant',
    )

    search_fields = (
        'demande_achat__numero',
        'article__designation',
    )

    readonly_fields = (
        'uuid',
        'montant',
    )


# ==============================================================================
# BONS DE COMMANDE
# ==============================================================================

class GACLigneBonCommandeInline(admin.TabularInline):
    """Inline pour les lignes de bon de commande."""
    model = GACLigneBonCommande
    extra = 0
    fields = (
        'article',
        'quantite_commandee',
        'prix_unitaire',
        'taux_tva',
        'montant',
        'montant_ttc',
    )
    readonly_fields = ('montant', 'montant_ttc')


@admin.register(GACBonCommande)
class GACBonCommandeAdmin(admin.ModelAdmin):
    """Administration des bons de commande."""

    list_display = (
        'numero',
        'fournisseur',
        'date_creation',
        'montant_total_ttc',
        'statut_badge',
        'date_emission',
    )

    list_filter = (
        'statut',
        'fournisseur',
        'date_creation',
        'date_emission',
    )

    search_fields = (
        'numero',
        'fournisseur__raison_sociale',
        'demande_achat__numero',
    )

    readonly_fields = (
        'uuid',
        'numero',
        'montant_total_ht',
        'montant_total_tva',
        'montant_total_ttc',
        'date_creation',
        'date_modification',
        'date_emission',
        'date_envoi',
    )

    inlines = [GACLigneBonCommandeInline]

    def statut_badge(self, obj):
        """Badge pour le statut."""
        colors = {
            'BROUILLON': 'gray',
            'EMIS': 'blue',
            'ENVOYE': 'orange',
            'CONFIRME': 'green',
            'RECU_PARTIEL': 'purple',
            'RECU_COMPLET': 'darkgreen',
            'ANNULE': 'red',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.statut, 'gray'),
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'


@admin.register(GACLigneBonCommande)
class GACLigneBonCommandeAdmin(admin.ModelAdmin):
    """Administration des lignes de bon de commande."""

    list_display = (
        'bon_commande',
        'article',
        'quantite_commandee',
        'quantite_recue',
        'prix_unitaire',
        'montant_ttc',
    )

    search_fields = (
        'bon_commande__numero',
        'article__designation',
    )

    readonly_fields = (
        'uuid',
        'montant',
        'montant_ttc',
    )


# ==============================================================================
# RÉCEPTIONS
# ==============================================================================

class GACLigneReceptionInline(admin.TabularInline):
    """Inline pour les lignes de réception."""
    model = GACLigneReception
    extra = 0
    fields = (
        'ligne_bon_commande',
        'quantite_recue',
        'quantite_acceptee',
        'quantite_refusee',
        'motif_refus',
    )
    readonly_fields = ('ligne_bon_commande',)


@admin.register(GACReception)
class GACReceptionAdmin(admin.ModelAdmin):
    """Administration des réceptions."""

    list_display = (
        'numero',
        'bon_commande',
        'date_reception',
        'receptionnaire',
        'statut_badge',
        'date_creation',
    )

    list_filter = (
        'statut',
        'date_reception',
        'date_creation',
    )

    search_fields = (
        'numero',
        'bon_commande__numero',
        'bon_livraison_fournisseur',
    )

    readonly_fields = (
        'uuid',
        'numero',
        'date_creation',
        'date_modification',
        'date_validation',
    )

    inlines = [GACLigneReceptionInline]

    def statut_badge(self, obj):
        """Badge pour le statut."""
        colors = {
            'BROUILLON': 'gray',
            'VALIDEE': 'green',
            'ANNULEE': 'red',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.statut, 'gray'),
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'


@admin.register(GACLigneReception)
class GACLigneReceptionAdmin(admin.ModelAdmin):
    """Administration des lignes de réception."""

    list_display = (
        'reception',
        'ligne_bon_commande',
        'quantite_recue',
        'quantite_acceptee',
        'quantite_refusee',
    )

    search_fields = (
        'reception__numero',
        'ligne_bon_commande__article__designation',
    )


# ==============================================================================
# BONS DE RETOUR
# ==============================================================================

class GACLigneBonRetourInline(admin.TabularInline):
    """Inline pour les lignes de bon de retour."""
    model = GACLigneBonRetour
    extra = 0
    fields = (
        'ligne_reception',
        'quantite_retournee',
        'motif_retour',
    )


@admin.register(GACBonRetour)
class GACBonRetourAdmin(admin.ModelAdmin):
    """Administration des bons de retour."""

    list_display = (
        'numero',
        'reception',
        'date_creation',
        'statut_badge',
    )

    list_filter = (
        'statut',
        'date_creation',
    )

    search_fields = (
        'numero',
        'reception__numero',
    )

    readonly_fields = (
        'uuid',
        'numero',
        'date_creation',
    )

    inlines = [GACLigneBonRetourInline]

    def statut_badge(self, obj):
        """Badge pour le statut."""
        colors = {
            'BROUILLON': 'gray',
            'SOUMIS': 'blue',
            'ACCEPTE': 'green',
            'REFUSE': 'red',
            'TRAITE': 'purple',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.statut, 'gray'),
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'


@admin.register(GACLigneBonRetour)
class GACLigneBonRetourAdmin(admin.ModelAdmin):
    """Administration des lignes de bon de retour."""

    list_display = (
        'bon_retour',
        'ligne_reception',
        'quantite_retournee',
        'motif_retour',
    )

    search_fields = (
        'bon_retour__numero',
        'motif_retour',
    )

    readonly_fields = (
        'uuid',
    )


# ==============================================================================
# PIÈCES JOINTES
# ==============================================================================

@admin.register(GACPieceJointe)
class GACPieceJointeAdmin(admin.ModelAdmin):
    """Administration des pièces jointes."""

    list_display = (
        'nom_fichier',
        'content_type',
        'object_id',
        'type_fichier',
        'taille_fichier_display',
        'date_ajout',
    )

    list_filter = (
        'type_fichier',
        'content_type',
        'date_ajout',
    )

    search_fields = (
        'nom_fichier',
        'description',
    )

    readonly_fields = (
        'uuid',
        'date_ajout',
        'taille_fichier',
    )

    def taille_fichier_display(self, obj):
        """Affichage formaté de la taille du fichier."""
        if not obj.taille_fichier:
            return '-'

        taille = obj.taille_fichier
        for unite in ['o', 'Ko', 'Mo', 'Go']:
            if taille < 1024.0:
                return f"{taille:.2f} {unite}"
            taille /= 1024.0
        return f"{taille:.2f} To"
    taille_fichier_display.short_description = 'Taille'


# ==============================================================================
# HISTORIQUE
# ==============================================================================

@admin.register(GACHistorique)
class GACHistoriqueAdmin(admin.ModelAdmin):
    """Administration de l'historique."""

    list_display = (
        'date_action',
        'utilisateur',
        'action',
        'content_type',
        'object_id',
    )

    list_filter = (
        'action',
        'content_type',
        'date_action',
    )

    search_fields = (
        'utilisateur__nom',
        'utilisateur__prenom',
        'details',
    )

    readonly_fields = (
        'uuid',
        'date_action',
        'utilisateur',
        'action',
        'content_type',
        'object_id',
        'details',
    )

    def has_add_permission(self, request):
        """Empêcher l'ajout manuel d'historique."""
        return False

    def has_change_permission(self, request, obj=None):
        """Empêcher la modification de l'historique."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression de l'historique."""
        return False


# ==============================================================================
# PARAMÈTRES
# ==============================================================================

@admin.register(GACParametres)
class GACParametresAdmin(admin.ModelAdmin):
    """Administration des paramètres."""

    list_display = (
        'id',
        'seuil_validation_n2',
        'delai_livraison_defaut',
    )

    readonly_fields = (
        'date_creation',
        'date_modification',
    )

    def has_add_permission(self, request):
        """Permettre l'ajout seulement s'il n'y a pas de paramètres."""
        return not GACParametres.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression des paramètres."""
        return False
