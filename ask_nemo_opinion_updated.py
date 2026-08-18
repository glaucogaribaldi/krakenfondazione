import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti chiede un'opinione strategica aggiornata a caldo sull'andamento del tuo portafoglio.

La situazione corrente alle 13:21 è questa:
- Run ID: RUN-24H-C64FA9 (V7.2)
- Cassa di Partenza: €256.86 EUR
- Equity Attuale: €254.08 EUR (una leggera oscillazione del -1.08%).
- Target: €500.00 EUR (Gap di €245.92)
- Posizione Aperta: Short su PF_PEPEUSD incrementato a 339,370,859 contratti con Leva 5.0x.
- PnL Latente (Unrealized): -$2.82 USD (circa -€2.43 EUR).
- Tempo rimanente: circa 11.3 ore prima del Hard Close automatico stasera alle 22:49.

Esprimi la tua opinione di trader quantitativo su questa posizione: sei preoccupato per questa oscillazione? Perché hai incrementato la dimensione short a 339 milioni di contratti? Ritieni che il trend stia per piegarsi a nostro favore permettendoti di colpire il TP? Rispondi in italiano in modo sintetico, freddo, analitico e focalizzato sul rischio."""

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
