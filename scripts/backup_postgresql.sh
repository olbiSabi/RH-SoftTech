#!/bin/bash

# =============================================================================
# SCRIPT DE BACKUP QUOTIDIEN POSTGRESQL - HR_ONIAN
# =============================================================================

# Configuration
DB_NAME="hrapp"
DB_USER="hr"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/backups"
LOG_FILE="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/logs/backup.log"
MAX_BACKUPS=7
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/hrapp_backup_${DATE}.sql"

# Création des répertoires nécessaires
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Début du backup
log "Début du backup de la base de données $DB_NAME"

# Vérification si PostgreSQL est en cours d'exécution
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
    log "ERREUR: PostgreSQL n'est pas accessible sur $DB_HOST:$DB_PORT"
    exit 1
fi

# Vérification si la base de données existe
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    log "ERREUR: La base de données $DB_NAME n'existe pas"
    exit 1
fi

# Création du backup
log "Création du backup: $BACKUP_FILE"

if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE" 2>> "$LOG_FILE"; then
    # Compression du backup
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    # Vérification de la taille du fichier
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup créé avec succès: $BACKUP_FILE (Taille: $BACKUP_SIZE)"
    
    # Nettoyage des anciens backups
    log "Nettoyage des anciens backups (conservation des $MAX_BACKUPS plus récents)"
    
    # Suppression des anciens backups
    find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f -mtime +$MAX_BACKUPS -delete
    
    # Compte des backups restants
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f | wc -l)
    log "Nombre de backups conservés: $BACKUP_COUNT"
    
    log "Backup terminé avec succès"
else
    log "ERREUR: Échec de la création du backup"
    # Suppression du fichier incomplet si existant
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Affichage de l'espace disque disponible
DISK_SPACE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $4}')
log "Espace disque disponible dans $BACKUP_DIR: $DISK_SPACE"

exit 0
