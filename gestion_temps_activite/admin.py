# gestion_temps_activite/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ZDCL, ZDAC, ZDPJ, ZDTA, ZDDO, ZDIT
from django.contrib.humanize.templatetags.humanize import intcomma

@admin.register(ZDCL)
class ZDCLAdmin(admin.ModelAdmin):
    """Administration des Clients"""

    list_display = [
        'code_client',
        'raison_sociale',
        'type_client',
        'ville',
        'telephone',
        'email',
        'nombre_projets',
        'actif_badge',
        'date_creation'
    ]

    list_filter = [
        'type_client',
        'actif',
        'pays',
        'date_creation'
    ]

    search_fields = [
        'code_client',
        'raison_sociale',
        'personne_contact',
        'email',
        'ville'
    ]

    readonly_fields = [
        'date_creation',
        'date_modification',
        'get_adresse_complete'
    ]

    fieldsets = (
        ('Informations Générales', {
            'fields': (
                'code_client',
                'raison_sociale',
                'type_client',
                'secteur_activite',
                'actif'
            )
        }),
        ('Coordonnées', {
            'fields': (
                'personne_contact',
                'fonction_contact',
                'telephone',
                'email'
            )
        }),
        ('Adresse', {
            'fields': (
                'adresse_ligne1',
                'adresse_ligne2',
                'ville',
                'code_postal',
                'pays',
                'get_adresse_complete'
            )
        }),
        ('Informations Complémentaires', {
            'fields': (
                'notes',
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': (
                'cree_par',
                'date_creation',
                'date_modification'
            ),
            'classes': ('collapse',)
        }),
    )

    def actif_badge(self, obj):
        """Badge coloré pour le statut actif"""
        if obj.actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Inactif</span>'
        )

    actif_badge.short_description = 'Statut'

    def nombre_projets(self, obj):
        """Nombre de projets du client"""
        count = obj.projets.count()
        if count > 0:
            url = reverse('admin:gestion_temps_activite_zdpj_changelist') + f'?client__id__exact={obj.id}'
            return format_html('<a href="{}">{} projet(s)</a>', url, count)
        return '0 projet'

    nombre_projets.short_description = 'Projets'

    def save_model(self, request, obj, form, change):
        """Enregistrer le créateur lors de la création"""
        if not change:  # Nouveau client
            obj.cree_par = request.user.employe if hasattr(request.user, 'employe') else None
        super().save_model(request, obj, form, change)


@admin.register(ZDAC)
class ZDACAdmin(admin.ModelAdmin):
    """Administration des Types d'Activités"""

    list_display = [
        'code_activite',
        'libelle',
        'facturable_badge',
        'taux_horaire_defaut',
        'date_debut',
        'date_fin',
        'statut_badge',
        'actif_badge'
    ]

    list_filter = [
        'facturable',
        'actif',
        'date_debut',
        'date_fin'
    ]

    search_fields = [
        'code_activite',
        'libelle',
        'description'
    ]

    readonly_fields = [
        'date_creation',
        'date_modification',
        'get_statut_display'
    ]

    fieldsets = (
        ('Informations Générales', {
            'fields': (
                'code_activite',
                'libelle',
                'description'
            )
        }),
        ('Facturation', {
            'fields': (
                'facturable',
                'taux_horaire_defaut'
            )
        }),
        ('Période de Validité', {
            'fields': (
                'date_debut',
                'date_fin',
                'actif',
                'get_statut_display'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'date_creation',
                'date_modification'
            ),
            'classes': ('collapse',)
        }),
    )

    def actif_badge(self, obj):
        """Badge pour le statut actif/inactif"""
        if obj.actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Inactif</span>'
        )

    actif_badge.short_description = 'Statut Manuel'

    def facturable_badge(self, obj):
        """Badge pour facturable"""
        if obj.facturable:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 10px; border-radius: 3px;">Facturable</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">Non facturable</span>'
        )

    facturable_badge.short_description = 'Facturation'

    def statut_badge(self, obj):
        """Badge pour le statut en vigueur"""
        statut = obj.get_statut_display()

        if "Actif" in statut and "jusqu'au" not in statut:
            color = "#28a745"  # Vert
        elif "Actif (jusqu'au" in statut:
            color = "#ffc107"  # Jaune
        elif "À venir" in statut:
            color = "#17a2b8"  # Bleu
        else:
            color = "#dc3545"  # Rouge

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, statut
        )

    statut_badge.short_description = 'Statut en Vigueur'


@admin.register(ZDPJ)
class ZDPJAdmin(admin.ModelAdmin):
    """Administration des Projets"""

    list_display = [
        'code_projet',
        'nom_projet',
        'client',
        'chef_projet',
        'statut_badge',
        'priorite_badge',
        'avancement_bar',
        'date_debut',
        'date_fin_prevue',
        'actif_badge'
    ]

    list_filter = [
        'statut',
        'priorite',
        'type_facturation',
        'actif',
        'date_creation',
        'client'
    ]

    search_fields = [
        'code_projet',
        'nom_projet',
        'description',
        'client__raison_sociale',
        'chef_projet__nom',
        'chef_projet__prenom'
    ]

    readonly_fields = [
        'date_creation',
        'date_modification',
        'get_avancement_pourcentage',
        'get_heures_consommees',
        'budget_restant'
    ]

    autocomplete_fields = [
        'client',
        'chef_projet'
    ]

    fieldsets = (
        ('Informations Générales', {
            'fields': (
                'code_projet',
                'nom_projet',
                'description',
                'client',
                'chef_projet'
            )
        }),
        ('Planification', {
            'fields': (
                'date_debut',
                'date_fin_prevue',
                'date_fin_reelle'
            )
        }),
        ('Budget', {
            'fields': (
                'budget_heures',
                'budget_montant',
                'get_heures_consommees',
                'budget_restant'
            )
        }),
        ('Statut et Facturation', {
            'fields': (
                'statut',
                'priorite',
                'type_facturation',
                'actif'
            )
        }),
        ('Avancement', {
            'fields': (
                'get_avancement_pourcentage',
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': (
                'cree_par',
                'date_creation',
                'date_modification'
            ),
            'classes': ('collapse',)
        }),
    )

    def statut_badge(self, obj):
        """Badge coloré pour le statut"""
        colors = {
            'PLANIFIE': '#17a2b8',
            'EN_COURS': '#28a745',
            'EN_PAUSE': '#ffc107',
            'TERMINE': '#6c757d',
            'ANNULE': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.statut, '#6c757d'),
            obj.get_statut_display()
        )

    statut_badge.short_description = 'Statut'

    def priorite_badge(self, obj):
        """Badge pour la priorité"""
        colors = {
            'BASSE': '#28a745',
            'NORMALE': '#17a2b8',
            'HAUTE': '#ffc107',
            'CRITIQUE': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.priorite, '#6c757d'),
            obj.get_priorite_display()
        )

    priorite_badge.short_description = 'Priorité'

    def actif_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Inactif</span>'
        )

    actif_badge.short_description = 'Statut'

    def avancement_bar(self, obj):
        """Barre de progression pour l'avancement"""
        pourcentage = obj.get_avancement_pourcentage()

        # Couleur selon l'avancement
        if pourcentage >= 100:
            color = '#28a745'  # Vert
        elif pourcentage >= 75:
            color = '#8BC34A'  # Vert clair
        elif pourcentage >= 50:
            color = '#FFC107'  # Orange
        else:
            color = '#FF5722'  # Rouge

        return format_html(
            '<div style="width:100px; background:#f0f0f0; border-radius:5px;">'
            '<div style="width:{}%; background:{}; height:20px; border-radius:5px; text-align:center; color:white; line-height:20px;">'
            '{}%'
            '</div></div>',
            pourcentage, color, pourcentage  # ✅ CORRECTION
        )

    avancement_bar.short_description = 'Avancement'

    def budget_restant(self, obj):
        """Calcule le budget restant"""
        if obj.budget_heures:
            consommees = obj.get_heures_consommees()
            restant = float(obj.budget_heures) - consommees
            color = 'green' if restant > 0 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.2f} heures</span>',
                color, restant
            )
        return "N/A"

    budget_restant.short_description = 'Budget Restant'

    def save_model(self, request, obj, form, change):
        """Enregistrer le créateur lors de la création"""
        if not change:
            obj.cree_par = request.user.employe if hasattr(request.user, 'employe') else None
        super().save_model(request, obj, form, change)


@admin.register(ZDTA)
class ZDTAAdmin(admin.ModelAdmin):
    """Administration des Tâches"""

    list_display = [
        'code_tache',
        'titre',
        'projet',
        'assignee',
        'statut_badge',
        'priorite_badge',
        'avancement_bar',
        'estimation_heures',
        'heures_realisees',
        'ecart',
        'date_fin_prevue'
    ]

    list_filter = [
        'statut',
        'priorite',
        'projet',
        'assignee',
        'date_creation'
    ]

    search_fields = [
        'code_tache',
        'titre',
        'description',
        'projet__nom_projet',
        'assignee__nom',
        'assignee__prenom'
    ]

    readonly_fields = [
        'date_creation',
        'date_modification',
        'get_heures_realisees',
        'get_ecart_estimation'
    ]

    autocomplete_fields = [
        'projet',
        'assignee',
        'tache_parente'
    ]

    fieldsets = (
        ('Informations Générales', {
            'fields': (
                'code_tache',
                'titre',
                'description',
                'projet',
                'assignee',
                'tache_parente'
            )
        }),
        ('Estimations', {
            'fields': (
                'estimation_heures',
                'get_heures_realisees',
                'get_ecart_estimation'
            )
        }),
        ('Planification', {
            'fields': (
                'date_debut_prevue',
                'date_fin_prevue',
                'date_debut_reelle',
                'date_fin_reelle'
            )
        }),
        ('Statut et Avancement', {
            'fields': (
                'statut',
                'priorite',
                'avancement'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'cree_par',
                'date_creation',
                'date_modification'
            ),
            'classes': ('collapse',)
        }),
    )

    def statut_badge(self, obj):
        """Badge pour le statut"""
        colors = {
            'A_FAIRE': '#6c757d',
            'EN_COURS': '#17a2b8',
            'EN_ATTENTE': '#ffc107',
            'TERMINE': '#28a745',
            'ANNULE': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.statut, '#6c757d'),
            obj.get_statut_display()
        )

    statut_badge.short_description = 'Statut'

    def priorite_badge(self, obj):
        """Badge pour la priorité"""
        colors = {
            'BASSE': '#28a745',
            'NORMALE': '#17a2b8',
            'HAUTE': '#ffc107',
            'CRITIQUE': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.priorite, '#6c757d'),
            obj.get_priorite_display()
        )

    priorite_badge.short_description = 'Priorité'

    def avancement_bar(self, obj):
        """Barre de progression"""
        pourcentage = obj.avancement  # ✅ C'est correct pour ZDTA car c'est un champ direct

        # Couleur selon l'avancement
        if pourcentage >= 100:
            color = '#28a745'  # Vert
        elif pourcentage >= 75:
            color = '#8BC34A'  # Vert clair
        elif pourcentage >= 50:
            color = '#FFC107'  # Orange
        else:
            color = '#FF5722'  # Rouge

        return format_html(
            '<div style="width:100px; background:#f0f0f0; border-radius:5px;">'
            '<div style="width:{}%; background:{}; height:20px; border-radius:5px; text-align:center; color:white; line-height:20px;">'
            '{}%'
            '</div></div>',
            pourcentage, color, pourcentage
        )

    avancement_bar.short_description = 'Avancement'

    def heures_realisees(self, obj):
        """Heures réalisées"""
        heures = obj.get_heures_realisees()
        heures_formate = f"{heures:.2f}"
        return format_html('<strong>{}h</strong>', heures_formate)

    heures_realisees.short_description = 'Réalisé'

    def ecart(self, obj):
        """Écart estimation/réalisé"""
        ecart_value = obj.get_ecart_estimation()
        if ecart_value is None:
            return "N/A"

        color = 'red' if ecart_value > 0 else 'green'
        signe = '+' if ecart_value > 0 else ''
        ecart_formate = f"{ecart_value:.2f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}h</span>',
            color, signe, ecart_formate
        )

    ecart.short_description = 'Écart'

    ecart.short_description = 'Écart'

    def save_model(self, request, obj, form, change):
        """Enregistrer le créateur lors de la création"""
        if not change:
            obj.cree_par = request.user.employe if hasattr(request.user, 'employe') else None
        super().save_model(request, obj, form, change)


@admin.register(ZDDO)
class ZDDOAdmin(admin.ModelAdmin):
    """Administration des Documents"""

    list_display = [
        'nom_document',
        'type_rattachement',
        'objet_rattache',
        'categorie_badge',
        'type_fichier',
        'taille_formatee',
        'version',
        'date_upload',
        'actif_badge'
    ]

    list_filter = [
        'type_rattachement',
        'categorie',
        'type_fichier',
        'actif',
        'date_upload'
    ]

    search_fields = [
        'nom_document',
        'description',
        'projet__nom_projet',
        'tache__titre'
    ]

    readonly_fields = [
        'date_upload',
        'type_fichier',
        'taille_fichier',
        'get_taille_formatee',
        'get_objet_rattache'
    ]

    autocomplete_fields = [
        'projet',
        'tache',
        'uploade_par',
        'document_precedent'
    ]

    fieldsets = (
        ('Informations du Document', {
            'fields': (
                'nom_document',
                'description',
                'fichier',
                'categorie',
                'version',
                'document_precedent'
            )
        }),
        ('Rattachement', {
            'fields': (
                'type_rattachement',
                'projet',
                'tache',
                'get_objet_rattache'
            )
        }),
        ('Métadonnées du Fichier', {
            'fields': (
                'type_fichier',
                'taille_fichier',
                'get_taille_formatee'
            ),
            'classes': ('collapse',)
        }),
        ('Informations Système', {
            'fields': (
                'uploade_par',
                'date_upload',
                'actif'
            ),
            'classes': ('collapse',)
        }),
    )

    def categorie_badge(self, obj):
        """Badge pour la catégorie"""
        colors = {
            'CONTRAT': '#dc3545',
            'CAHIER_CHARGES': '#ffc107',
            'SPECIFICATION': '#17a2b8',
            'RAPPORT': '#28a745',
            'FACTURE': '#6f42c1',
            'LIVRABLE': '#fd7e14',
            'AUTRE': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.categorie, '#6c757d'),
            obj.get_categorie_display()
        )

    categorie_badge.short_description = 'Catégorie'

    def objet_rattache(self, obj):
        """Objet auquel le document est rattaché"""
        rattache = obj.get_objet_rattache()
        if obj.type_rattachement == 'PROJET':
            url = reverse('admin:gestion_temps_activite_zdpj_change', args=[rattache.id])
        else:
            url = reverse('admin:gestion_temps_activite_zdta_change', args=[rattache.id])

        return format_html('<a href="{}">{}</a>', url, rattache)

    objet_rattache.short_description = 'Rattaché à'

    def taille_formatee(self, obj):
        """Taille du fichier formatée"""
        return obj.get_taille_formatee()

    taille_formatee.short_description = 'Taille'

    def actif_badge(self, obj):
        """Badge pour le statut actif"""
        if obj.actif:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Actif</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Inactif</span>'
        )

    actif_badge.short_description = 'Statut'

    def save_model(self, request, obj, form, change):
        """Enregistrer l'uploadeur lors de la création"""
        if not change:
            obj.uploade_par = request.user.employe if hasattr(request.user, 'employe') else None
        super().save_model(request, obj, form, change)


@admin.register(ZDIT)
class ZDITAdmin(admin.ModelAdmin):
    """Administration des Imputations Temps"""

    list_display = [
        'employe',
        'tache',
        'activite',
        'date',
        'duree',
        'facturable_badge',
        'valide_badge',
        'facture_badge',
        'montant_facturable'
    ]

    list_filter = [
        'valide',
        'facturable',
        'facture',
        'date',
        'employe',
        'tache__projet',
        'activite'
    ]

    search_fields = [
        'employe__nom',
        'employe__prenom',
        'employe__matricule',
        'tache__titre',
        'tache__code_tache',
        'commentaire'
    ]

    readonly_fields = [
        'date_creation',
        'date_modification',
        'get_montant_facturable'
    ]

    autocomplete_fields = [
        'employe',
        'tache',
        'activite',
        'valide_par'
    ]

    fieldsets = (
        ('Imputation', {
            'fields': (
                'employe',
                'tache',
                'activite',
                'date',
                'duree'
            )
        }),
        ('Timer (Optionnel)', {
            'fields': (
                'timer_debut',
                'timer_fin'
            ),
            'classes': ('collapse',)
        }),
        ('Détails', {
            'fields': (
                'commentaire',
            )
        }),
        ('Validation', {
            'fields': (
                'valide',
                'valide_par',
                'date_validation'
            )
        }),
        ('Facturation', {
            'fields': (
                'facturable',
                'facture',
                'taux_horaire_applique',
                'get_montant_facturable'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'date_creation',
                'date_modification'
            ),
            'classes': ('collapse',)
        }),
    )

    def facturable_badge(self, obj):
        """Badge facturable"""
        if obj.facturable:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Oui</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">Non</span>'
        )

    facturable_badge.short_description = 'Facturable'

    def valide_badge(self, obj):
        """Badge validation"""
        if obj.valide:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Validé</span>'
            )
        return format_html(
            '<span style="background-color: #ffc107; color: white; padding: 3px 10px; border-radius: 3px;">⏳ En attente</span>'
        )

    valide_badge.short_description = 'Validation'

    def facture_badge(self, obj):
        """Badge facturation"""
        if obj.facture:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 10px; border-radius: 3px;">✓ Facturé</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">Non facturé</span>'
        )

    facture_badge.short_description = 'Facturé'

    def montant_facturable(self, obj):
        """Montant facturable"""
        montant = obj.get_montant_facturable()
        if montant > 0:
            # Utiliser intcomma pour le formatage avec séparateurs
            montant_formate = intcomma(int(montant))
            return format_html(
                '<strong style="color: green;">{} FCFA</strong>',
                montant_formate
            )
        return "0 FCFA"

    montant_facturable.short_description = 'Montant'

    def save_model(self, request, obj, form, change):
        """Gestion de la validation"""
        if obj.valide and not obj.valide_par:
            obj.valide_par = request.user.employe if hasattr(request.user, 'employe') else None
            from django.utils import timezone
            obj.date_validation = timezone.now()
        super().save_model(request, obj, form, change)