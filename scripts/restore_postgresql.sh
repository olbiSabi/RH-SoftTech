#!/bin/bash

# =============================================================================
# SCRIPT DE RESTAURATION POSTGRESQL - HR_ONIAN
# =============================================================================

# Configuration
DB_NAME="hrapp"
DB_USER="hr"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/backups"
LOG_FILE="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/logs/backup.log"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fonction d'aide
show_help() {
    echo "Usage: $0 [backup_file]"
    echo "  backup_file: Chemin vers le fichier de backup à restaurer"
    echo "  Si non spécifié, liste les backups disponibles"
    echo ""
    echo "Exemples:"
    echo "  $0                                    # Lister les backups"
    echo "  $0 /path/to/backup.sql.gz            # Restaurer un backup spécifique"
    echo "  $0 hrapp_backup_20240208_120000.sql.gz  # Restaurer depuis le dossier backups"
}

# Vérification des arguments
if [ $# -eq 0 ]; then
    echo "Backups disponibles dans $BACKUP_DIR:"
    ls -la "$BACKUP_DIR"/hrapp_backup_*.sql.gz 2>/dev/null | awk '{print $9, $5}' | column -t
    echo ""
    echo "Utilisation: $0 <backup_file>"
    exit 0
fi

BACKUP_FILE="$1"

# Vérification si le fichier existe
if [ ! -f "$BACKUP_FILE" ]; then
    # Si le chemin n'est pas complet, chercher dans le dossier backups
    if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        log "ERREUR: Fichier de backup non trouvé: $BACKUP_FILE"
        echo "Backups disponibles:"
        ls -la "$BACKUP_DIR"/hrapp_backup_*.sql.gz 2>/dev/null | awk '{print $9}' | sed 's#.*/##'
        exit 1
    else
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    fi
fi

log "Début de la restauration depuis: $BACKUP_FILE"

# Vérification si PostgreSQL est en cours d'exécution
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
    log "ERREUR: PostgreSQL n'est pas accessible sur $DB_HOST:$DB_PORT"
    exit 1
fi

# Confirmation de la restauration
echo "ATTENTION: Cette opération va remplacer complètement la base de données $DB_NAME"
echo "Backup à restaurer: $BACKUP_FILE"
echo "Base de données cible: $DB_NAME"
echo ""
read -p "Êtes-vous sûr de vouloir continuer? (oui/non): " confirm

if [ "$confirm" != "oui" ]; then
    log "Restauration annulée par l'utilisateur"
    exit 0
fi

# Création d'un backup de sécurité avant restauration
SAFETY_BACKUP="${BACKUP_DIR}/safety_backup_before_restore_$(date +%Y%m%d_%H%M%S).sql"
log "Création d'un backup de sécurité: $SAFETY_BACKUP"

if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$SAFETY_BACKUP" 2>> "$LOG_FILE"; then
    gzip "$SAFETY_BACKUP"
    log "Backup de sécurité créé: ${SAFETY_BACKUP}.gz"
else
    log "AVERTISSEMENT: Impossible de créer le backup de sécurité"
fi

# Suppression et recréation de la base de données
log "Suppression de la base de données $DB_NAME"
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>> "$LOG_FILE"

log "Création de la base de données $DB_NAME"
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>> "$LOG_FILE"

# Restauration
log "Restauration de la base de données depuis $BACKUP_FILE"

if [[ "$BACKUP_FILE" == *.gz ]]; then
    # Fichier compressé
    if gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>> "$LOG_FILE"; then
        log "Restauration terminée avec succès"
    else
        log "ERREUR: Échec de la restauration"
        exit 1
    fi
else
    # Fichier non compressé
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE" 2>> "$LOG_FILE"; then
        log "Restauration terminée avec succès"
    else
        log "ERREUR: Échec de la restauration"
        exit 1
    fi
fi

# Vérification de la restauration
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ -n "$TABLE_COUNT" ] && [ "$TABLE_COUNT" -gt 0 ]; then
    log "Restauration vérifiée: $TABLE_COUNT tables trouvées"
    echo "Restauration réussie! Base de données $DB_NAME contient $TABLE_COUNT tables"
else
    log "AVERTISSEMENT: La restauration semble incomplète"
fi

exit 0
