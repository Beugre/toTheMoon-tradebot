# 🚀 ToTheMoon Bot Dashboard

Dashboard Streamlit en temps réel pour monitorer votre bot de trading connecté à Firebase.

## 🎯 Fonctionnalités

### 📊 Vue d'ensemble
- **Statut du bot en temps réel**
- **Métriques clés** : Capital total, trades du jour, dernière activité
- **Graphiques de performance** en temps réel
- **Répartition du portefeuille** USDC vs Crypto
- **Derniers logs** avec codes couleur par niveau

### 💹 Trades
- **Historique complet** des trades
- **Filtres avancés** : par paire, statut, date
- **Statistiques** : total trades, rentabilité, P&L, taux de réussite
- **Export des données** en CSV

### 📈 Performance
- **Graphiques d'évolution** du capital
- **Métriques de performance** : rendement, drawdown
- **P&L journalier** en barres
- **Analyse des tendances**

### 🔔 Logs Temps Réel
- **Stream live** des logs Firebase
- **Filtrage par niveau** (INFO, WARNING, ERROR)
- **Recherche textuelle** dans les logs
- **Codes couleur** pour faciliter la lecture

## 🚀 Installation Rapide

### 1. Installer les dépendances
```bash
pip install -r requirements_dashboard.txt
```

### 2. Configurer Firebase
```bash
# Copiez votre fichier de credentials Firebase
cp /path/to/firebase_credentials.json ./firebase_credentials.json
```

### 3. Lancer le dashboard

**Sur Windows :**
```powershell
.\run_dashboard.ps1
```

**Sur Linux/Mac :**
```bash
./run_dashboard.sh
```

**Manuellement :**
```bash
streamlit run dashboard.py --server.port 8501
```

## 🧪 Mode Demo

Pour tester l'interface sans Firebase :

```bash
# Générer des données de test
python generate_sample_data.py

# Lancer la version demo
streamlit run dashboard_demo.py
```

## 📊 Structure des Données Firebase

Le dashboard lit les collections Firebase suivantes :

### `bot_logs`
```json
{
  "timestamp": "2025-07-21T10:30:00Z",
  "level": "INFO",
  "message": "🟢 [RUNNING] Bot lancé avec succès",
  "component": "TradingBot"
}
```

### `trades`
```json
{
  "timestamp": "2025-07-21T10:30:00Z",
  "pair": "EURUSDT",
  "side": "LONG",
  "entry_price": 1.0850,
  "exit_price": 1.0875,
  "quantity": 500.0,
  "pnl": 12.50,
  "status": "CLOSED"
}
```

### `metrics`
```json
{
  "timestamp": "2025-07-21T10:30:00Z",
  "capital_total": 22859.56,
  "usdc_balance": 19247.10,
  "crypto_value": 3612.46,
  "daily_pnl": 125.40,
  "trades_count": 12,
  "win_rate": 66.7
}
```

## ⚙️ Configuration

### Paramètres du dashboard
- **Port** : Modifiable dans `run_dashboard.ps1`
- **Auto-refresh** : Configurable dans l'interface (30s par défaut)
- **Filtres** : Persistants pendant la session

### Variables d'environnement
```bash
# Optionnel : personnaliser la configuration Firebase
export FIREBASE_PROJECT_ID="votre-project-id"
export DASHBOARD_PORT="8501"
```

## 🔧 Personnalisation

### Ajouter une nouvelle métrique
1. Modifiez `show_overview()` dans `dashboard.py`
2. Ajoutez la logique de récupération des données
3. Créez le widget Streamlit correspondant

### Nouveau type de graphique
1. Utilisez `plotly.express` ou `plotly.graph_objects`
2. Ajoutez dans la fonction appropriée (`show_performance`, etc.)
3. Configurez les options d'affichage

### Nouvelle page
1. Ajoutez l'option dans la selectbox de navigation
2. Créez la fonction `show_nouvelle_page()`
3. Ajoutez la condition dans `main()`

## 🌐 Déploiement

### Local
```bash
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
```

### Streamlit Cloud
1. Push le code sur GitHub
2. Connectez votre repo sur [share.streamlit.io](https://share.streamlit.io)
3. Ajoutez `firebase_credentials.json` dans les secrets

### Docker
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements_dashboard.txt .
RUN pip install -r requirements_dashboard.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🚨 Résolution de Problèmes

### Firebase non accessible
- Vérifiez `firebase_credentials.json`
- Testez la connexion avec `dashboard.py` page Configuration

### Données manquantes
- Vérifiez que le bot envoie bien les données vers Firebase
- Utilisez le mode demo pour tester l'interface

### Performance lente
- Réduisez le nombre de données chargées (limite dans `get_real_time_data`)
- Désactivez l'auto-refresh
- Utilisez des filtres pour limiter les données

### Erreur de port
```bash
# Changer le port si 8501 est occupé
streamlit run dashboard.py --server.port 8502
```

## 📱 Accès Mobile

Le dashboard est responsive et accessible depuis :
- **Ordinateur** : `http://localhost:8501`
- **Mobile/Tablette** : `http://[votre-ip]:8501`
- **Réseau local** : Partageable avec d'autres appareils

## 🔐 Sécurité

- **Credentials Firebase** : Jamais committés dans Git
- **Accès réseau** : Configurable via `--server.address`
- **HTTPS** : Recommandé pour la production
- **Authentification** : À implémenter selon vos besoins

## 📈 Métriques Avancées

Le dashboard peut afficher :
- **Sharpe Ratio** : Rendement ajusté du risque
- **Maximum Drawdown** : Perte maximale depuis un pic
- **Win Rate** : Pourcentage de trades gagnants
- **Profit Factor** : Ratio profits/pertes
- **Average Trade** : Gain moyen par trade

## 🎨 Thèmes et Style

Personnalisez l'apparence :
- **Couleurs** : Modifiez le CSS dans le code
- **Layout** : Ajustez les colonnes et sections
- **Graphiques** : Thèmes Plotly configurables

---

**🚀 Bon trading avec votre dashboard ToTheMoon !**
