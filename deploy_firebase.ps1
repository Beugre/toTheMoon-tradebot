# Script de déploiement Firebase pour Windows
# PowerShell script pour configuration locale

Write-Host "🚀 Configuration Bot Trading avec Firebase Integration" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# Vérification Python
Write-Host "🐍 Vérification Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python non trouvé! Installez Python 3.8+" -ForegroundColor Red
    exit 1
}

# Navigation vers le répertoire
$botPath = "C:\dev\toTheMoon_tradebot"
if (-not (Test-Path $botPath)) {
    Write-Host "❌ Répertoire $botPath non trouvé!" -ForegroundColor Red
    exit 1
}

Set-Location $botPath

# Création environnement virtuel si nécessaire
Write-Host "🔧 Configuration environnement virtuel..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activation environnement virtuel
Write-Host "📦 Activation environnement virtuel..." -ForegroundColor Yellow
& ".\venv\Scripts\activate.ps1"

# Installation des dépendances
Write-Host "📚 Installation des dépendances (avec Firebase)..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Installation Firebase Admin SDK
Write-Host "🔥 Installation Firebase Admin SDK..." -ForegroundColor Yellow
python -m pip install firebase-admin==6.4.0

# Vérification des fichiers critiques
Write-Host "✅ Vérification des fichiers..." -ForegroundColor Yellow
$requiredFiles = @("main.py", "utils\firebase_logger.py", "utils\firebase_config.py")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Fichier manquant: $file" -ForegroundColor Red
        exit 1
    }
}

# Configuration Firebase
Write-Host "🔥 Configuration Firebase..." -ForegroundColor Yellow
if (-not (Test-Path "firebase_env.txt")) {
    Write-Host "⚠️  Fichier firebase_env.txt manquant!" -ForegroundColor Yellow
    Write-Host "📋 Création du fichier depuis template..." -ForegroundColor Yellow
    Copy-Item "firebase_env_template.txt" "firebase_env.txt"
    Write-Host "📝 Éditez firebase_env.txt avec vos clés Firebase!" -ForegroundColor Red
}

# Intégration variables Firebase dans .env
Write-Host "📝 Intégration configuration Firebase..." -ForegroundColor Yellow
if (Test-Path "firebase_env.txt") {
    Get-Content "firebase_env.txt" | Add-Content ".env"
    Write-Host "✅ Variables Firebase ajoutées à .env" -ForegroundColor Green
}

# Vérification syntaxe Python
Write-Host "🔍 Vérification syntaxe Python..." -ForegroundColor Yellow
python -m py_compile main.py
python -m py_compile utils\firebase_logger.py
python -m py_compile utils\firebase_config.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Syntaxe Python valide" -ForegroundColor Green
}
else {
    Write-Host "❌ Erreurs de syntaxe détectées!" -ForegroundColor Red
    exit 1
}

# Test connexion Firebase
Write-Host "🧪 Test de connexion Firebase..." -ForegroundColor Yellow
python -c "
try:
    from utils.firebase_logger import firebase_logger
    firebase_logger.test_firebase_connection()
    print('✅ Connexion Firebase OK')
except Exception as e:
    print(f'⚠️  Test Firebase échoué: {e}')
    print('ℹ️  Le bot peut fonctionner sans Firebase')
"

Write-Host ""
Write-Host "🎉 Configuration terminée avec succès!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Prochaines étapes:" -ForegroundColor Cyan
Write-Host "1. ✅ Vérifiez votre configuration .env" -ForegroundColor White
Write-Host "2. 🔥 Configurez firebase_env.txt avec vos clés Firebase" -ForegroundColor White
Write-Host "3. 🧪 Testez le bot: python main.py" -ForegroundColor White
Write-Host ""
Write-Host "🔥 Analytics Firebase disponibles en temps réel!" -ForegroundColor Yellow
Write-Host "📈 Accédez à vos données depuis Firebase Console" -ForegroundColor Yellow
Write-Host ""
