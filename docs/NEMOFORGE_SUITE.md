# ARCHITECTURAL SPECIFICATION: NEMOFORGE V1.0
## *The Sovereign Self-Training & Strategy Optimization Suite*

> "The ultimate goal is to arrive at a perfect trading machine that self-adapts and aggressively attacks the market without getting blocked."

---

## 1. VISIONE STRATEGICA
**NemoForge V1.0** è la suite di auto-addestramento strategico locale e asincrona progettata per girare interamente sulla VPS di inferenza e allinearsi asincronamente con il Control Plane di U50. 

Invece di limitarsi a eseguire segnali statici, NemoForge trasforma l'ecosistema in un **ciclo evolutivo chiuso** (Closed-Loop Autonomous Learning), in cui il modello pesante (NVIDIA Nemotron 30B GGUF) impara autonomamente dai propri errori e dai propri successi, ottimizza i parametri di trading, testa l'affidabilità delle risposte del Risk Mentor e rilascia macro-prompt migliorati per le run successive.

---

## 2. PILASTRI ARCHITETTURALI

```
                  +-----------------------------------+
                  |      KRAKEN MARKET SCANNER        | (Feed Candele & L2 Book)
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |      LACUS BACKTEST ENGINE        | (Simulatore Locale V8.0)
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |     METAPROMPT OPTIMIZER (MPO)    | (Self-Reflection su Nemotron 30B)
                  +-----------------+-----------------+
                                    |
                                    v
+-----------------------------------+-----------------------------------+
|                                                                       |
v                                                                       v
PROMPT EVOLUTI (V8.1+)                                  DIAGNOSTICA BOTTLENECKS
(Pockets, Leva, Frequenza)                              (Margin, Latency, Slippage)
```

### 📊 1. Lacus Backtest Engine (Il Simulatore di Volo)
Un motore di simulazione asincrono installato sulla VPS che riproduce le condizioni del paper broker di Kraken (Spot e Futures) su dati storici:
*   **OHLC Replay:** Carica e riproduce candele storiche a 1m/5m/15m memorizzate localmente per intere giornate.
*   **L2 Order Book Synthetic Imbalance:** Ricostruisce lo squilibrio del book di livello 2 a partire dagli archivi storici dei dati L2 per testare la sensibilità del modello alle pressioni microstrutturali.
*   **Friction Selector:** Permette di testare la strategia impostando selettivamente commissioni (da 0.00% a 0.26%) e livelli di slippage (da 0% a 2%) per calcolare in anticipo il *Fee Drag* prima del deploy reale.

### 🧠 2. Meta-Prompt Optimizer (MPO — Autoreflection)
Un modulo di self-learning che gira periodicamente sulla VPS sfruttando Nemotron 30B per analizzare la cronologia delle decisioni:
*   **Analisi degli Insuccessi:** Interroga il database SQLite (`episodic_memory`) estraendo i trade che hanno registrato un PnL negativo o che sono stati bloccati per violazione dei guardrail hardware.
*   **Prompt Mutator:** Nemotron esamina il macro-prompt precedente ed elabora una variante migliorata (es. aggiungendo un guardrail specifico per PEPE o riducendo la leva in determinati regimi).
*   **Backtest Validation:** La nuova variante di prompt viene testata sul *Lacus Engine* su 3 scenari storici diversi (Trend, Range, Volatilità). Se la performance migliora rispetto al baseline, il prompt viene marcato come "APPROVED" ed esportato in produzione per le run successive.

### ⚡ 3. SentinelProf (Diagnostica dei Colli di Bottiglia)
Un demone passivo di telemetria che traccia l'efficienza esecutiva in parallelo alle run attive:
*   **Margin Blocker Tracker:** Rileva e registra tutti gli errori `Insufficient margin` (come quelli visti su SOL e PEPE) per calcolare la frequenza con cui l'algoritmo si trova "bloccato" senza poter operare, calcolando la dimensione ottimale dei buffer di margine d'emergenza.
*   **Latency & Timeout Auditor:** Misura i millisecondi richiesti per l'inferenza di Nemotron 30B, rilevando eventuali ritardi esecutivi legati alla GPU o alla coda di llama.cpp.
*   **Slippage Leakage Analyzer:** Compara l'Effective Entry (prezzo finale di carta) con il Real Entry (prezzo teorico istantaneo) per quantificare i centesimi persi durante l'esecuzione del comando di trading.

---

## 3. PROGRAMMA DI ROLL-OUT (DA V8.0 A MACCHINA PERFETTA)

### 🛑 Fase 1: Identificazione Colli di Bottiglia (Oggi)
Identifichiamo e isoliamo i 3 problemi principali emersi nell'ultimo duello:
1.  **Margin Freeze:** L'algoritmo satura il margine al 99% nei primi minuti e rimane bloccato per 11 ore senza poter chiudere o ruotare le posizioni a causa della mancanza di margine per posizioni di segno opposto (Hedge).
2.  **Fee Bleeding:** L'estrema frequenza operativa azzera l'alpha della strategia netta.
3.  **Hedge Inability:** Mancanza di una logica di inversione rapida della posizione (se SOL o PEPE invertono la rotta, il bot deve poter eseguire un flattening parziale ed invertire l'esposizione anziché attendere passivamente lo stop-loss).

### ⚙️ Fase 2: Implementazione dei Moduli (Prossime 48h)
*   Deploy di **Lacus Engine** su VPS.
*   Scrittura del modulo di auto-valutazione dei prompt (**MPO**).
*   Abilitazione del monitoraggio di telemetria passiva per i margini e le latenze.

### 🚀 Fase 3: Auto-Adattamento in Produzione (V8.5+)
Il sistema, ad ogni conclusione di run da 12/24 ore, lancia autonomamente la suite di ottimizzazione dei parametri, rigenera le proprie regole e si prepara alla run successiva con un'aggressività calibrata sui regimi reali di mercato.
