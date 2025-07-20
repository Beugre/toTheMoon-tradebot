#!/usr/bin/env python3
"""
Analyse détaillée des 19-20 juillet pour retrouver les -800€
"""

from datetime import date, datetime

import pandas as pd


def analyze_last_two_days(csv_path):
    """Analyse détaillée des 19-20 juillet"""
    print("🔍 RECHERCHE DES -800€ - 19-20 JUILLET")
    print("=" * 50)
    
    # Lecture du CSV
    df = pd.read_csv(csv_path, sep=';')
    df['Date(UTC)'] = pd.to_datetime(df['Date(UTC)'])
    df['Date'] = df['Date(UTC)'].dt.date
    
    # Filtre sur les 2 derniers jours
    target_dates = [date(2025, 7, 19), date(2025, 7, 20)]
    recent_trades = df[df['Date'].isin(target_dates)].copy()
    
    print(f"📊 DONNÉES FILTRÉES")
    print(f"   Trades 19-20 juillet: {len(recent_trades):,}")
    
    # Calcul du flux EUR (réel)
    recent_trades['EUR_Flow'] = recent_trades.apply(lambda row: 
        row['Total'] + row['Fee'] if row['Type'] == 'SELL' 
        else -(row['Total'] + row['Fee']), axis=1)
    
    # Analyse par jour
    for target_date in target_dates:
        day_trades = recent_trades[recent_trades['Date'] == target_date].copy()
        
        if len(day_trades) == 0:
            continue
            
        print(f"\n📅 {target_date.strftime('%d JUILLET %Y')}")
        print(f"   Transactions: {len(day_trades):,}")
        
        # Flux EUR total
        daily_flow = day_trades['EUR_Flow'].sum()
        print(f"   Flux EUR net: {daily_flow:+.2f}€")
        
        # Analyse par heure
        day_trades['Hour'] = day_trades['Date(UTC)'].dt.hour
        hourly_flows = day_trades.groupby('Hour')['EUR_Flow'].sum()
        
        print(f"   Répartition horaire:")
        for hour, flow in hourly_flows.items():
            if abs(flow) > 100:  # Seulement les heures significatives
                status = "🚨" if flow < -500 else "📉" if flow < 0 else "📈"
                print(f"      {hour:02d}h: {flow:+8.2f}€ {status}")
        
        # Recherche des minutes catastrophiques
        print(f"   Minutes avec pertes >200€:")
        day_trades['Minute_Key'] = day_trades['Date(UTC)'].dt.strftime('%H:%M')
        minute_flows = day_trades.groupby('Minute_Key')['EUR_Flow'].sum()
        bad_minutes = minute_flows[minute_flows < -200].sort_values()
        
        for minute, flow in bad_minutes.items():
            print(f"      {minute}: {flow:+.2f}€")
            
            # Détail de cette minute
            minute_trades = day_trades[day_trades['Minute_Key'] == minute]
            pairs_in_minute = minute_trades.groupby('Pair')['EUR_Flow'].sum()
            for pair, pair_flow in pairs_in_minute.items():
                if abs(pair_flow) > 50:
                    print(f"         {pair}: {pair_flow:+.2f}€")
    
    # Calcul cumulatif sur les 2 jours
    print(f"\n📈 ÉVOLUTION CUMULATIVE (19-20 JUILLET)")
    recent_sorted = recent_trades.sort_values('Date(UTC)')
    recent_sorted['Cumulative_Flow'] = recent_sorted['EUR_Flow'].cumsum()
    
    # Points clés
    start_balance = 20000  # Supposé
    min_point = recent_sorted['Cumulative_Flow'].min()
    max_point = recent_sorted['Cumulative_Flow'].max()
    final_point = recent_sorted['Cumulative_Flow'].iloc[-1]
    
    min_time = recent_sorted.loc[recent_sorted['Cumulative_Flow'].idxmin(), 'Date(UTC)']
    max_time = recent_sorted.loc[recent_sorted['Cumulative_Flow'].idxmax(), 'Date(UTC)']
    
    print(f"   Point le plus bas: {min_time} = {start_balance + min_point:,.2f}€ ({min_point:+.2f}€)")
    print(f"   Point le plus haut: {max_time} = {start_balance + max_point:,.2f}€ ({max_point:+.2f}€)")
    print(f"   Solde final: {start_balance + final_point:,.2f}€ ({final_point:+.2f}€)")
    
    # Vérification de l'hypothèse -800€
    print(f"\n🎯 RECHERCHE DES -800€")
    
    # Y a-t-il eu un moment où le compte était à 19,200€ ?
    if start_balance + min_point <= 19200:
        print(f"   ✅ TROUVÉ! À {min_time}, le solde était de {start_balance + min_point:,.2f}€")
        print(f"   Cela correspond à une perte de {20000 - (start_balance + min_point):,.2f}€ depuis 20,000€")
    else:
        print(f"   ❌ Aucun moment trouvé où le solde était à 19,200€ ou moins")
    
    # Recherche de grosses pertes individuelles
    print(f"\n💸 GROSSES PERTES INDIVIDUELLES (19-20 JUILLET)")
    big_losses = recent_trades[recent_trades['EUR_Flow'] < -200].sort_values('EUR_Flow')
    
    if len(big_losses) > 0:
        total_big_losses = big_losses['EUR_Flow'].sum()
        print(f"   {len(big_losses)} transactions avec perte >200€ = {total_big_losses:+.2f}€")
        
        for _, trade in big_losses.head(10).iterrows():
            print(f"      {trade['Date(UTC)']} {trade['Pair']}: {trade['EUR_Flow']:+.2f}€")
    
    # Résumé final
    total_flow_2_days = recent_trades['EUR_Flow'].sum()
    print(f"\n📋 RÉSUMÉ 19-20 JUILLET")
    print(f"   Flux total: {total_flow_2_days:+.2f}€")
    print(f"   Transactions: {len(recent_trades):,}")
    
    if abs(total_flow_2_days + 800) < 100:
        print(f"   🎯 POSSIBLE: Les -800€ correspondent aux trades de ces 2 jours")
    else:
        print(f"   ❓ Les -800€ ne correspondent PAS aux trades de ces 2 jours")
    
    return recent_trades

if __name__ == "__main__":
    df = analyze_last_two_days('binance_export_20250720.csv')
