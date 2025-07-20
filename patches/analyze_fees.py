#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse détaillée des frais de trading Binance
Pourquoi tant de trades ? Pourquoi tant de frais ?
"""

from datetime import datetime

import numpy as np
import pandas as pd


def analyze_fees():
    print("🔍 ANALYSE DES FRAIS ET PATTERNS DE TRADING")
    print("=" * 60)
    
    # Charger le fichier
    df = pd.read_csv('binance_export_20250720.csv', sep=';')
    
    # Colonnes importantes
    df['DateTime'] = pd.to_datetime(df['Date(UTC)'])
    df['Fee'] = df['Fee'].astype(float)
    df['Total'] = df['Total'].astype(float)
    df['Amount'] = df['Amount'].astype(float)
    
    # 1. ANALYSE DES FRAIS
    total_fees = df['Fee'].sum()
    total_volume = df['Total'].sum()
    avg_fee_rate = (total_fees / total_volume) * 100
    
    print(f"💰 FRAIS TOTAUX: {total_fees:.2f}€")
    print(f"📊 VOLUME TOTAL: {total_volume:,.0f}€")
    print(f"📈 TAUX MOYEN: {avg_fee_rate:.4f}%")
    print()
    
    # 2. DISTRIBUTION DES TAILLES
    print("📏 DISTRIBUTION DES TAILLES DE TRADES:")
    print(f"   Min: {df['Total'].min():.2f}€")
    print(f"   Max: {df['Total'].max():.2f}€")
    print(f"   Moyenne: {df['Total'].mean():.2f}€")
    print(f"   Médiane: {df['Total'].median():.2f}€")
    
    # Catégories de tailles
    micro = df[df['Total'] < 10]
    small = df[(df['Total'] >= 10) & (df['Total'] < 100)]
    medium = df[(df['Total'] >= 100) & (df['Total'] < 1000)]
    large = df[df['Total'] >= 1000]
    
    print(f"   🔸 Micro (<10€): {len(micro)} trades ({len(micro)/len(df)*100:.1f}%) - {micro['Fee'].sum():.2f}€ frais")
    print(f"   🔹 Small (10-100€): {len(small)} trades ({len(small)/len(df)*100:.1f}%) - {small['Fee'].sum():.2f}€ frais")
    print(f"   🔶 Medium (100-1K€): {len(medium)} trades ({len(medium)/len(df)*100:.1f}%) - {medium['Fee'].sum():.2f}€ frais")
    print(f"   🟥 Large (>1K€): {len(large)} trades ({len(large)/len(df)*100:.1f}%) - {large['Fee'].sum():.2f}€ frais")
    print()
    
    # 3. ANALYSE TEMPORELLE - BURST TRADING
    df_sorted = df.sort_values('DateTime')
    df_sorted['TimeDiff'] = df_sorted['DateTime'].diff().dt.total_seconds()
    
    # Trades dans la même seconde/minute
    same_second = df_sorted[df_sorted['TimeDiff'] <= 1]
    same_minute = df_sorted[df_sorted['TimeDiff'] <= 60]
    
    print("⚡ BURST TRADING:")
    print(f"   Même seconde: {len(same_second)} trades - {same_second['Fee'].sum():.2f}€ frais")
    print(f"   Même minute: {len(same_minute)} trades - {same_minute['Fee'].sum():.2f}€ frais")
    
    # 4. ANALYSE PAR PAIRE
    print("\n🎯 TOP PAIRES PAR FRAIS:")
    pair_analysis = df.groupby('Pair').agg({
        'Fee': 'sum',
        'Total': 'count',
        'Amount': 'sum'
    }).sort_values('Fee', ascending=False)
    
    for pair, data in pair_analysis.head(10).iterrows():
        print(f"   {pair}: {data['Fee']:.2f}€ frais ({data['Total']} trades)")
    
    # 5. DÉTECTION DE FRAGMENTATION
    print("\n🔄 ANALYSE DE FRAGMENTATION:")
    
    # Grouper par minute pour détecter les ordres fragmentés
    df['Minute'] = df['DateTime'].dt.floor('T')
    minute_groups = df.groupby(['Minute', 'Pair', 'Type']).agg({
        'Total': ['count', 'sum'],
        'Fee': 'sum'
    })
    
    # Chercher les minutes avec beaucoup de trades
    fragmented = minute_groups[minute_groups[('Total', 'count')] > 5]
    
    if len(fragmented) > 0:
        print(f"   🚨 {len(fragmented)} minutes avec >5 trades (fragmentation suspectée)")
        print("   Top 5 pires fragmentations:")
        
        worst_frag = fragmented.sort_values(('Total', 'count'), ascending=False).head(5)
        for (minute, pair, trade_type), data in worst_frag.iterrows():
            trades_count = data[('Total', 'count')]
            total_value = data[('Total', 'sum')]
            total_fees = data[('Fee', 'sum')]
            print(f"      {minute} {pair} {trade_type}: {trades_count} trades = {total_value:.0f}€ ({total_fees:.2f}€ frais)")
    
    # 6. RECOMMANDATIONS
    print("\n💡 RECOMMANDATIONS:")
    
    # Calcul des économies potentielles
    micro_fee_waste = micro['Fee'].sum()
    burst_fee_waste = same_minute['Fee'].sum()
    
    print(f"   💸 Économies micro-trades: -{micro_fee_waste:.2f}€")
    print(f"   ⚡ Économies burst trading: -{burst_fee_waste:.2f}€")
    print(f"   🎯 Économies totales possibles: -{(micro_fee_waste + burst_fee_waste):.2f}€")
    
    # Taille de trade optimale
    optimal_size = df[df['Fee'] / df['Total'] < 0.001]['Total'].median()
    print(f"   📏 Taille optimale suggérée: >{optimal_size:.0f}€ par trade")
    
    return {
        'total_fees': total_fees,
        'total_trades': len(df),
        'micro_trades': len(micro),
        'burst_trades': len(same_minute),
        'potential_savings': micro_fee_waste + burst_fee_waste
    }

if __name__ == "__main__":
    results = analyze_fees()
