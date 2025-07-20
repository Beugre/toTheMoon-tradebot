#!/usr/bin/env python3
"""
Test rapide de connexion Firebase
Vérifiez que le fichier firebase_credentials.json est bien présent
"""

import os
import sys


def check_firebase_setup():
    """Vérifie la configuration Firebase"""
    print("🔥 Vérification Configuration Firebase")
    print("=" * 50)
    
    # Check 1: Fichier credentials
    credentials_file = "firebase_credentials.json"
    if os.path.exists(credentials_file):
        print(f"✅ Fichier credentials trouvé: {credentials_file}")
        file_size = os.path.getsize(credentials_file)
        print(f"   📦 Taille: {file_size} bytes")
    else:
        print(f"❌ Fichier credentials manquant: {credentials_file}")
        print("📝 Actions à faire:")
        print("1. Allez dans Firebase Console > Paramètres > Comptes de service")
        print("2. Cliquez 'Générer une nouvelle clé privée'")
        print("3. Téléchargez le fichier JSON")
        print("4. Renommez-le 'firebase_credentials.json'")
        print("5. Placez-le dans le dossier du bot")
        return False
    
    # Check 2: Variables d'environnement
    from utils.firebase_config import FIREBASE_CONFIG
    print(f"\n📋 Configuration:")
    print(f"   🏷️  Projet ID: {FIREBASE_CONFIG.PROJECT_ID}")
    print(f"   🔗 Database URL: {FIREBASE_CONFIG.DATABASE_URL}")
    print(f"   🔑 Credentials: {FIREBASE_CONFIG.CREDENTIALS_PATH}")
    
    # Check 3: Test de connexion
    print(f"\n🧪 Test de connexion...")
    try:
        from utils.firebase_logger import firebase_logger
        result = firebase_logger.test_firebase_connection()
        if result:
            print("✅ Connexion Firebase RÉUSSIE!")
            print("🎉 Firebase est prêt pour le bot!")
            return True
        else:
            print("❌ Connexion Firebase échouée")
            print("🔧 Vérifiez vos credentials et la configuration")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False

if __name__ == "__main__":
    success = check_firebase_setup()
    
    print("\n" + "=" * 50)
    if success:
        print("🚀 FIREBASE PRÊT!")
        print("Vous pouvez maintenant lancer le bot avec Firebase Analytics")
        sys.exit(0)
    else:
        print("⚠️  CONFIGURATION INCOMPLÈTE")
        print("Complétez la configuration avant de continuer")
        sys.exit(1)
