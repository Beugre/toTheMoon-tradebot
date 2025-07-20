#!/usr/bin/env python3
"""
Test du chemin credentials.json
"""

import os
import sys

# Ajouter le chemin racine
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_path)

from config import API_CONFIG

print("🔍 TEST CHEMIN CREDENTIALS")
print("=" * 40)
print(f"📁 Chemin configuré: {API_CONFIG.GOOGLE_SHEETS_CREDENTIALS}")
print(f"📋 Existe: {'✅' if os.path.exists(API_CONFIG.GOOGLE_SHEETS_CREDENTIALS) else '❌'}")
print(f"📂 Répertoire: {os.path.dirname(API_CONFIG.GOOGLE_SHEETS_CREDENTIALS)}")
print(f"📄 Nom fichier: {os.path.basename(API_CONFIG.GOOGLE_SHEETS_CREDENTIALS)}")

if os.path.exists(API_CONFIG.GOOGLE_SHEETS_CREDENTIALS):
    file_size = os.path.getsize(API_CONFIG.GOOGLE_SHEETS_CREDENTIALS)
    print(f"📊 Taille: {file_size} octets")
    print("✅ CHEMIN CREDENTIALS CORRECT")
else:
    print("❌ FICHIER CREDENTIALS NON TROUVÉ")
    print(f"💡 Vérifiez que le fichier existe: {API_CONFIG.GOOGLE_SHEETS_CREDENTIALS}")
