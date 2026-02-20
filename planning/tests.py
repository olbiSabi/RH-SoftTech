"""
Tests pour le module Planning.
Couvre: modeles, formulaires, permissions et vues.
"""
from datetime import date, time, timedelta
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone

from employee.tests.base import EmployeeTestCase
from planning.models import Planning, SiteTravail, PosteTravail, Affectation, Evenement
from planning.forms import (
    SiteTravailForm, PosteTravailForm, PlanningForm,
    AffectationForm, EvenementForm
)
from planning.permissions import get_planning_role, can_edit_planning


# ============================================================
# TESTS MODELES
# ============================================================

class SiteTravailModelTest(TestCase):
    """Tests pour le modele SiteTravail."""

    def test_creation_site(self):
        site = SiteTravail.objects.create(nom='Siege Lome', adresse='123 rue Test')
        self.assertEqual(str(site), 'Siege Lome')
        self.assertTrue(site.is_active)
        self.assertEqual(site.fuseau_horaire, 'Africa/Lome')

    def test_str_representation(self):
        site = SiteTravail.objects.create(nom='Agence Kara')
        self.assertEqual(str(site), 'Agence Kara')

    def test_ordering(self):
        SiteTravail.objects.create(nom='Zebra')
        SiteTravail.objects.create(nom='Alpha')
        sites = list(SiteTravail.objects.values_list('nom', flat=True))
        self.assertEqual(sites, ['Alpha', 'Zebra'])


class PosteTravailModelTest(TestCase):
    """Tests pour le modele PosteTravail."""

    @classmethod
    def setUpTestData(cls):
        cls.site = SiteTravail.objects.create(nom='Siege')

    def test_creation_poste(self):
        poste = PosteTravail.objects.create(
            nom='Accueil Matin', site=self.site,
            heure_debut=time(8, 0), heure_fin=time(12, 0)
        )
        self.assertEqual(str(poste), 'Accueil Matin (Siege)')
        self.assertEqual(poste.type_poste, 'JOURNEE')
        self.assertTrue(poste.is_active)

    def test_duree_travail(self):
        poste = PosteTravail.objects.create(
            nom='Standard', site=self.site,
            heure_debut=time(9, 0), heure_fin=time(17, 0),
            pause_dejeune=timedelta(minutes=30)
        )
        # 8h - 0.5h pause = 7.5h
        self.assertAlmostEqual(poste.duree_travail, 7.5, places=1)


class PlanningModelTest(TestCase):
    """Tests pour le modele Planning."""

    def test_creation_planning_auto_reference(self):
        planning = Planning.objects.create(
            titre='Planning Janvier',
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 1, 31),
        )
        self.assertTrue(planning.REFERENCE.startswith('PLN-2026-'))
        self.assertEqual(planning.statut, 'BROUILLON')

    def test_str_representation(self):
        planning = Planning.objects.create(
            titre='Planning Test',
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 1, 31),
        )
        self.assertIn('Planning Test', str(planning))
        self.assertIn('PLN-', str(planning))

    def test_nombre_semaines(self):
        planning = Planning.objects.create(
            titre='2 Semaines',
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 1, 14),
        )
        self.assertEqual(planning.nombre_semaines, 2)

    def test_reference_auto_increment(self):
        p1 = Planning.objects.create(
            titre='P1', date_debut=date(2026, 1, 1), date_fin=date(2026, 1, 7)
        )
        p2 = Planning.objects.create(
            titre='P2', date_debut=date(2026, 2, 1), date_fin=date(2026, 2, 7)
        )
        num1 = int(p1.REFERENCE.split('-')[-1])
        num2 = int(p2.REFERENCE.split('-')[-1])
        self.assertEqual(num2, num1 + 1)


class AffectationModelTest(EmployeeTestCase):
    """Tests pour le modele Affectation."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.site = SiteTravail.objects.create(nom='Siege')
        cls.poste_travail = PosteTravail.objects.create(
            nom='Accueil', site=cls.site
        )
        cls.planning = Planning.objects.create(
            titre='Planning Test',
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 1, 31),
        )

    def test_creation_affectation(self):
        employe = self.create_employee(matricule='AFF001')
        affectation = Affectation.objects.create(
            planning=self.planning,
            employe=employe,
            poste=self.poste_travail,
            date=date(2026, 1, 5),
            heure_debut=time(9, 0),
            heure_fin=time(17, 0),
        )
        self.assertEqual(affectation.statut, 'PLANIFIE')
        self.assertIn('Accueil', str(affectation))

    def test_duree_heures(self):
        employe = self.create_employee(matricule='AFF002')
        affectation = Affectation.objects.create(
            planning=self.planning,
            employe=employe,
            poste=self.poste_travail,
            date=date(2026, 1, 6),
            heure_debut=time(9, 0),
            heure_fin=time(17, 0),
        )
        self.assertAlmostEqual(affectation.duree_heures, 8.0, places=1)

    def test_unique_together(self):
        employe = self.create_employee(matricule='AFF003')
        Affectation.objects.create(
            planning=self.planning,
            employe=employe,
            poste=self.poste_travail,
            date=date(2026, 1, 10),
            heure_debut=time(9, 0),
            heure_fin=time(17, 0),
        )
        with self.assertRaises(Exception):
            Affectation.objects.create(
                planning=self.planning,
                employe=employe,
                poste=self.poste_travail,
                date=date(2026, 1, 10),
                heure_debut=time(9, 0),
                heure_fin=time(12, 0),
            )


class EvenementModelTest(TestCase):
    """Tests pour le modele Evenement."""

    def test_creation_evenement(self):
        evt = Evenement.objects.create(
            titre='Reunion equipe',
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(hours=2),
            type_evenement='REUNION',
        )
        self.assertIn('Reunion equipe', str(evt))
        self.assertIn('Reunion', str(evt))

    def test_type_evenement_default(self):
        evt = Evenement.objects.create(
            titre='Test',
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(evt.type_evenement, 'REUNION')


# ============================================================
# TESTS FORMULAIRES
# ============================================================

class SiteTravailFormTest(TestCase):
    """Tests pour SiteTravailForm."""

    def test_form_valide(self):
        form = SiteTravailForm(data={
            'nom': 'Siege Lome',
            'adresse': '123 rue Test',
            'telephone': '+228 90 00 00 00',
            'heure_ouverture': '08:00',
            'heure_fermeture': '18:00',
            'fuseau_horaire': 'Africa/Lome',
            'is_active': True,
        })
        self.assertTrue(form.is_valid())

    def test_form_nom_requis(self):
        form = SiteTravailForm(data={
            'nom': '',
            'heure_ouverture': '08:00',
            'heure_fermeture': '18:00',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('nom', form.errors)


class PosteTravailFormTest(TestCase):
    """Tests pour PosteTravailForm."""

    @classmethod
    def setUpTestData(cls):
        cls.site = SiteTravail.objects.create(nom='Siege', is_active=True)

    def test_form_valide(self):
        form = PosteTravailForm(data={
            'nom': 'Accueil',
            'type_poste': 'JOURNEE',
            'site': self.site.pk,
            'heure_debut': '09:00',
            'heure_fin': '17:00',
            'pause_dejeune': '00:30:00',
            'taux_horaire': '12.50',
            'is_active': True,
        })
        self.assertTrue(form.is_valid())

    def test_heure_fin_avant_debut(self):
        form = PosteTravailForm(data={
            'nom': 'Poste invalide',
            'type_poste': 'JOURNEE',
            'site': self.site.pk,
            'heure_debut': '17:00',
            'heure_fin': '09:00',
            'pause_dejeune': '00:30:00',
            'taux_horaire': '12.50',
            'is_active': True,
        })
        self.assertFalse(form.is_valid())

    def test_site_inactif_non_propose(self):
        site_inactif = SiteTravail.objects.create(nom='Ferme', is_active=False)
        form = PosteTravailForm()
        site_ids = list(form.fields['site'].queryset.values_list('pk', flat=True))
        self.assertNotIn(site_inactif.pk, site_ids)
        self.assertIn(self.site.pk, site_ids)


class PlanningFormTest(EmployeeTestCase):
    """Tests pour PlanningForm."""

    def test_form_valide_admin(self):
        form = PlanningForm(data={
            'titre': 'Planning Janvier',
            'date_debut': '2026-01-01',
            'date_fin': '2026-01-31',
            'statut': 'BROUILLON',
        }, user_role='admin')
        self.assertTrue(form.is_valid())

    def test_date_fin_avant_debut(self):
        form = PlanningForm(data={
            'titre': 'Planning invalide',
            'date_debut': '2026-02-01',
            'date_fin': '2026-01-01',
            'statut': 'BROUILLON',
        }, user_role='admin')
        self.assertFalse(form.is_valid())

    def test_manager_sans_champ_departement(self):
        form = PlanningForm(user_role='manager')
        self.assertNotIn('departement', form.fields)

    def test_admin_avec_champ_departement(self):
        form = PlanningForm(user_role='admin')
        self.assertIn('departement', form.fields)


class AffectationFormTest(EmployeeTestCase):
    """Tests pour AffectationForm."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.site = SiteTravail.objects.create(nom='Siege', is_active=True)
        cls.poste_travail = PosteTravail.objects.create(
            nom='Accueil', site=cls.site, is_active=True
        )
        cls.planning = Planning.objects.create(
            titre='Planning Test',
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 1, 31),
            statut='BROUILLON',
        )

    def test_form_valide(self):
        employe = self.create_employee(matricule='AFFT01')
        form = AffectationForm(data={
            'planning': self.planning.pk,
            'employe': employe.pk,
            'poste': self.poste_travail.pk,
            'date': '2026-01-05',
            'heure_debut': '09:00',
            'heure_fin': '17:00',
            'statut': 'PLANIFIE',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_heure_fin_avant_debut(self):
        employe = self.create_employee(matricule='AFFT02')
        form = AffectationForm(data={
            'planning': self.planning.pk,
            'employe': employe.pk,
            'poste': self.poste_travail.pk,
            'date': '2026-01-05',
            'heure_debut': '17:00',
            'heure_fin': '09:00',
            'statut': 'PLANIFIE',
        })
        self.assertFalse(form.is_valid())


class EvenementFormTest(TestCase):
    """Tests pour EvenementForm."""

    def test_form_valide(self):
        form = EvenementForm(data={
            'titre': 'Reunion equipe',
            'date_debut': '2026-01-15 10:00',
            'date_fin': '2026-01-15 12:00',
            'type_evenement': 'REUNION',
            'lieu': 'Salle A',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_fin_avant_debut(self):
        form = EvenementForm(data={
            'titre': 'Evenement invalide',
            'date_debut': '2026-01-15 14:00',
            'date_fin': '2026-01-15 10:00',
            'type_evenement': 'REUNION',
        })
        self.assertFalse(form.is_valid())


# ============================================================
# TESTS PERMISSIONS
# ============================================================

class PermissionsTest(EmployeeTestCase):
    """Tests pour le systeme de permissions du planning."""

    def test_superuser_est_admin(self):
        superuser = User.objects.create_superuser(
            username='admin', password='admin123', email='admin@test.com'
        )
        self.assertEqual(get_planning_role(superuser), 'admin')
        self.assertTrue(can_edit_planning(superuser))

    def test_drh_est_admin(self):
        employe = self.create_employee(matricule='DRH001')
        user = self.create_user_for_employee(employe)
        self.assign_role(employe, self.role_drh)
        self.assertEqual(get_planning_role(user), 'admin')
        self.assertTrue(can_edit_planning(user))

    def test_manager_peut_editer(self):
        employe = self.create_employee(matricule='MGR001')
        user = self.create_user_for_employee(employe)
        self.assign_as_manager(employe)
        role = get_planning_role(user)
        self.assertEqual(role, 'manager')
        self.assertTrue(can_edit_planning(user))

    def test_employe_simple_ne_peut_pas_editer(self):
        employe = self.create_employee(matricule='EMP001')
        user = self.create_user_for_employee(employe)
        role = get_planning_role(user)
        self.assertEqual(role, 'employee')
        self.assertFalse(can_edit_planning(user))

    def test_utilisateur_non_authentifie(self):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        self.assertIsNone(get_planning_role(anon))
        self.assertFalse(can_edit_planning(anon))


# ============================================================
# TESTS VUES
# ============================================================

class SiteViewsTest(EmployeeTestCase):
    """Tests pour les vues CRUD des sites de travail."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Admin user
        cls.admin_employe = cls().create_employee(matricule='VADM01', nom='Admin')
        cls.admin_user = User.objects.create_user(
            username='VADM01', password='testpass123', email='admin@test.com'
        )
        cls.admin_employe.user = cls.admin_user
        cls.admin_employe.save()
        # DRH role
        from employee.models import ZYRE
        ZYRE.objects.create(
            employe=cls.admin_employe,
            role=cls.role_drh,
            date_debut=date.today(),
            actif=True
        )
        # Simple employee
        cls.simple_employe = cls().create_employee(matricule='VEMP01', nom='Simple')
        cls.simple_user = User.objects.create_user(
            username='VEMP01', password='testpass123', email='simple@test.com'
        )
        cls.simple_employe.user = cls.simple_user
        cls.simple_employe.save()

    def test_liste_sites_admin(self):
        self.client.login(username='VADM01', password='testpass123')
        response = self.client.get('/planning/sites/')
        self.assertEqual(response.status_code, 200)

    def test_liste_sites_employe_interdit(self):
        self.client.login(username='VEMP01', password='testpass123')
        response = self.client.get('/planning/sites/')
        self.assertEqual(response.status_code, 403)

    def test_creer_site_get(self):
        self.client.login(username='VADM01', password='testpass123')
        response = self.client.get('/planning/sites/creer/')
        self.assertEqual(response.status_code, 200)

    def test_creer_site_post(self):
        self.client.login(username='VADM01', password='testpass123')
        response = self.client.post('/planning/sites/creer/', {
            'nom': 'Nouveau Site',
            'heure_ouverture': '08:00',
            'heure_fermeture': '18:00',
            'fuseau_horaire': 'Africa/Lome',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SiteTravail.objects.filter(nom='Nouveau Site').exists())

    def test_modifier_site(self):
        self.client.login(username='VADM01', password='testpass123')
        site = SiteTravail.objects.create(nom='A Modifier')
        response = self.client.post(f'/planning/sites/{site.pk}/modifier/', {
            'nom': 'Site Modifie',
            'heure_ouverture': '08:00',
            'heure_fermeture': '18:00',
            'fuseau_horaire': 'Africa/Lome',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        site.refresh_from_db()
        self.assertEqual(site.nom, 'Site Modifie')

    def test_supprimer_site_sans_postes(self):
        self.client.login(username='VADM01', password='testpass123')
        site = SiteTravail.objects.create(nom='A Supprimer')
        response = self.client.post(f'/planning/sites/{site.pk}/supprimer/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SiteTravail.objects.filter(pk=site.pk).exists())

    def test_supprimer_site_avec_postes_refuse(self):
        self.client.login(username='VADM01', password='testpass123')
        site = SiteTravail.objects.create(nom='Site Occupe')
        PosteTravail.objects.create(nom='Poste', site=site)
        response = self.client.post(f'/planning/sites/{site.pk}/supprimer/')
        self.assertEqual(response.status_code, 302)
        # Le site existe toujours
        self.assertTrue(SiteTravail.objects.filter(pk=site.pk).exists())

    def test_non_authentifie_redirige(self):
        response = self.client.get('/planning/sites/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class PosteViewsTest(EmployeeTestCase):
    """Tests pour les vues CRUD des postes de travail."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.site = SiteTravail.objects.create(nom='Siege', is_active=True)
        cls.admin_employe = cls().create_employee(matricule='PADM01', nom='Admin')
        cls.admin_user = User.objects.create_user(
            username='PADM01', password='testpass123', email='padm@test.com'
        )
        cls.admin_employe.user = cls.admin_user
        cls.admin_employe.save()
        from employee.models import ZYRE
        ZYRE.objects.create(
            employe=cls.admin_employe, role=cls.role_drh,
            date_debut=date.today(), actif=True
        )

    def test_liste_postes(self):
        self.client.login(username='PADM01', password='testpass123')
        response = self.client.get('/planning/postes/')
        self.assertEqual(response.status_code, 200)

    def test_creer_poste(self):
        self.client.login(username='PADM01', password='testpass123')
        response = self.client.post('/planning/postes/creer/', {
            'nom': 'Nouveau Poste',
            'type_poste': 'JOURNEE',
            'site': self.site.pk,
            'heure_debut': '09:00',
            'heure_fin': '17:00',
            'pause_dejeune': '00:30:00',
            'taux_horaire': '12.50',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PosteTravail.objects.filter(nom='Nouveau Poste').exists())

    def test_supprimer_poste_avec_affectation_refuse(self):
        self.client.login(username='PADM01', password='testpass123')
        poste = PosteTravail.objects.create(nom='Poste Occupe', site=self.site)
        planning = Planning.objects.create(
            titre='Test', date_debut=date(2026, 1, 1), date_fin=date(2026, 1, 31)
        )
        employe = self.create_employee(matricule='PAFF01')
        Affectation.objects.create(
            planning=planning, employe=employe, poste=poste,
            date=date(2026, 1, 5), heure_debut=time(9, 0), heure_fin=time(17, 0)
        )
        response = self.client.post(f'/planning/postes/{poste.pk}/supprimer/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PosteTravail.objects.filter(pk=poste.pk).exists())

    def test_filtrer_par_site(self):
        self.client.login(username='PADM01', password='testpass123')
        PosteTravail.objects.create(nom='P1', site=self.site)
        site2 = SiteTravail.objects.create(nom='Autre Site')
        PosteTravail.objects.create(nom='P2', site=site2)
        response = self.client.get(f'/planning/postes/?site={self.site.pk}')
        self.assertEqual(response.status_code, 200)


class PlanningViewsTest(EmployeeTestCase):
    """Tests pour les vues CRUD des plannings."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_employe = cls().create_employee(matricule='PLADM1', nom='Admin')
        cls.admin_user = User.objects.create_user(
            username='PLADM1', password='testpass123', email='pladm@test.com'
        )
        cls.admin_employe.user = cls.admin_user
        cls.admin_employe.save()
        from employee.models import ZYRE
        ZYRE.objects.create(
            employe=cls.admin_employe, role=cls.role_drh,
            date_debut=date.today(), actif=True
        )

        cls.simple_employe = cls().create_employee(matricule='PLEMP1', nom='Simple')
        cls.simple_user = User.objects.create_user(
            username='PLEMP1', password='testpass123', email='plemp@test.com'
        )
        cls.simple_employe.user = cls.simple_user
        cls.simple_employe.save()

    def test_liste_plannings_admin(self):
        self.client.login(username='PLADM1', password='testpass123')
        response = self.client.get('/planning/plannings/')
        self.assertEqual(response.status_code, 200)

    def test_liste_plannings_employe_interdit(self):
        self.client.login(username='PLEMP1', password='testpass123')
        response = self.client.get('/planning/plannings/')
        self.assertEqual(response.status_code, 403)

    def test_creer_planning(self):
        self.client.login(username='PLADM1', password='testpass123')
        response = self.client.post('/planning/plannings/creer/', {
            'titre': 'Planning Fevrier',
            'date_debut': '2026-02-01',
            'date_fin': '2026-02-28',
            'statut': 'BROUILLON',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Planning.objects.filter(titre='Planning Fevrier').exists())

    def test_modifier_planning(self):
        self.client.login(username='PLADM1', password='testpass123')
        planning = Planning.objects.create(
            titre='Original', date_debut=date(2026, 3, 1),
            date_fin=date(2026, 3, 31), created_by=self.admin_user,
        )
        response = self.client.post(f'/planning/plannings/{planning.pk}/modifier/', {
            'titre': 'Modifie',
            'date_debut': '2026-03-01',
            'date_fin': '2026-03-31',
            'statut': 'PUBLIE',
        })
        self.assertEqual(response.status_code, 302)
        planning.refresh_from_db()
        self.assertEqual(planning.titre, 'Modifie')
        self.assertEqual(planning.statut, 'PUBLIE')

    def test_supprimer_planning_sans_affectation(self):
        self.client.login(username='PLADM1', password='testpass123')
        planning = Planning.objects.create(
            titre='A supprimer', date_debut=date(2026, 4, 1), date_fin=date(2026, 4, 30)
        )
        response = self.client.post(f'/planning/plannings/{planning.pk}/supprimer/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Planning.objects.filter(pk=planning.pk).exists())

    def test_supprimer_planning_avec_affectation_refuse(self):
        self.client.login(username='PLADM1', password='testpass123')
        planning = Planning.objects.create(
            titre='Planning Occupe', date_debut=date(2026, 5, 1), date_fin=date(2026, 5, 31)
        )
        site = SiteTravail.objects.create(nom='Site PL')
        poste = PosteTravail.objects.create(nom='Poste PL', site=site)
        employe = self.create_employee(matricule='PLAFF1')
        Affectation.objects.create(
            planning=planning, employe=employe, poste=poste,
            date=date(2026, 5, 5), heure_debut=time(9, 0), heure_fin=time(17, 0)
        )
        response = self.client.post(f'/planning/plannings/{planning.pk}/supprimer/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Planning.objects.filter(pk=planning.pk).exists())


class CalendarViewsTest(EmployeeTestCase):
    """Tests pour les vues calendrier."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_employe = cls().create_employee(matricule='CADM01', nom='Admin')
        cls.admin_user = User.objects.create_user(
            username='CADM01', password='testpass123', email='cadm@test.com'
        )
        cls.admin_employe.user = cls.admin_user
        cls.admin_employe.save()
        from employee.models import ZYRE
        ZYRE.objects.create(
            employe=cls.admin_employe, role=cls.role_drh,
            date_debut=date.today(), actif=True
        )

        cls.simple_employe = cls().create_employee(matricule='CEMP01', nom='Simple')
        cls.simple_user = User.objects.create_user(
            username='CEMP01', password='testpass123', email='cemp@test.com'
        )
        cls.simple_employe.user = cls.simple_user
        cls.simple_employe.save()

    def test_planning_calendar_admin(self):
        self.client.login(username='CADM01', password='testpass123')
        response = self.client.get('/planning/')
        self.assertEqual(response.status_code, 200)

    def test_planning_calendar_employe(self):
        self.client.login(username='CEMP01', password='testpass123')
        response = self.client.get('/planning/')
        self.assertEqual(response.status_code, 200)

    def test_mon_planning(self):
        self.client.login(username='CEMP01', password='testpass123')
        response = self.client.get('/planning/mon-planning/')
        self.assertEqual(response.status_code, 200)

    def test_non_authentifie_redirige(self):
        response = self.client.get('/planning/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
