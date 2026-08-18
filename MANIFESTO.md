# MANIFESTO DEL PROGETTO: KRAKENFONDAZIONE
## *La Scienza delle Orbite Specolative Cartacee*

> "Se questo algoritmo avesse preso il controllo del portafoglio reale che avevo su Kraken nel momento esatto in cui ho premuto START, e avesse fatto trading solo su carta da quel secondo in poi, come si sarebbe evoluto il capitale?"

---

## 1. VISIONE E MISSIONE
**KRAKENFONDAZIONE** è un laboratorio di trading quantitativo ed evolutivo, progettato per girare in ambiente **Ubuntu** privato e sicuro, interfacciato asincronamente con modelli di intelligenza artificiale per l'analisi del rischio e l'esecuzione tattica.

La nostra missione è costruire un'infrastruttura di simulazione finanziaria deterministica ed impermeabile che permetta a Giacomo di testare, ottimizzare e stressare strategie speculative complesse (sia Spot che Futures, Long e Short) in condizioni reali di mercato, senza esporre un singolo centesimo di capitale reale.

---

## 2. PILASTRI E PRINCIPI INVARIANTI

### 🛡️ Impermeabilità Totale (Rigidamente PAPER-ONLY)
Il sistema è tecnicamente e strutturalmente incapace di inviare ordini reali a mercato. Non richiede credenziali Kraken con permessi di scrittura, creazione chiavi di prelievo o negoziazione reale. Le chiavi reali sono utilizzate in **sola lettura** al solo scopo di campionare lo stato iniziale del conto reale.

### 📸 Snapshot Iniziale Immutabile
Ogni nuova strategia avviata segue il ciclo vitale deterministico:
`START -> SNAPSHOT CONTO REALE KRAKEN -> INIZIALIZZAZIONE RUN INDIPENDENTE (RUN_ID) -> STOP`
L'equity di partenza, i saldi e le allocazioni sono specchio esatto della realtà all'istante zero. Da quel momento, l'universo cartaceo si scinde, computando commissioni, slippage e profitti in modo autonomo e immutabile.

### 🏛️ Architettura Asimmetrica Separata
* **Zava U50 (Control Plane):** Il computer di Giacomo. Ospita l'orchestratore OpenClaw, i database SQLite/WAL dei contratti, la dashboard visiva di controllo e la logica decisionale. Custodisce le chiavi di sola lettura e definisce le regole del gioco.
* **VPS di Inferenza (Execution/Inference Plane):** Un'appliance pura di calcolo accelerato (Tesla T4). Non conosce chiavi reali, non ospita database finanziari né logica di esecuzione. Risponde unicamente come server API per i modelli linguistici (NVIDIA Nemotron 30B).

### 🤖 Logica Cognitiva Unificata (The Sovereign Team)
L'intera intelligenza strategica è centralizzata su un **singolo modello pesante (NVIDIA Nemotron 30B GGUF)** servito in locale sulla VPS per eliminare sfasamenti cognitivi e timeout:
1. **Risk Mentor (Il Mentore di Rischio):** Valuta in tempo reale lo snapshot di volatilità, sentiment e cassa, traducendo le metriche in raccomandazioni rigide e conservative di leva e size.
2. **Sovereign Broker / Trader (Il Trader Esecutivo):** Riceve le raccomandazioni del Mentore, esamina i momentum volumetrici e propone l'operazione (BUY/SELL/HOLD), vincolata a rigidi guardrail hardware e watchdog di TP/SL.

---

## 3. DEFINIZIONE DI SUCCESSO
KRAKENFONDAZIONE ha successo quando Giacomo può lanciare, arrestare, monitorare e comparare decine di orbite speculative parallele, ricavandone un quadro matematicamente esatto delle performance, dei drawdown e delle decisioni delle intelligenze artificiali, avendo la certezza matematica che nessuna oscillazione di mercato o errore del codice possa intaccare la sua cassa reale.
