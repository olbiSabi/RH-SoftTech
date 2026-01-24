# frais/urls.py
"""
URLs pour le module Notes de Frais.
"""
from django.urls import path
from frais import views

app_name = 'frais'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_frais, name='dashboard'),

    # Notes de frais
    path('notes/', views.liste_notes_frais, name='liste_notes'),
    path('notes/creer/', views.creer_note_frais, name='creer_note'),
    path('notes/<uuid:uuid>/', views.detail_note_frais, name='detail_note'),
    path('notes/<uuid:uuid>/modifier/', views.modifier_note_frais, name='modifier_note'),
    path('notes/<uuid:uuid>/supprimer/', views.supprimer_note_frais, name='supprimer_note'),

    # Workflow notes de frais
    path('notes/<uuid:uuid>/soumettre/', views.soumettre_note, name='soumettre_note'),
    path('notes/<uuid:uuid>/valider/', views.valider_note, name='valider_note'),
    path('notes/<uuid:uuid>/rejeter/', views.rejeter_note, name='rejeter_note'),
    path('notes/<uuid:uuid>/rembourser/', views.rembourser_note, name='rembourser_note'),

    # Lignes de frais
    path('notes/<uuid:note_uuid>/ligne/ajouter/', views.ajouter_ligne, name='ajouter_ligne'),
    path('lignes/<uuid:ligne_uuid>/supprimer/', views.supprimer_ligne, name='supprimer_ligne'),

    # Avances
    path('avances/', views.liste_avances, name='liste_avances'),
    path('avances/creer/', views.creer_avance, name='creer_avance'),
    path('avances/<uuid:uuid>/', views.detail_avance, name='detail_avance'),

    # Workflow avances
    path('avances/<uuid:uuid>/approuver/', views.approuver_avance, name='approuver_avance'),
    path('avances/<uuid:uuid>/rejeter/', views.rejeter_avance, name='rejeter_avance'),
    path('avances/<uuid:uuid>/verser/', views.verser_avance, name='verser_avance'),

    # Validation (admin)
    path('validation/notes/', views.notes_a_valider, name='notes_a_valider'),
    path('validation/avances/', views.avances_a_approuver, name='avances_a_approuver'),
    path('validation/remboursements/', views.notes_a_rembourser, name='notes_a_rembourser'),

    # Statistiques
    path('statistiques/', views.statistiques_frais, name='statistiques'),

    # API
    path('api/categories/', views.api_categories, name='api_categories'),

    # Gestion des catégories (admin)
    path('categories/', views.liste_categories, name='liste_categories'),
    path('categories/creer/', views.creer_categorie, name='creer_categorie'),
    path('categories/<int:pk>/modifier/', views.modifier_categorie, name='modifier_categorie'),
    path('categories/<int:pk>/supprimer/', views.supprimer_categorie, name='supprimer_categorie'),
    path('categories/defaut/', views.creer_categories_defaut, name='creer_categories_defaut'),

    # Administration (DRH, DAF, Comptable)
    path('admin/notes-validees/', views.admin_notes_validees, name='admin_notes_validees'),
    path('admin/notes-validees/export/', views.export_notes_validees_excel, name='export_notes_validees'),
    path('admin/avances-approuvees/', views.admin_avances_approuvees, name='admin_avances_approuvees'),
    path('admin/avances-approuvees/export/', views.export_avances_approuvees_excel, name='export_avances_approuvees'),
    path('admin/remboursements/', views.admin_remboursements, name='admin_remboursements'),
    path('admin/remboursements/<uuid:uuid>/confirmer/', views.confirmer_remboursement, name='confirmer_remboursement'),
    path('admin/remboursements/<uuid:uuid>/fiche/', views.fiche_remboursement, name='fiche_remboursement'),
]
