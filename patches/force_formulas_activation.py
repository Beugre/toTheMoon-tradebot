#!/usr/bin/env python3
"""
🔧 ACTIVATION FORCÉE DES FORMULES GOOGLE SHEETS
Script pour forcer le calcul des formules dans tous les onglets
"""

import os
import sys
from datetime import datetime

# Ajouter le chemin vers utils
utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
sys.path.insert(0, utils_path)

# Charger les variables d'environnement
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

from enhanced_sheets_logger import EnhancedSheetsLogger  # type: ignore


async def force_formulas_calculation():
    """Force le calcul des formules dans tous les onglets"""
    
    print("🔧 ACTIVATION FORCÉE DES FORMULES GOOGLE SHEETS")
    print("=" * 60)
    
    # Configuration
    credentials_path = "../credentials.json"
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    
    if not os.path.exists(credentials_path):
        print("❌ Fichier credentials.json manquant")
        return
    
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_ID non défini")
        return
    
    # Initialisation logger
    logger = EnhancedSheetsLogger(credentials_path, spreadsheet_id)
    
    if not logger.client:
        print("❌ Impossible d'initialiser Google Sheets")
        return
    
    print("✅ Logger initialisé")
    
    try:
        # 1. FORCER CALCUL PERFORMANCE_PAIRS
        print("\n📈 ACTIVATION ONGLET PERFORMANCE_PAIRS...")
        pairs_sheet = logger.spreadsheet.worksheet("Performance_Pairs")
        
        # Forcer le recalcul en modifiant puis restaurant une cellule
        original_value = pairs_sheet.acell('A1').value
        pairs_sheet.update('A1', 'REFRESH')
        pairs_sheet.update('A1', original_value)
        
        # Ajouter des valeurs calculées manuellement pour vérification
        pairs_data = pairs_sheet.get_all_values()
        if len(pairs_data) > 1:
            print("   ✅ Données trouvées, mise à jour des calculs...")
            
            # Mise à jour ligne BTCUSDC (ligne 2) avec calculs forcés
            trades_sheet = logger.spreadsheet.worksheet("Trades_Detailed")
            all_trades = trades_sheet.get_all_values()
            
            # Compter trades BTCUSDC
            btc_trades = [row for row in all_trades[1:] if len(row) > 2 and row[2] == 'BTCUSDC']
            btc_pnl = sum(float(row[13]) for row in btc_trades if len(row) > 13 and row[13])
            btc_wins = len([row for row in btc_trades if len(row) > 13 and row[13] and float(row[13]) > 0])
            btc_total = len(btc_trades)
            btc_win_rate = (btc_wins / btc_total * 100) if btc_total > 0 else 0
            
            # Mise à jour avec valeurs calculées
            if btc_total > 0:
                pairs_sheet.update('B2', btc_total)  # Nb trades
                pairs_sheet.update('F2', f"{btc_pnl:.2f}")  # P&L Net
                pairs_sheet.update('G2', f"{btc_win_rate:.1f}%")  # Win Rate
                pairs_sheet.update('M2', "HIGH" if btc_win_rate > 60 else "MEDIUM")  # Priorité
                print(f"   📊 BTCUSDC: {btc_total} trades, P&L: {btc_pnl:.2f}$, Win: {btc_win_rate:.1f}%")
        
        # 2. FORCER CALCUL HOURLY_ANALYSIS
        print("\n⏰ ACTIVATION ONGLET HOURLY_ANALYSIS...")
        hourly_sheet = logger.spreadsheet.worksheet("Hourly_Analysis")
        
        # Calculer répartition par heure
        current_hour = datetime.now().hour
        hourly_trades = {}
        
        for row in all_trades[1:]: # type: ignore
            if len(row) > 1 and row[1]:  # Colonne heure
                try:
                    hour = int(row[1].split(':')[0])
                    hourly_trades[hour] = hourly_trades.get(hour, 0) + 1
                except:
                    pass
        
        # Mettre à jour quelques heures avec données réelles
        for hour, count in hourly_trades.items():
            row_num = hour + 2  # Header en ligne 1, heure 0 en ligne 2
            if row_num <= 25:  # Max 24 heures
                hourly_sheet.update(f'B{row_num}', count)
                print(f"   ⏰ {hour:02d}h: {count} trades")
        
        # 3. FORCER CALCUL ANALYTICS_DASHBOARD
        print("\n🎯 ACTIVATION ONGLET ANALYTICS_DASHBOARD...")
        dashboard_sheet = logger.spreadsheet.worksheet("Analytics_Dashboard")
        
        # Calculer métriques globales
        total_trades = len(all_trades) - 1  # -1 pour header # type: ignore
        total_pnl = sum(float(row[13]) for row in all_trades[1:] if len(row) > 13 and row[13]) # type: ignore
        winning_trades = len([row for row in all_trades[1:] if len(row) > 13 and row[13] and float(row[13]) > 0]) # type: ignore
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0 
        
        # Mise à jour dashboard avec vraies valeurs
        dashboard_sheet.update('B4', total_trades)  # Total trades
        dashboard_sheet.update('B5', f"{total_pnl:.2f}$")  # P&L Total
        dashboard_sheet.update('B6', f"{win_rate:.1f}%")  # Win Rate
        dashboard_sheet.update('B7', datetime.now().strftime("%Y-%m-%d %H:%M"))  # Dernière MAJ
        
        # Top paire
        pair_performance = {}
        for row in all_trades[1:]: # type: ignore
            if len(row) > 13 and row[2] and row[13]:
                pair = row[2]
                pnl = float(row[13])
                if pair not in pair_performance:
                    pair_performance[pair] = 0
                pair_performance[pair] += pnl
        
        if pair_performance:
            best_pair = max(pair_performance.items(), key=lambda x: x[1])
            worst_pair = min(pair_performance.items(), key=lambda x: x[1])
            
            dashboard_sheet.update('B9', f"{best_pair[0]} (+{best_pair[1]:.2f}$)")
            dashboard_sheet.update('B10', f"{worst_pair[0]} ({worst_pair[1]:.2f}$)")
        
        print(f"   🎯 Total: {total_trades} trades, P&L: {total_pnl:.2f}$, Win: {win_rate:.1f}%")
        
        # 4. FORCER RECALCUL GÉNÉRAL
        print("\n🔄 FORÇAGE RECALCUL GÉNÉRAL...")
        
        # Technique pour forcer Google Sheets à recalculer toutes les formules
        # Modifier et restaurer une cellule dans chaque onglet
        for sheet_name in ["Performance_Pairs", "Hourly_Analysis", "Analytics_Dashboard"]:
            try:
                sheet = logger.spreadsheet.worksheet(sheet_name)
                # Déclencher un recalcul
                sheet.update('A1', f'=NOW()')
                print(f"   ✅ {sheet_name} forcé au recalcul")
            except Exception as e:
                print(f"   ⚠️ {sheet_name}: {e}")
        
        print(f"\n🎉 ACTIVATION TERMINÉE!")
        print(f"📋 Toutes les formules devraient maintenant être actives")
        print(f"🔗 Vérifiez: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        # Résumé final
        print(f"\n📊 RÉSUMÉ DES DONNÉES ACTIVÉES:")
        print(f"   📈 Performance_Pairs: {len(pair_performance)} paires avec données")
        print(f"   ⏰ Hourly_Analysis: {len(hourly_trades)} heures avec activité")
        print(f"   🎯 Analytics_Dashboard: Métriques globales mises à jour")
        print(f"   ✅ Formules forcées au recalcul")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'activation: {e}")
        import traceback
        print(f"Détails: {traceback.format_exc()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(force_formulas_calculation())
