#!/bin/bash
# Script de déploiement complet du bot sur VPS

VPS_HOST="root@213.199.41.168"
BOT_DIR="/opt/toTheMoon_tradebot"
SERVICE_NAME="tothemoon-tradebot"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 DÉPLOIEMENT COMPLET DU BOT TOTHEMOON${NC}"
echo "=================================================="
echo ""

# Étape 1: Vérification de la connexion SSH
echo -e "${YELLOW}📡 Vérification de la connexion SSH...${NC}"
if ssh -o ConnectTimeout=10 $VPS_HOST "echo 'Connexion SSH OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connexion SSH établie${NC}"
else
    echo -e "${RED}❌ Impossible de se connecter au VPS${NC}"
    echo "Vérifiez l'adresse IP et les clés SSH"
    exit 1
fi

# Étape 2: Désactivation de l'ancien bot
echo ""
echo -e "${YELLOW}🔄 Désactivation de l'ancien bot...${NC}"
ssh $VPS_HOST 'bash -s' < scripts/disable_old_bot.sh

# Étape 3: Création du répertoire et copie des fichiers
echo ""
echo -e "${YELLOW}📁 Création du répertoire et copie des fichiers...${NC}"
ssh $VPS_HOST "rm -rf $BOT_DIR && mkdir -p $BOT_DIR"

# Exclusion des fichiers locaux non nécessaires
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.vscode' \
    --exclude='logs/' \
    --exclude='data/' \
    --exclude='.env' \
    ./ $VPS_HOST:$BOT_DIR/

echo -e "${GREEN}✅ Fichiers copiés avec succès${NC}"

# Étape 4: Installation des dépendances
echo ""
echo -e "${YELLOW}📦 Installation des dépendances...${NC}"
ssh $VPS_HOST << EOF
cd $BOT_DIR

# Mise à jour du système
apt update -y

# Installation de Python et outils
apt install -y python3 python3-pip python3-venv build-essential wget curl

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Mise à jour de pip
pip install --upgrade pip

# Installation des dépendances Python
pip install -r requirements.txt

# Installation de TA-Lib
echo "Installation de TA-Lib..."
if [ ! -f "/usr/local/lib/libta_lib.so" ]; then
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr/local
    make && make install
    cd ..
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
    ldconfig
fi

# Installation du package Python TA-Lib
pip install TA-Lib

# Test de l'installation
python3 -c "import talib; print('✅ TA-Lib OK')"
python3 -c "import ccxt; print('✅ CCXT OK')"
python3 -c "import binance; print('✅ Binance OK')"

# Permissions
chmod +x run.py
chmod +x investor_report.py
chmod +x scripts/*.sh

echo "✅ Installation des dépendances terminée"
EOF

# Étape 5: Configuration du service systemd
echo ""
echo -e "${YELLOW}⚙️ Configuration du service systemd...${NC}"
ssh $VPS_HOST << EOF
cd $BOT_DIR

# Installation du service
cp scripts/tothemoon-tradebot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

echo "✅ Service systemd configuré"
EOF

# Étape 6: Configuration du fichier .env
echo ""
echo -e "${YELLOW}📝 Configuration du fichier .env...${NC}"
echo "IMPORTANT: Vous devez maintenant configurer le fichier .env sur le VPS"
echo ""
echo "Exécutez les commandes suivantes :"
echo -e "${BLUE}ssh $VPS_HOST${NC}"
echo -e "${BLUE}cd $BOT_DIR${NC}"
echo -e "${BLUE}nano .env${NC}"
echo ""
echo "Copiez la configuration de votre fichier .env local"

# Étape 7: Instructions finales
echo ""
echo -e "${GREEN}🎉 DÉPLOIEMENT TERMINÉ !${NC}"
echo "=================================================="
echo ""
echo -e "${YELLOW}📋 PROCHAINES ÉTAPES :${NC}"
echo ""
echo "1. Configurez le fichier .env :"
echo -e "   ${BLUE}ssh $VPS_HOST${NC}"
echo -e "   ${BLUE}cd $BOT_DIR${NC}"
echo -e "   ${BLUE}nano .env${NC}"
echo ""
echo "2. Configurez credentials.json pour Google Sheets :"
echo -e "   ${BLUE}nano credentials.json${NC}"
echo ""
echo "3. Testez la configuration :"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo -e "   ${BLUE}python3 run.py --test${NC}"
echo ""
echo "4. Démarrez le service :"
echo -e "   ${BLUE}systemctl start $SERVICE_NAME${NC}"
echo ""
echo "5. Vérifiez les logs :"
echo -e "   ${BLUE}journalctl -u $SERVICE_NAME -f${NC}"
echo ""
echo -e "${YELLOW}📊 COMMANDES UTILES :${NC}"
echo -e "   ${BLUE}systemctl status $SERVICE_NAME${NC}    # Statut"
echo -e "   ${BLUE}systemctl restart $SERVICE_NAME${NC}   # Redémarrage"
echo -e "   ${BLUE}systemctl stop $SERVICE_NAME${NC}      # Arrêt"
echo -e "   ${BLUE}journalctl -u $SERVICE_NAME -f${NC}    # Logs temps réel"
echo ""
echo -e "${GREEN}✅ Le bot est prêt à être démarré !${NC}"
echo ""
