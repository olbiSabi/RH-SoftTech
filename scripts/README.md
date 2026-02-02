# Scripts d'automatisation - HR_ONIAN

Ce dossier contient les scripts d'automatisation pour le système HR_ONIAN :
- **Vérifications de conformité** (contrats, documents, visites médicales, matériel)
- **Calcul des acquisitions de congés** (mensuel)

## 📁 Fichiers disponibles

### Scripts de conformité

1. **`verifier_conformite.sh`** - Script Bash pour la conformité
   - Pour Linux/macOS
   - Vérifications quotidiennes automatiques
   - Gestion automatique des logs

2. **`verifier_conformite.py`** - Script Python pour la conformité
   - Multi-plateforme (Linux/macOS/Windows)
   - Alternative au script Bash
   - Support des notifications par email

### Scripts d'acquisitions

3. **`calculer_acquisitions.sh`** - Script Bash pour les acquisitions
   - Calcul mensuel des congés acquis
   - Pour Linux/macOS
   - Gestion automatique des logs

4. **`calculer_acquisitions.py`** - Script Python pour les acquisitions
   - Multi-plateforme (Linux/macOS/Windows)
   - Support mode simulation (--dry-run)
   - Notifications par email

### Documentation

5. **`CRON_SETUP.md`** - Guide d'ordonnancement pour la conformité
   - Configuration Cron (Linux/macOS)
   - Configuration systemd (Linux)
   - Configuration Task Scheduler (Windows)
   - Exemples et recommandations

6. **`ACQUISITIONS_SETUP.md`** - Guide d'ordonnancement pour les acquisitions
   - Configuration mensuelle recommandée
   - Bonnes pratiques
   - Monitoring et vérification

7. **`celery_config_example.py`** - Configuration Celery Beat (optionnel)
   - Alternative avancée à cron
   - Configuration pour Redis/Celery
   - Tâches planifiées pour conformité ET acquisitions

## 🚀 Démarrage rapide

### 1. Rendre les scripts exécutables

```bash
chmod +x scripts/verifier_conformite.sh
chmod +x scripts/verifier_conformite.py
chmod +x scripts/calculer_acquisitions.sh
chmod +x scripts/calculer_acquisitions.py
```

### 2. Tester manuellement

**Conformité (Bash) :**
```bash
./scripts/verifier_conformite.sh
```

**Conformité (Python) :**
```bash
python scripts/verifier_conformite.py
```

**Acquisitions (Bash) :**
```bash
./scripts/calculer_acquisitions.sh
```

**Acquisitions (Python) :**
```bash
python scripts/calculer_acquisitions.py
# Mode simulation (sans sauvegarder)
python scripts/calculer_acquisitions.py --dry-run
```

### 3. Configurer l'ordonnancement

**Configuration complète recommandée pour la production :**

```bash
# Éditer la crontab
crontab -e

# Ajouter ces lignes (remplacer /chemin/vers par le chemin réel)

# Vérification de conformité - Quotidien à 6h00
0 6 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh

# Calcul des acquisitions - Mensuel le 1er à 1h00
0 1 1 * * /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh
```

## 📊 Vérification des logs

### Logs de conformité

Emplacement : `logs/conformite/`

```bash
# Voir le log du jour
tail -f logs/conformite/conformite_$(date +%Y%m%d).log

# Chercher les erreurs
grep "ERREUR\|❌" logs/conformite/*.log

# Voir le résumé
grep "Total:" logs/conformite/*.log
```

### Logs des acquisitions

Emplacement : `logs/acquisitions/`

```bash
# Voir le log du jour
tail -f logs/acquisitions/acquisitions_$(date +%Y%m%d).log

# Chercher les erreurs
grep "ERREUR\|❌" logs/acquisitions/*.log

# Voir le résumé
grep "Traitements réussis" logs/acquisitions/*.log
```

## 🔧 Options disponibles

### Script Bash

```bash
# Exécution standard
./scripts/verifier_conformite.sh

# Le script accepte les mêmes options que la commande Django
# (modifiez le script pour passer des arguments)
```

### Script Python

```bash
# Toutes les vérifications
python scripts/verifier_conformite.py

# Type spécifique
python scripts/verifier_conformite.py --type contrat

# Mode verbeux
python scripts/verifier_conformite.py --verbose

# Avec notification email
python scripts/verifier_conformite.py --email admin@example.com
```

## 📅 Recommandations de planification

### Production

```cron
# Vérification complète quotidienne à 6h00
0 6 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

### Développement/Test

```cron
# Vérification toutes les heures (pour tests)
0 * * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

### Configuration avancée

Voir le fichier `CRON_SETUP.md` pour :
- Différentes fréquences d'exécution
- Configuration systemd (Linux)
- Configuration Task Scheduler (Windows)
- Gestion des logs
- Notifications par email
- Dépannage

## ⚠️ Important pour le déploiement

1. **Chemins absolus** : Utilisez toujours des chemins absolus dans les configurations cron

2. **Permissions** : Assurez-vous que les scripts ont les bonnes permissions

3. **Environnement virtuel** : Vérifiez que le chemin vers l'environnement virtuel est correct

4. **Logs** : Créez le dossier `logs/conformite/` s'il n'existe pas

5. **Test** : Testez toujours manuellement avant de planifier

## 🐛 Dépannage

### Le script ne s'exécute pas

```bash
# Vérifier les permissions
ls -l scripts/verifier_conformite.sh

# Tester manuellement
./scripts/verifier_conformite.sh

# Vérifier les logs
cat logs/conformite/conformite_$(date +%Y%m%d).log
```

### Cron ne fonctionne pas

```bash
# Vérifier les tâches cron
crontab -l

# Vérifier les logs système
tail -f /var/log/syslog | grep CRON  # Linux
tail -f /var/log/system.log | grep cron  # macOS
```

## 📞 Support

Pour plus d'informations, consultez :
- `CRON_SETUP.md` - Guide complet d'ordonnancement
- Documentation Django du projet
- Logs dans `logs/conformite/`

## 🔄 Exécution manuelle avec Django

Si vous préférez utiliser directement les commandes Django :

### Conformité

```bash
# Activer l'environnement virtuel
source ../.env/bin/activate

# Vérification complète
python manage.py verifier_conformite --tous --verbeux

# Vérification spécifique
python manage.py verifier_conformite --type contrat
```

### Acquisitions

```bash
# Calcul pour tous les employés
python manage.py calculer_acquisitions --tous --verbeux

# Calcul pour une année spécifique
python manage.py calculer_acquisitions --annee 2025 --tous

# Mode simulation (sans sauvegarder)
python manage.py calculer_acquisitions --dry-run --verbeux

# Calcul pour un employé spécifique
python manage.py calculer_acquisitions --employe MT000001

# Vérifier les acquisitions
python manage.py verifier_acquisitions --annee 2026
```
