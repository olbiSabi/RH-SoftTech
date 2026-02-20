"""
Configuration Gunicorn pour HR_ONIAN en production.

Lancer avec :
    gunicorn HR_ONIAN.wsgi:application -c gunicorn.conf.py
"""
import multiprocessing
import os

# ============================================
# SERVEUR
# ============================================

# Adresse et port d'ecoute (Nginx fait le proxy vers ce socket)
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8000')

# Nombre de workers : (2 x CPU) + 1
workers = os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1)

# Type de worker
worker_class = 'sync'

# Timeout pour les requetes longues (ex: generation PDF)
timeout = 120

# Taille max du body des requetes (10 Mo)
limit_request_body = 10485760


# ============================================
# LOGGING
# ============================================

# Logs d'acces et d'erreur
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', 'logs/gunicorn-access.log')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', 'logs/gunicorn-error.log')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Format des logs d'acces
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'


# ============================================
# PROCESSUS
# ============================================

# Fichier PID
pidfile = os.environ.get('GUNICORN_PID', '/tmp/hr_onian.pid')

# Relancer les workers apres N requetes (evite les fuites memoire)
max_requests = 1000
max_requests_jitter = 50

# Mode daemon (False si lance par systemd)
daemon = False

# Recharger automatiquement en dev (desactiver en production)
reload = False


# ============================================
# SECURITE
# ============================================

# Headers proxy (Nginx ajoute X-Forwarded-For)
forwarded_allow_ips = '127.0.0.1'

# Desactiver le keep-alive cote Gunicorn (Nginx gere le keep-alive client)
keepalive = 2


# ============================================
# HOOKS
# ============================================

def on_starting(server):
    """Appele au demarrage du serveur."""
    pass


def on_reload(server):
    """Appele lors d'un reload."""
    pass


def worker_abort(worker):
    """Appele quand un worker est tue (timeout)."""
    import traceback
    import threading
    id2name = {th.ident: th.name for th in threading.enumerate()}
    for thread_id, stack in sys._current_frames().items():
        print(f"\n# Thread: {id2name.get(thread_id, '')} ({thread_id})")
        traceback.print_stack(f=stack)
