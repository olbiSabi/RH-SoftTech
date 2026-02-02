#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Python d'automatisation du calcul des acquisitions de congés.

Alternative au script shell pour les environnements qui préfèrent Python.
Peut être utilisé avec cron, systemd, ou Task Scheduler.

Usage:
    python scripts/calculer_acquisitions.py
    python scripts/calculer_acquisitions.py --annee 2026
    python scripts/calculer_acquisitions.py --email admin@example.com
    python scripts/calculer_acquisitions.py --dry-run
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

# Configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
VENV_DIR = PROJECT_DIR.parent / '.env'
LOG_DIR = PROJECT_DIR / 'logs' / 'acquisitions'

# Créer le dossier de logs s'il n'existe pas
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuration du logging
log_file = LOG_DIR / f"acquisitions_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def send_email_notification(subject, body, recipient):
    """Envoie une notification par email (si configuré)."""
    try:
        subprocess.run(
            ['mail', '-s', subject, recipient],
            input=body.encode(),
            check=True
        )
        logger.info(f"Email envoyé à {recipient}")
    except FileNotFoundError:
        logger.warning("Commande 'mail' non disponible. Email non envoyé.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {e}")


def run_calcul(annee=None, dry_run=False, verbose=False):
    """Exécute la commande de calcul Django."""
    logger.info("="*70)
    logger.info("DÉBUT DU CALCUL DES ACQUISITIONS DE CONGÉS")
    logger.info("="*70)

    # Construire la commande Django
    python_exec = VENV_DIR / 'bin' / 'python'
    if not python_exec.exists():
        # Windows
        python_exec = VENV_DIR / 'Scripts' / 'python.exe'

    if not python_exec.exists():
        logger.error(f"Python non trouvé dans l'environnement virtuel: {VENV_DIR}")
        return False

    manage_py = PROJECT_DIR / 'manage.py'
    if not manage_py.exists():
        logger.error(f"manage.py non trouvé: {manage_py}")
        return False

    # Construire la commande
    cmd = [str(python_exec), str(manage_py), 'calculer_acquisitions', '--tous']

    if annee:
        cmd.extend(['--annee', str(annee)])

    if verbose:
        cmd.append('--verbeux')

    if dry_run:
        cmd.append('--dry-run')

    logger.info(f"Répertoire de travail: {PROJECT_DIR}")
    logger.info(f"Commande: {' '.join(cmd)}")

    # Exécuter la commande
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=False
        )

        # Afficher la sortie
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(line)

        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(line)

        success = result.returncode == 0

        if success:
            logger.info("✅ Calcul terminé avec succès")
        else:
            logger.error(f"❌ Erreur lors du calcul (code: {result.returncode})")

        logger.info("="*70)
        logger.info("FIN DU CALCUL DES ACQUISITIONS DE CONGÉS")
        logger.info("="*70)

        return success

    except Exception as e:
        logger.exception(f"Erreur lors de l'exécution de la commande: {e}")
        return False


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description='Automatisation du calcul des acquisitions de congés HR_ONIAN'
    )
    parser.add_argument(
        '--annee',
        type=int,
        help='Année de référence (par défaut: année en cours)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Afficher plus de détails'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulation sans sauvegarder les changements'
    )
    parser.add_argument(
        '--email',
        help='Adresse email pour recevoir les notifications'
    )

    args = parser.parse_args()

    # Exécuter le calcul
    success = run_calcul(
        annee=args.annee,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    # Envoyer une notification par email si demandé
    if args.email:
        subject = "✅ HR_ONIAN - Calcul des acquisitions réussi" if success else "❌ HR_ONIAN - Erreur de calcul"

        # Lire le contenu du log
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                body = f.read()
        except Exception as e:
            body = f"Impossible de lire le fichier de log: {e}"

        send_email_notification(subject, body, args.email)

    # Code de sortie
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
