# Script de deploiement rapide - Capital Dynamique
param(
    [string]$VpsHost = "root@213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot",
    [string]$ServiceName = "tothemoon-tradebot"
)

Write-Host "Deploiement Capital Dynamique" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Etape 1: Arreter le bot
Write-Host "Arret du bot..." -ForegroundColor Yellow
ssh $VpsHost "systemctl stop $ServiceName 2>/dev/null; pkill -f 'python.*main.py' 2>/dev/null; echo 'Bot arrete'"

# Etape 2: Deployer les fichiers modifies
Write-Host "Deploiement des fichiers..." -ForegroundColor Yellow
scp main.py ${VpsHost}:${BotDir}/main.py
scp utils/telegram_notifier.py ${VpsHost}:${BotDir}/utils/telegram_notifier.py
scp utils/sheets_logger.py ${VpsHost}:${BotDir}/utils/sheets_logger.py

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
} else {
    Write-Host "Demarrage manuel..." -ForegroundColor Yellow
    ssh $VpsHost "cd $BotDir; nohup python3 main.py > logs/bot.log 2>&1 &"
    Start-Sleep 3
    
    $processCheck = ssh $VpsHost "pgrep -f 'python.*main.py'"
    if ($processCheck) {
        Write-Host "Bot demarre manuellement (PID: $processCheck)" -ForegroundColor Green
    } else {
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
Write-Host "Nouvelles fonctionnalites:" -ForegroundColor Cyan
Write-Host "- Capital total dynamique (EUR + crypto)"
Write-Host "- P&L journalier base sur capital reel"
Write-Host "- Notifications Telegram optimisees"
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "Logs: ssh $VpsHost 'tail -f $BotDir/logs/bot.log'"
Write-Host "Status: ssh $VpsHost 'systemctl status $ServiceName'"
