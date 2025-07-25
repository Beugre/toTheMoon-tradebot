# Configuration sécurisée pour le déploiement Streamlit Cloud

import json
import os
from pathlib import Path

import streamlit as st


def get_firebase_credentials():
    """
    Récupère les credentials Firebase de manière sécurisée
    - En local : utilise firebase_credentials.json
    - En production : utilise les secrets Streamlit
    """
    
    # En production Streamlit Cloud
    if "firebase_credentials" in st.secrets:
        return dict(st.secrets["firebase_credentials"])
    
    # En local - fichier JSON
    credentials_path = Path("firebase_credentials.json")
    if credentials_path.exists():
        with open(credentials_path, 'r') as f:
            return json.load(f)
    
    # Variables d'environnement (fallback)
    firebase_creds_env = os.getenv('FIREBASE_CREDENTIALS')
    if firebase_creds_env:
        return json.loads(firebase_creds_env)
    
    raise ValueError("❌ Credentials Firebase non trouvées")

def get_binance_credentials():
    """
    Récupère les credentials Binance de manière sécurisée
    """
    
    # En production Streamlit Cloud
    if hasattr(st, 'secrets') and "binance" in st.secrets:
        return {
            'api_key': st.secrets["binance"]["api_key"],
            'api_secret': st.secrets["binance"]["api_secret"]
        }
    
    # En local - variables d'environnement
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not api_secret:
        raise ValueError("❌ Credentials Binance non trouvées")
    
    return {
        'api_key': api_key,
        'api_secret': api_secret
    }
        'api_secret': api_secret
    }
