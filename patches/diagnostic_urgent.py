#!/usr/bin/env python3
"""
DIAGNOSTIC URGENT: Pourquoi 2400€ de frais ?
"""

import pandas as pd

# Lecture simple
print("Loading CSV...")
df = pd.read_csv('binance_export_20250720.csv', sep=';')

print(f"Total trades: {len(df)}")
print(f"Columns: {list(df.columns)}")

# BNB analysis
bnb_trades = df[df['Pair'] == 'BNB/EUR']
print(f"\nBNB/EUR trades: {len(bnb_trades)}")

if len(bnb_trades) > 0:
    total_bnb_eur = bnb_trades['Total'].sum()
    total_bnb_fees = bnb_trades['Fee'].sum()
    print(f"BNB total volume: {total_bnb_eur:.2f}€")
    print(f"BNB total fees: {total_bnb_fees:.4f} BNB")
    
    # Sample of BNB trades
    print("\nBNB sample:")
    for _, row in bnb_trades.head(5).iterrows():
        print(f"  {row['Date(UTC)']} {row['Type']} {row['Amount']} BNB = {row['Total']}€ (fee: {row['Fee']} BNB)")

# Fee coins analysis
print(f"\nFee coins breakdown:")
fee_breakdown = df['Fee Coin'].value_counts()
print(fee_breakdown)

# Check biggest trades by value
print(f"\nBiggest trades by value:")
biggest = df.nlargest(5, 'Total')
for _, row in biggest.iterrows():
    print(f"  {row['Date(UTC)']} {row['Pair']} {row['Type']} {row['Total']:.2f}€ (fee: {row['Fee']} {row['Fee Coin']})")
