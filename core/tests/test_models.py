# core/tests/test_models.py
"""
Tests pour le modèle ZDLOG (système d'audit).
"""
from datetime import datetime
from unittest.mock import Mock, MagicMock

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from core.models import ZDLOG

User = get_user_model()


class TestZDLOGModel(TestCase):
    """Tests pour le modèle ZDLOG."""

    def test_model_exists(self):
        """Test que le modèle ZDLOG existe."""
        self.assertIsNotNone(ZDLOG)

    def test_type_constants(self):
        """Test que les constantes de type existent."""
        self.assertEqual(ZDLOG.TYPE_CREATION, 'CREATE')
        self.assertEqual(ZDLOG.TYPE_MODIFICATION, 'UPDATE')
        self.assertEqual(ZDLOG.TYPE_SUPPRESSION, 'DELETE')

    def test_type_choices(self):
        """Test que les choix de type sont corrects."""
        expected = [
            ('CREATE', 'Création'),
            ('UPDATE', 'Modification'),
            ('DELETE', 'Suppression'),
        ]
        self.assertEqual(ZDLOG.TYPE_CHOICES, expected)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        self.assertEqual(ZDLOG._meta.db_table, 'ZDLOG')

    def test_meta_ordering(self):
        """Test que l'ordering par défaut est correct."""
        self.assertEqual(ZDLOG._meta.ordering, ['-DATE_MODIFICATION'])

    def test_str_representation(self):
        """Test la représentation string du modèle."""
        log = ZDLOG(
            TABLE_NAME='ZY00',
            RECORD_ID='123',
            TYPE_MOUVEMENT=ZDLOG.TYPE_CREATION,
            USER_NAME='John Doe'
        )
        str_repr = str(log)
        self.assertIn('ZY00', str_repr)
        self.assertIn('123', str_repr)
        self.assertIn('John Doe', str_repr)

    def test_str_representation_no_user(self):
        """Test la représentation string sans utilisateur."""
        log = ZDLOG(
            TABLE_NAME='ZY00',
            RECORD_ID='123',
            TYPE_MOUVEMENT=ZDLOG.TYPE_CREATION,
        )
        str_repr = str(log)
        self.assertIn('Système', str_repr)


class TestZDLOGLogAction(TestCase):
    """Tests pour la méthode log_action."""

    def test_log_action_creation(self):
        """Test création d'un log via log_action."""
        log = ZDLOG.log_action(
            table_name='TestTable',
            record_id='1',
            type_mouvement=ZDLOG.TYPE_CREATION,
            description='Test creation'
        )

        self.assertIsNotNone(log)
        self.assertIsNotNone(log.pk)
        self.assertEqual(log.TABLE_NAME, 'TestTable')
        self.assertEqual(log.RECORD_ID, '1')
        self.assertEqual(log.TYPE_MOUVEMENT, ZDLOG.TYPE_CREATION)
        self.assertEqual(log.DESCRIPTION, 'Test creation')

    def test_log_action_with_user(self):
        """Test log_action avec un utilisateur."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        log = ZDLOG.log_action(
            table_name='TestTable',
            record_id='2',
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            description='Test modification'
        )

        self.assertEqual(log.USER, user)
        self.assertIn('Test', log.USER_NAME)

    def test_log_action_with_request(self):
        """Test log_action avec une requête HTTP."""
        factory = RequestFactory()
        request = factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        log = ZDLOG.log_action(
            table_name='TestTable',
            record_id='3',
            type_mouvement=ZDLOG.TYPE_SUPPRESSION,
            request=request,
            description='Test suppression'
        )

        self.assertEqual(log.IP_ADDRESS, '192.168.1.1')

    def test_log_action_with_x_forwarded_for(self):
        """Test log_action avec X-Forwarded-For."""
        factory = RequestFactory()
        request = factory.get('/test/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'

        log = ZDLOG.log_action(
            table_name='TestTable',
            record_id='4',
            type_mouvement=ZDLOG.TYPE_CREATION,
            request=request,
            description='Test with proxy'
        )

        self.assertEqual(log.IP_ADDRESS, '10.0.0.1')

    def test_log_action_with_json_values(self):
        """Test log_action avec valeurs JSON."""
        ancienne = {'nom': 'Ancien', 'age': 25}
        nouvelle = {'nom': 'Nouveau', 'age': 26}

        log = ZDLOG.log_action(
            table_name='TestTable',
            record_id='5',
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            ancienne_valeur=ancienne,
            nouvelle_valeur=nouvelle,
            description='Test JSON values'
        )

        self.assertEqual(log.ANCIENNE_VALEUR, ancienne)
        self.assertEqual(log.NOUVELLE_VALEUR, nouvelle)

    def test_log_action_record_id_conversion(self):
        """Test que record_id est converti en string."""
        log = ZDLOG.log_action(
            table_name='TestTable',
            record_id=12345,  # Integer
            type_mouvement=ZDLOG.TYPE_CREATION,
            description='Test int conversion'
        )

        self.assertEqual(log.RECORD_ID, '12345')
        self.assertIsInstance(log.RECORD_ID, str)


class TestZDLOGQueryset(TestCase):
    """Tests pour les requêtes sur ZDLOG."""

    def setUp(self):
        """Créer des logs pour les tests."""
        ZDLOG.log_action(
            table_name='ZY00',
            record_id='1',
            type_mouvement=ZDLOG.TYPE_CREATION,
            description='Creation employé 1'
        )
        ZDLOG.log_action(
            table_name='ZY00',
            record_id='2',
            type_mouvement=ZDLOG.TYPE_CREATION,
            description='Creation employé 2'
        )
        ZDLOG.log_action(
            table_name='ZDDE',
            record_id='1',
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            description='Modification département'
        )

    def test_filter_by_table_name(self):
        """Test filtrage par nom de table."""
        zy00_logs = ZDLOG.objects.filter(TABLE_NAME='ZY00')
        self.assertEqual(zy00_logs.count(), 2)

    def test_filter_by_type_mouvement(self):
        """Test filtrage par type de mouvement."""
        creation_logs = ZDLOG.objects.filter(TYPE_MOUVEMENT=ZDLOG.TYPE_CREATION)
        self.assertEqual(creation_logs.count(), 2)

    def test_filter_by_record_id(self):
        """Test filtrage par record_id."""
        logs = ZDLOG.objects.filter(TABLE_NAME='ZY00', RECORD_ID='1')
        self.assertEqual(logs.count(), 1)

    def test_ordering(self):
        """Test que les logs sont ordonnés par date décroissante."""
        logs = list(ZDLOG.objects.all())
        for i in range(len(logs) - 1):
            self.assertGreaterEqual(
                logs[i].DATE_MODIFICATION,
                logs[i + 1].DATE_MODIFICATION
            )


class TestZDLOGIndexes(TestCase):
    """Tests pour les index du modèle ZDLOG."""

    def test_indexes_exist(self):
        """Test que les index sont définis."""
        indexes = ZDLOG._meta.indexes
        self.assertGreater(len(indexes), 0)

    def test_index_fields(self):
        """Test les champs indexés."""
        index_fields = []
        for index in ZDLOG._meta.indexes:
            index_fields.extend(index.fields)

        self.assertIn('TABLE_NAME', index_fields)
        self.assertIn('RECORD_ID', index_fields)
        self.assertIn('DATE_MODIFICATION', index_fields)
        self.assertIn('USER', index_fields)
        self.assertIn('TYPE_MOUVEMENT', index_fields)
