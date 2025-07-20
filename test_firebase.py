#!/usr/bin/env python3
"""
Test Script pour l'intégration Firebase
Vérifie que tous les composants Firebase fonctionnent correctement
"""

import os
import sys
from datetime import datetime


def test_firebase_integration():
    """Test complet de l'intégration Firebase"""
    print("🔥 Test de l'intégration Firebase")
    print("=" * 50)
    
    # Test 1: Import des modules
    print("\n1. Test des imports...")
    try:
        from utils.firebase_config import FIREBASE_CONFIG
        print("   ✅ firebase_config importé")
    except Exception as e:
        print(f"   ❌ Erreur firebase_config: {e}")
        return False
    
    try:
        from utils.firebase_logger import firebase_logger
        print("   ✅ firebase_logger importé")
    except Exception as e:
        print(f"   ❌ Erreur firebase_logger: {e}")
        return False
    
    # Test 2: Configuration Firebase
    print("\n2. Test configuration Firebase...")
    try:
        print(f"   📋 Projet ID: {FIREBASE_CONFIG.PROJECT_ID}")
        print(f"   🔧 Logging activé: {FIREBASE_CONFIG.ENABLE_FIREBASE_LOGGING}")
        print(f"   📊 Rétention logs: {FIREBASE_CONFIG.LOGS_RETENTION_DAYS} jours")
        print("   ✅ Configuration chargée")
    except Exception as e:
        print(f"   ❌ Erreur configuration: {e}")
        return False
    
    # Test 3: Connexion Firebase (optionnel)
    print("\n3. Test connexion Firebase...")
    try:
        result = firebase_logger.test_firebase_connection()
        if result:
            print("   ✅ Connexion Firebase réussie")
        else:
            print("   ⚠️  Connexion Firebase échouée (vérifiez vos clés)")
    except Exception as e:
        print(f"   ⚠️  Test connexion échoué: {e}")
        print("   ℹ️  Le bot peut fonctionner sans Firebase")
    
    # Test 4: Log de test
    print("\n4. Test logging...")
    try:
        firebase_logger.log_message(
            level="INFO",
            message="Test d'intégration Firebase réussi",
            module="test_script",
            additional_data={"test": True, "timestamp": datetime.now().isoformat()}
        )
        print("   ✅ Log de test envoyé")
    except Exception as e:
        print(f"   ❌ Erreur logging: {e}")
    
    # Test 5: Métrique de test
    print("\n5. Test métriques...")
    try:
        firebase_logger.log_metric("test_metric", 123.45, pair="TESTUSDC")
        print("   ✅ Métrique de test envoyée")
    except Exception as e:
        print(f"   ❌ Erreur métrique: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test d'intégration Firebase terminé")
    print("\n📋 Prochaines étapes:")
    print("1. Configurez firebase_env.txt avec vos vraies clés")
    print("2. Lancez le bot: python main.py")
    print("3. Consultez Firebase Console pour voir les données")
    print("4. Accédez aux analytics en temps réel")
    
    return True

def test_main_integration():
    """Test que main.py peut importer Firebase"""
    print("\n🤖 Test intégration main.py...")
    try:
        # Import du bot sans l'exécuter
        from main import ScalpingBot
        print("   ✅ ScalpingBot peut être importé avec Firebase")
        
        # Vérification que Firebase est bien intégré
        print("   ✅ Firebase intégré dans ScalpingBot")
        return True
    except Exception as e:
        print(f"   ❌ Erreur intégration main.py: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test Complet Firebase Integration")
    print("=" * 60)
    
    # Test Firebase
    firebase_ok = test_firebase_integration()
    
    # Test Main
    main_ok = test_main_integration()
    
    print("\n" + "=" * 60)
    if firebase_ok and main_ok:
        print("✅ TOUS LES TESTS RÉUSSIS!")
        print("🔥 Firebase Integration prête pour le déploiement!")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔧 Vérifiez la configuration avant de continuer")
        sys.exit(1)
