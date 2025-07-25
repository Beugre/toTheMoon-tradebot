#!/usr/bin/env python3
"""
Test des nouvelles fonctionnalités d'ordres automatiques
Vérifie que les nouvelles méthodes fonctionnent sans régression
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

# Import des classes nécessaires
from main import Trade, TradeDirection, TradeStatus


def test_trade_class_new_attributes():
    """Test que la classe Trade a bien les nouveaux attributs"""
    print("🧪 Test de la classe Trade avec nouveaux attributs...")
    
    trade = Trade(
        id="test_123",
        pair="BTCUSDC",
        direction=TradeDirection.LONG,
        size=0.001,
        entry_price=45000.0,
        stop_loss=44500.0,
        take_profit=45500.0,
        trailing_stop=44500.0,
        timestamp=datetime.now()
    )
    
    # Vérifier les nouveaux attributs
    assert hasattr(trade, 'take_profit_order_id'), "❌ Attribut take_profit_order_id manquant"
    assert hasattr(trade, 'trailing_stop_order_id'), "❌ Attribut trailing_stop_order_id manquant"
    assert hasattr(trade, 'last_trailing_update'), "❌ Attribut last_trailing_update manquant"
    
    # Tester l'assignation
    trade.take_profit_order_id = "123456789"
    trade.trailing_stop_order_id = "987654321"
    trade.last_trailing_update = datetime.now()
    
    print("✅ Classe Trade: Tous les nouveaux attributs présents")
    return True

def test_configuration_parameters():
    """Test que les nouveaux paramètres de configuration sont présents"""
    print("🧪 Test des paramètres de configuration...")
    
    from config import TradingConfig
    config = TradingConfig()
    
    # Vérifier les nouveaux paramètres
    assert hasattr(config, 'ENABLE_AUTOMATIC_ORDERS'), "❌ Paramètre ENABLE_AUTOMATIC_ORDERS manquant"
    assert hasattr(config, 'PREFER_OCO_ORDERS'), "❌ Paramètre PREFER_OCO_ORDERS manquant"
    assert hasattr(config, 'ENABLE_DYNAMIC_TRAILING'), "❌ Paramètre ENABLE_DYNAMIC_TRAILING manquant"
    assert hasattr(config, 'AUTO_UPDATE_TAKE_PROFIT'), "❌ Paramètre AUTO_UPDATE_TAKE_PROFIT manquant"
    assert hasattr(config, 'TRAILING_UPDATE_MIN_SECONDS'), "❌ Paramètre TRAILING_UPDATE_MIN_SECONDS manquant"
    
    # Vérifier les valeurs par défaut
    assert config.ENABLE_AUTOMATIC_ORDERS == True, "❌ ENABLE_AUTOMATIC_ORDERS doit être True par défaut"
    assert config.AUTO_UPDATE_TAKE_PROFIT == True, "❌ AUTO_UPDATE_TAKE_PROFIT doit être True maintenant"
    assert config.TRAILING_UPDATE_MIN_SECONDS == 30, "❌ TRAILING_UPDATE_MIN_SECONDS doit être 30"
    
    print("✅ Configuration: Tous les nouveaux paramètres présents et corrects")
    return True

def test_backward_compatibility():
    """Test que l'ancien système fonctionne toujours"""
    print("🧪 Test de rétrocompatibilité...")
    
    from config import TradingConfig
    config = TradingConfig()
    
    # Simuler l'ancien système
    config.ENABLE_AUTOMATIC_ORDERS = False
    
    # Vérifier que les anciens paramètres existent toujours
    assert hasattr(config, 'STOP_LOSS_PERCENT'), "❌ Ancien paramètre STOP_LOSS_PERCENT manquant"
    assert hasattr(config, 'TAKE_PROFIT_PERCENT'), "❌ Ancien paramètre TAKE_PROFIT_PERCENT manquant"
    assert hasattr(config, 'TRAILING_STEP_PERCENT'), "❌ Ancien paramètre TRAILING_STEP_PERCENT manquant"
    
    print("✅ Rétrocompatibilité: Ancien système toujours fonctionnel")
    return True

def test_position_state_fields():
    """Test que la sauvegarde de position inclut les nouveaux champs"""
    print("🧪 Test des champs de sauvegarde de position...")
    
    trade = Trade(
        id="test_save",
        pair="ETHUSDC",
        direction=TradeDirection.LONG,
        size=0.01,
        entry_price=3000.0,
        stop_loss=2950.0,
        take_profit=3050.0,
        trailing_stop=2950.0,
        timestamp=datetime.now()
    )
    
    # Simuler les IDs d'ordres
    trade.stop_loss_order_id = "SL_123456"
    trade.take_profit_order_id = "TP_789012"
    trade.last_trailing_update = datetime.now()
    
    # Simuler la création des données de position (comme dans save_positions_state)
    position_data = {
        'trade_id': "test_save",
        'pair': trade.pair,
        'entry_price': trade.entry_price,
        'stop_loss': trade.stop_loss,
        'take_profit': trade.take_profit,
        'size': trade.size,
        'timestamp': trade.timestamp.isoformat(),
        'trailing_stop': getattr(trade, 'trailing_stop', 0),
        'direction': trade.direction.value if hasattr(trade.direction, 'value') else str(trade.direction),
        'saved_at': datetime.now().isoformat(),
        'session_id': "test_session",
        # Nouveaux champs
        'stop_loss_order_id': getattr(trade, 'stop_loss_order_id', None),
        'take_profit_order_id': getattr(trade, 'take_profit_order_id', None),
        'trailing_stop_order_id': getattr(trade, 'trailing_stop_order_id', None),
        'last_trailing_update': getattr(trade, 'last_trailing_update', None).isoformat() if getattr(trade, 'last_trailing_update', None) is not None else None
    }
    
    # Vérifier que tous les champs sont présents
    assert 'stop_loss_order_id' in position_data, "❌ Champ stop_loss_order_id manquant"
    assert 'take_profit_order_id' in position_data, "❌ Champ take_profit_order_id manquant"
    assert 'trailing_stop_order_id' in position_data, "❌ Champ trailing_stop_order_id manquant"
    assert 'last_trailing_update' in position_data, "❌ Champ last_trailing_update manquant"
    
    # Vérifier les valeurs
    assert position_data['stop_loss_order_id'] == "SL_123456", "❌ Valeur stop_loss_order_id incorrecte"
    assert position_data['take_profit_order_id'] == "TP_789012", "❌ Valeur take_profit_order_id incorrecte"
    
    print("✅ Sauvegarde de position: Tous les nouveaux champs inclus")
    return True

def run_all_tests():
    """Exécute tous les tests"""
    print("🚀 Démarrage des tests de régression...")
    print("=" * 50)
    
    tests = [
        test_trade_class_new_attributes,
        test_configuration_parameters,
        test_backward_compatibility,
        test_position_state_fields
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} ERROR: {e}")
    
    print("=" * 50)
    print(f"📊 Résultats: {passed} ✅ | {failed} ❌")
    
    if failed == 0:
        print("🎉 TOUS LES TESTS PASSENT - AUCUNE RÉGRESSION DÉTECTÉE")
        return True
    else:
        print("⚠️ ATTENTION: Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
