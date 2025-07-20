#!/bin/bash
# Script de lancement du dashboard Streamlit

echo "🚀 Lancement du Dashboard ToTheMoon Bot"
echo "========================================"

# Vérifier si streamlit est installé
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installation des dépendances..."
    pip install -r requirements_dashboard.txt
fi

# Vérifier si les credentials Firebase existent
if [ ! -f "firebase_credentials.json" ]; then
    echo "❌ Erreur: firebase_credentials.json non trouvé"
    echo "💡 Copiez votre fichier de credentials Firebase dans ce répertoire"
    exit 1
fi

echo "✅ Prérequis OK"
echo "🌐 Lancement du dashboard sur http://localhost:8501"
echo "🔄 Utilisez Ctrl+C pour arrêter"

# Lancer Streamlit
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
