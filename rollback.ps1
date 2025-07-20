# Script de Rollback Ultra Simple
param(
    [string]$VpsHost = "213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot"
)

Write-Host "ROLLBACK ULTRA SIMPLE" -ForegroundColor Red
Write-Host "====================" -ForegroundColor Red
Write-Host "Date: $(Get-Date)" -ForegroundColor Blue
Write-Host ""

# 1. Lister les backups disponibles
Write-Host "1. Backups disponibles:" -ForegroundColor Yellow
$backups = ssh root@$VpsHost "ls -la /root/backups/ | grep backup_ | tail -10"
Write-Host $backups -ForegroundColor Cyan

# 2. Choisir le dernier backup automatiquement
$lastBackup = ssh root@$VpsHost "ls -1t /root/backups/ | grep backup_ | head -1"
if ($lastBackup) {
    Write-Host "2. Backup le plus recent: $lastBackup" -ForegroundColor Green
    
    # 3. Arreter le bot
    Write-Host "3. Arret du bot..." -ForegroundColor Yellow
    ssh root@$VpsHost "systemctl stop toTheMoon_tradebot 2>/dev/null"
    
    # 4. Restaurer le backup
    Write-Host "4. Restauration du backup..." -ForegroundColor Cyan
    ssh root@$VpsHost "rm -rf $BotDir"
    ssh root@$VpsHost "cp -r /root/backups/$lastBackup $BotDir"
    
    # 5. Redemarrer
    Write-Host "5. Redemarrage..." -ForegroundColor Green
    ssh root@$VpsHost "systemctl start toTheMoon_tradebot"
    Start-Sleep 3
    
    # 6. Verification
    Start-Sleep 3
    $serviceStatus = ssh root@$VpsHost "systemctl is-active toTheMoon_tradebot"
    if ($serviceStatus -eq "active") {
        $processId = ssh root@$VpsHost "systemctl show --property MainPID toTheMoon_tradebot | cut -d= -f2"
        Write-Host "6. ROLLBACK REUSSI! Service actif (PID: $processId)" -ForegroundColor Green
    }
    else {
        Write-Host "6. Probleme - verifiez manuellement" -ForegroundColor Red
    }
}
else {
    Write-Host "Aucun backup trouve!" -ForegroundColor Red
}

Write-Host ""
Write-Host "ROLLBACK TERMINE" -ForegroundColor Green
Write-Host "Commandes utiles:" -ForegroundColor Cyan
Write-Host "  Logs: ssh root@$VpsHost 'tail -f $BotDir/logs/bot.log'"
Write-Host "  Connexion: ssh root@$VpsHost"
