#!/usr/bin/env python3
"""
Script pour supprimer les trades aberrants de PENGUUSDC
"""

import logging
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    from utils.firebase_config import FIREBASE_CONFIG
    
    def delete_aberrant_pengu_trades():
        """Supprime les trades aberrants et analyse les incohérences"""
        
        # Initialisation Firebase
        try:
            if firebase_admin._apps:
                app = firebase_admin.get_app()
            else:
                cred = credentials.Certificate(FIREBASE_CONFIG.CREDENTIALS_PATH)
                app = firebase_admin.initialize_app(cred, {
                    'projectId': FIREBASE_CONFIG.PROJECT_ID
                })
            
            db = firestore.client()
            print("✅ Firebase connecté")
            
        except Exception as e:
            print(f"❌ Erreur connexion Firebase: {e}")
            return
        
        # Rechercher TOUS les trades aberrants (pas seulement PENGUUSDC)
        try:
            print("\n🔍 Recherche de TOUS les trades aberrants...")
            
            # Query pour tous les trades
            trades_ref = db.collection('trades')
            docs = trades_ref.stream()
            
            aberrant_trades = []
            total_trades = 0
            
            for doc in docs:
                total_trades += 1
                data = doc.to_dict()
                
                # Calculer le P&L réel
                capital_before = data.get('capital_before', 0)
                capital_after = data.get('capital_after', 0)
                real_pnl = capital_after - capital_before
                
                # Considérer comme aberrant si perte > 50 USDC ou gain > 50 USDC
                if abs(real_pnl) > 50:
                    aberrant_trades.append({
                        'doc_id': doc.id,
                        'pair': data.get('pair'),
                        'real_pnl': real_pnl,
                        'capital_before': capital_before,
                        'capital_after': capital_after,
                        'timestamp': data.get('timestamp'),
                        'exit_reason': data.get('exit_reason'),
                        'execution_source': data.get('execution_source'),
                        'entry_price': data.get('entry_price'),
                        'exit_price': data.get('exit_price'),
                        'size': data.get('size')
                    })
                    print(f"   🚨 Trade aberrant: {data.get('pair')} | P&L={real_pnl:+.4f} | {data.get('timestamp')}")
            
            print(f"\n📊 Résumé GÉNÉRAL:")
            print(f"   - Total trades: {total_trades}")
            print(f"   - Trades aberrants (>50 USDC): {len(aberrant_trades)}")
            
            if len(aberrant_trades) > 0:
                print(f"\n🔍 DÉTAILS DES TRADES ABERRANTS:")
                for i, trade in enumerate(aberrant_trades):
                    print(f"\n   {i+1}. {trade['pair']} - {trade['timestamp']}")
                    print(f"      💰 P&L: {trade['real_pnl']:+.4f} USDC")
                    print(f"      📊 Capital: {trade['capital_before']} → {trade['capital_after']}")
                    print(f"      💹 Prix: {trade['entry_price']} → {trade['exit_price']}")
                    print(f"      📏 Size: {trade['size']}")
                    print(f"      🚪 Exit reason: {trade['exit_reason']}")
                    print(f"      🤖 Source: {trade['execution_source']}")
                
                print(f"\n❓ Supprimer {len(aberrant_trades)} trades aberrants ? (y/N): ")
                response = input().strip().lower()
                
                if response == 'y':
                    print("\n🗑️ Suppression des trades aberrants...")
                    
                    batch = db.batch()
                    for trade in aberrant_trades:
                        doc_ref = db.collection('trades').document(trade['doc_id'])
                        batch.delete(doc_ref)
                        print(f"   ❌ Suppression: {trade['pair']} P&L={trade['real_pnl']:+.4f}")
                    
                    batch.commit()
                    print(f"\n✅ {len(aberrant_trades)} trades aberrants supprimés !")
                else:
                    print("\n❌ Suppression annulée")
            else:
                print("\n✅ Aucun trade aberrant trouvé")
                
        except Exception as e:
            print(f"❌ Erreur suppression: {e}")
    
    if __name__ == "__main__":
        delete_aberrant_pengu_trades()
        
except ImportError:
    print("❌ Firebase non installé. Ce script nécessite firebase-admin.")
    print("💡 Installez avec: pip install firebase-admin")
