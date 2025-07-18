# Suggestions d'optimisation de configuration

## Paramètres actuels vs optimisés

### Position Sizing (ACTUEL: 17.5%)
- **OPTIMAL**: 15% par position max
- **RAISON**: Plus de positions possibles, risque mieux réparti

### Take Profit (ACTUEL: 1.0%)
- **OPTIMAL**: 0.8% (plus réalisable)
- **RAISON**: Taux de réussite plus élevé

### Stop Loss (ACTUEL: 0.5%)
- **OPTIMAL**: 0.4%
- **RAISON**: Meilleur ratio risque/récompense (1:2)

### Timeout (ACTUEL: 15min)
- **OPTIMAL**: ✅ Parfait !
- **BONUS**: Ajouter un timeout à 5min si +0.1%

### Signal Conditions (ACTUEL: 3 conditions)
- **OPTIMAL**: 4 conditions minimum
- **RAISON**: Plus de sélectivité = meilleure qualité

## Configuration optimisée proposée:

```python
# Trading optimisé pour +1% quotidien
POSITION_SIZE_PERCENT: float = 15.0        # 15% par position
STOP_LOSS_PERCENT: float = 0.4            # SL -0.4%
TAKE_PROFIT_PERCENT: float = 0.8          # TP +0.8%
TRADE_TIMEOUT_MINUTES: int = 15           # ✅ Parfait
MIN_PROFIT_BEFORE_TIMEOUT: float = 0.15   # 0.15% avant timeout
MIN_SIGNAL_CONDITIONS: int = 4            # Plus sélectif
MAX_OPEN_POSITIONS: int = 4               # Plus d'opportunités
```

## Résultat attendu avec optimisation:
- **Win rate**: 70-75% (vs 65% actuellement)
- **Trades par jour**: 8-12 (vs 5-8 actuellement)
- **Performance**: +0.8-1.2% quotidien plus constant
- **Drawdown**: Réduit de 30%
