#!/usr/bin/env python3
"""
Analyse de la fragmentation des trades
"""

import pandas as pd


def analyze_fragmentation():
    print("🔍 ANALYSE DE LA FRAGMENTATION")
    print("="*50)
    
    df = pd.read_csv('binance_export_20250720.csv', sep=';')
    df['DateTime'] = pd.to_datetime(df['Date(UTC)'])
    df['Second'] = df['DateTime'].dt.floor('S')
    
    # Grouper par seconde pour détecter la fragmentation
    grouped = df.groupby(['Second', 'Pair', 'Type']).agg({
        'Total': ['count', 'sum'],
        'Fee': 'sum',
        'Amount': 'sum'
    })
    
    # Flatten columns
    grouped.columns = ['TradeCount', 'TotalValue', 'TotalFees', 'TotalAmount']
    grouped = grouped.reset_index()
    
    # Fragmentation = plus d'1 trade par seconde
    fragmented = grouped[grouped['TradeCount'] > 1].sort_values('TradeCount', ascending=False)
    
    print(f"📊 RÉSULTATS:")
    print(f"   Secondes avec fragmentation: {len(fragmented)}")
    print(f"   Total trades fragmentés: {fragmented['TradeCount'].sum()}")
    print(f"   Total valeur fragmentée: {fragmented['TotalValue'].sum():,.0f}€")
    
    print(f"\n🚨 TOP 10 PIRES FRAGMENTATIONS:")
    for _, row in fragmented.head(10).iterrows():
        avg_size = row['TotalValue'] / row['TradeCount']
        print(f"   {row['Second']} {row['Pair']} {row['Type']}: {row['TradeCount']} × {avg_size:.0f}€ = {row['TotalValue']:.0f}€")
    
    # Calcul de l'économie potentielle
    # Si au lieu de N trades fragmentés, on faisait 1 seul trade
    trades_saved = fragmented['TradeCount'].sum() - len(fragmented)
    avg_fee_per_trade = df['Fee'].mean() * 0.1  # Estimation frais EUR
    potential_savings = trades_saved * avg_fee_per_trade
    
    print(f"\n💰 ÉCONOMIE POTENTIELLE:")
    print(f"   Trades évités: {trades_saved}")
    print(f"   Économie estimée: -{potential_savings:.2f}€")
    
    return fragmented

if __name__ == "__main__":
    result = analyze_fragmentation()
