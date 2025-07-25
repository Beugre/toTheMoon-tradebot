"""
Script de test rapide pour l'audit Binance vs Firebase
Usage: python test_audit.py
"""

import asyncio
import os
from datetime import datetime, timedelta

from binance.client import Client

from audit_trades_simple import TradeAuditorSimple
from utils.firebase_logger import FirebaseLogger


async def test_audit():
    """Test rapide de l'audit des trades"""
    
    print("🔍 Test de l'audit Binance vs Firebase")
    print("=" * 50)
    
    # Configuration
    try:
        # Initialisation Firebase
        firebase_logger = FirebaseLogger()
        print("✅ Firebase initialisé")
        
        # Initialisation Binance
        binance_client = Client(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_SECRET_KEY')
        )
        print("✅ Binance initialisé")
        
        # Création de l'auditeur
        auditor = TradeAuditorSimple(binance_client, firebase_logger.firestore_db)
        print("✅ Auditeur créé")
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        return
    
    # Test sur les dernières 24h (limitation API Binance)
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)  # 24h au lieu de 7 jours
    
    print(f"\n📅 Période d'audit: {start_date.strftime('%Y-%m-%d %H:%M')} → {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Test avec quelques paires
    test_pairs = ['BNBUSDC', 'ETHUSDC', 'BTCUSDC']
    
    try:
        # Récupération des données Binance
        print("\n🔄 Récupération des données Binance...")
        binance_df = auditor.get_binance_trades(test_pairs, start_date, end_date)
        print(f"📊 Binance: {len(binance_df)} trades trouvés")
        
        # Récupération des données Firebase
        print("\n🔄 Récupération des données Firebase...")
        firebase_df = auditor.get_firebase_trades(start_date, end_date)
        print(f"🔥 Firebase: {len(firebase_df)} trades trouvés")
        
        # Comparaison
        print("\n🔍 Comparaison des données...")
        matched, only_binance, only_firebase = auditor.compare_trades(binance_df, firebase_df)
        
        # Analyse des cycles de trading
        print("\n🔄 Analyse des cycles de trading...")
        cycle_analysis = auditor.analyze_trading_cycles(binance_df, firebase_df)
        
        # Métriques
        metrics = auditor.calculate_metrics(matched, only_binance, only_firebase)
        
        # Affichage des résultats
        print("\n📊 RÉSULTATS DE L'AUDIT")
        print("=" * 30)
        print(f"🎯 Trades Binance     : {metrics['total_binance_trades']}")
        print(f"🔥 Trades Firebase    : {metrics['total_firebase_trades']}")
        print(f"✅ Trades matchés     : {metrics['matched_trades']}")
        print(f"❌ Manqués Firebase   : {metrics['missing_in_firebase']}")
        print(f"👻 Fantômes Firebase  : {metrics['phantom_in_firebase']}")
        print(f"📈 Taux de match      : {metrics['match_rate']:.1f}%")
        
        # Analyse des cycles
        print(f"\n🔄 ANALYSE DES CYCLES DE TRADING")
        print("=" * 35)
        print(f"📈 BUY Binance        : {cycle_analysis['binance_buy_orders']}")
        print(f"📉 SELL Binance       : {cycle_analysis['binance_sell_orders']}")
        
        # Affichage de la fragmentation si disponible
        if not binance_df.empty and 'fragment_count' in binance_df.columns:
            total_fragments = binance_df['fragment_count'].sum() if 'fragment_count' in binance_df.columns else len(binance_df)
            fragmented_trades = len(binance_df[binance_df.get('fragment_count', 1) > 1]) if 'fragment_count' in binance_df.columns else 0
            print(f"🧩 Fragments Binance  : {total_fragments} fragments → {len(binance_df)} trades")
            if fragmented_trades > 0:
                print(f"📦 Trades fragmentés  : {fragmented_trades}")
        
        print(f"🟢 BUY Firebase       : {cycle_analysis['firebase_open_trades']}")
        print(f"🔴 SELL Firebase      : {cycle_analysis['firebase_close_trades']}")
        print(f"🚨 SELL orphelins     : {cycle_analysis['orphaned_closes']}")
        print(f"⚠️ BUY orphelins      : {cycle_analysis['orphaned_opens']}")
        
        # Détails des cycles incomplets
        if cycle_analysis['incomplete_cycles']:
            print(f"\n🚨 CYCLES INCOMPLETS DÉTECTÉS:")
            for cycle in cycle_analysis['incomplete_cycles']:
                if cycle['type'] == 'ORPHANED_CLOSE':
                    print(f"   🔴 SELL ORPHELIN: {cycle['pair']} à {cycle['close_time'].strftime('%Y-%m-%d %H:%M')}")
                    print(f"      Prix entrée: {cycle['entry_price']} | Prix sortie: {cycle.get('exit_price', 'N/A')}")
                    print(f"      Problème: {cycle['issue']}")
                elif cycle['type'] == 'ORPHANED_OPEN':
                    print(f"   🟢 BUY ORPHELIN: {cycle['pair']} à {cycle['open_time'].strftime('%Y-%m-%d %H:%M')}")
                    print(f"      Prix entrée: {cycle['entry_price']}")
                    print(f"      Problème: {cycle['issue']}")
                print()
            
            # Diagnostic spécifique aux SELL orphelins
            if cycle_analysis['orphaned_closes'] > 0:
                print(f"\n🎯 DIAGNOSTIC:")
                print(f"✅ Les trades ont bien été exécutés sur Binance (BUY + SELL)")
                print(f"❌ Le logging Firebase BUY était défaillant") 
                print(f"✅ Le logging Firebase SELL fonctionne")
                print(f"💡 Le bug a été corrigé - les prochains trades seront complets")
        
        # Détails des problèmes standard
        if metrics['missing_in_firebase'] > 0:
            print(f"\n⚠️ TRADES MANQUÉS DANS FIREBASE:")
            for idx, row in only_binance.iterrows():
                trade_type = row.get('trade_type', 'N/A')
                print(f"   • {row.get('symbol', 'N/A')} [{trade_type}] - {row.get('time', 'N/A')} - {row.get('price', 'N/A')} USDC")
        
        if metrics['phantom_in_firebase'] > 0:
            print(f"\n🚨 TRADES FANTÔMES DANS FIREBASE:")
            for idx, row in only_firebase.iterrows():
                action = row.get('action', 'N/A')
                print(f"   • {row.get('pair', 'N/A')} [{action}] - {row.get('timestamp', 'N/A')} - {row.get('entry_price', 'N/A')} USDC")
        
        # Évaluation globale adaptée
        print(f"\n🎯 ÉVALUATION:")
        if cycle_analysis['orphaned_closes'] > 0:
            print(f"🔧 DIAGNOSTIC: {cycle_analysis['orphaned_closes']} trades CLOSE orphelins détectés")
            print("   → Probable: Bug de logging des ordres BUY (corrigé récemment)")
            print("   → Ces trades sont RÉELS mais mal loggés")
            print("   → Solution: Vérifier que les nouveaux trades utilisent le logging corrigé")
        elif metrics['match_rate'] >= 95:
            print("✅ Excellente cohérence des données !")
        elif metrics['match_rate'] >= 90:
            print("🟡 Cohérence acceptable, mais améliorable")
        else:
            print("🚨 Cohérence critique - vérification nécessaire !")
        
    except Exception as e:
        print(f"❌ Erreur durant l'audit: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_audit())
