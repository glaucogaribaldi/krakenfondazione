import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti chiede un'opinione strategica aggiornata alle 20:46 sull'andamento del tuo portafoglio.

La situazione corrente è questa:
- Run ID: RUN-24H-C64FA9 (V7.2)
- Cassa di Partenza: €256.86 EUR
- Equity Attuale: €250.79 EUR (un P&L di -2.36%, cassa in leggera flessione a causa di un piccolo pump temporaneo di PEPE).
- Target: €500.00 EUR (Gap di €249.21)
- Posizione Aperta: Short su PF_PEPEUSD a 574,870,466 contratti con Leva 5.0x.
- PnL Latente (Unrealized): -$6.67 USD (circa -€5.75 EUR).
- Tempo rimanente: circa 2 ore prima del Hard Close automatico stasera alle 22:49.

Esprimi la tua opinione di trader quantitativo: mancano esattamente 2 ore all'Hard Close finale. L'esposizione Short è imponente (circa 574 milioni di PEPE) ed è in passivo latente di -$6.67 USD. Sei preoccupato per questo drawdown? Pensi che PEPE ritraccerà in extremis facendoti chiudere in pari o in leggero utile alla scadenza delle 22:49? Qual è la tua valutazione del rischio per queste ultime 2 ore? Rispondi in italiano in modo sintetico, freddo, analitico e focalizzato sul rischio."""

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
    
    with open("/tmp/nemo_opinion_2046.txt", "w") as f:
        f.write(content)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
