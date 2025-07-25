#!/usr/bin/env python3
"""
Script de nettoyage Firebase 
"""

import logging
from datetime import datetime, timedelta

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    from utils.firebase_config import FIREBASE_CONFIG
    
    def cleanup_firebase_collections():
        """Nettoie les collections avec des timestamps problématiques"""
        
        # Initialisation Firebase
        try:
            if firebase_admin._apps:
                app = firebase_admin.get_app()
            else:
                cred = credentials.Certificate(FIREBASE_CONFIG.CREDENTIALS_PATH)
                app = firebase_admin.initialize_app(cred, {
                    'projectId': FIREBASE_CONFIG.PROJECT_ID
                })
            
            db = firestore.client()
            print("✅ Firebase connecté")
            
        except Exception as e:
            print(f"❌ Erreur connexion Firebase: {e}")
            return
        
        # Collections à nettoyer
        collections_to_clean = [
            'bot_logs',
            'result_pair_scan'
        ]
        
        for collection_name in collections_to_clean:
            try:
                print(f"\n🧹 Vidage COMPLET de la collection '{collection_name}'...")
                
                # Supprimer TOUS les documents de la collection
                docs = db.collection(collection_name).stream()
                
                batch = db.batch()
                count = 0
                
                for doc in docs:
                    batch.delete(doc.reference)
                    count += 1
                    
                    if count >= 500:  # Limite batch Firestore
                        batch.commit()
                        print(f"   📦 Batch de {count} documents supprimés")
                        batch = db.batch()
                        count = 0
                
                if count > 0:
                    batch.commit()
                    print(f"   📦 Dernier batch de {count} documents supprimés")
                
                print(f"✅ Collection '{collection_name}' COMPLÈTEMENT VIDÉE")
                
            except Exception as e:
                print(f"❌ Erreur vidage {collection_name}: {e}")
        
        print("\n🎉 Vidage terminé ! Les collections sont maintenant vides.")
        print("💡 Les nouvelles données du bot utiliseront des timestamps UTC uniformes.")
    
    if __name__ == "__main__":
        cleanup_firebase_collections()
        
except ImportError:
    print("❌ Firebase non installé. Ce script nécessite firebase-admin.")
    print("💡 Installez avec: pip install firebase-admin")
