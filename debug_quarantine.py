"""
Debug des ordres en quarantaine Firebase
Analyser pourquoi pnl_amount manque
"""

from datetime import datetime, timedelta

import firebase_admin
import pandas as pd
from firebase_admin import credentials, firestore


def init_firebase():
    """Initialiser Firebase"""
    try:
        app = firebase_admin.get_app()
        return firestore.client(app)
    except ValueError:
        cred = credentials.Certificate('firebase_credentials.json')
        app = firebase_admin.initialize_app(cred)
        return firestore.client(app)

def check_quarantine_orders():
    """Vérifier les ordres en quarantaine"""
    db = init_firebase()
    
    print("🔍 Analyse des ordres en quarantaine...")
    
    # Récupérer les ordres en quarantaine récents (24h)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    docs = db.collection("quarantine").where(
        "timestamp", ">=", start_time.isoformat()
    ).order_by("timestamp").stream()
    
    quarantine_orders = []
    for doc in docs:
        data = doc.to_dict()
        quarantine_orders.append({
            'doc_id': doc.id,
            'timestamp': data.get('timestamp'),
            'pair': data.get('pair'),
            'action': data.get('action'),
            'entry_price': data.get('entry_price'),
            'exit_price': data.get('exit_price'),
            'size': data.get('size'),
            'pnl_amount': data.get('pnl_amount'),
            'reason': data.get('reason'),
            'binance_order_id': data.get('binance_order_id'),
            'trailing_data': data.get('trailing_data', {}),
            'raw_data': str(data)  # Pour debug complet
        })
    
    if not quarantine_orders:
        print("✅ Aucun ordre en quarantaine récent")
        return
    
    print(f"🚨 {len(quarantine_orders)} ordres en quarantaine trouvés:\n")
    
    for order in quarantine_orders:
        print("=" * 60)
        print(f"📅 Timestamp: {order['timestamp']}")
        print(f"💰 Paire: {order['pair']}")
        print(f"🎯 Action: {order['action']}")
        print(f"💵 Entry: {order['entry_price']}")
        print(f"💵 Exit: {order['exit_price']}")
        print(f"📊 Size: {order['size']}")
        print(f"💎 PnL: {order['pnl_amount']}")
        print(f"❌ Raison quarantaine: {order['reason']}")
        print(f"🔢 Binance Order ID: {order['binance_order_id']}")
        
        if order['trailing_data']:
            print(f"📈 Trailing Data: {order['trailing_data']}")
        
        # Calculer PnL si manquant
        if order['entry_price'] and order['exit_price'] and order['size']:
            try:
                entry = float(order['entry_price'])
                exit_price = float(order['exit_price'])
                size = float(order['size'])
                
                if order['action'] == 'SELL':
                    calculated_pnl = (exit_price - entry) * size
                else:  # BUY (short close)
                    calculated_pnl = (entry - exit_price) * size
                
                print(f"🧮 PnL calculé: {calculated_pnl:.4f} USDC")
                
                # Calculer le pourcentage
                pnl_percent = (calculated_pnl / (entry * size)) * 100
                print(f"📈 PnL %: {pnl_percent:.2f}%")
                
            except Exception as e:
                print(f"❌ Erreur calcul PnL: {e}")
        
        print()

if __name__ == "__main__":
    check_quarantine_orders()
if __name__ == "__main__":
    check_quarantine_orders()
