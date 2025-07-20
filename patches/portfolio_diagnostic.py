#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC COMPLET DU PORTEFEUILLE BINANCE
Analyse de tous les assets pour conversion optimale vers USDC
"""

import os

from binance.client import Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def analyze_full_portfolio():
    print("🔍 " + "="*60)
    print("📊 DIAGNOSTIC COMPLET DU PORTEFEUILLE BINANCE")
    print("🔍 " + "="*60)
    
    try:
        # Connexion Binance
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not api_secret:
            print("❌ ERREUR: Clés API manquantes")
            return
            
        client = Client(api_key, api_secret)
        
        # Récupérer les informations du compte
        account_info = client.get_account()
        
        print(f"\n💰 ANALYSE DES SOLDES:")
        print("="*40)
        
        total_btc_value = 0.0
        total_eur_value = 0.0
        assets_found = []
        
        # Récupérer les prix pour conversion
        all_prices = client.get_all_tickers()
        price_dict = {ticker['symbol']: float(ticker['price']) for ticker in all_prices}
        
        # Analyser chaque asset
        for balance in account_info['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0.001:  # Seuil minimal pour éviter les dust
                # Calculer la valeur en BTC
                btc_value = 0.0
                eur_value = 0.0
                
                if asset == 'BTC':
                    btc_value = total
                elif asset == 'EUR':
                    eur_value = total
                    # Convertir EUR en BTC
                    if 'BTCEUR' in price_dict:
                        btc_value = total / price_dict['BTCEUR']
                elif asset == 'USDC':
                    # Convertir USDC en EUR puis BTC
                    if 'EURUSDC' in price_dict:
                        eur_value = total / price_dict['EURUSDC']
                        if 'BTCEUR' in price_dict:
                            btc_value = eur_value / price_dict['BTCEUR']
                else:
                    # Essayer de trouver la paire vers BTC
                    symbol_btc = f"{asset}BTC"
                    symbol_usdt = f"{asset}USDT"
                    symbol_eur = f"{asset}EUR"
                    
                    if symbol_btc in price_dict:
                        btc_value = total * price_dict[symbol_btc]
                    elif symbol_usdt in price_dict and 'BTCUSDT' in price_dict:
                        usdt_value = total * price_dict[symbol_usdt]
                        btc_value = usdt_value / price_dict['BTCUSDT']
                    elif symbol_eur in price_dict and 'BTCEUR' in price_dict:
                        eur_value = total * price_dict[symbol_eur]
                        btc_value = eur_value / price_dict['BTCEUR']
                
                # Convertir BTC en EUR pour affichage
                if btc_value > 0 and 'BTCEUR' in price_dict:
                    eur_value = btc_value * price_dict['BTCEUR']
                
                if total > 0.01 or eur_value > 1:  # Seuil d'affichage
                    status = "🔓" if free > 0 else "🔒"
                    if locked > 0:
                        status += "🔒"
                    
                    print(f"   {status} {asset:<8} {total:>12.8f} (~{eur_value:>8.2f}€)")
                    
                    assets_found.append({
                        'asset': asset,
                        'total': total,
                        'free': free,
                        'locked': locked,
                        'btc_value': btc_value,
                        'eur_value': eur_value
                    })
                    
                total_btc_value += btc_value
                total_eur_value += eur_value
        
        print(f"\n💎 RÉSUMÉ GLOBAL:")
        print("="*25)
        print(f"   📊 Valeur totale: ~{total_eur_value:,.2f}€")
        print(f"   ₿  Équivalent BTC: {total_btc_value:.8f} BTC")
        
        if 'EURUSDC' in price_dict:
            usdc_equivalent = total_eur_value * price_dict['EURUSDC']
            print(f"   💵 Équivalent USDC: ~{usdc_equivalent:,.2f}$ USDC")
        
        # Recommandations de conversion
        print(f"\n🎯 PLAN DE CONVERSION VERS USDC:")
        print("="*35)
        
        conversion_steps = []
        
        for asset_info in sorted(assets_found, key=lambda x: x['eur_value'], reverse=True):
            asset = asset_info['asset']
            total = asset_info['total']
            free = asset_info['free']
            eur_value = asset_info['eur_value']
            
            if eur_value > 10:  # Worth converting
                if asset == 'USDC':
                    print(f"   ✅ {asset}: Déjà en USDC - {total:.2f}$")
                elif asset == 'EUR':
                    print(f"   🔄 {asset}: {total:.2f}€ → {asset}USDC (conversion directe)")
                    conversion_steps.append(f"Convertir {free:.2f}€ via EURUSDC")
                elif free > 0:  # Asset libre, convertible
                    # Chercher le meilleur chemin de conversion
                    direct_usdc = f"{asset}USDC"
                    via_btc = f"{asset}BTC"
                    via_usdt = f"{asset}USDT"
                    
                    if direct_usdc in price_dict:
                        print(f"   🔄 {asset}: {total:.6f} → {direct_usdc} (conversion directe)")
                        conversion_steps.append(f"Vendre {free:.6f} {asset} via {direct_usdc}")
                    elif via_usdt in price_dict:
                        print(f"   🔄 {asset}: {total:.6f} → USDT → USDC (2 étapes)")
                        conversion_steps.append(f"Vendre {free:.6f} {asset} via {via_usdt}, puis USDTUSDC")
                    elif via_btc in price_dict:
                        print(f"   🔄 {asset}: {total:.6f} → BTC → USDC (2 étapes)")
                        conversion_steps.append(f"Vendre {free:.6f} {asset} via {via_btc}, puis BTCUSDC")
                    else:
                        print(f"   ⚠️  {asset}: Chemin de conversion à déterminer manuellement")
                else:
                    print(f"   🔒 {asset}: {asset_info['locked']:.6f} bloqué - Annuler ordres d'abord")
        
        print(f"\n📋 ÉTAPES DE CONVERSION:")
        print("="*25)
        for i, step in enumerate(conversion_steps, 1):
            print(f"   {i}. {step}")
        
        print(f"\n🎯 OBJECTIF FINAL:")
        print("="*18)
        if 'EURUSDC' in price_dict:
            final_usdc = total_eur_value * price_dict['EURUSDC'] * 0.995  # -0.5% frais
            print(f"   💵 Capital USDC final: ~{final_usdc:,.2f}$ USDC")
            print(f"   🎯 Prêt pour trading haute liquidité!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    analyze_full_portfolio()
