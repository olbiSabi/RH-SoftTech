from django.test import TestCase
from django.utils import timezone
from ..models import JRClient, JRProject, JRTicket


class JRClientModelTest(TestCase):
    """Tests pour le modèle JRClient"""
    
    def test_create_client(self):
        client = JRClient.objects.create(
            raison_sociale='Test Client',
            contact_principal='John Doe',
            email_contact='john@test.com',
            statut='ACTIF'
        )
        self.assertEqual(client.raison_sociale, 'Test Client')
        self.assertTrue(client.code_client.startswith('CL-'))


class JRProjectModelTest(TestCase):
    """Tests pour le modèle JRProject"""
    
    def test_create_project(self):
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


class JRTicketModelTest(TestCase):
    """Tests pour le modèle JRTicket"""
    
    def test_create_ticket(self):
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
