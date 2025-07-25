"""
Test simple des clés API Binance
"""
import os

from binance.client import Client
from dotenv import load_dotenv


def test_binance_api():
    """Test rapide des clés API Binance"""
    
    # Charger le fichier .env
    load_dotenv()
    
    print("🔑 Test des clés API Binance")
    print("=" * 30)
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')
    
    print(f"API Key: {'✅ Configurée' if api_key else '❌ Manquante'}")
    print(f"API Secret: {'✅ Configurée' if api_secret else '❌ Manquante'}")
    
    if not api_key or not api_secret:
        print("\n❌ Clés API manquantes!")
        print("💡 Configurez vos variables d'environnement:")
        print("   BINANCE_API_KEY=votre_clé")
        print("   BINANCE_API_SECRET=votre_secret")
        return
    
    try:
        client = Client(api_key=api_key, api_secret=api_secret)
        
        # Test de connexion
        account_info = client.get_account()
        print(f"\n✅ Connexion réussie!")
        print(f"📊 Account Type: {account_info.get('accountType', 'N/A')}")
        
        # Test get_my_trades sur BNBUSDC
        print(f"\n🔍 Test récupération trades BNBUSDC...")
        trades = client.get_my_trades(symbol='BNBUSDC', limit=5)
        print(f"📈 {len(trades)} trades trouvés")
        
        if trades:
            latest = trades[-1]
            from datetime import datetime
            trade_time = datetime.fromtimestamp(latest['time'] / 1000)
            print(f"🕐 Dernier trade: {trade_time}")
            print(f"💰 Prix: {latest['price']} USDC")
            print(f"📊 Quantité: {latest['qty']}")
            print(f"🔄 Type: {'BUY' if latest['isBuyer'] else 'SELL'}")
    
    except Exception as e:
        print(f"\n❌ Erreur API: {e}")
        if "Invalid API-key" in str(e):
            print("💡 Clé API invalide - vérifiez vos credentials")
        elif "Signature for this request" in str(e):
            print("💡 Secret API invalide - vérifiez votre secret")

if __name__ == "__main__":
    test_binance_api()
if __name__ == "__main__":
    test_binance_api()
