# ARCHITECTURAL EVOLUTION PLAN: NEMOFORGE V2.0
## *Addressing Core Execution Integrity, Ledger Reconciliations, and Cognitive Sanity*

This plan outlines the concrete technical architecture, database schemas, and migration steps designed to address the vulnerabilities identified in the recent system audit, fully integrated with Giacomo's strict design mandates.

---

## 1. CLASSIFICAZIONE DELLE MANOVRE

Per garantire la massima sicurezza operativa e stabilità delle run attive, dividiamo gli interventi in tre classi di priorità:

### A. Correzioni Urgenti di Integrità Operativa (Priorità 1)
*   **Problema 1: Processi Concorrenti (Doppio Loop).** Più istanze del loop scrivono sullo stesso DB ed inviano segnali concorrenti, bloccando SQLite e alterando la frequenza dei fills.
    *   *Soluzione V2.0 (Upgrade):* Implementazione di un **lock del file descriptor tramite `flock` esclusivo e non bloccante** (modulo `fcntl` di Python su `/tmp/nemoloop.lock`). Poiché il lock è legato al file descriptor del processo gestito dal kernel del sistema operativo, in caso di crash il lock viene **rilasciato automaticamente**, azzerando il rischio di "lock fantasma". Migrazione totale del loop a **servizio systemd controllato (`nemoloop.service`)**.
*   **Problema 2: Registro Ledger Corrotto (PnL = 0 all'apertura).** La tabella `episodic_memory` registra il trade come concluso con P&L a zero all'istante di invio dell'ordine.
    *   *Soluzione V2.0 (Upgrade):* **Eliminazione totale della riga incriminata `update_t1(... pnl_pct=0, exit_timestamp=...)`** subito dopo il fill in `run_24h_loop.py`. Separazione relazionale del database: gli ordini e le posizioni storicizzano gli eventi, mentre il P&L reale viene registrato ed aggiornato **solo ed esclusivamente alla chiusura effettiva e consolidata della posizione**.
*   **Problema 3: active_trades.json vuoto & Volatilità TP/SL.** Perdita di tracciamento di entry, size e parametri a seguito di crash o riavvii dei processi.
    *   *Soluzione V2.0:* Transizione totale dello stato di monitoraggio TP/SL a tabelle transazionali SQLite, oppure ricostruzione dinamica dello stato interrogando direttamente le API del paper broker all'avvio.

### B. Miglioramenti del Sistema di Ricerca (Priorità 2)
*   **Problema 4: Lacus con segnali Mock.** Il simulatore di backtest non testa la vera strategia decisionale di Nemotron ma esegue operazioni di prova.
    *   *Soluzione V2.0:* Refactoring di `lacus_engine.py` per importare ed eseguire lo stesso identico modulo decisionale del loop di produzione (`trader.py` + `mentor_advice`), permettendo un vero addestramento cognitivo out-of-sample.
*   **Problema 5: Tracciabilità del Codice VPS.** Il codice in esecuzione sulla VPS non è attualmente agganciato in modo tracciabile al repository pubblicato su GitHub.
    *   *Soluzione V2.0:* Inizializzazione e configurazione di un **repository Git locale sulla VPS** in `/broker/storage/storage-next` agganciato al remote ufficiale di NemoForge. Questo permette il tracciamento esatto di ogni commit e la verifica digit-exact di quale versione del codice sta girando sulla VPS in tempo reale.

### C. Funzionalità Opzionali & Configurazione (Priorità 3)
*   **Problema 6: Parametrizzazione dell'Esposizione.** Il limite notional fisso potrebbe frenare l'intento speculativo ad alta aggressività richiesto da Giacomo.
    *   *Soluzione V2.0 (Upgrade):* Il limite di esposizione notional totale (es. l'80% o 100% del capitale) viene spostato come **variabile dinamica di configurazione in `run_config.json`**. Non agirà come vincolo fisso di sistema, ma come parametro di missione. Se Giacomo richiede massima aggressività, la soglia rimarrà elevata: ciò che conta è che l'esposizione, la leva e il rischio complessivo siano **misurati, loggati ed analizzati con precisione millimetrica**, mai forzatamente ridotti.

---

## 2. FONTE DI VERITÀ & POSIZIONI DINAMICHE (Ledger Rules)

Sotto le nuove linee guida, l'architettura finanziaria è governata da regole inflessibili:

### 🏛️ 1. Il Paper Broker come Unica Fonte di Verità
Il database SQLite e i file di stato interni agiscono come registri di eventi e specchi contabili, ma **il paper broker sulla VPS è l'unica ed assoluta fonte di verità finanziaria**.
*   In caso di riconciliazione o discrepanze, SQLite deve leggere e allinearsi allo stato delle posizioni del broker (tramite le query della CLI); **SQLite non deve mai sovrascrivere o "correggere" silenziosamente l'esposizione reale del broker paper**.

### 📉 2. Gestione Dinamica delle Posizioni (Scale-In / Scale-Out)
Il database deve supportare la variazione dinamica della taglia per lo stesso simbolo, registrando con precisione atomica:
*   **Prezzo Medio di Carico (Average Entry Price):** Ricalcolato ad ogni aumento di posizione (Scale-In):
    $$\text{Average Price} = \frac{\sum (\text{Prezzo}_i \times \text{Size}_i)}{\sum \text{Size}_i}$$
*   **Commissioni Cumulative:** Somma corrente di tutte le fee pagate per gli ordini parziali legati a quella posizione.
*   **PnL Realizzato:** Calcolato e consolidato in tempo reale su SQLite ogni volta che una posizione viene parzialmente o interamente ridotta (Scale-Out).
*   **Funding Rates:** Storicizzazione dei costi di finanziamento applicati sui perpetuals.
*   **PnL Non Realizzato:** Calcolato in tempo reale sulla base della differenza tra il prezzo medio di carico (`entry_price`) ed il mark price corrente fornito dallo scanner.

---

## 3. MODIFICHE PROPOSTE AL DATABASE (SCHEMA EVOLUTION)

```sql
-- 1. Registro storico di ogni singolo ordine inviato/eseguito
CREATE TABLE IF NOT EXISTS paper_orders (
    order_id TEXT PRIMARY KEY,       -- es. FP-00001
    run_id TEXT,                     -- Legato alla run attiva
    symbol TEXT,                     -- es. PF_SOLUSD
    action TEXT,                     -- buy o sell
    size REAL,                       
    fill_price REAL,                 
    fee REAL,                        
    slippage REAL,                   
    timestamp INTEGER,               
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

-- 2. Registro transazionale delle posizioni attualmente aperte a mercato
CREATE TABLE IF NOT EXISTS paper_positions (
    symbol TEXT PRIMARY KEY,         -- Chiave primaria basata sul simbolo (un'unica riga attiva per asset)
    run_id TEXT,
    side TEXT,                       -- 'long' o 'short'
    size REAL,                       -- quantitativo esposto corrente (somma algebrica)
    average_entry_price REAL,        -- prezzo medio ponderato aggiornato ad ogni scale-in
    leverage REAL,                   -- leva corrente impostata
    cumulative_fees REAL,            -- totale fee pagate per questa posizione
    accumulated_funding REAL,        -- totale funding accumulato
    tp_price REAL,                   -- take profit dinamico
    sl_price REAL,                   -- stop loss dinamico
    opened_at INTEGER,
    last_updated INTEGER,
    status TEXT                      -- 'OPEN' o 'CLOSED'
);

-- 3. Registro dei trade conclusi e del P&L realizzato definitivo (Sorgente MPO)
CREATE TABLE IF NOT EXISTS paper_trades_closed (
    trade_id TEXT PRIMARY KEY,
    run_id TEXT,
    symbol TEXT,
    side TEXT,
    size REAL,
    entry_price REAL,
    exit_price REAL,
    realized_pnl REAL,               -- in valuta reale ($)
    realized_pnl_pct REAL,           -- percentuale reale esatta
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

## 4. PIANO DI MIGRAZIONE: MANUTENZIONE PROGRAMMATA

Abbandoniamo la dicitura di migrazione "zero downtime" per adottare un protocollo di **Manutenzione Programmata** sicuro, controllato e verificato:

1.  **Fase Flat (Nessun rischio a mercato):** Si attende una finestra temporale in cui il paper broker è in stato di **posizione flat (0 posizioni aperte)**, oppure si forza manualmente il flattening delle posizioni attive in EUR.
2.  **Snapshot e Backup DB:** Si arresta il daemon di background e si esegue un backup fisico completo (`cp -r`) dei database SQLite e dello stato del sistema in una cartella di salvataggio temporanea sulla VPS.
3.  **Applicazione Migrazioni:** Si esegue la migrazione degli schemi del database SQLite creando le nuove tabelle relazionali.
4.  **Verifica e Rollback:** Si avvia un ciclo di smoke test automatici. Se i test falliscono, si effettua il rollback ripristinando il backup del DB ed il commit git precedente in meno di 2 minuti.

---

## 5. TEST DI ACCETTAZIONE ESPLICITI

Ogni fase di sviluppo di NemoForge V2.0 deve essere convalidata dal superamento di 8 test di accettazione espliciti:

1.  **Doppio Avvio (Double-Start test):**  
    *Esecuzione:* Tentativo di lanciare manualmente `run_24h_loop.py` mentre il servizio systemd `nemoloop` è già attivo.  
    *Risultato atteso:* Il secondo processo fallisce immediatamente all'istante zero restituendo l'errore di violazione del lock esclusivo `flock` (risorsa occupata).
2.  **Crash / Restart Recovery test:**  
    *Esecuzione:* Uccidere forzatamente il processo attivo (`kill -9`) mentre vi sono posizioni aperte a mercato, e riavviare il servizio.  
    *Risultato atteso:* Al riavvio, il sistema interroga il paper broker (fonte di verità), recupera lo stato delle posizioni, ricostruisce il monitor TP/SL e riprende l'esecuzione senza perdere alcun parametro o generare trade orfani.
3.  **Inserimento / Fill Rifiutato (Rejected Fill test):**  
    *Esecuzione:* Inviare un ordine che viola i limiti di margine o di leva dell'exchange.  
    *Risultato atteso:* L'ordine viene rifiutato correttamente dal broker, lo stato delle posizioni rimane immutato e l'errore viene loggato esplicitamente in `logs/rejections.log` per l'analisi di Nemotron.
4.  **Riconciliazione Posizioni (Position Reconciliation test):**  
    *Esecuzione:* Modificare o chiudere manualmente una posizione tramite la CLI di Kraken Futures.  
    *Risultato atteso:* Entro 5 minuti, la routine di riconciliazione rileva lo scostamento, aggiorna il database SQLite transazionale allineando lo specchio contabile all'esatto stato del broker paper, calcolando l'eventuale P&L realizzato.
5.  **Take Profit (TP test):**  
    *Esecuzione:* Simulare o attendere che il mark price tocchi la soglia impostata di `tp_price`.  
    *Risultato atteso:* Il monitor rileva la violazione, invia l'ordine di mercato di chiusura, consolida la riga in `paper_trades_closed` e aggiorna l'equity reale.
6.  **Stop Loss (SL test):**  
    *Esecuzione:* Simulare o attendere che il mark price tocchi la soglia impostata di `sl_price`.  
    *Risultato atteso:* Chiusura immediata della posizione a mercato, scrittura in `paper_trades_closed` specificando la causale 'SL' e consolidamento delle perdite.
7.  **Spiattellamento Forzato (Flatten test):**  
    *Esecuzione:* Raggiungere la data di scadenza della run o inviare il comando di stop manuale.  
    *Risultato atteso:* Liquidazione atomica di tutte le posizioni a mercato, cassa convertita interamente in EUR, e tutti i log marcati come `MISSION COMPLETE`.
8.  **Calcolo P&L Realizzato test:**  
    *Esecuzione:* Eseguire un'operazione di Scale-Out parziale su una posizione aperta.  
    *Risultato atteso:* SQLite registra l'ordine parziale, calcola e aggiorna il P&L realizzato sulla quota parte chiusa basandosi sull'Average Entry Price, e mantiene aperta la riga della posizione con la size aggiornata.
