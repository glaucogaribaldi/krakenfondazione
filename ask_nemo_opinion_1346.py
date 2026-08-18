import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti chiede un'opinione strategica aggiornata alle 13:46 sull'andamento del tuo portafoglio.

La situazione corrente è questa:
- Run ID: RUN-24H-C64FA9 (V7.2)
- Cassa di Partenza: €256.86 EUR
- Equity Attuale: €253.80 EUR (una flessione dell'1.19% sulla cassa reale di partenza della run, con cassa stabile in quest'ora).
- Target: €500.00 EUR (Gap di €246.20)
- Posizione Aperta: Short su PF_PEPEUSD incrementato a circa 400 milioni di contratti con Leva 5.0x.
- PnL Latente (Unrealized): circa -$3.00 USD.
- Tempo rimanente: circa 9 ore prima del Hard Close automatico stasera alle 22:49.

Esprimi la tua opinione di trader quantitativo: l'esposizione Short è ormai imponente (circa 400 milioni di PEPE). Sei fiducioso nel ricalo del prezzo e nel colpire il TP di +3.5%? Qual è la tua valutazione del rischio attuale e del tempo che scorre (scadenza a 9 ore)? Rispondi in italiano in modo sintetico, freddo, analitico e focalizzato sul rischio."""

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
