#!/usr/bin/env python3
"""
🧪 TEST ET AMÉLIORATION GOOGLE SHEETS
Vérification et optimisation du logging pour analyse fine
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MockTrade:
    """Trade simulé pour test"""
    pair: str
    direction: str
    size: float
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    pnl: float
    exit_reason: str
    duration: timedelta
    
def create_enhanced_sheets_headers():
    """Définit les en-têtes améliorés pour analyse fine"""
    
    print("📊 STRUCTURE GOOGLE SHEETS OPTIMISÉE POUR ANALYSE FINE")
    print("="*60)
    
    # En-têtes Trade avec analyse frais détaillée
    trade_headers = [
        "Date",
        "Heure", 
        "Paire",
        "Direction",
        "Taille (USDC)",
        "Prix Entrée",
        "Prix Sortie", 
        "Stop Loss",
        "Take Profit",
        "P&L Brut (USDC)",
        "Frais Entrée (USDC)",
        "Frais Sortie (USDC)", 
        "Frais Total (USDC)",
        "P&L Net (USDC)",
        "P&L %",
        "ROI Net %",
        "Durée",
        "Raison Sortie",
        "Capital Avant",
        "Capital Après",
        "Session Trading",
        "Intensité Horaire",
        "Volatilité Paire",
        "Volume 24h",
        "Spread %"
    ]
    
    print("\n📋 EN-TÊTES ONGLET TRADES:")
    for i, header in enumerate(trade_headers, 1):
        print(f"   {chr(64+i)}: {header}")
    
    # En-têtes Performance par paire
    performance_headers = [
        "Paire", 
        "Nb Trades",
        "Volume Total (USDC)",
        "P&L Brut (USDC)",
        "Frais Total (USDC)", 
        "P&L Net (USDC)",
        "Win Rate %",
        "Profit Factor",
        "ROI Net %",
        "Frais/Volume %",
        "Durée Moy (min)",
        "Score Rentabilité",
        "Priorité",
        "Dernière MAJ"
    ]
    
    print(f"\n📈 EN-TÊTES ONGLET PERFORMANCE PAR PAIRE:")
    for i, header in enumerate(performance_headers, 1):
        print(f"   {chr(64+i)}: {header}")
    
    # Métriques horaires
    hourly_headers = [
        "Heure",
        "Session",
        "Nb Trades", 
        "Volume (USDC)",
        "P&L Net (USDC)",
        "Frais (USDC)",
        "Win Rate %",
        "ROI Horaire %",
        "Intensité",
        "Score Session"
    ]
    
    print(f"\n⏰ EN-TÊTES ONGLET ANALYSE HORAIRE:")
    for i, header in enumerate(hourly_headers, 1):
        print(f"   {chr(64+i)}: {header}")
    
    return {
        'trades': trade_headers,
        'performance_pairs': performance_headers, 
        'hourly': hourly_headers
    }

def calculate_trade_metrics(trade, capital_before, capital_after):
    """Calcule toutes les métriques d'un trade"""
    
    # Calcul des frais (0.1% par transaction)
    fee_rate = 0.001  # 0.1%
    
    entry_fee = trade.size * fee_rate  # Frais d'entrée
    exit_value = trade.size * (trade.exit_price / trade.entry_price)
    exit_fee = exit_value * fee_rate   # Frais de sortie
    total_fees = entry_fee + exit_fee
    
    # P&L brut et net
    pnl_gross = trade.pnl  # P&L avant frais
    pnl_net = pnl_gross - total_fees  # P&L après frais
    
    # Pourcentages
    pnl_percent = (pnl_gross / trade.size) * 100
    roi_net_percent = (pnl_net / trade.size) * 100
    
    # Session et intensité (simulation)
    hour = trade.timestamp.hour
    if 9 <= hour < 12:
        session = "EU_MORNING"
        intensity = 1.0
    elif 15 <= hour < 18:
        session = "EU_US_OVERLAP"  
        intensity = 1.0
    elif 18 <= hour < 21:
        session = "US_PRIME"
        intensity = 1.0
    elif 12 <= hour < 14:
        session = "LUNCH_BREAK"
        intensity = 0.5
    else:
        session = "NORMAL"
        intensity = 0.7
    
    return {
        'entry_fee': entry_fee,
        'exit_fee': exit_fee,
        'total_fees': total_fees,
        'pnl_net': pnl_net,
        'pnl_percent': pnl_percent,
        'roi_net_percent': roi_net_percent,
        'session': session,
        'intensity': intensity
    }

def simulate_enhanced_logging():
    """Simule le logging avec structure améliorée"""
    
    print(f"\n🧪 SIMULATION LOGGING AMÉLIORÉ")
    print("="*40)
    
    # Trades simulés
    mock_trades = [
        MockTrade(
            pair="BTCUSDC",
            direction="LONG", 
            size=5000.0,
            entry_price=65000.0,
            exit_price=65780.0,
            stop_loss=64837.5,
            take_profit=65780.0,
            timestamp=datetime(2025, 7, 20, 10, 30),
            pnl=60.0,
            exit_reason="TAKE_PROFIT",
            duration=timedelta(minutes=15)
        ),
        MockTrade(
            pair="ETHUSDC", 
            direction="LONG",
            size=5000.0,
            entry_price=3500.0,
            exit_price=3458.25,
            stop_loss=3458.25, 
            take_profit=3542.0,
            timestamp=datetime(2025, 7, 20, 16, 45),
            pnl=-41.75,
            exit_reason="STOP_LOSS",
            duration=timedelta(minutes=8)
        )
    ]
    
    total_volume = 0
    total_fees = 0
    total_pnl_net = 0
    
    for trade in mock_trades:
        print(f"\n📊 TRADE: {trade.pair}")
        
        # Simulation capital
        capital_before = 22819.0 + total_pnl_net
        capital_after = capital_before + trade.pnl
        
        # Calcul métriques
        metrics = calculate_trade_metrics(trade, capital_before, capital_after)
        
        # Affichage ligne Excel/Sheets
        row_data = [
            trade.timestamp.strftime("%Y-%m-%d"),
            trade.timestamp.strftime("%H:%M:%S"),
            trade.pair,
            trade.direction,
            f"{trade.size:.2f}",
            f"{trade.entry_price:.2f}",
            f"{trade.exit_price:.2f}",
            f"{trade.stop_loss:.2f}",
            f"{trade.take_profit:.2f}",
            f"{trade.pnl:.2f}",
            f"{metrics['entry_fee']:.2f}",
            f"{metrics['exit_fee']:.2f}",
            f"{metrics['total_fees']:.2f}",
            f"{metrics['pnl_net']:.2f}",
            f"{metrics['pnl_percent']:.2f}%",
            f"{metrics['roi_net_percent']:.2f}%",
            f"{trade.duration.total_seconds()/60:.0f}min",
            trade.exit_reason,
            f"{capital_before:.2f}",
            f"{capital_after:.2f}",
            metrics['session'],
            f"{metrics['intensity']*100:.0f}%",
            "2.1%",  # Volatilité simulée
            "2.1B$", # Volume simulé
            "0.01%"  # Spread simulé
        ]
        
        print("   Ligne Google Sheets:")
        for i, value in enumerate(row_data[:10]):  # Premiers 10 champs
            print(f"     {chr(65+i)}: {value}")
        
        total_volume += trade.size
        total_fees += metrics['total_fees']
        total_pnl_net += metrics['pnl_net']
    
    # Résumé analyse
    print(f"\n💰 RÉSUMÉ ANALYSE:")
    print(f"   Volume total: {total_volume:,.2f} USDC")
    print(f"   Frais total: {total_fees:.2f} USDC")
    print(f"   P&L net: {total_pnl_net:.2f} USDC")
    print(f"   Frais/Volume: {(total_fees/total_volume)*100:.3f}%")
    
    return total_volume, total_fees, total_pnl_net

def create_analysis_formulas():
    """Créé les formules d'analyse automatique"""
    
    print(f"\n📊 FORMULES GOOGLE SHEETS POUR ANALYSE AUTOMATIQUE")
    print("="*55)
    
    analysis_formulas = {
        "Performance par paire": {
            "BTCUSDC Trades": '=COUNTIF(Trades!C:C,"BTCUSDC")',
            "BTCUSDC Volume": '=SUMIF(Trades!C:C,"BTCUSDC",Trades!E:E)', 
            "BTCUSDC P&L Net": '=SUMIF(Trades!C:C,"BTCUSDC",Trades!N:N)',
            "BTCUSDC Frais": '=SUMIF(Trades!C:C,"BTCUSDC",Trades!M:M)',
            "BTCUSDC Win Rate": '=COUNTIFS(Trades!C:C,"BTCUSDC",Trades!N:N,">0")/COUNTIF(Trades!C:C,"BTCUSDC")'
        },
        "Analyse horaire": {
            "Trades 10h": '=COUNTIFS(Trades!B:B,">=10:00:00",Trades!B:B,"<11:00:00")',
            "P&L 10h": '=SUMIFS(Trades!N:N,Trades!B:B,">=10:00:00",Trades!B:B,"<11:00:00")',
            "Volume 10h": '=SUMIFS(Trades!E:E,Trades!B:B,">=10:00:00",Trades!B:B,"<11:00:00")'
        },
        "KPIs globaux": {
            "Frais total": '=SUM(Trades!M:M)',
            "Volume total": '=SUM(Trades!E:E)', 
            "P&L net total": '=SUM(Trades!N:N)',
            "Ratio frais/volume": '=SUM(Trades!M:M)/SUM(Trades!E:E)',
            "ROI net moyen": '=AVERAGE(Trades!P:P)'
        }
    }
    
    for category, formulas in analysis_formulas.items():
        print(f"\n📈 {category.upper()}:")
        for name, formula in formulas.items():
            print(f"   {name}: {formula}")
    
    return analysis_formulas

def create_test_script():
    """Créé un script de test complet"""
    
    print(f"\n🧪 SCRIPT DE TEST GOOGLE SHEETS")
    print("="*35)
    
    test_code = '''
# Test des colonnes et formules Google Sheets
from utils.sheets_logger import SheetsLogger
import asyncio

async def test_enhanced_logging():
    """Test du logging amélioré"""
    
    # Initialisation
    sheets = SheetsLogger("credentials.json", os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"))
    
    # Test d'un trade avec toutes les métriques
    mock_trade = MockTrade(...)
    
    # Capital avant/après
    capital_before = 22819.0
    capital_after = 22879.0
    
    # Log avec métriques complètes
    await sheets.log_enhanced_trade(
        trade=mock_trade,
        action="CLOSE",
        capital_before=capital_before,
        capital_after=capital_after,
        fees_entry=5.0,
        fees_exit=5.01,
        session="EU_MORNING", 
        intensity=1.0,
        volatility=2.1,
        volume_24h="2.1B$",
        spread=0.01
    )
    
    print("✅ Test logging terminé - Vérifier Google Sheets")

# Lancer le test
asyncio.run(test_enhanced_logging())
'''
    
    print(test_code)
    
    return test_code

if __name__ == "__main__":
    print("🔍 ANALYSE ET TEST GOOGLE SHEETS POUR TRADING BOT")
    print("="*55)
    
    # 1. Structure des en-têtes
    headers = create_enhanced_sheets_headers()
    
    # 2. Simulation
    simulate_enhanced_logging()
    
    # 3. Formules d'analyse
    create_analysis_formulas()
    
    # 4. Script de test
    create_test_script()
    
    print(f"\n✅ ANALYSE TERMINÉE")
    print("📋 TODO:")
    print("   1. Mettre à jour SheetsLogger avec nouvelles colonnes")
    print("   2. Ajouter calcul frais détaillé")  
    print("   3. Créer onglets Performance par paire")
    print("   4. Tester avec trade réel")
    print("   5. Créer dashboard d'analyse automatique")
