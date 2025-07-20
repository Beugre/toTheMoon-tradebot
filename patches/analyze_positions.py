import sqlite3
from datetime import datetime

with sqlite3.connect('data/trading_bot.db') as conn:
    cursor = conn.cursor()
    
    print('=== POSITIONS OUVERTES RÉCENTES ===')
    cursor.execute("""
        SELECT symbol, side, entry_price, quantity, capital_engaged, entry_time 
        FROM trades 
        WHERE status = 'OPEN' 
        ORDER BY entry_time DESC 
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        symbol, side, price, qty, capital, entry_time = row
        print(f'{symbol} {side} - {price:.4f} x {qty:.4f} = {capital:.2f}€ ({entry_time})')
    
    print('\n=== RÉSUMÉ PAR SYMBOLE ===')
    cursor.execute("""
        SELECT symbol, COUNT(*), SUM(capital_engaged) 
        FROM trades 
        WHERE status = 'OPEN' 
        GROUP BY symbol 
        ORDER BY SUM(capital_engaged) DESC
    """)
    
    total = 0
    for symbol, count, capital in cursor.fetchall():
        print(f'{symbol}: {count} positions = {capital:.2f}€')
        total += capital
    
    print(f'\nTOTAL CAPITAL ENGAGÉ: {total:.2f}€')
    
    # Vérification du surexposition
    print('\n=== VÉRIFICATION SUREXPOSITION ===')
    capital_limit = 19650 * 0.20  # 20% du capital
    print(f'Limite par asset: {capital_limit:.2f}€')
    
    cursor.execute("""
        SELECT symbol, SUM(capital_engaged) as total_exposure
        FROM trades 
        WHERE status = 'OPEN' 
        GROUP BY symbol 
        HAVING total_exposure > ?
        ORDER BY total_exposure DESC
    """, (capital_limit,))
    
    overexposed = cursor.fetchall()
    if overexposed:
        print('🚨 SUREXPOSITION DÉTECTÉE:')
        for symbol, exposure in overexposed:
            print(f'  {symbol}: {exposure:.2f}€ (limite: {capital_limit:.2f}€)')
    else:
        print('✅ Aucune surexposition')
