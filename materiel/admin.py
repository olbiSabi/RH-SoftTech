from django.contrib import admin
from materiel.models import MTCA, MTFO, MTMT, MTAF, MTMV, MTMA


@admin.register(MTCA)
class MTCAAdmin(admin.ModelAdmin):
    list_display = ['CODE', 'LIBELLE', 'DUREE_AMORTISSEMENT', 'STATUT', 'ORDRE']
    list_filter = ['STATUT']
    search_fields = ['CODE', 'LIBELLE']
    ordering = ['ORDRE', 'LIBELLE']


@admin.register(MTFO)
class MTFOAdmin(admin.ModelAdmin):
    list_display = ['CODE', 'RAISON_SOCIALE', 'CONTACT', 'TELEPHONE', 'EMAIL', 'STATUT']
    list_filter = ['STATUT']
    search_fields = ['CODE', 'RAISON_SOCIALE', 'CONTACT']


@admin.register(MTMT)
class MTMTAdmin(admin.ModelAdmin):
    list_display = ['CODE_INTERNE', 'DESIGNATION', 'CATEGORIE', 'MARQUE', 'ETAT', 'STATUT', 'AFFECTE_A']
    list_filter = ['CATEGORIE', 'ETAT', 'STATUT', 'FOURNISSEUR']
    search_fields = ['CODE_INTERNE', 'DESIGNATION', 'NUMERO_SERIE', 'MARQUE', 'MODELE']
    date_hierarchy = 'DATE_ACQUISITION'
    raw_id_fields = ['AFFECTE_A', 'CREATED_BY']


@admin.register(MTAF)
class MTAFAdmin(admin.ModelAdmin):
    list_display = ['MATERIEL', 'EMPLOYE', 'TYPE_AFFECTATION', 'DATE_DEBUT', 'DATE_FIN', 'ACTIF']
    list_filter = ['TYPE_AFFECTATION', 'ACTIF']
    search_fields = ['MATERIEL__CODE_INTERNE', 'EMPLOYE__nom', 'EMPLOYE__prenoms']
    date_hierarchy = 'DATE_DEBUT'
    raw_id_fields = ['MATERIEL', 'EMPLOYE', 'AFFECTE_PAR', 'RETOUR_PAR']


@admin.register(MTMV)
class MTMVAdmin(admin.ModelAdmin):
    list_display = ['REFERENCE', 'MATERIEL', 'TYPE_MOUVEMENT', 'DATE_MOUVEMENT', 'EFFECTUE_PAR']
    list_filter = ['TYPE_MOUVEMENT']
    search_fields = ['REFERENCE', 'MATERIEL__CODE_INTERNE']
    date_hierarchy = 'DATE_MOUVEMENT'
    raw_id_fields = ['MATERIEL', 'EFFECTUE_PAR']


@admin.register(MTMA)
class MTMAAdmin(admin.ModelAdmin):
    list_display = ['REFERENCE', 'MATERIEL', 'TYPE_MAINTENANCE', 'DATE_PLANIFIEE', 'STATUT', 'cout_total']
    list_filter = ['TYPE_MAINTENANCE', 'STATUT', 'PRESTATAIRE']
    search_fields = ['REFERENCE', 'MATERIEL__CODE_INTERNE', 'DESCRIPTION']
    date_hierarchy = 'DATE_PLANIFIEE'
    raw_id_fields = ['MATERIEL', 'PRESTATAIRE', 'INTERVENANT_INTERNE', 'DEMANDE_PAR']
