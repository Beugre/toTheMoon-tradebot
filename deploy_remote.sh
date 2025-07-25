#!/bin/bash
# Script de déploiement automatique complet via SSH
# Lance le déploiement sur le VPS sans intervention manuelle

set -e

# Configuration
VPS_HOST="root@213.199.41.168"
VPS_PROJECT_DIR="/opt/toTheMoon_tradebot"
LOCAL_PROJECT_DIR="."

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

echo "🚀 DÉPLOIEMENT AUTOMATIQUE VPS BINANCE PROXY"
echo "============================================="

# Étape 1: Copie des fichiers
log_info "Copie des fichiers vers le VPS..."

# Copier seulement les fichiers modifiés
scp utils/binance_proxy_service.py $VPS_HOST:$VPS_PROJECT_DIR/utils/
scp -r scripts/ $VPS_HOST:$VPS_PROJECT_DIR/

log_success "Fichiers copiés avec succès"

# Étape 2: Rendre le script exécutable et lancer le déploiement
log_info "Lancement du déploiement sur le VPS..."

ssh $VPS_HOST "cd $VPS_PROJECT_DIR && chmod +x scripts/deploy_vps_proxy.sh && ./scripts/deploy_vps_proxy.sh"

# Étape 3: Validation du déploiement
log_info "Validation du déploiement..."

ssh $VPS_HOST "systemctl status binance-proxy --no-pager"

# Étape 4: Test final
log_info "Test final de fonctionnement..."

ssh $VPS_HOST "cd $VPS_PROJECT_DIR && python3 scripts/test_usdc_discovery.py"

echo ""
log_success "🎉 DÉPLOIEMENT VPS TERMINÉ AVEC SUCCÈS!"
echo ""
echo "📋 Commandes de monitoring à distance:"
echo "  ssh $VPS_HOST 'systemctl status binance-proxy'"
echo "  ssh $VPS_HOST 'journalctl -u binance-proxy -f'"
echo ""
echo "🎯 Prochaine étape:"
echo "  Lancer monitor_realtime.py en local pour voir les données VPS"
echo ""
