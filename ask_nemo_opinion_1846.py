import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti chiede un'opinione strategica aggiornata alle 18:46 sull'andamento del tuo portafoglio.

La situazione corrente è questa:
- Run ID: RUN-24H-C64FA9 (V7.2)
- Cassa di Partenza: €256.86 EUR
- Equity Attuale: €256.77 EUR (un P&L di -0.03%, praticamente in perfetto pareggio).
- Target: €500.00 EUR (Gap di €243.23)
- Posizione Aperta: Short su PF_PEPEUSD a 573,745,410 contratti con Leva 5.0x.
- PnL Latente (Unrealized): +$0.59 USD (circa +€0.51 EUR).
- Tempo rimanente: circa 4 ore prima del Hard Close automatico stasera alle 22:49.

Esprimi la tua opinione di trader quantitativo: l'esposizione Short è imponente (circa 573 milioni di PEPE) ed è praticamente in pari. Hai esaurito il margine disponibile sulla VPS (Available: $0.49 USD), quindi la tua posizione è al picco dell'esposizione consentita. Sei fiducioso che il trend ribassista si accentuerà per farti colpire il TP di +3.5% su gran parte della posizione prima dell'Hard Close temporale? Qual è la tua valutazione del rischio attuale e la gestione della cassa residua per le restanti 4 ore? Rispondi in italiano in modo sintetico, freddo, analitico e focalizzato sul rischio."""

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
