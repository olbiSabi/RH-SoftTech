from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from ..models import JRClient, JRProject, JRTicket

User = get_user_model()


class ProjectManagementAPITest(APITestCase):
    """Tests pour les API de project_management"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer des données de test
        self.test_client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        self.test_project = JRProject.objects.create(
            nom='Test Project',
            client=self.test_client,
            statut='ACTIF'
        )
        self.test_ticket = JRTicket.objects.create(
            titre='Test Ticket',
            projet=self.test_project,
            statut='OUVERT'
        )
    
    def test_dashboard_stats_api(self):
        """Test l'API des statistiques du dashboard"""
        url = reverse('pm:dashboard_stats_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('total_projets', data)
        self.assertIn('tickets_en_cours', data)
        self.assertIn('tickets_termines', data)
        self.assertIn('heures_semaine', data)
    
    def test_tickets_recents_api(self):
        """Test l'API des tickets récents"""
        url = reverse('pm:tickets_recents_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
    
    def test_projets_actifs_api(self):
        """Test l'API des projets actifs"""
        url = reverse('pm:projets_actifs_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
    
    def test_alertes_api(self):
        """Test l'API des alertes"""
        url = reverse('pm:alertes_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_stats_personnelles_api(self):
        """Test l'API des statistiques personnelles"""
        url = reverse('pm:stats_personnelles_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('tickets_assignes', data)
        self.assertIn('tickets_termines', data)
        self.assertIn('temps_mois', data)
        self.assertIn('taux_completion', data)
