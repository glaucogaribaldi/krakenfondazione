# MASTERPLAN: Nemotron Sovereign Broker Infrastructure (v2.0)

## Obiettivo Globale
Trasformare Nemotron in un broker autonomo istituzionale, capace di eseguire operazioni API direttamente, gestire il proprio rischio, e addestrarsi in continuo tramite 50 simulazioni parallele in Reinforcement Learning. Lo scopo finale è la massimizzazione del saldo su Kraken, trovando e testando pattern nel mercato passato, presente e futuro.

## I 4 Pilastri (La Catena di Comando)
1.  **Nemotron (30B - Il Broker):** Autonomia totale (esecuzione ordini e risk management). Cosciente del suo ecosistema, decide e si addestra in modo autonomo.
2.  **Llama-8B (Il Mini-Reporter):** Interfaccia Telegram esclusiva. Filtra e traduce, non consumando la potenza di Nemotron per operazioni umane. Raccoglie le strategie scoperte da Nemotron e le propone a Giacomo.
3.  **TRE (L'Ingegnere):** Sviluppa e mantiene l'infrastruttura (Docker, Pipeline dati, Storage) ma NON esegue trade e NON blocca operazioni (fuori dal loop di failsafe del rischio).
4.  **Architetto Gemini:** Analisi e supervisione strategica a lungo raggio offline, ma fuori dal ciclo vitale delle esecuzioni.

## Mappa dell'Infrastruttura e Hardware
*   **Host Computazionale:** VPS (100.73.54.72) con 2x NVIDIA Tesla T4.
*   **Storage (Nuovo Asset):** Disco dedicato da 256GB.
    *   Verrà formattato pulito (senza backup dei dati precedenti) e montato su `/broker/storage`.
    *   Ospiterà le directory:
        *   `/broker/storage/simulations/{sim_id}` (Modelli, pesi, log).
        *   `/broker/storage/shared/data` (Dati storici OHLCV e orderbook Parquet/CSV).
        *   `/broker/storage/shared/config` (Vault locale, setup API di Kraken Paper per Nemotron).

## Fase 1: Setup Storage e Isolamento
1.  Formattazione e mount del nuovo disco da 256GB sulla VPS.
2.  Creazione dell'albero di directory (`/broker/storage/...`).
3.  Implementazione di una cassaforte locale sulla VPS (es. file env criptato) per permettere a Nemotron di accedere alle chiavi API Kraken Paper in autonomia.

## Fase 2: Ingestion Pipeline (Data Feeds)
1.  Sviluppo di un demone (eseguito in background) per il download dei dati storici Kraken.
2.  Setup di una connessione WebSocket per popolare l'Orderbook in tempo reale in `/shared/data`, in modo che le simulazioni possano attingere al flusso live.

## Fase 3: Simulazioni Dockerizzate e Addestramento (RL)
1.  Creazione di un `Dockerfile` (Python 3.10, PyTorch, CCXT, Gymnasium/Ray) per i cloni di addestramento.
2.  Avvio di 50 container Docker, ognuno con una variante strategica.
3.  **Il Loop di Addestramento:**
    *   Ogni agente simula operazioni.
    *   Limite interno imposto da Nemotron per le simulazioni: Max Drawdown 20%, 100 trade/giorno max.
    *   Dopo 10.000 step di addestramento (o X giorni), le strategie fallimentari vengono terminate e i pesi delle strategie con Sharpe Ratio > 1.5 vengono salvati.

## Fase 4: Esecuzione Live (Paper) e Promozione
1.  Nemotron osserva i risultati delle 50 simulazioni.
2.  Promuove la strategia migliore estraendo i pesi dal miglior container.
3.  Esegue lo script di "Live Paper Trading" usando la libreria `ccxt` direttamente verso Kraken.

## Fase 5: Consapevolezza e Reportistica (Il Ruolo di Llama-8B)
1.  Nemotron scriverà un file di riassunto strategico in `/broker/storage/shared/insights.md`.
2.  Il modello Mini (Llama-8B) leggerà questo file e genererà i report via Telegram per Giacomo.
3.  I report conterranno: Performance attuali, Strategie attualmente testate nei 50 cloni paralleli, e nuove intuizioni o pattern scoperti dal modello primario (Nemotron 30B).

## Fase 6: Testing della Catena di Comando e Sblocco Limiti (Aggiunta del 2026-08-14)
1.  **Test End-to-End:** Verifica periodica della comunicazione tra TRE, Nemotron e Reporter.
2.  **Report Capacità Kraken:** Nemotron è incaricato di testare i limiti dell'API Kraken Paper, redigere un report su cosa è in grado di scambiare (asset disponibili, tipi di ordini) e identificare eventuali blocchi da rimuovere (es. margin trading, futures, limiti di rate).
3.  **Inizializzazione Self-Training:** Nemotron avvia autonomamente le simulazioni caricando il portafoglio iniziale di Giacomo come base e simulando scenari (passati/presenti/futuri) su tutti gli asset.

---
*Status: IN ESECUZIONE.*