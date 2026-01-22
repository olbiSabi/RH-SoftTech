# gestion_temps_activite/tests/test_services.py
"""
Tests pour les services de l'application Gestion Temps et Activités.
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from gestion_temps_activite.services import (
    NotificationService,
    ImputationService,
    StatistiqueService,
    CommentaireService
)


class TestNotificationService(TestCase):
    """Tests pour NotificationService."""

    def test_constants_defined(self):
        """Test que les constantes de type sont définies."""
        self.assertEqual(NotificationService.TYPE_TACHE_ASSIGNEE, 'TACHE_ASSIGNEE')
        self.assertEqual(NotificationService.TYPE_TACHE_REASSIGNEE, 'TACHE_REASSIGNEE')
        self.assertEqual(NotificationService.TYPE_TACHE_MODIFIEE, 'TACHE_MODIFIEE')
        self.assertEqual(NotificationService.TYPE_STATUT_CHANGE, 'STATUT_TACHE_CHANGE')
        self.assertEqual(NotificationService.TYPE_COMMENTAIRE, 'COMMENTAIRE_TACHE')
        self.assertEqual(NotificationService.TYPE_ECHEANCE_PROCHE, 'ECHEANCE_TACHE_PROCHE')

    def test_messages_statut_defined(self):
        """Test que les messages de statut sont définis."""
        self.assertIn(('A_FAIRE', 'EN_COURS'), NotificationService.MESSAGES_STATUT)
        self.assertIn(('EN_COURS', 'TERMINE'), NotificationService.MESSAGES_STATUT)
        self.assertIn(('EN_COURS', 'EN_ATTENTE'), NotificationService.MESSAGES_STATUT)

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_nouvelle_tache_sans_assignee(self, mock_notif):
        """Test notification nouvelle tâche sans assigné."""
        mock_tache = Mock()
        mock_tache.assignee = None

        result = NotificationService.notifier_nouvelle_tache(mock_tache, Mock())

        self.assertIsNone(result)
        mock_notif.creer_notification.assert_not_called()

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_nouvelle_tache_avec_assignee(self, mock_notif):
        """Test notification nouvelle tâche avec assigné."""
        mock_tache = Mock()
        mock_tache.assignee = Mock()
        mock_tache.titre = "Tâche Test"

        NotificationService.notifier_nouvelle_tache(mock_tache, Mock())

        mock_notif.creer_notification.assert_called_once()
        call_kwargs = mock_notif.creer_notification.call_args.kwargs
        self.assertEqual(call_kwargs['destinataire'], mock_tache.assignee)
        self.assertEqual(call_kwargs['type_notif'], 'TACHE_ASSIGNEE')
        self.assertIn('Tâche Test', call_kwargs['message'])

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_reassignation_nouvel_assignee(self, mock_notif):
        """Test notification réassignation au nouvel assigné."""
        mock_tache = Mock()
        mock_tache.titre = "Tâche Test"
        ancien = Mock()
        nouveau = Mock()

        notifications = NotificationService.notifier_reassignation(mock_tache, ancien, nouveau)

        # Doit notifier le nouveau ET l'ancien
        self.assertEqual(mock_notif.creer_notification.call_count, 2)

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_modification_meme_employe(self, mock_notif):
        """Test pas de notification si même employé."""
        mock_tache = Mock()
        mock_tache.assignee = Mock()

        result = NotificationService.notifier_modification(mock_tache, mock_tache.assignee, ['titre'])

        self.assertIsNone(result)
        mock_notif.creer_notification.assert_not_called()

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_changement_statut_connu(self, mock_notif):
        """Test notification changement statut connu."""
        mock_tache = Mock()
        mock_tache.assignee = Mock()
        mock_tache.titre = "Tâche Test"

        NotificationService.notifier_changement_statut(mock_tache, 'A_FAIRE', 'EN_COURS')

        mock_notif.creer_notification.assert_called_once()

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_changement_statut_inconnu(self, mock_notif):
        """Test pas de notification pour statut inconnu."""
        mock_tache = Mock()
        mock_tache.assignee = Mock()

        result = NotificationService.notifier_changement_statut(mock_tache, 'INCONNU', 'AUTRE')

        self.assertIsNone(result)
        mock_notif.creer_notification.assert_not_called()

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_echeance_proche_dans_delai(self, mock_notif):
        """Test notification échéance dans le délai."""
        mock_tache = Mock()
        mock_tache.assignee = Mock()
        mock_tache.date_fin_prevue = date.today()
        mock_tache.titre = "Tâche Test"

        NotificationService.notifier_echeance_proche(mock_tache, 1)

        mock_notif.creer_notification.assert_called_once()

    @patch('gestion_temps_activite.services.notification_service.NotificationAbsence')
    def test_notifier_echeance_hors_delai(self, mock_notif):
        """Test pas de notification échéance hors délai."""
        mock_tache = Mock()
        mock_tache.assignee = Mock()
        mock_tache.date_fin_prevue = date.today() + timedelta(days=10)

        result = NotificationService.notifier_echeance_proche(mock_tache, 10)

        self.assertIsNone(result)


class TestImputationService(TestCase):
    """Tests pour ImputationService."""

    def test_valider_imputation_deja_validee(self):
        """Test validation imputation déjà validée."""
        mock_imputation = Mock()
        mock_imputation.valide = True

        result = ImputationService.valider_imputation(mock_imputation, Mock())

        self.assertFalse(result)
        mock_imputation.save.assert_not_called()

    def test_valider_imputation_success(self):
        """Test validation imputation réussie."""
        mock_imputation = Mock()
        mock_imputation.valide = False
        mock_validateur = Mock()

        result = ImputationService.valider_imputation(mock_imputation, mock_validateur)

        self.assertTrue(result)
        self.assertTrue(mock_imputation.valide)
        self.assertEqual(mock_imputation.valide_par, mock_validateur)
        mock_imputation.save.assert_called_once()

    def test_rejeter_imputation_sans_motif(self):
        """Test rejet sans motif échoue."""
        mock_imputation = Mock()

        result = ImputationService.rejeter_imputation(mock_imputation, '')

        self.assertFalse(result)
        mock_imputation.save.assert_not_called()

    def test_rejeter_imputation_avec_motif(self):
        """Test rejet avec motif réussi."""
        mock_imputation = Mock()
        mock_imputation.commentaire = "Ancien commentaire"

        result = ImputationService.rejeter_imputation(mock_imputation, "Motif de rejet")

        self.assertTrue(result)
        self.assertIn('[REJETÉ]', mock_imputation.commentaire)
        mock_imputation.save.assert_called_once()

    def test_peut_modifier_valide(self):
        """Test modification imputation validée impossible."""
        mock_imputation = Mock()
        mock_imputation.valide = True
        mock_imputation.facture = False

        result = ImputationService.peut_modifier(mock_imputation, Mock())

        self.assertFalse(result)

    def test_peut_modifier_facture(self):
        """Test modification imputation facturée impossible."""
        mock_imputation = Mock()
        mock_imputation.valide = False
        mock_imputation.facture = True

        result = ImputationService.peut_modifier(mock_imputation, Mock())

        self.assertFalse(result)

    def test_peut_modifier_proprietaire(self):
        """Test modification par propriétaire autorisée."""
        mock_employe = Mock()
        mock_imputation = Mock()
        mock_imputation.valide = False
        mock_imputation.facture = False
        mock_imputation.employe = mock_employe

        result = ImputationService.peut_modifier(mock_imputation, mock_employe)

        self.assertTrue(result)

    def test_peut_modifier_drh(self):
        """Test modification par DRH autorisée."""
        mock_employe = Mock()
        mock_employe.has_role = Mock(side_effect=lambda r: r == 'DRH')
        mock_imputation = Mock()
        mock_imputation.valide = False
        mock_imputation.facture = False
        mock_imputation.employe = Mock()

        result = ImputationService.peut_modifier(mock_imputation, mock_employe)

        self.assertTrue(result)

    def test_get_dates_periode_semaine(self):
        """Test calcul dates période semaine."""
        date_test = date(2024, 1, 15)  # Lundi

        debut, fin = ImputationService.get_dates_periode('semaine', date_test)

        self.assertEqual(debut.weekday(), 0)  # Lundi
        self.assertEqual(fin.weekday(), 6)  # Dimanche
        self.assertEqual((fin - debut).days, 6)

    def test_get_dates_periode_mois(self):
        """Test calcul dates période mois."""
        date_test = date(2024, 3, 15)

        debut, fin = ImputationService.get_dates_periode('mois', date_test)

        self.assertEqual(debut.day, 1)
        self.assertEqual(debut.month, 3)
        self.assertEqual(fin.month, 3)
        self.assertEqual(fin.day, 31)

    def test_get_dates_periode_annee(self):
        """Test calcul dates période année."""
        date_test = date(2024, 6, 15)

        debut, fin = ImputationService.get_dates_periode('annee', date_test)

        self.assertEqual(debut.month, 1)
        self.assertEqual(debut.day, 1)
        self.assertEqual(fin.month, 12)
        self.assertEqual(fin.day, 31)

    def test_calculer_montant_facturable_non_facturable(self):
        """Test montant facturable = 0 si non facturable."""
        mock_imputation = Mock()
        mock_imputation.facturable = False

        result = ImputationService.calculer_montant_facturable(mock_imputation)

        self.assertEqual(result, 0)

    def test_calculer_montant_facturable_success(self):
        """Test calcul montant facturable."""
        mock_imputation = Mock()
        mock_imputation.facturable = True
        mock_imputation.duree = Decimal('8')
        mock_imputation.taux_horaire_applique = Decimal('50')

        result = ImputationService.calculer_montant_facturable(mock_imputation)

        self.assertEqual(result, 400.0)


class TestStatistiqueService(TestCase):
    """Tests pour StatistiqueService."""

    def test_get_stats_dashboard(self):
        """Test statistiques dashboard."""
        stats = StatistiqueService.get_stats_dashboard()

        self.assertIn('total_clients', stats)
        self.assertIn('total_projets', stats)
        self.assertIn('projets_en_cours', stats)
        self.assertIn('total_taches', stats)
        # Toutes les valeurs doivent être des entiers
        self.assertIsInstance(stats['total_clients'], int)
        self.assertIsInstance(stats['total_projets'], int)

    def test_get_stats_client(self):
        """Test statistiques client."""
        mock_client = Mock()
        mock_projets = Mock()
        mock_projets.count.return_value = 5
        mock_projets.filter.return_value.count.return_value = 3
        mock_client.projets.all.return_value = mock_projets

        stats = StatistiqueService.get_stats_client(mock_client)

        self.assertEqual(stats['total_projets'], 5)

    def test_annotate_projets_stats(self):
        """Test annotation projets."""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset

        result = StatistiqueService.annotate_projets_stats(mock_queryset)

        mock_queryset.annotate.assert_called_once()

    def test_annotate_taches_stats(self):
        """Test annotation tâches."""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset

        result = StatistiqueService.annotate_taches_stats(mock_queryset)

        mock_queryset.annotate.assert_called_once()

    def test_annotate_clients_stats(self):
        """Test annotation clients."""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset

        result = StatistiqueService.annotate_clients_stats(mock_queryset)

        mock_queryset.annotate.assert_called_once()


class TestCommentaireService(TestCase):
    """Tests pour CommentaireService."""

    def test_peut_voir_prives_sans_employe(self):
        """Test visibilité privés sans employé."""
        result = CommentaireService.peut_voir_commentaires_prives(None, Mock())

        self.assertFalse(result)

    def test_peut_voir_prives_assignee(self):
        """Test visibilité privés si assigné."""
        mock_employe = Mock()
        mock_tache = Mock()
        mock_tache.assignee = mock_employe
        mock_tache.projet = None

        result = CommentaireService.peut_voir_commentaires_prives(mock_employe, mock_tache)

        self.assertTrue(result)

    def test_peut_voir_prives_chef_projet(self):
        """Test visibilité privés si chef projet."""
        mock_employe = Mock()
        mock_employe.has_role = Mock(return_value=False)
        mock_employe.est_manager_departement = Mock(return_value=False)
        mock_tache = Mock()
        mock_tache.assignee = Mock()
        mock_tache.projet.chef_projet = mock_employe

        result = CommentaireService.peut_voir_commentaires_prives(mock_employe, mock_tache)

        self.assertTrue(result)

    def test_peut_voir_prives_drh(self):
        """Test visibilité privés si DRH."""
        mock_employe = Mock()
        mock_employe.has_role = Mock(side_effect=lambda r: r == 'DRH')
        mock_employe.est_manager_departement = Mock(return_value=False)
        mock_tache = Mock()
        mock_tache.assignee = Mock()
        mock_tache.projet = None

        result = CommentaireService.peut_voir_commentaires_prives(mock_employe, mock_tache)

        self.assertTrue(result)

    def test_peut_ajouter_commentaire_sans_employe(self):
        """Test ajout commentaire sans employé."""
        result = CommentaireService.peut_ajouter_commentaire(None, Mock())

        self.assertFalse(result)

    def test_peut_ajouter_commentaire_assignee(self):
        """Test ajout commentaire si assigné."""
        mock_employe = Mock()
        mock_tache = Mock()
        mock_tache.assignee = mock_employe
        mock_tache.projet = None

        result = CommentaireService.peut_ajouter_commentaire(mock_employe, mock_tache)

        self.assertTrue(result)

    def test_extraire_mentions_simple(self):
        """Test extraction mentions simples."""
        contenu = "Hello @Jean Dupont, comment vas-tu?"

        mentions = CommentaireService.extraire_mentions(contenu)

        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0], "Jean Dupont")

    def test_extraire_mentions_multiples(self):
        """Test extraction mentions multiples."""
        contenu = "@Alice et @Bob, pouvez-vous regarder?"

        mentions = CommentaireService.extraire_mentions(contenu)

        self.assertEqual(len(mentions), 2)

    def test_extraire_mentions_aucune(self):
        """Test extraction sans mention."""
        contenu = "Un commentaire simple sans mention"

        mentions = CommentaireService.extraire_mentions(contenu)

        self.assertEqual(len(mentions), 0)

    def test_extraire_mentions_accents(self):
        """Test extraction mentions avec accents."""
        contenu = "@André et @Marie-Claire regardent"

        mentions = CommentaireService.extraire_mentions(contenu)

        self.assertEqual(len(mentions), 2)
        self.assertIn("André", mentions[0])

    def test_get_details_visibilite_assignee(self):
        """Test détails visibilité assigné."""
        mock_employe = Mock()
        mock_employe.has_role = Mock(return_value=False)
        mock_employe.est_manager_departement = Mock(return_value=False)
        mock_employe.get_departement_actuel = Mock(return_value=None)
        mock_tache = Mock()
        mock_tache.assignee = mock_employe
        mock_tache.projet = None

        details = CommentaireService.get_details_visibilite(mock_employe, mock_tache)

        self.assertIn("Vous êtes assigné à cette tâche", details)

    def test_rechercher_mentions_autocomplete_query_courte(self):
        """Test autocomplete avec query trop courte."""
        result = CommentaireService.rechercher_mentions_autocomplete('a')

        self.assertEqual(result, [])

    def test_peut_modifier_commentaire_sans_employe(self):
        """Test modification commentaire sans employé."""
        result = CommentaireService.peut_modifier_commentaire(None, Mock())

        self.assertFalse(result)

    def test_peut_supprimer_commentaire_sans_employe(self):
        """Test suppression commentaire sans employé."""
        result = CommentaireService.peut_supprimer_commentaire(None, Mock())

        self.assertFalse(result)
