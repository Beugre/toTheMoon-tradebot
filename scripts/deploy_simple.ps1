# Script de deploiement simplifie pour VPS
param(
    [string]$VpsHost = "root@213.199.41.168",
    [string]$BotDir = "/opt/toTheMoon_tradebot",
    [string]$ServiceName = "tothemoon-tradebot"
)

Write-Host "DEPLOIEMENT DU BOT TOTHEMOON SUR VPS" -ForegroundColor Blue
Write-Host "=====================================" -ForegroundColor Blue

# Test connexion SSH
Write-Host "Test de la connexion SSH..." -ForegroundColor Yellow
try {
    ssh -o ConnectTimeout=10 $VpsHost "echo 'Test connexion OK'"
    Write-Host "Connexion SSH OK" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de se connecter au VPS" -ForegroundColor Red
    exit 1
}

# Copie des scripts restants
Write-Host "Copie des scripts..." -ForegroundColor Yellow
scp -r scripts/ $VpsHost`:$BotDir/

# Copie du fichier .env
Write-Host "Copie du fichier .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    scp .env $VpsHost`:$BotDir/
    Write-Host "Fichier .env copie" -ForegroundColor Green
} else {
    Write-Host "ATTENTION: Fichier .env non trouve" -ForegroundColor Yellow
}

# Copie du fichier credentials.json
Write-Host "Copie du fichier credentials.json..." -ForegroundColor Yellow
if (Test-Path "credentials.json") {
    scp credentials.json $VpsHost`:$BotDir/
    Write-Host "Fichier credentials.json copie" -ForegroundColor Green
} else {
    Write-Host "ATTENTION: Fichier credentials.json non trouve" -ForegroundColor Yellow
}

# Installation des dependances sur le VPS
Write-Host "Installation des dependances sur le VPS..." -ForegroundColor Yellow
$installScript = @"
cd $BotDir

# Mise a jour du systeme
apt update -y

# Installation de Python et outils
apt install -y python3 python3-pip python3-venv build-essential wget curl

# Creation de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Mise a jour de pip
pip install --upgrade pip

# Installation des dependances Python
pip install -r requirements.txt

# Installation de TA-Lib
echo "Installation de TA-Lib..."
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
python3 -c "import talib; print('TA-Lib OK')"
python3 -c "import ccxt, binance; print('Trading libs OK')"

# Permissions
chmod +x run.py investor_report.py scripts/*.sh

echo "Installation terminee"
"@

ssh $VpsHost $installScript

# Configuration systemd
Write-Host "Configuration du service systemd..." -ForegroundColor Yellow
$systemdScript = @"
cd $BotDir
cp scripts/tothemoon-tradebot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $ServiceName
echo "Service systemd configure"
"@

ssh $VpsHost $systemdScript

Write-Host ""
Write-Host "DEPLOIEMENT TERMINE !" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host ""
Write-Host "PROCHAINES ETAPES :" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Verifiez la configuration :" -ForegroundColor White
Write-Host "   ssh $VpsHost" -ForegroundColor Cyan
Write-Host "   cd $BotDir" -ForegroundColor Cyan
Write-Host "   nano .env" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Testez la configuration :" -ForegroundColor White
Write-Host "   source venv/bin/activate" -ForegroundColor Cyan
Write-Host "   python3 run.py --test" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Demarrez le service :" -ForegroundColor White
Write-Host "   systemctl start $ServiceName" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Verifiez les logs :" -ForegroundColor White
Write-Host "   journalctl -u $ServiceName -f" -ForegroundColor Cyan
Write-Host ""
Write-Host "COMMANDES UTILES :" -ForegroundColor Yellow
Write-Host "   systemctl status $ServiceName    # Statut" -ForegroundColor Cyan
Write-Host "   systemctl restart $ServiceName   # Redemarrage" -ForegroundColor Cyan
Write-Host "   systemctl stop $ServiceName      # Arret" -ForegroundColor Cyan
Write-Host ""
Write-Host "Le bot est pret !" -ForegroundColor Green
