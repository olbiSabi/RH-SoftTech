from django.contrib import admin
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA
from django.utils.html import format_html
from django.urls import reverse

# ===============================
# ADMIN INLINES
# ===============================

class ZYCOInline(admin.TabularInline):
    """Contrats inline dans l'admin employé"""
    model = ZYCO
    extra = 0
    fields = ('type_contrat', 'date_debut', 'date_fin', 'actif')
    readonly_fields = ('actif',)


class ZYTEInline(admin.TabularInline):
    """Téléphones inline dans l'admin employé"""
    model = ZYTE
    extra = 0
    fields = ('numero', 'date_debut_validite', 'date_fin_validite', 'actif')
    readonly_fields = ('actif',)


class ZYMEInline(admin.TabularInline):
    """Emails inline dans l'admin employé"""
    model = ZYME
    extra = 0
    fields = ('email', 'date_debut_validite', 'date_fin_validite', 'actif')
    readonly_fields = ('actif',)


class ZYAFInline(admin.TabularInline):
    """Affectations inline dans l'admin employé"""
    model = ZYAF
    extra = 0
    fields = ('poste', 'date_debut', 'date_fin', 'actif')
    readonly_fields = ('actif',)


class ZYADInline(admin.TabularInline):
    """Adresses inline dans l'admin employé"""
    model = ZYAD
    extra = 0
    fields = ('type_adresse', 'rue', 'ville', 'pays', 'date_debut', 'date_fin', 'actif')
    readonly_fields = ('actif',)


class ZYDOInline(admin.TabularInline):
    """Documents inline dans l'admin employé"""
    model = ZYDO
    extra = 0
    fields = ('type_document', 'fichier', 'description', 'date_ajout')
    readonly_fields = ('date_ajout',)


class ZYFAInline(admin.TabularInline):
    """Personnes à charge inline dans l'admin employé"""
    model = ZYFA
    extra = 0
    fields = ('personne_charge', 'nom', 'prenom', 'sexe', 'date_naissance', 'actif')
    readonly_fields = ('actif',)


# ===============================
# ADMIN MODEL ADMINS
# ===============================

@admin.register(ZY00)
class ZY00Admin(admin.ModelAdmin):
    """Admin pour les employés (ZY00)"""
    list_display = (
        'matricule',
        'nom_complet',
        'type_dossier_display',
        'etat_display',
        'photo_preview'
    )
    list_filter = (
        'type_dossier',
        'etat',
        'sexe',
        'situation_familiale'
    )
    search_fields = (
        'matricule',
        'nom',
        'prenoms',
        'ville_naissance',
        'pays_naissance'
    )
    readonly_fields = (
        'matricule',
        'uuid',
        'photo_preview'
    )
    fieldsets = (
        ('Informations Personnelles', {
            'fields': (
                'photo_preview',
                'photo',
                'nom',
                'prenoms',
                'date_naissance',
                'sexe',
                'situation_familiale'
            )
        }),
        ('Lieu de Naissance', {
            'fields': (
                'ville_naissance',
                'pays_naissance',
            )
        }),
        ('Pièce d\'Identité', {
            'fields': (
                'type_id',
                'numero_id',
                'date_validite_id',
                'date_expiration_id'
            )
        }),
        ('Informations Administratives', {
            'fields': (
                'type_dossier',
                'etat',
                'date_validation_embauche'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'matricule',
                'uuid'
            ),
            'classes': ('collapse',)
        }),
    )
    inlines = [
        ZYCOInline,
        ZYTEInline,
        ZYMEInline,
        ZYAFInline,
        ZYADInline,
        ZYDOInline,
        ZYFAInline,
    ]

    def nom_complet(self, obj):
        return f"{obj.nom} {obj.prenoms}"
    nom_complet.short_description = 'Nom complet'

    def type_dossier_display(self, obj):
        return obj.get_type_dossier_display()
    type_dossier_display.short_description = 'Type dossier'

    def etat_display(self, obj):
        return obj.get_etat_display()
    etat_display.short_description = 'État'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 5px;" />',
                obj.photo.url
            )
        return "Aucune photo"
    photo_preview.short_description = 'Photo'


@admin.register(ZYFA)
class ZYFAAdmin(admin.ModelAdmin):
    """Admin pour les personnes à charge (Famille)"""
    list_display = (
        'employe',
        'personne_charge_display',
        'nom_complet',
        'sexe_display',
        'date_naissance',
        'date_debut_prise_charge',
        'actif_status'
    )
    list_filter = (
        'personne_charge',
        'sexe',
        'actif',
        'date_naissance',
        'date_debut_prise_charge'
    )
    search_fields = (
        'employe__nom',
        'employe__prenoms',
        'employe__matricule',
        'nom',
        'prenom'
    )
    fieldsets = (
        ('Informations Personnelles', {
            'fields': (
                'employe',
                'personne_charge',
                'nom',
                'prenom',
                'sexe',
                'date_naissance'
            )
        }),
        ('Prise en Charge', {
            'fields': (
                'date_debut_prise_charge',
                'date_fin_prise_charge',
                'actif'
            )
        }),
    )

    def employe_display(self, obj):
        return f"{obj.employe.nom} {obj.employe.prenoms} ({obj.employe.matricule})"
    employe_display.short_description = 'Employé'

    def personne_charge_display(self, obj):
        icons = {
            'ENFANT': '👶',
            'CONJOINT': '💑',
            'PARENT': '👵',
            'AUTRE': '👤',
        }
        icon = icons.get(obj.personne_charge, '👤')
        return f"{icon} {obj.get_personne_charge_display()}"
    personne_charge_display.short_description = 'Type'

    def nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}"
    nom_complet.short_description = 'Nom complet'

    def sexe_display(self, obj):
        return obj.get_sexe_display()
    sexe_display.short_description = 'Sexe'

    def actif_status(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: red;">● Inactif</span>')
    actif_status.short_description = 'Statut'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employe')


@admin.register(ZYCO)
class ZYCOAdmin(admin.ModelAdmin):
    """Admin pour les contrats"""
    list_display = (
        'employe',
        'type_contrat_display',
        'date_debut',
        'date_fin',
        'duree_contrat',
        'actif_status'
    )
    list_filter = (
        'type_contrat',
        'date_debut',
        'date_fin'
    )
    search_fields = (
        'employe__nom',
        'employe__prenoms',
        'employe__matricule'
    )

    def employe_display(self, obj):
        return f"{obj.employe.nom} {obj.employe.prenoms}"
    employe_display.short_description = 'Employé'

    def type_contrat_display(self, obj):
        return obj.get_type_contrat_display()
    type_contrat_display.short_description = 'Type de contrat'

    def duree_contrat(self, obj):
        if obj.date_fin:
            return f"{(obj.date_fin - obj.date_debut).days} jours"
        return "En cours"
    duree_contrat.short_description = 'Durée'

    def actif_status(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: red;">● Inactif</span>')
    actif_status.short_description = 'Statut'


@admin.register(ZYTE)
class ZYTEAdmin(admin.ModelAdmin):
    """Admin pour les téléphones"""
    list_display = (
        'employe',
        'numero',
        'date_debut_validite',
        'date_fin_validite',
        'actif_status'
    )
    list_filter = (
        'actif',
        'date_debut_validite',
        'date_fin_validite'
    )
    search_fields = (
        'employe__nom',
        'employe__prenoms',
        'numero'
    )

    def employe_display(self, obj):
        return f"{obj.employe.nom} {obj.employe.prenoms}"
    employe_display.short_description = 'Employé'

    def actif_status(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: red;">● Inactif</span>')
    actif_status.short_description = 'Statut'


@admin.register(ZYME)
class ZYMEAdmin(admin.ModelAdmin):
    """Admin pour les emails"""
    list_display = (
        'employe',
        'email',
        'date_debut_validite',
        'date_fin_validite',
        'actif_status'
    )
    list_filter = (
        'actif',
        'date_debut_validite',
        'date_fin_validite'
    )
    search_fields = (
        'employe__nom',
        'employe__prenoms',
        'email'
    )

    def employe_display(self, obj):
        return f"{obj.employe.nom} {obj.employe.prenoms}"
    employe_display.short_description = 'Employé'

    def actif_status(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: red;">● Inactif</span>')
    actif_status.short_description = 'Statut'


@admin.register(ZYAF)
class ZYAFAdmin(admin.ModelAdmin):
    """Admin pour les affectations"""
    list_display = (
        'employe',
        'poste_display',
        'departement_display',
        'date_debut',
        'date_fin',
        'actif_status'
    )
    list_filter = (
        'poste__DEPARTEMENT',
        'actif',
        'date_debut',
        'date_fin'
    )
    search_fields = (
        'employe__nom',
        'employe__prenoms',
        'poste__LIBELLE',
        'poste__DEPARTEMENT__LIBELLE'
    )

    def employe_display(self, obj):
        return f"{obj.employe.nom} {obj.employe.prenoms}"
    employe_display.short_description = 'Employé'

    def poste_display(self, obj):
        return obj.poste.LIBELLE
    poste_display.short_description = 'Poste'

    def departement_display(self, obj):
        return obj.poste.DEPARTEMENT.LIBELLE
    departement_display.short_description = 'Département'

    def actif_status(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: red;">● Inactif</span>')
    actif_status.short_description = 'Statut'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employe', 'poste', 'poste__DEPARTEMENT')


@admin.register(ZYAD)
class ZYADAdmin(admin.ModelAdmin):
    """Admin pour les adresses"""
    list_display = (
        'employe',
        'type_adresse_display',
        'adresse_complete',
        'date_debut',
        'date_fin',
        'actif_status'
    )
    list_filter = (
        'type_adresse',
        'pays',
        'actif',
        'date_debut',
        'date_fin'
    )
    search_fields = (
        'employe__nom',
        'employe__prenoms',
        'rue',
        'ville',
        'pays'
    )

    def employe_display(self, obj):
        return f"{obj.employe.nom} {obj.employe.prenoms}"
    employe_display.short_description = 'Employé'

    def type_adresse_display(self, obj):
        return obj.get_type_adresse_display()
    type_adresse_display.short_description = 'Type'

    def adresse_complete(self, obj):
        return f"{obj.rue}, {obj.code_postal} {obj.ville}, {obj.pays}"
    adresse_complete.short_description = 'Adresse'

    def actif_status(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: red;">● Inactif</span>')
    actif_status.short_description = 'Statut'



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



# ===============================
# CUSTOMIZATION DE L'ADMIN
# ===============================

# Personnalisation du titre de l'admin
admin.site.site_header = "Gestion des Employés"