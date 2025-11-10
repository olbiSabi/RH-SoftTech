from django.contrib import admin
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD


class ZYCOInline(admin.TabularInline):
    """Inline pour les contrats"""
    model = ZYCO
    extra = 1
    fields = ['type_contrat', 'date_debut', 'date_fin', 'actif']


class ZYTEInline(admin.TabularInline):
    """Inline pour les téléphones"""
    model = ZYTE
    extra = 1
    fields = ['numero', 'date_debut_validite', 'date_fin_validite', 'actif']


class ZYMEInline(admin.TabularInline):
    """Inline pour les emails"""
    model = ZYME
    extra = 1
    fields = ['email', 'date_debut_validite', 'date_fin_validite', 'actif']


class ZYAFInline(admin.TabularInline):
    """Inline pour les affectations"""
    model = ZYAF
    extra = 1
    fields = ['poste', 'date_debut', 'date_fin', 'actif']


class ZYADInline(admin.TabularInline):
    """Inline pour les adresses"""
    model = ZYAD
    extra = 1
    fields = ['rue', 'ville', 'pays', 'code_postal', 'type_adresse', 'date_debut', 'date_fin', 'actif']


@admin.register(ZY00)
class ZY00Admin(admin.ModelAdmin):
    """Administration des employés"""
    list_display = [
        'matricule', 'nom', 'prenoms', 'date_naissance',
        'sexe', 'type_dossier', 'date_validation_embauche', 'etat'
    ]
    list_filter = ['type_dossier', 'sexe', 'situation_familiale']
    search_fields = ['matricule', 'nom', 'prenoms', 'numero_id']
    readonly_fields = ['matricule', 'uuid']

    fieldsets = (
        ('Identification', {
            'fields': ('matricule', 'uuid')
        }),
        ('Informations personnelles', {
            'fields': (
                'nom', 'prenoms', 'date_naissance', 'sexe',
                'ville_naissance', 'pays_naissance', 'situation_familiale'
            )
        }),
        ('Pièce d\'identité', {
            'fields': (
                'type_id', 'numero_id',
                'date_validite_id', 'date_expiration_id'
            )
        }),
        ('Statut', {
            'fields': ('type_dossier', 'date_validation_embauche')
        }),
    )

    inlines = [ZYCOInline, ZYTEInline, ZYMEInline, ZYAFInline, ZYADInline]

    def save_model(self, request, obj, form, change):
        """Validation de l'embauche automatique si demandé"""
        super().save_model(request, obj, form, change)


@admin.register(ZYCO)
class ZYCOAdmin(admin.ModelAdmin):
    """Administration des contrats"""
    list_display = ['employe', 'type_contrat', 'date_debut', 'date_fin', 'actif']
    list_filter = ['type_contrat', 'date_debut']
    search_fields = ['employe__matricule', 'employe__nom', 'employe__prenoms']
    date_hierarchy = 'date_debut'


@admin.register(ZYTE)
class ZYTEAdmin(admin.ModelAdmin):
    """Administration des téléphones"""
    list_display = ['employe', 'numero', 'date_debut_validite', 'date_fin_validite', 'actif']
    search_fields = ['employe__matricule', 'employe__nom', 'numero']
    list_filter = ['date_debut_validite']


@admin.register(ZYME)
class ZYMEAdmin(admin.ModelAdmin):
    """Administration des emails"""
    list_display = ['employe', 'email', 'date_debut_validite', 'date_fin_validite', 'actif']
    search_fields = ['employe__matricule', 'employe__nom', 'email']
    list_filter = ['date_debut_validite']


@admin.register(ZYAF)
class ZYAFAdmin(admin.ModelAdmin):
    """Administration des affectations"""
    list_display = ['employe', 'poste', 'date_debut', 'date_fin', 'actif']
    list_filter = ['poste', 'date_debut']
    search_fields = ['employe__matricule', 'employe__nom', 'poste__libelle']
    date_hierarchy = 'date_debut'


@admin.register(ZYAD)
class ZYADAdmin(admin.ModelAdmin):
    """Administration des adresses"""
    list_display = ['employe', 'ville', 'pays', 'type_adresse', 'date_debut', 'date_fin', 'actif']
    list_filter = ['type_adresse', 'pays', 'ville']
    search_fields = ['employe__matricule', 'employe__nom', 'ville', 'rue']