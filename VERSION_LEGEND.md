# LEGENDA DELLE VERSIONI DEL PROGETTO
## *krakenfondazione — Evoluzione Architetturale*

Questa legenda mappa ufficialmente la cronologia dello sviluppo, dei moduli attivi e dell'infrastruttura di ciascuna versione dell'agente speculativo, fino alle odierne orbite di produzione.

---

### 🟢 V5.0 — Standard Orbit
*   **Nome in Codice:** *Standard Standard (Zero-Sentiment)*
*   **Obiettivo:** Primo rilascio stabile dell'agente speculativo bidirezionale su Futures.
*   **Caratteristiche & Moduli:**
    *   Dynamic Asset Mapping (Spot/Futures).
    *   Auto-Mentoring tramite Risk Mentor locale (Llama 3.1 8B).
    *   Nessun feed Sentiment esterno.
    *   Nessuna analisi della microstruttura del book (L2 Book Imbalance).
*   **Directory di default sulla VPS:** `/broker/storage` (ora archiviata in `storage_v5_archive`).

---

### 🔵 V6.0 — Next-Gen Mirror Loop
*   **Nome in Codice:** *Dual-Mirror Loop*
*   **Obiettivo:** Sperimentare l'isolamento ambientale totale per permettere run parallele indipendenti.
*   **Caratteristiche & Moduli:**
    *   Introduzione dell'**isolamento della variabile `$HOME`** in Python (`os.environ["HOME"]`) per isolare i database SQLite del paper broker di Kraken.
    *   Watchdog automatico di chiusura forzata (Flattening a tempo).
*   **Directory di default sulla VPS:** `/broker/storage/storage-next` (originaria).

---

### 🟡 V6.1 — Sentimental Imbalance
*   **Nome in Codice:** *Deep Structure Sentiment*
*   **Obiettivo:** Integrare segnali strutturali del book e sentiment globale delle notizie.
*   **Caratteristiche & Moduli:**
    *   **Sentiment RSS Locale:** Parser integrato per scaricare i feed RSS XML di *CoinTelegraph* e *CoinDesk*, classificati in tempo reale con sentiment da -1.0 a +1.0.
    *   **L2 Order Book Imbalance (LOB Imbalance):** Monitoraggio della pressione microstrutturale del book di livello 2 (bids vs asks cumulati sulle prime 5 righe) per i 10 candidati più volatili.

---

### 🟠 V6.2 — Budget Alignment
*   **Nome in Codice:** *Sovereign Budget Isolation*
*   **Obiettivo:** Prevenire bug di sovrascrittura di bilancio e allineare la cassa di partenza al saldo reale Kraken.
*   **Caratteristiche & Moduli:**
    *   Isolamento e pulizia rigorosa delle variabili `KRAKEN_WORKSPACE` ereditate per sbloccare la CLI cartacea dei Futures.
    *   Preservazione del capitale iniziale reale come parametro immodificabile per l'intera durata della run.

---

### 🔴 V7.0 — Sovereign Safety Gated
*   **Nome in Codice:** *Sovereign Safety & TP/SL Gated*
*   **Obiettivo:** Centralizzare l'esecuzione su Nemotron 30B ed eliminare Llama 8B per prevenire sfasamenti cognitivi e timeout.
*   **Caratteristiche & Moduli:**
    *   **TRE (Main Orchestrator):** Amministratore esterno del loop.
    *   **Risk Mentor & Sovereign Broker unificati** su un singolo modello pesante (**NVIDIA Nemotron 30B GGUF** sulla porta `8080`).
    *   Watchdog rigido di Take Profit (TP) e Stop Loss (SL) gestito a livello di codice deterministico, non delegato all'LLM.

---

### 🟤 V7.1 — Sentinel Mentor
*   **Nome in Codice:** *Mentore d'Accuratezza e Filtro Volumetrico*
*   **Obiettivo:** Proteggere il capitale da decisioni irrazionali dell'agente speculativo.
*   **Caratteristiche & Moduli:**
    *   **Blocco Hardware d'Autorità:** Lo script valuta l'accuratezza storica del Risk Mentor. Se l'affidabilità è alta (>75%) e il Trader tenta un override insensato delle raccomandazioni sul rischio, il codice inibisce l'azione d'ufficio.
    *   **Squeezer Volumetrico:** Esclusione automatica dal trading di tutti i perpetuals con volume di scambio nelle 24 ore inferiore a 500k USD.

---

### 🛰️ V8.0 — Dual-Orbit (La Produzione Corrente)
*   **Nome in Codice:** *The Ultimate Frictionless Duel*
*   **Obiettivo:** Confrontare in tempo reale l'impatto economico e l'attrito delle commissioni (Frictionless vs Real-Friction) su run gemelle.
*   **Caratteristiche & Struttura Parallela:**
    *   **Orbit A (REAL-FEE - *storage-next*):** Simula il trading reale comprensivo di commissioni (fee rate dello 0.26% del livello Kraken Starter) e simulazione di slippage dinamico.
    *   **Orbit B (ZERO-FEE - *storage-zero*):** Esegue il trading in condizioni ideali senza commissioni (fee rate dello 0.00%) e senza slippage, fungendo da benchmark teorico puro.
    *   **Infrastruttura:** Due demoni di background `run_24h_loop.py` completamente isolati, avviati con `$HOME` asimmetrici e configurazioni paper broker separate, che attingono allo stesso server di inferenza pesante (Nemotron 30B, porta 8080).
