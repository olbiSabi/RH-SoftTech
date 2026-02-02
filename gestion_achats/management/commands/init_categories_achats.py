"""
Management command pour initialiser les catégories d'achats par défaut.

Usage:
    python manage.py init_categories_achats
"""

from django.core.management.base import BaseCommand
from gestion_achats.models import GACCategorie


class Command(BaseCommand):
    help = 'Initialise les catégories d\'achats par défaut du module GAC'

    def handle(self, *args, **options):
        """Exécute la commande d'initialisation des catégories."""

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Initialisation des catégories d\'achats'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        # Définition de l'arborescence des catégories
        categories = [
            {
                'nom': 'Fournitures de bureau',
                'code': 'FRN_BUREAU',
                'description': 'Fournitures et consommables de bureau',
                'sous_categories': [
                    {'nom': 'Papeterie', 'code': 'FRN_PAPETERIE'},
                    {'nom': 'Classement et archivage', 'code': 'FRN_CLASSEMENT'},
                    {'nom': 'Outils d\'écriture', 'code': 'FRN_ECRITURE'},
                ]
            },
            {
                'nom': 'Équipements informatiques',
                'code': 'EQP_INFO',
                'description': 'Matériel informatique et accessoires',
                'sous_categories': [
                    {'nom': 'Ordinateurs', 'code': 'EQP_ORDINATEURS'},
                    {'nom': 'Périphériques', 'code': 'EQP_PERIPHERIQUES'},
                    {'nom': 'Câbles et connectique', 'code': 'EQP_CABLES'},
                    {'nom': 'Stockage', 'code': 'EQP_STOCKAGE'},
                ]
            },
            {
                'nom': 'Logiciels et licences',
                'code': 'LOG_LICENCES',
                'description': 'Logiciels, licences et abonnements',
                'sous_categories': [
                    {'nom': 'Licences bureautique', 'code': 'LOG_BUREAUTIQUE'},
                    {'nom': 'Licences développement', 'code': 'LOG_DEV'},
                    {'nom': 'Abonnements SaaS', 'code': 'LOG_SAAS'},
                ]
            },
            {
                'nom': 'Mobilier et aménagement',
                'code': 'MOB_AMENAG',
                'description': 'Mobilier de bureau et aménagement des locaux',
                'sous_categories': [
                    {'nom': 'Bureaux et tables', 'code': 'MOB_BUREAUX'},
                    {'nom': 'Sièges', 'code': 'MOB_SIEGES'},
                    {'nom': 'Rangements', 'code': 'MOB_RANGEMENTS'},
                    {'nom': 'Éclairage', 'code': 'MOB_ECLAIRAGE'},
                ]
            },
            {
                'nom': 'Services et prestations',
                'code': 'SRV_PRESTA',
                'description': 'Services externes et prestations intellectuelles',
                'sous_categories': [
                    {'nom': 'Maintenance', 'code': 'SRV_MAINTENANCE'},
                    {'nom': 'Formation', 'code': 'SRV_FORMATION'},
                    {'nom': 'Consulting', 'code': 'SRV_CONSULTING'},
                ]
            },
            {
                'nom': 'Consommables',
                'code': 'CONSOMMABLES',
                'description': 'Consommables divers',
                'sous_categories': [
                    {'nom': 'Cartouches d\'encre', 'code': 'CONS_ENCRE'},
                    {'nom': 'Fournitures d\'entretien', 'code': 'CONS_ENTRETIEN'},
                    {'nom': 'Cafétéria', 'code': 'CONS_CAFETERIA'},
                ]
            },
            {
                'nom': 'Téléphonie et communication',
                'code': 'TEL_COMM',
                'description': 'Équipements et services de téléphonie',
                'sous_categories': [
                    {'nom': 'Téléphones', 'code': 'TEL_APPAREILS'},
                    {'nom': 'Abonnements téléphoniques', 'code': 'TEL_ABONNEMENTS'},
                ]
            },
            {
                'nom': 'Marketing et communication',
                'code': 'MKT_COMM',
                'description': 'Supports marketing et communication',
                'sous_categories': [
                    {'nom': 'Supports publicitaires', 'code': 'MKT_PUBLICITE'},
                    {'nom': 'Goodies et cadeaux', 'code': 'MKT_GOODIES'},
                    {'nom': 'Impression', 'code': 'MKT_IMPRESSION'},
                ]
            },
        ]

        created_count = 0
        updated_count = 0

        for cat_data in categories:
            # Créer ou mettre à jour la catégorie parente
            categorie_parent, created = GACCategorie.objects.update_or_create(
                code=cat_data['code'],
                defaults={
                    'nom': cat_data['nom'],
                    'description': cat_data.get('description', ''),
                    'parent': None,
                    'ordre': 0
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Catégorie créée: {categorie_parent.code:20s} - {categorie_parent.nom}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Catégorie mise à jour: {categorie_parent.code:20s} - {categorie_parent.nom}"
                    )
                )

            # Créer les sous-catégories
            for i, sous_cat_data in enumerate(cat_data.get('sous_categories', [])):
                sous_categorie, created = GACCategorie.objects.update_or_create(
                    code=sous_cat_data['code'],
                    defaults={
                        'nom': sous_cat_data['nom'],
                        'parent': categorie_parent,
                        'ordre': i + 1
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"   ├── Sous-catégorie créée: {sous_categorie.code:20s} - {sous_categorie.nom}"
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"   ├── Sous-catégorie mise à jour: {sous_categorie.code:20s} - {sous_categorie.nom}"
                        )
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Résumé:'))
        self.stdout.write(self.style.SUCCESS(f"  - Catégories créées: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Catégories mises à jour: {updated_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Total: {created_count + updated_count}"))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('✅ Initialisation terminée avec succès!'))
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'Note: Vous pouvez maintenant créer des articles et les associer '
                'à ces catégories.'
            )
        )
