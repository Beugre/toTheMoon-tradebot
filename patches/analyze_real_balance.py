#!/usr/bin/env python3
"""
Analyse de l'export Binance pour calculer le solde réel
et identifier où sont passés les 800€ manquants
"""

from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd


def analyze_real_balance_from_binance(csv_path):
    """Calcule le solde réel basé uniquement sur l'export Binance"""
    print("💰 CALCUL DU SOLDE RÉEL - EXPORT BINANCE UNIQUEMENT")
    print("=" * 60)
    
    # Lecture du CSV
    df = pd.read_csv(csv_path, sep=';')
    df['Date(UTC)'] = pd.to_datetime(df['Date(UTC)'])
    df['Date'] = df['Date(UTC)'].dt.date
    
    print(f"📊 DONNÉES BINANCE")
    print(f"   Total transactions: {len(df):,}")
    print(f"   Période: {df['Date'].min()} → {df['Date'].max()}")
    print(f"   Première transaction: {df['Date(UTC)'].min()}")
    print(f"   Dernière transaction: {df['Date(UTC)'].max()}")
    
    # Calcul du P&L réalisé (trades fermés uniquement)
    # BUY = sortie d'EUR, SELL = entrée d'EUR
    df['EUR_Flow'] = df.apply(lambda row: 
        row['Total'] + row['Fee'] if row['Type'] == 'SELL' 
        else -(row['Total'] + row['Fee']), axis=1)
    
    print(f"\n💸 FLUX D'EUR (Sorties/Entrées)")
    total_eur_flow = df['EUR_Flow'].sum()
    print(f"   Flux EUR total: {total_eur_flow:+.2f}€")
    
    if total_eur_flow > 0:
        print(f"   📈 Gain net réalisé: +{total_eur_flow:.2f}€")
    else:
        print(f"   📉 Perte nette réalisée: {total_eur_flow:.2f}€")
    
    # Analyse par jour pour voir l'évolution
    print(f"\n📅 ÉVOLUTION QUOTIDIENNE DU SOLDE")
    daily_flows = df.groupby('Date')['EUR_Flow'].sum().sort_index()
    
    # Capital de départ supposé
    starting_capital = 20000  # Basé sur votre indication
    current_balance = starting_capital
    
    print(f"   Capital initial: {starting_capital:,.2f}€")
    print(f"   ═══════════════════════════════")
    
    for trade_date, daily_flow in daily_flows.items():
        current_balance += daily_flow
        change_percent = (daily_flow / starting_capital) * 100
        status = "📈" if daily_flow > 0 else "📉" if daily_flow < -100 else "➖"
        
        print(f"   {trade_date}: {daily_flow:+8.2f}€ ({change_percent:+5.2f}%) → {current_balance:8.2f}€ {status}")
    
    print(f"   ═══════════════════════════════")
    print(f"   Capital final calculé: {current_balance:,.2f}€")
    print(f"   Capital réel actuel:   19,200.00€ (votre indication)")
    print(f"   Différence:            {19200 - current_balance:+.2f}€")
    
    # Analyse des commissions
    print(f"\n💳 ANALYSE DES COMMISSIONS")
    total_fees = df['Fee'].sum()
    print(f"   Total commissions: {total_fees:.2f}€")
    
    # Analyse par type de transaction
    buys = df[df['Type'] == 'BUY']
    sells = df[df['Type'] == 'SELL']
    
    buy_volume = buys['Total'].sum()
    sell_volume = sells['Total'].sum()
    
    print(f"\n📊 VOLUMES DE TRADING")
    print(f"   Volume achats (BUY):  {buy_volume:,.2f}€")
    print(f"   Volume ventes (SELL): {sell_volume:,.2f}€")
    print(f"   Différence:           {sell_volume - buy_volume:+.2f}€")
    
    # Recherche des grosses variations journalières
    print(f"\n🚨 JOURS AVEC GROSSES VARIATIONS")
    big_changes = daily_flows[abs(daily_flows) > 500]
    
    for trade_date, flow in big_changes.items():
        print(f"   {trade_date}: {flow:+.2f}€")
        
        # Détail de ce jour
        day_trades = df[df['Date'] == trade_date]
        print(f"      {len(day_trades)} transactions")
        
        # Principales paires ce jour-là
        day_pairs = day_trades.groupby('Pair')['EUR_Flow'].sum().sort_values()
        for pair, pair_flow in day_pairs.items():
            if abs(pair_flow) > 100:
                print(f"         {pair}: {pair_flow:+.2f}€")
    
    # Calcul théorique vs réel
    print(f"\n🎯 DIAGNOSTIC FINAL")
    expected_balance = starting_capital + total_eur_flow
    actual_balance = 19200
    missing_amount = actual_balance - expected_balance
    
    print(f"   Balance théorique (export): {expected_balance:,.2f}€")
    print(f"   Balance réelle (compte):    {actual_balance:,.2f}€")
    print(f"   Écart inexpliqué:           {missing_amount:+.2f}€")
    
    if abs(missing_amount) > 100:
        print(f"\n💡 HYPOTHÈSES SUR L'ÉCART:")
        print(f"   1. Positions ouvertes avec pertes latentes")
        print(f"   2. Frais de financement overnight non inclus")
        print(f"   3. Autres frais Binance non listés")
        print(f"   4. Période d'export incomplète")
        print(f"   5. Retraits/dépôts non inclus dans l'export")
    
    return {
        'expected_balance': expected_balance,
        'actual_balance': actual_balance,
        'missing_amount': missing_amount,
        'total_fees': total_fees,
        'total_flow': total_eur_flow
    }

if __name__ == "__main__":
    result = analyze_real_balance_from_binance('binance_export_20250720.csv')
