#!/usr/bin/env python3
"""
Comparaison entre la base de données bot et l'export Binance
Identifie les désynchronisations et incohérences
"""

import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd


def analyze_bot_database(db_path="data/trading_bot.db"):
    """Analyse la base de données du bot"""
    print("🤖 ANALYSE BASE DE DONNÉES BOT")
    print("=" * 50)
    
    with sqlite3.connect(db_path) as conn:
        # Récupération de tous les trades
        query = """
            SELECT symbol, side, entry_price, exit_price, quantity, 
                   entry_time, exit_time, status, pnl_amount, pnl_percent,
                   capital_engaged, exit_reason
            FROM trades 
            ORDER BY entry_time DESC
        """
        
        bot_df = pd.read_sql_query(query, conn)
        
        if len(bot_df) == 0:
            print("❌ Aucun trade trouvé dans la base de données")
            return None
        
        # Conversion des dates
        bot_df['entry_time'] = pd.to_datetime(bot_df['entry_time'])
        bot_df['exit_time'] = pd.to_datetime(bot_df['exit_time'])
        bot_df['entry_date'] = bot_df['entry_time'].dt.date
        bot_df['exit_date'] = bot_df['exit_time'].dt.date
        
        print(f"📊 STATISTIQUES BOT DB")
        print(f"   Total trades: {len(bot_df):,}")
        print(f"   Période: {bot_df['entry_date'].min()} → {bot_df['entry_date'].max()}")
        print(f"   Statuts: {bot_df['status'].value_counts().to_dict()}")
        
        # Analyse par statut
        open_trades = bot_df[bot_df['status'] == 'OPEN']
        closed_trades = bot_df[bot_df['status'] != 'OPEN']
        
        print(f"\n📈 TRADES FERMÉS ({len(closed_trades)})")
        if len(closed_trades) > 0:
            # P&L par jour (trades fermés)
            closed_daily = closed_trades.groupby('exit_date').agg({
                'pnl_amount': 'sum',
                'symbol': 'count'
            }).round(2)
            closed_daily.columns = ['P&L_EUR', 'Nb_Trades']
            
            for date, row in closed_daily.tail(10).iterrows():  # 10 derniers jours
                pnl_percent = (row['P&L_EUR'] / 19650) * 100
                status = "🛑" if pnl_percent <= -2.0 else "✅" if pnl_percent > 0 else "⚠️"
                print(f"   {date}: {row['P&L_EUR']:+.2f}€ ({pnl_percent:+.2f}%) - {row['Nb_Trades']} trades {status}")
        
        print(f"\n📊 POSITIONS OUVERTES ({len(open_trades)})")
        if len(open_trades) > 0:
            # Résumé par symbole
            open_summary = open_trades.groupby('symbol').agg({
                'capital_engaged': 'sum',
                'symbol': 'count'
            }).round(2)
            open_summary.columns = ['Capital_Engagé', 'Nb_Positions']
            
            total_engaged = 0
            for symbol, row in open_summary.iterrows():
                print(f"   {symbol}: {row['Nb_Positions']} pos = {row['Capital_Engagé']:.2f}€")
                total_engaged += row['Capital_Engagé']
            
            print(f"   TOTAL ENGAGÉ: {total_engaged:.2f}€")
            
            # Surexposition
            capital_limit = 19650 * 0.20  # 20%
            overexposed = open_summary[open_summary['Capital_Engagé'] > capital_limit]
            if len(overexposed) > 0:
                print(f"   🚨 SUREXPOSITION: {len(overexposed)} symbols au-dessus de {capital_limit:.0f}€")
        
        return bot_df

def compare_with_binance(bot_df, binance_csv="binance_export_20250720.csv"):
    """Compare avec l'export Binance"""
    print(f"\n🔄 COMPARAISON BOT vs BINANCE")
    print("=" * 50)
    
    # Lecture Binance
    binance_df = pd.read_csv(binance_csv, sep=';')
    binance_df['Date(UTC)'] = pd.to_datetime(binance_df['Date(UTC)'])
    binance_df['Date'] = binance_df['Date(UTC)'].dt.date
    
    # P&L Binance par jour
    binance_df['PnL'] = binance_df.apply(lambda row: 
        row['Total'] if row['Type'] == 'SELL' else -row['Total'], axis=1)
    
    binance_daily = binance_df.groupby('Date')['PnL'].sum()
    
    # P&L Bot par jour (trades fermés seulement)
    closed_trades = bot_df[bot_df['status'] != 'OPEN']
    if len(closed_trades) > 0:
        bot_daily = closed_trades.groupby('exit_date')['pnl_amount'].sum()
    else:
        bot_daily = pd.Series(dtype=float)
    
    print(f"📊 COMPARAISON QUOTIDIENNE (derniers 7 jours)")
    
    # Dates communes
    last_7_days = [(date.today() - timedelta(days=i)) for i in range(7)]
    
    for check_date in reversed(last_7_days):
        binance_pnl = binance_daily.get(check_date, 0)
        bot_pnl = bot_daily.get(check_date, 0)
        
        diff = abs(binance_pnl - bot_pnl)
        status = "✅" if diff < 1 else "⚠️" if diff < 50 else "🚨"
        
        print(f"   {check_date}:")
        print(f"      Binance: {binance_pnl:+.2f}€")
        print(f"      Bot DB:  {bot_pnl:+.2f}€")
        print(f"      Diff:    {diff:.2f}€ {status}")
    
    # Recherche des incohérences majeures
    print(f"\n🔍 INCOHÉRENCES DÉTECTÉES")
    
    # Total P&L
    total_binance = binance_df['PnL'].sum()
    total_bot = closed_trades['pnl_amount'].sum() if len(closed_trades) > 0 else 0
    
    print(f"   P&L total Binance: {total_binance:+.2f}€")
    print(f"   P&L total Bot:     {total_bot:+.2f}€")
    print(f"   Différence:        {abs(total_binance - total_bot):+.2f}€")
    
    # Positions ouvertes fantômes
    open_trades = bot_df[bot_df['status'] == 'OPEN']
    if len(open_trades) > 0:
        print(f"\n🚨 POSITIONS FANTÔMES")
        print(f"   {len(open_trades)} positions ouvertes dans la DB")
        print(f"   Mais 0 positions sur Binance selon l'utilisateur")
        print(f"   Capital fantôme: {open_trades['capital_engaged'].sum():.2f}€")
    
    return {
        'bot_trades': len(bot_df),
        'binance_trades': len(binance_df),
        'open_positions': len(open_trades),
        'pnl_diff': abs(total_binance - total_bot)
    }

def main():
    print("🔍 ANALYSE COMPLÈTE : BOT DB vs BINANCE")
    print("=" * 60)
    
    # 1. Analyse de la base bot
    bot_df = analyze_bot_database()
    
    if bot_df is None:
        return
    
    # 2. Comparaison avec Binance
    try:
        comparison = compare_with_binance(bot_df)
        
        print(f"\n📋 RÉSUMÉ FINAL")
        print(f"   Trades bot: {comparison['bot_trades']}")
        print(f"   Trades Binance: {comparison['binance_trades']}")
        print(f"   Positions ouvertes: {comparison['open_positions']}")
        print(f"   Différence P&L: {comparison['pnl_diff']:.2f}€")
        
        if comparison['open_positions'] > 0:
            print(f"\n⚡ ACTION RECOMMANDÉE:")
            print(f"   1. Arrêter le bot")
            print(f"   2. Nettoyer les positions fantômes")
            print(f"   3. Redémarrer avec base propre")
            
    except Exception as e:
        print(f"❌ Erreur comparaison: {e}")

if __name__ == "__main__":
    main()
