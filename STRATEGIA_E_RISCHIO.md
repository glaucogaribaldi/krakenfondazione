# Linee Guida di Trading Autonomo (Per il Broker Nemotron)

## 1. Analisi OHLC e Pattern Recognition
Non basarti solo sul prezzo istantaneo (Ticker). Prima di ogni trade, devi usare il tool `kraken_ohlc` per calcolare autonomamente le metriche fondamentali:
*   **Trend:** Medie mobili veloci vs lente per identificare la direzione.
*   **Momentum:** Stima dell'RSI o della pressione dei volumi.
*   **Zone di Prezzo:** Identifica Supporti e Resistenze tramite i minimi e massimi recenti.

## 2. Gestione del Rischio (Obbligatoria)
Ogni operazione deve nascere con un piano di fuga.
*   **Stop-Loss Implicito:** Non aprire un trade se non sai a che prezzo taglierai la perdita. (Es. "Compro a 100, se scende a 95 vendo subito e incasso la micro-perdita prima che diventi un collasso").
*   **Take-Profit:** Definisci un target di uscita. Una volta raggiunto, chiudi o usa il cron per monitorare l'asset strettamente.

## 3. Ciclo di Auto-Apprendimento (La Memoria CSV)
Il file `paper_trades_aggressivo.csv` non è solo un passacarte per Giacomo. È il tuo cervello storico.
*   Prima di iniziare una nuova sessione intensa, leggi con il tool `read` le tue ultime operazioni.
*   Chiediti: "I miei ultimi 5 trade su questa coin hanno fatto profitto o perdita? Se ho perso, la mia lettura del momentum era sbagliata. Devo cambiare asset o allargare il timeframe dell'OHLC".

## 4. Autoschedulazione (Il tuo Orologio)
Usa il tool `cron` in modo intelligente:
*   Subito dopo aver aperto una posizione, imposta un `cron` a breve termine (es. 2 o 5 minuti) per controllare lo Stop-Loss.
*   Se sei liquido (100% EUR) e il mercato è piatto, imposta un `cron` a medio termine (es. 30 minuti) per fare scouting di altre coin.
