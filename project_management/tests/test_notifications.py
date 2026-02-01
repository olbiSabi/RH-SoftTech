"""
Tests pour le service de notifications du module Project Management.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock

from ..models import JRClient, JRProject, JRTicket, JRCommentaire
from ..services.notification_service import NotificationService

User = get_user_model()


class NotificationServiceTestCase(TestCase):
    """Tests de base pour NotificationService."""

    def setUp(self):
        """Configuration des données de test."""
        # Créer un client de test
        self.test_client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )

        # Créer un projet de test
        self.test_project = JRProject.objects.create(
            nom='Test Project',
            client=self.test_client,
            statut='ACTIF'
        )

        # Créer un ticket de test
        self.test_ticket = JRTicket.objects.create(
            titre='Test Ticket',
            description='Description du ticket test',
            projet=self.test_project,
            priorite='MOYENNE',
            statut='OUVERT'
        )


class NotificationServiceConstantsTest(NotificationServiceTestCase):
    """Tests pour les constantes du service de notifications."""

    def test_type_constants_exist(self):
        """Test que les constantes de type existent."""
        self.assertEqual(NotificationService.TYPE_PROJET_ASSIGNE, 'PROJET_ASSIGNE')
        self.assertEqual(NotificationService.TYPE_PROJET_REASSIGNE, 'PROJET_REASSIGNE')
        self.assertEqual(NotificationService.TYPE_TICKET_ASSIGNE, 'TICKET_ASSIGNE')
        self.assertEqual(NotificationService.TYPE_TICKET_REASSIGNE, 'TICKET_REASSIGNE')
        self.assertEqual(NotificationService.TYPE_STATUT_PROJET_CHANGE, 'STATUT_PROJET_CHANGE')
        self.assertEqual(NotificationService.TYPE_STATUT_TICKET_CHANGE, 'STATUT_TICKET_CHANGE')
        self.assertEqual(NotificationService.TYPE_COMMENTAIRE_TICKET, 'COMMENTAIRE_TICKET')
        self.assertEqual(NotificationService.TYPE_ECHEANCE_PROCHE, 'ECHEANCE_PROCHE')

    def test_messages_statut_ticket_exist(self):
        """Test que les messages de statut ticket existent."""
        self.assertIn(('OUVERT', 'EN_COURS'), NotificationService.MESSAGES_STATUT_TICKET)
        self.assertIn(('EN_COURS', 'EN_REVUE'), NotificationService.MESSAGES_STATUT_TICKET)
        self.assertIn(('EN_REVUE', 'TERMINE'), NotificationService.MESSAGES_STATUT_TICKET)

    def test_messages_statut_projet_exist(self):
        """Test que les messages de statut projet existent."""
        self.assertIn(('PLANIFIE', 'EN_COURS'), NotificationService.MESSAGES_STATUT_PROJET)
        self.assertIn(('EN_COURS', 'TERMINE'), NotificationService.MESSAGES_STATUT_PROJET)
        self.assertIn(('EN_COURS', 'EN_PAUSE'), NotificationService.MESSAGES_STATUT_PROJET)


class NotificationServiceCreerNotificationTest(NotificationServiceTestCase):
    """Tests pour la méthode _creer_notification."""

    @patch('project_management.services.notification_service.NotificationAbsence')
    def test_creer_notification_with_valid_data(self, mock_notification):
        """Test la création d'une notification avec des données valides."""
        mock_destinataire = Mock()
        mock_notification.creer_notification.return_value = Mock()

        result = NotificationService._creer_notification(
            destinataire=mock_destinataire,
            type_notif='TEST',
            message='Test message'
        )

        mock_notification.creer_notification.assert_called_once()

    def test_creer_notification_without_destinataire(self):
        """Test que la création retourne None sans destinataire."""
        result = NotificationService._creer_notification(
            destinataire=None,
            type_notif='TEST',
            message='Test message'
        )

        self.assertIsNone(result)


class NotificationServiceAssignationProjetTest(NotificationServiceTestCase):
    """Tests pour les notifications d'assignation de projet."""

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_assignation_projet_new_assignment(self, mock_creer):
        """Test la notification d'une nouvelle assignation de projet."""
        mock_creer.return_value = Mock()
        mock_employe = Mock()
        mock_employe.nom = 'Doe'
        mock_employe.prenoms = 'John'

        result = NotificationService.notifier_assignation_projet(
            projet=self.test_project,
            employe_assigne=mock_employe
        )

        # Vérifie qu'au moins une notification a été créée
        mock_creer.assert_called()
        self.assertIsInstance(result, list)

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_assignation_projet_reassignment(self, mock_creer):
        """Test la notification lors d'une réassignation de projet."""
        mock_creer.return_value = Mock()

        mock_ancien = Mock()
        mock_ancien.nom = 'Smith'
        mock_ancien.prenoms = 'Jane'
        mock_ancien.pk = 1

        mock_nouveau = Mock()
        mock_nouveau.nom = 'Doe'
        mock_nouveau.prenoms = 'John'
        mock_nouveau.pk = 2

        result = NotificationService.notifier_assignation_projet(
            projet=self.test_project,
            employe_assigne=mock_nouveau,
            ancien_chef_projet=mock_ancien
        )

        # Doit notifier les deux
        self.assertEqual(mock_creer.call_count, 2)

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_assignation_projet_no_new_assignee(self, mock_creer):
        """Test quand il n'y a pas de nouvel assigné."""
        mock_ancien = Mock()
        mock_ancien.pk = 1

        result = NotificationService.notifier_assignation_projet(
            projet=self.test_project,
            employe_assigne=None,
            ancien_chef_projet=mock_ancien
        )

        # Doit notifier l'ancien uniquement
        self.assertEqual(mock_creer.call_count, 1)


class NotificationServiceAssignationTicketTest(NotificationServiceTestCase):
    """Tests pour les notifications d'assignation de ticket."""

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_assignation_ticket_new_assignment(self, mock_creer):
        """Test la notification d'une nouvelle assignation de ticket."""
        mock_creer.return_value = Mock()

        mock_assigne = Mock()
        mock_assigne.nom = 'Doe'
        mock_assigne.prenoms = 'John'
        self.test_ticket.assigne = mock_assigne

        result = NotificationService.notifier_assignation_ticket(
            ticket=self.test_ticket
        )

        mock_creer.assert_called()
        self.assertIsInstance(result, list)

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_assignation_ticket_no_assignee(self, mock_creer):
        """Test quand le ticket n'a pas d'assigné."""
        self.test_ticket.assigne = None

        result = NotificationService.notifier_assignation_ticket(
            ticket=self.test_ticket
        )

        # Pas de notification si pas d'assigné
        mock_creer.assert_not_called()
        self.assertEqual(result, [])


class NotificationServiceStatutProjetTest(NotificationServiceTestCase):
    """Tests pour les notifications de changement de statut projet."""

    @patch.object(NotificationService, '_creer_notification')
    @patch.object(NotificationService, '_get_equipe_employe')
    @patch.object(NotificationService, '_get_manager_employe')
    def test_notifier_changement_statut_projet(self, mock_manager, mock_equipe, mock_creer):
        """Test la notification de changement de statut de projet."""
        mock_creer.return_value = Mock()
        mock_equipe.return_value = []
        mock_manager.return_value = None

        mock_chef = Mock()
        mock_chef.pk = 1
        self.test_project.chef_projet = mock_chef

        result = NotificationService.notifier_changement_statut_projet(
            projet=self.test_project,
            ancien_statut='PLANIFIE',
            nouveau_statut='EN_COURS'
        )

        mock_creer.assert_called()
        self.assertIsInstance(result, list)

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_changement_statut_projet_no_chef(self, mock_creer):
        """Test quand le projet n'a pas de chef de projet."""
        self.test_project.chef_projet = None

        result = NotificationService.notifier_changement_statut_projet(
            projet=self.test_project,
            ancien_statut='PLANIFIE',
            nouveau_statut='EN_COURS'
        )

        # Pas de notification si pas de chef de projet
        mock_creer.assert_not_called()
        self.assertEqual(result, [])


class NotificationServiceStatutTicketTest(NotificationServiceTestCase):
    """Tests pour les notifications de changement de statut ticket."""

    @patch.object(NotificationService, '_creer_notification')
    @patch.object(NotificationService, '_get_equipe_employe')
    @patch.object(NotificationService, '_get_manager_employe')
    def test_notifier_changement_statut_ticket(self, mock_manager, mock_equipe, mock_creer):
        """Test la notification de changement de statut de ticket."""
        mock_creer.return_value = Mock()
        mock_equipe.return_value = []
        mock_manager.return_value = None

        mock_assigne = Mock()
        mock_assigne.pk = 1
        self.test_ticket.assigne = mock_assigne

        mock_chef = Mock()
        mock_chef.pk = 2
        self.test_project.chef_projet = mock_chef

        result = NotificationService.notifier_changement_statut_ticket(
            ticket=self.test_ticket,
            ancien_statut='OUVERT',
            nouveau_statut='EN_COURS'
        )

        mock_creer.assert_called()
        self.assertIsInstance(result, list)

    def test_message_statut_ticket_known_transition(self):
        """Test le message pour une transition connue."""
        cle = ('OUVERT', 'EN_COURS')
        message = NotificationService.MESSAGES_STATUT_TICKET[cle]
        self.assertIn('{code}', message)


class NotificationServiceCommentaireTest(NotificationServiceTestCase):
    """Tests pour les notifications de commentaires."""

    @patch.object(NotificationService, '_creer_notification')
    @patch.object(NotificationService, '_get_equipe_employe')
    def test_notifier_commentaire_ticket(self, mock_equipe, mock_creer):
        """Test la notification de nouveau commentaire."""
        mock_creer.return_value = Mock()
        mock_equipe.return_value = []

        mock_auteur = Mock()
        mock_auteur.pk = 1

        mock_assigne = Mock()
        mock_assigne.pk = 2
        self.test_ticket.assigne = mock_assigne

        mock_chef = Mock()
        mock_chef.pk = 3
        self.test_project.chef_projet = mock_chef

        mock_commentaire = Mock()
        mock_commentaire.ticket = self.test_ticket
        mock_commentaire.mentions = Mock()
        mock_commentaire.mentions.all.return_value = []

        result = NotificationService.notifier_commentaire_ticket(
            commentaire=mock_commentaire,
            auteur=mock_auteur
        )

        mock_creer.assert_called()
        self.assertIsInstance(result, list)

    @patch.object(NotificationService, '_creer_notification')
    @patch.object(NotificationService, '_get_equipe_employe')
    def test_notifier_commentaire_ticket_mentions(self, mock_equipe, mock_creer):
        """Test la notification avec des mentions."""
        mock_creer.return_value = Mock()
        mock_equipe.return_value = []

        mock_auteur = Mock()
        mock_auteur.pk = 1

        mock_mentionne = Mock()
        mock_mentionne.pk = 4

        mock_assigne = Mock()
        mock_assigne.pk = 2
        self.test_ticket.assigne = mock_assigne

        mock_chef = Mock()
        mock_chef.pk = 3
        self.test_project.chef_projet = mock_chef

        mock_commentaire = Mock()
        mock_commentaire.ticket = self.test_ticket
        mock_commentaire.mentions = Mock()
        mock_commentaire.mentions.all.return_value = [mock_mentionne]

        result = NotificationService.notifier_commentaire_ticket(
            commentaire=mock_commentaire,
            auteur=mock_auteur
        )

        # Doit notifier les personnes mentionnées
        self.assertTrue(mock_creer.call_count >= 1)


class NotificationServiceEcheanceTest(NotificationServiceTestCase):
    """Tests pour les notifications d'échéance."""

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_echeance_proche_today(self, mock_creer):
        """Test la notification d'échéance pour aujourd'hui."""
        mock_creer.return_value = Mock()

        mock_assigne = Mock()
        mock_assigne.pk = 1
        self.test_ticket.assigne = mock_assigne
        self.test_ticket.date_echeance = timezone.now().date()

        result = NotificationService.notifier_echeance_proche(
            ticket=self.test_ticket,
            jours_restants=0
        )

        mock_creer.assert_called()
        # Vérifier que le message contient "aujourd'hui"
        call_args = mock_creer.call_args
        self.assertIn("aujourd'hui", call_args.kwargs['message'])

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_echeance_proche_tomorrow(self, mock_creer):
        """Test la notification d'échéance pour demain."""
        mock_creer.return_value = Mock()

        mock_assigne = Mock()
        mock_assigne.pk = 1
        self.test_ticket.assigne = mock_assigne
        self.test_ticket.date_echeance = timezone.now().date()

        result = NotificationService.notifier_echeance_proche(
            ticket=self.test_ticket,
            jours_restants=1
        )

        mock_creer.assert_called()
        # Vérifier que le message contient "demain"
        call_args = mock_creer.call_args
        self.assertIn("demain", call_args.kwargs['message'])

    @patch.object(NotificationService, '_creer_notification')
    def test_notifier_echeance_proche_several_days(self, mock_creer):
        """Test la notification d'échéance pour plusieurs jours."""
        mock_creer.return_value = Mock()

        mock_assigne = Mock()
        mock_assigne.pk = 1
        self.test_ticket.assigne = mock_assigne
        self.test_ticket.date_echeance = timezone.now().date()

        result = NotificationService.notifier_echeance_proche(
            ticket=self.test_ticket,
            jours_restants=5
        )

        mock_creer.assert_called()
        # Vérifier que le message contient "5 jours"
        call_args = mock_creer.call_args
        self.assertIn("5 jours", call_args.kwargs['message'])

    def test_notifier_echeance_no_assignee(self):
        """Test que pas de notification sans assigné."""
        self.test_ticket.assigne = None
        self.test_ticket.date_echeance = timezone.now().date()

        result = NotificationService.notifier_echeance_proche(
            ticket=self.test_ticket,
            jours_restants=1
        )

        self.assertEqual(result, [])

    def test_notifier_echeance_no_date(self):
        """Test que pas de notification sans date d'échéance."""
        mock_assigne = Mock()
        self.test_ticket.assigne = mock_assigne
        self.test_ticket.date_echeance = None

        result = NotificationService.notifier_echeance_proche(
            ticket=self.test_ticket,
            jours_restants=1
        )

        self.assertEqual(result, [])


class NotificationServiceHelperMethodsTest(NotificationServiceTestCase):
    """Tests pour les méthodes helper du service de notifications."""

    def test_get_equipe_employe_no_employe(self):
        """Test _get_equipe_employe sans employé."""
        result = NotificationService._get_equipe_employe(None)
        self.assertEqual(result, [])

    def test_get_manager_employe_no_employe(self):
        """Test _get_manager_employe sans employé."""
        result = NotificationService._get_manager_employe(None)
        self.assertIsNone(result)

    @patch('project_management.services.notification_service.ZYAF')
    @patch('project_management.services.notification_service.ZY00')
    def test_get_equipe_employe_with_valid_employe(self, mock_zy00, mock_zyaf):
        """Test _get_equipe_employe avec un employé valide."""
        mock_employe = Mock()
        mock_employe.get_departement_actuel.return_value = Mock()

        mock_zyaf.objects.filter.return_value.exclude.return_value.values_list.return_value.distinct.return_value = [1, 2]
        mock_zy00.objects.filter.return_value = [Mock(), Mock()]

        result = NotificationService._get_equipe_employe(mock_employe)

        self.assertIsInstance(result, list)
