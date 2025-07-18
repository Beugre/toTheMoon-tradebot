<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Bot de Trading Scalping - Instructions Copilot

Ce projet est un bot de trading automatisé spécialisé dans le scalping sur les paires EUR avec les fonctionnalités suivantes :

## Architecture du projet
- **Gestion dynamique du capital** : Récupération en temps réel via API Binance
- **Multi-paires EUR** : Sélection automatique des meilleures paires
- **Signaux techniques** : EMA, MACD, RSI, Bollinger Bands
- **Gestion des risques** : Stop Loss, Take Profit, Trailing Stop
- **Notifications Telegram** : Alertes en temps réel
- **Logging Google Sheets** : Suivi des performances

## Bonnes pratiques
- Utiliser la gestion d'erreurs robuste pour les API calls
- Implémenter le logging détaillé pour le debugging
- Respecter les limites de rate des APIs
- Sécuriser les clés API avec des variables d'environnement
- Utiliser le pattern async/await pour les opérations I/O
- Implémenter un système de retry pour les connexions réseau

## Sécurité
- Jamais de clés API en dur dans le code
- Validation stricte des paramètres de trading
- Gestion des timeouts et des erreurs réseau
- Protection contre les positions multiples sur la même paire
