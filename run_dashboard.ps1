# Script de lancement du dashboard Streamlit pour Windows
param(
    [int]$Port = 8501
)

Write-Host "🚀 Lancement du Dashboard ToTheMoon Bot" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Vérifier si streamlit est installé
try {
    streamlit --version | Out-Null
    Write-Host "✅ Streamlit détecté" -ForegroundColor Green
}
catch {
    Write-Host "📦 Installation des dépendances..." -ForegroundColor Yellow
    pip install -r requirements_dashboard.txt
}

# Vérifier si les credentials Firebase existent
if (-not (Test-Path "firebase_credentials.json")) {
    Write-Host "❌ Erreur: firebase_credentials.json non trouvé" -ForegroundColor Red
    Write-Host "💡 Copiez votre fichier de credentials Firebase dans ce répertoire" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Prérequis OK" -ForegroundColor Green
Write-Host "🌐 Lancement du dashboard sur http://localhost:$Port" -ForegroundColor Cyan
Write-Host "🔄 Utilisez Ctrl+C pour arrêter" -ForegroundColor Yellow

# Lancer Streamlit
streamlit run dashboard.py --server.port $Port --server.address 0.0.0.0
