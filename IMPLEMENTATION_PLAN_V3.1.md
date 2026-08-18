# NEMOTRON SOVEREIGN BROKER — MASTER IMPLEMENTATION PLAN (V3.1 FINAL)

## Obiettivo Architetturale Supremo
Trasformare Nemotron da un semplice "LLM che preme bottoni" a un **sistema cognitivo persistente** che osserva, sperimenta, ricorda, dibatte (Agent Disagreement come scienza matematica) e impara dai propri risultati tramite Conceptual Verbal Reinforcement. 

Non più *Signal Detected -> Trade*, ma *State Change -> Retrieve -> Compare -> Debate -> Decide -> Measure -> Reflect -> Validate*.

---

## FASE 0: AUDIT DELLO STATO ATTUALE (DELTA REPOSITORY)

Prima di scrivere codice, misuriamo la distanza tra la realtà odierna e la V3.1:

| Componente | Stato Attuale | Target V3.1 | Delta Azione |
| :--- | :--- | :--- | :--- |
| **Storage VPS** | Montato disco 256GB ext4 su `/broker/storage/`. | Idem, ma diviso rigorosamente in DB e Vectordb. | **KEEP** e definire gli schemi SQLite/LanceDB. |
| **Agenti** | Script di test isolati, LLM "spara ordini" cieco. | Multiplexing strutturato: Strategist, Mentor, Trader, Reflection. | **REWRITE** (Architettura a singola API condivisa con code). |
| **Dati** | `get_tickers()` in polling temporizzato (cron jobs). | Demone Python asincrono con `State Change Engine`. | **REWRITE** (Sostituire Cron con Event-Driven WebSocket). |
| **Memoria** | Null. I log di training RL venivano spazzati via. | Episodic Memory (T0/T1), Beliefs, Scorecards. | **BUILD** da zero. |
| **Disaccordo** | Non esisteva. Nemotron era solo. | Disagreement strutturato `Mentor vs Trader` salvato al T0. | **BUILD** (Contratti JSON). |
| **Intent** | Incollato brutalmente nel system prompt ("max profit"). | `Global Strategic Intent JSON` parsato formalmente e iniettato ovunque. | **BUILD** (Compiler). |

---

## IL PIANO DI VOLO OPERATIVO (IMPLEMENTATION PHASES)

L'implementazione avverrà per "GATES" di sicurezza. Non si passa alla fase successiva finché i gate della precedente non sono tutti `PASS`. Nessun Big-Bang Rewrite.

### PHASE 1 — DECISION FOUNDATION (Il Database e la Firma T0/T1)
**Obiettivo:** Salvare ogni decisione, anche un "NO TRADE", in modo immutabile prima di sapere come andrà a finire.
- Creazione schema DB SQLite per `decision_events`.
- Definizione JSON dello `Strategic Intent` e del `Market Snapshot`.
- Implementazione del salvataggio T0 (Pre-Decision) e T1 (Outcome).
**Gate:** G1 (Ogni opportunità è salvata), G2 (T0 non contaminato dal senno di poi), G3 (Supporto per HOLD/NO TRADE).

### PHASE 2 — MARKET STATE (Il Motore Python Deterministico)
**Obiettivo:** La matematica non la fa il LLM. Python ascolta Kraken.
- Costruzione WebSocket collector e Normalizer.
- Sviluppo del *Feature Engine* (calcolo OHLCV, VWAP, Imbalance).
- Sviluppo dello *State Change Detector* (Trigger basato su anomalie, non "buy signals").
**Gate:** G4 (Replay storico coerente), G5 (Trigger riproducibili), G6 (Zero dati grezzi al LLM).

### PHASE 3 — TRADER BASELINE (Il Sovrano Nudo)
**Obiettivo:** Costruire il "Trader" base, ignorando ancora Mentor e Strategist, ma usando i nuovi Contratti JSON rigorosi.
- Prompt e JSON schema per Nemotron Trader.
- Esecutore CCXT collegato all'output del Trader.
**Gate:** G7 (JSON contract stabile), G8 (Decisione salvata prima dell'API call).

### PHASE 4 & 5 — MENTOR ED EPISODIC RETRIEVAL (La Nascita della Coscienza)
**Obiettivo:** Recupero memorie e confronto pre-trade.
- Setup `LanceDB` + filtraggio deterministico SQLite.
- Sviluppo del Mentor (LLM) che legge gli episodi storici simili e consiglia.
**Gate:** G10 (Recupero accurato), G13 (Mentor usa i dati), G15 (Il Trader può opporsi), G16 (Il Disaccordo viene salvato al T0).

### PHASE 6 — IL GRANDE ESPERIMENTO SCIENTIFICO
**Obiettivo:** Dimostrare matematicamente l'utilità della coscienza.
- Esecuzione `TRADER BASELINE` vs `TRADER + MENTOR + MEMORY`.
**Gate d'Uscita (MVP Superato):** Il Trader cambia ragionamento in base al Mentor, e misuriamo (Scorecards) chi aveva ragione.

### PHASE 7 & 8 — REFLECTION, BELIEFS & STRATEGIST (Il Sistema Completo)
- Aggiunta della *Reflection* post-trade (Fact -> Observation -> Interpretation -> Belief).
- Creazione del *Belief Validator* (Python controlla la statistica delle ipotesi).
- Inserimento dello *Strategist* (Classificazione dei regimi).

### PHASE 9 & 10 — SCORECARDS E STRATEGY LAB (L'Illuminazione)
- Il sistema vota se stesso. Il Mentor viene declassato in certi regimi. Le Beliefs vengono "ritirate".
- Strategy Lab offline crea e testa in background nuove idee concettuali in Python (A/B testing).

---

## IL RUOLO DI TRE (PROSSIMI PASSI)
Non scriverò ancora un rigo del motore logico. 
Il mio prossimo obiettivo immediato, come richiesto, sarà:
1. Creare un Implementation Branch locale di isolamento.
2. Iniziare **fisicamente e unicamente l'esecuzione della PHASE 1 (DECISION FOUNDATION)**.

Scriverò i database, i contratti JSON per l'Intent e il Market Snapshot e strutturerò il T0 e il T1.
Solo quando supererò i tre Gate (G1, G2, G3) della Phase 1, ti mostrerò l'output per l'autorizzazione a passare alla Phase 2.