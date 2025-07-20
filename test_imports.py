#!/usr/bin/env python3
"""
Test de base pour identifier les problèmes d'import
"""

print("🔍 Test d'imports étape par étape")
print("=" * 40)

def test_import(module_name, from_module=None):
    """Test d'import sécurisé"""
    try:
        if from_module:
            exec(f"from {from_module} import {module_name}")
            print(f"   ✅ {module_name} depuis {from_module}")
        else:
            exec(f"import {module_name}")
            print(f"   ✅ {module_name}")
        return True
    except Exception as e:
        print(f"   ❌ {module_name}: {e}")
        return False

# Test imports de base
print("\n1. Modules Python standard...")
test_import("os")
test_import("sys")
test_import("datetime")
test_import("asyncio")

print("\n2. Modules trading...")
test_import("ccxt")
test_import("binance")
test_import("pandas")
test_import("numpy")

print("\n3. Modules du bot...")
test_import("config")
test_import("trading_hours")

print("\n4. Modules utils...")
test_import("TechnicalAnalyzer", "utils.technical_indicators")
test_import("RiskManager", "utils.risk_manager")
test_import("TelegramNotifier", "utils.telegram_notifier")

print("\n5. Firebase (optionnel)...")
test_import("firebase_admin")
test_import("FIREBASE_CONFIG", "utils.firebase_config")
test_import("firebase_logger", "utils.firebase_logger")

print("\n6. Main module...")
if test_import("main"):
    print("   🎯 Test création ScalpingBot...")
    try:
        from main import ScalpingBot
        bot = ScalpingBot()
        print("   ✅ ScalpingBot créé avec succès")
        print(f"   🔧 Firebase: {'Activé' if bot.firebase_logger else 'Désactivé'}")
    except Exception as e:
        print(f"   ❌ Erreur ScalpingBot: {e}")

print("\n" + "=" * 40)
print("🎯 Test d'imports terminé")
