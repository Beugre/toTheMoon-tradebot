# Script de synchronisation Windows -> VPS
# Usage: .\sync_to_vps.ps1

param(
    [string]$VpsUser = "root",
    [string]$VpsHost = "your-vps-ip"
)

Write-Host "🔄 SYNCHRONISATION VERS VPS" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

$localPath = "C:\dev\toTheMoon_tradebot"
$remotePath = "/home/$VpsUser/toTheMoon_tradebot"

# Vérification des prérequis
if (-not (Test-Path $localPath)) {
    Write-Host "❌ Répertoire local non trouvé: $localPath" -ForegroundColor Red
    exit 1
}

# 1. Commit local
Write-Host "📦 Commit des changements locaux..." -ForegroundColor Yellow
Set-Location $localPath
git add .
git commit -m "Auto-commit avant sync $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ErrorAction SilentlyContinue
git push origin main

# 2. Connexion et mise à jour VPS
Write-Host "🌐 Connexion au VPS: $VpsUser@$VpsHost" -ForegroundColor Yellow
$sshCommands = @"
cd $remotePath
echo '📥 Récupération des changements...'
git pull origin main
echo '🔄 Redémarrage du bot...'
sudo systemctl restart toTheMoon-bot
sleep 3
echo '✅ Status du bot:'
sudo systemctl status toTheMoon-bot --no-pager -l | head -10
"@

ssh "$VpsUser@$VpsHost" $sshCommands

Write-Host "🎉 Synchronisation terminée!" -ForegroundColor Green
Write-Host "📋 Pour voir les logs: ssh $VpsUser@$VpsHost 'sudo journalctl -u toTheMoon-bot -f'" -ForegroundColor Cyan
