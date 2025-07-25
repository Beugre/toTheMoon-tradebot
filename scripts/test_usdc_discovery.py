#!/usr/bin/env python3
"""
Test de découverte des paires USDC - Validation avant déploiement
Vérifie que le système détecte bien toutes les paires USDC avec activité
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le répertoire parent au PATH pour les imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv

    from utils.binance_proxy_service import BinanceProxyService
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    print("Assurez-vous d'avoir installé: pip install python-binance firebase-admin python-dotenv")
    sys.exit(1)


def test_usdc_discovery():
    """Test de découverte des paires USDC"""
    print("🧪 TEST DÉCOUVERTE PAIRES USDC")
    print("=" * 40)
    
    try:
        # Charger les variables d'environnement depuis la racine du projet
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'
        
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Fichier .env chargé depuis: {env_path}")
        else:
            print(f"⚠️ Fichier .env non trouvé dans: {env_path}")
            # Essayer le répertoire courant en fallback
            load_dotenv()
        
        # Créer une instance temporaire (sans Firebase pour le test)
        service = BinanceProxyService.__new__(BinanceProxyService)
        service.setup_logging()
        service.setup_binance_client()
        service.monitored_pairs = []
        
        print("✅ Client Binance initialisé")
        
        # Test 1: Découverte des paires avec activité
        print("\n🔍 Test 1: Paires avec activité (48h)")
        active_pairs = service.discover_usdc_pairs_with_activity(hours_back=48)
        print(f"   Trouvé: {len(active_pairs)} paires")
        for pair in active_pairs[:10]:  # Afficher les 10 premières
            print(f"   - {pair}")
        if len(active_pairs) > 10:
            print(f"   ... et {len(active_pairs) - 10} autres")
        
        # Test 2: Toutes les paires USDC de l'exchange
        print("\n📊 Test 2: Toutes les paires USDC disponibles")
        all_pairs = service.get_all_usdc_pairs_from_exchange()
        print(f"   Trouvé: {len(all_pairs)} paires USDC sur Binance")
        
        # Test 3: Mise à jour intelligente
        print("\n🔄 Test 3: Mise à jour intelligente des paires surveillées")
        service.update_monitored_pairs()
        print(f"   Paires finales surveillées: {len(service.monitored_pairs)}")
        
        # Test 4: Récupération d'un échantillon de trades
        print("\n📈 Test 4: Échantillon de trades récents")
        try:
            # Récupérer les trades pour les paires USDC principales d'abord
            test_pairs = ['BNBUSDC', 'BTCUSDC', 'ETHUSDC', 'SAHARAUSDC']
            all_trades = []
            pairs_with_trades = []
            
            for symbol in test_pairs:
                try:
                    trades = service.binance_client.get_my_trades(
                        symbol=symbol,
                        startTime=int((datetime.now() - timedelta(hours=24)).timestamp() * 1000),
                        limit=50
                    )
                    if trades:
                        all_trades.extend(trades)
                        pairs_with_trades.append(symbol)
                        print(f"   {symbol}: {len(trades)} trades")
                except Exception as e:
                    # Ignorer les paires sans trades ou avec erreurs
                    continue
            
            if all_trades:
                usdc_trades = [t for t in all_trades if t['symbol'].endswith('USDC')]
                pairs_in_trades = set(t['symbol'] for t in usdc_trades)
                
                print(f"   Total trades USDC 24h: {len(usdc_trades)}")
                print(f"   Paires avec activité: {', '.join(sorted(pairs_with_trades))}")
                
                # Afficher quelques détails des trades récents
                if usdc_trades:
                    recent_trade = usdc_trades[0]
                    trade_time = datetime.fromtimestamp(recent_trade['time'] / 1000)
                    side = 'BUY' if recent_trade.get('isBuyer', False) else 'SELL'
                    print(f"   Dernier trade: {recent_trade['symbol']} - {side} - {trade_time.strftime('%H:%M:%S')}")
            else:
                print("   Aucun trade trouvé sur les paires testées")
                
        except Exception as e:
            print(f"   ⚠️ Impossible de récupérer les trades récents: {e}")
        
        # Résumé
        print("\n" + "=" * 40)
        print("📋 RÉSUMÉ DU TEST")
        print("=" * 40)
        print(f"✅ Paires avec activité récente: {len(active_pairs)}")
        print(f"✅ Total paires USDC disponibles: {len(all_pairs)}")
        print(f"✅ Paires qui seront surveillées: {len(service.monitored_pairs)}")
        
        if len(service.monitored_pairs) > len(active_pairs):
            print("ℹ️ Le système surveillera plus de paires que celles avec activité récente")
            print("   (normal pour capturer toute activité future)")
        
        print("\n🎯 RECOMMANDATIONS:")
        if len(service.monitored_pairs) > 100:
            print("⚠️ Beaucoup de paires surveillées - peut ralentir la collecte")
            print("   Considérez limiter aux 50 plus importantes")
        elif len(service.monitored_pairs) < 10:
            print("ℹ️ Peu de paires détectées - normal si compte peu actif")
        else:
            print("✅ Nombre de paires optimal pour surveillance complète")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False


def test_account_info():
    """Test des informations de compte"""
    print("\n💰 TEST INFORMATIONS COMPTE")
    print("=" * 40)
    
    try:
        # Charger les variables d'environnement depuis la racine du projet
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'
        
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        service = BinanceProxyService.__new__(BinanceProxyService)
        service.setup_logging()
        service.setup_binance_client()
        
        account = service.binance_client.get_account()
        
        print(f"✅ Type de compte: {account.get('accountType', 'UNKNOWN')}")
        print(f"✅ Trading autorisé: {account.get('canTrade', False)}")
        print(f"✅ Retrait autorisé: {account.get('canWithdraw', False)}")
        
        # Balances non nulles
        non_zero_balances = [
            b for b in account['balances'] 
            if float(b['free']) + float(b['locked']) > 0
        ]
        
        print(f"✅ Assets avec balance: {len(non_zero_balances)}")
        for balance in non_zero_balances[:5]:
            total = float(balance['free']) + float(balance['locked'])
            print(f"   - {balance['asset']}: {total:.8f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test compte: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("🚀 TESTS DE VALIDATION PROXY VPS BINANCE")
    print("=" * 50)
    
    # Vérification du fichier .env
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Fichier .env trouvé: {env_path}")
    else:
        print(f"❌ Fichier .env non trouvé dans: {env_path}")
        print("   Créez le fichier .env à la racine du projet avec:")
        print("   BINANCE_API_KEY=your_api_key")
        print("   BINANCE_SECRET_KEY=your_secret_key")
        return 1
    
    # Vérification des variables d'environnement
    if not os.getenv('BINANCE_API_KEY') or not os.getenv('BINANCE_SECRET_KEY'):
        print("❌ Variables d'environnement BINANCE_API_KEY et BINANCE_SECRET_KEY requises")
        print("   Vérifiez le contenu de votre fichier .env")
        return 1
    
    print(f"✅ Variables d'environnement chargées depuis: {env_path}")
    
    tests_results = []
    
    # Test découverte paires USDC
    tests_results.append(test_usdc_discovery())
    
    # Test informations compte
    tests_results.append(test_account_info())
    
    # Résultats finaux
    print("\n" + "=" * 50)
    print("🏁 RÉSULTATS FINAUX")
    print("=" * 50)
    
    passed = sum(tests_results)
    total = len(tests_results)
    
    if passed == total:
        print(f"✅ Tous les tests réussis ({passed}/{total})")
        print("🚀 Le système est prêt pour le déploiement VPS!")
        return 0
    else:
        print(f"❌ Certains tests ont échoué ({passed}/{total})")
        print("🔧 Corrigez les erreurs avant le déploiement")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
    exit(exit_code)
