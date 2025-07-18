#!/usr/bin/env python3
"""
Script de vérification pré-déploiement
Vérifie que tous les éléments sont en place avant le déploiement
"""

import json
import os
import sys
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Vérifie qu'un fichier existe"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} MANQUANT: {file_path}")
        return False

def check_env_file() -> bool:
    """Vérifie le fichier .env"""
    if not os.path.exists('.env'):
        print("❌ Fichier .env manquant")
        return False
    
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    with open('.env', 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in content or f"{var}=" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables manquantes dans .env: {', '.join(missing_vars)}")
        return False
    
    print("✅ Fichier .env: Toutes les variables requises présentes")
    return True

def check_credentials_json() -> bool:
    """Vérifie le fichier credentials.json"""
    if not os.path.exists('credentials.json'):
        print("⚠️  credentials.json manquant (Google Sheets optionnel)")
        return True
    
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]
        
        if missing_fields:
            print(f"❌ Champs manquants dans credentials.json: {', '.join(missing_fields)}")
            return False
        
        print("✅ credentials.json: Valide")
        return True
    
    except json.JSONDecodeError:
        print("❌ credentials.json: Format JSON invalide")
        return False

def main():
    """Fonction principale de vérification"""
    print("🔍 VÉRIFICATION PRÉ-DÉPLOIEMENT")
    print("=" * 50)
    
    all_good = True
    
    # Vérification des fichiers principaux
    files_to_check = [
        ('main.py', 'Script principal'),
        ('config.py', 'Configuration'),
        ('run.py', 'Launcher'),
        ('requirements.txt', 'Dépendances Python'),
        ('investor_report.py', 'Script de rapport'),
        ('utils/database.py', 'Module base de données'),
        ('utils/logger.py', 'Module logging'),
        ('utils/risk_manager.py', 'Gestionnaire de risques'),
        ('utils/technical_indicators.py', 'Indicateurs techniques'),
        ('utils/telegram_notifier.py', 'Notifications Telegram'),
        ('utils/helpers.py', 'Utilitaires'),
        ('scripts/full_deploy.sh', 'Script de déploiement'),
        ('scripts/deploy_windows.ps1', 'Script PowerShell'),
        ('scripts/tothemoon-tradebot.service', 'Service systemd'),
        ('scripts/README.md', 'Documentation déploiement')
    ]
    
    print("\n📁 FICHIERS DU PROJET")
    print("-" * 30)
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False
    
    # Vérification de la configuration
    print("\n⚙️  CONFIGURATION")
    print("-" * 30)
    if not check_env_file():
        all_good = False
    
    if not check_credentials_json():
        all_good = False
    
    # Vérification des dossiers
    print("\n📂 STRUCTURE DES DOSSIERS")
    print("-" * 30)
    directories = ['utils', 'scripts', 'logs', 'data']
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ Dossier {directory}/ existe")
        else:
            print(f"⚠️  Dossier {directory}/ sera créé automatiquement")
    
    # Résumé final
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 VÉRIFICATION RÉUSSIE !")
        print("Le projet est prêt pour le déploiement.")
        print("")
        print("📋 PROCHAINES ÉTAPES :")
        print("1. Exécutez: deploy.bat (Windows) ou ./scripts/full_deploy.sh (Linux/Mac)")
        print("2. Configurez .env sur le VPS")
        print("3. Démarrez le service: systemctl start tothemoon-tradebot")
        print("")
        sys.exit(0)
    else:
        print("❌ VÉRIFICATION ÉCHOUÉE !")
        print("Corrigez les erreurs ci-dessus avant le déploiement.")
        print("")
        sys.exit(1)

if __name__ == "__main__":
    main()
