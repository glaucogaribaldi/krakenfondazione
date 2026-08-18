# MISSION INTEGRATION PLAN: 24H AGGRESSIVE RUN (V3.1 COMPLIANT)

## 1. COMPATIBILITÀ E CRITICHE ARCHITETTURALI
La missione delineata nel file `NEMOTRON_24H_AGGRESSIVE` si innesta **perfettamente** sul telaio che abbiamo appena costruito (SQLite, LanceDB, Multiplexing, CVRF, JSON Contracts). Non c'è nulla da scartare della V3.1, ma ci sono componenti da **potenziare** prima del lancio.

### Le Sfide Immediate (Cosa devo adattare/costruire prima dello START):
1. **Discovery Dinamica:** Non possiamo più cablare in hardcode la lista delle coppie in `market_engine.py`. Devo scrivere un modulo che, allo startup, interroghi Kraken tramite la tua *Real API (Read-Only)* per scaricare l'intero universo scambiabile (Spot + Futures Perpetui compatibili), ne calcoli il volume e scremi via lo "scarto" illiquido, passandolo al *Market Scanner* che abbiamo teorizzato.
2. **Unified Paper Ledger (Spot + Futures):** Kraken tratta le API Spot e Futures in modo diverso. Noi dobbiamo creare un `Portfolio_State_JSON` unificato. Nemotron deve vedere "Capitale X" e decidere da solo se allocarlo comprando Spot o simulando l'apertura di un margine Futures (sfruttando il trasferimento simulato che abbiamo sbloccato prima).
3. **Target-Awareness Injection:** Il prompt del Trader deve includere una calcolatrice matematica viva. Se l'obiettivo è +5% e siamo a -2%, il `distance_from_target` e il `time_remaining` devono entrare nel `Market Snapshot` prima della decisione (T0).

---

## 2. MODIFICHE ALL'INVENTARIO (Rispetto all'AUTONOMOUS_EXECUTION_ROADMAP.md)

Ecco come cambia il piano d'azione per supportare questa missione:

### Fase 1: Inizializzazione della "Run" (Start Procedure)
Prima di lanciare il Fast Loop, scriverò uno script "Bootstrapper" (`start_24h_run.py`) che eseguirà i passaggi indicati:
- Leggere la *Total Real Kraken Equity* dalle tue chiavi API Read-Only e bloccarla in un file `run_state.json`. Questo è il nostro **Paper Initial Equity**.
- Registrare un UUID fisso (`run_id`) che firmerà ogni singolo T0 inserito nel Database SQLite.
- Scrivere le scadenze: `start_time` e `flattening_deadline` (Esattamente 23 ore e 45 minuti dopo lo start, per dare tempo al sistema di liquidare gli ordini).

### Fase 2: Il Motore di Discovery e Ranking
Integro il `market_engine.py` (lo Scanner) affinché non faccia solo calcoli di prezzo, ma filtri l'universo:
- Estrae tutti gli asset Kraken con leva abilitata e mercato spot liquido.
- Produce un JSON con i *Top 10 Opportunity Candidates* basati su volatilità e momentum. Questo alleggerisce il prompt del Trader e risparmia VRAM.

### Fase 3: Shadow Lanes (La genialata architetturale)
Il documento chiede simulazioni alternative (Shadow Lanes).
*Come lo implemento sulle Tesla T4:* Non posso spawnare container infiniti, ma posso far calcolare asincronamente al LLM **scenari paralleli pre-trade** in Python. Quando si verifica uno *State Change*, il Python chiede a Nemotron "Dammi la mossa principale (Main Paper) e 2 alternative puramente numeriche (Shadow)". Solo la principale viene sparata su Kraken tramite CCXT. Le Shadow vengono scritte in una tabella separata di SQLite (`shadow_ledger`) e monitorate matematicamente dallo script di scoring. Questo fornisce addestramento in tempo reale (Online Learning a 24H) senza inquinare il capitale.

### Fase 4: Flattening Deadline (Il Kill Switch)
Allo scadere della `Flattening Window` (es. 15 minuti prima della fine delle 24h), lo script in background impone un override di sistema al *Trader*. 
La direttiva diventa: `{"objective": "FORCE_LIQUIDATION_MARKET"}`. Il motore chiuderà brutalmente a mercato ogni singola posizione futures e venderà ogni moneta spot contro l'asset di riferimento (EUR o USD) per fermare il conteggio e preparare la generazione del report.

---

## 3. L'ORCHESTRAZIONE FINALE: COME DARE IL VIA LIBERA

Se questo piano di sintesi è approvato, il mio compito in totale autonomia sarà:

1. Modificare i file base creati prima (`db_manager.py`, `schemas.py`) per aggiungere il `run_id` e i calcoli del Target.
2. Scrivere il modulo di **Boot/Discovery** (`run_24h_aggro.py`) che si connette alle tue API live per la fotografia iniziale.
3. Incorporare il *Target Gap* nel prompt del Sovrano.
4. Lasciare il *Reporter Llama-8B* attivo come demone (che ti invierà gli stati di avanzamento su Telegram).

Quando tutto è pronto, attenderò il tuo comando **"START MISSION 24H"**. 
Da quel momento spegnerò i miei input umani, lancerò in `nohup` lo script, e la macchina opererà da sola per un'intera orbita terrestre, fino all'avvenuta chiusura e al report finale.

Sei d'accordo con questa rotta di collisione? Procedo a compilare le modifiche tecniche necessarie prima dello startup?
