#!/usr/bin/env python3
"""
Script de validation post-déploiement VPS
Vérifie que le service proxy fonctionne correctement
"""

import subprocess
import sys
import time
from datetime import datetime, timedelta


def check_systemd_service():
    """Vérifier le statut du service systemd"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'binance-proxy'], 
                               capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == 'active':
            print("✅ Service binance-proxy actif")
            return True
        else:
            print(f"❌ Service binance-proxy inactif: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ Erreur vérification service: {e}")
        return False

def check_firebase_data():
    """Vérifier la présence de données Firebase récentes"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Initialiser Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('/opt/toTheMoon_tradebot/firebase_credentials.json')
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Vérifier les données proxy
        doc = db.collection('binance_live').document('recent_trades').get()
        
        if doc.exists:
            data = doc.to_dict()
            timestamp = data.get('timestamp')
            trades_count = len(data.get('trades', []))
            pairs_count = len(data.get('pairs_detected', []))
            
            print(f"✅ Données Firebase VPS trouvées:")
            print(f"   - Dernière MAJ: {timestamp}")
            print(f"   - {trades_count} trades collectés")
            print(f"   - {pairs_count} paires USDC surveillées")
            return True
        else:
            print("❌ Aucune donnée Firebase proxy trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification Firebase: {e}")
        return False

def check_logs():
    """Vérifier les logs récents"""
    try:
        result = subprocess.run(['journalctl', '-u', 'binance-proxy', '--no-pager', '-n', '10'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Logs service (10 dernières lignes):")
            print(result.stdout)
            return True
        else:
            print("❌ Impossible de lire les logs")
            return False
    except Exception as e:
        print(f"❌ Erreur lecture logs: {e}")
        return False

def main():
    """Validation complète post-déploiement"""
    print("🔍 VALIDATION POST-DÉPLOIEMENT VPS")
    print("=" * 40)
    
    checks = []
    
    # Test 1: Service systemd
    print("\n1️⃣ Vérification service systemd")
    checks.append(check_systemd_service())
    
    # Test 2: Données Firebase
    print("\n2️⃣ Vérification données Firebase")
    checks.append(check_firebase_data())
    
    # Test 3: Logs
    print("\n3️⃣ Vérification logs")
    checks.append(check_logs())
    
    # Résumé
    print("\n" + "=" * 40)
    print("📋 RÉSUMÉ VALIDATION")
    print("=" * 40)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ Déploiement VPS réussi ({passed}/{total})")
        print("🚀 Le proxy Binance est opérationnel!")
        print("\n🔗 Prochaine étape:")
        print("   Lancer monitor_realtime.py en local pour voir les données VPS")
        return 0
    else:
        print(f"❌ Problèmes détectés ({passed}/{total})")
        print("🔧 Consultez les logs pour diagnostiquer")
        return 1

if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
