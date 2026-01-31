from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import JRClient, JRProject, JRTicket

User = get_user_model()


class MinimalProjectManagementTest(TestCase):
    """Tests minimaux pour vérifier que l'application fonctionne"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_client_creation(self):
        """Test simple création d'un client"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            contact_principal='John Doe',
            email_contact='john@test.com',
            statut='ACTIF'
        )
        
        self.assertEqual(client.raison_sociale, 'Test Client')
        self.assertEqual(client.statut, 'ACTIF')
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.updated_at)
    
    def test_project_creation(self):
        """Test simple création d'un projet"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut=timezone.now().date(),
            date_fin_prevue=timezone.now().date() + timezone.timedelta(days=30),
            statut='PLANIFIE'
        )
        
        self.assertEqual(project.nom, 'Test Project')
        self.assertEqual(project.client, client)
        self.assertEqual(project.statut, 'PLANIFIE')
    
    def test_ticket_creation(self):
        """Test simple création d'un ticket"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut=timezone.now().date(),
            date_fin_prevue=timezone.now().date() + timezone.timedelta(days=30),
            statut='PLANIFIE'
        )
        
        ticket = JRTicket.objects.create(
            titre='Test Ticket',
            description='Test description',
            projet=project,
            priorite='MOYENNE',
            statut='OUVERT'
        )
        
        self.assertEqual(ticket.titre, 'Test Ticket')
        self.assertEqual(ticket.projet, project)
        self.assertEqual(ticket.priorite, 'MOYENNE')
        self.assertEqual(ticket.statut, 'OUVERT')
    
    def test_url_resolution(self):
        """Test que les URLs sont bien définies"""
        # Test que les URLs peuvent être résolues
        try:
            reverse('pm:dashboard')
            reverse('pm:dashboard_stats_api')
            reverse('pm:client_list')
            reverse('pm:projet_list')
            reverse('pm:ticket_list')
            url_resolution_ok = True
        except:
            url_resolution_ok = False
        
        self.assertTrue(url_resolution_ok)
    
    def test_unauthenticated_redirect(self):
        """Test que les pages non authentifiées redirigent"""
        # Test dashboard
        response = self.client.get(reverse('pm:dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # Test API
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 302)
    
    def test_authenticated_basic(self):
        """Test basique avec authentification"""
        self.client.login(username='testuser', password='testpass123')
        
        # Créer des données de test
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut=timezone.now().date(),
            date_fin_prevue=timezone.now().date() + timezone.timedelta(days=30),
            statut='PLANIFIE'
        )
        
        ticket = JRTicket.objects.create(
            titre='Test Ticket',
            projet=project,
            priorite='MOYENNE',
            statut='OUVERT'
        )
        
        # Vérifier que les objets existent
        self.assertEqual(JRClient.objects.count(), 1)
        self.assertEqual(JRProject.objects.count(), 1)
        self.assertEqual(JRTicket.objects.count(), 1)
        
        # Vérifier les relations
        self.assertEqual(project.client, client)
        self.assertEqual(ticket.projet, project)
    
    def test_model_string_representations(self):
        """Test les représentations string des modèles"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut=timezone.now().date(),
            date_fin_prevue=timezone.now().date() + timezone.timedelta(days=30),
            statut='PLANIFIE'
        )
        
        ticket = JRTicket.objects.create(
            titre='Test Ticket',
            projet=project,
            priorite='MOYENNE',
            statut='OUVERT'
        )
        
        # Test des représentations string
        self.assertIn('Test Client', str(client))
        self.assertIn('Test Project', str(project))
        self.assertIn('Test Ticket', str(ticket))
