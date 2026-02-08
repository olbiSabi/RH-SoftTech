# Configuration du système de logging

## Modifications effectuées dans absence/views.py

✅ Tous les `print()` ont été remplacés par des appels `logger`
✅ Tous les `traceback.print_exc()` ont été remplacés par `logger.exception()`
✅ Import de `logging` ajouté
✅ Logger configuré: `logger = logging.getLogger(__name__)`

## Configuration recommandée pour settings.py

Ajoutez cette configuration dans votre fichier `HR_ONIAN/settings.py`:

```python
# Configuration du logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            'class': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            'class': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'absence': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

## Étapes d'installation

1. **Créer le répertoire logs**
   ```bash
   mkdir -p /Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/logs
   ```

2. **Ajouter logs/ au .gitignore**
   ```bash
   echo "logs/" >> .gitignore
   ```

3. **Ajouter la configuration LOGGING dans settings.py**
   Copiez la configuration ci-dessus dans votre fichier `settings.py`

## Niveaux de log utilisés

- **`logger.debug()`**: Informations détaillées pour le débogage (données POST, paramètres API, etc.)
- **`logger.info()`**: Informations générales (succès d'opérations, étapes de traitement)
- **`logger.warning()`**: Avertissements (situations anormales mais gérables)
- **`logger.error()`**: Erreurs (erreurs de validation, erreurs métier)
- **`logger.exception()`**: Exceptions avec stack trace complète (erreurs critiques)

## Exemples d'utilisation dans le code

```python
# Debug - informations détaillées
logger.debug("📥 POST data: %s", request.POST)

# Info - opérations réussies
logger.info("✅ Formulaire valide - Année: %s", annee)

# Warning - avertissements
logger.warning("⚠️  AVERTISSEMENT: Date limite proche")

# Error - erreurs de validation
logger.error("❌ Formulaire invalide: %s", form.errors)

# Exception - erreurs avec stack trace
logger.exception("❌ ERREUR lors de la suppression:")
```

## Fichiers de log générés

- **`logs/app.log`**: Tous les logs (INFO et supérieur)
- **`logs/errors.log`**: Uniquement les erreurs (ERROR et EXCEPTION)
- **Console**: Affichage en temps réel pendant le développement

## Configuration pour production

Pour la production, modifiez les niveaux:

```python
'absence': {
    'handlers': ['file', 'error_file'],  # Pas de console en production
    'level': 'INFO',  # Pas de DEBUG en production
    'propagate': False,
},
```

## Rotation des logs (optionnel)

Pour éviter que les fichiers de log deviennent trop gros:

```python
'file': {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'app.log',
    'maxBytes': 1024 * 1024 * 10,  # 10 MB
    'backupCount': 5,
    'formatter': 'verbose',
},
```

## Avantages de ce système

✅ Traçabilité complète des opérations
✅ Fichiers de log séparés par niveau (erreurs à part)
✅ Format standardisé avec timestamps
✅ Facile à filtrer et analyser
✅ Conservation de l'historique
✅ Meilleur débogage en production
