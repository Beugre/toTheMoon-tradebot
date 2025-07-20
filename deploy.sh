#!/bin/bash

# Script de Déploiement Simplifié - toTheMoon Bot
# Usage: ./deploy.sh

set -e  # Arrêt en cas d'erreur

echo "🚀 DÉPLOIEMENT TOTHE MOON BOT - Firebase Integration"
echo "=================================================="
echo "📅 $(date)"
echo ""

# Variables
BOT_DIR="/home/$(whoami)/toTheMoon_tradebot"
SERVICE_NAME="toTheMoon-bot"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Arrêt du service existant
print_step "Arrêt du service bot..."
if systemctl is-active --quiet $SERVICE_NAME; then
    sudo systemctl stop $SERVICE_NAME
    print_success "Service arrêté"
else
    print_warning "Service non actif"
fi

# 2. Sauvegarde de la configuration
print_step "Sauvegarde de la configuration..."
cd $BOT_DIR
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp firebase_credentials.json firebase_credentials.json.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
print_success "Configuration sauvegardée"

# 3. Récupération des dernières modifications
print_step "Mise à jour du code..."
git stash push -m "Auto-stash before deploy $(date)" 2>/dev/null || true
git pull origin main
print_success "Code mis à jour"

# 4. Installation/mise à jour des dépendances
print_step "Mise à jour des dépendances..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dépendances installées"

# 5. Installation Firebase si nécessaire
print_step "Vérification Firebase..."
if ! pip show firebase-admin > /dev/null 2>&1; then
    pip install firebase-admin==6.4.0
    print_success "Firebase Admin SDK installé"
else
    print_success "Firebase Admin SDK déjà installé"
fi

# 6. Vérification de la configuration
print_step "Vérification de la configuration..."

# Variables critiques
if [ ! -f ".env" ]; then
    print_error "Fichier .env manquant!"
    exit 1
fi

if [ ! -f "firebase_credentials.json" ]; then
    print_warning "Fichier firebase_credentials.json manquant - Firebase désactivé"
else
    print_success "Configuration Firebase OK"
fi

# 7. Test de syntaxe
print_step "Vérification syntaxe..."
python3 -m py_compile main.py
python3 -m py_compile utils/firebase_logger.py
python3 -m py_compile utils/firebase_config.py
print_success "Syntaxe Python valide"

# 8. Test de non-régression
print_step "Test de non-régression..."
if python3 test_non_regression_simple.py > /dev/null 2>&1; then
    print_success "Tests de non-régression réussis"
else
    print_warning "Tests échoués - vérifiez la configuration"
fi

# 9. Configuration du service systemd
print_step "Configuration du service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=toTheMoon Trading Bot with Firebase Analytics
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
print_success "Service configuré"

# 10. Démarrage du service
print_step "Démarrage du bot..."
sudo systemctl start $SERVICE_NAME

# Attente et vérification
sleep 5
if systemctl is-active --quiet $SERVICE_NAME; then
    print_success "Bot démarré avec succès!"
else
    print_error "Échec du démarrage - consultez les logs"
    echo "📊 Logs récents:"
    sudo journalctl -u $SERVICE_NAME --no-pager -n 20
    exit 1
fi

# 11. Résumé du déploiement
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!${NC}"
echo "=================================================="
echo ""
echo "📊 Status du bot:"
sudo systemctl status $SERVICE_NAME --no-pager -l

echo ""
echo "🔧 Commandes utiles:"
echo "   📊 Status:        sudo systemctl status $SERVICE_NAME"
echo "   📋 Logs temps réel: sudo journalctl -u $SERVICE_NAME -f"
echo "   🛑 Arrêt:         sudo systemctl stop $SERVICE_NAME"
echo "   🚀 Redémarrage:   sudo systemctl restart $SERVICE_NAME"
echo ""
echo "🔥 Nouvelles fonctionnalités:"
echo "   📈 Firebase Analytics en temps réel"
echo "   🧹 Gestion intelligente des miettes"
echo "   📊 API Google Sheets robuste"
echo "   💰 Métriques live du capital"
echo ""
echo -e "${BLUE}🌍 Accédez à Firebase Console pour voir vos données en temps réel!${NC}"
echo ""
