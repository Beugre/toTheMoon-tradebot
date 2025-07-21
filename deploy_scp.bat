@echo off
REM Script de déploiement SCP simple pour ToTheMoon Trading Bot
REM Usage: deploy_scp.bat

echo 🚀 Déploiement SCP ToTheMoon Trading Bot
echo =======================================

set VPS_HOST=root@213.199.41.168
set BOT_DIR=/opt/toTheMoon_tradebot
set SERVICE_NAME=toTheMoon-bot

echo 📋 Configuration:
echo    🖥️  VPS: %VPS_HOST%
echo    📁 Répertoire: %BOT_DIR%
echo    ⚙️  Service: %SERVICE_NAME%
echo.

REM 1. Arrêt du service
echo 🛑 Arrêt du service...
ssh %VPS_HOST% "systemctl stop %SERVICE_NAME%"
if %ERRORLEVEL% neq 0 (
    echo ⚠️ Erreur arrêt service - continuons...
)
echo.

REM 2. Copie du fichier principal modifié
echo 📤 Copie de main.py...
scp main.py %VPS_HOST%:%BOT_DIR%/main.py
if %ERRORLEVEL% neq 0 (
    echo ❌ Erreur copie main.py
    exit /b 1
)

REM 3. Copie du fichier de configuration technique indicators
echo 📤 Copie de utils/technical_indicators.py...
scp utils/technical_indicators.py %VPS_HOST%:%BOT_DIR%/utils/technical_indicators.py
if %ERRORLEVEL% neq 0 (
    echo ⚠️ Erreur copie technical_indicators.py - continuons...
)

REM 4. Copie des tests de validation
echo 📤 Copie des tests...
scp test_dust_trades_fix.py %VPS_HOST%:%BOT_DIR%/test_dust_trades_fix.py
if %ERRORLEVEL% neq 0 (
    echo ⚠️ Erreur copie test - continuons...
)

scp test_simple_dust.py %VPS_HOST%:%BOT_DIR%/test_simple_dust.py
if %ERRORLEVEL% neq 0 (
    echo ⚠️ Erreur copie test simple - continuons...
)

REM 5. Copie de la documentation mise à jour
echo 📤 Copie de la documentation...
scp docs/commandes_utiles.md %VPS_HOST%:%BOT_DIR%/docs/commandes_utiles.md
if %ERRORLEVEL% neq 0 (
    echo ⚠️ Erreur copie documentation - continuons...
)

REM 6. Copie du fichier service si nécessaire
echo 📤 Copie du service systemd...
scp toTheMoon-bot.service %VPS_HOST%:/etc/systemd/system/toTheMoon-bot.service
if %ERRORLEVEL% neq 0 (
    echo ⚠️ Erreur copie service - continuons...
)

REM 7. Redémarrage du service
echo 🔄 Rechargement systemd et redémarrage du service...
ssh %VPS_HOST% "systemctl daemon-reload && systemctl start %SERVICE_NAME%"
if %ERRORLEVEL% neq 0 (
    echo ❌ Erreur redémarrage service
    exit /b 1
)

REM 8. Vérification du statut
echo 📊 Vérification du statut...
ssh %VPS_HOST% "systemctl status %SERVICE_NAME% --no-pager -l"

echo.
echo ✅ Déploiement terminé !
echo 💡 Pour surveiller les logs: ssh %VPS_HOST% "journalctl -u %SERVICE_NAME% -f"
echo 💡 Pour vérifier le service: ssh %VPS_HOST% "systemctl status %SERVICE_NAME%"
echo.

pause
