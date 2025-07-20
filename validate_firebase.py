"""
Script de test pour vérifier la connexion Firebase
Utilisez ce script pour valider vos credentials avant le déploiement
"""

import json
import os
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore


def test_firebase_connection():
    """Teste la connexion Firebase et affiche les données disponibles"""
    
    print("🔥 Test de connexion Firebase pour ToTheMoon Bot")
    print("=" * 50)
    
    try:
        # Initialiser Firebase
        if not firebase_admin._apps:
            if os.path.exists("firebase_credentials.json"):
                cred = credentials.Certificate("firebase_credentials.json")
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialisé avec firebase_credentials.json")
            else:
                print("❌ Fichier firebase_credentials.json non trouvé")
                print("   Placez votre fichier de credentials Firebase dans le dossier du projet")
                return False
        
        # Connexion à Firestore
        db = firestore.client()
        print("✅ Connexion à Firestore établie")
        
        # Test des collections
        collections = ['bot_logs', 'trades', 'metrics', 'performance']
        
        for collection_name in collections:
            print(f"\n📊 Collection: {collection_name}")
            try:
                # Compter les documents
                docs = list(db.collection(collection_name).limit(5).stream())
                count = len(docs)
                
                if count > 0:
                    print(f"   ✅ {count} documents trouvés")
                else:
                    print(f"   ⚠️  Collection vide - votre bot n'a pas encore envoyé de données")
                    
            except Exception as e:
                print(f"   ❌ Erreur d'accès: {e}")
        
        print(f"\n🎉 Test terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion Firebase: {e}")
        return False

if __name__ == "__main__":
    test_firebase_connection()
