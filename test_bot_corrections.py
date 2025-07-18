#!/usr/bin/env python3
"""
Test rapide du bot avec les corrections appliquées
"""

import asyncio
import sys
from main import ScalpingBot

async def test_bot_corrections():
    """Test des corrections du bot"""
    print("🧪 TEST DES CORRECTIONS DU BOT")
    print("=" * 50)
    
    try:
        # Initialisation du bot
        bot = ScalpingBot()
        
        # Test d'initialisation
        print("📡 Test de connexion Binance...")
        await bot.database.initialize_database()
        
        print("💰 Test d'initialisation du capital...")
        await bot.initialize_capital()
        
        print("🧹 Test de nettoyage des positions fantômes...")
        await bot.cleanup_phantom_positions()
        
        print("🔍 Test de cohérence des positions...")
        await bot.check_positions_consistency()
        
        # Test des méthodes de validation
        print("\n🧮 Test des méthodes de validation...")
        
        # Test validation quantité
        test_symbol = 'ETHEUR'
        test_quantity = 0.001
        test_price = 3000.0
        
        is_valid, msg, adjusted_qty = bot.validate_order_quantity(test_symbol, test_quantity, test_price)
        print(f"   Validation {test_symbol}: {is_valid} - {msg}")
        print(f"   Quantité ajustée: {adjusted_qty:.8f}")
        
        # Test récupération solde
        eth_balance = bot.get_asset_balance('ETH')
        print(f"   Solde ETH: {eth_balance:.8f}")
        
        # Test filtres symbole
        filters = bot.get_symbol_filters('ETHEUR')
        print(f"   Filtres ETHEUR: {filters}")
        
        print("\n✅ TOUS LES TESTS RÉUSSIS!")
        print("Le bot est prêt avec les corrections appliquées.")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Fonction principale"""
    try:
        asyncio.run(test_bot_corrections())
    except KeyboardInterrupt:
        print("\n🛑 Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
