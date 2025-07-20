# Script de deploiement rapide - Bot v3.0 Enhanced Edition + Notifications Horaires
param(
    [string]$VpsHost = "root@213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot",
    [string]$ServiceName = "tothemoon-tradebot"
)

Write-Host "Deploiement Bot v3.0 Enhanced Edition + Notifications Horaires" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Etape 1: Arreter le bot
Write-Host "Arret du bot..." -ForegroundColor Yellow
ssh $VpsHost "systemctl stop $ServiceName 2>/dev/null; pkill -f 'python.*main.py' 2>/dev/null; echo 'Bot arrete'"

# Etape 2: Deployer les fichiers modifies
Write-Host "Deploiement des fichiers..." -ForegroundColor Yellow
scp config.py ${VpsHost}:${BotDir}/config.py
scp main.py ${VpsHost}:${BotDir}/main.py
scp utils/risk_manager.py ${VpsHost}:${BotDir}/utils/risk_manager.py
scp utils/telegram_notifier.py ${VpsHost}:${BotDir}/utils/telegram_notifier.py
scp utils/enhanced_sheets_logger.py ${VpsHost}:${BotDir}/utils/enhanced_sheets_logger.py
scp utils/trading_hours_notifier.py ${VpsHost}:${BotDir}/utils/trading_hours_notifier.py
scp trading_hours.py ${VpsHost}:${BotDir}/trading_hours.py

# Deploiement des scripts de test (optionnel)
Write-Host "Deploiement des scripts de test..." -ForegroundColor Yellow
ssh $VpsHost "mkdir -p ${BotDir}/patches"
scp patches/test_notifications_horaires.py ${VpsHost}:${BotDir}/patches/test_notifications_horaires.py
scp patches/integration_notifications_guide.py ${VpsHost}:${BotDir}/patches/integration_notifications_guide.py

# Etape 3: Test de compilation
Write-Host "Test de compilation..." -ForegroundColor Yellow
$compileResult = ssh $VpsHost "cd $BotDir; python3 -m py_compile main.py && echo 'COMPILE_OK'"

if ($compileResult -notcontains "COMPILE_OK") {
    Write-Host "Erreur de compilation!" -ForegroundColor Red
    exit 1
}

Write-Host "Compilation reussie" -ForegroundColor Green

# Etape 4: Redemarrer le bot
Write-Host "Redemarrage du bot..." -ForegroundColor Yellow

# Essayer systemd d'abord
$systemdResult = ssh $VpsHost "systemctl start $ServiceName 2>/dev/null && systemctl is-active $ServiceName 2>/dev/null"

if ($systemdResult -eq "active") {
    Write-Host "Bot redemarre avec systemd" -ForegroundColor Green
}
else {
    Write-Host "Demarrage manuel..." -ForegroundColor Yellow
    ssh $VpsHost "cd $BotDir; nohup python3 main.py > logs/bot.log 2>&1 &"
    Start-Sleep 3
    
    $processCheck = ssh $VpsHost "pgrep -f 'python.*main.py'"
    if ($processCheck) {
        Write-Host "Bot demarre manuellement (PID: $processCheck)" -ForegroundColor Green
    }
    else {
        Write-Host "Echec du demarrage" -ForegroundColor Red
        exit 1
    }
}

# Etape 5: Verification
Write-Host "Verification..." -ForegroundColor Yellow
Start-Sleep 5

$healthCheck = ssh $VpsHost "cd $BotDir; tail -n 10 logs/bot.log 2>/dev/null | tail -n 3"

if ($healthCheck) {
    Write-Host "Bot operationnel - Logs:" -ForegroundColor Green
    Write-Host $healthCheck -ForegroundColor White
}

Write-Host ""
Write-Host "DEPLOIEMENT TERMINE!" -ForegroundColor Green
Write-Host "Nouvelles fonctionnalites Bot v3.0 Enhanced Edition:" -ForegroundColor Cyan
Write-Host "- 🌅 Notifications horaires automatiques avec emojis fun"
Write-Host "- 🍽️ Alertes lunch time et power hour US"
Write-Host "- 📊 Notifications volatilite adaptatives"
Write-Host "- 🔥 Messages motivants selon sessions de marche"
Write-Host "- 💰 Migration USDC pour liquidite 26x superieure"
Write-Host "- 🛡️ BNB burn desactive (economie 1,824€/mois)"
Write-Host "- 📈 TP optimise a 1.2% pour meilleur risk/reward"
Write-Host "- ⏰ Trading hours 9h-23h avec intensite adaptative"
Write-Host "- 📋 Enhanced Google Sheets avec calculs automatiques"
Write-Host "- 🚫 Anti-fragmentation et gestion intelligente positions"
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "Logs: ssh $VpsHost 'tail -f $BotDir/logs/bot.log'"
Write-Host "Status: ssh $VpsHost 'systemctl status $ServiceName'"
Write-Host "Test notifications: ssh $VpsHost 'cd $BotDir && python3 patches/test_notifications_horaires.py'"
Write-Host "Verification integration: ssh $VpsHost 'cd $BotDir && python3 patches/integration_notifications_guide.py'"
