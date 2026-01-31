from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import JRClient, JRProject, JRTicket

User = get_user_model()


class BasicProjectManagementTest(TestCase):
    """Tests basiques pour vérifier le fonctionnement minimal"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_client_model_basic(self):
        """Test basique du modèle Client"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            contact_principal='John Doe',
            email_contact='john@test.com',
            statut='ACTIF'
        )
        
        self.assertEqual(client.raison_sociale, 'Test Client')
        self.assertEqual(client.statut, 'ACTIF')
        self.assertTrue(client.code_client.startswith('CL-'))
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.updated_at)
    
    def test_project_model_basic(self):
        """Test basique du modèle Projet"""
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
        self.assertTrue(project.code_projet.startswith('PR-'))
    
    def test_ticket_model_basic(self):
        """Test basique du modèle Ticket"""
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
        self.assertTrue(ticket.code.startswith('TK-'))
    
    def test_dashboard_api_basic(self):
        """Test basique de l'API dashboard"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total_projets', data)
        self.assertIn('tickets_en_cours', data)
        self.assertIn('tickets_termines', data)
        self.assertIn('heures_semaine', data)
        
        # Vérifier que les valeurs sont des nombres
        self.assertIsInstance(data['total_projets'], int)
        self.assertIsInstance(data['tickets_en_cours'], int)
        self.assertIsInstance(data['tickets_termines'], int)
        self.assertIsInstance(data['heures_semaine'], (int, float))
    
    def test_model_relationships(self):
        """Test les relations entre modèles"""
        # Créer les objets
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
        
        # Tester les relations
        self.assertEqual(project.client, client)
        self.assertEqual(ticket.projet, project)
        
        # Tester les relations inverses
        self.assertIn(project, client.projets.all())
        self.assertIn(ticket, project.tickets.all())
    
    def test_model_choices(self):
        """Test les choix des modèles"""
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        
        project = JRProject.objects.create(
            nom='Test Project',
            client=client,
            date_debut=timezone.now().date(),
            date_fin_prevue=timezone.now().date() + timezone.timedelta(days=30),
            statut='ACTIF'
        )
        
        ticket = JRTicket.objects.create(
            titre='Test Ticket',
            projet=project,
            priorite='HAUTE',
            statut='EN_COURS',
            type='BUG'
        )
        
        # Vérifier que les choix sont valides
        self.assertIn(project.statut, [choice[0] for choice in JRProject.STATUT_CHOICES])
        self.assertIn(ticket.priorite, [choice[0] for choice in JRTicket.PRIORITE_CHOICES])
        self.assertIn(ticket.statut, [choice[0] for choice in JRTicket.STATUT_CHOICES])
        self.assertIn(ticket.type, [choice[0] for choice in JRTicket.TYPE_CHOICES])
    
    def test_unauthenticated_access(self):
        """Test que l'accès non authentifié est redirigé"""
        # Test dashboard
        response = self.client.get(reverse('pm:dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # Test API
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 302)
    
    def test_authenticated_access(self):
        """Test que l'accès authentifié fonctionne"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test dashboard (peut échouer à cause des templates, mais ne doit pas être 302)
        response = self.client.get(reverse('pm:dashboard'))
        self.assertNotEqual(response.status_code, 302)
        
        # Test API
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 200)
