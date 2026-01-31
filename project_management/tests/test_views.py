from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import JRClient, JRProject, JRTicket

User = get_user_model()


class ProjectManagementViewsTest(TestCase):
    """Tests pour les vues de project_management"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Créer un client de test
        self.test_client = JRClient.objects.create(
            raison_sociale='Test Client',
            contact_principal='John Doe',
            email_contact='john@test.com',
            statut='ACTIF'
        )
        
        # Créer un projet de test
        self.test_project = JRProject.objects.create(
            nom='Test Project',
            client=self.test_client,
            date_debut=timezone.now().date(),
            date_fin_prevue=timezone.now().date() + timezone.timedelta(days=30),
            statut='PLANIFIE'
        )
        
        # Créer un ticket de test
        self.test_ticket = JRTicket.objects.create(
            titre='Test Ticket',
            description='Test description',
            projet=self.test_project,
            priorite='MOYENNE',
            statut='OUVERT'
        )
    
    def test_dashboard_view_requires_login(self):
        """Test que le dashboard nécessite une connexion"""
        response = self.client.get(reverse('pm:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_dashboard_view_authenticated(self):
        """Test le dashboard avec utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pm:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dashboard')
    
    def test_client_list_view(self):
        """Test la liste des clients"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pm:client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
    
    def test_client_detail_view(self):
        """Test le détail d'un client"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pm:client_detail', args=[self.test_client.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
    
    def test_project_list_view(self):
        """Test la liste des projets"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pm:projet_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')
    
    def test_ticket_list_view(self):
        """Test la liste des tickets"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pm:ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ticket')
    
    def test_dashboard_stats_api(self):
        """Test l'API des statistiques du dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'total_projets': 1,
            'tickets_en_cours': 0,
            'tickets_termines': 0,
            'heures_semaine': 0
        })
