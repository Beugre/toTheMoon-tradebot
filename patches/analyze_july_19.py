#!/usr/bin/env python3
"""
Analyse spécifique du 19 juillet 2025 pour comprendre les -800€
"""

from datetime import datetime

import pandas as pd


def analyze_july_19():
    print("🔍 ANALYSE DÉTAILLÉE DU 19 JUILLET 2025")
    print("=" * 50)
    
    # Lecture du CSV
    df = pd.read_csv('binance_export_20250720.csv', sep=';')
    df['Date(UTC)'] = pd.to_datetime(df['Date(UTC)'])
    
    # Filtre 19 juillet uniquement
    july_19 = df[df['Date(UTC)'].dt.date.astype(str) == '2025-07-19'].copy()
    
    print(f"📊 STATISTIQUES 19 JUILLET")
    print(f"   Nombre de trades: {len(july_19):,}")
    print(f"   Première transaction: {july_19['Date(UTC)'].min()}")
    print(f"   Dernière transaction: {july_19['Date(UTC)'].max()}")
    
    # Calcul P&L
    july_19['PnL'] = july_19.apply(lambda row: 
        row['Total'] if row['Type'] == 'SELL' else -row['Total'], axis=1)
    
    total_pnl = july_19['PnL'].sum()
    print(f"   P&L total: {total_pnl:+.2f}€")
    
    # Analyse par paire
    print(f"\n📈 RÉPARTITION PAR PAIRE")
    pair_analysis = july_19.groupby('Pair').agg({
        'PnL': 'sum',
        'Pair': 'count',
        'Total': 'sum'
    }).round(2)
    pair_analysis.columns = ['P&L_EUR', 'Nb_Trades', 'Volume_EUR']
    pair_analysis = pair_analysis.sort_values('P&L_EUR')
    
    for pair, row in pair_analysis.iterrows():
        status = "📈" if row['P&L_EUR'] > 0 else "📉" if row['P&L_EUR'] < -100 else "➖"
        print(f"   {pair}: {row['P&L_EUR']:+.2f}€ ({row['Nb_Trades']} trades) {status}")
    
    # Analyse par heure
    print(f"\n⏰ RÉPARTITION PAR HEURE")
    july_19['Hour'] = july_19['Date(UTC)'].dt.hour
    hourly_analysis = july_19.groupby('Hour').agg({
        'PnL': 'sum',
        'Pair': 'count'
    }).round(2)
    hourly_analysis.columns = ['P&L_EUR', 'Nb_Trades']
    
    for hour, row in hourly_analysis.iterrows():
        if row['P&L_EUR'] < -100:  # Heures avec grosses pertes
            print(f"   {hour:02d}h: {row['P&L_EUR']:+.2f}€ ({row['Nb_Trades']} trades) 🚨")
        elif row['P&L_EUR'] > 100:  # Heures avec gros gains
            print(f"   {hour:02d}h: {row['P&L_EUR']:+.2f}€ ({row['Nb_Trades']} trades) ✅")
    
    # Recherche des grosses pertes individuelles
    print(f"\n💸 GROSSES PERTES INDIVIDUELLES (>500€)")
    big_losses = july_19[july_19['PnL'] < -500].sort_values('PnL')
    
    if len(big_losses) > 0:
        total_big_losses = big_losses['PnL'].sum()
        print(f"   {len(big_losses)} trades avec perte >500€ = {total_big_losses:+.2f}€")
        
        for _, trade in big_losses.head(10).iterrows():
            print(f"      {trade['Date(UTC)']} {trade['Pair']}: {trade['PnL']:+.2f}€")
    else:
        print("   Aucune perte individuelle >500€")
    
    # Recherche par minute pour détecter les "crashes"
    print(f"\n🚨 MINUTES CATASTROPHIQUES")
    july_19['Minute_Key'] = july_19['Date(UTC)'].dt.strftime('%H:%M')
    minute_analysis = july_19.groupby('Minute_Key')['PnL'].sum().sort_values()
    
    worst_minutes = minute_analysis[minute_analysis < -100]
    if len(worst_minutes) > 0:
        print(f"   {len(worst_minutes)} minutes avec perte >100€:")
        for minute, pnl in worst_minutes.head(10).items():
            print(f"      {minute}: {pnl:+.2f}€")
    
    # Calcul cumulé pour voir l'évolution
    print(f"\n📊 ÉVOLUTION CUMULATIVE")
    july_19_sorted = july_19.sort_values('Date(UTC)')
    july_19_sorted['PnL_Cumulative'] = july_19_sorted['PnL'].cumsum()
    
    # Points clés de la journée
    min_pnl = july_19_sorted['PnL_Cumulative'].min()
    max_pnl = july_19_sorted['PnL_Cumulative'].max()
    
    min_time = july_19_sorted.loc[july_19_sorted['PnL_Cumulative'].idxmin(), 'Date(UTC)']
    max_time = july_19_sorted.loc[july_19_sorted['PnL_Cumulative'].idxmax(), 'Date(UTC)']
    
    print(f"   Pire moment: {min_time} = {min_pnl:+.2f}€")
    print(f"   Meilleur moment: {max_time} = {max_pnl:+.2f}€")
    print(f"   Récupération: {max_pnl - min_pnl:+.2f}€")
    
    # HYPOTHÈSE sur les -800€
    print(f"\n🤔 HYPOTHÈSE SUR LES -800€")
    if abs(min_pnl) > 700:
        print(f"   💡 POSSIBLE: Vous avez vu le P&L à {min_time}")
        print(f"      P&L cumulé à ce moment: {min_pnl:+.2f}€")
        print(f"      Mais le bot a récupéré ensuite: {total_pnl:+.2f}€ final")
    else:
        print(f"   ❓ Les -800€ ne correspondent à aucun moment de la journée")
        print(f"   📝 Possible erreur d'affichage ou calcul P&L non-réalisé")
    
    return july_19

if __name__ == "__main__":
    df = analyze_july_19()
