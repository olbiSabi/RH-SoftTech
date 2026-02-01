# audit/management/commands/init_regles_conformite.py
"""
Commande Django pour initialiser les règles de conformité par défaut.

Usage:
    python manage.py init_regles_conformite
    python manage.py init_regles_conformite --force  # Réinitialiser toutes les règles
"""
from django.core.management.base import BaseCommand
from audit.models import AURC


class Command(BaseCommand):
    help = 'Initialise les règles de conformité par défaut pour le module audit'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Supprimer et recréer toutes les règles existantes'
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write(self.style.WARNING(f"\n{'='*70}"))
        self.stdout.write(self.style.WARNING("🔧 INITIALISATION DES RÈGLES DE CONFORMITÉ"))
        self.stdout.write(self.style.WARNING(f"{'='*70}\n"))

        if force:
            self.stdout.write(self.style.WARNING("⚠️  Mode FORCE activé - Suppression des règles existantes..."))
            count = AURC.objects.all().count()
            AURC.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"   ✅ {count} règle(s) supprimée(s)\n"))

        # Définir les règles par défaut
        regles_defaut = [
            {
                'CODE': 'CONT-001',
                'LIBELLE': 'Contrats expirant dans 60 jours',
                'DESCRIPTION': 'Alerte pour les contrats arrivant à échéance dans les 60 prochains jours',
                'TYPE_REGLE': 'CONTRAT',
                'SEVERITE': 'WARNING',
                'FREQUENCE_VERIFICATION': 'QUOTIDIEN',
                'JOURS_AVANT_EXPIRATION': 60,
                'NOTIFIER_EMPLOYE': True,
                'NOTIFIER_MANAGER': True,
                'NOTIFIER_RH': True,
                'STATUT': True,
            },
            {
                'CODE': 'CONT-002',
                'LIBELLE': 'Contrats expirant dans 30 jours',
                'DESCRIPTION': 'Alerte critique pour les contrats arrivant à échéance dans les 30 prochains jours',
                'TYPE_REGLE': 'CONTRAT',
                'SEVERITE': 'CRITICAL',
                'FREQUENCE_VERIFICATION': 'QUOTIDIEN',
                'JOURS_AVANT_EXPIRATION': 30,
                'NOTIFIER_EMPLOYE': True,
                'NOTIFIER_MANAGER': True,
                'NOTIFIER_RH': True,
                'STATUT': True,
            },
            {
                'CODE': 'CONT-003',
                'LIBELLE': 'Contrats expirant dans 15 jours',
                'DESCRIPTION': 'Alerte urgente pour les contrats arrivant à échéance dans les 15 prochains jours',
                'TYPE_REGLE': 'CONTRAT',
                'SEVERITE': 'CRITICAL',
                'FREQUENCE_VERIFICATION': 'QUOTIDIEN',
                'JOURS_AVANT_EXPIRATION': 15,
                'NOTIFIER_EMPLOYE': True,
                'NOTIFIER_MANAGER': True,
                'NOTIFIER_RH': True,
                'STATUT': True,
            },
            {
                'CODE': 'DOC-001',
                'LIBELLE': 'Documents obligatoires manquants',
                'DESCRIPTION': 'Vérification des documents obligatoires (CNI, CV, diplôme, RIB)',
                'TYPE_REGLE': 'DOCUMENT',
                'SEVERITE': 'WARNING',
                'FREQUENCE_VERIFICATION': 'HEBDOMADAIRE',
                'JOURS_AVANT_EXPIRATION': 0,
                'NOTIFIER_EMPLOYE': True,
                'NOTIFIER_MANAGER': False,
                'NOTIFIER_RH': True,
                'STATUT': True,
            },
            {
                'CODE': 'VMED-001',
                'LIBELLE': 'Visites médicales à renouveler',
                'DESCRIPTION': 'Alerte pour les visites médicales arrivant à échéance dans les 30 jours',
                'TYPE_REGLE': 'VISITE_MEDICALE',
                'SEVERITE': 'WARNING',
                'FREQUENCE_VERIFICATION': 'HEBDOMADAIRE',
                'JOURS_AVANT_EXPIRATION': 30,
                'NOTIFIER_EMPLOYE': True,
                'NOTIFIER_MANAGER': True,
                'NOTIFIER_RH': True,
                'STATUT': True,
            },
            {
                'CODE': 'MAT-001',
                'LIBELLE': 'Matériel en retard de restitution',
                'DESCRIPTION': 'Vérification des prêts de matériel non restitués à la date prévue',
                'TYPE_REGLE': 'MATERIEL',
                'SEVERITE': 'WARNING',
                'FREQUENCE_VERIFICATION': 'QUOTIDIEN',
                'JOURS_AVANT_EXPIRATION': 0,
                'NOTIFIER_EMPLOYE': True,
                'NOTIFIER_MANAGER': True,
                'NOTIFIER_RH': False,
                'STATUT': True,
            },
        ]

        # Créer les règles
        regles_creees = 0
        regles_existantes = 0

        for regle_data in regles_defaut:
            code = regle_data['CODE']

            # Vérifier si la règle existe déjà
            if AURC.objects.filter(CODE=code).exists():
                self.stdout.write(f"   ⏭️  {code} - {regle_data['LIBELLE']} (existe déjà)")
                regles_existantes += 1
            else:
                # Créer la règle
                regle = AURC.objects.create(**regle_data)
                self.stdout.write(self.style.SUCCESS(
                    f"   ✅ {code} - {regle_data['LIBELLE']} "
                    f"({regle_data['JOURS_AVANT_EXPIRATION']} jours)"
                ))
                regles_creees += 1

        # Résumé
        self.stdout.write(self.style.WARNING(f"\n{'='*70}"))
        self.stdout.write(self.style.WARNING("📊 RÉSUMÉ"))
        self.stdout.write(self.style.WARNING(f"{'='*70}"))
        self.stdout.write(f"   Règles créées: {regles_creees}")
        self.stdout.write(f"   Règles existantes: {regles_existantes}")
        self.stdout.write(f"   Total: {regles_creees + regles_existantes}")
        self.stdout.write(self.style.SUCCESS(f"\n✅ Initialisation terminée avec succès !"))
        self.stdout.write(self.style.WARNING(f"{'='*70}\n"))

        # Conseil
        if regles_creees > 0:
            self.stdout.write(self.style.HTTP_INFO(
                "💡 Conseil: Vous pouvez maintenant exécuter la vérification avec:\n"
                "   python manage.py verifier_conformite\n"
            ))
