Write-Host "Dashboard Demo ToTheMoon" -ForegroundColor Green

if (-not (Test-Path "sample_data.json")) {
    python generate_sample_data.py
}

Write-Host "Demarrage sur http://localhost:8504" -ForegroundColor Cyan

echo "" | python -m streamlit run dashboard_demo.py --server.port 8504
