import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti chiede un'opinione strategica aggiornata alle 14:46 sull'andamento del tuo portafoglio.

La situazione corrente è questa:
- Run ID: RUN-24H-C64FA9 (V7.2)
- Cassa di Partenza: €256.86 EUR
- Equity Attuale: €263.73 EUR (un profitto reale del +2.67%, con cassa in forte ripresa).
- Target: €500.00 EUR (Gap ridotto a €236.27)
- Posizione Aperta: Short su PF_PEPEUSD incrementato a circa 430 milioni di contratti con Leva 5.0x.
- PnL Latente (Unrealized): +$8.45 USD (circa +€7.30 EUR).
- Tempo rimanente: circa 8 ore prima del Hard Close automatico stasera alle 22:49.

Esprimi la tua opinione di trader quantitativo: l'esposizione Short è ormai imponente (circa 430 milioni di PEPE) ed è in netto profitto di +$8.45 USD. Sei fiducioso che il trend ribassista continuerà per farti colpire il TP di +3.5% su gran parte della posizione? Qual è la tua valutazione del rischio attuale e la gestione della cassa residua per le restanti 8 ore? Rispondi in italiano in modo sintetico, freddo, analitico e focalizzato sul rischio."""

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano in modo approfondito e strutturato."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 600
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    print(content)
except Exception as e:
    print(f"Error querying Nemotron: {e}")
