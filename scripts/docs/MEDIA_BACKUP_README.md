# Scripts de Backup Média - HR_ONIAN

Ce dossier contient les scripts de gestion des backups des fichiers média pour le projet HR_ONIAN.

## Script disponible

### `backup_media.sh`
Script de backup des fichiers uploadés (BLs, PDFs, pièces jointes, photos, documents).

**Fonctionnalités:**
- Backup complet de tous les fichiers média
- Backup incrémental (optionnel)
- Compression automatique (tar.gz)
- Nettoyage des anciens backups (conservation des 7 derniers)
- Inventaire détaillé des fichiers sauvegardés
- Vérification de l'intégrité des archives
- Logging détaillé

**Configuration:**
```bash
PROJECT_DIR="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN"
MEDIA_DIR="$PROJECT_DIR/media"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="$PROJECT_DIR/logs/backup.log"
MAX_BACKUPS=7
```

**Dossiers sauvegardés:**
- `audit/rapports` - Rapports d'audit
- `frais/justificatifs` - Justificatifs de frais
- `gestion_achats/bons_commande` - Bons de commande
- `gestion_achats/pieces_jointes` - Pièces jointes d'achats
- `materiel/photos` - Photos du matériel
- `materiel/documents` - Documents du matériel
- `materiel/affectations` - Documents d'affectation
- `materiel/mouvements` - Documents de mouvements
- `materiel/maintenances` - Documents de maintenance
- `justificatifs_absences` - Justificatifs d'absences
- `photos/employes` - Photos des employés
- `documents/employes` - Documents des employés
- `tickets_pieces_jointes` - Pièces jointes des tickets
- `logos_entreprise` - Logos de l'entreprise

**Utilisation:**
```bash
# Backup complet
./scripts/backup_media.sh

# Backup incrémental (nouveaux fichiers depuis le dernier backup)
./scripts/backup_media.sh --incremental
```

**Exemple de sortie:**
```
========================================
Début du backup des fichiers media
========================================
Mode COMPLET - Sauvegarde de tous les fichiers

--- Inventaire des fichiers ---
  frais/justificatifs: 2 fichier(s) (117.4 Ko)
  gestion_achats/bons_commande: 87 fichier(s) (1.0 Mo)
  justificatifs_absences: 2 fichier(s) (3.0 Mo)
  photos/employes: 20 fichier(s) (799.4 Ko)
  documents/employes: 20 fichier(s) (16.5 Mo)
  tickets_pieces_jointes: 2 fichier(s) (25.1 Ko)
  logos_entreprise: 2 fichier(s) (504.4 Ko)

Total: 135 fichier(s) dans 7 dossier(s) (22.0 Mo)

Création de l'archive: hrapp_media_backup_20260208_194638.tar.gz
Backup créé avec succès: hrapp_media_backup_20260208_194638.tar.gz (20M)
Intégrité vérifiée: 135 fichier(s) dans l'archive

Nettoyage des anciens backups (conservation des 7 plus récents)
Backups conservés: 1

========================================
Backup terminé avec succès
  Archive     : hrapp_media_backup_20260208_194638.tar.gz
  Fichiers    : 135
  Taille      : 20M
  Mode        : Complet
  Espace total backups media : 21M
  Espace disque disponible   : 265Gi
========================================
```

## Automatisation avec Cron

### Configuration quotidienne
```bash
# Ouvrir l'éditeur crontab
crontab -e

# Ajouter la ligne suivante pour backup quotidien à 3h du matin
0 3 * * * /Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/scripts/backup_media.sh
```

### Configuration avec backup base de données + média
```bash
# Backup base de données à 2h
0 2 * * * /Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/scripts/backup_postgresql.sh

# Backup fichiers média à 3h
0 3 * * * /Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/scripts/backup_media.sh

# Nettoyage hebdomadaire le dimanche à 4h
0 4 * * 0 /Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/scripts/cleanup_backups.sh
```

## Logs

Les scripts génèrent des logs dans le fichier `logs/backup.log` avec:
- Horodatage de chaque opération
- Inventaire détaillé des fichiers
- Taille des backups créés
- Espace disque disponible

## Bonnes pratiques

1. **Test régulier**: Vérifiez régulièrement l'intégrité des archives
2. **Stockage externe**: Copiez les backups sur un stockage externe
3. **Monitoring**: Surveillez les logs pour détecter les erreurs
4. **Espace disque**: Vérifiez régulièrement l'espace disponible
5. **Sécurité**: Protégez les backups contenant des documents sensibles

## Dépannage

### Problèmes courants

1. **Permission refusée**
   ```bash
   chmod +x scripts/backup_media.sh
   ```

2. **Répertoire media vide**
   ```bash
   # Vérifier le contenu
   ls -la media/
   
   # Le script créera le répertoire si nécessaire
   ```

3. **Espace disque insuffisant**
   ```bash
   # Vérifier l'espace disque
   df -h
   
   # Nettoyer manuellement les anciens backups
   ./scripts/cleanup_backups.sh
   ```

## Sécurité

- Les backups contiennent des documents sensibles, protégez-les
- Utilisez des permissions restrictives sur les scripts et backups
- Envisagez le chiffrement des backups pour les données sensibles
- Stockez une copie des backups hors site (offsite)

## Restauration

Pour restaurer les fichiers média:
```bash
# Extraire l'archive complète
tar -xzf backups/hrapp_media_backup_20260208_194638.tar.gz -C media/

# Lister le contenu d'une archive
tar -tzf backups/hrapp_media_backup_20260208_194638.tar.gz
```
