# Script de déploiement automatique VPS - Version PowerShell
# Lance le déploiement sur le VPS sans intervention manuelle

# Configuration
$VPS_HOST = "root@213.199.41.168"
$VPS_PROJECT_DIR = "/opt/toTheMoon_tradebot"

Write-Host "🚀 DÉPLOIEMENT AUTOMATIQUE VPS BINANCE PROXY" -ForegroundColor Blue
Write-Host "=============================================" -ForegroundColor Blue

# Étape 1: Copie des fichiers
Write-Host "📁 Copie des fichiers vers le VPS..." -ForegroundColor Cyan

# Créer le répertoire sur le VPS
ssh $VPS_HOST "mkdir -p $VPS_PROJECT_DIR"

# Copier les fichiers essentiels (utiliser scp avec des chemins Windows)
scp -r utils/ scripts/ requirements.txt monitor_realtime.py "${VPS_HOST}:${VPS_PROJECT_DIR}/"

Write-Host "✅ Fichiers copiés avec succès" -ForegroundColor Green

# Étape 2: Lancer le déploiement
Write-Host "🔧 Lancement du déploiement sur le VPS..." -ForegroundColor Cyan

ssh $VPS_HOST "cd $VPS_PROJECT_DIR && chmod +x scripts/deploy_vps_proxy.sh && ./scripts/deploy_vps_proxy.sh"

# Étape 3: Validation
Write-Host "🔍 Validation du déploiement..." -ForegroundColor Cyan

ssh $VPS_HOST "systemctl status binance-proxy --no-pager"

# Étape 4: Test final
Write-Host "🧪 Test final de fonctionnement..." -ForegroundColor Cyan

ssh $VPS_HOST "cd $VPS_PROJECT_DIR && python3 scripts/test_usdc_discovery.py"

Write-Host ""
Write-Host "🎉 DÉPLOIEMENT VPS TERMINÉ AVEC SUCCÈS!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Commandes de monitoring à distance:"
Write-Host "  ssh $VPS_HOST 'systemctl status binance-proxy'"
Write-Host "  ssh $VPS_HOST 'journalctl -u binance-proxy -f'"
Write-Host ""
Write-Host "🎯 Prochaine étape:"
Write-Host "  Lancer monitor_realtime.py en local pour voir les données VPS"
Write-Host ""
