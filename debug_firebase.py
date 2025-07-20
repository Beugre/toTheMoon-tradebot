#!/usr/bin/env python3
"""
Debug Firebase step by step
"""

print("🔍 Debug Firebase Configuration")
print("=" * 40)

# Étape 1: Test import dotenv
print("1. Test dotenv...")
try:
    from dotenv import load_dotenv
    result = load_dotenv()
    print(f"   ✅ dotenv chargé: {result}")
except Exception as e:
    print(f"   ❌ Erreur dotenv: {e}")

# Étape 2: Test variables env
print("\n2. Test variables d'environnement...")
import os

project_id = os.getenv("FIREBASE_PROJECT_ID")
database_url = os.getenv("FIREBASE_DATABASE_URL")
credentials = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")

print(f"   PROJECT_ID: '{project_id}'")
print(f"   DATABASE_URL: '{database_url}'")
print(f"   CREDENTIALS: '{credentials}'")

# Étape 3: Test fichier credentials
print(f"\n3. Test fichier credentials...")
if os.path.exists(credentials):
    print(f"   ✅ Fichier trouvé: {credentials}")
    size = os.path.getsize(credentials)
    print(f"   📦 Taille: {size} bytes")
else:
    print(f"   ❌ Fichier manquant: {credentials}")

# Étape 4: Test import firebase admin
print(f"\n4. Test import Firebase Admin...")
try:
    import firebase_admin
    print(f"   ✅ firebase_admin importé")
    print(f"   📦 Version: {firebase_admin.__version__}")
except Exception as e:
    print(f"   ❌ Erreur import: {e}")

# Étape 5: Test firebase config
print(f"\n5. Test firebase_config...")
try:
    from utils.firebase_config import FIREBASE_CONFIG
    print(f"   ✅ Config chargée")
    print(f"   PROJECT_ID: '{FIREBASE_CONFIG.PROJECT_ID}'")
    print(f"   DATABASE_URL: '{FIREBASE_CONFIG.DATABASE_URL}'")
except Exception as e:
    print(f"   ❌ Erreur config: {e}")

print("\n" + "=" * 40)
