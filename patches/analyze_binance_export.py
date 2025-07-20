#!/usr/bin/env python3
"""
Analyse de l'export Binance pour identifier les problèmes de trading
"""

from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def analyze_binance_export(csv_path):
    """Analyse l'export Binance"""
    print("🔍 ANALYSE DE L'EXPORT BINANCE")
    print("=" * 50)
    
    # Lecture du CSV avec séparateur point-virgule
    df = pd.read_csv(csv_path, sep=';')
    
    # Conversion des dates
    df['Date(UTC)'] = pd.to_datetime(df['Date(UTC)'])
    df['Date'] = df['Date(UTC)'].dt.date
    df['Hour'] = df['Date(UTC)'].dt.hour
    df['Minute'] = df['Date(UTC)'].dt.minute
    
    # Calcul du P&L par trade
    df['PnL'] = df.apply(lambda row: 
        row['Total'] if row['Type'] == 'SELL' else -row['Total'], axis=1)
    
    print(f"📊 STATISTIQUES GÉNÉRALES")
    print(f"   Total trades: {len(df):,}")
    print(f"   Période: {df['Date'].min()} → {df['Date'].max()}")
    print(f"   Paires tradées: {df['Pair'].nunique()}")
    print(f"   Types: {df['Type'].value_counts().to_dict()}")
    
    # Analyse par jour
    print(f"\n📅 ANALYSE PAR JOUR")
    daily_analysis = df.groupby('Date').agg({
        'PnL': 'sum',
        'Total': 'sum',
        'Pair': 'count'
    }).round(2)
    daily_analysis.columns = ['P&L_EUR', 'Volume_EUR', 'Nb_Trades']
    
    for date, row in daily_analysis.iterrows():
        pnl_percent = (row['P&L_EUR'] / 19650) * 100  # Supposant capital de 19650€
        status = "🛑" if pnl_percent <= -2.0 else "✅" if pnl_percent > 0 else "⚠️"
        print(f"   {date}: {row['P&L_EUR']:+.2f}€ ({pnl_percent:+.2f}%) - {row['Nb_Trades']} trades {status}")
    
    # Analyse des patterns suspects
    print(f"\n🚨 DÉTECTION DE PATTERNS SUSPECTS")
    
    # 1. Trades en rafale (même minute)
    burst_trades = df.groupby(['Date', 'Hour', 'Minute', 'Pair']).size()
    suspicious_bursts = burst_trades[burst_trades > 50]  # Plus de 50 trades/minute
    
    if len(suspicious_bursts) > 0:
        print(f"   ⚠️  {len(suspicious_bursts)} rafales de trades détectées:")
        for idx, count in suspicious_bursts.head(10).items():
            # idx can be a tuple (date, hour, minute, pair) or a single value if not MultiIndex
            if isinstance(idx, tuple) and len(idx) == 4:
                date, hour, minute, pair = idx
                print(f"      {date} {hour:02d}:{minute:02d} - {pair}: {count} trades")
            else:
                print(f"      {idx} : {count} trades")
    
    # 2. Analyse DOGE (le plus actif)
    doge_trades = df[df['Pair'] == 'DOGE/EUR']
    if len(doge_trades) > 0:
        print(f"\n💎 ANALYSE DOGE/EUR ({len(doge_trades):,} trades)")
        doge_daily = doge_trades.groupby('Date')['PnL'].sum()
        for date, pnl in doge_daily.items():
            print(f"   {date}: {pnl:+.2f}€")
        
        # Moment exact de la rafale
        doge_minute = doge_trades.groupby(['Date', 'Hour', 'Minute']).agg({
            'PnL': 'sum',
            'Pair': 'count'
        })
        worst_minute = doge_minute.loc[doge_minute['Pair'].idxmax()]
        print(f"   🚨 Pire minute: {worst_minute['Pair']} trades = {worst_minute['PnL']:+.2f}€")
    
    # 3. Recherche de grosses pertes
    print(f"\n💸 GROSSES PERTES INDIVIDUELLES")
    big_losses = df[df['PnL'] < -50].sort_values('PnL')
    if len(big_losses) > 0:
        print(f"   {len(big_losses)} trades avec perte > 50€:")
        for _, trade in big_losses.head(10).iterrows():
            print(f"      {trade['Date(UTC)']} - {trade['Pair']}: {trade['PnL']:+.2f}€")
    
    # 4. Calcul du P&L total
    total_pnl = df['PnL'].sum()
    print(f"\n💰 RÉSULTATS FINAUX")
    print(f"   P&L total: {total_pnl:+.2f}€")
    
    # Comparaison avec ce qu'on a vu dans les logs (-800€)
    if total_pnl < -500:
        print(f"   🚨 CONFIRMATION: Grosses pertes détectées ({total_pnl:+.2f}€)")
    
    return df

if __name__ == "__main__":
    df = analyze_binance_export('binance_export_20250720.csv')
