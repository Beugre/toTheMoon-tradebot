#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE CORRECTE DES FRAIS - BUY vs SELL
"""

import pandas as pd


def analyze_fees_correctly():
    print("🔍 ANALYSE CORRECTE DES FRAIS BINANCE")
    print("="*60)
    
    # Lecture du fichier
    df = pd.read_csv('binance_export_20250720.csv', sep=';')
    
    # Statistiques de base
    print(f"📊 TOTAL: {len(df)} trades")
    print(f"   SELL: {len(df[df['Type'] == 'SELL'])} trades")
    print(f"   BUY: {len(df[df['Type'] == 'BUY'])} trades")
    print()
    
    # Analyser les frais
    print("💰 ANALYSE DES FRAIS:")
    
    # SELL trades - frais en EUR
    sell_trades = df[df['Type'] == 'SELL']
    sell_fees_eur = sell_trades['Fee'].sum()
    print(f"   📤 SELL frais: {sell_fees_eur:.2f}€ ({len(sell_trades)} trades)")
    
    # BUY trades - frais en crypto qu'il faut convertir
    buy_trades = df[df['Type'] == 'BUY']
    buy_fees_converted = 0
    
    print(f"   📥 BUY frais (conversion crypto→EUR):")
    
    for coin in buy_trades['Fee Coin'].unique():
        coin_trades = buy_trades[buy_trades['Fee Coin'] == coin]
        total_fee_crypto = coin_trades['Fee'].sum()
        
        # Conversion en EUR en utilisant le prix moyen des trades
        avg_price = coin_trades['Price'].mean()
        fee_in_eur = total_fee_crypto * avg_price
        buy_fees_converted += fee_in_eur
        
        print(f"      {coin}: {total_fee_crypto:.4f} {coin} × {avg_price:.4f}€ = {fee_in_eur:.2f}€")
    
    # Total réel
    total_real_fees = sell_fees_eur + buy_fees_converted
    print(f"\n🎯 FRAIS TOTAUX RÉELS: {total_real_fees:.2f}€")
    print(f"   (vs les {693.60:.2f}€ calculés incorrectement)")
    
    # Impact sur la perte
    print(f"\n💸 IMPACT SUR VOS PERTES:")
    loss_total = 900  # EUR (20K → 19.1K)
    fees_percentage = (total_real_fees / loss_total) * 100
    
    print(f"   Perte totale: -{loss_total}€")
    print(f"   Frais réels: -{total_real_fees:.2f}€")
    print(f"   Part des frais: {fees_percentage:.1f}%")
    
    if fees_percentage > 50:
        print(f"   🚨 LES FRAIS SONT LA CAUSE PRINCIPALE !")
        print(f"   ⚡ Optimisation urgente nécessaire")
    elif fees_percentage > 30:
        print(f"   ⚠️  Les frais sont un problème significatif")
        print(f"   🔧 Optimisation recommandée")
    else:
        print(f"   ✅ Les frais ne sont pas le problème principal")
        print(f"   🔍 Chercher les vraies causes des pertes")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    if total_real_fees > 200:
        print(f"   1. ⬆️  Augmenter taille min des trades (>500€)")
        print(f"   2. ⏱️  Réduire la fréquence (max 1 trade/minute/paire)")
        print(f"   3. 🎯 Grouper les ordres au lieu de les fragmenter")
    
    return {
        'total_fees': total_real_fees,
        'sell_fees': sell_fees_eur,
        'buy_fees': buy_fees_converted,
        'percentage_of_loss': fees_percentage
    }

if __name__ == "__main__":
    result = analyze_fees_correctly()
    print(f"\n📋 RÉSUMÉ:")
    print(f"   Frais réels: {result['total_fees']:.2f}€")
    print(f"   Impact: {result['percentage_of_loss']:.1f}% des pertes")
