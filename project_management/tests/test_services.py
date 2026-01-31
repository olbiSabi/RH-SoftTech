from django.test import TestCase
from django.utils import timezone
from ..models import JRClient, JRProject, JRTicket
from ..services import client_service, ticket_service


class ClientServiceTest(TestCase):
    """Tests pour le service client"""
    
    def setUp(self):
        self.client = JRClient.objects.create(
            raison_sociale='Test Client',
            contact_principal='John Doe',
            email_contact='john@test.com',
            statut='ACTIF'
        )
    
    def test_get_active_clients(self):
        """Test la récupération des clients actifs"""
        active_clients = client_service.get_active_clients()
        self.assertEqual(active_clients.count(), 1)
        self.assertEqual(active_clients.first(), self.client)
    
    def test_get_client_stats(self):
        """Test les statistiques d'un client"""
        stats = client_service.get_client_stats(self.client.id)
        self.assertEqual(stats['nombre_projets'], 0)
        self.assertEqual(stats['chiffre_affaires_total'], 0)


class TicketServiceTest(TestCase):
    """Tests pour le service ticket"""
    
    def setUp(self):
        self.client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
        self.project = JRProject.objects.create(
            nom='Test Project',
            client=self.client,
            statut='ACTIF'
        )
        self.ticket = JRTicket.objects.create(
            titre='Test Ticket',
            description='Test description',
            projet=self.project,
            priorite='MOYENNE',
            statut='OUVERT'
        )
    
    def test_get_tickets_by_status(self):
        """Test la récupération des tickets par statut"""
        tickets = ticket_service.get_tickets_by_status('OUVERT')
        self.assertEqual(tickets.count(), 1)
        self.assertEqual(tickets.first(), self.ticket)
    
    def test_create_historique_entry(self):
        """Test la création d'une entrée d'historique"""
        historique = ticket_service.create_historique_entry(
            ticket=self.ticket,
            champ_modifie='statut',
            ancienne_valeur='OUVERT',
            nouvelle_valeur='EN_COURS',
            utilisateur=None
        )
        self.assertIsNotNone(historique)
        self.assertEqual(historique.champ_modifie, 'statut')
        self.assertEqual(historique.ancienne_valeur, 'OUVERT')
        self.assertEqual(historique.nouvelle_valeur, 'EN_COURS')
