# Tests pour l'application Project Management

Ce dossier contient les tests pour l'application Django `project_management` qui implémente une solution de gestion de projet de type JIRA.

## Structure des tests

### Tests principaux

- **`test_minimal.py`** - Tests de base qui vérifient le fonctionnement minimal de l'application
  - Création des modèles (Client, Projet, Ticket)
  - Résolution des URLs
  - Authentification
  - Représentations string

- **`test_models.py`** - Tests des modèles de données
  - Validation des champs
  - Relations entre modèles
  - Propriétés et méthodes

- **`test_views.py`** - Tests des vues Django
  - Accès authentifié/non authentifié
  - Réponses HTTP
  - Templates

- **`test_forms.py`** - Tests des formulaires
  - Validation des données
  - Formulaires valides/invalides

- **`test_services.py`** - Tests des services métier
  - Logique métier
  - Calculs et traitements

- **`test_api.py`** - Tests des endpoints API
  - Réponses JSON
  - Codes de statut HTTP

- **`test_integration.py`** - Tests d'intégration
  - Flux complets
  - Workflows de bout en bout

- **`test_performance.py`** - Tests de performance
  - Nombre de requêtes
  - Temps de réponse
  - Utilisation mémoire

## Comment lancer les tests

### Lancer tous les tests
```bash
python manage.py test project_management --verbosity=2
```

### Lancer un fichier de test spécifique
```bash
python manage.py test project_management.tests.test_minimal --verbosity=2
```

### Lancer une méthode de test spécifique
```bash
python manage.py test project_management.tests.test_minimal.MinimalProjectManagementTest.test_client_creation --verbosity=2
```

### Lancer les tests avec couverture de code
```bash
coverage run --source='.' manage.py test project_management
coverage report
coverage html
```

## Tests recommandés pour commencer

1. **Tests minimaux** - Pour vérifier rapidement que tout fonctionne :
   ```bash
   python manage.py test project_management.tests.test_minimal
   ```

2. **Tests des modèles** - Pour valider la structure des données :
   ```bash
   python manage.py test project_management.tests.test_models
   ```

3. **Tests d'intégration** - Pour vérifier les flux complets :
   ```bash
   python manage.py test project_management.tests.test_integration
   ```

## Problèmes connus

Certains tests peuvent échouer en raison de :
- Modèles qui n'existent pas encore (propriétés manquantes)
- Templates qui ne sont pas encore créés
- Relations complexes entre modèles

Les tests dans `test_minimal.py` sont conçus pour fonctionner avec l'état actuel de l'application.

## Amélioration des tests

Pour améliorer la couverture de tests :

1. **Ajouter des tests pour les vues manquantes**
2. **Tester les cas limites et les erreurs**
3. **Ajouter des tests de charge**
4. **Tester la sécurité (permissions, validation)**
5. **Ajouter des tests pour les formulaires complexes**

## Bonnes pratiques

- Utiliser des noms de tests descriptifs
- Tester les cas positifs et négatifs
- Utiliser `setUp()` pour préparer les données
- Nettoyer les données après chaque test
- Utiliser des assertions spécifiques
- Documenter les tests complexes
