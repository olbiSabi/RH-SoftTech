from django.contrib import admin
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO
from django.utils.html import format_html
from django.urls import reverse

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



@admin.register(ZYDO)
class ZYDOAdmin(admin.ModelAdmin):
    """Administration des documents"""

    list_display = [
        'id',
        'employe_link',
        'type_document_badge',
        'get_nom_fichier_display',
        'get_taille_fichier_display',
        'date_ajout',
        'actif_status',
        'action_buttons',
    ]

    list_filter = [
        'type_document',
        'actif',
        'date_ajout',
        ('employe', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'employe__matricule',
        'employe__nom',
        'employe__prenoms',
        'description',
    ]

    readonly_fields = [
        'date_ajout',
        'date_modification',
        'taille_fichier',
        'get_extension_display',
        'get_taille_fichier_display',
        'fichier_preview',
    ]

    fieldsets = (
        ('Informations employé', {
            'fields': ('employe',)
        }),
        ('Informations document', {
            'fields': ('type_document', 'description', 'fichier', 'fichier_preview')
        }),
        ('Informations techniques', {
            'fields': (
                'taille_fichier',
                'get_extension_display',
                'get_taille_fichier_display',
                'date_ajout',
                'date_modification',
            ),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )

    list_per_page = 25
    date_hierarchy = 'date_ajout'

    def employe_link(self, obj):
        """Lien vers l'employé"""
        url = reverse('admin:employee_zy00_change', args=[obj.employe.matricule])
        return format_html(
            '<a href="{}">{} - {} {}</a>',
            url,
            obj.employe.matricule,
            obj.employe.nom,
            obj.employe.prenoms
        )

    employe_link.short_description = "Employé"

    def type_document_badge(self, obj):
        """Badge coloré pour le type de document"""
        colors = {
            'CV': '#007bff',
            'DIPLOME': '#28a745',
            'CNI': '#dc3545',
            'PASSEPORT': '#dc3545',
            'RIB': '#ffc107',
        }
        color = colors.get(obj.type_document, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_type_document_display()
        )

    type_document_badge.short_description = "Type"

    def actif_status(self, obj):
        """Badge pour le statut actif/inactif"""
        if obj.actif:
            return format_html(
                '<span style="color: green;">✓ Actif</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inactif</span>'
            )

    actif_status.short_description = "Statut"

    def get_nom_fichier_display(self, obj):
        """Affiche le nom du fichier"""
        return obj.get_nom_fichier()

    get_nom_fichier_display.short_description = "Nom du fichier"

    def get_taille_fichier_display(self, obj):
        """Affiche la taille du fichier de manière lisible"""
        return obj.get_taille_lisible()

    get_taille_fichier_display.short_description = "Taille"

    def get_extension_display(self, obj):
        """Affiche l'extension du fichier"""
        return obj.get_extension().upper()

    get_extension_display.short_description = "Extension"

    def fichier_preview(self, obj):
        """Prévisualisation du fichier (pour les images)"""
        if obj.fichier:
            ext = obj.get_extension()
            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                return format_html(
                    '<a href="{}" target="_blank"><img src="{}" style="max-width: 200px; max-height: 200px;" /></a>',
                    obj.fichier.url,
                    obj.fichier.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank" class="button">📄 Télécharger le fichier</a>',
                    obj.fichier.url
                )
        return "-"

    fichier_preview.short_description = "Aperçu"

    def action_buttons(self, obj):
        """Boutons d'action"""
        if obj.fichier:
            return format_html(
                '<a class="button" href="{}" target="_blank">📥 Télécharger</a>',
                obj.fichier.url
            )
        return "-"

    action_buttons.short_description = "Actions"

    actions = ['desactiver_documents', 'activer_documents', 'exporter_liste']

    def desactiver_documents(self, request, queryset):
        """Action pour désactiver plusieurs documents"""
        count = queryset.update(actif=False)
        self.message_user(request, f"{count} document(s) désactivé(s) avec succès.")

    desactiver_documents.short_description = "Désactiver les documents sélectionnés"

    def activer_documents(self, request, queryset):
        """Action pour activer plusieurs documents"""
        count = queryset.update(actif=True)
        self.message_user(request, f"{count} document(s) activé(s) avec succès.")

    activer_documents.short_description = "Activer les documents sélectionnés"

    def exporter_liste(self, request, queryset):
        """Exporter la liste des documents sélectionnés"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="documents_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['Matricule', 'Employé', 'Type', 'Fichier', 'Taille', 'Date', 'Actif'])

        for doc in queryset:
            writer.writerow([
                doc.employe.matricule,
                f"{doc.employe.nom} {doc.employe.prenoms}",
                doc.get_type_document_display(),
                doc.get_nom_fichier(),
                doc.get_taille_lisible(),
                doc.date_ajout.strftime('%d/%m/%Y %H:%M'),
                'Oui' if doc.actif else 'Non'
            ])

        return response

    exporter_liste.short_description = "Exporter la liste en CSV"