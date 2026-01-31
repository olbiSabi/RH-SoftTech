from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import JRClient, JRProject, JRTicket, JRImputation, JRSprint

User = get_user_model()


class ProjectManagementIntegrationTest(TestCase):
    """Tests d'intégration pour le flux complet de project_management"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.client.login(username='testuser', password='testpass123')
    
    def test_complete_client_workflow(self):
        """Test le flux complet de gestion des clients"""
        # 1. Créer un client
        client_data = {
            'raison_sociale': 'Integration Test Client',
            'contact_principal': 'Jane Doe',
            'email_contact': 'jane@test.com',
            'telephone_contact': '0123456789',
            'adresse': '123 Integration Street',
            'code_postal': '75001',
            'ville': 'Paris',
            'pays': 'France',
            'statut': 'ACTIF'
        }
        
        response = self.client.post(reverse('pm:client_create'), client_data)
        self.assertEqual(response.status_code, 302)  # Redirection après création
        
        # Vérifier que le client a été créé
        created_client = JRClient.objects.get(raison_sociale='Integration Test Client')
        self.assertEqual(created_client.contact_principal, 'Jane Doe')
        
        # 2. Voir la liste des clients
        response = self.client.get(reverse('pm:client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Test Client')
        
        # 3. Voir le détail du client
        response = self.client.get(reverse('pm:client_detail', args=[created_client.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Test Client')
        
        # 4. Mettre à jour le client
        update_data = client_data.copy()
        update_data['contact_principal'] = 'Jane Smith'
        response = self.client.post(
            reverse('pm:client_update', args=[created_client.id]),
            update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Vérifier la mise à jour
        updated_client = JRClient.objects.get(id=created_client.id)
        self.assertEqual(updated_client.contact_principal, 'Jane Smith')
    
    def test_complete_project_workflow(self):
        """Test le flux complet de gestion des projets"""
        # Créer un client d'abord
        test_client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        
        # 1. Créer un projet
        project_data = {
            'nom': 'Integration Test Project',
            'description': 'Test project for integration',
            'client': test_client.id,
            'statut': 'PLANIFIE',
            'date_debut': '2024-01-01',
            'date_fin_prevue': '2024-12-31'
        }
        
        response = self.client.post(reverse('pm:projet_create'), project_data)
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que le projet a été créé
        created_project = JRProject.objects.get(nom='Integration Test Project')
        self.assertEqual(created_project.client, test_client)
        
        # 2. Voir la liste des projets
        response = self.client.get(reverse('pm:projet_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Test Project')
    
    def test_complete_ticket_workflow(self):
        """Test le flux complet de gestion des tickets"""
        # Créer un client et un projet
        test_client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        test_project = JRProject.objects.create(
            nom='Test Project',
            client=test_client,
            statut='ACTIF'
        )
        
        # 1. Créer un ticket
        ticket_data = {
            'titre': 'Integration Test Ticket',
            'description': 'Test ticket for integration',
            'projet': test_project.id,
            'priorite': 'MOYENNE',
            'statut': 'OUVERT',
            'type': 'TACHE'
        }
        
        response = self.client.post(reverse('pm:ticket_create'), ticket_data)
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que le ticket a été créé
        created_ticket = JRTicket.objects.get(titre='Integration Test Ticket')
        self.assertEqual(created_ticket.projet, test_project)
        self.assertEqual(created_ticket.statut, 'OUVERT')
        
        # 2. Voir la liste des tickets
        response = self.client.get(reverse('pm:ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Test Ticket')
        
        # 3. Mettre à jour le statut du ticket
        update_data = ticket_data.copy()
        update_data['statut'] = 'EN_COURS'
        response = self.client.post(
            reverse('pm:ticket_update', args=[created_ticket.id]),
            update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Vérifier la mise à jour
        updated_ticket = JRTicket.objects.get(id=created_ticket.id)
        self.assertEqual(updated_ticket.statut, 'EN_COURS')
    
    def test_complete_imputation_workflow(self):
        """Test le flux complet de gestion des imputations"""
        # Créer les données nécessaires
        test_client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        test_project = JRProject.objects.create(
            nom='Test Project',
            client=test_client,
            statut='ACTIF'
        )
        test_ticket = JRTicket.objects.create(
            titre='Test Ticket',
            projet=test_project,
            statut='OUVERT'
        )
        
        # 1. Créer une imputation
        imputation_data = {
            'ticket': test_ticket.id,
            'date_imputation': timezone.now().date(),
            'type_activite': 'DEVELOPPEMENT',
            'heures': 2,
            'minutes': 30,
            'description': 'Test imputation for integration'
        }
        
        response = self.client.post(reverse('pm:imputation_create'), imputation_data)
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que l'imputation a été créée
        created_imputation = JRImputation.objects.get(
            ticket=test_ticket,
            employe__user=self.user
        )
        self.assertEqual(created_imputation.heures, 2)
        self.assertEqual(created_imputation.minutes, 30)
        self.assertEqual(created_imputation.statut_validation, 'EN_ATTENTE')
        
        # 2. Voir la liste des imputations
        response = self.client.get(reverse('pm:imputation_list'))
        self.assertEqual(response.status_code, 200)
        
        # 3. Voir ses propres imputations
        response = self.client.get(reverse('pm:mes_imputations'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_integration(self):
        """Test l'intégration du dashboard"""
        # Créer des données de test
        test_client = JRClient.objects.create(
            raison_sociale='Dashboard Test Client',
            statut='ACTIF'
        )
        test_project = JRProject.objects.create(
            nom='Dashboard Test Project',
            client=test_client,
            statut='ACTIF'
        )
        test_ticket = JRTicket.objects.create(
            titre='Dashboard Test Ticket',
            projet=test_project,
            statut='OUVERT'
        )
        
        # Accéder au dashboard
        response = self.client.get(reverse('pm:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Tester les API du dashboard
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('pm:tickets_recents_api'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('pm:projets_actifs_api'))
        self.assertEqual(response.status_code, 200)
    
    def test_error_handling(self):
        """Test la gestion des erreurs"""
        # Test accès à une ressource inexistante
        response = self.client.get(reverse('pm:client_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)
        
        # Test formulaire invalide
        response = self.client.post(reverse('pm:client_create'), {})
        self.assertEqual(response.status_code, 200)  # Le formulaire est réaffiché avec erreurs
        
        # Test API non authentifiée
        self.client.logout()
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
