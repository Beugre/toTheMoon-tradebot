#!/usr/bin/env python3
"""
Test manuel d'initialisation Firebase
"""

print("🔥 Test Manuel Firebase")
print("=" * 30)

# Import Firebase
try:
    import firebase_admin
    from firebase_admin import credentials, db, firestore
    print("✅ Firebase admin importé")
except Exception as e:
    print(f"❌ Erreur import Firebase: {e}")
    exit(1)

# Config
try:
    from utils.firebase_config import FIREBASE_CONFIG
    print("✅ Config chargée")
    print(f"   PROJECT_ID: {FIREBASE_CONFIG.PROJECT_ID}")
    print(f"   DATABASE_URL: {FIREBASE_CONFIG.DATABASE_URL}")
    print(f"   CREDENTIALS: {FIREBASE_CONFIG.CREDENTIALS_PATH}")
except Exception as e:
    print(f"❌ Erreur config: {e}")
    exit(1)

# Test initialisation
try:
    print("\n🚀 Initialisation Firebase...")
    
    # Nettoyage des apps existantes
    for app in firebase_admin._apps.values():
        firebase_admin.delete_app(app)
    
    # Initialisation
    cred = credentials.Certificate(FIREBASE_CONFIG.CREDENTIALS_PATH)
    app = firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_CONFIG.DATABASE_URL,
        'projectId': FIREBASE_CONFIG.PROJECT_ID
    })
    print("✅ App Firebase initialisée")
    
    # Test Realtime Database
    print("\n📊 Test Realtime Database...")
    db_ref = db.reference()
    test_ref = db_ref.child('_test')
    test_ref.set({
        'timestamp': '2024-01-01T00:00:00Z',
        'status': 'test_manual'
    })
    print("✅ Realtime Database OK")
    
    # Test Firestore
    print("\n🗃️  Test Firestore...")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection('_test').document('manual')
    doc_ref.set({
        'timestamp': '2024-01-01T00:00:00Z',
        'status': 'test_manual'
    })
    print("✅ Firestore OK")
    
    print("\n🎉 FIREBASE FONCTIONNE PARFAITEMENT!")
    
except Exception as e:
    print(f"❌ Erreur initialisation: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
