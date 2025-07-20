#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCUL CORRECT DES FRAIS - Distinction EUR vs Crypto
"""

import numpy as np
import pandas as pd


def calculate_real_fees():
    print("🔍 CALCUL CORRECT DES FRAIS BINANCE")
    print("="*60)
    
    df = pd.read_csv('binance_export_20250720.csv', sep=';')
    
    # Séparer les frais EUR vs Crypto
    fees_eur = df[df['Fee Coin'] == 'EUR']
    fees_crypto = df[df['Fee Coin'] != 'EUR']
    
    print(f"📊 RÉPARTITION DES FRAIS:")
    print(f"   Frais en EUR: {len(fees_eur)} trades = {fees_eur['Fee'].sum():.2f}€")
    print(f"   Frais en crypto: {len(fees_crypto)} trades")
    
    # Analyser les frais crypto par devise
    print(f"\n💰 FRAIS PAR DEVISE:")
    for coin in fees_crypto['Fee Coin'].unique():
        coin_fees = fees_crypto[fees_crypto['Fee Coin'] == coin]
        total_fee = coin_fees['Fee'].sum()
        print(f"   {coin}: {total_fee:.4f} {coin} ({len(coin_fees)} trades)")
    
    # Pour convertir les frais crypto en EUR, on utilise le prix du trade
    print(f"\n🔄 CONVERSION FRAIS CRYPTO → EUR:")
    
    total_fees_eur = fees_eur['Fee'].sum()
    
    # Pour les BUY, les frais sont en crypto, on les convertit avec le prix d'achat
    crypto_fees_eur = 0
    
    for _, trade in fees_crypto.iterrows():
        if trade['Type'] == 'BUY':
            # Frais en crypto, convertir au prix d'achat
            fee_in_eur = trade['Fee'] * trade['Price']
            crypto_fees_eur += fee_in_eur
    
    total_real_fees = total_fees_eur + crypto_fees_eur
    
    print(f"   Frais EUR directs: {total_fees_eur:.2f}€")
    print(f"   Frais crypto convertis: {crypto_fees_eur:.2f}€")
    print(f"   🎯 TOTAL RÉEL: {total_real_fees:.2f}€")
    
    # Vérification des types de trades
    print(f"\n📈 VÉRIFICATION TYPES:")
    type_counts = df['Type'].value_counts()
    for trade_type, count in type_counts.items():
        avg_fee = df[df['Type'] == trade_type]['Fee'].mean()
        fee_coin = df[df['Type'] == trade_type]['Fee Coin'].iloc[0] if count > 0 else 'N/A'
        print(f"   {trade_type}: {count} trades - Frais moy: {avg_fee:.4f} {fee_coin}")
    
    # Impact sur les pertes
    print(f"\n💸 IMPACT SUR LES PERTES:")
    print(f"   Perte totale estimée: -900€")
    print(f"   Frais réels: -{total_real_fees:.2f}€")
    print(f"   % frais dans la perte: {(total_real_fees/900)*100:.1f}%")
    
    if total_real_fees < 200:
        print(f"   ✅ Les frais ne sont PAS la cause principale !")
        print(f"   🔍 Il faut chercher ailleurs... Losses réelles ?")
    else:
        print(f"   🚨 Les frais restent un problème majeur !")
    
    return total_real_fees

if __name__ == "__main__":
    real_fees = calculate_real_fees()
