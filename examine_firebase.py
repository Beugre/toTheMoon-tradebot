"""
Script pour examiner le contenu des trades Firebase
"""

import asyncio
from datetime import datetime, timedelta

from utils.firebase_logger import FirebaseLogger


async def examine_firebase_trades():
    """Examine le contenu des trades Firebase"""
    
    print("🔍 Examen des trades Firebase")
    print("=" * 40)
    
    try:
        firebase_logger = FirebaseLogger()
        print("✅ Firebase initialisé")
        
        # Récupération des trades des dernières 24h
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        docs = firebase_logger.firestore_db.collection("trades").where(
            "timestamp", ">=", start_date.isoformat()
        ).where(
            "timestamp", "<=", end_date.isoformat()
        ).stream()
        
        trades = []
        for doc in docs:
            trade_data = doc.to_dict()
            trade_data['doc_id'] = doc.id
            trades.append(trade_data)
        
        print(f"\n📊 {len(trades)} trades trouvés dans Firebase")
        print("=" * 40)
        
        for i, trade in enumerate(trades, 1):
            print(f"\n🔸 Trade #{i}:")
            print(f"   📅 Timestamp: {trade.get('timestamp')}")
            print(f"   🪙 Pair: {trade.get('pair')}")
            print(f"   📈 Action: {trade.get('action', 'N/A')}")
            print(f"   💰 Entry Price: {trade.get('entry_price')}")
            print(f"   📊 Size: {trade.get('size')}")
            print(f"   🆔 Binance Order ID: {trade.get('binance_order_id', 'MANQUANT!')}")
            print(f"   🎯 Trade ID: {trade.get('trade_id')}")
            print(f"   🔄 Direction: {trade.get('direction')}")
            
            # Match key calculation
            binance_id = trade.get('binance_order_id', 'UNKNOWN')
            timestamp = int(datetime.fromisoformat(trade['timestamp']).timestamp()) if trade.get('timestamp') else 0
            match_key = f"{trade.get('pair')}_{binance_id}_{timestamp}"
            print(f"   🔑 Match Key: {match_key}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(examine_firebase_trades())
if __name__ == "__main__":
    asyncio.run(examine_firebase_trades())
