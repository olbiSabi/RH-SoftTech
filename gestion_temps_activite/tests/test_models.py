# gestion_temps_activite/tests/test_models.py
"""
Tests pour les modèles de l'application Gestion Temps et Activités.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from gestion_temps_activite.models import (
    ZDCL, ZDAC, ZDPJ, ZDTA, ZDDO, ZDIT, ZDCM
)


class TestZDCLModel(TestCase):
    """Tests pour le modèle Client (ZDCL)."""

    def test_model_exists(self):
        """Test que le modèle ZDCL existe."""
        self.assertIsNotNone(ZDCL)

    def test_type_client_field_has_choices(self):
        """Test que le champ type_client a des choix définis."""
        field = ZDCL._meta.get_field('type_client')
        self.assertIsNotNone(field.choices)
        self.assertGreater(len(field.choices), 0)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        # Les tables sont en minuscules par défaut
        self.assertEqual(ZDCL._meta.db_table, 'zdcl')

    def test_str_representation(self):
        """Test la représentation string du modèle."""
        client = ZDCL(
            code_client='CLT-001',
            raison_sociale='Test Company'
        )
        str_repr = str(client)
        self.assertIn('CLT-001', str_repr)
        self.assertIn('Test Company', str_repr)


class TestZDACModel(TestCase):
    """Tests pour le modèle Type d'Activité (ZDAC)."""

    def test_model_exists(self):
        """Test que le modèle ZDAC existe."""
        self.assertIsNotNone(ZDAC)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        self.assertEqual(ZDAC._meta.db_table, 'zdac')

    def test_str_representation(self):
        """Test la représentation string du modèle."""
        activite = ZDAC(
            code_activite='DEV',
            libelle='Développement'
        )
        str_repr = str(activite)
        self.assertIn('DEV', str_repr)


class TestZDPJModel(TestCase):
    """Tests pour le modèle Projet (ZDPJ)."""

    def test_model_exists(self):
        """Test que le modèle ZDPJ existe."""
        self.assertIsNotNone(ZDPJ)

    def test_statut_field_has_choices(self):
        """Test que le champ statut a des choix définis."""
        field = ZDPJ._meta.get_field('statut')
        self.assertIsNotNone(field.choices)
        self.assertGreater(len(field.choices), 0)

    def test_priorite_field_has_choices(self):
        """Test que le champ priorite a des choix définis."""
        field = ZDPJ._meta.get_field('priorite')
        self.assertIsNotNone(field.choices)
        self.assertGreater(len(field.choices), 0)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        self.assertEqual(ZDPJ._meta.db_table, 'zdpj')

    def test_str_representation(self):
        """Test la représentation string du modèle."""
        projet = ZDPJ(
            code_projet='PRJ-001',
            nom_projet='Projet Test'
        )
        str_repr = str(projet)
        self.assertIn('PRJ-001', str_repr)


class TestZDTAModel(TestCase):
    """Tests pour le modèle Tâche (ZDTA)."""

    def test_model_exists(self):
        """Test que le modèle ZDTA existe."""
        self.assertIsNotNone(ZDTA)

    def test_statut_field_has_choices(self):
        """Test que le champ statut a des choix définis."""
        field = ZDTA._meta.get_field('statut')
        self.assertIsNotNone(field.choices)
        self.assertGreater(len(field.choices), 0)

    def test_priorite_field_has_choices(self):
        """Test que le champ priorite a des choix définis."""
        field = ZDTA._meta.get_field('priorite')
        self.assertIsNotNone(field.choices)
        self.assertGreater(len(field.choices), 0)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        self.assertEqual(ZDTA._meta.db_table, 'zdta')

    def test_str_representation(self):
        """Test la représentation string du modèle."""
        tache = ZDTA(
            code_tache='TASK-0001',
            titre='Tâche Test'
        )
        str_repr = str(tache)
        self.assertIn('TASK-0001', str_repr)


class TestZDDOModel(TestCase):
    """Tests pour le modèle Document (ZDDO)."""

    def test_model_exists(self):
        """Test que le modèle ZDDO existe."""
        self.assertIsNotNone(ZDDO)

    def test_type_rattachement_field_has_choices(self):
        """Test que le champ type_rattachement a des choix définis."""
        field = ZDDO._meta.get_field('type_rattachement')
        self.assertIsNotNone(field.choices)
        self.assertGreater(len(field.choices), 0)

    def test_categorie_field_has_choices(self):
        """Test que le champ categorie a des choix définis."""
        field = ZDDO._meta.get_field('categorie')
        self.assertIsNotNone(field.choices)
        self.assertGreater(len(field.choices), 0)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        self.assertEqual(ZDDO._meta.db_table, 'zddo')


class TestZDITModel(TestCase):
    """Tests pour le modèle Imputation Temps (ZDIT)."""

    def test_model_exists(self):
        """Test que le modèle ZDIT existe."""
        self.assertIsNotNone(ZDIT)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        self.assertEqual(ZDIT._meta.db_table, 'zdit')

    def test_ordering_defined(self):
        """Test que l'ordering par défaut est défini."""
        self.assertIsNotNone(ZDIT._meta.ordering)


class TestZDCMModel(TestCase):
    """Tests pour le modèle Commentaire (ZDCM)."""

    def test_model_exists(self):
        """Test que le modèle ZDCM existe."""
        self.assertIsNotNone(ZDCM)

    def test_meta_db_table(self):
        """Test que la table DB est correcte."""
        self.assertEqual(ZDCM._meta.db_table, 'zdcm')

    def test_ordering_defined(self):
        """Test que l'ordering par défaut est défini."""
        self.assertIsNotNone(ZDCM._meta.ordering)

    def test_has_queryset_manager(self):
        """Test que le manager personnalisé existe."""
        self.assertTrue(hasattr(ZDCM, 'objects'))


class TestModelsRelations(TestCase):
    """Tests pour les relations entre modèles."""

    def test_zdpj_has_client_relation(self):
        """Test que ZDPJ a une relation vers ZDCL."""
        field = ZDPJ._meta.get_field('client')
        self.assertIsNotNone(field)

    def test_zdta_has_projet_relation(self):
        """Test que ZDTA a une relation vers ZDPJ."""
        field = ZDTA._meta.get_field('projet')
        self.assertIsNotNone(field)

    def test_zdta_has_assignee_relation(self):
        """Test que ZDTA a une relation vers ZY00."""
        field = ZDTA._meta.get_field('assignee')
        self.assertIsNotNone(field)

    def test_zdit_has_tache_relation(self):
        """Test que ZDIT a une relation vers ZDTA."""
        field = ZDIT._meta.get_field('tache')
        self.assertIsNotNone(field)

    def test_zdit_has_employe_relation(self):
        """Test que ZDIT a une relation vers ZY00."""
        field = ZDIT._meta.get_field('employe')
        self.assertIsNotNone(field)

    def test_zdcm_has_tache_relation(self):
        """Test que ZDCM a une relation vers ZDTA."""
        field = ZDCM._meta.get_field('tache')
        self.assertIsNotNone(field)

    def test_zdcm_has_employe_relation(self):
        """Test que ZDCM a une relation vers ZY00 (employe)."""
        field = ZDCM._meta.get_field('employe')
        self.assertIsNotNone(field)

    def test_zdcm_has_mentions_relation(self):
        """Test que ZDCM a une relation ManyToMany pour les mentions."""
        field = ZDCM._meta.get_field('mentions')
        self.assertIsNotNone(field)
        self.assertTrue(field.many_to_many)
