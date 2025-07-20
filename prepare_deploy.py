"""
Script de déploiement pour Streamlit Cloud
Prépare le repo pour le déploiement
"""

import os
import json
import subprocess

def prepare_deployment():
    """Prépare le déploiement Streamlit Cloud"""
    
    print("🚀 Préparation du déploiement Streamlit Cloud")
    print("=" * 50)
    
    # Vérifier que les credentials Firebase existent
    if os.path.exists("firebase_credentials.json"):
        print("✅ Credentials Firebase trouvés")
        
        # Lire et formater pour Streamlit secrets
        with open("firebase_credentials.json", 'r') as f:
            firebase_creds = json.load(f)
        
        print("\n📋 Configuration pour Streamlit Cloud Secrets:")
        print("Copiez cette configuration dans la section 'Secrets' de Streamlit Cloud:")
        print("-" * 60)
        print("[firebase]")
        for key, value in firebase_creds.items():
            if key == "private_key":
                # Formater la clé privée correctement
                print(f'{key} = """"{value}""""')
            else:
                print(f'{key} = "{value}"')
        print("-" * 60)
        
    else:
        print("❌ firebase_credentials.json non trouvé")
        print("   Ajoutez vos credentials Firebase avant le déploiement")
        return False
    
    # Vérifier que .gitignore protège les secrets
    if os.path.exists(".gitignore"):
        with open(".gitignore", 'r') as f:
            gitignore_content = f.read()
        
        if "firebase_credentials.json" in gitignore_content:
            print("✅ .gitignore protège les credentials")
        else:
            print("⚠️  Ajoutez firebase_credentials.json au .gitignore")
    
    # Vérifier les dépendances
    if os.path.exists("requirements_dashboard.txt"):
        print("✅ requirements_dashboard.txt trouvé")
    else:
        print("❌ requirements_dashboard.txt manquant")
    
    print("\n🌐 Étapes suivantes pour déployer:")
    print("1. Allez sur https://share.streamlit.io")
    print("2. Connectez votre repo GitHub")
    print("3. Sélectionnez 'dashboard.py' comme fichier principal")
    print("4. Ajoutez la configuration Firebase dans les Secrets")
    print("5. Déployez !")
    
    return True

if __name__ == "__main__":
    prepare_deployment()
