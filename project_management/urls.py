from django.urls import path
from . import views

app_name = 'pm'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Clients
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<uuid:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<uuid:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<uuid:pk>/delete/', views.client_delete, name='client_delete'),
    path('clients/stats/', views.client_stats_api, name='client_stats_api'),
    
    # Projets
    path('projets/', views.ProjetListView.as_view(), name='projet_list'),
    path('projets/create/', views.ProjetCreateView.as_view(), name='projet_create'),
    path('projets/<uuid:pk>/', views.projet_detail, name='projet_detail'),
    path('projets/<uuid:pk>/update/', views.ProjetUpdateView.as_view(), name='projet_update'),
    path('projets/<uuid:pk>/delete/', views.projet_delete, name='projet_delete'),
    path('projets/<uuid:pk>/tickets/', views.projet_tickets, name='projet_tickets'),
    path('projets/<uuid:pk>/imputations/', views.projet_imputations, name='projet_imputations'),
    path('projets/stats/', views.projet_stats_api, name='projet_stats_api'),

    # Tickets
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/create/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<uuid:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<uuid:pk>/update/', views.TicketUpdateView.as_view(), name='ticket_update'),
    path('tickets/<uuid:pk>/delete/', views.ticket_delete, name='ticket_delete'),
    path('tickets/<uuid:pk>/commentaire/', views.ticket_ajouter_commentaire, name='ticket_commentaire'),
    path('tickets/<uuid:pk>/piece-jointe/', views.ticket_ajouter_piece_jointe, name='ticket_piece_jointe'),
    path('tickets/<uuid:pk>/changer-statut/', views.ticket_changer_statut, name='ticket_changer_statut'),
    path('tickets/<uuid:pk>/assigner/', views.ticket_assigner, name='ticket_assigner'),
    path('tickets/kanban/', views.ticket_kanban, name='ticket_kanban'),
    path('tickets/stats/', views.ticket_stats_api, name='ticket_stats_api'),

    # Imputations
    path('imputations/', views.ImputationListView.as_view(), name='imputation_list'),
    path('imputations/create/', views.ImputationCreateView.as_view(), name='imputation_create'),
    path('imputations/mes/', views.mes_imputations, name='mes_imputations'),
    path('imputations/<uuid:pk>/update/', views.ImputationUpdateView.as_view(), name='imputation_update'),
    path('imputations/<uuid:pk>/delete/', views.ImputationDeleteView.as_view(), name='imputation_delete'),
    path('imputations/validation/', views.validation_imputations, name='validation_imputations'),
    path('imputations/<uuid:pk>/valider/', views.valider_imputation, name='valider_imputation'),
    path('imputations/valider-multiple/', views.valider_multiple_imputations, name='valider_multiple_imputations'),
    path('imputations/rapports/', views.rapports_temps, name='rapports_temps'),
    path('imputations/export/', views.export_temps_excel, name='export_temps_excel'),
    path('imputations/stats/', views.imputation_stats_api, name='imputation_stats_api'),

    # Backlog
    path('backlog/', views.BacklogListView.as_view(), name='backlog_list'),
    path('backlog/projet/<uuid:pk>/', views.backlog_projet, name='backlog_projet'),
    path('backlog/projet/<uuid:pk>/ajouter/', views.backlog_ajouter_ticket, name='backlog_ajouter_ticket'),
    path('backlog/projet/<uuid:pk>/retirer/', views.backlog_retirer_ticket, name='backlog_retirer_ticket'),
    path('backlog/reorganiser/', views.backlog_reorganiser, name='backlog_reorganiser'),
    path('backlog/projet/<uuid:pk>/priorisation/', views.backlog_priorisation, name='backlog_priorisation'),
    path('backlog/projet/<uuid:pk>/changer-priorite/', views.backlog_changer_priorite, name='backlog_changer_priorite'),
    path('backlog/projet/<uuid:pk>/planning-sprint/', views.backlog_planning_sprint, name='backlog_planning_sprint'),
    path('backlog/projet/<uuid:pk>/creer-sprint/', views.backlog_creer_sprint, name='backlog_creer_sprint'),
    path('backlog/stats/', views.backlog_stats_api, name='backlog_stats_api'),

    # Sprints
    path('sprints/', views.SprintListView.as_view(), name='sprint_list'),
    path('sprints/create/', views.SprintCreateView.as_view(), name='sprint_create'),
    path('sprints/<uuid:pk>/', views.sprint_detail, name='sprint_detail'),
    path('sprints/<uuid:pk>/update/', views.SprintUpdateView.as_view(), name='sprint_update'),
    path('sprints/<uuid:pk>/board/', views.sprint_board, name='sprint_board'),
    path('sprints/<uuid:pk>/tickets/', views.sprint_tickets, name='sprint_tickets'),
    path('sprints/<uuid:pk>/demarrer/', views.sprint_demarrer, name='sprint_demarrer'),
    path('sprints/<uuid:pk>/terminer/', views.sprint_terminer, name='sprint_terminer'),
    path('sprints/<uuid:pk>/supprimer/', views.sprint_supprimer, name='sprint_supprimer'),
    path('sprints/<uuid:pk>/rapport/', views.sprint_rapport, name='sprint_rapport'),
    path('sprints/stats/', views.sprint_stats_api, name='sprint_stats_api'),
    
    # API endpoints
    path('api/stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/tickets-recents/', views.tickets_recents_api, name='tickets_recents_api'),
    path('api/projets-actifs/', views.projets_actifs_api, name='projets_actifs_api'),
    path('api/alertes/', views.alertes_api, name='alertes_api'),
    path('api/stats-personnelles/', views.stats_personnelles_api, name='stats_personnelles_api'),
    path('api/search-employes/', views.search_employes_api, name='search_employes_api'),
]
