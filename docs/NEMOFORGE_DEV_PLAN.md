# DEVELOPMENT & IMPLEMENTATION PLAN: NEMOFORGE V1.0
## *Autonomous Self-Training & Optimization Suite*

Questo documento delinea il piano di sviluppo operativo e l'audit tecnico della codebase corrente di `krakenfondazione` per ospitare la nuova suite **NemoForge V1.0**.

---

## 1. AUDIT TECNICO DELLA CODEBASE CORRENTE
Abbiamo esaminato lo stato del codice sorgente nel workspace per identificare i punti di integrazione ottimali per NemoForge:

*   **Logica del Database (`db_manager.py`, `schemas.py`):**
    *   La struttura attuale è già eccellente e persistente. Possiede la tabella `episodic_memory` che registra per ogni decisione: `market_regime`, `trader_decision`, `mentor_advice`, `action_taken` e il `outcome_pnl_pct` finale.
    *   *Azione per NemoForge:* Leggeremo direttamente questa tabella per alimentare la logica di ottimizzazione dei prompt (Meta-Prompt Optimizer).
*   **Motore di Mercato (`market_engine.py`):**
    *   Fornisce le astrazioni CCXT per scaricare candele e calcolare squilibri L2.
    *   *Azione per NemoForge:* Utilizzeremo questo modulo per scaricare dati storici di test (scenari di addestramento) e salvarli localmente in formato JSON/Parquet.
*   **Orchestratore Loop (`run_24h_loop.py`):**
    *   La logica di esecuzione è solida e gestisce i guardrail.
    *   *Azione per NemoForge:* Isoleremo la simulazione del paper broker in una classe riutilizzabile (`LacusEngine`) in modo da poter testare la logica esecutiva sia in tempo reale che su candele storiche velocizzate.

---

## 2. STRUTTURA DELLE CARTELLE DI PROGETTO (NEMOFORGE)
I file di NemoForge saranno organizzati in un modulo dedicato per garantire il massimo isolamento ed AI-navigabilità:

```text
nemoforge/
  ├── __init__.py
  ├── lacus_engine.py       # Motore di backtesting locale accelerato (Spot/Futures)
  ├── prompt_optimizer.py   # Meta-Prompt Optimizer (Interfaccia asincrona con Nemotron 30B)
  ├── telemetry_profiler.py # SentinelProf (Telemetria margini, latenze e GPU)
  └── prompts/
      ├── baseline_broker.txt # Prompt originale di Nemotron
      └── mutated_broker.txt  # Prompt ottimizzato dall'MPO
nemoforge_cli.py            # Interfaccia a riga di comando per Giacomo (es. train, backtest, profiles)
```

---

## 3. PIANO DI SVILUPPO DETTAGLIATO (FASI OPERATIVE)

### 📈 FASE 1: Ingestione Dati Storici & Lacus Engine (Backtester)
*   **Obiettivo:** Creare un simulatore locale deterministico sulla VPS in grado di eseguire strategie su candele passate ad altissima velocità.
*   **Sviluppo:**
    1.  Scrivere `nemoforge/lacus_engine.py`. Questo modulo caricherà file storici di OHLC (es. file di candele PEPE e SOL a 1m scaricate da Kraken) e simulerà un portafoglio cartaceo completo di leva, margini di liquidazione e commissioni impostabili (0.00% o 0.26%).
    2.  Implementare il caricamento del L2 Book Imbalance sintetico.
*   **Verifica:** Una simulazione di 24 ore storiche deve essere eseguita e completata in meno di 5 secondi.

### 🧠 FASE 2: Meta-Prompt Optimizer (MPO — Autoreflection)
*   **Obiettivo:** Sviluppo del ciclo cognitivo di auto-correzione dei prompt tramite Nemotron 30B.
*   **Sviluppo:**
    1.  Scrivere `nemoforge/prompt_optimizer.py`. Il codice interroga `episodic_memory` del database di produzione, estrae i trade con PnL negativo o quelli bloccati per errore di margine.
    2.  Invia questa "cronologia degli errori" a Nemotron-30B (porta 8080) chiedendogli di identificare i pattern fallimentari e modificare il sistema di regole del prompt.
    3.  Salva il prompt modificato in `nemoforge/prompts/mutated_broker.txt`.
*   **Verifica:** Generazione automatica di un prompt modificato contenente veti specifici basati sulle perdite storiche reali.

### 🔄 FASE 3: Circuito di Validazione & Autoadattamento
*   **Obiettivo:** Validare il prompt modificato prima di promuoverlo in produzione.
*   **Sviluppo:**
    1.  Scrivere l'orchestratore di validazione. Esegue il *Lacus Engine* usando il prompt mutato su tre scenari storici diversi.
    2.  Compara le performance (PnL finale, drawdown, turnover) del prompt mutato rispetto al baseline.
    3.  Se il nuovo prompt supera il vecchio in almeno 2 scenari su 3, lo sovrascrive come prompt attivo della run successiva.
*   **Verifica:** Test di promozione automatica superato in ambiente di prova.

### ⚡ FASE 4: SentinelProf (Telemetria)
*   **Obiettivo:** Monitoraggio in background durante le run reali.
*   **Sviluppo:**
    1.  Scrivere `nemoforge/telemetry_profiler.py` per tracciare in tempo reale latenza esecutiva, margin failures e consumo VRAM.

### 🛠️ FASE 5: Integrazione & CLI (nemoforge_cli.py)
*   **Obiettivo:** Dare a Giacomo il controllo completo tramite riga di comando.
*   **Sviluppo:**
    1.  Scrivere `nemoforge_cli.py` per esporre i comandi:
        *   `python3 nemoforge_cli.py download-history --pair PEPEUSD --days 7`
        *   `python3 nemoforge_cli.py backtest --prompt baseline`
        *   `python3 nemoforge_cli.py optimize --run-id FCD467`
        *   `python3 nemoforge_cli.py train` (avvia il ciclo completo MPO + Backtest + Promotion).
