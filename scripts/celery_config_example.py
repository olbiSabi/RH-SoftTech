"""
Configuration Celery Beat pour l'ordonnancement des tâches de conformité.

Ce fichier est un EXEMPLE de configuration pour utiliser Celery Beat
au lieu de Cron pour l'ordonnancement des vérifications de conformité.

Installation requise:
    pip install celery redis django-celery-beat

Configuration:
    1. Copier ce fichier vers HR_ONIAN/celery.py
    2. Ajouter CELERY_BEAT_SCHEDULE dans settings.py
    3. Lancer Redis: redis-server
    4. Lancer Celery worker: celery -A HR_ONIAN worker -l info
    5. Lancer Celery beat: celery -A HR_ONIAN beat -l info

Pour la production, utilisez supervisord ou systemd pour gérer les processus Celery.
"""

from celery import Celery
from celery.schedules import crontab
import os

# Configuration de l'application Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HR_ONIAN.settings')

app = Celery('HR_ONIAN')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# ============================================================================
# TÂCHE DE VÉRIFICATION DE CONFORMITÉ
# ============================================================================

@app.task(name='verifier_conformite_complete')
def verifier_conformite_complete():
    """
    Exécute toutes les vérifications de conformité.
    """
    from django.core.management import call_command
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Début de la vérification de conformité complète")
        call_command('verifier_conformite', '--tous', '--verbeux')
        logger.info("Vérification de conformité terminée avec succès")
        return {'status': 'success', 'message': 'Vérification complète effectuée'}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de conformité: {e}")
        return {'status': 'error', 'message': str(e)}


@app.task(name='verifier_contrats')
def verifier_contrats():
    """
    Vérifie uniquement les contrats expirants.
    """
    from django.core.management import call_command
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Début de la vérification des contrats")
        call_command('verifier_conformite', '--type', 'contrat', '--verbeux')
        logger.info("Vérification des contrats terminée")
        return {'status': 'success', 'message': 'Contrats vérifiés'}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des contrats: {e}")
        return {'status': 'error', 'message': str(e)}


@app.task(name='verifier_documents')
def verifier_documents():
    """
    Vérifie les documents manquants.
    """
    from django.core.management import call_command
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Début de la vérification des documents")
        call_command('verifier_conformite', '--type', 'document', '--verbeux')
        logger.info("Vérification des documents terminée")
        return {'status': 'success', 'message': 'Documents vérifiés'}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des documents: {e}")
        return {'status': 'error', 'message': str(e)}


@app.task(name='verifier_visites_medicales')
def verifier_visites_medicales():
    """
    Vérifie les visites médicales.
    """
    from django.core.management import call_command
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Début de la vérification des visites médicales")
        call_command('verifier_conformite', '--type', 'visite', '--verbeux')
        logger.info("Vérification des visites médicales terminée")
        return {'status': 'success', 'message': 'Visites médicales vérifiées'}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des visites médicales: {e}")
        return {'status': 'error', 'message': str(e)}


@app.task(name='verifier_materiel')
def verifier_materiel():
    """
    Vérifie le matériel en retard.
    """
    from django.core.management import call_command
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Début de la vérification du matériel")
        call_command('verifier_conformite', '--type', 'materiel', '--verbeux')
        logger.info("Vérification du matériel terminée")
        return {'status': 'success', 'message': 'Matériel vérifié'}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du matériel: {e}")
        return {'status': 'error', 'message': str(e)}


# ============================================================================
# CONFIGURATION DES PLANIFICATIONS
# À ajouter dans settings.py sous CELERY_BEAT_SCHEDULE
# ============================================================================

CELERY_BEAT_SCHEDULE_EXAMPLE = {
    # Vérification complète quotidienne à 6h00
    'verifier-conformite-quotidien': {
        'task': 'verifier_conformite_complete',
        'schedule': crontab(hour=6, minute=0),
        'options': {
            'expires': 3600,  # Expire après 1 heure
        }
    },

    # Vérification des contrats tous les jours à 6h00
    'verifier-contrats-quotidien': {
        'task': 'verifier_contrats',
        'schedule': crontab(hour=6, minute=0),
        'options': {
            'expires': 3600,
        }
    },

    # Vérification des documents tous les lundis à 7h00
    'verifier-documents-hebdomadaire': {
        'task': 'verifier_documents',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),  # 1 = Lundi
        'options': {
            'expires': 3600,
        }
    },

    # Vérification des visites médicales le 1er de chaque mois à 8h00
    'verifier-visites-mensuel': {
        'task': 'verifier_visites_medicales',
        'schedule': crontab(hour=8, minute=0, day_of_month=1),
        'options': {
            'expires': 3600,
        }
    },

    # Vérification du matériel tous les lundis à 7h00
    'verifier-materiel-hebdomadaire': {
        'task': 'verifier_materiel',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),
        'options': {
            'expires': 3600,
        }
    },
}


# ============================================================================
# CONFIGURATION À AJOUTER DANS settings.py
# ============================================================================

"""
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Paris'  # ou votre timezone
CELERY_ENABLE_UTC = True

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'verifier-conformite-quotidien': {
        'task': 'verifier_conformite_complete',
        'schedule': crontab(hour=6, minute=0),
    },
}

# Optionnel: Utiliser django-celery-beat pour stocker les planifications en DB
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
"""


# ============================================================================
# COMMANDES POUR DÉMARRER CELERY
# ============================================================================

"""
# Démarrer Redis (requis)
redis-server

# Démarrer Celery worker (dans un terminal)
celery -A HR_ONIAN worker -l info

# Démarrer Celery beat (dans un autre terminal)
celery -A HR_ONIAN beat -l info

# Ou tout démarrer ensemble (développement uniquement)
celery -A HR_ONIAN worker -B -l info

# Production: Utiliser supervisord ou systemd
# Voir la documentation Celery pour les configurations de production
"""


# ============================================================================
# EXEMPLE DE CONFIGURATION SUPERVISORD (PRODUCTION)
# ============================================================================

"""
; /etc/supervisor/conf.d/hronian-celery.conf

[program:hronian-celery-worker]
command=/chemin/vers/.env/bin/celery -A HR_ONIAN worker -l info
directory=/chemin/vers/HR_ONIAN
user=votre_utilisateur
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998

[program:hronian-celery-beat]
command=/chemin/vers/.env/bin/celery -A HR_ONIAN beat -l info
directory=/chemin/vers/HR_ONIAN
user=votre_utilisateur
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=999

[group:hronian-celery]
programs=hronian-celery-worker,hronian-celery-beat
priority=999
"""
