# HR_ONIAN/settings_test.py
"""
Settings pour les tests - utilise SQLite en mémoire pour éviter
les problèmes de permissions PostgreSQL.

Usage:
    python manage.py test --settings=HR_ONIAN.settings_test employee.tests
"""
from .settings import *

# Utiliser SQLite en mémoire pour les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Désactiver le cache pour les tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Accélérer les tests en utilisant MD5 pour les mots de passe
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Désactiver les logs pendant les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {},
    'loggers': {},
}

# Mode test
DEBUG = False
