#!/bin/bash
# Script de déploiement du nouveau bot sur VPS

VPS_HOST="root@213.199.41.168"
BOT_DIR="/opt/toTheMoon_tradebot"
SERVICE_NAME="tothemoon-tradebot"

echo "🚀 Déploiement du nouveau bot de trading sur VPS..."

# Création du répertoire sur le VPS
echo "📁 Création du répertoire du bot sur le VPS..."
ssh $VPS_HOST "mkdir -p $BOT_DIR"

# Copie des fichiers
echo "📤 Copie des fichiers vers le VPS..."
scp -r * $VPS_HOST:$BOT_DIR/

# Installation des dépendances sur le VPS
echo "📦 Installation des dépendances Python sur le VPS..."
ssh $VPS_HOST << 'EOF'
cd /opt/toTheMoon_tradebot

# Mise à jour du système
apt update

# Installation de Python et pip si nécessaire
apt install -y python3 python3-pip python3-venv

# Création d'un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Installation de TA-Lib (nécessaire compilation)
apt install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
make install
cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Reinstallation de TA-Lib Python
pip install TA-Lib

# Test de l'installation
python3 -c "import talib; print('✅ TA-Lib installé avec succès')"

# Permissions
chmod +x run.py
chmod +x investor_report.py
EOF

echo "✅ Installation terminée sur le VPS !"
echo ""
echo "📝 Prochaines étapes :"
echo "   1. Configurer le fichier .env sur le VPS"
echo "   2. Configurer le service systemd"
echo "   3. Démarrer le bot"
echo ""
