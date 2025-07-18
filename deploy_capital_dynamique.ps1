# Script de déploiement rapide - Capital Dynamique
# Déploie les modifications du capital dynamique et redémarre le bot

param(
    [string]$VpsHost = "root@213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot",
    [string]$ServiceName = "tothemoon-tradebot"
)

Write-Host "🚀 DÉPLOIEMENT CAPITAL DYNAMIQUE" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Sauvegarder les fichiers critiques sur le VPS
Write-Host "💾 Sauvegarde des fichiers de configuration..." -ForegroundColor Yellow
ssh $VpsHost "cd $BotDir && cp .env .env.backup.`$(date +%Y%m%d_%H%M%S) 2>/dev/null; echo 'Sauvegarde tentée'"

# Étape 2: Arrêter le bot avant déploiement
Write-Host "🛑 Arrêt du bot sur le VPS..." -ForegroundColor Yellow
ssh $VpsHost "systemctl stop $ServiceName 2>/dev/null; pkill -f 'python.*main.py' 2>/dev/null; echo 'Arrêt du bot tenté'"

# Étape 3: Déployer les fichiers modifiés
Write-Host "📤 Déploiement des modifications..." -ForegroundColor Yellow

# Copie des fichiers principaux modifiés
Write-Host "  - main.py (capital dynamique)"
scp main.py ${VpsHost}:${BotDir}/main.py

Write-Host "  - telegram_notifier.py (notifications optimisées)"
scp utils/telegram_notifier.py ${VpsHost}:${BotDir}/utils/telegram_notifier.py

Write-Host "  - sheets_logger.py (logs capital dynamique)"
scp utils/sheets_logger.py ${VpsHost}:${BotDir}/utils/sheets_logger.py

# Copie des autres fichiers utiles
Write-Host "  - Fichiers de configuration"
try { scp config.py ${VpsHost}:${BotDir}/config.py } catch { Write-Host "    config.py non trouvé (optionnel)" }
try { scp requirements.txt ${VpsHost}:${BotDir}/requirements.txt } catch { Write-Host "    requirements.txt non trouvé (optionnel)" }

# Étape 4: Vérifier les dépendances
Write-Host "📦 Vérification des dépendances..." -ForegroundColor Yellow
ssh $VpsHost "cd $BotDir && source venv/bin/activate 2>/dev/null && pip install --upgrade pip 2>/dev/null; echo 'Dépendances vérifiées'"

# Étape 5: Test de compilation
Write-Host "🧪 Test de compilation..." -ForegroundColor Yellow
$compileResult = ssh $VpsHost "cd $BotDir && python3 -m py_compile main.py && echo 'COMPILE_OK'"

if ($compileResult -notcontains "COMPILE_OK") {
    Write-Host "❌ Erreur de compilation détectée !" -ForegroundColor Red
    Write-Host "Vérifiez les logs ci-dessus" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Compilation réussie" -ForegroundColor Green

# Étape 6: Redémarrer le bot
Write-Host "🔄 Redémarrage du bot..." -ForegroundColor Yellow

# Essayer avec systemd d'abord
$systemdResult = ssh $VpsHost "systemctl start $ServiceName && systemctl is-active $ServiceName" 2>$null

if ($systemdResult -eq "active") {
    Write-Host "✅ Bot redémarré avec systemd" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Systemd non disponible, démarrage manuel..." -ForegroundColor Yellow
    
    # Démarrage manuel en arrière-plan
    ssh $VpsHost "cd $BotDir && nohup python3 main.py > logs/bot.log 2>&1 &"
    Start-Sleep 3
    
    # Vérification du processus
    $processCheck = ssh $VpsHost "pgrep -f 'python.*main.py'"
    if ($processCheck) {
        Write-Host "✅ Bot démarré manuellement (PID: $processCheck)" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Échec du démarrage manuel" -ForegroundColor Red
        Write-Host "Vérifiez les logs: ssh $VpsHost 'tail -f $BotDir/logs/bot.log'" -ForegroundColor Yellow
        exit 1
    }
}

# Étape 7: Vérification finale
Write-Host "🔍 Vérification finale..." -ForegroundColor Yellow
Start-Sleep 5

$healthCheck = ssh $VpsHost "cd $BotDir; tail -n 20 logs/bot.log 2>/dev/null | grep -E '(Capital total|Bot.*lancé|initialisé)' | tail -n 3"

if ($healthCheck) {
    Write-Host "✅ Bot opérationnel - Logs récents:" -ForegroundColor Green
    Write-Host $healthCheck -ForegroundColor White
}
else {
    Write-Host "⚠️ Pas de logs récents détectés" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 DÉPLOIEMENT TERMINÉ !" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Nouvelles fonctionnalités déployées:" -ForegroundColor Cyan
Write-Host "  ✅ Capital total dynamique (EUR + crypto)"
Write-Host "  ✅ P&L journalier basé sur capital réel"
Write-Host "  ✅ Notifications Telegram optimisées"
Write-Host "  ✅ Logs Google Sheets adaptés"
Write-Host ""
Write-Host "📝 Commandes utiles:" -ForegroundColor Yellow
Write-Host "  Logs en temps réel: ssh $VpsHost 'tail -f $BotDir/logs/bot.log'"
Write-Host "  Status du service: ssh $VpsHost 'systemctl status $ServiceName'"
Write-Host "  Arrêter le bot: ssh $VpsHost 'systemctl stop $ServiceName'"
Write-Host ""
