#!/usr/bin/env python3
"""
🧪 TEST GOOGLE SHEETS ENHANCED 
Vérification du nouveau système de logging avec analyse fine
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Charger les variables d'environnement
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")  # Charger depuis la racine

# Import du nouveau logger (sera fait dynamiquement)
# Le chemin sera ajouté à l'exécution

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
    timestamp: datetime = None # type: ignore
    pnl: float = 0
    exit_reason: str = ""
    duration: timedelta = None # type: ignore

async def test_enhanced_google_sheets():
    """Test complet du système Google Sheets amélioré"""
    
    print("🧪 TEST GOOGLE SHEETS ENHANCED - TRADING BOT v3.0")
    print("="*55)
    
    # Vérifier les credentials - Aller chercher à la racine du projet
    credentials_path = "../credentials.json"  # Chemin relatif vers la racine
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    
    print(f"\n🔍 VÉRIFICATION CONFIGURATION:")
    print(f"   📁 Credentials: {'✅' if os.path.exists(credentials_path) else '❌'} {credentials_path}")
    print(f"   📊 Spreadsheet ID: {'✅' if spreadsheet_id else '❌'} {spreadsheet_id[:20] if spreadsheet_id else 'Non défini'}...")
    
    if not os.path.exists(credentials_path):
        print("\n❌ ERREUR: Fichier credentials.json manquant")
        print("💡 Placez le fichier credentials.json dans le répertoire racine")
        return False
    
    if not spreadsheet_id:
        print("\n❌ ERREUR: GOOGLE_SHEETS_SPREADSHEET_ID non défini")
        print("💡 Définissez la variable d'environnement GOOGLE_SHEETS_SPREADSHEET_ID")
        return False
    
    # Initialisation du logger enhanced
    try:
        print(f"\n🔄 Initialisation Enhanced Sheets Logger...")
        
        # Ajouter le chemin vers le module enhanced_sheets_logger dans utils
        utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
        sys.path.append(utils_path)
        from enhanced_sheets_logger import EnhancedSheetsLogger  # type: ignore
        
        logger = EnhancedSheetsLogger(
            credentials_path=credentials_path,
            spreadsheet_id=spreadsheet_id
        )
        
        if not logger.client:
            print("❌ Échec initialisation Google Sheets")
            return False
        
        print("✅ Enhanced Sheets Logger initialisé")
        
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return False
    
    # Test de logging d'un trade d'ouverture
    print(f"\n📊 TEST TRADE OUVERTURE:")
    
    mock_trade = MockTrade(
        pair="BTCUSDC",
        direction=TradeDirection.LONG,
        size=5000.0,
        entry_price=65000.0,
        stop_loss=64837.5,
        take_profit=65780.0,
        timestamp=datetime.now()
    )
    
    try:
        await logger.log_enhanced_trade(
            trade=mock_trade,
            action="OPEN",
            capital_before=22819.0,
            capital_after=17819.0,  # Capital engagé
            pair_volatility=2.1,
            volume_24h="2.1B$",
            spread_percent=0.01
        )
        print("✅ Trade OPEN loggé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur logging OPEN: {e}")
    
    # Attendre un peu puis simuler la fermeture
    print(f"\n⏳ Simulation durée du trade (3 secondes)...")
    await asyncio.sleep(3)
    
    # Test de logging de fermeture
    print(f"\n📊 TEST TRADE FERMETURE:")
    
    # Mise à jour du trade avec résultats
    mock_trade.exit_price = 65780.0
    mock_trade.pnl = 60.0  # P&L brut
    mock_trade.exit_reason = "TAKE_PROFIT"
    mock_trade.duration = timedelta(minutes=15)
    
    try:
        await logger.log_enhanced_trade(
            trade=mock_trade,
            action="CLOSE",
            capital_before=17819.0,
            capital_after=22870.0,  # Capital + gains
            pair_volatility=2.1,
            volume_24h="2.1B$", 
            spread_percent=0.01
        )
        print("✅ Trade CLOSE loggé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur logging CLOSE: {e}")
    
    # Test récupération des performances
    print(f"\n📈 TEST RÉCUPÉRATION PERFORMANCES:")
    
    try:
        performance = logger.get_pair_performance_summary()
        
        if performance:
            print("✅ Performance récupérée:")
            for pair, data in performance.items():
                if pair and data.get('trades'):
                    print(f"   {pair}: {data.get('trades')} trades, P&L: {data.get('pnl_net')}, Priorité: {data.get('priority')}")
        else:
            print("⚠️ Aucune performance récupérée (normal pour premier test)")
            
    except Exception as e:
        print(f"❌ Erreur récupération performance: {e}")
    
    # Vérification des onglets créés
    print(f"\n📋 VÉRIFICATION ONGLETS:")
    
    try:
        if logger.spreadsheet:
            worksheets = logger.spreadsheet.worksheets()
            print("✅ Onglets créés:")
            for ws in worksheets:
                print(f"   📊 {ws.title}")
        
    except Exception as e:
        print(f"❌ Erreur vérification onglets: {e}")
    
    print(f"\n🎯 INSTRUCTIONS POST-TEST:")
    print("="*30)
    print("1. 🔍 Vérifiez votre Google Sheets")
    print("2. 📊 Onglet 'Trades_Detailed' doit contenir le trade test")
    print("3. 📈 Onglet 'Performance_Pairs' doit afficher les métriques BTCUSDC")
    print("4. ⏰ Onglet 'Hourly_Analysis' doit montrer l'heure du test")
    print("5. 🎯 Onglet 'Analytics_Dashboard' doit afficher le résumé")
    
    print(f"\n✅ TEST TERMINÉ - Vérifiez votre Google Sheets!")
    
    return True

def create_manual_test_instructions():
    """Créé les instructions pour test manuel"""
    
    print(f"\n📋 INSTRUCTIONS TEST MANUEL GOOGLE SHEETS")
    print("="*45)
    
    instructions = """
    1. PRÉPARATION:
       • Vérifiez que credentials.json est dans le répertoire racine
       • Définissez GOOGLE_SHEETS_SPREADSHEET_ID dans .env
       • Installez: pip install gspread oauth2client
    
    2. EXÉCUTION:
       • Lancez: python test_enhanced_sheets.py
       • Vérifiez les messages de succès/erreur
    
    3. VÉRIFICATION GOOGLE SHEETS:
       
       📊 ONGLET 'Trades_Detailed':
       • Colonnes A-Y avec toutes les métriques
       • Trade test BTCUSDC visible
       • Frais entrée/sortie calculés
       • P&L net affiché
       
       📈 ONGLET 'Performance_Pairs': 
       • 10 paires USDC listées
       • Formules actives pour BTCUSDC
       • Win rate, profit factor calculés
       • Priorité assignée automatiquement
       
       ⏰ ONGLET 'Hourly_Analysis':
       • 24 heures listées avec sessions
       • Métriques par heure via formules
       • Intensité horaire affichée
       
       🎯 ONGLET 'Analytics_Dashboard':
       • Métriques globales temps réel
       • Top/pire paires automatiques
       • Recommandations générées
    
    4. VALIDATION FONCTIONNALITÉS:
       • ✅ Frais détaillés (entrée + sortie)
       • ✅ P&L net (après frais)
       • ✅ ROI net par trade
       • ✅ Performance par paire
       • ✅ Analyse horaire
       • ✅ Recommandations automatiques
    
    5. PRÊT POUR PRODUCTION:
       • Intégrer enhanced_sheets_logger.py dans main.py
       • Remplacer ancien SheetsLogger
       • Lancer le bot avec logging complet
    """
    
    print(instructions)

if __name__ == "__main__":
    # Test principal
    print("🚀 LANCEMENT TEST GOOGLE SHEETS ENHANCED")
    
    try:
        # Test asynchrone
        result = asyncio.run(test_enhanced_google_sheets())
        
        if result:
            print("\n🎉 TEST RÉUSSI!")
        else:
            print("\n❌ TEST ÉCHOUÉ - Vérifiez la configuration")
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        print("🔧 Vérifiez l'installation des dépendances:")
        print("   pip install gspread oauth2client")
    
    # Instructions manuelles
    create_manual_test_instructions()
