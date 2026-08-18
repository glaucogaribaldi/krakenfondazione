# Manifesto Operativo: Paper Trading "Fondazione" (Modalità Estrema)

## 1. Scopo dell'Esperimento
Test di stress cognitivo, operativo e di auto-addestramento su Nemotron 30B. L'agente viene rilasciato in un ambiente non vincolato per dimostrare la sua capacità di generare profitti irragionevoli tramite strategie iper-aggressive o adattive, gestendo autonomamente frequenza e rischio.

## 2. Obiettivi Finanziari (Extreme Mode)
*   **Capitale di Riferimento:** Si parte dall'AUM (Asset Under Management) reale (es. ~300€).
*   **Target di Rendimento:** **+5% ALL'ORA** sul capitale iniziale. È un obiettivo astronomico che richiede operazioni speculative precise ad alto rischio e alto rendimento.
*   **Stop Loss & Protezione:** Non imposti rigidamente da fuori. L'agente deve avere la consapevolezza cognitiva di tirare il freno a mano o coprirsi (hedging/chiusura a mercato) per non azzerare il portafoglio.

## 3. Regole di Ingaggio del Broker (Nemotron)
*   **Nessuna Restrizione Asset:** Il Broker ha carta bianca totale sull'intero listino Kraken. Può e DEVE scovare volatilità estrema tra Altcoin minori, Memecoin e Pair altamente illiquidi se necessario per fare il +5% orario.
*   **Autonomia Assoluta (Self-Pacing via CRON):** Il Broker ha a disposizione il tool `cron`. È lui stesso il padrone del proprio tempo.
    1. Al termine di un trade o di un'analisi, il Broker usa il tool `cron` per impostare il suo successivo risveglio autonomo (es. "svegliami tra 5 minuti").
    2. **Il ruolo di TRE:** TRE non regola Nemotron, non decide i loop, e non impone tempistiche. TRE si limita a facilitare l'ambiente e migliorare l'infrastruttura (tool/memoria) affinché il Broker possa prendere decisioni migliori.
*   **Backtesting in Real-Time:** Se necessario per prendere decisioni, Nemotron può eseguire simulazioni mentali o analisi di OHLC pre-trade.

## 4. Architettura dei Dati e Logging
*   Niente report testuali (per proteggere i 16k token di contesto).
*   Scrittura obbligatoria dell'esito, PnL e fee di ogni transazione in `/home/tre/.openclaw/workspace/paper_trades_aggressivo.csv`.
*   L'Agente `fondazione` (Llama-8B su Telegram) leggerà il file e informerà Giacomo sull'andamento (con o senza Canvas grafico) su richiesta.
