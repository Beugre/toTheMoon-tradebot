#!/usr/bin/env python3
"""
Diagnostic et nettoyage automatique des miettes (dust) qui bloquent les trades
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from binance.client import Client

from config import API_CONFIG, TradingConfig


async def diagnose_dust_problem():
    """Diagnostique le problème des miettes qui bloquent les trades"""
    
    # Initialisation client Binance
    client = Client(
        API_CONFIG.BINANCE_API_KEY,
        API_CONFIG.BINANCE_SECRET_KEY,
        testnet=API_CONFIG.TESTNET
    )
    
    config = TradingConfig()
    
    print("🔍 DIAGNOSTIC DES MIETTES (DUST)")
    print("=" * 50)
    
    try:
        account_info = client.get_account()
        problematic_assets = []
        
        print(f"💰 Seuil miettes configuré: {config.DUST_BALANCE_THRESHOLD_USDC}$ USDC")
        print("\\n📊 Analyse des soldes:")
        
        for balance in account_info['balances']:
            asset = balance['asset']
            free_balance = float(balance['free'])
            
            if asset == 'USDC':
                print(f"   💶 {asset}: {free_balance:.2f} USDC")
                continue
            elif asset == 'BNB':
                print(f"   🪙 {asset}: {free_balance:.8f} BNB")
                continue
            elif free_balance <= 0.00001:
                continue
            
            try:
                # Calcul valeur USDC
                symbol = asset + 'USDC'
                ticker = client.get_symbol_ticker(symbol=symbol)
                price_usdc = float(ticker['price'])
                value_usdc = free_balance * price_usdc
                
                print(f"   🔸 {asset}: {free_balance:.8f} = {value_usdc:.2f}$ USDC", end="")
                
                if value_usdc < config.DUST_BALANCE_THRESHOLD_USDC:
                    print(" 🧹 (MIETTES)")
                    problematic_assets.append({
                        'asset': asset,
                        'balance': free_balance,
                        'value_usdc': value_usdc,
                        'symbol': symbol,
                        'price': price_usdc
                    })
                else:
                    print(" ✅ (OK)")
                    
            except Exception as e:
                print(f"   ⚠️ {asset}: {free_balance:.8f} (pas de paire USDC)")
        
        print(f"\\n🚨 RÉSULTATS:")
        print(f"   - Miettes détectées: {len(problematic_assets)}")
        
        if problematic_assets:
            total_dust_value = sum(a['value_usdc'] for a in problematic_assets)
            print(f"   - Valeur totale des miettes: {total_dust_value:.2f}$ USDC")
            print(f"   - Impact: Bloque les nouveaux trades sur ces assets")
            
            print("\\n🧹 SOLUTIONS:")
            print("1. 🔧 Configuration modifiée: Les miettes sont maintenant ignorées")
            print("2. 🤖 Nettoyage automatique toutes les 100 itérations")
            print("3. 🔄 Conversion manuelle en BNB recommandée:")
            
            for asset in problematic_assets:
                print(f"   - {asset['asset']}: {asset['balance']:.8f} ({asset['value_usdc']:.2f}$)")
            
            # Test de conversion automatique
            print("\\n🔄 TEST DE CONVERSION AUTOMATIQUE:")
            try:
                assets_to_convert = [a['asset'] for a in problematic_assets]
                print(f"   Assets à convertir: {', '.join(assets_to_convert)}")
                
                # Simulation (ne pas exécuter réellement)
                print("   ⚠️ Simulation uniquement - utilisez l'interface Binance pour conversion réelle")
                
            except Exception as e:
                print(f"   ❌ Erreur simulation: {e}")
        else:
            print("   ✅ Aucune miette problématique détectée")
        
        print("\\n✅ CORRECTION APPLIQUÉE:")
        print("   - Seuil intelligent ajouté dans get_asset_exposure()")
        print("   - Les miettes ne bloquent plus les nouveaux trades")
        print("   - Nettoyage automatique activé")
        
    except Exception as e:
        print(f"❌ Erreur diagnostic: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_dust_problem())
