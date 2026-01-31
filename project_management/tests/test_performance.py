from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import connection

from ..models import JRClient, JRProject, JRTicket, JRImputation

User = get_user_model()


class ProjectManagementPerformanceTest(TestCase):
    """Tests de performance pour project_management"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Créer des données de test en masse
        self.create_test_data()
    
    def create_test_data(self):
        """Crée des données de test pour les tests de performance"""
        # Créer 10 clients
        clients = []
        for i in range(10):
            client = JRClient.objects.create(
                raison_sociale=f'Client {i}',
                contact_principal=f'Contact {i}',
                email_contact=f'client{i}@test.com',
                statut='ACTIF'
            )
            clients.append(client)
        
        # Créer 5 projets par client (50 projets)
        projects = []
        for client in clients:
            for j in range(5):
                project = JRProject.objects.create(
                    nom=f'Project {client.id}-{j}',
                    client=client,
                    statut='ACTIF'
                )
                projects.append(project)
        
        # Créer 10 tickets par projet (500 tickets)
        tickets = []
        for project in projects:
            for k in range(10):
                ticket = JRTicket.objects.create(
                    titre=f'Ticket {project.id}-{k}',
                    description=f'Description for ticket {project.id}-{k}',
                    projet=project,
                    priorite='MOYENNE',
                    statut='OUVERT'
                )
                tickets.append(ticket)
        
        return clients, projects, tickets
    
    def test_client_list_performance(self):
        """Test les performances de la liste des clients"""
        with self.assertNumQueries(1):  # Devrait faire une seule requête
            response = self.client.get(reverse('pm:client_list'))
            self.assertEqual(response.status_code, 302)  # Redirection login
    
    def test_dashboard_stats_performance(self):
        """Test les performances des statistiques du dashboard"""
        self.client.login(username='testuser', password='testpass123')
        
        # Compter le nombre de requêtes
        with self.assertNumQueries(5):  # Approximation du nombre de requêtes attendues
            response = self.client.get(reverse('pm:dashboard_stats_api'))
            self.assertEqual(response.status_code, 200)
    
    def test_ticket_list_with_filters_performance(self):
        """Test les performances de la liste des tickets avec filtres"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test sans filtres
        with self.assertNumQueries(2):  # Requête principale + count pour pagination
            response = self.client.get(reverse('pm:ticket_list'))
            self.assertEqual(response.status_code, 200)
        
        # Test avec filtres
        with self.assertNumQueries(2):
            response = self.client.get(reverse('pm:ticket_list'), {
                'statut': 'OUVERT',
                'priorite': 'MOYENNE'
            })
            self.assertEqual(response.status_code, 200)
    
    def test_database_query_optimization(self):
        """Test l'optimisation des requêtes de base de données"""
        self.client.login(username='testuser', password='testpass123')
        
        # Mesurer les requêtes avant optimisation
        with self.assertNumQueries(1):
            # Test select_related pour les relations ForeignKey
            tickets = list(JRTicket.objects.select_related('projet', 'projet__client')[:10])
            self.assertEqual(len(tickets), 10)
        
        with self.assertNumQueries(1):
            # Test prefetch_related pour les relations ManyToMany/Reverse
            clients = list(JRClient.objects.prefetch_related('projets')[:5])
            self.assertEqual(len(clients), 5)
    
    def test_pagination_performance(self):
        """Test les performances de la pagination"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test pagination avec beaucoup de données
        with self.assertNumQueries(2):  # Requête principale + count
            response = self.client.get(reverse('pm:ticket_list'), {'page': 1})
            self.assertEqual(response.status_code, 200)
        
        with self.assertNumQueries(2):
            response = self.client.get(reverse('pm:ticket_list'), {'page': 10})
            self.assertEqual(response.status_code, 200)
    
    def test_search_performance(self):
        """Test les performances de la recherche"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test recherche simple
        with self.assertNumQueries(2):
            response = self.client.get(reverse('pm:ticket_list'), {
                'recherche': 'Ticket 1'
            })
            self.assertEqual(response.status_code, 200)
        
        # Test recherche complexe
        with self.assertNumQueries(2):
            response = self.client.get(reverse('pm:ticket_list'), {
                'recherche': 'Project',
                'statut': 'OUVERT',
                'priorite': 'MOYENNE'
            })
            self.assertEqual(response.status_code, 200)
    
    @override_settings(DEBUG=True)
    def test_slow_queries_detection(self):
        """Test la détection des requêtes lentes"""
        self.client.login(username='testuser', password='testpass123')
        
        # Simuler une requête potentiellement lente
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse('pm:ticket_list'))
            
            # Vérifier qu'il n'y a pas de requêtes excessivement longues
            for query in queries:
                # En pratique, on pourrait vérifier le temps d'exécution
                self.assertLess(len(query['sql']), 1000)  # Éviter les requêtes trop complexes
    
    def test_memory_usage(self):
        """Test l'utilisation mémoire"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        # Effectuer des opérations qui pourraient consommer de la mémoire
        self.client.login(username='testuser', password='testpass123')
        
        # Charger beaucoup de données
        response = self.client.get(reverse('pm:ticket_list'))
        self.assertEqual(response.status_code, 200)
        
        # Charger les statistiques
        response = self.client.get(reverse('pm:dashboard_stats_api'))
        self.assertEqual(response.status_code, 200)
        
        memory_after = process.memory_info().rss
        
        # Vérifier que l'augmentation de mémoire est raisonnable (< 50MB)
        memory_increase = memory_after - memory_before
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # 50 MB
    
    def test_concurrent_access(self):
        """Test l'accès concurrent"""
        import threading
        import time
        
        results = []
        
        def access_dashboard():
            self.client.login(username='testuser', password='testpass123')
            response = self.client.get(reverse('pm:dashboard'))
            results.append(response.status_code)
        
        # Créer 10 threads simultanés
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=access_dashboard)
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        # Vérifier que toutes les requêtes ont réussi
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status == 200 for status in results))
