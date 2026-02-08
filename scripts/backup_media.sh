#!/bin/bash

# =============================================================================
# SCRIPT DE BACKUP DES FICHIERS UPLOADES - HR_ONIAN
# =============================================================================
#
# Sauvegarde tous les fichiers media (BLs, PDFs, justificatifs, photos,
# pièces jointes) dans une archive compressée.
#
# Usage:
#   ./scripts/backup_media.sh                  # Backup complet
#   ./scripts/backup_media.sh --incremental    # Backup incrémental (nouveaux fichiers depuis le dernier backup)
#
# Planification cron (quotidien à 2h00):
#   0 2 * * * /chemin/vers/HR_ONIAN/scripts/backup_media.sh >> /chemin/vers/logs/backup_media.log 2>&1
#
# =============================================================================

# Configuration
PROJECT_DIR="/Users/sabioniankitan/Desktop/ProjetDjango/App/HR_ONIAN"
MEDIA_DIR="$PROJECT_DIR/media"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="$PROJECT_DIR/logs/backup.log"
MAX_BACKUPS=7
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/hrapp_media_backup_${DATE}.tar.gz"

# Dossiers media à sauvegarder
MEDIA_SUBDIRS=(
    "audit/rapports"
    "frais/justificatifs"
    "gestion_achats/bons_commande"
    "gestion_achats/pieces_jointes"
    "materiel/photos"
    "materiel/documents"
    "materiel/affectations"
    "materiel/mouvements"
    "materiel/maintenances"
    "justificatifs_absences"
    "photos/employes"
    "documents/employes"
    "tickets_pieces_jointes"
    "logos_entreprise"
)

# Création des répertoires nécessaires
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fonction pour formater la taille
format_size() {
    local size=$1
    if [ "$size" -ge 1073741824 ]; then
        echo "$(echo "scale=1; $size / 1073741824" | bc) Go"
    elif [ "$size" -ge 1048576 ]; then
        echo "$(echo "scale=1; $size / 1048576" | bc) Mo"
    elif [ "$size" -ge 1024 ]; then
        echo "$(echo "scale=1; $size / 1024" | bc) Ko"
    else
        echo "${size} octets"
    fi
}

# =============================================================================
# Début du backup
# =============================================================================

log "========================================"
log "Début du backup des fichiers media"
log "========================================"

# Vérification du répertoire media
if [ ! -d "$MEDIA_DIR" ]; then
    log "AVERTISSEMENT: Le répertoire media n'existe pas: $MEDIA_DIR"
    log "Création du répertoire media"
    mkdir -p "$MEDIA_DIR"
fi

# Mode incrémental ou complet
INCREMENTAL=false
if [ "$1" = "--incremental" ]; then
    INCREMENTAL=true
    # Compter les backups existants
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "hrapp_media_backup_*.tar.gz" -type f | wc -l | tr -d ' ')

    if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
        # Suppression des anciens backups
        find "$BACKUP_DIR" -name "hrapp_media_backup_*.tar.gz" -type f -mtime +$MAX_BACKUPS -delete
    fi

    # Trouver le dernier backup
    LAST_BACKUP=$(find "$BACKUP_DIR" -name "hrapp_media_backup_*.tar.gz" -type f | sort -r | head -1)
    if [ -n "$LAST_BACKUP" ]; then
        BACKUP_FILE="${BACKUP_DIR}/media_incremental_${DATE}.tar.gz"
        log "Mode INCREMENTAL - Fichiers modifiés depuis: $(stat -f '%Sm' "$LAST_BACKUP" 2>/dev/null || stat -c '%y' "$LAST_BACKUP" 2>/dev/null)"
    else
        log "Aucun backup précédent trouvé, passage en mode complet"
        INCREMENTAL=false
    fi
fi

if [ "$INCREMENTAL" = false ]; then
    log "Mode COMPLET - Sauvegarde de tous les fichiers"
fi

# Inventaire des fichiers à sauvegarder
log ""
log "--- Inventaire des fichiers ---"
TOTAL_FILES=0
TOTAL_SIZE=0
DIRS_FOUND=0

for subdir in "${MEDIA_SUBDIRS[@]}"; do
    dir_path="${MEDIA_DIR}/${subdir}"
    if [ -d "$dir_path" ]; then
        if [ "$INCREMENTAL" = true ]; then
            count=$(find "$dir_path" -type f -newer "$LAST_BACKUP" | wc -l | tr -d ' ')
            size=$(find "$dir_path" -type f -newer "$LAST_BACKUP" -exec stat -f '%z' {} + 2>/dev/null | awk '{s+=$1}END{print s+0}' || find "$dir_path" -type f -newer "$LAST_BACKUP" -printf '%s\n' 2>/dev/null | awk '{s+=$1}END{print s+0}')
        else
            count=$(find "$dir_path" -type f | wc -l | tr -d ' ')
            size=$(find "$dir_path" -type f -exec stat -f '%z' {} + 2>/dev/null | awk '{s+=$1}END{print s+0}' || find "$dir_path" -type f -printf '%s\n' 2>/dev/null | awk '{s+=$1}END{print s+0}')
        fi
        if [ "$count" -gt 0 ]; then
            log "  ${subdir}: ${count} fichier(s) ($(format_size ${size:-0}))"
            TOTAL_FILES=$((TOTAL_FILES + count))
            TOTAL_SIZE=$((TOTAL_SIZE + ${size:-0}))
            DIRS_FOUND=$((DIRS_FOUND + 1))
        fi
    fi
done

log ""
log "Total: ${TOTAL_FILES} fichier(s) dans ${DIRS_FOUND} dossier(s) ($(format_size $TOTAL_SIZE))"

# Vérifier s'il y a des fichiers à sauvegarder
if [ "$TOTAL_FILES" -eq 0 ]; then
    log "Aucun fichier à sauvegarder. Fin du script."
    exit 0
fi

# =============================================================================
# Création du backup
# =============================================================================

log ""
log "Création de l'archive: $(basename "$BACKUP_FILE")"

if [ "$INCREMENTAL" = true ]; then
    # Backup incrémental : uniquement les fichiers modifiés depuis le dernier backup
    tar -czf "$BACKUP_FILE" \
        -C "$MEDIA_DIR" \
        --newer-mtime="$(stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$LAST_BACKUP" 2>/dev/null || stat -c '%y' "$LAST_BACKUP" 2>/dev/null)" \
        . 2>> "$LOG_FILE"
else
    # Backup complet : construire la liste des dossiers existants
    EXISTING_DIRS=()
    for subdir in "${MEDIA_SUBDIRS[@]}"; do
        if [ -d "${MEDIA_DIR}/${subdir}" ]; then
            EXISTING_DIRS+=("$subdir")
        fi
    done

    if [ ${#EXISTING_DIRS[@]} -eq 0 ]; then
        log "Aucun dossier media trouvé. Fin du script."
        exit 0
    fi

    tar -czf "$BACKUP_FILE" \
        -C "$MEDIA_DIR" \
        "${EXISTING_DIRS[@]}" 2>> "$LOG_FILE"
fi

# Vérification du résultat
if [ $? -eq 0 ] && [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup créé avec succès: $(basename "$BACKUP_FILE") (${BACKUP_SIZE})"

    # Vérification de l'intégrité de l'archive
    if tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
        ARCHIVED_COUNT=$(tar -tzf "$BACKUP_FILE" | grep -v '/$' | wc -l | tr -d ' ')
        log "Intégrité vérifiée: ${ARCHIVED_COUNT} fichier(s) dans l'archive"
    else
        log "AVERTISSEMENT: L'archive pourrait être corrompue"
    fi
else
    log "ERREUR: Échec de la création du backup"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# =============================================================================
# Nettoyage des anciens backups
# =============================================================================

log ""
log "Nettoyage des anciens backups (conservation des ${MAX_BACKUPS} plus récents)"

find "$BACKUP_DIR" -name "hrapp_media_backup_*.tar.gz" -type f -mtime +$MAX_BACKUPS -delete

REMAINING=$(find "$BACKUP_DIR" -name "hrapp_media_backup_*.tar.gz" -type f | wc -l | tr -d ' ')
log "Backups conservés: ${REMAINING}"

# =============================================================================
# Résumé
# =============================================================================

DISK_SPACE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $4}')
TOTAL_BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

log ""
log "========================================"
log "Backup terminé avec succès"
log "  Archive     : $(basename "$BACKUP_FILE")"
log "  Fichiers    : ${TOTAL_FILES}"
log "  Taille      : ${BACKUP_SIZE}"
log "  Mode        : $([ "$INCREMENTAL" = true ] && echo "Incrémental" || echo "Complet")"
log "  Espace total backups media : ${TOTAL_BACKUP_SIZE}"
log "  Espace disque disponible   : ${DISK_SPACE}"
log "========================================"

exit 0
