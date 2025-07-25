#!/bin/bash
# Script de déploiement automatique VPS via SSH
# Les fichiers .env et firebase_credentials.json sont déjà sur le VPS

set -e

# Configuration
VPS_HOST="root@213.199.41.168"
VPS_PROJECT_DIR="/opt/toTheMoon_tradebot"
LOCAL_PROJECT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🚀 DÉPLOIEMENT AUTOMATIQUE VPS BINANCE PROXY"
echo "=============================================="
echo "VPS: $VPS_HOST"
echo "Projet local: $LOCAL_PROJECT_DIR"
echo ""

# 1. Test de connexion SSH
log_info "Test de connexion SSH..."
if ssh -o ConnectTimeout=10 "$VPS_HOST" "echo 'Connexion SSH OK'" > /dev/null 2>&1; then
    log_success "Connexion SSH établie"
else
    log_error "Impossible de se connecter au VPS"
    exit 1
fi

# 2. Copie des fichiers sources (sans .env et firebase_credentials.json)
log_info "Copie des fichiers sources vers le VPS..."

# Créer les répertoires
ssh "$VPS_HOST" "mkdir -p $VPS_PROJECT_DIR/{utils,scripts,logs}"

# Copier les fichiers Python
scp -q "$LOCAL_PROJECT_DIR/utils/binance_proxy_service.py" "$VPS_HOST:$VPS_PROJECT_DIR/utils/"
scp -q "$LOCAL_PROJECT_DIR/scripts/start_binance_proxy.py" "$VPS_HOST:$VPS_PROJECT_DIR/scripts/"
scp -q "$LOCAL_PROJECT_DIR/scripts/test_usdc_discovery.py" "$VPS_HOST:$VPS_PROJECT_DIR/scripts/"
scp -q "$LOCAL_PROJECT_DIR/scripts/validate_vps_deployment.py" "$VPS_HOST:$VPS_PROJECT_DIR/scripts/"
scp -q "$LOCAL_PROJECT_DIR/requirements.txt" "$VPS_HOST:$VPS_PROJECT_DIR/"

# Copier le script de déploiement (version VPS)
scp -q "$LOCAL_PROJECT_DIR/scripts/deploy_vps_proxy.sh" "$VPS_HOST:$VPS_PROJECT_DIR/scripts/"

log_success "Fichiers copiés vers le VPS"

# 3. Vérification des fichiers de configuration existants
log_info "Vérification des fichiers de configuration sur le VPS..."
ssh "$VPS_HOST" "
if [ -f '$VPS_PROJECT_DIR/.env' ] && [ -f '$VPS_PROJECT_DIR/firebase_credentials.json' ]; then
    echo '✅ Fichiers de configuration trouvés'
else
    echo '❌ Fichiers .env ou firebase_credentials.json manquants'
    exit 1
fi
"

# 4. Modification du script de déploiement pour ignorer la vérification interactive
log_info "Adaptation du script de déploiement pour mode automatique..."
ssh "$VPS_HOST" "
# Modifier le script pour ignorer les vérifications interactives
sed -i 's/read -p.*Appuyez sur Entrée.*/echo \"Fichiers de configuration déjà présents\"/' '$VPS_PROJECT_DIR/scripts/deploy_vps_proxy.sh'
chmod +x '$VPS_PROJECT_DIR/scripts/deploy_vps_proxy.sh'
"

# 5. Exécution du déploiement automatique
log_info "Lancement du déploiement automatique sur le VPS..."
ssh "$VPS_HOST" "cd $VPS_PROJECT_DIR && ./scripts/deploy_vps_proxy.sh"

# 6. Validation du déploiement
log_info "Validation du déploiement..."
ssh "$VPS_HOST" "cd $VPS_PROJECT_DIR && python3 scripts/validate_vps_deployment.py"

# 7. Affichage du statut final
echo ""
log_success "🎉 DÉPLOIEMENT VPS TERMINÉ AVEC SUCCÈS!"
echo ""
echo "📊 Statut du service:"
ssh "$VPS_HOST" "systemctl status binance-proxy --no-pager || true"

echo ""
echo "📋 Commandes de monitoring:"
echo "  ssh $VPS_HOST 'journalctl -u binance-proxy -f'"
echo "  ssh $VPS_HOST 'systemctl status binance-proxy'"
echo ""
echo "🔗 Prochaine étape:"
echo "  Lancer 'streamlit run monitor_realtime.py' en local pour voir les données VPS"
echo ""
