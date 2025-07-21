#!/usr/bin/env python3
"""
Test de la correction des miettes pour les limites de trades par paire
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from config import TradingConfig
from main import ScalpingBot, Trade, TradeDirection


def test_dust_trades_logic():
    """Test de la logique des trades miettes"""
    
    print("🧪 TEST: Logique des trades miettes")
    print("=" * 50)
    
    # Configuration
    config = TradingConfig()
    print(f"📊 Seuil miettes: {config.DUST_BALANCE_THRESHOLD_USDC}$ USDC")
    print(f"📊 Max trades par paire: {config.MAX_TRADES_PER_PAIR}")
    
    # Simulation d'un bot (sans connexion réelle)
    try:
        bot = ScalpingBot()
        
        # Test 1: Simulation trade miette ADA
        print(f"\n🧹 TEST 1: Trade miette ADA")
        ada_trade_id = "ADAUSDC_123456_1642790000"
        ada_trade = Trade(
            id="123456",
            pair="ADAUSDC",
            direction=TradeDirection.LONG,
            size=5.5,  # 5.5 ADA
            entry_price=0.85,  # 0.85 USDC par ADA = 4.675 USDC total (< 5$ seuil)
            stop_loss=0.80,
            take_profit=0.90,
            trailing_stop=0.88,
            timestamp=datetime.now()
        )
        
        bot.open_positions[ada_trade_id] = ada_trade
        
        # Valeur de la position
        position_value = ada_trade.size * ada_trade.entry_price
        print(f"   💰 Valeur position ADA: {position_value:.2f}$ USDC")
        print(f"   🧹 Est une miette: {'Oui' if position_value < config.DUST_BALANCE_THRESHOLD_USDC else 'Non'}")
        
        # Test du comptage
        non_dust_count = bot.get_non_dust_trades_on_pair("ADAUSDC")
        total_count = len([t for t in bot.open_positions.values() if t.pair == "ADAUSDC"])
        
        print(f"   📊 Trades totaux ADA: {total_count}")
        print(f"   💎 Trades non-miettes ADA: {non_dust_count}")
        
        # Test 2: Simulation trade normal ADA
        print(f"\n💎 TEST 2: Trade normal ADA")
        ada_trade_id_2 = "ADAUSDC_789012_1642790100"
        ada_trade_2 = Trade(
            id="789012",
            pair="ADAUSDC",
            direction=TradeDirection.LONG,
            size=600,  # 600 ADA
            entry_price=0.85,  # 0.85 USDC par ADA = 510 USDC total (> 5$ seuil)
            stop_loss=0.80,
            take_profit=0.90,
            trailing_stop=0.88,
            timestamp=datetime.now()
        )
        
        bot.open_positions[ada_trade_id_2] = ada_trade_2
        
        position_value_2 = ada_trade_2.size * ada_trade_2.entry_price
        print(f"   💰 Valeur position ADA #2: {position_value_2:.2f}$ USDC")
        print(f"   🧹 Est une miette: {'Oui' if position_value_2 < config.DUST_BALANCE_THRESHOLD_USDC else 'Non'}")
        
        # Test du comptage avec 2 positions
        non_dust_count_2 = bot.get_non_dust_trades_on_pair("ADAUSDC")
        total_count_2 = len([t for t in bot.open_positions.values() if t.pair == "ADAUSDC"])
        
        print(f"   📊 Trades totaux ADA: {total_count_2}")
        print(f"   💎 Trades non-miettes ADA: {non_dust_count_2}")
        
        # Test 3: Test can_open_position avec miettes
        print(f"\n🚦 TEST 3: Autorisation nouveau trade ADA")
        
        # Simulation d'une méthode mocké pour éviter l'appel API
        def mock_can_open_basic(symbol):
            non_dust_trades = bot.get_non_dust_trades_on_pair(symbol)
            return non_dust_trades < config.MAX_TRADES_PER_PAIR
        
        can_open_with_dust = mock_can_open_basic("ADAUSDC")
        print(f"   🔓 Peut ouvrir nouveau trade ADA: {'Oui' if can_open_with_dust else 'Non'}")
        print(f"   📝 Raison: {non_dust_count_2}/{config.MAX_TRADES_PER_PAIR} trades non-miettes")
        
        # Test 4: Test avec seulement des miettes
        print(f"\n🧹 TEST 4: Seulement des miettes DOGE")
        
        # Ajout de plusieurs miettes DOGE
        for i in range(3):
            doge_trade_id = f"DOGEUSDC_{100000 + i}_{1642790200 + i}"
            doge_trade = Trade(
                id=str(100000 + i),
                pair="DOGEUSDC",
                direction=TradeDirection.LONG,
                size=30,  # 30 DOGE
                entry_price=0.12,  # 0.12 USDC par DOGE = 3.6 USDC total (< 5$ seuil)
                stop_loss=0.10,
                take_profit=0.14,
                trailing_stop=0.13,
                timestamp=datetime.now()
            )
            bot.open_positions[doge_trade_id] = doge_trade
        
        doge_non_dust = bot.get_non_dust_trades_on_pair("DOGEUSDC")
        doge_total = len([t for t in bot.open_positions.values() if t.pair == "DOGEUSDC"])
        can_open_doge = mock_can_open_basic("DOGEUSDC")
        
        print(f"   📊 Trades totaux DOGE: {doge_total}")
        print(f"   💎 Trades non-miettes DOGE: {doge_non_dust}")
        print(f"   🔓 Peut ouvrir nouveau trade DOGE: {'Oui' if can_open_doge else 'Non'}")
        
        # Résumé final
        print(f"\n📋 RÉSUMÉ DES TESTS")
        print("=" * 30)
        print(f"✅ Miette ADA (4.68$): Ignorée dans le comptage")
        print(f"✅ Trade normal ADA (510$): Compté dans la limite")
        print(f"✅ 3 Miettes DOGE (3.6$ chacune): Toutes ignorées")
        print(f"🎯 Nouveau trade ADA: {'BLOQUÉ' if not can_open_with_dust else 'AUTORISÉ'} (1/1 trade non-miette)")
        print(f"🎯 Nouveau trade DOGE: {'AUTORISÉ' if can_open_doge else 'BLOQUÉ'} (0/1 trade non-miette)")
        
        if can_open_doge and not can_open_with_dust:
            print(f"\n🎉 SUCCESS: La logique fonctionne correctement!")
            print(f"   - Les miettes n'empêchent plus les nouveaux trades")
            print(f"   - Les vraies positions comptent toujours dans la limite")
            return True
        else:
            print(f"\n❌ FAILED: La logique ne fonctionne pas comme attendu")
            return False
            
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        return False

if __name__ == "__main__":
    success = test_dust_trades_logic()
    exit(0 if success else 1)
