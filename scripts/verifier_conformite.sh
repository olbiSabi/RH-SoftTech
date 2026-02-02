#!/bin/bash

# Script d'automatisation de la vérification de conformité
# Auteur: HR_ONIAN
# Description: Exécute les vérifications de conformité et envoie les alertes

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${PROJECT_DIR}/../.env"
LOG_DIR="${PROJECT_DIR}/logs/conformite"
LOG_FILE="${LOG_DIR}/conformite_$(date +%Y%m%d).log"

# Créer le dossier de logs s'il n'existe pas
mkdir -p "$LOG_DIR"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Début du script
log "======================================================================"
log "DÉBUT DE LA VÉRIFICATION DE CONFORMITÉ"
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

# Exécuter la commande de vérification
log "Exécution de la vérification de conformité..."
python manage.py verifier_conformite --tous --verbeux 2>&1 | tee -a "$LOG_FILE"

# Vérifier le code de sortie
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Vérification terminée avec succès"
else
    log "❌ Erreur lors de la vérification (code: $EXIT_CODE)"
fi

# Désactiver l'environnement virtuel
deactivate

log "======================================================================"
log "FIN DE LA VÉRIFICATION DE CONFORMITÉ"
log "======================================================================"
log ""

exit $EXIT_CODE
