#!/usr/bin/env python3
"""
Script pour analyser les grosses pertes des dernier        print('\n🚨 TOP 15 PLUS GROSSES PERTES (3 derniers jours):')
        print('-' * 60)
        cursor.execute('''
        SELECT entry_time, symbol, entry_price, exit_price, pnl_amount, exit_reason,
               quantity, pnl_percent
        FROM trades 
        WHERE pnl_amount < 0 AND entry_time >= ?
        ORDER BY pnl_amount ASC
        LIMIT 15
        ''', (yesterday.strftime('%Y-%m-%d'),)) exécuter sur le VPS pour analyser la vraie base de données
"""

import sqlite3
from datetime import datetime, timedelta


def analyze_recent_losses():
    """Analyse les trades des derniers jours pour identifier les grosses pertes"""
    
    print('🔍 ANALYSE DES TRADES DES 3 DERNIERS JOURS')
    print('=' * 60)
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect('/opt/toTheMoon_tradebot/trading_bot.db')
        cursor = conn.cursor()
        
        # Récupérer les trades des 3 derniers jours
        yesterday = datetime.now() - timedelta(days=3)
        query = '''
        SELECT entry_time, exit_time, symbol, entry_price, exit_price, pnl_amount, 
               exit_reason, quantity, pnl_percent
        FROM trades 
        WHERE entry_time >= ? 
        ORDER BY entry_time DESC
        '''
        
        cursor.execute(query, (yesterday.strftime('%Y-%m-%d'),))
        trades = cursor.fetchall()
        
        print(f"📊 Nombre total de trades: {len(trades)}")
        
        # Grouper par jour
        daily_pnl = {}
        for trade in trades:
            date = trade[0][:10]  # Extraire la date
            pnl = float(trade[5]) if trade[5] else 0
            
            if date not in daily_pnl:
                daily_pnl[date] = {'total': 0, 'trades': [], 'count': 0}
            
            daily_pnl[date]['total'] += pnl
            daily_pnl[date]['count'] += 1
            daily_pnl[date]['trades'].append({
                'time': trade[0][11:19],  # Heure
                'symbol': trade[2],
                'pnl': pnl,
                'reason': trade[6],
                'pnl_percent': round(float(trade[8]) if trade[8] else 0, 2),
                'quantity': float(trade[7]) if trade[7] else 0
            })
        
        # Afficher le résumé par jour
        for date in sorted(daily_pnl.keys(), reverse=True):
            data = daily_pnl[date]
            print(f'\n📅 {date}: {data["total"]:.2f} EUR ({data["count"]} trades)')
            
            # Grouper par raison de fermeture
            reasons = {}
            for t in data['trades']:
                reason = t['reason'] or 'NORMAL'
                if reason not in reasons:
                    reasons[reason] = {'count': 0, 'pnl': 0}
                reasons[reason]['count'] += 1
                reasons[reason]['pnl'] += t['pnl']
            
            for reason, stats in reasons.items():
                print(f'   📋 {reason}: {stats["count"]} trades, {stats["pnl"]:.2f} EUR')
            
            # Afficher les plus grosses pertes du jour
            day_losses = [t for t in data['trades'] if t['pnl'] < -10]  # Pertes > 10 EUR
            if day_losses:
                print(f'   🚨 Grosses pertes (> 10 EUR):')
                for loss in sorted(day_losses, key=lambda x: x['pnl']):
                    print(f'      {loss["time"]} {loss["symbol"]}: {loss["pnl"]:.2f} EUR ({loss["pnl_percent"]:.2f}%) - {loss["reason"]}')
        
        # Chercher les plus grosses pertes globales
        print('\n🚨 TOP 15 PLUS GROSSES PERTES (3 derniers jours):')
        print('-' * 60)
        cursor.execute('''
        SELECT opened_at, symbol, entry_price, exit_price, pnl_eur, close_reason,
               quantity, (exit_price - entry_price) / entry_price * 100 as pnl_percent
        FROM trades 
        WHERE pnl_eur < 0 AND opened_at >= ?
        ORDER BY pnl_eur ASC
        LIMIT 15
        ''', (yesterday.strftime('%Y-%m-%d'),))
        
        big_losses = cursor.fetchall()
        for i, loss in enumerate(big_losses, 1):
            print(f'{i:2}. {loss[0]} | {loss[1]:8} | {loss[4]:8.2f} EUR ({loss[7]:6.2f}%) | {loss[5]:15} | Qty: {loss[6]:.6f}')
        
        # Analyser les raisons de fermeture
        print('\n📊 ANALYSE DES RAISONS DE FERMETURE:')
        print('-' * 40)
        cursor.execute('''
        SELECT exit_reason, COUNT(*) as count, SUM(pnl_amount) as total_pnl, AVG(pnl_amount) as avg_pnl
        FROM trades 
        WHERE entry_time >= ?
        GROUP BY exit_reason
        ORDER BY total_pnl ASC
        ''', (yesterday.strftime('%Y-%m-%d'),))
        
        reasons_stats = cursor.fetchall()
        for reason_stat in reasons_stats:
            reason = reason_stat[0] or 'NORMAL'
            print(f'{reason:20} | {reason_stat[1]:3} trades | Total: {reason_stat[2]:8.2f} EUR | Moy: {reason_stat[3]:6.2f} EUR')
        
        # Analyser les stop loss qui n'ont pas fonctionné
        print('\n⚠️ ANALYSE DES STOP LOSS:')
        print('-' * 30)
        cursor.execute('''
        SELECT entry_time, symbol, entry_price, exit_price, pnl_amount, exit_reason,
               pnl_percent
        FROM trades 
        WHERE pnl_amount < -100 AND entry_time >= ?
        ORDER BY pnl_amount ASC
        ''', (yesterday.strftime('%Y-%m-%d'),))
        
        big_stop_losses = cursor.fetchall()
        if big_stop_losses:
            print("🔥 Trades avec pertes > 100 EUR (stop loss défaillant?):")
            for loss in big_stop_losses:
                expected_sl = -0.25  # Stop loss attendu à -0.25%
                actual_loss = loss[6]
                print(f'{loss[0]} | {loss[1]} | {loss[4]:.2f} EUR ({loss[6]:.2f}%) | Attendu: {expected_sl}% | {loss[5]}')
        else:
            print("✅ Aucune perte > 100 EUR trouvée")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    analyze_recent_losses()
