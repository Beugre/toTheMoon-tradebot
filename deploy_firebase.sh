#!/bin/bash

# Script de déploiement avec Firebase Integration
# Pour VPS Ubuntu/Debian

echo "🚀 Déploiement Bot Trading avec Firebase Integration"
echo "================================================="

# Mise à jour du système
echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation Python et pip si nécessaire
echo "🐍 Vérification Python..."
if ! command -v python3 &> /dev/null; then
    sudo apt install python3 python3-pip python3-venv -y
fi

# Navigation vers le répertoire du bot
cd /home/$(whoami)/toTheMoon_tradebot || exit 1

# Sauvegarde des configurations existantes
echo "💾 Sauvegarde des configurations..."
cp config.py config.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Activation de l'environnement virtuel
echo "🔧 Configuration environnement virtuel..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Installation des dépendances avec Firebase
echo "📚 Installation des dépendances (avec Firebase)..."
pip install --upgrade pip
pip install -r requirements.txt

# Installation spécifique Firebase Admin SDK
echo "🔥 Installation Firebase Admin SDK..."
pip install firebase-admin==6.4.0

# Vérification des fichiers critiques
echo "✅ Vérification des fichiers..."
if [ ! -f "main.py" ]; then
    echo "❌ main.py manquant!"
    exit 1
fi

if [ ! -f "utils/firebase_logger.py" ]; then
    echo "❌ firebase_logger.py manquant!"
    exit 1
fi

if [ ! -f "utils/firebase_config.py" ]; then
    echo "❌ firebase_config.py manquant!"
    exit 1
fi

# Configuration Firebase
echo "🔥 Configuration Firebase..."
if [ ! -f "firebase_env.txt" ]; then
    echo "⚠️  Fichier firebase_env.txt manquant!"
    echo "📋 Copiez firebase_env_template.txt vers firebase_env.txt"
    echo "📝 Puis remplissez vos clés Firebase"
    cp firebase_env_template.txt firebase_env.txt
    echo "❌ Configurez Firebase avant de continuer!"
    exit 1
fi

# Chargement des variables Firebase dans .env
echo "📝 Intégration configuration Firebase..."
if [ -f "firebase_env.txt" ]; then
    cat firebase_env.txt >> .env
    echo "✅ Variables Firebase ajoutées à .env"
fi

# Vérification syntaxe Python
echo "🔍 Vérification syntaxe Python..."
python3 -m py_compile main.py
python3 -m py_compile utils/firebase_logger.py
python3 -m py_compile utils/firebase_config.py

if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python valide"
else
    echo "❌ Erreurs de syntaxe détectées!"
    exit 1
fi

# Test de connexion Firebase (optionnel)
echo "🧪 Test de connexion Firebase..."
python3 -c "
try:
    from utils.firebase_logger import firebase_logger
    firebase_logger.test_firebase_connection()
    print('✅ Connexion Firebase OK')
except Exception as e:
    print(f'⚠️  Test Firebase échoué: {e}')
    print('ℹ️  Le bot peut fonctionner sans Firebase')
"

# Configuration du service systemd (optionnel)
echo "⚙️  Configuration service systemd..."
sudo tee /etc/systemd/system/toTheMoon-bot.service > /dev/null <<EOF
[Unit]
Description=toTheMoon Trading Bot with Firebase
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=/home/$(whoami)/toTheMoon_tradebot
Environment=PATH=/home/$(whoami)/toTheMoon_tradebot/venv/bin
ExecStart=/home/$(whoami)/toTheMoon_tradebot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable toTheMoon-bot.service

echo ""
echo "🎉 Déploiement terminé avec succès!"
echo "=================================="
echo ""
echo "📋 Prochaines étapes:"
echo "1. ✅ Vérifiez votre configuration .env"
echo "2. 🔥 Configurez firebase_env.txt avec vos clés Firebase"
echo "3. 🧪 Testez le bot: python3 main.py"
echo "4. 🚀 Démarrez le service: sudo systemctl start toTheMoon-bot"
echo "5. 📊 Consultez les logs: sudo journalctl -u toTheMoon-bot -f"
echo ""
echo "🔥 Analytics Firebase disponibles en temps réel!"
echo "📈 Accédez à vos données depuis Firebase Console"
echo ""
