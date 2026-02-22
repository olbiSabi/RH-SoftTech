#!/bin/bash
# ============================================
# HR_ONIAN - Script d'initialisation Docker
# ============================================
# Ce script s'execute au demarrage du conteneur web.
# Il gere : attente BDD, migrations, collectstatic, seed data.

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  HR_ONIAN - Initialisation             ${NC}"
echo -e "${GREEN}========================================${NC}"

# ------------------------------------------
# 1. Attendre que Redis soit pret (si configure)
# ------------------------------------------
if [ -n "${REDIS_URL}" ]; then
    echo -e "${YELLOW}[0/6] Attente de Redis...${NC}"
    MAX_RETRIES=20
    RETRY=0
    until python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
r.ping()
" 2>/dev/null; do
        RETRY=$((RETRY + 1))
        if [ $RETRY -ge $MAX_RETRIES ]; then
            echo "  ATTENTION: Redis non disponible apres ${MAX_RETRIES} tentatives - sessions en base de donnees."
            break
        fi
        echo "  Redis non disponible, tentative $RETRY/$MAX_RETRIES..."
        sleep 2
    done
    echo "  Redis pret."
fi

# ------------------------------------------
# 2. Attendre que PostgreSQL soit pret
# ------------------------------------------
echo -e "${YELLOW}[1/6] Attente de PostgreSQL...${NC}"
MAX_RETRIES=30
RETRY=0
until python -c "
import psycopg2
psycopg2.connect(
    dbname='${DB_NAME:-hrapp}',
    user='${DB_USER:-hr}',
    password='${DB_PASSWORD:-}',
    host='${DB_HOST:-db}',
    port='${DB_PORT:-5432}'
)
" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo "ERREUR: PostgreSQL n'est pas disponible apres ${MAX_RETRIES} tentatives."
        exit 1
    fi
    echo "  PostgreSQL non disponible, tentative $RETRY/$MAX_RETRIES..."
    sleep 2
done
echo "  PostgreSQL pret."

# ------------------------------------------
# 2. Appliquer les migrations
# ------------------------------------------
echo -e "${YELLOW}[2/6] Application des migrations...${NC}"
python manage.py migrate --noinput

# ------------------------------------------
# 3. Collecter les fichiers statiques
# ------------------------------------------
echo -e "${YELLOW}[3/6] Collecte des fichiers statiques...${NC}"
python manage.py collectstatic --noinput

# ------------------------------------------
# 4. Charger les donnees par defaut
# ------------------------------------------
if [ "${LOAD_DEFAULT_DATA}" = "true" ]; then
    echo -e "${YELLOW}[4/6] Chargement des donnees par defaut...${NC}"
    python manage.py charger_donnees 2>&1 || echo "  (donnees deja presentes ou erreur ignoree)"
else
    echo -e "${YELLOW}[4/6] Chargement des donnees par defaut... IGNORE (LOAD_DEFAULT_DATA != true)${NC}"
fi

# ------------------------------------------
# 5. Charger l'employe par defaut
# ------------------------------------------
if [ "${LOAD_DEFAULT_EMPLOYEE}" = "true" ]; then
    echo -e "${YELLOW}[5/6] Chargement de l'employe par defaut (MT000001)...${NC}"
    python manage.py charger_employe 2>&1 || echo "  (employe deja present ou erreur ignoree)"
else
    echo -e "${YELLOW}[5/6] Chargement de l'employe par defaut... IGNORE (LOAD_DEFAULT_EMPLOYEE != true)${NC}"
fi

# ------------------------------------------
# 6. Creer un superutilisateur si demande
# ------------------------------------------
if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
    echo -e "${YELLOW}[6/6] Creation du superutilisateur...${NC}"
    python manage.py createsuperuser --noinput 2>/dev/null || echo "  (superutilisateur deja existant)"
else
    echo -e "${YELLOW}[6/6] Creation du superutilisateur... IGNORE (DJANGO_SUPERUSER_* non definis)${NC}"
fi

# ------------------------------------------
# Creer les repertoires necessaires
# ------------------------------------------
mkdir -p logs media backups

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Initialisation terminee !              ${NC}"
echo -e "${GREEN}========================================${NC}"

# Executer la commande passee en argument (gunicorn ou runserver)
exec "$@"
