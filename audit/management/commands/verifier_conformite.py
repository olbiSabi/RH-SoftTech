# audit/management/commands/verifier_conformite.py
"""
Commande Django pour vérifier la conformité et générer les alertes.

Usage:
    python manage.py verifier_conformite
    python manage.py verifier_conformite --type contrat
    python manage.py verifier_conformite --type document
    python manage.py verifier_conformite --tous
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from audit.services import ConformiteService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vérifie la conformité et génère des alertes pour les contrats expirants, documents manquants, etc.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['contrat', 'document', 'visite', 'materiel'],
            help='Type de vérification à effectuer'
        )
        parser.add_argument(
            '--tous',
            action='store_true',
            help='Exécuter toutes les vérifications'
        )
        parser.add_argument(
            '--verbeux',
            action='store_true',
            help='Afficher plus de détails'
        )

    def handle(self, *args, **options):
        debut = timezone.now()
        self.stdout.write(self.style.WARNING(f"\n{'='*70}"))
        self.stdout.write(self.style.WARNING(f"🔍 VÉRIFICATION DE CONFORMITÉ - {debut.strftime('%d/%m/%Y %H:%M:%S')}"))
        self.stdout.write(self.style.WARNING(f"{'='*70}\n"))

        type_verification = options.get('type')
        tous = options.get('tous')
        verbeux = options.get('verbeux')

        total_alertes = 0
        resultats = {}

        # Si aucune option, exécuter toutes les vérifications
        if not type_verification and not tous:
            tous = True

        # Vérification des contrats
        if tous or type_verification == 'contrat':
            self.stdout.write(self.style.HTTP_INFO("\n📋 Vérification des contrats expirants..."))
            try:
                alertes = ConformiteService.verifier_contrats_expirants()
                resultats['contrats'] = len(alertes)
                total_alertes += len(alertes)

                if alertes:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {len(alertes)} alerte(s) créée(s)"))

                    if verbeux:
                        for alerte in alertes:
                            self.stdout.write(f"      → {alerte.TITRE} (Priorité: {alerte.PRIORITE})")
                else:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Aucune alerte à créer"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erreur: {str(e)}"))
                logger.exception("Erreur lors de la vérification des contrats")

        # Vérification des documents
        if tous or type_verification == 'document':
            self.stdout.write(self.style.HTTP_INFO("\n📄 Vérification des documents manquants..."))
            try:
                alertes = ConformiteService.verifier_documents_manquants()
                resultats['documents'] = len(alertes)
                total_alertes += len(alertes)

                if alertes:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {len(alertes)} alerte(s) créée(s)"))

                    if verbeux:
                        for alerte in alertes:
                            self.stdout.write(f"      → {alerte.TITRE}")
                else:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Aucune alerte à créer"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erreur: {str(e)}"))
                logger.exception("Erreur lors de la vérification des documents")

        # Vérification des visites médicales
        if tous or type_verification == 'visite':
            self.stdout.write(self.style.HTTP_INFO("\n🏥 Vérification des visites médicales..."))
            try:
                alertes = ConformiteService.verifier_visites_medicales()
                resultats['visites_medicales'] = len(alertes)
                total_alertes += len(alertes)

                if alertes:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {len(alertes)} alerte(s) créée(s)"))

                    if verbeux:
                        for alerte in alertes:
                            self.stdout.write(f"      → {alerte.TITRE} (Priorité: {alerte.PRIORITE})")
                else:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Aucune alerte à créer"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erreur: {str(e)}"))
                logger.exception("Erreur lors de la vérification des visites médicales")

        # Vérification du matériel
        if tous or type_verification == 'materiel':
            self.stdout.write(self.style.HTTP_INFO("\n💻 Vérification du matériel en retard..."))
            try:
                alertes = ConformiteService.verifier_materiel_en_retard()
                resultats['materiel'] = len(alertes)
                total_alertes += len(alertes)

                if alertes:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {len(alertes)} alerte(s) créée(s)"))

                    if verbeux:
                        for alerte in alertes:
                            self.stdout.write(f"      → {alerte.TITRE} (Priorité: {alerte.PRIORITE})")
                else:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Aucune alerte à créer"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erreur: {str(e)}"))
                logger.exception("Erreur lors de la vérification du matériel")

        # Résumé
        fin = timezone.now()
        duree = (fin - debut).total_seconds()

        self.stdout.write(self.style.WARNING(f"\n{'='*70}"))
        self.stdout.write(self.style.WARNING("📊 RÉSUMÉ"))
        self.stdout.write(self.style.WARNING(f"{'='*70}"))

        for type_verif, nombre in resultats.items():
            self.stdout.write(f"   {type_verif.capitalize()}: {nombre} alerte(s)")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Total: {total_alertes} alerte(s) créée(s)"))
        self.stdout.write(f"⏱️  Durée: {duree:.2f} secondes")
        self.stdout.write(self.style.WARNING(f"{'='*70}\n"))

        logger.info(f"Vérification de conformité terminée: {total_alertes} alertes créées en {duree:.2f}s")
