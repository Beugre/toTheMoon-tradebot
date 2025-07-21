"""
Configuration Firebase pour le Trading Bot
Système de logging et analytics temps réel
"""

import os
from dataclasses import dataclass
from typing import Optional

# Chargement des variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv n'est pas installé


@dataclass
class FirebaseConfig:
    """Configuration Firebase"""
    
    # Firebase Realtime Database
    DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")
    PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    
    # Firebase Credentials
    CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")
    
    # Configuration du logging
    ENABLE_FIREBASE_LOGGING: bool = os.getenv("ENABLE_FIREBASE_LOGGING", "True").lower() == "true"
    ENABLE_TRADES_LOGGING: bool = os.getenv("ENABLE_TRADES_LOGGING", "True").lower() == "true"
    ENABLE_PERFORMANCE_LOGGING: bool = os.getenv("ENABLE_PERFORMANCE_LOGGING", "True").lower() == "true"
    
    # Structure des données
    LOGS_COLLECTION: str = "bot_logs"
    TRADES_COLLECTION: str = "trades"
    PERFORMANCE_COLLECTION: str = "performance"
    METRICS_COLLECTION: str = "metrics"
    ALERTS_COLLECTION: str = "alerts"
    
    # Paramètres de rétention
    LOGS_RETENTION_DAYS: int = 30  # Garder les logs 30 jours
    TRADES_RETENTION_DAYS: int = 365  # Garder les trades 1 an
    PERFORMANCE_RETENTION_DAYS: int = 90  # Garder les perfs 3 mois
    
    # Paramètres de batch
    BATCH_SIZE: int = 100  # Nombre d'entrées par batch
    BATCH_INTERVAL_SECONDS: int = 10  # Fréquence des uploads
    
    def validate(self) -> bool:
        """Valide la configuration Firebase"""
        if not self.DATABASE_URL:
            raise ValueError("FIREBASE_DATABASE_URL manquant")
        if not self.PROJECT_ID:
            raise ValueError("FIREBASE_PROJECT_ID manquant")
        if not os.path.exists(self.CREDENTIALS_PATH):
            raise ValueError(f"Fichier credentials Firebase manquant: {self.CREDENTIALS_PATH}")
        return True

# Configuration globale
FIREBASE_CONFIG = FirebaseConfig()