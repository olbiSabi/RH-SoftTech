#!/bin/bash

# =============================================================================
# SCRIPT DE NETTOYAGE DES BACKUPS - HR_ONIAN
# =============================================================================

# Configuration
BACKUP_DIR="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/backups"
LOG_FILE="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN/logs/backup.log"
MAX_BACKUPS=7
MAX_SIZE_GB=10

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fonction de conversion de taille en bytes
convert_to_bytes() {
    local size=$1
    local unit=${size: -1}
    local number=${size%?}
    
    case $unit in
        G|g) echo $((number * 1024 * 1024 * 1024)) ;;
        M|m) echo $((number * 1024 * 1024)) ;;
        K|k) echo $((number * 1024)) ;;
        *) echo $number ;;
    esac
}

log "Début du nettoyage des backups"

# Vérification du répertoire de backups
if [ ! -d "$BACKUP_DIR" ]; then
    log "ERREUR: Répertoire de backups non trouvé: $BACKUP_DIR"
    exit 1
fi

# Compte actuel des backups
CURRENT_BACKUPS=$(find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f | wc -l)
log "Nombre actuel de backups: $CURRENT_BACKUPS"

# Espace total utilisé par les backups
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Espace total utilisé: $TOTAL_SIZE"

# Nettoyage par nombre de backups
if [ "$CURRENT_BACKUPS" -gt "$MAX_BACKUPS" ]; then
    log "Trop de backups ($CURRENT_BACKUPS > $MAX_BACKUPS), suppression des plus anciens"
    
    # Trouver et supprimer les backups les plus anciens
    find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f -mtime +$MAX_BACKUPS -delete
    
    # CURRENT_BACKUPS=$(find "$BACKUP_DIR" -name "hr_onian_backup_*.sql.gz" -type f | wc -l)
    # log "Nombre actuel de backups: $CURRENT_BACKUPS"
        rm "$file"
    done
fi

# Nettoyage par taille totale
MAX_SIZE_BYTES=$(convert_to_bytes "${MAX_SIZE_GB}G")
CURRENT_SIZE_BYTES=$(du -sb "$BACKUP_DIR" | cut -f1)

if [ "$CURRENT_SIZE_BYTES" -gt "$MAX_SIZE_BYTES" ]; then
    log "Espace total dépassé ($TOTAL_SIZE > ${MAX_SIZE_GB}GB), suppression des plus anciens"
    
    # Supprimer les plus anciens jusqu'à atteindre la limite
    find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f -printf "%T@ %p\n" | \
    sort -n | \
    while read timestamp file; do
        if [ "$(du -sb "$BACKUP_DIR" | cut -f1)" -le "$MAX_SIZE_BYTES" ]; then
            break
        fi
        SIZE=$(du -h "$file" | cut -f1)
        log "Suppression: $file ($SIZE)"
        rm "$file"
    done
fi

# Nettoyage des fichiers corrompus ou incomplets
log "Vérification des fichiers corrompus"
find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f | while read file; do
    if ! gzip -t "$file" 2>/dev/null; then
        SIZE=$(du -h "$file" | cut -f1)
        log "Suppression du fichier corrompu: $file ($SIZE)"
        rm "$file"
    fi
done

# Rapport final
FINAL_BACKUPS=$(find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f | wc -l)
FINAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "Nettoyage terminé"
log "Backups restants: $FINAL_BACKUPS"
log "Espace utilisé: $FINAL_SIZE"

# Liste des backups restants
log "Liste des backups conservés:"
find "$BACKUP_DIR" -name "hrapp_backup_*.sql.gz" -type f -printf "%T@ %f\n" | \
sort -nr | \
while read timestamp filename; do
    SIZE=$(du -h "$BACKUP_DIR/$filename" | cut -f1)
    DATE=$(date -d "@${timestamp%.*}" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -r "$BACKUP_DIR/$filename" "+%Y-%m-%d %H:%M:%S")
    log "  $filename ($SIZE) - $DATE"
done

exit 0
