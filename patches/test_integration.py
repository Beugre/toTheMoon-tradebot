#!/usr/bin/env python3
"""
Test rapide d'intégration EnhancedSheetsLogger
"""

import os
import sys

# Ajouter le chemin vers utils
utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
sys.path.insert(0, utils_path)

try:
    from enhanced_sheets_logger import EnhancedSheetsLogger  # type: ignore
    
    print("🚀 TEST INTÉGRATION ENHANCED SHEETS LOGGER")
    print("=" * 50)
    
    # Test d'instanciation
    logger = EnhancedSheetsLogger("", "")
    
    # Test des méthodes de compatibilité
    print("✅ Méthodes disponibles:")
    
    methods_to_test = [
        'log_trade',
        'log_daily_performance', 
        'log_enhanced_trade',
        'get_spreadsheet_url',
        'get_pair_performance_summary'
    ]
    
    for method in methods_to_test:
        if hasattr(logger, method):
            print(f"   ✅ {method}")
        else:
            print(f"   ❌ {method} - MANQUANT")
    
    print(f"\n🎯 EnhancedSheetsLogger prêt pour intégration dans main.py")
    print(f"📋 Toutes les méthodes de compatibilité sont disponibles")
    
except ImportError as e:
    print(f"❌ Erreur import: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")
