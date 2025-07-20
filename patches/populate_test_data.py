#!/usr/bin/env python3
"""
Ajout de trades de test pour valider les formules Google Sheets
"""

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Ajouter le chemin vers utils
utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
sys.path.insert(0, utils_path)

# Charger les variables d'environnement
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

from enhanced_sheets_logger import EnhancedSheetsLogger  # type: ignore


class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

@dataclass
class MockTrade:
    """Trade simulé pour test"""
    pair: str
    direction: TradeDirection
    size: float
    entry_price: float
    exit_price: float = 0
    stop_loss: float = 0
    take_profit: float = 0
    timestamp: datetime = None  # type: ignore
    pnl: float = 0
    exit_reason: str = ""
    duration: str = ""

async def populate_test_data():
    """Ajoute plusieurs trades de test pour valider les formules"""
    
    print("📊 AJOUT DE TRADES DE TEST POUR VALIDATION FORMULES")
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
    
    # Création de trades de test diversifiés
    test_trades = [
        # BTCUSDC - Profitable
        MockTrade("BTCUSDC", TradeDirection.LONG, 1000, 65000, 65780, 64837, 65780, 
                 datetime.now() - timedelta(hours=2), 780, "TAKE_PROFIT", "1h 45m"),
        
        # ETHUSDC - Perte
        MockTrade("ETHUSDC", TradeDirection.SHORT, 800, 3200, 3150, 3264, 3168, 
                 datetime.now() - timedelta(hours=1, minutes=30), -50, "STOP_LOSS", "45m"),
        
        # SOLUSDC - Profitable  
        MockTrade("SOLUSDC", TradeDirection.LONG, 600, 140, 141.68, 139.3, 141.4, 
                 datetime.now() - timedelta(hours=1), 1008, "TAKE_PROFIT", "1h 10m"),
        
        # XRPUSDC - Break even
        MockTrade("XRPUSDC", TradeDirection.SHORT, 500, 0.52, 0.5198, 0.5304, 0.5148, 
                 datetime.now() - timedelta(minutes=45), -1, "MANUAL", "30m"),
        
        # DOGEUSDC - Profitable
        MockTrade("DOGEUSDC", TradeDirection.LONG, 400, 0.12, 0.1214, 0.1194, 0.1214, 
                 datetime.now() - timedelta(minutes=20), 56, "TAKE_PROFIT", "15m"),
        
        # ADAUSDC - En cours (pas de sortie)
        MockTrade("ADAUSDC", TradeDirection.LONG, 300, 0.45, 0, 0.4477, 0.454, 
                 datetime.now() - timedelta(minutes=5)),
    ]
    
    print(f"\n📈 AJOUT DE {len(test_trades)} TRADES DE TEST")
    
    for i, trade in enumerate(test_trades, 1):
        try:
            if trade.exit_price > 0:
                # Trade complet (ouverture + fermeture)
                print(f"   {i}. {trade.pair} {trade.direction.value} - COMPLET")
                await logger.log_enhanced_trade(trade, "OPEN", 22000, 21000)
                await logger.log_enhanced_trade(trade, "CLOSE", 21000, 22000 + trade.pnl)
            else:
                # Trade en cours (ouverture seulement)
                print(f"   {i}. {trade.pair} {trade.direction.value} - EN COURS")
                await logger.log_enhanced_trade(trade, "OPEN", 22000, 21700)
                
        except Exception as e:
            print(f"   ❌ Erreur trade {trade.pair}: {e}")
    
    print(f"\n🎯 VALIDATION DES ONGLETS:")
    print(f"   📊 Trades_Detailed: {len(test_trades)} trades ajoutés")
    print(f"   📈 Performance_Pairs: Formules calculées automatiquement")
    print(f"   ⏰ Hourly_Analysis: Répartition horaire visible")
    print(f"   🎯 Analytics_Dashboard: KPI mis à jour")
    
    print(f"\n✅ DONNÉES DE TEST AJOUTÉES!")
    print(f"📋 Vérifiez votre Google Sheets pour voir les formules actives")
    print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(populate_test_data())
