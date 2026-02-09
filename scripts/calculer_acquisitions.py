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
    logger.info("DEBUT DU CALCUL DES ACQUISITIONS DE CONGES")
    logger.info("="*70)

    # Construire la commande Django
    python_exec = VENV_DIR / 'bin' / 'python'
    if not python_exec.exists():
        # Windows
        python_exec = VENV_DIR / 'Scripts' / 'python.exe'

    if not python_exec.exists():
        logger.error("Python non trouve dans l'environnement virtuel: %s", VENV_DIR)
        return False

    manage_py = PROJECT_DIR / 'manage.py'
    if not manage_py.exists():
        logger.error("manage.py non trouve: %s", manage_py)
        return False

    # Construire la commande - toujours --verbeux pour capturer les rejets
    cmd = [str(python_exec), str(manage_py), 'calculer_acquisitions', '--tous', '--verbeux']

    if annee:
        cmd.extend(['--annee', str(annee)])

    if dry_run:
        cmd.append('--dry-run')

    logger.info("Repertoire de travail: %s", PROJECT_DIR)
    logger.info("Commande: %s", ' '.join(cmd))

    # Exécuter la commande
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=False
        )

        # Classer et afficher la sortie selon le type de message
        if result.stdout:
            for line in result.stdout.split('\n'):
                stripped = line.strip()
                if not stripped:
                    continue
                if 'REJET' in stripped or 'DETAIL DES REJETS' in stripped:
                    logger.warning(stripped)
                elif 'ERREUR' in stripped or 'DETAIL DES ERREURS' in stripped:
                    logger.error(stripped)
                elif 'IGNORE' in stripped:
                    logger.debug(stripped) if not verbose else logger.info(stripped)
                else:
                    logger.info(stripped)

        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(line.strip())

        success = result.returncode == 0

        if success:
            logger.info("Calcul termine avec succes")
        else:
            logger.error("Erreur lors du calcul (code: %s)", result.returncode)

        logger.info("="*70)
        logger.info("FIN DU CALCUL DES ACQUISITIONS DE CONGES")
        logger.info("="*70)

        return success

    except Exception as e:
        logger.exception("Erreur lors de l'execution de la commande: %s", e)
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
