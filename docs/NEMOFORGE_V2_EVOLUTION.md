# ARCHITECTURAL EVOLUTION PLAN: NEMOFORGE V2.0
## *Addressing Core Execution Integrity, Ledger Reconciliations, and Cognitive Sanity*

This plan outlines the concrete technical architecture, database schemas, and migration steps designed to address the vulnerabilities identified in the recent system audit. It defines the path to transition the `krakenfondazione` core loop into a bulletproof, institutional-grade sovereign trading machine.

---

## 1. CLASSIFICAZIONE DELLE MANOVRE

Per garantire la massima sicurezza operativa e stabilità delle run attive, dividiamo gli interventi in tre classi di priorità:

### A. Correzioni Urgenti di Integrità Operativa (Priorità 1)
*   **Problema 1: Processi Concorrenti (Doppio Loop).** Più istanze del loop scrivono sullo stesso DB ed inviano segnali concorrenti, bloccando SQLite e alterando la frequenza dei fills.
    *   *Soluzione:* Implementazione di un **file lock atomico (`/tmp/nemoloop.lock`)** e di un heartbeat a database per impedire l'avvio di istanze duplicate. Migrazione del loop da script `nohup` a **servizio gestito `systemd`**.
*   **Problema 2: Registro Ledger Corrotto (PnL = 0 all'apertura).** La tabella `episodic_memory` registra il trade come concluso con P&L a zero all'istante di invio dell'ordine, rendendo nullo l'apprendimento di Nemotron.
    *   *Soluzione:* Separazione formale delle tabelle dei trade in due entità: `orders` (stato di invio/riempimento) e `positions` (esposizione in corso). Il P&L reale (`outcome_pnl_pct`) viene valorizzato ed aggiornato **esclusivamente alla chiusura fisica e documentata** della posizione.
*   **Problema 3: active_trades.json vuoto.** Perdita di tracciamento di entry, size e TP/SL a seguito di arresti o riavvii dei processi.
    *   *Soluzione:* Transizione totale dello stato delle posizioni attive da file JSON volatile a tabelle transazionali SQLite, oppure ricostruzione dinamica dello stato interrogando direttamente le API del paper broker all'avvio.

### B. Miglioramenti del Sistema di Ricerca (Priorità 2)
*   **Problema 4: Lacus con segnali Mock.** Il simulatore di backtest non testa la vera strategia decisionale di Nemotron ma esegue operazioni di prova.
    *   *Soluzione:* Refactoring di `lacus_engine.py` per importare ed eseguire lo stesso identico modulo decisionale del loop di produzione (`trader.py` + `mentor_advice`), permettendo un vero addestramento cognitivo out-of-sample.

### C. Funzionalità Opzionali (Priorità 3)
*   **Problema 5: Sovraesposizione / Sbilanciamento dello Short.** Il modello ripete decisioni short in modo cieco senza controllare l'esposizione cumulata.
    *   *Soluzione:* Introduzione di filtri di diversificazione per simbolo, limiti notional massimi di esposizione complessiva e log esplicito dei guardrail attivati.

---

## 2. MODIFICHE PROPOSTE AL DATABASE (SCHEMA EVOLUTION)

Attualmente, il DB ha solo 4 tabelle (`episodic_memory`, `beliefs`, `scorecards`, `runs`). Proponiamo l'introduzione di tre nuove tabelle strutturate per tracciare il ciclo di vita del trade in modo transazionale ed atomico:

```sql
-- Tracciamento di ogni singolo ordine inviato ed eseguito
CREATE TABLE IF NOT EXISTS paper_orders (
    order_id TEXT PRIMARY KEY,       -- ID univoco dell'ordine (es. FP-00001)
    run_id TEXT,                     -- Legato alla run corrente
    symbol TEXT,                     -- es. PF_SOLUSD
    action TEXT,                     -- buy o sell
    size REAL,                       -- quantitativo ordinato
    fill_price REAL,                 -- prezzo medio di carico eseguito
    fee REAL,                        -- commissione pagata
    slippage REAL,                   -- slippage stimato/reale
    timestamp INTEGER,               -- epoch
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

-- Tracciamento delle posizioni attive sul mercato
CREATE TABLE IF NOT EXISTS paper_positions (
    position_id TEXT PRIMARY KEY,    -- Generato all'apertura
    run_id TEXT,
    symbol TEXT,
    side TEXT,                       -- long o short
    size REAL,                       -- quantitativo attualmente esposto
    entry_price REAL,                -- prezzo medio d'ingresso
    leverage REAL,                   -- leva impostata
    tp_price REAL,                   -- take profit dinamico
    sl_price REAL,                   -- stop loss dinamico
    opened_at INTEGER,
    status TEXT,                     -- 'OPEN' o 'CLOSED'
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

-- Tracciamento dei trade conclusi e del P&L realizzato reale
CREATE TABLE IF NOT EXISTS paper_trades_closed (
    trade_id TEXT PRIMARY KEY,
    run_id TEXT,
    symbol TEXT,
    side TEXT,
    size REAL,
    entry_price REAL,
    exit_price REAL,
    realized_pnl REAL,               -- P&L assoluto in valuta
    realized_pnl_pct REAL,           -- P&L percentuale esatto
    fee_total REAL,
    duration INTEGER,                -- in secondi
    mae_pct REAL,                    -- Maximum Adverse Excursion %
    mfe_pct REAL,                    -- Maximum Favorable Excursion %
    exit_reason TEXT,                -- 'TP', 'SL', 'FLATTENING' o 'MANUAL'
    closed_at INTEGER,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);
```

---

## 3. PIANO DI IMPLEMENTAZIONE (FASE PER FASE)

### FASE 1: Stabilizzazione & Lock Atomico
1.  Sviluppare un modulo di locking (`nemoforge/utils/lock.py`) che all'avvio di `run_24h_loop.py` crea `/tmp/nemoloop.lock` scrivendoci il PID del processo. Se il file esiste e il PID è attivo, il loop si arresta immediatamente con errore prevenendo doppie istanze concorrenti.
2.  Scrivere il file unit di systemd `/etc/systemd/system/nemoloop.service` per gestire il loop come servizio di sistema resiliente (con riavvio automatico in caso di crash).
3.  Modificare `bootstrap_24h.py` affinché, all'avvio di una nuova run, interroghi systemd, arresti in modo sicuro il servizio attivo, esegua la riconciliazione/flattening, e solo allora riavvii il servizio con il nuovo `run_id`.

### FASE 2: Ledger Riconciliato & Transazionale
1.  Implementare lo schema DB descritto sopra.
2.  Modificare `run_24h_loop.py` per scrivere in `paper_orders` e `paper_positions` in modo atomico ad ogni fill.
3.  Implementare una routine di **Riconciliazione Periodica** (eseguita ogni 5 minuti) che interroga il paper broker tramite CLI (`futures paper positions`) e corregge lo stato di `paper_positions` in SQLite per sanare eventuali discrepanze.
4.  Scrivere il calcolatore esatto di P&L in `paper_trades_closed` valorizzando l'esito reale solo alla chiusura fisica della posizione.

### FASE 3: TP/SL ed Esposizione Notional
1.  Spostare la logica di monitoraggio TP/SL da `active_trades.json` alla tabella transazionale `paper_positions` di SQLite.
2.  All'avvio, il monitor TP/SL interroga il DB per trovare tutte le righe con stato `OPEN` e le traccia in tempo reale, garantendo la totale tolleranza ai riavvii dei processi.
3.  Aggiungere controlli di esposizione nel modulo di decisione del Trader per inibire nuove aperture se l'esposizione notional totale supera l'80% del capitale.

### FASE 4: Apprendimento & Audit Cognitivo Nemotron
1.  Rilasciare il nuovo modulo di ottimizzazione dei prompt `PromptOptimizer` che si nutre dei dati esatti di `paper_trades_closed` (analizzando esclusivamente trade con esiti reali e chiusi, non ordini vuoti).
2.  Associare a ciascuna run e variante di prompt un hash di versione per tracciare scientificamente quale prompt ha generato quali risultati.

### FASE 5: Integrazione & Backtest Out-Of-Sample
1.  Modificare `nemoforge/lacus_engine.py` affinché importi la vera logica esecutiva e di giudizio (`trader.py` e `mentor_advice`) invece di usare segnali mock, simulando commissioni, slippage e vincoli di margine del paper broker in modo matematicamente identico.
2.  Scrivere la suite di test automatica per stressare il sistema contro riavvii del processo, concorrenza e calcoli di P&L.

---

## 4. STRATEGIA DI MIGRAZIONE & RISCHI (Zero Downtime)
*   **Nessuna Perdita dei Dati Correnti:** Le vecchie tabelle (`episodic_memory`) non verranno cancellate ma mantenute. Le nuove tabelle verranno create in modo incrementale tramite migrazione dello schema.
*   **Rollback Plan:** Se una fase di sviluppo della V2.0 fallisce o si blocca durante il live paper loop, è sufficiente ripristinare il backup fisico di pre-migrazione della V8.2 (che conserviamo in `/broker/storage/storage_v6_backup_2026-08-16.tar.gz` o tramite ripristino git al commit `a1b212a`), garantendo il ritorno immediato alle condizioni operative stabili e flattate.
