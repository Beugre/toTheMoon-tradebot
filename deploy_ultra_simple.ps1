# Deploy Ultra Simple - Sans problemes d'encodage
param(
    [string]$VpsHost = "213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot",
    [string]$ServiceName = "toTheMoon-bot"
)

Write-Host "DEPLOIEMENT ULTRA SIMPLE" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host "Date: $(Get-Date)" -ForegroundColor Blue
Write-Host ""

# 1. Push vers GitHub
Write-Host "1. Push vers GitHub..." -ForegroundColor Yellow
git add .
git commit -m "Deploy-$(Get-Date -Format 'yyyyMMdd-HHmm')" -ErrorAction SilentlyContinue
git push origin main
Write-Host "   Push termine" -ForegroundColor Green

# 2. Verification et installation des prérequis sur VPS
Write-Host "2. Verification prerequis VPS..." -ForegroundColor Cyan
Write-Host "   Installation git, python3..." -ForegroundColor Yellow
ssh root@$VpsHost "apt update >/dev/null 2>&1"
ssh root@$VpsHost "apt install -y git python3 python3-pip python3-venv >/dev/null 2>&1"
Write-Host "   Prerequisites installes" -ForegroundColor Green

# 3. Backup sur VPS
Write-Host "3. Backup sur VPS..." -ForegroundColor Cyan
$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
ssh root@$VpsHost "mkdir -p /root/backups"
ssh root@$VpsHost "cp -r $BotDir /root/backups/backup_$backupDate 2>/dev/null"
Write-Host "   Backup termine" -ForegroundColor Green

# 4. Verification et arret de tous les bots
Write-Host "4. Verification des processus existants..." -ForegroundColor Yellow
$existingProcesses = ssh root@$VpsHost "pgrep -f 'python.*main.py' | wc -l"
if ($existingProcesses -gt 0) {
    Write-Host "   $existingProcesses processus bot detectes - arret en cours..." -ForegroundColor Yellow
    ssh root@$VpsHost "systemctl stop $ServiceName 2>/dev/null"
    ssh root@$VpsHost "pkill -f python.*main.py 2>/dev/null"
    Start-Sleep 2
    
    # Double verification
    $remainingProcesses = ssh root@$VpsHost "pgrep -f 'python.*main.py' | wc -l"
    if ($remainingProcesses -gt 0) {
        Write-Host "   Force kill des processus restants..." -ForegroundColor Red
        ssh root@$VpsHost "pkill -9 -f python.*main.py 2>/dev/null"
        Start-Sleep 1
    }
    
    # Verification finale
    $finalCheck = ssh root@$VpsHost "pgrep -f 'python.*main.py' | wc -l"
    if ($finalCheck -eq 0) {
        Write-Host "   Tous les bots arretes avec succes" -ForegroundColor Green
    }
    else {
        Write-Host "   ATTENTION: $finalCheck processus encore actifs!" -ForegroundColor Red
        $stillRunning = ssh root@$VpsHost "ps aux | grep 'python.*main.py' | grep -v grep"
        Write-Host "   Processus actifs: $stillRunning" -ForegroundColor Yellow
    }
}
else {
    Write-Host "   Aucun bot en cours d'execution" -ForegroundColor Green
}

# 5. Clone ou pull du repository
Write-Host "5. Mise a jour du code..." -ForegroundColor Cyan
$repoExists = ssh root@$VpsHost "test -d $BotDir/.git && echo 'exists'"
if ($repoExists -eq "exists") {
    Write-Host "   Git pull..." -ForegroundColor Yellow
    ssh root@$VpsHost "cd $BotDir; git stash; git pull origin main"
}
else {
    Write-Host "   Clone initial..." -ForegroundColor Yellow
    ssh root@$VpsHost "rm -rf $BotDir"
    ssh root@$VpsHost "git clone https://github.com/Beugre/toTheMoon-tradebot.git $BotDir"
}
Write-Host "   Code mis a jour" -ForegroundColor Green

# 6. Installation des dependances Python
Write-Host "6. Installation dependances..." -ForegroundColor Cyan
ssh root@$VpsHost "cd $BotDir; python3 -m pip install -r requirements.txt >/dev/null 2>&1"
ssh root@$VpsHost "mkdir -p $BotDir/logs"

# 7. Creation du service systemd si necessaire
Write-Host "7. Configuration service systemd..." -ForegroundColor Yellow
ssh root@$VpsHost "if [ ! -f /etc/systemd/system/$ServiceName.service ]; then cat > /etc/systemd/system/$ServiceName.service << 'EOF'
[Unit]
Description=toTheMoon Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BotDir
ExecStart=/usr/bin/python3 $BotDir/main.py
Restart=always
RestartSec=10
StandardOutput=file:$BotDir/logs/bot.log
StandardError=file:$BotDir/logs/bot.log

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable $ServiceName
echo 'Service systemd cree et active'
else
echo 'Service systemd deja present'
fi"

# 8. Redemarrage avec systemd
Write-Host "8. Demarrage avec systemd..." -ForegroundColor Green
ssh root@$VpsHost "systemctl restart $ServiceName"
Start-Sleep 3

# 9. Verification unicite du bot
Write-Host "9. Verification unicite..." -ForegroundColor Yellow
$botProcesses = ssh root@$VpsHost "pgrep -f 'python.*main.py' | wc -l"
$systemdStatus = ssh root@$VpsHost "systemctl is-active $ServiceName"

Write-Host "   Processus python detectes: $botProcesses" -ForegroundColor Cyan
Write-Host "   Status systemd: $systemdStatus" -ForegroundColor Cyan

if ($botProcesses -eq 1 -and $systemdStatus -eq "active") {
    Write-Host "   PARFAIT - Un seul bot actif!" -ForegroundColor Green
    $pid = ssh root@$VpsHost "pgrep -f 'python.*main.py'"
    Write-Host "   PID du bot: $pid" -ForegroundColor Green
}
elseif ($botProcesses -gt 1) {
    Write-Host "   ALERTE - $botProcesses bots detectes! (Doublon)" -ForegroundColor Red
    $allProcesses = ssh root@$VpsHost "ps aux | grep 'python.*main.py' | grep -v grep"
    Write-Host "   Processus multiples:" -ForegroundColor Yellow
    Write-Host "   $allProcesses" -ForegroundColor White
}
elseif ($botProcesses -eq 0) {
    Write-Host "   ECHEC - Aucun bot actif" -ForegroundColor Red
}
else {
    Write-Host "   Status incertain - verification manuelle requise" -ForegroundColor Yellow
}

# 9. Verification
Write-Host "9. Verification..." -ForegroundColor Yellow
$status = ssh root@$VpsHost "systemctl is-active $ServiceName"
if ($status -eq "active") {
    Write-Host "   SUCCES - Bot actif avec systemd!" -ForegroundColor Green
    # Afficher le statut complet
    $serviceStatus = ssh root@$VpsHost "systemctl status $ServiceName --no-pager -l | head -10"
    Write-Host "   Status:" -ForegroundColor Cyan
    Write-Host "   $serviceStatus" -ForegroundColor White
}
else {
    Write-Host "   ECHEC - Service non actif" -ForegroundColor Red
    # Afficher les erreurs systemd
    $errors = ssh root@$VpsHost "journalctl -u $ServiceName --no-pager -n 10"
    if ($errors) {
        Write-Host "   Erreurs systemd:" -ForegroundColor Red
        Write-Host "   $errors" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "DEPLOIEMENT TERMINE" -ForegroundColor Green
Write-Host "Commandes utiles:" -ForegroundColor Cyan
Write-Host "  Logs: ssh root@$VpsHost 'journalctl -u $ServiceName -f'"
Write-Host "  Status: ssh root@$VpsHost 'systemctl status $ServiceName'"
Write-Host "  Restart: ssh root@$VpsHost 'systemctl restart $ServiceName'"
Write-Host "  Stop: ssh root@$VpsHost 'systemctl stop $ServiceName'"
Write-Host "  Connexion: ssh root@$VpsHost"
