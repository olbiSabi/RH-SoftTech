from django.test import TestCase
from django.core.exceptions import ValidationError
from ..forms import ClientForm, ProjetForm
from ..models import JRClient, JRProject


class ClientFormTest(TestCase):
    """Tests pour le formulaire ClientForm"""
    
    def test_valid_client_form(self):
        """Test un formulaire client valide"""
        form_data = {
            'raison_sociale': 'Test Client',
            'contact_principal': 'John Doe',
            'email_contact': 'john@test.com',
            'statut': 'ACTIF'
        }
        form = ClientForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_client_form_missing_required(self):
        """Test un formulaire client invalide (champ requis manquant)"""
        form_data = {
            'contact_principal': 'John Doe',
            'email_contact': 'john@test.com',
        }
        form = ClientForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('raison_sociale', form.errors)


class ProjetFormTest(TestCase):
    """Tests pour le formulaire ProjetForm"""
    
    def setUp(self):
        self.client = JRClient.objects.create(
            raison_sociale='Test Client',
            statut='ACTIF'
        )
    
    def test_valid_projet_form(self):
        """Test un formulaire projet valide"""
        form_data = {
            'nom': 'Test Project',
            'client': self.client.id,
            'statut': 'PLANIFIE'
        }
        form = ProjetForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_date_range(self):
        """Test une plage de dates invalide"""
        form_data = {
            'nom': 'Test Project',
            'client': self.client.id,
            'statut': 'PLANIFIE',
            'date_debut': '2024-12-31',
            'date_fin_prevue': '2024-01-01'
        }
        form = ProjetForm(data=form_data)
        self.assertFalse(form.is_valid())
