# 🚀 ToTheMoon Trading Bot - Utilitaires de Gestion (Windows)

# Variables de configuration
$VPS_HOST = "root@213.199.41.168"
$BOT_DIR = "/opt/toTheMoon_tradebot"
$SERVICE_NAME = "tothemoon-tradebot"

function Show-Menu {
    Clear-Host
    Write-Host "🚀 ToTheMoon Trading Bot - Gestionnaire VPS" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 MONITORING & STATUT:" -ForegroundColor Yellow
    Write-Host "  1. Statut du service" -ForegroundColor White
    Write-Host "  2. Logs en temps réel" -ForegroundColor White
    Write-Host "  3. Logs des dernières 24h" -ForegroundColor White
    Write-Host "  4. Résumé complet du statut" -ForegroundColor White
    Write-Host ""
    Write-Host "⚙️ GESTION DU SERVICE:" -ForegroundColor Yellow
    Write-Host "  5. Démarrer le bot" -ForegroundColor White
    Write-Host "  6. Arrêter le bot" -ForegroundColor White
    Write-Host "  7. Redémarrer le bot" -ForegroundColor White
    Write-Host ""
    Write-Host "🗄️ BASE DE DONNÉES:" -ForegroundColor Yellow
    Write-Host "  8. Voir les derniers trades" -ForegroundColor White
    Write-Host "  9. Statistiques des trades" -ForegroundColor White
    Write-Host " 10. Performance du jour" -ForegroundColor White
    Write-Host " 11. Sauvegarder la base de données" -ForegroundColor White
    Write-Host ""
    Write-Host "🔄 DÉPLOIEMENT & MISE À JOUR:" -ForegroundColor Yellow
    Write-Host " 12. Déploiement complet" -ForegroundColor White
    Write-Host " 13. Mise à jour rapide du code" -ForegroundColor White
    Write-Host " 14. Test en mode dry-run" -ForegroundColor White
    Write-Host ""
    Write-Host "🚨 URGENCE:" -ForegroundColor Red
    Write-Host " 15. Arrêt d'urgence" -ForegroundColor Red
    Write-Host " 16. Fermer toutes les positions" -ForegroundColor Red
    Write-Host ""
    Write-Host " 17. Connexion SSH directe" -ForegroundColor Green
    Write-Host "  0. Quitter" -ForegroundColor Gray
    Write-Host ""
}

function Invoke-SSHCommand {
    param([string]$Command)
    ssh $VPS_HOST $Command
}

function Show-ServiceStatus {
    Write-Host "📊 Vérification du statut du service..." -ForegroundColor Yellow
    Invoke-SSHCommand "systemctl status $SERVICE_NAME"
}

function Show-RealtimeLogs {
    Write-Host "📊 Affichage des logs en temps réel (Ctrl+C pour arrêter)..." -ForegroundColor Yellow
    Invoke-SSHCommand "journalctl -u $SERVICE_NAME -f"
}

function Show-RecentLogs {
    Write-Host "📊 Logs des dernières 24h..." -ForegroundColor Yellow
    Invoke-SSHCommand "journalctl -u $SERVICE_NAME --since '24 hours ago'"
}

function Show-CompleteStatus {
    Write-Host "📊 Résumé complet du statut..." -ForegroundColor Yellow
    $statusCommand = @"
echo '🔍 STATUT DU BOT TOTHEMOON'
echo '========================='
echo '📊 Service:' `$(systemctl is-active $SERVICE_NAME)
echo '💾 Mémoire:' `$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -p `$(pgrep -f run.py) | tail -n +2)
echo '📁 Espace disque:' `$(df -h $BOT_DIR | tail -1 | awk '{print `$4\" disponible\"}')
echo '🕐 Uptime:' `$(systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp --value)
echo '📈 Dernière activité:'
journalctl -u $SERVICE_NAME -n 5 --no-pager
"@
    Invoke-SSHCommand $statusCommand
}

function Start-Bot {
    Write-Host "🚀 Démarrage du bot..." -ForegroundColor Green
    Invoke-SSHCommand "systemctl start $SERVICE_NAME"
    Write-Host "✅ Commande de démarrage envoyée" -ForegroundColor Green
}

function Stop-Bot {
    Write-Host "⏹️ Arrêt du bot..." -ForegroundColor Red
    Invoke-SSHCommand "systemctl stop $SERVICE_NAME"
    Write-Host "✅ Commande d'arrêt envoyée" -ForegroundColor Green
}

function Restart-Bot {
    Write-Host "🔄 Redémarrage du bot..." -ForegroundColor Yellow
    Invoke-SSHCommand "systemctl restart $SERVICE_NAME"
    Write-Host "✅ Commande de redémarrage envoyée" -ForegroundColor Green
}

function Show-RecentTrades {
    Write-Host "📈 Derniers trades..." -ForegroundColor Yellow
    $sqlCommand = "cd $BOT_DIR && sqlite3 trading_bot.db 'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;'"
    Invoke-SSHCommand $sqlCommand
}

function Show-TradeStats {
    Write-Host "📊 Statistiques des trades..." -ForegroundColor Yellow
    $sqlCommand = @"
cd $BOT_DIR && sqlite3 trading_bot.db '
SELECT symbol, COUNT(*) as nb_trades, 
       ROUND(AVG(profit_loss), 4) as avg_profit, 
       ROUND(SUM(profit_loss), 4) as total_profit
FROM trades 
WHERE profit_loss IS NOT NULL 
GROUP BY symbol;'
"@
    Invoke-SSHCommand $sqlCommand
}

function Show-TodayPerformance {
    Write-Host "📅 Performance du jour..." -ForegroundColor Yellow
    $sqlCommand = @"
cd $BOT_DIR && sqlite3 trading_bot.db '
SELECT symbol, side, quantity, price, profit_loss, timestamp 
FROM trades 
WHERE DATE(timestamp) = DATE(\"now\") 
ORDER BY timestamp DESC;'
"@
    Invoke-SSHCommand $sqlCommand
}

function Backup-Database {
    Write-Host "💾 Sauvegarde de la base de données..." -ForegroundColor Yellow
    $backupName = "trading_bot_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
    Invoke-SSHCommand "cd $BOT_DIR && cp trading_bot.db $backupName"
    
    # Téléchargement local
    Write-Host "📥 Téléchargement de la sauvegarde..." -ForegroundColor Yellow
    scp "${VPS_HOST}:${BOT_DIR}/${backupName}" "./backup/"
    Write-Host "✅ Sauvegarde créée : ./backup/$backupName" -ForegroundColor Green
}

function Deploy-Complete {
    Write-Host "🚀 Déploiement complet..." -ForegroundColor Cyan
    .\scripts\deploy_simple.ps1
}

function Update-Code {
    Write-Host "🔄 Mise à jour rapide du code..." -ForegroundColor Yellow
    
    # Copie des fichiers
    $rsyncCommand = @"
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.vscode' \
    --exclude='logs/' \
    --exclude='data/' \
    --exclude='.env' \
    ./ ${VPS_HOST}:${BOT_DIR}/
"@
    
    Invoke-Expression $rsyncCommand
    
    # Redémarrage du service
    Write-Host "🔄 Redémarrage du service..." -ForegroundColor Yellow
    Invoke-SSHCommand "systemctl restart $SERVICE_NAME"
    Write-Host "✅ Mise à jour terminée" -ForegroundColor Green
}

function Test-DryRun {
    Write-Host "🧪 Test en mode dry-run..." -ForegroundColor Cyan
    Invoke-SSHCommand "cd $BOT_DIR && source venv/bin/activate && python3 run.py --test"
}

function Emergency-Stop {
    Write-Host "🚨 ARRÊT D'URGENCE..." -ForegroundColor Red
    Invoke-SSHCommand "systemctl stop $SERVICE_NAME && pkill -f run.py"
    Write-Host "⚠️ Bot arrêté en urgence" -ForegroundColor Red
}

function Close-AllPositions {
    Write-Host "🚨 Fermeture de toutes les positions..." -ForegroundColor Red
    $closeCommand = "cd $BOT_DIR && source venv/bin/activate && python3 -c 'from main import ScalpingBot; bot = ScalpingBot(); bot.close_all_positions()'"
    Invoke-SSHCommand $closeCommand
}

function Connect-SSH {
    Write-Host "🔗 Connexion SSH directe..." -ForegroundColor Green
    ssh $VPS_HOST
}

# Créer le dossier backup s'il n'existe pas
if (-not (Test-Path "./backup")) {
    New-Item -ItemType Directory -Path "./backup" | Out-Null
}

# Boucle principale
do {
    Show-Menu
    $choice = Read-Host "Choisissez une option (0-17)"
    
    switch ($choice) {
        "1" { Show-ServiceStatus; Read-Host "Appuyez sur Entrée pour continuer" }
        "2" { Show-RealtimeLogs }
        "3" { Show-RecentLogs; Read-Host "Appuyez sur Entrée pour continuer" }
        "4" { Show-CompleteStatus; Read-Host "Appuyez sur Entrée pour continuer" }
        "5" { Start-Bot; Read-Host "Appuyez sur Entrée pour continuer" }
        "6" { Stop-Bot; Read-Host "Appuyez sur Entrée pour continuer" }
        "7" { Restart-Bot; Read-Host "Appuyez sur Entrée pour continuer" }
        "8" { Show-RecentTrades; Read-Host "Appuyez sur Entrée pour continuer" }
        "9" { Show-TradeStats; Read-Host "Appuyez sur Entrée pour continuer" }
        "10" { Show-TodayPerformance; Read-Host "Appuyez sur Entrée pour continuer" }
        "11" { Backup-Database; Read-Host "Appuyez sur Entrée pour continuer" }
        "12" { Deploy-Complete; Read-Host "Appuyez sur Entrée pour continuer" }
        "13" { Update-Code; Read-Host "Appuyez sur Entrée pour continuer" }
        "14" { Test-DryRun; Read-Host "Appuyez sur Entrée pour continuer" }
        "15" { Emergency-Stop; Read-Host "Appuyez sur Entrée pour continuer" }
        "16" { Close-AllPositions; Read-Host "Appuyez sur Entrée pour continuer" }
        "17" { Connect-SSH }
        "0" { Write-Host "Au revoir ! 👋" -ForegroundColor Green }
        default { Write-Host "Option invalide !" -ForegroundColor Red; Read-Host "Appuyez sur Entrée pour continuer" }
    }
} while ($choice -ne "0")
