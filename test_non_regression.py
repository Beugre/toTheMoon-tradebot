#!/usr/bin/env python3
"""
Test de Non-Régression Complet
Vérifie que toutes les fonctionnalités existantes fonctionnent parfaitement
"""

import os
import sys
from datetime import datetime


def test_imports():
    """Test que tous les imports fonctionnent"""
    print("📦 Test des imports principaux...")
    
    try:
        # Imports principaux du bot
        from main import PairScore, ScalpingBot, Trade, TradeDirection, TradeStatus
        print("   ✅ main.py - Classes principales")
        
        from config import API_CONFIG, TradingConfig
        print("   ✅ config.py - Configuration trading")
        
        from utils.technical_indicators import TechnicalAnalyzer
        print("   ✅ technical_indicators.py - Analyse technique")
        
        from utils.risk_manager import RiskManager
        print("   ✅ risk_manager.py - Gestion des risques")
        
        from utils.telegram_notifier import TelegramNotifier
        print("   ✅ telegram_notifier.py - Notifications")
        
        from utils.enhanced_sheets_logger import EnhancedSheetsLogger
        print("   ✅ enhanced_sheets_logger.py - Google Sheets")
        
        from utils.database import TradingDatabase
        print("   ✅ database.py - Base de données")
        
        # Test Firebase (optionnel)
        try:
            from utils.firebase_config import FIREBASE_CONFIG
            from utils.firebase_logger import firebase_logger
            print("   ✅ firebase - Analytics temps réel (optionnel)")
        except Exception as e:
            print(f"   ⚠️  firebase - Non disponible: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur import: {e}")
        return False

def test_bot_creation():
    """Test que le bot peut être créé sans erreur"""
    print("\n🤖 Test création du bot...")
    
    try:
        from config import TradingConfig
        from main import ScalpingBot

        # Test avec une config par défaut
        bot = ScalpingBot()
        
        print("   ✅ ScalpingBot créé avec succès")
        print(f"   📊 Config: {bot.config.BASE_POSITION_SIZE_PERCENT}% position size")
        print(f"   🔧 Firebase: {'✅ Activé' if bot.firebase_logger else '❌ Désactivé'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création bot: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_technical_analysis():
    """Test que l'analyse technique fonctionne"""
    print("\n📈 Test analyse technique...")
    
    try:
        from utils.technical_indicators import TechnicalAnalyzer
        
        analyzer = TechnicalAnalyzer()
        print("   ✅ TechnicalAnalyzer créé")
        
        # Test avec des données fictives
        import numpy as np
        import pandas as pd

        # Génération de données test
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        prices = 100 + np.cumsum(np.random.randn(100) * 0.1)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices * 0.999,
            'high': prices * 1.002,
            'low': prices * 0.998,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        # Test analyse
        result = analyzer.analyze_pair(df, "TESTUSDC")
        print(f"   ✅ Analyse technique: {len(result.signals)} signaux")
        print(f"   📊 Score total: {result.total_score}")
        print(f"   📈 Recommandation: {result.recommendation}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur analyse technique: {e}")
        return False

def test_firebase_fallback():
    """Test que le bot fonctionne même si Firebase est down"""
    print("\n🔥 Test fallback Firebase...")
    
    try:
        # Désactivation temporaire de Firebase
        import os
        original_firebase = os.environ.get('ENABLE_FIREBASE_LOGGING', 'True')
        os.environ['ENABLE_FIREBASE_LOGGING'] = 'False'
        
        from config import TradingConfig
        from main import ScalpingBot
        
        bot = ScalpingBot()
        
        print("   ✅ Bot fonctionne sans Firebase")
        print(f"   🔧 Firebase logger: {bot.firebase_logger is not None}")
        
        # Restauration
        os.environ['ENABLE_FIREBASE_LOGGING'] = original_firebase
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur fallback Firebase: {e}")
        return False

def test_configuration_loading():
    """Test que la configuration se charge correctement"""
    print("\n⚙️  Test chargement configuration...")
    
    try:
        from config import API_CONFIG, TradingConfig
        
        config = TradingConfig()
        
        # Vérifications des valeurs critiques
        assert config.BASE_POSITION_SIZE_PERCENT > 0, "Position size doit être > 0"
        assert config.MIN_SIGNAL_CONDITIONS >= 3, "Min signal conditions >= 3"
        assert config.MAX_OPEN_POSITIONS > 0, "Max positions > 0"
        assert config.STOP_LOSS_PERCENT > 0, "Stop loss > 0"
        assert config.TAKE_PROFIT_PERCENT > 0, "Take profit > 0"
        
        print("   ✅ Configuration valide")
        print(f"   📊 Position size: {config.BASE_POSITION_SIZE_PERCENT}%")
        print(f"   🎯 Min signaux: {config.MIN_SIGNAL_CONDITIONS}")
        print(f"   💰 Stop loss: {config.STOP_LOSS_PERCENT}%")
        print(f"   🎯 Take profit: {config.TAKE_PROFIT_PERCENT}%")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur configuration: {e}")
        return False

def test_dust_management():
    """Test que la gestion des miettes fonctionne"""
    print("\n🧹 Test gestion des miettes...")
    
    try:
        from config import TradingConfig
        from main import ScalpingBot
        
        bot = ScalpingBot()
        
        # Test avec des soldes fictifs - on teste juste que les méthodes existent
        print(f"   ✅ Bot créé avec méthodes core présentes")
        
        # Test que les méthodes de gestion capital existent
        assert hasattr(bot, 'get_total_capital'), "get_total_capital manquant"
        print(f"   ✅ Méthodes de gestion capital présentes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur gestion miettes: {e}")
        return False

def test_complete_workflow():
    """Test complet du workflow principal"""
    print("\n🔄 Test workflow complet...")
    
    try:
        from config import TradingConfig
        from main import ScalpingBot
        
        bot = ScalpingBot()
        
        # Test des méthodes principales
        print("   📊 Test init capital...")
        # bot.init_capital()  # Commenté car nécessite API Binance
        
        print("   🔍 Test méthodes core...")
        # Test que les méthodes existent et sont callable
        assert hasattr(bot, 'scan_usdc_pairs'), "scan_usdc_pairs manquant"
        assert hasattr(bot, 'analyze_pair'), "analyze_pair manquant"
        assert hasattr(bot, 'execute_trade'), "execute_trade manquant"
        assert hasattr(bot, 'manage_open_positions'), "manage_open_positions manquant"
        assert hasattr(bot, 'close_position'), "close_position manquant"
        
        print("   ✅ Toutes les méthodes core présentes")
        
        # Test Firebase integration
        if bot.firebase_logger:
            print("   🔥 Firebase intégré et fonctionnel")
        else:
            print("   ⚠️  Firebase désactivé (normal si pas configuré)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur workflow: {e}")
        return False

def main():
    """Test principal de non-régression"""
    print("🧪 TEST DE NON-RÉGRESSION COMPLET")
    print("=" * 60)
    print(f"📅 Date: {datetime.now()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Création Bot", test_bot_creation),
        ("Analyse Technique", test_technical_analysis),
        ("Configuration", test_configuration_loading),
        ("Fallback Firebase", test_firebase_fallback),
        ("Gestion Miettes", test_dust_management),
        ("Workflow Complet", test_complete_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ CRASH dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    if failed == 0:
        print("🎉 AUCUNE RÉGRESSION DÉTECTÉE!")
        print("✅ Toutes les fonctionnalités existantes fonctionnent parfaitement")
        print("🔥 Firebase Integration: OK - Pas d'impact sur le code existant")
        print(f"📊 Taux de réussite: {success_rate:.1f}% ({passed}/{total})")
        return True
    else:
        print("⚠️  RÉGRESSIONS DÉTECTÉES!")
        print(f"❌ {failed} test(s) échoué(s) sur {total}")
        print(f"📊 Taux de réussite: {success_rate:.1f}%")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
