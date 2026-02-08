# Scripts PostgreSQL - HR_ONIAN

Ce dossier contient les scripts de gestion des backups PostgreSQL pour le projet HR_ONIAN.

## Scripts disponibles

### 1. `backup_postgresql.sh`
Script de backup quotidien de la base de données.

**Fonctionnalités:**
- Création de backup complet avec pg_dump
- Compression automatique (gzip)
- Nettoyage des anciens backups (conservation des 7 derniers)
- Vérification de l'intégrité
- Logging détaillé
- Vérification de l'espace disque

**Configuration:**
```bash
DB_NAME="hrapp"           # Nom de la base de données
DB_USER="hr"               # Utilisateur PostgreSQL
DB_HOST="localhost"          # Hôte PostgreSQL
DB_PORT="5432"               # Port PostgreSQL
BACKUP_DIR="/path/to/backups" # Répertoire de stockage
MAX_BACKUPS=7                # Nombre de backups à conserver
```

**Utilisation:**
```bash
# Exécution manuelle
./backup_postgresql.sh

# Ajout au crontab pour exécution quotidienne à 2h du matin
0 2 * * * /path/to/scripts/backup_postgresql.sh
```

### 2. `restore_postgresql.sh`
Script de restauration de la base de données.

**Fonctionnalités:**
- Liste des backups disponibles
- Restauration depuis un backup spécifique
- Backup de sécurité avant restauration
- Confirmation utilisateur
- Vérification post-restauration

**Utilisation:**
```bash
# Lister les backups disponibles
./restore_postgresql.sh

# Restaurer un backup spécifique
./restore_postgresql.sh hrapp_backup_20240208_120000.sql.gz

# Restaurer depuis un chemin complet
./restore_postgresql.sh /path/to/backups/backup.sql.gz
```

### 3. `cleanup_backups.sh`
Script de nettoyage des anciens backups.

**Fonctionnalités:**
- Suppression des backups les plus anciens (limite par nombre)
- Suppression basée sur la taille totale
- Vérification et suppression des fichiers corrompus
- Rapport détaillé du nettoyage

**Configuration:**
```bash
MAX_BACKUPS=7        # Nombre maximum de backups à conserver
MAX_SIZE_GB=10        # Taille maximale du dossier de backups (GB)
```

**Utilisation:**
```bash
# Nettoyage manuel
./cleanup_backups.sh

# Ajout au crontab pour exécution hebdomadaire
0 3 * * 0 /path/to/scripts/cleanup_backups.sh
```

## Installation et configuration

### 1. Rendre les scripts exécutables
```bash
chmod +x scripts/*.sh
```

### 2. Configurer les variables
Modifier les variables de configuration dans chaque script:
- `DB_NAME`: Nom de votre base de données
- `DB_USER`: Utilisateur PostgreSQL
- `DB_HOST`: Hôte (localhost si local)
- `DB_PORT`: Port PostgreSQL
- `BACKUP_DIR`: Répertoire de stockage des backups

### 3. Créer les répertoires nécessaires
```bash
mkdir -p backups
mkdir -p logs
```

### 4. Configurer PostgreSQL
Assurez-vous que:
- PostgreSQL est installé et en cours d'exécution
- L'utilisateur `postgres` a les droits nécessaires
- La base de données `hr_onian` existe

### 5. Tester les scripts
```bash
# Tester le backup
./scripts/backup_postgresql.sh

# Vérifier le backup créé
ls -la backups/

# Tester la restauration (optionnel)
./scripts/restore_postgresql.sh
```

## Automatisation avec Cron

### Configuration quotidienne
```bash
# Ouvrir l'éditeur crontab
crontab -e

# Ajouter les lignes suivantes:
# Backup quotidien à 2h du matin
0 2 * * * /Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/scripts/backup_postgresql.sh

# Nettoyage hebdomadaire le dimanche à 3h du matin
0 3 * * 0 /Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/scripts/cleanup_backups.sh
```

### Vérification des tâches cron
```bash
# Lister les tâches cron actuelles
crontab -l

# Vérifier les logs cron
tail -f /var/log/cron.log  # macOS
```

## Logs

Les scripts génèrent des logs dans le fichier `logs/backup.log` avec:
- Horodatage de chaque opération
- Messages d'erreur et de succès
- Taille des backups créés
- Espace disque disponible

**Exemple de log:**
```
[2024-02-08 14:30:15] Début du backup de la base de données hrapp
[2024-02-08 14:30:16] Création du backup: /path/to/backups/hrapp_backup_20240208_143016.sql
[2024-02-08 14:30:45] Backup créé avec succès: /path/to/backups/hrapp_backup_20240208_143016.sql.gz (Taille: 45.2M)
[2024-02-08 14:30:45] Nettoyage des anciens backups (conservation des 7 plus récents)
[2024-02-08 14:30:45] Nombre de backups conservés: 7
[2024-02-08 14:30:45] Backup terminé avec succès
[2024-02-08 14:30:45] Espace disque disponible dans /path/to/backups: 125G
```

## Bonnes pratiques

1. **Test régulier**: Testez régulièrement la restauration pour vérifier l'intégrité des backups
2. **Stockage externe**: Copiez les backups sur un stockage externe pour une protection supplémentaire
3. **Monitoring**: Surveillez les logs pour détecter les erreurs rapidement
4. **Espace disque**: Vérifiez régulièrement l'espace disque disponible
5. **Sécurité**: Protégez les backups avec des permissions appropriées

## Dépannage

### Problèmes courants

1. **Permission refusée**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **PostgreSQL non accessible**
   ```bash
   # Vérifier si PostgreSQL tourne
   pg_isready
   
   # Démarrer PostgreSQL si nécessaire
   brew services start postgresql
   ```

3. **Base de données non trouvée**
   ```bash
   # Lister les bases de données
   psql -l
   
   # Créer la base de données
# Créer la base de données
   createdb hrapp
   ```

4. **Espace disque insuffisant**
   ```bash
   # Vérifier l'espace disque
   df -h
   
   # Nettoyer manuellement les anciens backups
   ./scripts/cleanup_backups.sh
   ```

## Sécurité

- Les backups contiennent toutes vos données, protégez-les
- Utilisez des permissions restrictives sur les scripts et backups
- Envisagez le chiffrement des backups pour les données sensibles
- Stockez une copie des backups hors site (offsite)
