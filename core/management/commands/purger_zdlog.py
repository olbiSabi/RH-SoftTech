# core/management/commands/purger_zdlog.py
"""
Commande Django pour purger la table ZDLOG avec sauvegarde préalable.

Usage:
    python manage.py purger_zdlog --profondeur 2
    python manage.py purger_zdlog --profondeur 1 --dry-run
    python manage.py purger_zdlog --profondeur 3 --format csv
"""
import json
import csv
import logging
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import ZDLOG

logger = logging.getLogger(__name__)

BACKUP_DIR = Path(settings.BASE_DIR) / 'backups' / 'zdlog'


class Command(BaseCommand):
    help = 'Purge les logs ZDLOG antérieurs à N années avec sauvegarde préalable'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profondeur',
            type=int,
            required=True,
            help="Nombre d'années de rétention (ex: 2 = supprime tout avant 2 ans)"
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='Format du fichier de sauvegarde (défaut: json)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans suppression ni sauvegarde'
        )

    def handle(self, *args, **options):
        profondeur = options['profondeur']
        fmt = options['format']
        dry_run = options['dry_run']

        if profondeur < 1:
            self.stderr.write(self.style.ERROR(
                "La profondeur doit être >= 1 an"
            ))
            return

        maintenant = timezone.now()
        date_limite = maintenant - timedelta(days=profondeur * 365)

        self._log_header(maintenant, profondeur, date_limite, dry_run)

        # Compter les enregistrements
        total_logs = ZDLOG.objects.count()
        logs_a_purger = ZDLOG.objects.filter(DATE_MODIFICATION__lt=date_limite)
        nb_a_purger = logs_a_purger.count()
        nb_conserves = total_logs - nb_a_purger

        self.stdout.write(f"  Total logs en base     : {total_logs}")
        self.stdout.write(f"  Logs a purger (< {date_limite.strftime('%d/%m/%Y')}) : {nb_a_purger}")
        self.stdout.write(f"  Logs conserves         : {nb_conserves}")
        self.stdout.write("")

        if nb_a_purger == 0:
            self.stdout.write(self.style.SUCCESS(
                "  Aucun log a purger. La base est deja propre."
            ))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "  MODE SIMULATION - Aucune action effectuee"
            ))
            self._afficher_apercu(logs_a_purger)
            return

        # Etape 1 : Sauvegarde COMPLETE avant purge
        self.stdout.write(self.style.HTTP_INFO("  [1/3] Sauvegarde complete de ZDLOG..."))
        fichier_backup = self._sauvegarder(fmt, maintenant)
        self.stdout.write(self.style.SUCCESS(
            f"  Sauvegarde: {fichier_backup} ({total_logs} enregistrements)"
        ))

        # Etape 2 : Purge
        self.stdout.write(self.style.HTTP_INFO(f"  [2/3] Purge des {nb_a_purger} logs..."))
        with transaction.atomic():
            nb_supprimes, _ = logs_a_purger.delete()

        self.stdout.write(self.style.SUCCESS(
            f"  {nb_supprimes} logs supprimes"
        ))

        # Etape 3 : Verification
        self.stdout.write(self.style.HTTP_INFO("  [3/3] Verification..."))
        restants = ZDLOG.objects.count()
        self.stdout.write(f"  Logs restants en base : {restants}")

        self._log_resume(
            total_logs, nb_supprimes, restants,
            fichier_backup, profondeur, date_limite
        )

        logger.info(
            "Purge ZDLOG: %s supprimes, %s conserves, profondeur=%s ans, backup=%s",
            nb_supprimes, restants, profondeur, fichier_backup
        )

    def _sauvegarder(self, fmt, maintenant):
        """Sauvegarde TOUS les logs ZDLOG avant la purge."""
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = maintenant.strftime('%Y%m%d_%H%M%S')
        fichier = BACKUP_DIR / f"zdlog_backup_{timestamp}.{fmt}"

        tous_les_logs = ZDLOG.objects.all().order_by('DATE_MODIFICATION')

        if fmt == 'json':
            self._sauvegarder_json(tous_les_logs, fichier)
        else:
            self._sauvegarder_csv(tous_les_logs, fichier)

        return fichier

    def _sauvegarder_json(self, queryset, fichier):
        """Sauvegarde en JSON."""
        data = []
        for log in queryset.iterator(chunk_size=1000):
            data.append({
                'id': log.id,
                'TABLE_NAME': log.TABLE_NAME,
                'RECORD_ID': log.RECORD_ID,
                'TYPE_MOUVEMENT': log.TYPE_MOUVEMENT,
                'DATE_MODIFICATION': log.DATE_MODIFICATION.isoformat(),
                'USER_ID': log.USER_id,
                'USER_NAME': log.USER_NAME,
                'ANCIENNE_VALEUR': log.ANCIENNE_VALEUR,
                'NOUVELLE_VALEUR': log.NOUVELLE_VALEUR,
                'DESCRIPTION': log.DESCRIPTION,
                'IP_ADDRESS': log.IP_ADDRESS,
            })

        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _sauvegarder_csv(self, queryset, fichier):
        """Sauvegarde en CSV."""
        champs = [
            'id', 'TABLE_NAME', 'RECORD_ID', 'TYPE_MOUVEMENT',
            'DATE_MODIFICATION', 'USER_ID', 'USER_NAME',
            'ANCIENNE_VALEUR', 'NOUVELLE_VALEUR', 'DESCRIPTION', 'IP_ADDRESS'
        ]

        with open(fichier, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=champs)
            writer.writeheader()

            for log in queryset.iterator(chunk_size=1000):
                writer.writerow({
                    'id': log.id,
                    'TABLE_NAME': log.TABLE_NAME,
                    'RECORD_ID': log.RECORD_ID,
                    'TYPE_MOUVEMENT': log.TYPE_MOUVEMENT,
                    'DATE_MODIFICATION': log.DATE_MODIFICATION.isoformat(),
                    'USER_ID': log.USER_id,
                    'USER_NAME': log.USER_NAME,
                    'ANCIENNE_VALEUR': json.dumps(log.ANCIENNE_VALEUR, ensure_ascii=False) if log.ANCIENNE_VALEUR else '',
                    'NOUVELLE_VALEUR': json.dumps(log.NOUVELLE_VALEUR, ensure_ascii=False) if log.NOUVELLE_VALEUR else '',
                    'DESCRIPTION': log.DESCRIPTION,
                    'IP_ADDRESS': log.IP_ADDRESS,
                })

    def _afficher_apercu(self, queryset):
        """Affiche un aperçu des logs qui seraient purgés."""
        self.stdout.write("")
        self.stdout.write("  APERCU (5 premiers logs a purger) :")
        for log in queryset[:5]:
            self.stdout.write(
                f"    - [{log.DATE_MODIFICATION.strftime('%d/%m/%Y %H:%M')}] "
                f"{log.TABLE_NAME} | {log.get_TYPE_MOUVEMENT_display()} | "
                f"{log.USER_NAME or 'Systeme'}"
            )

        # Répartition par table
        self.stdout.write("")
        self.stdout.write("  REPARTITION PAR TABLE :")
        from django.db.models import Count
        repartition = (
            queryset
            .values('TABLE_NAME')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        for item in repartition[:10]:
            self.stdout.write(
                f"    - {item['TABLE_NAME']}: {item['total']} logs"
            )

    def _log_header(self, maintenant, profondeur, date_limite, dry_run):
        """Affiche l'en-tête."""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(
            f"  PURGE ZDLOG - {maintenant.strftime('%d/%m/%Y %H:%M:%S')}"
        )
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"  Profondeur : {profondeur} an(s)")
        self.stdout.write(f"  Date limite: {date_limite.strftime('%d/%m/%Y %H:%M:%S')}")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "  MODE SIMULATION"
            ))
        self.stdout.write("")

    def _log_resume(self, total_avant, supprimes, restants, fichier, profondeur, date_limite):
        """Affiche le résumé final."""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("  RESUME PURGE")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"  Profondeur        : {profondeur} an(s)")
        self.stdout.write(f"  Date limite       : {date_limite.strftime('%d/%m/%Y')}")
        self.stdout.write(f"  Logs avant purge  : {total_avant}")
        self.stdout.write(self.style.ERROR(f"  Logs supprimes    : {supprimes}"))
        self.stdout.write(self.style.SUCCESS(f"  Logs conserves    : {restants}"))
        self.stdout.write(f"  Fichier backup    : {fichier}")
        self.stdout.write(f"{'='*60}\n")
