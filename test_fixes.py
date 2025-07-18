#!/usr/bin/env python3
"""
Script de test pour vérifier les corrections des quantités minimales
"""

import os
import sys
from binance.client import Client

def load_config():
    """Charge la configuration depuis le fichier .env"""
    config = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
        return config
    except Exception as e:
        print(f"❌ Erreur lecture .env: {e}")
        return {}

def test_symbol_filters():
    """Test des filtres de symboles"""
    try:
        # Chargement de la configuration
        config = load_config()
        
        # Initialisation du client Binance
        client = Client(
            api_key=config.get('BINANCE_API_KEY'),
            api_secret=config.get('BINANCE_SECRET_KEY'),
            testnet=False
        )
        
        print("🔍 TEST DES FILTRES DE SYMBOLES")
        print("=" * 50)
        
        # Test avec quelques paires EUR
        test_symbols = ['ETHEUR', 'BTCEUR', 'ADAEUR', 'DOTEUR', 'SOLEUR']
        
        for symbol in test_symbols:
            try:
                print(f"\n📊 {symbol}:")
                info = client.get_symbol_info(symbol)
                
                if info and 'filters' in info:
                    for filter_item in info['filters']:
                        if filter_item['filterType'] == 'LOT_SIZE':
                            print(f"   Min Qty: {filter_item['minQty']}")
                            print(f"   Max Qty: {filter_item['maxQty']}")
                            print(f"   Step Size: {filter_item['stepSize']}")
                        elif filter_item['filterType'] == 'MIN_NOTIONAL':
                            print(f"   Min Notional: {filter_item['minNotional']} EUR")
                        elif filter_item['filterType'] == 'PRICE_FILTER':
                            print(f"   Tick Size: {filter_item['tickSize']}")
                else:
                    print(f"   ❌ Pas d'informations disponibles")
                
            except Exception as e:
                print(f"   ❌ Erreur pour {symbol}: {e}")
        
    except Exception as e:
        print(f"❌ Erreur test filtres: {e}")

def test_account_balances():
    """Test des soldes du compte"""
    try:
        config = load_config()
        
        client = Client(
            api_key=config.get('BINANCE_API_KEY'),
            api_secret=config.get('BINANCE_SECRET_KEY'),
            testnet=False
        )
        
        print("\n\n💰 TEST DES SOLDES DU COMPTE")
        print("=" * 50)
        
        account_info = client.get_account()
        
        print("Soldes disponibles:")
        eur_found = False
        significant_balances = []
        
        for balance in account_info['balances']:
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            
            if balance['asset'] == 'EUR':
                eur_found = True
                print(f"💶 EUR: {free_balance:.2f} (libre) + {locked_balance:.2f} (bloqué) = {free_balance + locked_balance:.2f}")
            elif free_balance > 0.001 or locked_balance > 0.001:
                significant_balances.append({
                    'asset': balance['asset'],
                    'free': free_balance,
                    'locked': locked_balance,
                    'total': free_balance + locked_balance
                })
        
        if not eur_found:
            print("❌ Aucun solde EUR trouvé!")
        
        if significant_balances:
            print("\nAutres soldes significatifs:")
            for bal in significant_balances[:10]:  # Limite à 10
                print(f"🪙 {bal['asset']}: {bal['free']:.8f} (libre) + {bal['locked']:.8f} (bloqué)")
        
    except Exception as e:
        print(f"❌ Erreur test soldes: {e}")

def test_quantity_validation():
    """Test de validation des quantités"""
    print("\n\n🧮 TEST DE VALIDATION DES QUANTITÉS")
    print("=" * 50)
    
    test_cases = [
        {'symbol': 'ETHEUR', 'quantity': 0.001, 'price': 3000},
        {'symbol': 'ETHEUR', 'quantity': 0.0001, 'price': 3000},
        {'symbol': 'BTCEUR', 'quantity': 0.00001, 'price': 60000},
        {'symbol': 'ADAEUR', 'quantity': 1.5, 'price': 0.8},
        {'symbol': 'DOTEUR', 'quantity': 0.5, 'price': 8.0},
    ]
    
    try:
        config = load_config()
        
        client = Client(
            api_key=config.get('BINANCE_API_KEY'),
            api_secret=config.get('BINANCE_SECRET_KEY'),
            testnet=False
        )
        
        for test in test_cases:
            symbol = test['symbol']
            quantity = test['quantity']
            price = test['price']
            notional = quantity * price
            
            print(f"\n📋 Test {symbol}:")
            print(f"   Quantité: {quantity:.8f}")
            print(f"   Prix: {price:.2f} EUR")
            print(f"   Valeur notionnelle: {notional:.2f} EUR")
            
            try:
                info = client.get_symbol_info(symbol)
                filters = {}
                
                if info and 'filters' in info:
                    for filter_item in info['filters']:
                        if filter_item['filterType'] == 'LOT_SIZE':
                            filters['min_qty'] = float(filter_item['minQty'])
                            filters['step_size'] = float(filter_item['stepSize'])
                        elif filter_item['filterType'] == 'MIN_NOTIONAL':
                            filters['min_notional'] = float(filter_item['minNotional'])
                
                # Validation
                valid = True
                messages = []
                
                if quantity < filters.get('min_qty', 0):
                    valid = False
                    messages.append(f"Quantité < minimum ({filters['min_qty']:.8f})")
                
                if notional < filters.get('min_notional', 0):
                    valid = False
                    messages.append(f"Valeur notionnelle < minimum ({filters['min_notional']:.2f} EUR)")
                
                if valid:
                    print("   ✅ VALIDE")
                else:
                    print("   ❌ INVALIDE:")
                    for msg in messages:
                        print(f"      - {msg}")
                
            except Exception as e:
                print(f"   ❌ Erreur validation: {e}")
    
    except Exception as e:
        print(f"❌ Erreur test validation: {e}")

def main():
    """Fonction principale"""
    print("🧪 TESTS DE VALIDATION DES CORRECTIONS")
    print("=" * 60)
    
    # Vérification du fichier de configuration
    if not os.path.exists('.env'):
        print("❌ Fichier .env non trouvé!")
        sys.exit(1)
    
    try:
        # Tests
        test_symbol_filters()
        test_account_balances()
        test_quantity_validation()
        
        print("\n\n" + "=" * 60)
        print("✅ TESTS TERMINÉS")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
