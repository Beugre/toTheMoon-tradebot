# Script de déploiement VPS avec bon requirements
param(
    [string]$VpsHost = "213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot"
)

Write-Host "🚀 DEPLOIEMENT BOT VPS" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

# Push code
Write-Host "📤 Push vers GitHub..." -ForegroundColor Yellow
git add .
git commit -m "Update bot - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ErrorAction SilentlyContinue
git push origin main

# Déploiement sur VPS
Write-Host "🔄 Déploiement sur VPS..." -ForegroundColor Cyan

# Script de déploiement distant avec bon requirements
$deployScript = @"
#!/bin/bash
echo "🔄 Mise à jour du bot..."

# Aller dans le dossier du bot
cd $BotDir

# Arrêter le service
sudo systemctl stop toTheMoon-bot

# Pull latest
git pull origin main

# Activer l'environnement conda
source /opt/miniconda/etc/profile.d/conda.sh
conda activate trading

# Installer les dépendances BOT (pas dashboard)
pip install -r requirements_bot_production.txt

# Redémarrer le service
sudo systemctl start toTheMoon-bot
sudo systemctl status toTheMoon-bot --no-pager

echo "✅ Déploiement terminé!"
"@

# Exécuter le script sur le VPS
echo $deployScript | ssh root@$VpsHost "cat > /tmp/deploy_bot.sh && chmod +x /tmp/deploy_bot.sh && /tmp/deploy_bot.sh"

Write-Host "✅ Déploiement VPS terminé!" -ForegroundColor Green
