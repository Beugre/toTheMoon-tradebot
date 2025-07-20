"""
Générateur de données de test pour le dashboard
Utile pour tester l'interface sans avoir de vraies données Firebase
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List


def generate_sample_logs(count: int = 50) -> List[Dict]:
    """Génère des logs de test"""
    levels = ['INFO', 'WARNING', 'ERROR']
    messages = [
        "🟢 [RUNNING] Bot lancé avec succès",
        "💰 Capital initial total: 22859.56 USDC",
        "📊 Signal détecté sur EURUSDT",
        "💹 Trade ouvert: EURUSDT LONG à 1.0850",
        "✅ Trade fermé avec profit: +15.32 USDC",
        "⚠️ Volatilité élevée détectée",
        "❌ Erreur de connexion API Binance",
        "🔄 Reconnexion automatique réussie",
        "📈 Nouveau signal EMA crossover",
        "🛑 Stop Loss activé",
        "🎯 Take Profit atteint",
        "⏰ Hors horaires de trading",
        "🔥 Firebase Logger activé",
        "📱 Notification Telegram envoyée"
    ]
    
    logs = []
    base_time = datetime.now()
    
    for i in range(count):
        log = {
            'timestamp': (base_time - timedelta(minutes=i*5)).isoformat(),
            'level': random.choice(levels),
            'message': random.choice(messages),
            'component': random.choice(['TradingBot', 'RiskManager', 'TechnicalAnalyzer'])
        }
        logs.append(log)
    
    return logs

def generate_sample_trades(count: int = 20) -> List[Dict]:
    """Génère des trades de test"""
    pairs = ['EURUSDT', 'GBPUSDT', 'EURCHF', 'EURJPY', 'EURGBP']
    statuses = ['OPEN', 'CLOSED', 'CANCELLED']
    
    trades = []
    base_time = datetime.now()
    
    for i in range(count):
        entry_price = round(random.uniform(1.0, 1.2), 5)
        exit_price = round(entry_price + random.uniform(-0.01, 0.02), 5)
        quantity = round(random.uniform(100, 1000), 2)
        pnl = round((exit_price - entry_price) * quantity, 2)
        
        trade = {
            'timestamp': (base_time - timedelta(hours=i*2)).isoformat(),
            'pair': random.choice(pairs),
            'side': random.choice(['LONG', 'SHORT']),
            'entry_price': entry_price,
            'exit_price': exit_price if random.choice(statuses) == 'CLOSED' else None,
            'quantity': quantity,
            'pnl': pnl if random.choice(statuses) == 'CLOSED' else 0,
            'status': random.choice(statuses),
            'stop_loss': round(entry_price * 0.99, 5),
            'take_profit': round(entry_price * 1.02, 5)
        }
        trades.append(trade)
    
    return trades

def generate_sample_metrics(count: int = 100) -> List[Dict]:
    """Génère des métriques de test"""
    metrics = []
    base_time = datetime.now()
    base_capital = 22000
    
    for i in range(count):
        # Simulation d'une évolution réaliste du capital
        change = random.uniform(-50, 100)  # Variation de -50 à +100 USDC
        base_capital += change
        
        usdc_balance = base_capital * random.uniform(0.7, 0.9)
        crypto_value = base_capital - usdc_balance
        
        metric = {
            'timestamp': (base_time - timedelta(hours=i)).isoformat(),
            'capital_total': round(base_capital, 2),
            'usdc_balance': round(usdc_balance, 2),
            'crypto_value': round(crypto_value, 2),
            'daily_pnl': round(random.uniform(-100, 200), 2),
            'trades_count': random.randint(5, 25),
            'win_rate': round(random.uniform(45, 75), 1)
        }
        metrics.append(metric)
    
    return metrics

def save_sample_data():
    """Sauvegarde les données de test dans des fichiers JSON"""
    data = {
        'logs': generate_sample_logs(100),
        'trades': generate_sample_trades(50),
        'metrics': generate_sample_metrics(200)
    }
    
    with open('sample_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✅ Données de test générées dans sample_data.json")

if __name__ == "__main__":
    save_sample_data()
