"""
Django settings for HR_ONIAN project.

Utilise python-dotenv pour charger les variables d'environnement
depuis un fichier .env a la racine du projet.

En developpement : copier .env.dev en .env.local
En production    : copier .env.production en .env.local et adapter les valeurs
"""
import os
import sentry_sdk
from pathlib import Path
from django.urls import reverse_lazy
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables d'environnement
# En dev : copier .env.dev en .env.local
# En prod : copier .env.production en .env.local
load_dotenv(BASE_DIR / '.env.local')

# Configuration WeasyPrint pour macOS
if os.path.exists('/opt/homebrew/lib'):
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib'
elif os.path.exists('/usr/local/lib'):
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/usr/local/lib'


# ============================================
# SECURITE
# ============================================

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("La variable SECRET_KEY doit etre definie dans le fichier .env")

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()
]


# ============================================
# APPLICATIONS
# ============================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'employee',
    'departement',
    'core',
    'absence',
    'entreprise',
    'frais',
    'materiel',
    'audit',
    'project_management',
    'gestion_achats',
    'planning',
    'donneeParDefaut',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.CurrentRequestMiddleware',
    'core.middleware.PermissionDeniedMiddleware',
    'employee.middleware.LoginRequiredMiddleware',
    'employee.middleware.ContratExpirationMiddleware',
]

# URLs exemptees de l'authentification
LOGIN_EXEMPT_URLS = [
    r'^/api/public/',
]

ROOT_URLCONF = 'HR_ONIAN.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'absence.context_processors.notifications_absences',
                'core.context_processors.notifications_unifiees',
                'core.context_processors.entreprise_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'HR_ONIAN.wsgi.application'


# ============================================
# BASE DE DONNEES
# ============================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'hrapp'),
        'USER': os.environ.get('DB_USER', 'hr'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


# ============================================
# VALIDATION DES MOTS DE PASSE
# ============================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================
# INTERNATIONALISATION
# ============================================

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Douala'

USE_I18N = True

USE_TZ = True


# ============================================
# FICHIERS STATIQUES & MEDIA
# ============================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

APPEND_SLASH = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================
# UPLOAD
# ============================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 Mo
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 Mo


# ============================================
# GESTION DES ERREURS
# ============================================

handler404 = 'employee.error_handlers.handler404'
handler500 = 'employee.error_handlers.handler500'
handler403 = 'employee.error_handlers.handler403'
handler400 = 'employee.error_handlers.handler400'


# ============================================
# AUTHENTIFICATION & SESSIONS
# ============================================

LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_SAVE_EVERY_REQUEST = True

LOGIN_ATTEMPTS_LIMIT = 3
ACCOUNT_LOCKOUT_DURATION = 24  # heures


# ============================================
# REDIS — Cache & Sessions
# ============================================
# En développement : Redis optionnel (fallback sur cache mémoire locale)
# En production   : Redis obligatoire (REDIS_URL dans .env.local)
#
# Installation rapide :
#   apt install redis-server && systemctl start redis   (Linux)
#   brew install redis && brew services start redis      (macOS)
#   Docker : service redis dans docker-compose.yml

REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
_REDIS_AVAILABLE = bool(os.environ.get('REDIS_URL'))

if _REDIS_AVAILABLE or not DEBUG:
    # Cache Redis (production ou dev avec Redis explicitement configuré)
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'CONNECTION_POOL_KWARGS': {'max_connections': 50},
                # Si Redis est indisponible : ne pas crasher, recalculer à la volée
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'hr_onian',
            'TIMEOUT': 300,  # TTL par défaut : 5 minutes
        }
    }
    # Sessions stockées dans Redis (plus rapide que la base de données)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    # Développement sans Redis : cache local en mémoire (par processus)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'hr-onian-dev',
        }
    }
    # Sessions en base de données (comportement Django par défaut)
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# TTL par type de donnée (en secondes) — utilisé dans les vues
CACHE_TTL_DASHBOARD = 300       # 5 min  — dashboards (données fraîches)
CACHE_TTL_STATS = 3600          # 1 h    — statistiques annuelles
CACHE_TTL_PLANNING = 300        # 5 min  — calendrier planning
CACHE_TTL_DETAIL = 1800         # 30 min — pages de détail (matériel, employé)


# ============================================
# EMAIL
# ============================================

SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000')

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'ONIAN-EasyM <noreply@hronian.local>'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ONIAN-EasyM <noreply@onian-easym.com>')
    EMAIL_TIMEOUT = 10


# ============================================
# SECURITE PRODUCTION
# ============================================

if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Cookies securises
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True

    # Protection XSS et content type
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


# ============================================
# LOGGING
# ============================================

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# ============================================
# SENTRY — Monitoring des erreurs en production
# ============================================
# Créer un projet sur https://sentry.io et copier le DSN dans .env.local
# SENTRY_DSN=https://e9c41085399bc117f6717f7533d059d4@o4510926313160704.ingest.de.sentry.io/4510926448951376
#
# Sentry ne s'active QUE si SENTRY_DSN est défini — sans impact en dev.

_SENTRY_DSN = os.environ.get('https://e9c41085399bc117f6717f7533d059d4@o4510926313160704.ingest.de.sentry.io/4510926448951376', '').strip()

if _SENTRY_DSN:
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        # Intégration Django automatique (requêtes, SQL, signaux…)
        integrations=[],
        # Performance : échantillonnage 10 % des transactions
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        # Profiling : 10 % des transactions tracées
        profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        # Ne pas envoyer les données personnelles (IP, cookies…)
        send_default_pii=False,
        # Environnement pour filtrer dans le tableau de bord Sentry
        environment='production' if not DEBUG else 'development',
        # Aide à identifier quelle version est déployée
        release=os.environ.get('APP_VERSION', 'hr-onian@1.0.0'),
        # Ignorer les erreurs non-critiques redondantes
        ignore_errors=[
            KeyboardInterrupt,
        ],
    )


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'hr_onian.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5 Mo
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'errors.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'gestion_achats': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'absence': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'employee': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}
