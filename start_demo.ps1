# Lancement simple du dashboard demo
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

Write-Host "🚀 Lancement du dashboard ToTheMoon en mode DEMO..." -ForegroundColor Green

# Vérifier que les données de test existent
if (-not (Test-Path "sample_data.json")) {
    Write-Host "📊 Génération des données de test..." -ForegroundColor Yellow
    python generate_sample_data.py
}

Write-Host "📱 Démarrage du dashboard..." -ForegroundColor Cyan
Write-Host "🌐 URL: http://localhost:8504" -ForegroundColor Green

# Lancer directement avec echo pour passer l'email
echo "" | python -m streamlit run dashboard_demo.py --server.port 8504 --browser.gatherUsageStats false
