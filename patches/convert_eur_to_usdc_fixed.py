#!/usr/bin/env python3
"""
🔧 CONVERSION EUR → USDC AVEC GESTION DES FILTRES
Script corrigé pour respecter les contraintes Binance
"""

import math
import os
import time

from binance.client import Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def convert_eur_to_usdc_fixed():
    print("💱 === CONVERSION EUR → USDC (VERSION CORRIGÉE) ===")
    print()
    
    try:
        # Connexion Binance
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not api_secret:
            print("❌ ERREUR: Clés API manquantes")
            return False
            
        client = Client(api_key, api_secret)
        
        # Récupérer les informations sur la paire EURUSDC
        exchange_info = client.get_exchange_info()
        symbol_info = None
        
        for symbol in exchange_info['symbols']:
            if symbol['symbol'] == 'EURUSDC':
                symbol_info = symbol
                break
        
        if not symbol_info:
            print("❌ Paire EURUSDC non trouvée")
            return False
        
        # Analyser les filtres
        lot_size_filter = None
        min_notional_filter = None
        
        for filter_item in symbol_info['filters']:
            if filter_item['filterType'] == 'LOT_SIZE':
                lot_size_filter = filter_item
            elif filter_item['filterType'] == 'MIN_NOTIONAL':
                min_notional_filter = filter_item
        
        print(f"🔍 INFORMATIONS PAIRE EURUSDC:")
        print(f"   Status: {symbol_info['status']}")
        print(f"   Base Asset: {symbol_info['baseAsset']}")
        print(f"   Quote Asset: {symbol_info['quoteAsset']}")
        
        if lot_size_filter:
            min_qty = float(lot_size_filter['minQty'])
            max_qty = float(lot_size_filter['maxQty'])
            step_size = float(lot_size_filter['stepSize'])
            
            print(f"   📏 Quantité min: {min_qty}")
            print(f"   📏 Quantité max: {max_qty}")
            print(f"   📏 Step size: {step_size}")
        
        if min_notional_filter:
            min_notional = float(min_notional_filter['minNotional'])
            print(f"   💰 Valeur minimale: {min_notional} USDC")
        
        # Vérifier le solde EUR
        account_info = client.get_account()
        eur_balance = 0.0
        
        for balance in account_info['balances']:
            if balance['asset'] == 'EUR':
                eur_balance = float(balance['free'])
                break
        
        if eur_balance < min_qty: # type: ignore
            print(f"❌ Solde EUR insuffisant: {eur_balance:.2f}€ (min: {min_qty}€)") # type: ignore
            return False
        
        print(f"\n💶 Solde EUR actuel: {eur_balance:.8f}€")
        
        # Vérifier le taux EUR/USDC
        try:
            ticker = client.get_symbol_ticker(symbol='EURUSDC')
            eur_usdc_rate = float(ticker['price'])
            print(f"💱 Taux EUR/USDC: {eur_usdc_rate:.6f}")
        except Exception as e:
            print(f"❌ Impossible de récupérer le taux EUR/USDC: {e}")
            return False
        
        # Ajuster la quantité selon les filtres
        # Garder une marge pour les frais
        eur_to_sell = eur_balance * 0.999
        
        # Arrondir selon le step_size
        if lot_size_filter:
            # Calculer le nombre de steps
            steps = math.floor(eur_to_sell / step_size) # type: ignore
            eur_to_sell = steps * step_size # type: ignore
            
            # Vérifier les limites
            if eur_to_sell < min_qty: # type: ignore
                eur_to_sell = min_qty # type: ignore
            if eur_to_sell > max_qty:   # type: ignore
                eur_to_sell = max_qty # type: ignore
            if eur_to_sell > eur_balance:
                eur_to_sell = eur_balance
        
        # Calculer la quantité USDC attendue
        expected_usdc = eur_to_sell * eur_usdc_rate * 0.999  # -0.1% frais
        
        print(f"💵 Quantité EUR à vendre: {eur_to_sell:.8f}€")
        print(f"💵 USDC attendu: {expected_usdc:.2f}$ (après frais)")
        
        # Vérifier la valeur minimale
        if min_notional_filter:
            notional_value = eur_to_sell * eur_usdc_rate
            if notional_value < min_notional: # type: ignore
                print(f"❌ Valeur insuffisante: {notional_value:.2f} < {min_notional}")      # type: ignore
                return False
        
        # Demander confirmation
        print()
        print("⚠️  CONFIRMATION REQUISE:")
        print(f"   Convertir {eur_to_sell:.8f}€ → ~{expected_usdc:.2f}$ USDC")
        print("   Frais estimés: ~0.1%")
        print()
        
        confirmation = input("Confirmer la conversion ? (oui/non): ").lower().strip()
        if confirmation not in ['oui', 'o', 'yes', 'y']:
            print("❌ Conversion annulée")
            return False
        
        print()
        print("🔄 Exécution de la conversion...")
        
        # Exécuter la conversion via order
        try:
            order = client.order_market_sell(
                symbol='EURUSDC',
                quantity=f"{eur_to_sell:.8f}"
            )
            
            print("✅ Ordre de conversion exécuté!")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Status: {order['status']}")
            print(f"   Quantité: {order.get('executedQty', 'N/A')} EUR")
            
            # Attendre quelques secondes et vérifier le résultat
            time.sleep(5)
            
            # Vérifier les nouveaux soldes
            account_info = client.get_account()
            new_eur_balance = 0.0
            new_usdc_balance = 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'EUR':
                    new_eur_balance = float(balance['free'])
                elif balance['asset'] == 'USDC':
                    new_usdc_balance = float(balance['free'])
            
            print(f"\n📊 RÉSULTATS:")
            print(f"   💶 EUR avant: {eur_balance:.8f}€")
            print(f"   💶 EUR après: {new_eur_balance:.8f}€")
            print(f"   💵 USDC après: {new_usdc_balance:.2f}$")
            
            eur_converted = eur_balance - new_eur_balance
            print(f"   ✅ EUR converti: {eur_converted:.8f}€")
            
            # Estimer le gain USDC
            usdc_gained = new_usdc_balance - (new_usdc_balance - expected_usdc)  # Approximation
            print(f"   ✅ USDC gagné: ~{expected_usdc:.2f}$")
            
            print(f"\n🎯 CAPITAL TOTAL USDC ESTIMÉ: ~{new_usdc_balance:.2f}$")
            print("🚀 Prêt pour le trading haute liquidité!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la conversion: {e}")
            print("💡 Suggestion: Vérifier les filtres de la paire ou utiliser l'interface Binance")
            return False
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CONVERSION EUR → USDC POUR TRADING BOT")
    print("="*50)
    success = convert_eur_to_usdc_fixed()
    
    if success:
        print("\n✅ CONVERSION RÉUSSIE - BOT PRÊT À DÉMARRER!")
    else:
        print("\n❌ CONVERSION ÉCHOUÉE - VÉRIFIER LES PARAMÈTRES")
