from django.contrib import admin
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA, ZYNP, ZYPP, ZYIB, ZYRO, ZYRE
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

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


class ZYNPInline(admin.TabularInline):
    """Historique noms/prénoms inline dans l'admin employé"""
    model = ZYNP
    extra = 0
    fields = ('nom', 'prenoms', 'date_debut_validite', 'date_fin_validite', 'actif_status')
    readonly_fields = ('actif_status',)
    ordering = ['-date_debut_validite']

    def actif_status(self, obj):
        if obj.actif and not obj.date_fin_validite:
            return format_html('<span style="color: green; font-weight: bold;">● Actuel</span>')
        elif obj.actif:
            return format_html('<span style="color: orange;">● Futur</span>')
        else:
            return format_html('<span style="color: red;">● Passé</span>')

    actif_status.short_description = 'Statut'


class ZYPPInline(admin.TabularInline):
    """Inline pour afficher les personnes à prévenir dans l'admin de ZY00"""
    model = ZYPP
    extra = 0
    max_num = 3  # Maximum 3 contacts (un par priorité)

    fields = [
        'ordre_priorite',
        'prenom',
        'nom',
        'lien_parente',
        'telephone_principal',
        'telephone_secondaire',
        'actif',
    ]

    readonly_fields = []

    classes = ['collapse']

    verbose_name = "Personne à prévenir en cas d'urgence"
    verbose_name_plural = "Personnes à prévenir en cas d'urgence"

    def get_queryset(self, request):
        """Affiche uniquement les contacts actifs par défaut"""
        qs = super().get_queryset(request)
        return qs.filter(actif=True, date_fin_validite__isnull=True).order_by('ordre_priorite')

# ===============================
# ADMIN MODEL ADMINS
# ===============================

@admin.register(ZY00)
class ZY00Admin(admin.ModelAdmin):
    """Admin pour les employés (ZY00)"""
    list_display = (
        'matricule',
        'username',
        'prenomuser',
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
        'username',
        'prenomuser',
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


@admin.register(ZYNP)
class ZYNPAdmin(admin.ModelAdmin):
    """Admin pour l'historique des noms et prénoms"""
    list_display = (
        'employe_display',
        'nom_complet_historique',
        'date_debut_validite',
        'date_fin_validite',
        'statut_actif',
        'duree_validite',
        'employe_link'
    )
    list_filter = (
        'actif',
        'date_debut_validite',
        'date_fin_validite',
        'employe__type_dossier'
    )
    search_fields = (
        'nom',
        'prenoms',
        'employe__matricule',
        'employe__nom',
        'employe__prenoms'
    )
    readonly_fields = (
        'date_creation',
        'employe_link',
        'informations_employe'
    )
    fieldsets = (
        ('Informations Employé', {
            'fields': ('employe_link', 'employe', 'informations_employe')
        }),
        ('Historique Nom/Prénom', {
            'fields': (
                'nom',
                'prenoms',
                'date_debut_validite',
                'date_fin_validite',
                'actif'
            )
        }),
        ('Dates Techniques', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        })
    )

    def employe_display(self, obj):
        return f"{obj.employe.matricule}"
    employe_display.short_description = 'Matricule'
    employe_display.admin_order_field = 'employe__matricule'

    def nom_complet_historique(self, obj):
        return f"{obj.nom} {obj.prenoms}"
    nom_complet_historique.short_description = 'Nom Complet (Historique)'
    nom_complet_historique.admin_order_field = 'nom'

    def statut_actif(self, obj):
        if obj.actif and not obj.date_fin_validite:
            return format_html('<span style="color: green; font-weight: bold;">● Actuel</span>')
        elif obj.actif:
            return format_html('<span style="color: orange;">● Futur</span>')
        else:
            return format_html('<span style="color: red;">● Passé</span>')
    statut_actif.short_description = 'Statut'

    def employe_link(self, obj):
        if obj.employe:
            url = reverse('admin:employee_zy00_change', args=[obj.employe.matricule])
            return format_html(
                '<a href="{}"><strong>{} - {} {}</strong></a>',
                url,
                obj.employe.matricule,
                obj.employe.username or obj.employe.nom,
                obj.employe.prenomuser or obj.employe.prenoms
            )
        return "-"
    employe_link.short_description = 'Employé'

    def informations_employe(self, obj):
        if obj.employe:
            return format_html(
                """
                <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                    <strong>Informations actuelles de l'employé :</strong><br>
                    • Nom affiché: <strong>{} {}</strong><br>
                    • Nom original: {} {}<br>
                    • Type dossier: {}<br>
                    • État: {}
                </div>
                """,
                obj.employe.username or obj.employe.nom,
                obj.employe.prenomuser or obj.employe.prenoms,
                obj.employe.nom,
                obj.employe.prenoms,
                obj.employe.get_type_dossier_display(),
                obj.employe.get_etat_display()
            )
        return "-"
    informations_employe.short_description = 'État actuel'

    def duree_validite(self, obj):
        if obj.date_fin_validite:
            jours = (obj.date_fin_validite - obj.date_debut_validite).days
            return format_html(
                "{} → {}<br><small>({} jours)</small>",
                obj.date_debut_validite.strftime("%d/%m/%Y"),
                obj.date_fin_validite.strftime("%d/%m/%Y"),
                jours
            )
        else:
            jours_ecoules = (timezone.now().date() - obj.date_debut_validite).days
            return format_html(
                "Depuis {}<br><small>({} jours)</small>",
                obj.date_debut_validite.strftime("%d/%m/%Y"),
                jours_ecoules
            )
    duree_validite.short_description = 'Période'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employe')

    # Actions personnalisées
    actions = ['desactiver_historiques', 'activer_historiques']

    def desactiver_historiques(self, request, queryset):
        """Action pour désactiver les historiques sélectionnés"""
        updated = queryset.update(actif=False)
        self.message_user(request, f"{updated} historique(s) désactivé(s) avec succès.")
    desactiver_historiques.short_description = "Désactiver les historiques sélectionnés"

    def activer_historiques(self, request, queryset):
        """Action pour activer les historiques sélectionnés"""
        updated = queryset.update(actif=True)
        self.message_user(request, f"{updated} historique(s) activé(s) avec succès.")
    activer_historiques.short_description = "Activer les historiques sélectionnés"


@admin.register(ZYPP)
class ZYPPAdmin(admin.ModelAdmin):
    """Administration des personnes à prévenir en cas d'urgence"""

    list_display = [
        'get_employe_info',
        'get_nom_complet',
        'lien_parente',
        'telephone_principal',
        'get_ordre_priorite_display',
        'get_statut',
        'date_debut_validite',
        'date_fin_validite',
    ]

    list_filter = [
        'lien_parente',
        'ordre_priorite',
        'actif',
        'date_debut_validite',
        'employe__type_dossier',
    ]

    search_fields = [
        'nom',
        'prenom',
        'telephone_principal',
        'telephone_secondaire',
        'email',
        'employe__matricule',
        'employe__nom',
        'employe__prenoms',
    ]

    readonly_fields = [
        'date_creation',
        'date_modification',
        'get_nom_complet',
        'get_telephones_display',
        'get_statut_actuel',
    ]

    fieldsets = (
        ('👤 Employé Concerné', {
            'fields': ('employe',)
        }),
        ('📋 Informations Personnelles', {
            'fields': (
                'nom',
                'prenom',
                'get_nom_complet',
                'lien_parente',
            )
        }),
        ('📞 Coordonnées', {
            'fields': (
                'telephone_principal',
                'telephone_secondaire',
                'get_telephones_display',
                'email',
                'adresse',
            )
        }),
        ('⚠️ Informations d\'Urgence', {
            'fields': (
                'ordre_priorite',
                'remarques',
            ),
            'description': 'Priorité de contact en cas d\'urgence'
        }),
        ('📅 Période de Validité', {
            'fields': (
                'date_debut_validite',
                'date_fin_validite',
                'actif',
                'get_statut_actuel',
            )
        }),
        ('ℹ️ Métadonnées', {
            'fields': (
                'date_creation',
                'date_modification',
            ),
            'classes': ('collapse',)
        }),
    )

    autocomplete_fields = ['employe']

    date_hierarchy = 'date_debut_validite'

    ordering = ['employe__matricule', 'ordre_priorite', '-date_debut_validite']

    list_per_page = 25

    actions = [
        'activer_contacts',
        'desactiver_contacts',
        'cloturer_contacts',
    ]

    # ===== MÉTHODES D'AFFICHAGE =====

    @admin.display(description='Employé', ordering='employe__matricule')
    def get_employe_info(self, obj):
        """Affiche les informations de l'employé"""
        return f"{obj.employe.matricule} - {obj.employe.username} {obj.employe.prenomuser}"

    @admin.display(description='Nom Complet')
    def get_nom_complet(self, obj):
        """Affiche le nom complet de la personne à prévenir"""
        return f"{obj.prenom} {obj.nom}"

    @admin.display(description='Priorité', ordering='ordre_priorite')
    def get_ordre_priorite_display(self, obj):
        """Affiche la priorité avec icône"""
        icons = {
            1: '🔴',  # Contact principal
            2: '🟠',  # Contact secondaire
            3: '🟡',  # Contact tertiaire
        }
        icon = icons.get(obj.ordre_priorite, '⚪')
        return f"{icon} {obj.get_ordre_priorite_display()}"

    @admin.display(description='Statut', boolean=True)
    def get_statut(self, obj):
        """Indique si le contact est actuellement actif"""
        return obj.est_actif()

    @admin.display(description='Téléphones')
    def get_telephones_display(self, obj):
        """Affiche tous les téléphones disponibles"""
        telephones = [f"📞 Principal: {obj.telephone_principal}"]
        if obj.telephone_secondaire:
            telephones.append(f"📱 Secondaire: {obj.telephone_secondaire}")
        return " | ".join(telephones)

    @admin.display(description='Statut Actuel')
    def get_statut_actuel(self, obj):
        """Affiche le statut détaillé du contact"""
        from django.utils import timezone
        today = timezone.now().date()

        if not obj.actif:
            return "❌ Désactivé"

        if obj.date_fin_validite and obj.date_fin_validite < today:
            return "⏹️ Clôturé"

        if obj.date_debut_validite > today:
            return f"⏳ Débute le {obj.date_debut_validite.strftime('%d/%m/%Y')}"

        if obj.date_fin_validite:
            return f"✅ Actif jusqu'au {obj.date_fin_validite.strftime('%d/%m/%Y')}"

        return "✅ Actif (sans date de fin)"

    # ===== ACTIONS PERSONNALISÉES =====

    @admin.action(description='✅ Activer les contacts sélectionnés')
    def activer_contacts(self, request, queryset):
        """Active les contacts sélectionnés"""
        updated = queryset.update(actif=True)
        self.message_user(
            request,
            f"{updated} contact(s) activé(s) avec succès.",
            level='success'
        )

    @admin.action(description='❌ Désactiver les contacts sélectionnés')
    def desactiver_contacts(self, request, queryset):
        """Désactive les contacts sélectionnés"""
        updated = queryset.update(actif=False)
        self.message_user(
            request,
            f"{updated} contact(s) désactivé(s) avec succès.",
            level='warning'
        )

    @admin.action(description='⏹️ Clôturer les contacts sélectionnés (ajouter date de fin)')
    def cloturer_contacts(self, request, queryset):
        """Clôture les contacts en ajoutant la date du jour comme date de fin"""
        from django.utils import timezone
        today = timezone.now().date()

        contacts_actifs = queryset.filter(date_fin_validite__isnull=True)
        updated = contacts_actifs.update(date_fin_validite=today)

        self.message_user(
            request,
            f"{updated} contact(s) clôturé(s) avec la date du {today.strftime('%d/%m/%Y')}.",
            level='success'
        )

    # ===== MÉTHODES DE VALIDATION =====

    def save_model(self, request, obj, form, change):
        """Validation lors de la sauvegarde"""
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)

            if change:
                self.message_user(
                    request,
                    f"✅ Contact d'urgence pour {obj.employe.nom} modifié avec succès.",
                    level='success'
                )
            else:
                self.message_user(
                    request,
                    f"✅ Contact d'urgence pour {obj.employe.nom} créé avec succès.",
                    level='success'
                )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Erreur: {str(e)}",
                level='error'
            )

    def get_queryset(self, request):
        """Optimise les requêtes avec select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('employe')

    # ===== PERMISSIONS PERSONNALISÉES =====

    def has_delete_permission(self, request, obj=None):
        """Contrôle les permissions de suppression"""
        # Vous pouvez ajouter des règles personnalisées ici
        # Par exemple, empêcher la suppression des contacts actifs
        if obj and obj.est_actif():
            return False  # Ne pas permettre la suppression des contacts actifs
        return super().has_delete_permission(request, obj)


@admin.register(ZYIB)
class ZYIBAdmin(admin.ModelAdmin):
    """Administration des identités bancaires"""

    list_display = [
        'get_employe_info',
        'titulaire_compte',
        'nom_banque',
        'get_rib_display',
        'type_compte',
        'get_statut',
        'date_modification',
    ]

    list_filter = [
        'type_compte',
        'actif',
        'nom_banque',
        'date_ajout',
    ]

    search_fields = [
        'employe__matricule',
        'employe__nom',
        'employe__prenoms',
        'titulaire_compte',
        'nom_banque',
        'iban',
        'numero_compte',
    ]

    readonly_fields = [
        'date_ajout',
        'date_modification',
        'get_rib_complet',
        'get_iban_display',
        'get_validation_rib',
    ]

    fieldsets = (
        ('👤 Employé', {
            'fields': ('employe',)
        }),
        ('🏦 Informations Bancaires', {
            'fields': (
                'titulaire_compte',
                'nom_banque',
                'type_compte',
                'domiciliation',
                'date_ouverture',
            )
        }),
        ('📋 RIB', {
            'fields': (
                'code_banque',
                'code_guichet',
                'numero_compte',
                'cle_rib',
                'get_rib_complet',
                'get_validation_rib',
            ),
            'description': 'Relevé d\'Identité Bancaire'
        }),
        ('🌍 IBAN / BIC', {
            'fields': (
                'iban',
                'get_iban_display',
                'bic',
            ),
            'description': 'Identifiants bancaires internationaux'
        }),
        ('📝 Informations Complémentaires', {
            'fields': (
                'remarques',
                'actif',
            )
        }),
        ('ℹ️ Métadonnées', {
            'fields': (
                'date_ajout',
                'date_modification',
            ),
            'classes': ('collapse',)
        }),
    )

    autocomplete_fields = ['employe']

    date_hierarchy = 'date_modification'

    ordering = ['-date_modification']

    list_per_page = 25

    actions = [
        'activer_identites',
        'desactiver_identites',
        'valider_ribs',
    ]

    # ===== MÉTHODES D'AFFICHAGE =====

    @admin.display(description='Employé', ordering='employe__matricule')
    def get_employe_info(self, obj):
        """Affiche les informations de l'employé"""
        return f"{obj.employe.matricule} - {obj.employe.username} {obj.employe.prenomuser}"

    @admin.display(description='RIB')
    def get_rib_display(self, obj):
        """Affiche le RIB formaté"""
        return obj.get_rib()

    @admin.display(description='RIB Complet')
    def get_rib_complet(self, obj):
        """Affiche le RIB complet avec espaces"""
        return f"🏦 {obj.get_rib()}"

    @admin.display(description='IBAN Formaté')
    def get_iban_display(self, obj):
        """Affiche l'IBAN formaté"""
        if obj.iban:
            return f"🌍 {obj.get_iban_formate()}"
        return "-"

    @admin.display(description='Validation RIB', boolean=True)
    def get_validation_rib(self, obj):
        """Indique si le RIB est valide"""
        return obj.valider_rib()

    @admin.display(description='Statut', boolean=True)
    def get_statut(self, obj):
        """Indique si l'identité bancaire est active"""
        return obj.actif

    # ===== ACTIONS PERSONNALISÉES =====

    @admin.action(description='✅ Activer les identités bancaires sélectionnées')
    def activer_identites(self, request, queryset):
        """Active les identités bancaires sélectionnées"""
        updated = queryset.update(actif=True)
        self.message_user(
            request,
            f"{updated} identité(s) bancaire(s) activée(s) avec succès.",
            level='success'
        )

    @admin.action(description='❌ Désactiver les identités bancaires sélectionnées')
    def desactiver_identites(self, request, queryset):
        """Désactive les identités bancaires sélectionnées"""
        updated = queryset.update(actif=False)
        self.message_user(
            request,
            f"{updated} identité(s) bancaire(s) désactivée(s) avec succès.",
            level='warning'
        )

    @admin.action(description='🔍 Valider les RIB sélectionnés')
    def valider_ribs(self, request, queryset):
        """Valide les RIB sélectionnés"""
        valides = 0
        invalides = 0

        for ib in queryset:
            if ib.valider_rib():
                valides += 1
            else:
                invalides += 1

        self.message_user(
            request,
            f"✅ {valides} RIB valide(s) | ❌ {invalides} RIB invalide(s)",
            level='info'
        )

    # ===== MÉTHODES DE VALIDATION =====

    def save_model(self, request, obj, form, change):
        """Validation lors de la sauvegarde"""
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)

            if change:
                self.message_user(
                    request,
                    f"✅ Identité bancaire pour {obj.employe.nom} modifiée avec succès.",
                    level='success'
                )
            else:
                self.message_user(
                    request,
                    f"✅ Identité bancaire pour {obj.employe.nom} créée avec succès.",
                    level='success'
                )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Erreur: {str(e)}",
                level='error'
            )

    def get_queryset(self, request):
        """Optimise les requêtes avec select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('employe')


"""
Admin pour les rôles
À ajouter dans employee/admin.py
"""
@admin.register(ZYRO)
class ZYROAdmin(admin.ModelAdmin):
    """Admin pour les rôles"""

    list_display = [
        'CODE',
        'LIBELLE',
        'actif_badge',
        'nb_attributions',
        'permissions_display',
        'created_at'
    ]
    list_filter = ['actif', 'created_at']
    search_fields = ['CODE', 'LIBELLE', 'DESCRIPTION']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations principales', {
            'fields': ('CODE', 'LIBELLE', 'DESCRIPTION', 'actif')
        }),
        ('Permissions', {
            'fields': ('PERMISSIONS',),
            'description': 'Format JSON: {"can_validate_rh": true, "can_validate_manager": true}'
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def actif_badge(self, obj):
        if obj.actif:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Actif</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">✗ Inactif</span>'
        )

    actif_badge.short_description = 'Statut'

    def nb_attributions(self, obj):
        count = obj.attributions.filter(actif=True, date_fin__isnull=True).count()
        return format_html(
            '<span style="background: #dbeafe; padding: 4px 8px; border-radius: 4px;">{}</span>',
            count
        )

    nb_attributions.short_description = 'Employés'

    def permissions_display(self, obj):
        if not obj.PERMISSIONS:
            return '-'

        perms = []
        for key, value in obj.PERMISSIONS.items():
            if value:
                perms.append(f'✓ {key}')

        if perms:
            return format_html('<br>'.join(perms))
        return '-'

    permissions_display.short_description = 'Permissions'


@admin.register(ZYRE)
class ZYREAdmin(admin.ModelAdmin):
    """Admin pour les attributions de rôles"""

    list_display = [
        'employe_display',
        'role_display',
        'date_debut',
        'date_fin',
        'actif_badge',
        'created_by_display'
    ]
    list_filter = [
        'actif',
        'role',
        'date_debut',
        'created_at'
    ]
    search_fields = [
        'employe__nom',
        'employe__prenoms',
        'employe__matricule',
        'role__CODE',
        'role__LIBELLE'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['employe', 'created_by']
    date_hierarchy = 'date_debut'

    fieldsets = (
        ('Attribution', {
            'fields': ('employe', 'role')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin', 'actif')
        }),
        ('Informations complémentaires', {
            'fields': ('commentaire', 'created_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def employe_display(self, obj):
        return format_html(
            '<a href="/admin/employee/zy00/{}/change/" target="_blank">{} {}</a>',
            obj.employe.pk,
            obj.employe.nom,
            obj.employe.prenoms
        )

    employe_display.short_description = 'Employé'
    employe_display.admin_order_field = 'employe__nom'

    def role_display(self, obj):
        color = '#10b981' if obj.role.actif else '#6b7280'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} - {}</span>',
            color,
            obj.role.CODE,
            obj.role.LIBELLE
        )

    role_display.short_description = 'Rôle'
    role_display.admin_order_field = 'role__CODE'

    def actif_badge(self, obj):
        if obj.actif and not obj.date_fin:
            return format_html(
                '<span style="background: #d1fae5; color: #065f46; padding: 4px 8px; '
                'border-radius: 4px; font-weight: bold;">✓ Actif</span>'
            )
        elif obj.date_fin:
            return format_html(
                '<span style="background: #fee2e2; color: #991b1b; padding: 4px 8px; '
                'border-radius: 4px;">Terminé le {}</span>',
                obj.date_fin.strftime('%d/%m/%Y')
            )
        return format_html(
            '<span style="background: #e5e7eb; color: #374151; padding: 4px 8px; '
            'border-radius: 4px;">Inactif</span>'
        )

    actif_badge.short_description = 'Statut'

    def created_by_display(self, obj):
        if obj.created_by:
            return f"{obj.created_by.nom} {obj.created_by.prenoms}"
        return '-'

    created_by_display.short_description = 'Créé par'

    actions = ['activer_attributions', 'desactiver_attributions']

    def activer_attributions(self, request, queryset):
        count = queryset.update(actif=True)
        self.message_user(request, f'{count} attribution(s) activée(s).')

    activer_attributions.short_description = "Activer les attributions sélectionnées"

    def desactiver_attributions(self, request, queryset):
        from datetime import date
        count = queryset.update(actif=False, date_fin=date.today())
        self.message_user(request, f'{count} attribution(s) désactivée(s).')

    desactiver_attributions.short_description = "Désactiver les attributions sélectionnées"

# ===============================
# CUSTOMIZATION DE L'ADMIN
# ===============================

# Personnalisation du titre de l'admin
admin.site.site_header = "Gestion des Employés"