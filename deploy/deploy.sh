#!/bin/bash
# ============================================
# Script de deploiement HR_ONIAN
# ============================================
#
# Usage : bash deploy/deploy.sh
#
# Pre-requis :
#   - Python 3.12+ installe
#   - PostgreSQL installe et configure
#   - Nginx installe
#   - Fichier .env.local configure (copier .env.production et adapter)

set -e  # Arreter au premier erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploiement HR_ONIAN                  ${NC}"
echo -e "${GREEN}========================================${NC}"

# Verifier qu'on est dans le bon repertoire
if [ ! -f "manage.py" ]; then
    echo -e "${RED}ERREUR: Executez ce script depuis la racine du projet (ou se trouve manage.py)${NC}"
    exit 1
fi

# Verifier que .env.local existe
if [ ! -f ".env.local" ]; then
    echo -e "${RED}ERREUR: Fichier .env.local manquant.${NC}"
    echo -e "${YELLOW}Copiez .env.production en .env.local et adaptez les valeurs :${NC}"
    echo "  cp .env.production .env.local"
    exit 1
fi

# 1. Installer les dependances
echo -e "\n${YELLOW}[1/7] Installation des dependances Python...${NC}"
pip install -r requirements.txt --quiet

# 2. Appliquer les migrations
echo -e "${YELLOW}[2/7] Application des migrations...${NC}"
python manage.py migrate --noinput

# 3. Collecter les fichiers statiques
echo -e "${YELLOW}[3/7] Collecte des fichiers statiques...${NC}"
python manage.py collectstatic --noinput --clear

# 4. Verifier la configuration Django
echo -e "${YELLOW}[4/7] Verification de la configuration...${NC}"
python manage.py check --deploy 2>&1 || true

# 5. Creer le repertoire de logs
echo -e "${YELLOW}[5/7] Creation du repertoire de logs...${NC}"
mkdir -p logs

# 6. Lancer les tests
echo -e "${YELLOW}[6/7] Execution des tests...${NC}"
python manage.py test --verbosity=1 2>&1 | tail -3

# 7. Redemarrer Gunicorn
echo -e "${YELLOW}[7/7] Redemarrage du serveur...${NC}"
if systemctl is-active --quiet hr_onian 2>/dev/null; then
    sudo systemctl restart hr_onian
    echo -e "${GREEN}Service hr_onian redemarre.${NC}"
else
    echo -e "${YELLOW}Service hr_onian non installe en tant que service systemd.${NC}"
    echo -e "${YELLOW}Pour lancer manuellement :${NC}"
    echo "  gunicorn HR_ONIAN.wsgi:application -c gunicorn.conf.py"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploiement termine avec succes !     ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Prochaines etapes :"
echo "  1. Configurer Nginx : sudo cp deploy/nginx.conf /etc/nginx/sites-available/hr_onian"
echo "  2. Activer le site  : sudo ln -s /etc/nginx/sites-available/hr_onian /etc/nginx/sites-enabled/"
echo "  3. Obtenir un certificat SSL : sudo certbot --nginx -d votre-domaine.com"
echo "  4. Redemarrer Nginx : sudo systemctl reload nginx"
