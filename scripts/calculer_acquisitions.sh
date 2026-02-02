#!/bin/bash

# Script d'automatisation du calcul des acquisitions de congés
# Auteur: HR_ONIAN
# Description: Calcule automatiquement les acquisitions de congés pour les employés actifs

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${PROJECT_DIR}/../.env"
LOG_DIR="${PROJECT_DIR}/logs/acquisitions"
LOG_FILE="${LOG_DIR}/acquisitions_$(date +%Y%m%d).log"

# Créer le dossier de logs s'il n'existe pas
mkdir -p "$LOG_DIR"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Début du script
log "======================================================================"
log "DÉBUT DU CALCUL DES ACQUISITIONS DE CONGÉS"
log "======================================================================"

# Vérifier que l'environnement virtuel existe
if [ ! -d "$VENV_PATH" ]; then
    log "ERREUR: Environnement virtuel non trouvé à $VENV_PATH"
    exit 1
fi

# Activer l'environnement virtuel
log "Activation de l'environnement virtuel..."
source "${VENV_PATH}/bin/activate"

if [ $? -ne 0 ]; then
    log "ERREUR: Impossible d'activer l'environnement virtuel"
    exit 1
fi

# Se déplacer dans le dossier du projet
cd "$PROJECT_DIR" || exit 1
log "Répertoire de travail: $(pwd)"

# Exécuter la commande de calcul
log "Exécution du calcul des acquisitions..."
python manage.py calculer_acquisitions --tous --verbeux 2>&1 | tee -a "$LOG_FILE"

# Vérifier le code de sortie
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Calcul terminé avec succès"
else
    log "❌ Erreur lors du calcul (code: $EXIT_CODE)"
fi

# Désactiver l'environnement virtuel
deactivate

log "======================================================================"
log "FIN DU CALCUL DES ACQUISITIONS DE CONGÉS"
log "======================================================================"
log ""

exit $EXIT_CODE
