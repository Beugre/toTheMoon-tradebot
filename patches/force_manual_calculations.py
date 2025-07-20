#!/usr/bin/env python3
"""
🔧 FORÇAGE MANUEL DES CALCULS GOOGLE SHEETS
Script pour déclencher manuellement tous les calculs
"""

import os
import sys
from datetime import datetime

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

def force_all_calculations():
    """Force tous les calculs dans Google Sheets"""
    
    print("🔧 FORÇAGE MANUEL DES CALCULS GOOGLE SHEETS")
    print("=" * 60)
    
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
        
        # 1. FORCER RECALCUL PERFORMANCE_SUMMARY
        print("\n📈 FORÇAGE PERFORMANCE_SUMMARY...")
        try:
            summary_sheet = spreadsheet.worksheet("Performance_Summary")
            
            # Calculer manuellement depuis les données réelles
            trades_sheet = spreadsheet.worksheet("Trades_Detailed")
            all_data = trades_sheet.get_all_values()
            
            if len(all_data) > 1:  # Il y a des données en plus du header
                trades_data = all_data[1:]  # Skip header
                
                # Calculs manuels
                total_trades = len(trades_data)
                
                # P&L Net (colonne M = index 12)
                pnl_values = []
                for row in trades_data:
                    if len(row) > 12 and row[12]:  # P&L Net non vide
                        try:
                            pnl_values.append(float(row[12]))
                        except:
                            pass
                
                total_pnl = sum(pnl_values)
                winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
                losing_trades = len([pnl for pnl in pnl_values if pnl < 0])
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
                
                # ROI Net (colonne N = index 13)
                roi_values = []
                for row in trades_data:
                    if len(row) > 13 and row[13]:
                        try:
                            roi_values.append(float(row[13]))
                        except:
                            pass
                
                avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0
                
                # Mise à jour avec valeurs calculées
                summary_sheet.update('B4', total_trades)
                summary_sheet.update('B5', winning_trades)
                summary_sheet.update('B6', losing_trades)
                summary_sheet.update('B7', f"{win_rate:.1f}")
                summary_sheet.update('B8', f"{total_pnl:.2f}")
                summary_sheet.update('B9', f"{avg_pnl:.2f}")
                summary_sheet.update('B10', f"{avg_roi:.2f}")
                
                # P&L par paire
                pair_pnl = {}
                for row in trades_data:
                    if len(row) > 12 and row[2] and row[12]:  # Paire et P&L
                        pair = row[2]
                        try:
                            pnl = float(row[12])
                            if pair not in pair_pnl:
                                pair_pnl[pair] = 0
                            pair_pnl[pair] += pnl
                        except:
                            pass
                
                # Mise à jour top 5 paires
                pairs = ["BTCUSDC", "ETHUSDC", "SOLUSDC", "XRPUSDC", "DOGEUSDC"]
                for i, pair in enumerate(pairs, 13):
                    pnl = pair_pnl.get(pair, 0)
                    summary_sheet.update(f'B{i}', f"{pnl:.2f}")
                
                # Analyse horaire
                hourly_counts = {"09-12": 0, "12-15": 0, "15-18": 0, "18-23": 0}
                for row in trades_data:
                    if len(row) > 1 and row[1]:  # Colonne heure
                        try:
                            hour = int(row[1].split(':')[0])
                            if 9 <= hour < 12:
                                hourly_counts["09-12"] += 1
                            elif 12 <= hour < 15:
                                hourly_counts["12-15"] += 1
                            elif 15 <= hour < 18:
                                hourly_counts["15-18"] += 1
                            elif 18 <= hour < 23:
                                hourly_counts["18-23"] += 1
                        except:
                            pass
                
                summary_sheet.update('B20', hourly_counts["09-12"])
                summary_sheet.update('B21', hourly_counts["12-15"])
                summary_sheet.update('B22', hourly_counts["15-18"])
                summary_sheet.update('B23', hourly_counts["18-23"])
                
                # Dernière mise à jour
                summary_sheet.update('B25', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                print(f"   ✅ Métriques mises à jour:")
                print(f"      📊 Total trades: {total_trades}")
                print(f"      💰 P&L total: {total_pnl:.2f}$")
                print(f"      🎯 Win rate: {win_rate:.1f}%")
                print(f"      📈 ROI moyen: {avg_roi:.2f}%")
        
        except Exception as e:
            print(f"   ❌ Erreur Performance_Summary: {e}")
        
        # 2. FORCER RECALCUL PAIRS_ANALYSIS
        print("\n🎯 FORÇAGE PAIRS_ANALYSIS...")
        try:
            pairs_sheet = spreadsheet.worksheet("Pairs_Analysis")
            
            pairs = ["BTCUSDC", "ETHUSDC", "SOLUSDC", "XRPUSDC", "DOGEUSDC", 
                    "ADAUSDC", "MATICUSDC", "LTCUSDC", "LINKUSDC", "DOTUSDC"]
            
            for i, pair in enumerate(pairs, 2):
                # Filtrer les trades de cette paire
                pair_trades = [row for row in trades_data if len(row) > 2 and row[2] == pair] # type: ignore
                
                if pair_trades:
                    # Calculs pour cette paire
                    nb_trades = len(pair_trades)
                    
                    # P&L pour cette paire
                    pair_pnl_values = []
                    for row in pair_trades:
                        if len(row) > 12 and row[12]:
                            try:
                                pair_pnl_values.append(float(row[12]))
                            except:
                                pass
                    
                    if pair_pnl_values:
                        total_pnl_pair = sum(pair_pnl_values)
                        winning_pair = len([pnl for pnl in pair_pnl_values if pnl > 0])
                        win_rate_pair = (winning_pair / nb_trades * 100) if nb_trades > 0 else 0
                        avg_pnl_pair = total_pnl_pair / nb_trades
                        best_trade = max(pair_pnl_values)
                        worst_trade = min(pair_pnl_values)
                        
                        # ROI pour cette paire
                        pair_roi_values = []
                        for row in pair_trades:
                            if len(row) > 13 and row[13]:
                                try:
                                    pair_roi_values.append(float(row[13]))
                                except:
                                    pass
                        
                        avg_roi_pair = sum(pair_roi_values) / len(pair_roi_values) if pair_roi_values else 0
                        
                        # Recommandation
                        if win_rate_pair > 60:
                            recommendation = "HIGH"
                        elif win_rate_pair > 30:
                            recommendation = "MEDIUM"
                        else:
                            recommendation = "LOW"
                        
                        # Mise à jour de la ligne
                        pairs_sheet.update(f'B{i}', nb_trades)
                        pairs_sheet.update(f'C{i}', f"{win_rate_pair:.1f}")
                        pairs_sheet.update(f'D{i}', f"{total_pnl_pair:.2f}")
                        pairs_sheet.update(f'E{i}', f"{avg_pnl_pair:.2f}")
                        pairs_sheet.update(f'F{i}', f"{avg_roi_pair:.2f}")
                        pairs_sheet.update(f'G{i}', f"{best_trade:.2f}")
                        pairs_sheet.update(f'H{i}', f"{worst_trade:.2f}")
                        pairs_sheet.update(f'I{i}', recommendation)
                        
                        print(f"   ✅ {pair}: {nb_trades} trades, Win: {win_rate_pair:.1f}%, P&L: {total_pnl_pair:.2f}$")
                else:
                    # Pas de trades pour cette paire - mettre zéros
                    pairs_sheet.update(f'B{i}', 0)
                    pairs_sheet.update(f'C{i}', "0")
                    pairs_sheet.update(f'D{i}', "0")
                    pairs_sheet.update(f'E{i}', "0")
                    pairs_sheet.update(f'F{i}', "0")
                    pairs_sheet.update(f'G{i}', "0")
                    pairs_sheet.update(f'H{i}', "0")
                    pairs_sheet.update(f'I{i}', "LOW")
        
        except Exception as e:
            print(f"   ❌ Erreur Pairs_Analysis: {e}")
        
        print(f"\n🎉 FORÇAGE TERMINÉ!")
        print(f"📋 Tous les calculs ont été forcés manuellement")
        print(f"✅ Vérifiez maintenant vos onglets - tout devrait être calculé!")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        print(f"Détails: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = force_all_calculations()
    
    if success:
        print("\n🚀 CALCULS FORCÉS AVEC SUCCÈS!")
        print("📊 Tous les onglets devraient maintenant afficher les bonnes valeurs")
    else:
        print("\n❌ ÉCHEC DU FORÇAGE")
        print("💡 Vérifiez les credentials et les données")
