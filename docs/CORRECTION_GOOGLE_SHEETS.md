# Correction du Logging Google Sheets - 17 juillet 2025

## Problème identifié

Le bot affichait "Google Sheets activé" mais les trades n'étaient pas enregistrés dans la feuille Google Sheets. Analyse effectuée et corrections appliquées.

## Corrections apportées

### 1. Initialisation du SheetsLogger avec SPREADSHEET_ID

**Problème**: Le SheetsLogger était initialisé sans l'ID du spreadsheet
**Fichier**: `main.py`
**Ligne**: ~98

**Avant**:
```python
self.sheets_logger = SheetsLogger(API_CONFIG.GOOGLE_SHEETS_CREDENTIALS)
```

**Après**:
```python
self.sheets_logger = SheetsLogger(
    API_CONFIG.GOOGLE_SHEETS_CREDENTIALS, 
    API_CONFIG.GOOGLE_SHEETS_SPREADSHEET_ID
)
```

### 2. Amélioration de la gestion d'erreurs

**Problème**: Erreurs Google Sheets peu informatives
**Fichier**: `utils/sheets_logger.py`
**Section**: `log_trade()` method

**Améliorations**:
- Gestion spécifique de l'erreur "Drive storage quota exceeded"
- Gestion des erreurs de permissions
- Logs plus détaillés avec stacktrace
- Vérification de l'état du client avant les opérations

### 3. Correction de la mise à jour des cellules

**Problème**: Erreur API lors de la mise à jour individuelle des cellules
**Fichier**: `utils/sheets_logger.py`
**Section**: Mise à jour des trades fermés

**Avant**: Mise à jour cellule par cellule
```python
for cell, value in zip(updates, values):
    trades_sheet.update(cell, value)
```

**Après**: Mise à jour par batch
```python
range_name = f"G{i}:M{i}"
values = [[exit_price, "", "", pnl, pnl_percent, str(duration), exit_reason]]
trades_sheet.update(range_name, values)
```

### 4. Support des différents types de fermeture

**Amélioration**: Support pour `CLOSE`, `CLOSE_VIRTUAL`
**Gestion robuste**: Utilisation de `getattr()` pour les attributs optionnels

## Tests effectués

### Test manuel avec script de test
- ✅ Création d'un trade fictif
- ✅ Log d'ouverture réussi  
- ✅ Log de fermeture réussi
- ✅ Données visibles dans Google Sheets

### Redémarrage du bot
- ✅ Service redémarré avec succès
- ✅ Google Sheets initialisé avec l'ID correct
- ✅ Pas d'erreurs dans les logs

## Configuration finale

### Variables d'environnement (.env)
```
GOOGLE_SHEETS_CREDENTIALS=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=17UAKuA7nuyXgYlYm85DprQiU-W6MA4BZALudGxouYEs
ENABLE_GOOGLE_SHEETS=True
```

### URL du Google Sheet
https://docs.google.com/spreadsheets/d/17UAKuA7nuyXgYlYm85DprQiU-W6MA4BZALudGxouYEs

## Vérification du fonctionnement

Pour vérifier que le logging fonctionne lors des prochains trades réels:

1. **Suivre les logs en temps réel**:
   ```bash
   ssh root@213.199.41.168 "journalctl -u tothemoon-tradebot.service -f"
   ```

2. **Chercher les messages de logging**:
   - `📊 Trade OPEN loggé dans Google Sheets - [PAIR]`
   - `📊 Trade CLOSE loggé dans Google Sheets - [PAIR]`

3. **Vérifier dans Google Sheets**:
   - Onglet "Trades" pour les trades individuels
   - Onglet "Dashboard" pour les métriques temps réel

## Statut

✅ **CORRIGÉ** - Le logging Google Sheets fonctionne désormais correctement. Les prochains trades seront automatiquement enregistrés dans la feuille Google Sheets.

## Scripts utiles

- `scripts/surveillance_logs.py` - Surveillance automatique des logs
- `docs/commandes_utiles.md` - Commandes de diagnostic

---
*Corrections appliquées et testées le 17 juillet 2025 à 23:56*
