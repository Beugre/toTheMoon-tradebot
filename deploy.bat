@echo off
echo.
echo ======================================================
echo   DEPLOIEMENT TOTHEMOON TRADING BOT SUR VPS
echo ======================================================
echo.

REM Vérification de PowerShell
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: PowerShell n'est pas trouve ou installe
    echo Installez PowerShell pour continuer
    pause
    exit /b 1
)

echo Lancement du script de deploiement PowerShell...
echo.

REM Exécution du script PowerShell
powershell -ExecutionPolicy Bypass -File "scripts\deploy_windows.ps1"

echo.
echo ======================================================
echo   DEPLOIEMENT TERMINE
echo ======================================================
echo.
echo Prochaines etapes:
echo 1. Configurez le fichier .env sur le VPS
echo 2. Testez la configuration
echo 3. Demarrez le service systemd
echo.
echo Commandes utiles:
echo   ssh root@213.199.41.168
echo   systemctl status tothemoon-tradebot
echo   journalctl -u tothemoon-tradebot -f
echo.
pause
