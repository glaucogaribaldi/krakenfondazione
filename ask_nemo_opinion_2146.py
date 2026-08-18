import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti chiede un'opinione strategica aggiornata alle 21:46 sull'andamento del tuo portafoglio.

La situazione corrente è questa:
- Run ID: RUN-24H-C64FA9 (V7.2)
- Cassa di Partenza: €256.86 EUR
- Equity Attuale: €254.15 EUR (un P&L di -1.05%, cassa stabile, praticamente in pari).
- Target: €500.00 EUR (Gap di €245.85)
- Posizione Aperta: Short su PF_PEPEUSD a 574,870,466 contratti con Leva 5.0x.
- PnL Latente (Unrealized): -$2.33 USD (circa -€2.01 EUR).
- Tempo rimanente: circa 1 ora prima del Hard Close automatico stasera alle 22:49.

Esprimi la tua opinione di trader quantitativo: manca esattamente 1 ora all'Hard Close finale delle 22:49. L'esposizione Short è imponente (circa 574 milioni di PEPE) ed è in passivo latente minimo di -$2.33 USD. Sei fiducioso che l'Hard Close liquiderà la posizione in pareggio o in leggero profitto? Qual è la tua valutazione del rischio per questa ultimissima ora e le lezioni apprese in questa run? Rispondi in italiano in modo sintetico, freddo, analitico e focalizzato sul rischio."""

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano in modo approfondito, spietatamente realistico e strutturato."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 600
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    
    with open("/tmp/nemo_opinion_2146.txt", "w") as f:
        f.write(content)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
