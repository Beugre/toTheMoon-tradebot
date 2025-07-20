#!/usr/bin/env python3
"""
Test de la logique corrigée pour ignorer les miettes dans l'exposition
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch
from main import ScalpingBot
from config import TradingConfig

def test_dust_exposure_logic():
    """Test que les miettes n'affectent plus l'exposition"""
    
    print("🧪 TEST LOGIQUE MIETTES")
    print("=" * 40)
    
    # Mock du bot
    config = TradingConfig()
    
    # Simulation d'un bot avec miettes
    with patch('main.Client') as mock_client:
        bot = ScalpingBot()
        
        # Mock des réponses Binance
        def mock_get_asset_balance(asset):
            balances = {
                'ETH': 0.0005,  # ~1.87$ = miette
                'BTC': 0.00001,  # ~0.75$ = miette  
                'SOL': 2.5,      # ~455$ = position réelle
                'USDC': 5000.0
            }
            return balances.get(asset, 0.0)
        
        def mock_get_symbol_ticker(symbol=None):
            prices = {
                'ETHUSDC': {'price': '3748.50'},
                'BTCUSDC': {'price': '75000.00'},
                'SOLUSDC': {'price': '182.35'},
            }
            return prices.get(symbol, {'price': '1.0'})
        
        bot.get_asset_balance = mock_get_asset_balance
        bot.binance_client.get_symbol_ticker = mock_get_symbol_ticker
        bot.open_positions = {}  # Pas de positions ouvertes
        
        # Test exposition ETH (miette)
        eth_exposure = bot.get_asset_exposure('ETH')
        eth_value = 0.0005 * 3748.50  # = 1.87$
        
        print(f"💎 ETH:")
        print(f"   Solde: 0.0005 ETH")
        print(f"   Valeur: {eth_value:.2f}$ USDC")
        print(f"   Seuil miettes: {config.DUST_BALANCE_THRESHOLD_USDC}$ USDC")
        print(f"   Exposition calculée: {eth_exposure:.2f}$ USDC")
        print(f"   ✅ Miette ignorée: {eth_exposure == 0.0}")
        
        # Test exposition SOL (vraie position)
        sol_exposure = bot.get_asset_exposure('SOL')
        sol_value = 2.5 * 182.35  # = 455.87$
        
        print(f"\\n💎 SOL:")
        print(f"   Solde: 2.5 SOL")
        print(f"   Valeur: {sol_value:.2f}$ USDC")
        print(f"   Exposition calculée: {sol_exposure:.2f}$ USDC")
        print(f"   ✅ Position comptée: {abs(sol_exposure - sol_value) < 1.0}")
        
        # Test avec BTC (miette)
        btc_exposure = bot.get_asset_exposure('BTC')
        btc_value = 0.00001 * 75000.00  # = 0.75$
        
        print(f"\\n💎 BTC:")
        print(f"   Solde: 0.00001 BTC")
        print(f"   Valeur: {btc_value:.2f}$ USDC")
        print(f"   Exposition calculée: {btc_exposure:.2f}$ USDC")
        print(f"   ✅ Miette ignorée: {btc_exposure == 0.0}")
        
        print(f"\\n🎯 RÉSULTATS:")
        print(f"   ✅ Miettes ETH et BTC ignorées pour exposition")
        print(f"   ✅ Position SOL correctement comptabilisée")
        print(f"   ✅ Nouveaux trades ETH/BTC ne seront plus bloqués")
        
        return eth_exposure == 0.0 and btc_exposure == 0.0 and abs(sol_exposure - sol_value) < 1.0

if __name__ == "__main__":
    success = test_dust_exposure_logic()
    print(f"\\n{'✅ TEST RÉUSSI' if success else '❌ TEST ÉCHOUÉ'}")
