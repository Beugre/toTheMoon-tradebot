# 🚀 Guide de Déploiement Streamlit Cloud

## 📋 Prérequis

1. **Compte GitHub** avec votre repo ToTheMoon
2. **Credentials Firebase** (fichier JSON depuis Firebase Console)
3. **Compte Streamlit Cloud** gratuit

## 🔧 Étape 1: Préparer les Credentials Firebase

### Récupérer les credentials Firebase :
1. Allez sur [Firebase Console](https://console.firebase.google.com)
2. Sélectionnez votre projet
3. **Paramètres** > **Comptes de service**
4. **Générer une nouvelle clé privée**
5. Téléchargez le fichier JSON

### Configurer localement :
```bash
# Copiez le fichier dans votre projet
cp /path/to/downloaded-file.json firebase_credentials.json

# OU modifiez .streamlit/secrets.toml avec vos vraies données
```

## 🌐 Étape 2: Déploiement Streamlit Cloud

### 1. Préparer le repo GitHub :
```bash
# Vérifiez que les secrets ne sont pas committés
git status
git add .
git commit -m "Dashboard Firebase ready for cloud deployment"
git push origin main
```

### 2. Déployer sur Streamlit Cloud :
1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Connectez-vous avec GitHub
3. **New app** > Sélectionnez votre repo `toTheMoon-tradebot`
4. **Main file path** : `dashboard.py`
5. **Branch** : `main`

### 3. Configurer les Secrets :
Dans Streamlit Cloud, section **Secrets** :

```toml
[firebase]
type = "service_account"
project_id = "votre-project-id"
private_key_id = "votre-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
VOTRE_PRIVATE_KEY_ICI
-----END PRIVATE KEY-----"""
client_email = "firebase-adminsdk-xxxxx@votre-project.iam.gserviceaccount.com"
client_id = "votre-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs/firebase-adminsdk-xxxxx%40votre-project.iam.gserviceaccount.com"
```

## 🚀 Résultat Final

Votre dashboard sera accessible 24/7 depuis n'importe où avec :
- ✅ **Monitoring temps réel** de votre bot
- ✅ **Historique complet** des trades  
- ✅ **Graphiques interactifs** de performance
- ✅ **Logs en direct** pour debugging
- ✅ **Interface mobile** responsive
