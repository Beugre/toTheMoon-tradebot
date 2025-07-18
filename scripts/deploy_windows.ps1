# Script PowerShell pour déployer le bot sur VPS
# Exécuter avec: powershell -ExecutionPolicy Bypass -File deploy_windows.ps1

param(
    [string]$VpsHost = "root@213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot"
)

Write-Host "DEPLOIEMENT DU BOT TOTHEMOON SUR VPS" -ForegroundColor Blue
Write-Host "====================================" -ForegroundColor Blue
Write-Host ""

# Vérification des prérequis
Write-Host "🔍 Vérification des prérequis..." -ForegroundColor Yellow

# Vérification de SSH
try {
    ssh -o ConnectTimeout=10 $VpsHost "echo 'SSH OK'" | Out-Null
    Write-Host "Connexion SSH OK" -ForegroundColor Green
}
catch {
    Write-Host "❌ Erreur de connexion SSH" -ForegroundColor Red
    Write-Host "Vérifiez que SSH est installé et que les clés sont configurées" -ForegroundColor Red
    exit 1
}

# Vérification de SCP/RSYNC
if (!(Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "❌ SCP non trouvé. Installez OpenSSH ou Git for Windows" -ForegroundColor Red
    exit 1
}

Write-Host "Prérequis OK" -ForegroundColor Green
Write-Host ""

# Désactivation de l'ancien bot
Write-Host "Désactivation de l'ancien bot..." -ForegroundColor Yellow
$disableScript = Get-Content "scripts\disable_old_bot.sh" -Raw
ssh $VpsHost $disableScript

# Création du répertoire
Write-Host ""
Write-Host "📁 Préparation du répertoire..." -ForegroundColor Yellow
ssh $VpsHost "rm -rf $BotDir && mkdir -p $BotDir"

# Copie des fichiers (en excluant les fichiers inutiles)
Write-Host ""
Write-Host "📤 Copie des fichiers..." -ForegroundColor Yellow

$excludeFiles = @(
    "--exclude=.git",
    "--exclude=__pycache__",
    "--exclude=*.pyc",
    "--exclude=.vscode",
    "--exclude=logs/",
    "--exclude=data/",
    "--exclude=.env"
)

if (Get-Command rsync -ErrorAction SilentlyContinue) {
    # Utilisation de rsync si disponible
    $rsyncArgs = @("-avz", "--progress") + $excludeFiles + @("./", "$VpsHost`:$BotDir/")
    & rsync @rsyncArgs
}
else {
    # Fallback avec scp
    Write-Host "⚠️ Rsync non trouvé, utilisation de scp (plus lent)" -ForegroundColor Yellow
    scp -r * "${VpsHost}:${BotDir}/"
}

Write-Host "Fichiers copiés" -ForegroundColor Green

# Installation sur le VPS
Write-Host ""
Write-Host "📦 Installation des dépendances sur le VPS..." -ForegroundColor Yellow

$installScript = @"
cd $BotDir

# Mise à jour
apt update -y
apt install -y python3 python3-pip python3-venv build-essential wget curl

# Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Dépendances Python
pip install --upgrade pip
pip install -r requirements.txt

# TA-Lib
if [ ! -f "/usr/local/lib/libta_lib.so" ]; then
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr/local
    make && make install
    cd ..
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
    ldconfig
fi

pip install TA-Lib

# Tests
python3 -c "import talib; print(\"TA-Lib OK\")"
python3 -c "import ccxt, binance; print(\"Trading libs OK\")"

# Permissions
chmod +x run.py investor_report.py scripts/*.sh

echo "Installation terminée"
"@

ssh $VpsHost $installScript

# Configuration systemd
Write-Host ""
Write-Host "Configuration du service systemd..." -ForegroundColor Yellow

$systemdScript = @"
cd $BotDir
cp scripts/tothemoon-tradebot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable tothemoon-tradebot
echo "Service systemd configuré"
"@

ssh $VpsHost $systemdScript

# Instructions finales
Write-Host ""
Write-Host "🎉 DÉPLOIEMENT TERMINÉ !" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host ""
Write-Host "PROCHAINES ÉTAPES :" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Configurez le fichier .env :" -ForegroundColor White
Write-Host "   ssh $VpsHost" -ForegroundColor Cyan
Write-Host "   cd $BotDir" -ForegroundColor Cyan
Write-Host "   nano .env" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Testez la configuration :" -ForegroundColor White
Write-Host "   source venv/bin/activate" -ForegroundColor Cyan
Write-Host "   python3 run.py --test" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Démarrez le service :" -ForegroundColor White
Write-Host "   systemctl start tothemoon-tradebot" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Vérifiez les logs :" -ForegroundColor White
Write-Host "   journalctl -u tothemoon-tradebot -f" -ForegroundColor Cyan
Write-Host ""
Write-Host "Le bot est prêt !" -ForegroundColor Green
