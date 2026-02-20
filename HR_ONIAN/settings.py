"""
Django settings for HR_ONIAN project.

Utilise python-dotenv pour charger les variables d'environnement
depuis un fichier .env a la racine du projet.

En developpement : copier .env.dev en .env.local
En production    : copier .env.production en .env.local et adapter les valeurs
"""
import os
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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
    SESSION_COOKIE_HTTPONLY = True

    # Protection XSS et content type
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


# ============================================
# LOGGING
# ============================================

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

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
