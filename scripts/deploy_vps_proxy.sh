#!/bin/bash
# Script de déploiement du service Binance Proxy sur VPS
# Automatise l'installation et la configuration complète

set -e  # Arrêt sur erreur

echo "🚀 DÉPLOIEMENT SERVICE BINANCE PROXY VPS"
echo "=========================================="

# Variables
PROJECT_DIR="/opt/toTheMoon_tradebot"
SERVICE_NAME="binance-proxy"
PYTHON_ENV="/opt/toTheMoon_tradebot/venv"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérification des permissions root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté en tant que root"
        exit 1
    fi
    log_success "Permissions root confirmées"
}

# Installation des dépendances système
install_system_deps() {
    log_info "Installation des dépendances système..."
    
    apt update
    apt install -y python3 python3-pip python3-venv git htop curl
    
    log_success "Dépendances système installées"
}

# Création de l'environnement Python
setup_python_env() {
    log_info "Configuration environnement Python..."
    
    # Créer l'environnement virtuel
    if [ ! -d "$PYTHON_ENV" ]; then
        python3 -m venv "$PYTHON_ENV"
        log_success "Environnement virtuel créé"
    else
        log_info "Environnement virtuel existe déjà"
    fi
    
    # Activer et installer les packages
    source "$PYTHON_ENV/bin/activate"
    pip install --upgrade pip
    
    # Installation des packages requis
    pip install python-binance firebase-admin python-dotenv asyncio
    
    log_success "Packages Python installés"
}

# Création des répertoires nécessaires
create_directories() {
    log_info "Création des répertoires..."
    
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/utils"
    mkdir -p "$PROJECT_DIR/scripts"
    
    # Permissions
    chown -R root:root "$PROJECT_DIR"
    chmod -R 755 "$PROJECT_DIR"
    chmod -R 777 "$PROJECT_DIR/logs"  # Logs en écriture libre
    
    log_success "Répertoires créés et configurés"
}

# Vérification des fichiers de configuration
check_config_files() {
    log_info "Vérification des fichiers de configuration..."
    
    # Vérifier .env
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_warning "Fichier .env manquant"
        echo "Créez le fichier $PROJECT_DIR/.env avec:"
        echo "BINANCE_API_KEY=your_api_key"
        echo "BINANCE_SECRET_KEY=your_secret_key"
        read -p "Appuyez sur Entrée quand c'est fait..."
    fi
    
    # Vérifier firebase_credentials.json
    if [ ! -f "$PROJECT_DIR/firebase_credentials.json" ]; then
        log_warning "Fichier firebase_credentials.json manquant"
        echo "Copiez votre fichier Firebase credentials dans $PROJECT_DIR/"
        read -p "Appuyez sur Entrée quand c'est fait..."
    fi
    
    log_success "Fichiers de configuration vérifiés"
}

# Installation du service systemd
install_systemd_service() {
    log_info "Installation du service systemd..."
    
    # Créer le fichier service
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Binance Proxy Service for Trading Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PYTHON_ENV}/bin/python ${PROJECT_DIR}/scripts/start_binance_proxy.py --daemon
Restart=always
RestartSec=10
Environment=PYTHONPATH=${PROJECT_DIR}

[Install]
WantedBy=multi-user.target
EOF
    
    # Recharger systemd
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    log_success "Service systemd installé et activé"
}

# Test du service
test_service() {
    log_info "Test de la configuration..."
    
    # Test avec l'environnement Python
    source "$PYTHON_ENV/bin/activate"
    cd "$PROJECT_DIR"
    
    # Test d'importation des modules
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from utils.binance_proxy_service import BinanceProxyService
print('✅ Import modules OK')
"
    
    log_success "Configuration testée avec succès"
}

# Démarrage du service
start_service() {
    log_info "Démarrage du service..."
    
    systemctl start "$SERVICE_NAME"
    sleep 3
    
    # Vérifier le statut
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Service démarré avec succès"
        systemctl status "$SERVICE_NAME" --no-pager
    else
        log_error "Échec démarrage du service"
        systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

# Affichage des informations finales
show_final_info() {
    echo ""
    echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
    echo "=================================="
    echo ""
    echo "📋 Commandes utiles:"
    echo "  Status service:    systemctl status $SERVICE_NAME"
    echo "  Logs temps réel:   journalctl -u $SERVICE_NAME -f"
    echo "  Redémarrer:        systemctl restart $SERVICE_NAME"
    echo "  Arrêter:           systemctl stop $SERVICE_NAME"
    echo ""
    echo "📁 Fichiers importants:"
    echo "  Logs service:      $PROJECT_DIR/logs/binance_proxy.log"
    echo "  Logs manager:      $PROJECT_DIR/logs/proxy_manager.log"
    echo "  Configuration:     $PROJECT_DIR/.env"
    echo ""
    echo "🔍 Monitoring:"
    echo "  Vérifiez Firebase collection 'binance_live'"
    echo "  Le service collecte toutes les 60 secondes"
    echo ""
}

# Fonction principale
main() {
    echo "Démarrage du déploiement..."
    
    check_root
    install_system_deps
    create_directories
    setup_python_env
    check_config_files
    install_systemd_service
    test_service
    start_service
    show_final_info
    
    log_success "Déploiement terminé! 🚀"
}

# Exécution
main "$@"
