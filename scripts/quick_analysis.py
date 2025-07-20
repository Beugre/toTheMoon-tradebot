#!/usr/bin/env python3
"""
Script d'analyse des pertes - Version corrigée
"""

import sqlite3
from datetime import datetime, timedelta


def main():
    print('🔍 ANALYSE DES TRADES - VPS')
    print('=' * 50)
    
    try:
        conn = sqlite3.connect('/opt/toTheMoon_tradebot/trading_bot.db')
        cursor = conn.cursor()
        
        # Derniers 5 jours
        since_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        # Compter les trades
        cursor.execute('SELECT COUNT(*) FROM trades WHERE entry_time >= ?', (since_date,))
        total_trades = cursor.fetchone()[0]
        print(f'📊 Total trades depuis {since_date}: {total_trades}')
        
        if total_trades == 0:
            print('❌ Aucun trade trouvé dans les 5 derniers jours')
            # Vérifier les derniers trades
            cursor.execute('SELECT entry_time, symbol, pnl_amount FROM trades ORDER BY entry_time DESC LIMIT 5')
            recent = cursor.fetchall()
            if recent:
                print('\n📅 Derniers trades dans la DB:')
                for trade in recent:
                    print(f'  {trade[0]} | {trade[1]} | {trade[2]:.2f} EUR')
            else:
                print('❌ Aucun trade trouvé dans toute la base')
            return
        
        # Résumé par jour
        cursor.execute('''
        SELECT DATE(entry_time) as day, 
               COUNT(*) as trades_count,
               SUM(pnl_amount) as daily_pnl,
               AVG(pnl_amount) as avg_pnl
        FROM trades 
        WHERE entry_time >= ?
        GROUP BY DATE(entry_time)
        ORDER BY day DESC
        ''', (since_date,))
        
        daily_stats = cursor.fetchall()
        print('\n📈 PERFORMANCE PAR JOUR:')
        print('-' * 40)
        for day in daily_stats:
            print(f'{day[0]} | {day[1]:3} trades | {day[2]:8.2f} EUR | Moy: {day[3]:6.2f}')
        
        # Top pertes
        cursor.execute('''
        SELECT entry_time, symbol, pnl_amount, exit_reason, pnl_percent
        FROM trades 
        WHERE pnl_amount < 0 AND entry_time >= ?
        ORDER BY pnl_amount ASC
        LIMIT 10
        ''', (since_date,))
        
        losses = cursor.fetchall()
        if losses:
            print('\n🚨 TOP 10 PERTES:')
            print('-' * 40)
            for i, loss in enumerate(losses, 1):
                print(f'{i:2}. {loss[0][:19]} | {loss[1]:8} | {loss[2]:8.2f} EUR ({loss[4]:6.2f}%) | {loss[3]}')
        
        # Analyse des raisons de sortie
        cursor.execute('''
        SELECT exit_reason, COUNT(*) as count, SUM(pnl_amount) as total
        FROM trades 
        WHERE entry_time >= ?
        GROUP BY exit_reason
        ORDER BY total ASC
        ''', (since_date,))
        
        reasons = cursor.fetchall()
        if reasons:
            print('\n📊 RAISONS DE SORTIE:')
            print('-' * 30)
            for reason in reasons:
                reason_name = reason[0] if reason[0] else 'NORMAL'
                print(f'{reason_name:20} | {reason[1]:3} | {reason[2]:8.2f} EUR')
        
        # Chercher les gros stop loss
        cursor.execute('''
        SELECT entry_time, symbol, pnl_amount, pnl_percent, exit_reason
        FROM trades 
        WHERE pnl_amount < -50 AND entry_time >= ?
        ORDER BY pnl_amount ASC
        ''', (since_date,))
        
        big_losses = cursor.fetchall()
        if big_losses:
            print('\n⚠️ PERTES > 50 EUR:')
            print('-' * 35)
            for loss in big_losses:
                print(f'{loss[0][:19]} | {loss[1]} | {loss[2]:.2f} EUR ({loss[3]:.2f}%) | {loss[4]}')
        else:
            print('\n✅ Aucune perte > 50 EUR trouvée')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')

if __name__ == '__main__':
    main()
