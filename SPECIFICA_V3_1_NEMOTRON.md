# SPECIFICA TECNICA ESEGUIBILE V3.1: NEMOTRON SOVEREIGN BROKER
*Architettura Cognitiva Basata su CVRF, Reflection e Scorecards*

## 1. SEQUENZA DEL DECISION LOOP (Dall'arrivo dati all'apprendimento)

### A. Fast Loop (Trigger di Mercato -> Decisione)
1. **Trigger Deterministico:** Il demone in Python ascolta il WebSocket di Kraken.
   - Si attiva se rileva: Cambio Volatilità > X%, Anomalia Volume, Breakout di Prezzo, Cambio Regime, o Trigger Temporale.
   - Crea un oggetto JSON `MARKET_EVENT`.
2. **Context Compilation:** Python compatta in un JSON: `MARKET_EVENT` + Bilancio Portafoglio + `GLOBAL_INTENT` + Le top 5 `BELIEFS` attive.
3. **Interrogazione Strategist:** Lo Strategist analizza il contesto e restituisce un JSON definendo il Regime (es. `HIGH_VOL_BULLISH`) e la confidenza.
4. **Interrogazione Mentor:** Il Mentor riceve il Regime e l'evento, consulta il DB vettoriale delle operazioni passate simili (Episodic Memory), e restituisce un JSON con la sua opinione (`ADVICE`).
5. **Esecuzione Trader (Nemotron):** Il Trader riceve TUTTO (Mercato, Regime dello Strategist, Consiglio del Mentor). Prende la decisione finale e la giustifica.
6. **Execution (CCXT):** Se il Trader decide di operare, Python invia l'ordine via CCXT. I dati completi (JSON del Mentor, Strategist e Trader) vengono salvati in SQLite.

### B. Slow Loop (Apprendimento Post-Trade -> Belief Validation)
1. **Chiusura Trade / Outcome:** Python registra il risultato esatto (PnL, durata, drawdown) dell'operazione.
2. **Reflection Engine:** Genera un'osservazione post-trade ("Perché abbiamo perso/guadagnato?").
3. **Metrics Engine (Python):** Valuta matematicamente chi aveva ragione tra Trader, Mentor e Strategist, aggiornando le Scorecard.
4. **Belief Validator:** Se la Reflection suggerisce una nuova "Regola" (Belief Candidate), Python cerca tra i trade storici prove a favore o contro, calcola statistiche, e la promuove ad `ACTIVE` o la boccia.

---

## 2. SCHEMA DATABASE (SQLite)

### Table: `episodic_memory` (I trades e le decisioni passate)
- `trade_id` (PK)
- `timestamp`
- `market_regime` (Es. "HIGH_VOL_BEARISH")
- `strategist_view_json`
- `mentor_advice_json`
- `trader_decision_json`
- `who_disagreed` (JSON list, es. `["mentor"]`)
- `action_taken` (Buy/Sell/Hold, Pair, Volume, Price)
- `outcome_pnl_pct` (Risultato del trade)
- `outcome_drawdown`
- `reflection_notes`

### Table: `beliefs` (Il sistema di credenze e regole)
- `belief_id` (PK)
- `statement` (La regola in linguaggio naturale)
- `created_by` (Es. "mentor", "reflection", "strategy_lab")
- `supporting_trades_count` (Aggiornato dinamicamente)
- `contradicting_trades_count`
- `mean_return_supporting`
- `mean_return_contradicting`
- `applicable_regimes` (JSON list)
- `confidence_score` (Float 0-1)
- `status` (CANDIDATE, ACTIVE, RETIRED)

### Table: `scorecards` (Valutazione delle Intelligenze)
- `entity_id` (PK) ("trader", "mentor", "strategist")
- `regime` (Es. "OVERALL", "LATERAL", "VOLATILE")
- `correct_calls` (Quante volte la sua view ha portato o avrebbe portato profitto)
- `wrong_calls`
- `accuracy_rate` (correct / total)
- `avg_pnl_when_followed`

---

## 3. JSON CONTRACTS E PROMPT

### 3.1 Global Strategic Intent (Iniettato ovunque)
```json
{
 "objective": "maximize_growth",
 "aggressiveness": 1.0,
 "exploration": 0.9,
 "preferences": {
   "concentration": "allowed",
   "high_volatility": "allowed",
   "contrarian_trades": "allowed",
   "experimental_strategies": "encouraged"
 },
 "human_directive": "Sii aggressivo il più possibile e accetta operazioni spregiudicate. Inventa ed esplora senza paura del rischio."
}
```

### 3.2 Strategist Output Contract
**Prompt:** "Classifica il regime di mercato attuale usando i dati OHLCV recenti."
```json
{
  "regime": "HIGH_VOL_BREAKOUT",
  "confidence": 0.85,
  "rationale": "BTC dominance rising sharply accompanied by 3x average volume."
}
```

### 3.3 Mentor Output Contract
**Prompt:** "Confronta il mercato attuale con la tua Episodic Memory. Questo setup funziona?"
```json
{
  "past_similar_trades_found": 12,
  "success_rate_of_past_trades": 0.33,
  "advice": "DO NOT ENTER. Wait for retracement.",
  "confidence": 0.92,
  "active_belief_invoked": "BEL-00492"
}
```

### 3.4 Trader (Nemotron) Output Contract
**Prompt:** "Sei il decisore finale. Mentor dice di stare fermo. Strategist vede alta volatilità. La tua direttiva è aggressività estrema."
```json
{
  "trader_view": "Mentor's past data is based on lower momentum. Current volume supports a contrarian aggressive entry.",
  "confidence": 0.88,
  "disagrees_with": ["mentor"],
  "decision": {
    "action": "buy",
    "pair": "SOLEUR",
    "volume": 2.5
  }
}
```

---

## 4. IL "STRATEGY LAB" (Creazione Nuove Strategie)
Il Lab non si limita a cambiare i parametri (RSI 20 -> 30).
**Sequenza Creazione Strategia:**
1. **Observation (Da Reflection):** "Le rotture di volume alto in range laterali falliscono spesso."
2. **Hypothesis Generation (LLM):** "E se filtrassimo i breakout per l'accelerazione dell'Open Interest sui Futures invece che sul volume spot?"
3. **Specification (LLM):** Compila un JSON con le features necessarie (Es. `feature_1: Open_Interest_Delta_15m`).
4. **Backtest (Python):** Testa matematicamente l'ipotesi sui dati storici in `/shared/data`.
5. **Critique & Mutation (LLM):** "L'ipotesi produce troppo rumore, cambiamo il timeframe a 1H."
6. **Promotion:** Se il test supera l'indice di Sharpe prefissato, la nuova "Strategia" diventa una Belief attiva nel sistema.