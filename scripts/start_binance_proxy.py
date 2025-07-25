#!/usr/bin/env python3
"""
Script de démarrage pour le service Binance Proxy sur VPS
Gestion des erreurs, restart automatique et monitoring
"""

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au PATH pour les imports
sys.path.append(str(Path(__file__).parent.parent))

import asyncio

from utils.binance_proxy_service import BinanceProxyService


class ProxyServiceManager:
    """Gestionnaire du service proxy avec restart automatique"""
    
    def __init__(self, max_retries: int = 5, retry_delay: int = 30):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.service = None
        self.should_restart = True
        self.setup_logging()
        
    def setup_logging(self):
        """Configuration du logging pour le manager"""
        log_dir = Path('/opt/toTheMoon_tradebot/logs')
        log_dir.mkdir(exist_ok=True, parents=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'proxy_manager.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ProxyManager')
        
    def signal_handler(self, signum, frame):
        """Gestionnaire des signaux système"""
        self.logger.info(f"🛑 Signal {signum} reçu - Arrêt en cours")
        self.should_restart = False
        if self.service:
            self.service.stop_service()
            
    def setup_signal_handlers(self):
        """Configuration des gestionnaires de signaux"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    async def run_service_with_retry(self):
        """Exécute le service avec retry automatique"""
        retry_count = 0
        
        while self.should_restart and retry_count < self.max_retries:
            try:
                self.logger.info(f"🚀 Démarrage du service (tentative {retry_count + 1}/{self.max_retries})")
                
                # Créer nouvelle instance du service
                self.service = BinanceProxyService()
                
                # Démarrer le service
                await self.service.start_service()
                
                # Si on arrive ici, le service s'est arrêté proprement
                self.logger.info("✅ Service arrêté proprement")
                break
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"❌ Erreur service (tentative {retry_count}): {e}")
                
                if retry_count < self.max_retries and self.should_restart:
                    self.logger.info(f"⏳ Retry dans {self.retry_delay} secondes...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("💀 Nombre maximum de tentatives atteint")
                    break
        
        self.logger.info("🔚 Gestionnaire de service arrêté")
        
    async def start(self):
        """Démarrage du gestionnaire"""
        self.setup_signal_handlers()
        self.logger.info("🎯 Gestionnaire de service Binance Proxy démarré")
        
        await self.run_service_with_retry()


def check_environment():
    """Vérification de l'environnement VPS"""
    required_files = [
        '/opt/toTheMoon_tradebot/.env',
        '/opt/toTheMoon_tradebot/firebase_credentials.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Fichiers manquants:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    # Vérifier les permissions du répertoire de logs
    log_dir = Path('/opt/toTheMoon_tradebot/logs')
    try:
        log_dir.mkdir(exist_ok=True, parents=True)
        test_file = log_dir / 'test_permissions.tmp'
        test_file.write_text('test')
        test_file.unlink()
    except Exception as e:
        print(f"❌ Problème de permissions logs: {e}")
        return False
    
    print("✅ Environnement VPS validé")
    return True


def create_systemd_service():
    """Génère le fichier de service systemd"""
    service_content = """[Unit]
Description=Binance Proxy Service for Trading Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/toTheMoon_tradebot
ExecStart=/usr/bin/python3 /opt/toTheMoon_tradebot/scripts/start_binance_proxy.py --daemon
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/toTheMoon_tradebot

[Install]
WantedBy=multi-user.target
"""
    
    service_path = '/etc/systemd/system/binance-proxy.service'
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Service systemd créé: {service_path}")
        print("\n📋 Commandes pour activer le service:")
        print("   sudo systemctl daemon-reload")
        print("   sudo systemctl enable binance-proxy")
        print("   sudo systemctl start binance-proxy")
        print("   sudo systemctl status binance-proxy")
        
    except PermissionError:
        print("❌ Permissions insuffisantes pour créer le service systemd")
        print("   Exécutez avec sudo ou créez manuellement le fichier")


async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Gestionnaire du service Binance Proxy')
    parser.add_argument('--daemon', action='store_true', help='Mode démon (pour systemd)')
    parser.add_argument('--check-env', action='store_true', help='Vérifier l\'environnement')
    parser.add_argument('--create-service', action='store_true', help='Créer le service systemd')
    parser.add_argument('--max-retries', type=int, default=5, help='Nombre max de tentatives')
    parser.add_argument('--retry-delay', type=int, default=30, help='Délai entre tentatives (sec)')
    
    args = parser.parse_args()
    
    # Vérification de l'environnement
    if args.check_env:
        if check_environment():
            print("✅ Environnement prêt pour le service")
            return 0
        else:
            print("❌ Environnement non prêt")
            return 1
    
    # Création du service systemd
    if args.create_service:
        create_systemd_service()
        return 0
    
    # Vérification automatique avant démarrage
    if not check_environment():
        print("❌ Environnement non prêt - Vérifiez la configuration")
        return 1
    
    # Démarrage du service
    try:
        manager = ProxyServiceManager(
            max_retries=args.max_retries,
            retry_delay=args.retry_delay
        )
        
        await manager.start()
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
        return 0
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
    exit(exit_code)
