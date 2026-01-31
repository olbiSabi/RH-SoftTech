from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..models import JRClient, JRProject, JRTicket

User = get_user_model()


class SimpleProjectManagementTest(TestCase):
    """Tests simples pour vérifier le fonctionnement de base"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_models_creation(self):
        """Test la création des modèles de base"""
        # Créer un client
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            contact_principal='John Doe',
            email_contact='john@test.com',
            statut='ACTIF'
        )
        self.assertEqual(client.raison_sociale, 'Test Client')
        self.assertTrue(client.code_client.startswith('CL-'))
        
        # Créer un projet
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut='2024-01-01',
            date_fin_prevue='2024-12-31',
            statut='PLANIFIE'
        )
        self.assertEqual(project.nom, 'Test Project')
        self.assertEqual(project.client, client)
        
        # Créer un ticket
        ticket = JRTicket.objects.create(
            titre='Test Ticket',
            description='Test description',
            projet=project,
            priorite='MOYENNE',
            statut='OUVERT'
        )
        self.assertEqual(ticket.titre, 'Test Ticket')
        self.assertEqual(ticket.projet, project)
    
    def test_dashboard_api_unauthenticated(self):
        """Test que l'API dashboard nécessite une authentification"""
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_dashboard_api_authenticated(self):
        """Test l'API dashboard avec utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la réponse contient les clés attendues
        data = response.json()
        expected_keys = ['total_projets', 'tickets_en_cours', 'tickets_termines', 'heures_semaine']
        for key in expected_keys:
            self.assertIn(key, data)
    
    def test_client_str_representation(self):
        """Test la représentation string des modèles"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        expected = f"{client.code_client} - Test Client"
        self.assertEqual(str(client), expected)
    
    def test_project_properties(self):
        """Test les propriétés des projets"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut='2024-01-01',
            date_fin_prevue='2024-12-31',
            statut='PLANIFIE'
        )
        
        # Test des propriétés
        self.assertEqual(project.nombre_tickets, 0)
        self.assertEqual(project.progression, 0)
        self.assertTrue(project.code_projet.startswith('PR-'))
    
    def test_ticket_properties(self):
        """Test les propriétés des tickets"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut='2024-01-01',
            date_fin_prevue='2024-12-31',
            statut='PLANIFIE'
        )
        ticket = JRTicket.objects.create(
            titre='Test Ticket',
            projet=project,
            priorite='MOYENNE',
            statut='OUVERT'
        )
        
        # Test des propriétés
        self.assertTrue(ticket.code_ticket.startswith('TK-'))
        self.assertEqual(ticket.temps_total, 0)
        self.assertFalse(ticket.est_en_retard())
