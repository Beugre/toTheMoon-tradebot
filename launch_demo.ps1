# Script pour lancer le dashboard en mode demo avec configuration automatique
param(
    [int]$Port = 8501
)

Write-Host "Lancement du dashboard ToTheMoon en mode DEMO..." -ForegroundColor Green

# Verifier que les donnees de test existent
if (-not (Test-Path "sample_data.json")) {
    Write-Host "Generation des donnees de test..." -ForegroundColor Yellow
    python generate_sample_data.py
}

# Creer un fichier de configuration temporaire pour eviter l'email prompt
$configDir = "$env:USERPROFILE\.streamlit"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$configContent = @"
[global]
showWarningOnDirectExecution = false

[browser]
gatherUsageStats = false

[server]
port = $Port
"@

$configPath = Join-Path $configDir "config.toml"
$configContent | Out-File -FilePath $configPath -Encoding UTF8

Write-Host "Demarrage du dashboard sur le port $Port..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:$Port" -ForegroundColor Green

# Lancer Streamlit
python -m streamlit run dashboard_demo.py --server.port $Port

Write-Host "Dashboard ferme." -ForegroundColor Green
