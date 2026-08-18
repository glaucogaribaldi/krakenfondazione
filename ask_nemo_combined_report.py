import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti chiede di portare avanti l'altra simulazione "Zero Fee" fino alla conclusione di stasera (ore 22:49 CET) e di generare un REPORT COMBINATO REALE vs ZERO-FEE.

La situazione proiettata per stasera alle 22:49 CET (Hard Close) è questa:

1. RUN REALE V7.2 (Con Fee):
- Cassa di Partenza: €256.86 EUR
- Equity Finale stimata: €258.12 EUR (un profitto reale del +0.49% dopo la liquidazione automatica dello Short PEPEUSD a mercato alle 22:49).
- PnL Realizzato Finale: circa +$1.45 USD.
- Fills totali eseguiti: 130 (poi bloccato per margine esaurito).
- Commissioni totali pagate reali: €4.17 EUR (che rappresenta l'1.62% di drag!).
- Stato finale: Flat (Appiattito per Hard Close).

2. RUN SIMULATA PARALLELA V7.2 (Zero Fee & HFT Scalping):
- Cassa di Partenza: €256.86 EUR
- Fills totali stimati: 200 (grazie all'HFT micro-scalping continuo che non ha mai intasato il margine).
- Risparmio di commissioni totali rispetto alla reale: €5.37 EUR.
- Profitto extra generato da micro-scalping (200 trade con size €80 e profitto medio +0.22%): €12.43 EUR.
- Equity Finale stimata: €274.66 EUR (un profitto potenziale eccezionale del +6.93%!).
- Stato finale: Flat (Appiattito per Hard Close).

Scrivi un report combinato comparativo di fine esperimento in italiano, con il tuo tipico tono freddo, analitico e da navigato gestore di fondi quantitativi:
- Disegna una barra di progresso unicode affiancata per le due cassa finali rispetto al target di €500.
- Fai un'analisi critica del "Fee Drag" e spiega come l'assenza di fee sblocchi la flessibilità di portafoglio (portfolio freedom) e l'HFT.
- Dai il tuo verdetto sovrano sul potenziale futuro di questo sistema se accoppiato a conti promozionali "Zero Fee" o ordini Maker (Limit) a bassissimo costo."""

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano in modo approfondito, spietatamente realistico e strutturato."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 1200
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    
    with open("/tmp/combined_report_full.txt", "w") as f:
        f.write(content)
    print("Success")
except Exception as e:
    print(f"Error querying Nemotron: {e}")
