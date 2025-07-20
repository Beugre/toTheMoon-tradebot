#!/usr/bin/env python3
"""
🗑️ NETTOYAGE DES TRADES DE TEST
Vide les données de test pour préparer le VPS
"""

import os
import sys

# Configuration paths
utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
sys.path.insert(0, utils_path)

from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("❌ Modules manquants. Installez avec: pip install gspread oauth2client")
    sys.exit(1)

def clear_test_data():
    """Vide tous les trades de test pour préparer le VPS"""
    
    print("🗑️ NETTOYAGE DES TRADES DE TEST")
    print("=" * 50)
    
    # Configuration
    credentials_path = "../credentials.json"
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    
    if not os.path.exists(credentials_path):
        print(f"❌ Fichier credentials.json manquant: {credentials_path}")
        return False
    
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_ID non défini")
        return False
    
    try:
        # Connexion
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope # type: ignore
        )
        
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        print("✅ Connexion établie")
        
        # 1. VIDER TRADES_DETAILED (garder headers)
        print("\n📊 Nettoyage Trades_Detailed...")
        trades_sheet = spreadsheet.worksheet("Trades_Detailed")
        
        # Supprimer toutes les lignes sauf le header
        all_values = trades_sheet.get_all_values()
        if len(all_values) > 1:
            # Effacer du rang 2 jusqu'à la fin
            range_to_clear = f"A2:T{len(all_values)}"
            trades_sheet.batch_clear([range_to_clear])
            print(f"   ✅ {len(all_values)-1} trades de test supprimés")
        else:
            print("   ℹ️ Aucun trade à supprimer")
        
        # 2. RÉINITIALISER PERFORMANCE_SUMMARY
        print("\n📈 Réinitialisation Performance_Summary...")
        summary_sheet = spreadsheet.worksheet("Performance_Summary")
        
        # Remettre à zéro les valeurs calculées
        zero_updates = [
            ('B4', 0),    # Total Trades
            ('B5', 0),    # Trades Gagnants  
            ('B6', 0),    # Trades Perdants
            ('B7', "0.0"), # Win Rate
            ('B8', "0.00"), # P&L Total
            ('B9', "0.00"), # P&L Moyen
            ('B10', "0.00"), # ROI Moyen
            ('B13', "0.00"), # BTCUSDC
            ('B14', "0.00"), # ETHUSDC
            ('B15', "0.00"), # SOLUSDC
            ('B16', "0.00"), # XRPUSDC
            ('B17', "0.00"), # DOGEUSDC
            ('B20', 0),    # 09-12h
            ('B21', 0),    # 12-15h
            ('B22', 0),    # 15-18h
            ('B23', 0),    # 18-23h
        ]
        
        for cell, value in zero_updates:
            summary_sheet.update(cell, value)
        
        print("   ✅ Métriques remises à zéro")
        
        # 3. RÉINITIALISER PAIRS_ANALYSIS
        print("\n🎯 Réinitialisation Pairs_Analysis...")
        pairs_sheet = spreadsheet.worksheet("Pairs_Analysis")
        
        # Remettre à zéro toutes les paires (lignes 2-11)
        for row in range(2, 12):
            zero_row_updates = [
                (f'B{row}', 0),      # Nb_Trades
                (f'C{row}', "0.0"),  # Win_Rate_%
                (f'D{row}', "0.00"), # P&L_Total
                (f'E{row}', "0.00"), # P&L_Moyen
                (f'F{row}', "0.00"), # ROI_Moyen_%
                (f'G{row}', "0.00"), # Meilleur_Trade
                (f'H{row}', "0.00"), # Pire_Trade
                (f'I{row}', "LOW"),  # Recommandation
            ]
            
            for cell, value in zero_row_updates:
                pairs_sheet.update(cell, value)
        
        print("   ✅ Toutes les paires remises à zéro")
        
        print(f"\n🎉 NETTOYAGE TERMINÉ!")
        print(f"✅ Trades de test supprimés")
        print(f"✅ Métriques remises à zéro")
        print(f"✅ Prêt pour les trades en production VPS")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        print(f"Détails: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("⚠️  ATTENTION: Cette opération va supprimer TOUS les trades de test!")
    print("📋 Assurez-vous que c'est bien ce que vous voulez faire.")
    print()
    
    confirm = input("Confirmer le nettoyage ? (oui/non): ").lower().strip()
    if confirm not in ['oui', 'o', 'yes', 'y']:
        print("❌ Nettoyage annulé")
    else:
        success = clear_test_data()
        
        if success:
            print("\n🚀 GOOGLE SHEETS NETTOYÉ - PRÊT POUR VPS!")
        else:
            print("\n❌ ÉCHEC DU NETTOYAGE")
