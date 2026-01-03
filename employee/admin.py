from django.contrib import admin

from .forms import ZY00Form
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA, ZYNP, ZYPP, ZYIB, ZYRO, ZYRE
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin

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
    form = ZY00Form  # Utiliser le formulaire personnalisé
    list_display = (
        'matricule',
        'username',
        'prenomuser',
        'entreprise_display',  # Nouveau
        'type_dossier_display',
        'etat_display',
        'photo_preview'
    )
    list_filter = (
        'type_dossier',
        'etat',
        'sexe',
        'situation_familiale',
        'entreprise',  # Nouveau
    )
    search_fields = (
        'matricule',
        'username',
        'prenomuser',
        'ville_naissance',
        'pays_naissance',
        'entreprise__nom',  # Nouveau
    )
    readonly_fields = (
        'matricule',
        'uuid',
        'photo_preview',
        'anciennete_annees_display',  # Nouveau
    )
    fieldsets = (
        ('Photo et Identité', {
            'fields': (
                'photo_preview',
                'photo',
                'matricule',
                'nom',
                'prenoms',
                'username',
                'prenomuser',
            )
        }),
        ('Informations Personnelles', {
            'fields': (
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
        ('Rattachement Entreprise', {
            'fields': (
                'entreprise',
                'convention_personnalisee',
                'date_entree_entreprise',
                'anciennete_annees_display',  # Lecture seule
                'coefficient_temps_travail',
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
                'uuid',
                'user'
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

    # Actions personnalisées
    actions = ['activer_employes', 'desactiver_employes']

    def nom_complet(self, obj):
        return f"{obj.nom} {obj.prenoms}"

    nom_complet.short_description = 'Nom complet'

    def type_dossier_display(self, obj):
        return obj.get_type_dossier_display()

    type_dossier_display.short_description = 'Type dossier'

    def etat_display(self, obj):
        color = 'green' if obj.etat == 'actif' else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_etat_display()
        )

    etat_display.short_description = 'État'
    etat_display.admin_order_field = 'etat'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 5px;" />',
                obj.photo.url
            )
        # Photo par défaut selon le sexe
        default_photo = '/static/assets/img/default_female_avatar.png' if obj.sexe == 'F' else '/static/assets/img/default_male_avatar.png'
        return format_html(
            '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 5px; opacity: 0.5;" />',
            default_photo
        )

    photo_preview.short_description = 'Photo'

    def entreprise_display(self, obj):
        if obj.entreprise:
            return obj.entreprise.nom
        return "Non rattaché"

    entreprise_display.short_description = 'Entreprise'
    entreprise_display.admin_order_field = 'entreprise__nom'

    def anciennete_annees_display(self, obj):
        """Affiche l'ancienneté en années"""
        return f"{obj.anciennete_annees} ans"

    anciennete_annees_display.short_description = 'Ancienneté'

    # Actions admin
    def activer_employes(self, request, queryset):
        """Activer les employés sélectionnés"""
        updated = queryset.update(etat='actif')
        self.message_user(request, f"{updated} employé(s) activé(s) avec succès.")

    activer_employes.short_description = "Activer les employés sélectionnés"

    def desactiver_employes(self, request, queryset):
        """Désactiver les employés sélectionnés"""
        # Vérifier s'il y a des managers actifs
        managers = queryset.filter(is_manager=True, etat='actif')
        if managers.exists():
            self.message_user(
                request,
                f"Attention : {managers.count()} employé(s) sont managers. "
                "Veuillez réaffecter leur département avant désactivation.",
                level='warning'
            )
            return

        updated = queryset.update(etat='inactif')
        self.message_user(request, f"{updated} employé(s) désactivé(s) avec succès.")

    desactiver_employes.short_description = "Désactiver les employés sélectionnés"

    def get_queryset(self, request):
        """Optimisation des requêtes pour l'admin"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'entreprise',
            'convention_personnalisee',
            'user'
        )

    def save_model(self, request, obj, form, change):
        """Logique supplémentaire lors de la sauvegarde"""
        if not change:  # Nouvel employé
            obj.created_by = request.user.employe if hasattr(request.user, 'employe') else None

        # Mettre à jour l'utilisateur Django associé si nécessaire
        if not obj.user and obj.username:
            # Créer un utilisateur Django associé
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(
                username=obj.username,
                defaults={
                    'first_name': obj.prenomuser,
                    'last_name': obj.username,
                    'email': f"{obj.username}.{obj.prenomuser}@entreprise.com",
                    'is_active': obj.etat == 'actif'
                }
            )
            if created:
                obj.user = user

        super().save_model(request, obj, form, change)

        # Désactiver les données associées si l'employé est inactif
        if obj.etat == 'inactif':
            obj.desactiver_donnees_associees()


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


@admin.register(ZYRO)
class ZYROAdmin(admin.ModelAdmin):
    """Admin pour les rôles avec support système hybride"""

    list_display = [
        'CODE',
        'LIBELLE',
        'django_group_display',
        'actif',
        'nb_attributions',
        'permissions_count',
        'created_at'
    ]
    list_filter = ['actif', 'created_at']
    search_fields = ['CODE', 'LIBELLE', 'DESCRIPTION']
    readonly_fields = ['created_at', 'updated_at', 'permissions_preview']

    fieldsets = (
        ('Informations principales', {
            'fields': ('CODE', 'LIBELLE', 'DESCRIPTION', 'actif')
        }),
        ('Système hybride', {
            'fields': ('django_group',),
            'description': 'Groupe Django associé pour les permissions natives'
        }),
        ('Permissions personnalisées', {
            'fields': ('PERMISSIONS_CUSTOM', 'permissions_preview'),
            'description': 'Permissions métier au format JSON'
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def django_group_display(self, obj):
        """Affiche le groupe Django associé"""
        if obj.django_group:
            perms_count = obj.django_group.permissions.count()
            return f"{obj.django_group.name} ({perms_count} permissions)"
        return "Aucun groupe"

    django_group_display.short_description = 'Groupe Django'

    def nb_attributions(self, obj):
        """Nombre d'attributions actives"""
        count = obj.attributions.filter(actif=True, date_fin__isnull=True).count()
        return f"{count} employé(s)"

    nb_attributions.short_description = 'Attributions actives'

    def permissions_count(self, obj):
        """Compte des permissions (Django + Custom)"""
        django_count = 0
        if obj.django_group:
            django_count = obj.django_group.permissions.count()

        custom_count = 0
        if obj.PERMISSIONS_CUSTOM:
            custom_count = sum(1 for v in obj.PERMISSIONS_CUSTOM.values() if v)

        total = django_count + custom_count
        return f"{total} (Django: {django_count} | Custom: {custom_count})"

    permissions_count.short_description = 'Total permissions'

    def permissions_preview(self, obj):
        """Prévisualisation des permissions"""
        lines = []

        # Permissions Django
        if obj.django_group:
            lines.append("=== PERMISSIONS DJANGO ===")
            perms = obj.django_group.permissions.select_related('content_type').all()
            if perms:
                perms_by_model = {}
                for perm in perms:
                    model = perm.content_type.model
                    if model not in perms_by_model:
                        perms_by_model[model] = []
                    perms_by_model[model].append(perm.codename)

                for model, model_perms in sorted(perms_by_model.items()):
                    lines.append(f"{model.upper()}: {', '.join(model_perms)}")
            else:
                lines.append("Aucune permission Django")

        # Permissions Custom
        lines.append("\n=== PERMISSIONS PERSONNALISÉES ===")
        if obj.PERMISSIONS_CUSTOM:
            perms_actives = [k for k, v in obj.PERMISSIONS_CUSTOM.items() if v]
            if perms_actives:
                for perm in perms_actives:
                    lines.append(f"  - {perm}")
            else:
                lines.append("Aucune permission custom active")
        else:
            lines.append("Aucune permission custom définie")

        return '\n'.join(lines)

    permissions_preview.short_description = 'Aperçu des permissions'

    actions = ['synchroniser_groupes_django', 'activer_roles', 'desactiver_roles']

    def synchroniser_groupes_django(self, request, queryset):
        """Synchronise les rôles avec les groupes Django"""
        count = 0
        for role in queryset:
            if role.sync_to_django_group():
                count += 1

        self.message_user(request, f'{count} rôle(s) synchronisé(s) avec les groupes Django.')

    synchroniser_groupes_django.short_description = "Synchroniser avec groupes Django"

    def activer_roles(self, request, queryset):
        """Active les rôles sélectionnés"""
        count = queryset.update(actif=True)
        self.message_user(request, f'{count} rôle(s) activé(s).')

    activer_roles.short_description = "Activer les rôles sélectionnés"

    def desactiver_roles(self, request, queryset):
        """Désactive les rôles sélectionnés"""
        count = queryset.update(actif=False)
        self.message_user(request, f'{count} rôle(s) désactivé(s).')

    desactiver_roles.short_description = "Désactiver les rôles sélectionnés"


@admin.register(ZYRE)
class ZYREAdmin(admin.ModelAdmin):
    """Admin pour les attributions de rôles avec synchronisation Django Groups"""

    list_display = [
        'employe_display',
        'role_display',
        'django_group_sync_status',
        'date_debut',
        'date_fin',
        'actif',
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
    readonly_fields = ['created_at', 'updated_at', 'sync_info']
    autocomplete_fields = ['employe', 'created_by']
    date_hierarchy = 'date_debut'

    fieldsets = (
        ('Attribution', {
            'fields': ('employe', 'role')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin', 'actif')
        }),
        ('Synchronisation', {
            'fields': ('sync_info',),
            'description': 'Informations sur la synchronisation avec les groupes Django'
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
        """Affichage de l'employé"""
        has_user = "Oui" if obj.employe.user else "Non"
        return f"{obj.employe.nom} {obj.employe.prenoms} (User: {has_user})"

    employe_display.short_description = 'Employé'
    employe_display.admin_order_field = 'employe__nom'

    def role_display(self, obj):
        """Affichage du rôle"""
        statut = "Actif" if obj.role.actif else "Inactif"
        return f"{obj.role.CODE} - {obj.role.LIBELLE} ({statut})"

    role_display.short_description = 'Rôle'
    role_display.admin_order_field = 'role__CODE'

    def django_group_sync_status(self, obj):
        """Statut de synchronisation avec Django Groups"""
        if not obj.employe.user:
            return "Pas de compte"

        if not obj.role.django_group:
            return "Pas de groupe"

        if obj.actif and not obj.date_fin:
            is_in_group = obj.role.django_group in obj.employe.user.groups.all()
            return "Synchronisé" if is_in_group else "Non synchronisé"
        else:
            return "Inactif"

    django_group_sync_status.short_description = 'Sync Django'

    def created_by_display(self, obj):
        """Affichage du créateur"""
        if obj.created_by:
            return f"{obj.created_by.nom} {obj.created_by.prenoms}"
        return '-'

    created_by_display.short_description = 'Créé par'

    def sync_info(self, obj):
        """Informations détaillées sur la synchronisation"""
        lines = []

        # Employé
        lines.append("=== EMPLOYÉ ===")
        lines.append(f"Nom: {obj.employe.nom} {obj.employe.prenoms}")
        lines.append(f"Matricule: {obj.employe.matricule}")

        if obj.employe.user:
            lines.append(f"Username: {obj.employe.user.username}")
            groups = obj.employe.user.groups.all()
            if groups:
                lines.append(f"Groupes Django: {', '.join([g.name for g in groups])}")
            else:
                lines.append("Groupes Django: Aucun")
        else:
            lines.append("ATTENTION: Aucun compte utilisateur")

        # Rôle
        lines.append("\n=== RÔLE ===")
        lines.append(f"Code: {obj.role.CODE}")
        lines.append(f"Libellé: {obj.role.LIBELLE}")

        if obj.role.django_group:
            perms_count = obj.role.django_group.permissions.count()
            lines.append(f"Groupe Django: {obj.role.django_group.name} ({perms_count} permissions)")
        else:
            lines.append("ATTENTION: Aucun groupe Django associé")

        custom_perms = sum(1 for v in (obj.role.PERMISSIONS_CUSTOM or {}).values() if v)
        lines.append(f"Permissions custom: {custom_perms}")

        # Statut
        lines.append("\n=== STATUT ===")

        if obj.actif and not obj.date_fin:
            lines.append("Attribution: ACTIVE")

            if obj.employe.user and obj.role.django_group:
                is_synced = obj.role.django_group in obj.employe.user.groups.all()
                if is_synced:
                    lines.append("Synchronisation: OK")
                else:
                    lines.append("Synchronisation: ERREUR - Non synchronisé")
            elif not obj.employe.user:
                lines.append("Synchronisation: Impossible (pas de compte utilisateur)")
            else:
                lines.append("Synchronisation: Impossible (pas de groupe Django)")
        else:
            lines.append("Attribution: INACTIVE")

        return '\n'.join(lines)

    sync_info.short_description = 'Informations de synchronisation'

    actions = ['activer_attributions', 'desactiver_attributions', 'forcer_synchronisation']

    def activer_attributions(self, request, queryset):
        """Active les attributions sélectionnées"""
        count = queryset.update(actif=True, date_fin=None)

        # Synchroniser avec Django Groups
        for attribution in queryset:
            if attribution.employe.user and attribution.role.django_group:
                attribution.employe.user.groups.add(attribution.role.django_group)

        self.message_user(request, f'{count} attribution(s) activée(s) et synchronisée(s).')

    activer_attributions.short_description = "Activer les attributions sélectionnées"

    def desactiver_attributions(self, request, queryset):
        """Désactive les attributions sélectionnées"""
        from datetime import date
        count = queryset.update(actif=False, date_fin=date.today())

        # Retirer des Django Groups
        for attribution in queryset:
            if attribution.employe.user and attribution.role.django_group:
                attribution.employe.user.groups.remove(attribution.role.django_group)

        self.message_user(request, f'{count} attribution(s) désactivée(s).')

    desactiver_attributions.short_description = "Désactiver les attributions sélectionnées"

    def forcer_synchronisation(self, request, queryset):
        """Force la synchronisation avec les groupes Django"""
        count_synced = 0
        count_errors = 0

        for attribution in queryset:
            if attribution.actif and not attribution.date_fin:
                if attribution.employe.user and attribution.role.django_group:
                    attribution.employe.user.groups.add(attribution.role.django_group)
                    count_synced += 1
                else:
                    count_errors += 1

        if count_synced > 0:
            self.message_user(request, f'{count_synced} attribution(s) synchronisée(s).')

        if count_errors > 0:
            self.message_user(
                request,
                f'{count_errors} attribution(s) non synchronisées (pas de compte ou groupe).',
                level='warning'
            )

    forcer_synchronisation.short_description = "Forcer la synchronisation avec Django Groups"

admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    """Admin personnalisé pour les groupes Django"""

    list_display = ['name', 'role_zyro_link', 'permissions_count', 'users_count']

    def role_zyro_link(self, obj):
        """Lien vers le rôle ZYRO associé"""
        try:
            role = obj.role_zyro
            return f"{role.CODE} - {role.LIBELLE}"
        except:
            return "-"

    role_zyro_link.short_description = 'Rôle ZYRO'

    def permissions_count(self, obj):
        """Nombre de permissions"""
        return obj.permissions.count()

    permissions_count.short_description = 'Nb permissions'

    def users_count(self, obj):
        """Nombre d'utilisateurs"""
        return obj.user_set.count()

    users_count.short_description = 'Nb utilisateurs'


# ===============================
# CUSTOMIZATION DE L'ADMIN
# ===============================

# Personnalisation du titre de l'admin
admin.site.site_header = "Gestion des Employés"