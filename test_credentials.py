#!/usr/bin/env python3
"""
🔍 TEST CREDENTIALS GOOGLE SHEETS
Vérification rapide que credentials.json fonctionne
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv


def test_credentials():
    print("🔍 " + "="*50)
    print("🔑 TEST CREDENTIALS GOOGLE SHEETS")
    print("🔍 " + "="*50)
    
    # Charger les variables d'environnement
    load_dotenv()
    print("🌍 Variables d'environnement chargées depuis .env")
    
    # 1. Vérification fichier credentials.json
    credentials_path = "credentials.json"
    
    print(f"\n📁 VÉRIFICATION FICHIER:")
    if os.path.exists(credentials_path):
        print(f"   ✅ {credentials_path} trouvé")
        
        # Vérifier la taille
        size = os.path.getsize(credentials_path)
        print(f"   📊 Taille: {size} bytes")
        
        if size < 100:
            print(f"   ⚠️  Fichier très petit - vérifiez le contenu")
        else:
            print(f"   ✅ Taille normale")
    else:
        print(f"   ❌ {credentials_path} MANQUANT")
        return False
    
    # 2. Vérification contenu JSON
    print(f"\n📋 VÉRIFICATION CONTENU JSON:")
    try:
        with open(credentials_path, 'r') as f:
            credentials_data = json.load(f)
        
        # Vérifier les champs essentiels
        required_fields = [
            'type', 'project_id', 'private_key_id', 
            'private_key', 'client_email', 'client_id'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field in credentials_data:
                print(f"   ✅ {field}: Présent")
            else:
                print(f"   ❌ {field}: MANQUANT")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"   🚨 Champs manquants: {missing_fields}")
            return False
        
        # Vérifier le type
        if credentials_data.get('type') == 'service_account':
            print(f"   ✅ Type service_account confirmé")
        else:
            print(f"   ⚠️  Type: {credentials_data.get('type')} (devrait être 'service_account')")
        
        # Vérifier l'email
        client_email = credentials_data.get('client_email', '')
        if '@' in client_email and '.iam.gserviceaccount.com' in client_email:
            print(f"   ✅ Email service account valide: {client_email[:30]}...")
        else:
            print(f"   ⚠️  Email suspect: {client_email}")
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON invalide: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur lecture: {e}")
        return False
    
    # 3. Vérification variables d'environnement
    print(f"\n🌍 VÉRIFICATION VARIABLES D'ENVIRONNEMENT:")
    
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if spreadsheet_id:
        print(f"   ✅ GOOGLE_SHEETS_SPREADSHEET_ID: {spreadsheet_id[:20]}...")
        
        # Vérifier le format
        if len(spreadsheet_id) > 40 and len(spreadsheet_id) < 50:
            print(f"   ✅ Format ID valide (longueur: {len(spreadsheet_id)})")
        else:
            print(f"   ⚠️  Format ID suspect (longueur: {len(spreadsheet_id)})")
    else:
        print(f"   ❌ GOOGLE_SHEETS_SPREADSHEET_ID manquant dans .env")
        return False
    
    # 4. Test basique d'import gspread
    print(f"\n📦 VÉRIFICATION MODULES:")
    try:
        import gspread
        print(f"   ✅ gspread importé (version disponible)")
        
        from oauth2client.service_account import ServiceAccountCredentials
        print(f"   ✅ oauth2client importé")
        
    except ImportError as e:
        print(f"   ❌ Module manquant: {e}")
        print(f"   💡 Installez avec: pip install gspread oauth2client")
        return False
    
    # 5. Test de connexion basique
    print(f"\n🔗 TEST CONNEXION GOOGLE SHEETS:")
    try:
        # Configuration scopes
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Authentification
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope
        )
        print(f"   ✅ Credentials chargés")
        
        # Connexion client
        client = gspread.authorize(credentials)
        print(f"   ✅ Client Google Sheets connecté")
        
        # Test d'ouverture du spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"   ✅ Spreadsheet ouvert: {spreadsheet.title}")
        
        # Lister les onglets
        worksheets = spreadsheet.worksheets()
        print(f"   📊 Onglets trouvés: {len(worksheets)}")
        for ws in worksheets:
            print(f"      - {ws.title}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        print(f"   💡 Vérifiez:")
        print(f"      - Le spreadsheet est partagé avec {credentials_data.get('client_email', 'l email service')}")
        print(f"      - L'API Google Sheets est activée")
        print(f"      - L'ID du spreadsheet est correct")
        return False

def show_next_steps(success: bool):
    """Affiche les prochaines étapes"""
    print(f"\n🎯 PROCHAINES ÉTAPES:")
    print("="*20)
    
    if success:
        print(f"   ✅ CREDENTIALS OK - Prêt pour Google Sheets Enhanced!")
        print(f"   🚀 Vous pouvez maintenant:")
        print(f"      1. Tester le enhanced_sheets_logger.py")
        print(f"      2. Intégrer dans main.py")
        print(f"      3. Lancer le bot avec logging complet")
    else:
        print(f"   ❌ CREDENTIALS KO - Actions requises:")
        print(f"      1. Vérifiez credentials.json")
        print(f"      2. Partagez le spreadsheet avec le service account")
        print(f"      3. Activez l'API Google Sheets")
        print(f"      4. Vérifiez GOOGLE_SHEETS_SPREADSHEET_ID")

if __name__ == "__main__":
    print("🚀 LANCEMENT TEST CREDENTIALS GOOGLE SHEETS")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_credentials()
    show_next_steps(success)
    
    if success:
        print(f"\n🎉 TEST RÉUSSI - CREDENTIALS OPÉRATIONNELS!")
    else:
        print(f"\n❌ TEST ÉCHOUÉ - VÉRIFIEZ LA CONFIGURATION")
