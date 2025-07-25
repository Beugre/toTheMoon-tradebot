# 🔍 Trading Monitor - Guide d'utilisation

## Installation des dépendances

```bash
pip install -r requirements.txt
```

## Lancement du monitoring Streamlit

```bash
streamlit run monitor_streamlit.py
```

Puis ouvrir dans le navigateur : http://localhost:8501

## Fonctionnalités

### 📊 Dashboard en temps réel
- **Métriques instantanées** : Nombre de trades Binance vs Firebase
- **Taux de matching** : Pourcentage de concordance entre les sources
- **Détection d'anomalies** : Trades orphelins, fantômes, manqués

### 🎯 Matching intelligent
- **Agrégation automatique** des trades fragmentés Binance
- **Correspondance par prix et timestamp** avec tolérance configurable
- **Score de confiance** pour chaque match

### 🚨 Alertes automatiques
- **SELL orphelins** : Trades de vente sans achat correspondant
- **BUY orphelins** : Trades d'achat sans vente correspondant
- **Trades fantômes** : Présents dans Firebase mais pas sur Binance

### ⚙️ Configuration
- **Période d'analyse** : 1h, 4h, 24h ou personnalisé
- **Paires surveillées** : Sélection multiple des cryptomonnaies
- **Seuils d'alerte** : Tolérance prix et temps
- **Auto-refresh** : Mise à jour automatique toutes les 30s

## Structure des données

### Binance (Source de vérité)
- Trades avec fragmentation possible
- Agrégation automatique par `orderId`
- Types : BUY/SELL

### Firebase (Logging bot)
- Trades avec actions BUY/SELL
- Champs : pair, timestamp, entry_price, exit_price, action
- Peut contenir des cycles incomplets

## Diagnostic

### ✅ Système sain
- Taux de match > 90%
- Pas de SELL orphelins
- Correspondance prix/temps cohérente

### ⚠️ Attention requise
- Taux de match 50-90%
- Quelques BUY orphelins (positions ouvertes)

### 🚨 Problème critique
- Taux de match < 50%
- Nombreux SELL orphelins
- Décalages de prix importants

## Commandes utiles

### Test rapide CLI
```bash
python test_audit.py
```

### Vérification API Binance
```bash
python test_binance_api.py
```

### Inspection Firebase
```bash
python debug_firebase.py
```
