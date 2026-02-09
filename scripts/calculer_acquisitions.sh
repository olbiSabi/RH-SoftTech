#!/bin/bash

# =============================================================================
# Script d'automatisation du calcul des acquisitions de conges
# Auteur: HR_ONIAN
# Description: Calcule automatiquement les acquisitions de conges pour les
#              employes actifs. Les rejets et erreurs sont traces dans les logs.
#
# Usage:
#   ./scripts/calculer_acquisitions.sh                  # Calcul complet
#   ./scripts/calculer_acquisitions.sh --annee 2026     # Annee specifique
#   ./scripts/calculer_acquisitions.sh --dry-run        # Simulation
#
# Planification cron (quotidien a 3h00):
#   0 3 * * * /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh >> /dev/null 2>&1
# =============================================================================

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${PROJECT_DIR}/../.env"
LOG_DIR="${PROJECT_DIR}/logs/acquisitions"
LOG_FILE="${LOG_DIR}/acquisitions_$(date +%Y%m%d).log"

# Creer le dossier de logs s'il n'existe pas
mkdir -p "$LOG_DIR"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] AVERTISSEMENT - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERREUR - $1" | tee -a "$LOG_FILE"
}

# Debut du script
log "======================================================================"
log "DEBUT DU CALCUL DES ACQUISITIONS DE CONGES"
log "======================================================================"

# Verifier que l'environnement virtuel existe
if [ ! -d "$VENV_PATH" ]; then
    log_error "Environnement virtuel non trouve a $VENV_PATH"
    exit 1
fi

# Activer l'environnement virtuel
log "Activation de l'environnement virtuel..."
source "${VENV_PATH}/bin/activate"

if [ $? -ne 0 ]; then
    log_error "Impossible d'activer l'environnement virtuel"
    exit 1
fi

# Se deplacer dans le dossier du projet
cd "$PROJECT_DIR" || exit 1
log "Repertoire de travail: $(pwd)"

# Construire la commande avec les arguments passes au script
# --tous et --verbeux sont toujours actives pour capturer les rejets dans les logs
CMD_ARGS="--tous --verbeux"
for arg in "$@"; do
    CMD_ARGS="$CMD_ARGS $arg"
done

log "Execution: python manage.py calculer_acquisitions $CMD_ARGS"

# Fichier temporaire pour capturer la sortie
TEMP_OUTPUT=$(mktemp)

# Executer la commande de calcul
python manage.py calculer_acquisitions $CMD_ARGS > "$TEMP_OUTPUT" 2>&1

# Verifier le code de sortie
EXIT_CODE=$?

# Ecrire la sortie dans le log avec classification
while IFS= read -r line; do
    if [[ "$line" == *"REJET"* ]] || [[ "$line" == *"DETAIL DES REJETS"* ]]; then
        log_warn "$line"
    elif [[ "$line" == *"ERREUR"* ]] || [[ "$line" == *"DETAIL DES ERREURS"* ]]; then
        log_error "$line"
    elif [[ -n "$line" ]]; then
        log "$line"
    fi
done < "$TEMP_OUTPUT"

# Extraire les compteurs du resume
REJETS=$(grep -c "REJET" "$TEMP_OUTPUT" 2>/dev/null || echo "0")
ERREURS=$(grep -c "ERREUR" "$TEMP_OUTPUT" 2>/dev/null || echo "0")

# Nettoyer le fichier temporaire
rm -f "$TEMP_OUTPUT"

# Resume final
log ""
if [ $EXIT_CODE -eq 0 ]; then
    log "Calcul termine avec succes"
else
    log_error "Erreur lors du calcul (code: $EXIT_CODE)"
fi

if [ "$REJETS" -gt 0 ]; then
    log_warn "$REJETS ligne(s) de rejet dans la sortie (voir details ci-dessus)"
fi

if [ "$ERREURS" -gt 0 ]; then
    log_error "$ERREURS ligne(s) d'erreur dans la sortie (voir details ci-dessus)"
fi

# Desactiver l'environnement virtuel
deactivate

log "======================================================================"
log "FIN DU CALCUL DES ACQUISITIONS DE CONGES"
log "======================================================================"
log ""

exit $EXIT_CODE
