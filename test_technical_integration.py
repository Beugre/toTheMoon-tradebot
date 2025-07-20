#!/usr/bin/env python3
"""
Test de validation de l'intégration TechnicalAnalyzer avec la configuration
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TradingConfig
from utils.technical_indicators import TechnicalAnalyzer


def test_configuration_consistency():
    """Test de cohérence entre config et TechnicalAnalyzer"""
    
    config = TradingConfig()
    analyzer = TechnicalAnalyzer()
    
    print("🔍 Test de cohérence configuration vs TechnicalAnalyzer")
    print(f"📊 Configuration MIN_SIGNAL_CONDITIONS: {config.MIN_SIGNAL_CONDITIONS}")
    
    # Test avec des données simulées
    import numpy as np
    import pandas as pd

    # Génération de données test
    dates = pd.date_range('2025-01-01', periods=100, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(50000, 51000, 100),
        'high': np.random.uniform(50500, 51500, 100),
        'low': np.random.uniform(49500, 50500, 100),
        'close': np.random.uniform(50000, 51000, 100),
        'volume': np.random.uniform(1000, 10000, 100)
    })
    
    # Analyse technique
    analysis = analyzer.analyze_pair(df, "TESTUSDC")
    
    print(f"📈 Analyse technique générée:")
    print(f"   - Nombre de signaux: {len(analysis.signals)}")
    print(f"   - Score total: {analysis.total_score:.1f}")
    print(f"   - Recommandation: {analysis.recommendation}")
    
    # Test de validation avec config
    is_valid = analyzer.is_valid_signal(analysis, config.MIN_SIGNAL_CONDITIONS)
    
    print(f"✅ Signal valide selon config ({config.MIN_SIGNAL_CONDITIONS} conditions): {is_valid}")
    
    if not is_valid:
        print(f"⚠️ Signal rejeté car {len(analysis.signals)} < {config.MIN_SIGNAL_CONDITIONS}")
    
    print("\n🔧 Signaux détectés:")
    for signal in analysis.signals:
        print(f"   - {signal.indicator}: {signal.description} (Force: {signal.strength.name})")
    
    return is_valid

if __name__ == "__main__":
    test_configuration_consistency()
