#!/usr/bin/env python3
"""
💱 CONVERSION EUR → USDC SUR BINANCE
Script automatisé pour convertir le capital EUR en USDC
"""

import os
import time

from binance.client import Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def convert_eur_to_usdc():
    print("💱 === CONVERSION EUR → USDC ===")
    print()
    
    try:
        # Connexion Binance
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not api_secret:
            print("❌ ERREUR: Clés API manquantes")
            return False
            
        client = Client(api_key, api_secret)
        
        # Vérifier le solde EUR
        account_info = client.get_account()
        eur_balance = 0.0
        
        for balance in account_info['balances']:
            if balance['asset'] == 'EUR':
                eur_balance = float(balance['free'])
                break
        
        if eur_balance < 10:
            print(f"❌ Solde EUR insuffisant: {eur_balance:.2f}€")
            return False
        
        print(f"💶 Solde EUR actuel: {eur_balance:.2f}€")
        
        # Vérifier le taux EUR/USDC
        try:
            ticker = client.get_symbol_ticker(symbol='EURUSDC')
            eur_usdc_rate = float(ticker['price'])
            print(f"💱 Taux EUR/USDC: {eur_usdc_rate:.4f}")
        except Exception as e:
            print(f"❌ Impossible de récupérer le taux EUR/USDC: {e}")
            return False
        
        # Calculer la quantité USDC attendue
        expected_usdc = eur_balance * eur_usdc_rate * 0.999  # -0.1% frais
        print(f"💵 USDC attendu: {expected_usdc:.2f}$ (après frais)")
        
        # Demander confirmation
        print()
        print("⚠️  CONFIRMATION REQUISE:")
        print(f"   Convertir {eur_balance:.2f}€ → ~{expected_usdc:.2f}$ USDC")
        print("   Frais estimés: ~0.1%")
        print()
        
        confirmation = input("Confirmer la conversion ? (oui/non): ").lower().strip()
        if confirmation not in ['oui', 'o', 'yes', 'y']:
            print("❌ Conversion annulée")
            return False
        
        print()
        print("🔄 Exécution de la conversion...")
        
        # Exécuter la conversion via order
        # Note: Utilisation d'un ordre market pour conversion immédiate
        try:
            # Calculer la quantité à vendre (EUR)
            # On garde une petite marge pour les frais
            eur_to_sell = eur_balance * 0.999
            
            order = client.order_market_sell(
                symbol='EURUSDC',
                quantity=round(eur_to_sell, 2)
            )
            
            print("✅ Ordre de conversion exécuté!")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Status: {order['status']}")
            
            # Attendre quelques secondes et vérifier le résultat
            time.sleep(3)
            
            # Vérifier les nouveaux soldes
            account_info = client.get_account()
            new_eur_balance = 0.0
            new_usdc_balance = 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'EUR':
                    new_eur_balance = float(balance['free'])
                elif balance['asset'] == 'USDC':
                    new_usdc_balance = float(balance['free'])
            
            print()
            print("💰 RÉSULTAT DE LA CONVERSION:")
            print(f"   💶 EUR restant: {new_eur_balance:.2f}€")
            print(f"   💵 USDC obtenu: {new_usdc_balance:.2f}$")
            
            # Calculer l'efficacité de la conversion
            actual_rate = new_usdc_balance / (eur_balance - new_eur_balance) if (eur_balance - new_eur_balance) > 0 else 0
            fee_rate = (1 - actual_rate / eur_usdc_rate) * 100 if eur_usdc_rate > 0 else 0
            
            print(f"   📊 Taux réalisé: {actual_rate:.4f}")
            print(f"   💸 Frais effectifs: {fee_rate:.3f}%")
            
            if new_usdc_balance > expected_usdc * 0.98:  # Si on a au moins 98% du montant attendu
                print("✅ CONVERSION RÉUSSIE!")
                return True
            else:
                print("⚠️  Conversion partiellement réussie")
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la conversion: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

def verify_usdc_balance():
    """Vérifie le solde USDC final"""
    print("\n🔍 === VÉRIFICATION SOLDE FINAL ===")
    
    try:
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        client = Client(api_key, api_secret)
        
        account_info = client.get_account()
        usdc_balance = 0.0
        
        for balance in account_info['balances']:
            if balance['asset'] == 'USDC':
                usdc_balance = float(balance['free'])
                break
        
        print(f"💵 Solde USDC final: {usdc_balance:.2f}$")
        
        if usdc_balance > 1000:
            print("✅ Solde USDC suffisant pour le trading")
            return True
        else:
            print("⚠️  Solde USDC faible")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CONVERSION EUR → USDC POUR TRADING BOT")
    print("="*50)
    
    success = convert_eur_to_usdc()
    
    if success:
        verify_usdc_balance()
        print()
        print("🎯 PROCHAINES ÉTAPES:")
        print("   1️⃣ Bot migré vers USDC ✅")
        print("   2️⃣ Capital converti ✅") 
        print("   3️⃣ Redémarrer le bot")
        print("   4️⃣ Monitorer les performances")
    else:
        print()
        print("❌ CONVERSION ÉCHOUÉE - NE PAS REDÉMARRER LE BOT")
