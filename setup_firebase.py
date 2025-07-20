"""
Script d'assistance pour la configuration Firebase
Aide à vérifier et configurer Firebase pour le bot de trading
"""

import json
import os
import sys
from pathlib import Path


def check_firebase_setup():
    """Vérifie la configuration Firebase"""
    print("🔥 Vérification de la configuration Firebase...")
    print("=" * 50)
    
    # Vérifier les variables d'environnement
    env_vars = [
        "FIREBASE_DATABASE_URL",
        "FIREBASE_PROJECT_ID", 
        "FIREBASE_CREDENTIALS"
    ]
    
    missing_vars = []
    for var in env_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            if var == "FIREBASE_CREDENTIALS":
                print(f"✅ {var}: {value}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ Variables d'environnement manquantes:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    # Vérifier le fichier de credentials
    cred_path = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")
    if not os.path.exists(cred_path):
        print(f"\n❌ Fichier credentials manquant: {cred_path}")
        return False
    
    # Vérifier le contenu du fichier credentials
    try:
        with open(cred_path, 'r') as f:
            creds = json.load(f)
            required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
            missing_fields = [field for field in required_fields if field not in creds]
            
            if missing_fields:
                print(f"❌ Champs manquants dans le fichier credentials: {missing_fields}")
                return False
            else:
                print(f"✅ Fichier credentials valide: {cred_path}")
                print(f"   Project ID: {creds.get('project_id')}")
                print(f"   Client Email: {creds.get('client_email')}")
    except Exception as e:
        print(f"❌ Erreur lecture credentials: {e}")
        return False
    
    print("\n🎉 Configuration Firebase complète !")
    return True

def show_setup_instructions():
    """Affiche les instructions de configuration"""
    print("\n📋 INSTRUCTIONS DE CONFIGURATION FIREBASE")
    print("=" * 50)
    print("""
1. 🌐 Créer un projet Firebase:
   - Allez sur https://console.firebase.google.com/
   - Cliquez "Ajouter un projet"
   - Donnez un nom (ex: tothemoon-tradebot)

2. 🗄️ Configurer les bases de données:
   - Activez "Firestore Database" (mode production)
   - Activez "Realtime Database" (mode verrouillé)
   - Choisissez une région proche de vous

3. 🔑 Générer les credentials:
   - Allez dans "Paramètres du projet" (⚙️)
   - Onglet "Comptes de service"
   - Cliquez "Générer une nouvelle clé privée"
   - Téléchargez le fichier JSON

4. 📁 Configurer le bot:
   - Placez le fichier JSON dans ce dossier
   - Renommez-le "firebase_credentials.json"
   - Copiez le fichier .env.firebase.template vers .env
   - Remplissez les valeurs dans .env

5. 🔗 URLs nécessaires:
   - Database URL: https://VOTRE-PROJET-default-rtdb.REGION.firebasedatabase.app/
   - Project ID: trouvable dans les paramètres du projet
    """)

def create_sample_env():
    """Crée un fichier .env d'exemple"""
    if os.path.exists('.env'):
        print("❌ Le fichier .env existe déjà")
        return
    
    sample_content = """# Configuration Firebase pour le Trading Bot
FIREBASE_DATABASE_URL=https://VOTRE-PROJET-default-rtdb.europe-west1.firebasedatabase.app/
FIREBASE_PROJECT_ID=votre-project-id
FIREBASE_CREDENTIALS=firebase_credentials.json
ENABLE_FIREBASE_LOGGING=True
ENABLE_TRADES_LOGGING=True
ENABLE_PERFORMANCE_LOGGING=True
"""
    
    with open('.env', 'w') as f:
        f.write(sample_content)
    
    print("✅ Fichier .env créé avec des valeurs d'exemple")
    print("📝 Modifiez .env avec vos vraies valeurs Firebase")

def main():
    """Fonction principale"""
    print("🤖 Assistant Configuration Firebase - Trading Bot")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Vérification de la configuration
        if check_firebase_setup():
            print("\n✅ Prêt à utiliser Firebase !")
        else:
            print("\n❌ Configuration incomplète")
            show_setup_instructions()
    elif len(sys.argv) > 1 and sys.argv[1] == "create-env":
        # Création du fichier .env
        create_sample_env()
    else:
        # Affichage des instructions
        show_setup_instructions()
        print("\n🔧 Commandes disponibles:")
        print("   python setup_firebase.py check       - Vérifier la configuration")
        print("   python setup_firebase.py create-env  - Créer un fichier .env d'exemple")

if __name__ == "__main__":
    main()
