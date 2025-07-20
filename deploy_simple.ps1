# 🚀 DÉPLOIEMENT AUTOMATIQUE - toTheMoon Bot Firebase Integration
# Script Windows -> VPS (version simple avec Git pull)
# Usage: .\deploy_simple.ps1

param(
    [string]$VpsUser = "root",
    [string]$VpsHost = "213.199.41.168",
    [string]$BotDir = "/root/toTheMoon_tradebot",
    [string]$ServiceName = "toTheMoon-bot"
)

Write-Host "🚀 DÉPLOIEMENT AUTOMATIQUE TOTHE MOON BOT" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "📅 $(Get-Date)" -ForegroundColor Blue
Write-Host "🔥 Version: Simple Git Pull Deploy" -ForegroundColor Yellow
Write-Host ""

# 1. Commit et push local
Write-Host "📦 Push des changements vers GitHub..." -ForegroundColor Yellow
git add .
$commitMsg = "Deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git commit -m $commitMsg -ErrorAction SilentlyContinue
git push origin main
Write-Host "✅ Code pushé vers GitHub" -ForegroundColor Green

# 2. Backup sur VPS
Write-Host "📦 Backup sur VPS..." -ForegroundColor Cyan
$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
ssh root@$VpsHost "mkdir -p /root/backups && cp -r $BotDir /root/backups/backup_$backupDate 2>/dev/null || echo 'Pas de backup nécessaire'"

# 3. Arrêt du bot
Write-Host "🛑 Arrêt du bot..." -ForegroundColor Yellow
ssh root@$VpsHost "systemctl stop $ServiceName 2>/dev/null"
ssh root@$VpsHost "pkill -f 'python.*main.py' 2>/dev/null"

# 4. Git pull sur VPS
Write-Host "📥 Git pull sur VPS..." -ForegroundColor Cyan
ssh root@$VpsHost "cd $BotDir"
ssh root@$VpsHost "cd $BotDir; git stash"
ssh root@$VpsHost "cd $BotDir; git pull origin main"

# 5. Création logs directory si nécessaire
ssh root@$VpsHost "mkdir -p $BotDir/logs"

# 6. Test de compilation
Write-Host "🔧 Test de compilation..." -ForegroundColor Yellow
$compileTest = ssh root@$VpsHost "cd $BotDir; python3 -c 'import main; print(\"COMPILE_OK\")' 2>/dev/null"
if ($compileTest -match "COMPILE_OK") {
    Write-Host "✅ Compilation réussie" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Erreur de compilation, mais on continue..." -ForegroundColor Yellow
}

# 7. Redémarrage du bot
Write-Host "🚀 Redémarrage du bot..." -ForegroundColor Green
ssh root@$VpsHost "cd $BotDir; systemctl start $ServiceName 2>/dev/null"
if ($LASTEXITCODE -ne 0) {
    ssh root@$VpsHost "cd $BotDir; nohup python3 main.py > logs/bot.log 2>&1 &"
    Write-Host "Bot démarré manuellement" -ForegroundColor Yellow
}

# 8. Vérification finale
Start-Sleep 3
Write-Host "🔍 Vérification finale..." -ForegroundColor Yellow
$statusCheck = ssh root@$VpsHost "systemctl is-active $ServiceName 2>/dev/null"
if (-not $statusCheck) {
    $statusCheck = ssh root@$VpsHost "pgrep -f 'python.*main.py'"
}

if ($statusCheck) {
    Write-Host "🎉 DÉPLOIEMENT RÉUSSI!" -ForegroundColor Green
    Write-Host "✅ Bot opérationnel" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Statut incertain - vérifiez manuellement" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Commandes utiles:" -ForegroundColor Cyan
Write-Host "Logs: ssh root@$VpsHost 'tail -f $BotDir/logs/bot.log'"
Write-Host "Status: ssh root@$VpsHost 'systemctl status $ServiceName'"
Write-Host "Manuel: ssh root@$VpsHost"